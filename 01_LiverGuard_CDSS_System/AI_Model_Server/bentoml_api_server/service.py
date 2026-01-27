import os
import sys
import site
import bentoml
import numpy as np
import torch
import nibabel as nib
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
import traceback
import pydicom
from pydicom import dataset
import dicom2nifti 
import dicom2nifti.settings as dicom_settings
import imageio 
import requests # 👈 Orthanc 통신을 위해 추가
import shutil # 👈 임시 폴더 삭제를 위해 추가
import glob # 👈 DICOM 파일 목록을 가져오기 위해 추가

# ----------------------------------------------------
# ⚠️ Orthanc 설정 (필요에 따라 변경하세요)
# ----------------------------------------------------
# Docker Compose 환경에서 BentoML 컨테이너가 Orthanc 컨테이너와 통신할 때 사용
# Orthanc 컨테이너의 서비스 이름을 사용합니다.
ORTHANC_URL = "http://orthanc_pacs:8042" 
ORTHANC_AUTH = ('orthanc', 'orthanc') # 기본 인증 정보


# =====================================================================
# Custom Trainer 강제 주입 (BentoML 안에서도 이게 있어야 돌아갑니다)
# =====================================================================
try:
    # nnunetv2 설치 경로 찾기 (BentoML 컨테이너 내부)
    package_paths = site.getsitepackages()
    target_path = None
    for p in package_paths:
        potential_path = os.path.join(p, "nnunetv2", "training", "nnUNetTrainer", "variants")
        if os.path.exists(potential_path):
            target_path = potential_path
            break

    if target_path:
        custom_trainer_file = os.path.join(target_path, "custom_trainer.py")
        # 파일이 없을 때만 생성
        if not os.path.exists(custom_trainer_file):
            with open(custom_trainer_file, "w") as f:
                f.write("from nnunetv2.training.nnUNetTrainer.nnUNetTrainer import nnUNetTrainer\n")
                f.write("class nnUNetTrainer200epochs(nnUNetTrainer):\n")
                f.write("    def __init__(self, plans: dict, configuration: str, fold: int, dataset_json: dict, unpack_dataset: bool = True, device: str = 'cuda'):\n")
                f.write("        super().__init__(plans, configuration, fold, dataset_json, unpack_dataset, device)\n")
                f.write("        self.num_epochs = 200\n")
            print(f"[OK] Custom trainer injected at: {custom_trainer_file}")
except Exception as e:
    print(f"[WARNING] Trainer Injection Warning: {e}")

# 1. 환경변수에 'LITS_MODEL_PATH'가 없는지 확인 (즉, 로컬 개발 환경인지 확인)
if 'LITS_MODEL_PATH' not in os.environ:
    print("[WARNING] Local environment detected: Setting path manually.")

    # 2. 로컬일 때만 작동하는 코드 - 새로운 전이학습 모델 경로
    LITS_MODEL_PATH = r"c:\my_Deeplearning_project\Lits_results\bento_lits_service\model_data"
    os.environ['LITS_MODEL_PATH'] = LITS_MODEL_PATH

else:
    # 3. 환경변수가 있다면 (BentoML 배포 환경)
    print(f"✅ 서버 환경 감지: 설정된 경로를 사용합니다. ({os.environ['LITS_MODEL_PATH']})")


# =========================================================================
# 💡 헬퍼 함수 1: PNG 추출 (이전 수정된 버전)
# =========================================================================
def find_and_save_best_slices(data_array, mask_array, save_dir, base_name, label_tumor=2, num_slices=3):
    """
    3D 마스크에서 종양(라벨 2) 픽셀이 가장 많은 단면을 찾아 오버레이 PNG로 저장합니다.
    (이전 코드와 동일하므로 세부 구현은 생략)
    """
    if mask_array.ndim != 3:
        return []

    tumor_counts = np.sum(mask_array == label_tumor, axis=(0, 1))
    if np.max(tumor_counts) == 0:
        liver_counts = np.sum(mask_array == 1, axis=(0, 1))
        best_z_index = np.argmax(liver_counts)
    else:
        best_z_index = np.argmax(tumor_counts)

    z_indices = [
        max(0, best_z_index - 1), 
        best_z_index,             
        min(mask_array.shape[2] - 1, best_z_index + 1) 
    ]
    
    saved_files = []
    COLOR_MAP = {
        1: np.array([255, 0, 0]),     # Liver (Red)
        2: np.array([0, 255, 0])      # Tumor (Green)
    }
    ALPHA = 0.5 
    
    for i, z in enumerate(z_indices):
        slice_data = data_array[:, :, z]
        mask_slice = mask_array[:, :, z] 
        
        slice_data_norm = ((slice_data - slice_data.min()) / (slice_data.max() - slice_data.min()) * 255)
        rgb_slice = np.stack((slice_data_norm, slice_data_norm, slice_data_norm), axis=-1).astype(np.uint8)
        
        output_rgb = rgb_slice.copy()
        mask_indices = mask_slice > 0 

        if np.any(mask_indices):
            color_mask = np.zeros_like(rgb_slice, dtype=np.uint8)
            for label, color in COLOR_MAP.items():
                indices = mask_slice == label
                color_mask[indices] = color
            
            output_rgb[mask_indices] = (
                (1 - ALPHA) * rgb_slice[mask_indices] + ALPHA * color_mask[mask_indices]
            ).astype(np.uint8)

        png_path = os.path.join(save_dir, f"{base_name}_seg_slice_{i+1}_z{z}.png")
        imageio.imwrite(png_path, output_rgb) 
        
        saved_files.append(png_path)

    return saved_files


# =========================================================================
# 💡 헬퍼 함수 2: DICOM SEG 생성 및 Orthanc 업로드 (최종 안정 버전)
# =========================================================================
def create_dicom_seg_and_upload(dicom_dir: str, mask_array: np.ndarray, base_name: str, nii_affine) -> str:
    try:
        dicom_files = sorted(glob.glob(os.path.join(dicom_dir, '*.dcm')))
        if not dicom_files:
            return "❌ No DICOM files found."

        ds_list = [pydicom.dcmread(f) for f in dicom_files]
        ds_template = ds_list[0]

        from pydicom.uid import generate_uid, ExplicitVRLittleEndian
        from datetime import datetime

        seg = pydicom.Dataset()
        seg.file_meta = pydicom.dataset.FileMetaDataset()
        seg.file_meta.MediaStorageSOPClassUID = pydicom.uid.SegmentationStorage
        seg.file_meta.MediaStorageSOPInstanceUID = generate_uid()
        seg.file_meta.ImplementationClassUID = generate_uid()
        seg.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

        seg.SOPClassUID = pydicom.uid.SegmentationStorage
        seg.SOPInstanceUID = seg.file_meta.MediaStorageSOPInstanceUID
        seg.Modality = "SEG"

        # ✅ 환자 / 스터디 정보 "완전 복사"
        seg.PatientName = ds_template.PatientName
        seg.PatientID = ds_template.PatientID
        seg.StudyInstanceUID = ds_template.StudyInstanceUID
        seg.SeriesInstanceUID = generate_uid()
        seg.SeriesNumber = 999
        seg.InstanceNumber = 1
        seg.Manufacturer = "BENTOML_AI_SERVICE"

        now = datetime.now().strftime('%Y%m%d%H%M%S')
        seg.ContentDate = now[:8]
        seg.ContentTime = now[8:]

        # ✅ 픽셀 구조
        seg.Rows = mask_array.shape[0]
        seg.Columns = mask_array.shape[1]
        seg.NumberOfFrames = mask_array.shape[2]
        seg.BitsAllocated = 8
        seg.BitsStored = 8
        seg.HighBit = 7
        seg.SamplesPerPixel = 1
        seg.PhotometricInterpretation = "MONOCHROME2"
        seg.PixelRepresentation = 0
        seg.PixelData = (mask_array > 0).astype(np.uint8).tobytes()

        # ✅ Segment 정의
        seg1 = pydicom.Dataset()
        seg1.SegmentNumber = 1
        seg1.SegmentLabel = "Liver"
        seg1.SegmentAlgorithmType = "AUTOMATIC"

        seg2 = pydicom.Dataset()
        seg2.SegmentNumber = 2
        seg2.SegmentLabel = "Tumor"
        seg2.SegmentAlgorithmType = "AUTOMATIC"

        seg.SegmentSequence = pydicom.Sequence([seg1, seg2])

        # ✅✅✅ 핵심 1: Referenced Series 연결
        ref_series = pydicom.Dataset()
        ref_series.SeriesInstanceUID = ds_template.SeriesInstanceUID
        ref_series.ReferencedInstanceSequence = pydicom.Sequence()

        for ds in ds_list:
            ref = pydicom.Dataset()
            ref.ReferencedSOPClassUID = ds.SOPClassUID
            ref.ReferencedSOPInstanceUID = ds.SOPInstanceUID
            ref_series.ReferencedInstanceSequence.append(ref)

        seg.ReferencedSeriesSequence = pydicom.Sequence([ref_series])

        # ✅✅✅ 핵심 2: Referenced Study 연결
        ref_study = pydicom.Dataset()
        ref_study.ReferencedSOPClassUID = ds_template.SOPClassUID
        ref_study.ReferencedStudyInstanceUID = ds_template.StudyInstanceUID
        ref_study.ReferencedSeriesSequence = pydicom.Sequence([ref_series])

        seg.ReferencedStudySequence = pydicom.Sequence([ref_study])

        # ✅ SEG 파일 저장
        temp_seg_path = os.path.join(dicom_dir, f"{base_name}_seg_upload.dcm")
        pydicom.dcmwrite(temp_seg_path, seg)

        # ✅ Orthanc 업로드
        with open(temp_seg_path, "rb") as f:
            dicom_bytes = f.read()

        upload_response = requests.post(
            f"{ORTHANC_URL}/instances",
            data=dicom_bytes,
            headers={"Content-Type": "application/dicom"},
            auth=ORTHANC_AUTH,
            timeout=30
        )

        os.remove(temp_seg_path)

        if upload_response.status_code in [200, 201]:
            return f"✅ Success: {upload_response.json().get('ID')}"
        else:
            return f"❌ Upload Failed: {upload_response.status_code} {upload_response.text}"

    except Exception as e:
        traceback.print_exc()
        return f"❌ SEG Upload Error: {str(e)}"

# =========================================================================
# 💡 NNUNetService 클래스
# =========================================================================

@bentoml.service(
# ... (생략: @bentoml.service 데코레이터 및 __init__ 메서드는 동일)
    name="nnunet_liver_segmentation",
    traffic={"timeout": 3600},
    workers=1,
    resources={"cpu": "4"}
)
class NNUNetService:
    def __init__(self):
        print("Initializing NNUNetService with HCC transfer learning model...")
        try:
            self.predictor = nnUNetPredictor(
                tile_step_size=0.5,
                use_gaussian=True,
                use_mirroring=False,
                device=torch.device('cuda'),
                verbose=False,
                verbose_preprocessing=False,
                allow_tqdm=False
            )

            self.predictor.perform_everything_on_gpu = True

            # 새로운 전이학습 모델 경로 (Dataset007_HCC)
            model_folder = os.environ['LITS_MODEL_PATH']

            print(f"[INFO] Model loading path: {model_folder}")

            self.predictor.initialize_from_trained_model_folder(
                model_folder,
                use_folds=(0,),
                checkpoint_name='checkpoint_best.pth'
            )
            print("[OK] HCC Transfer Learning Model Loaded Successfully!")

        except Exception as e:
            print(f"[ERROR] Init Error: {e}")
            traceback.print_exc()
            raise e

    @bentoml.api
    def segment(self, file_path: str) -> dict:
        
        # 0. 필수 검사 (볼륨 마운트 확인)
        if not file_path or not os.path.exists(file_path):
            return {"status": "error", "message": f"File not found: {file_path}"}

        print(f"[INFO] [BentoML] File load request: {file_path}")

        dicom_dir = file_path 
        temp_output_dir = os.path.join(dicom_dir, 'nifti_temp')
        
        # 1. DICOM to NIfTI 변환
        try:
            # ... (생략: DICOM to NIfTI 변환 로직은 동일) ...
            if not os.path.isdir(temp_output_dir):
                os.makedirs(temp_output_dir, exist_ok=True)

            dicom_settings.disable_validate_slice_increment()
            # dicom_settings.enable_resampling() 
            
            dicom2nifti.convert_directory(dicom_dir, temp_output_dir)
             
        except Exception as e:
            print(f"❌ DICOM to NIfTI 변환 실패 오류: {e}")
            traceback.print_exc()
            return {"status": "error", "message": f"DICOM 변환 중 오류 발생: {e}"}

        # ----------------------------------------------------
        # 2. 변환된 NIfTI 파일을 모두 찾아서 루프 시작
        # ----------------------------------------------------
        nifti_files = [f for f in os.listdir(temp_output_dir) if f.endswith('.nii.gz')]
        
        if not nifti_files:
            return {"status": "error", "message": "NIfTI 파일 생성 실패. DICOM Series가 아닙니다. (입력 데이터 확인 필요)"}

        all_results = []
        
        for nifti_file_name in nifti_files:
            nifti_file_path = os.path.join(temp_output_dir, nifti_file_name)
            
            try:
                # 1. 파일 로드 및 추론 준비
                nii = nib.load(nifti_file_path)
                nii_canonical = nib.as_closest_canonical(nii)
                
                input_data_3d = nii_canonical.get_fdata().astype(np.float32)
                input_data = input_data_3d[np.newaxis, ...]

                print(f"🚀 [BentoML] 추론 시작: {nifti_file_name} (Shape: {input_data.shape})")
                
                # 2. 추론 수행
                ret = self.predictor.predict_single_npy_array(
                    input_data, {'spacing': [1.0, 1.0, 1.0]}, None, None, False
                )
                
                # 3. 결과 정리 및 NIfTI 저장
                if isinstance(ret, torch.Tensor):
                    ret = ret.cpu().numpy()
                if ret.ndim == 4: ret = ret[0] # 마스크 (X, Y, Z)

                base_name = nifti_file_name.replace(".nii.gz", "")
                save_path_nii = os.path.join(dicom_dir, f"{base_name}_seg.nii.gz") 
                
                result_img = nib.Nifti1Image(ret.astype(np.uint8), nii_canonical.affine)
                nib.save(result_img, save_path_nii)
                print(f"💾 [BentoML] NIfTI 저장 완료: {save_path_nii}")

                # ----------------------------------------------------
                # 4. PNG 추출 및 저장 (시각화 결과)
                # ----------------------------------------------------
                png_paths = find_and_save_best_slices(
                    input_data_3d, ret, dicom_dir, base_name
                )
                
                # ----------------------------------------------------
                # 5. DICOM SEG 생성 및 Orthanc 업로드 (핵심 추가)
                # ----------------------------------------------------
                orthanc_status = create_dicom_seg_and_upload(
                    dicom_dir, 
                    ret, # 마스크 배열
                    base_name,
                    nii_canonical.affine
                )

                all_results.append({
                    "series_name": base_name,
                    "nifti_path": save_path_nii,
                    "png_slices": png_paths,
                    "orthanc_upload_status": orthanc_status # 👈 최종 결과에 추가
                })

            except Exception as e:
                print(f"❌ Processing Error on {nifti_file_name}: {e}")
                traceback.print_exc()
                all_results.append({
                    "series_name": nifti_file_name,
                    "error": str(e)
                })

        # ----------------------------------------------------
        # 6. 임시 NIfTI 폴더 삭제
        # ----------------------------------------------------
        try:
            shutil.rmtree(temp_output_dir)
            print(f"🧹 임시 폴더 삭제 완료: {temp_output_dir}")
        except Exception as e:
            print(f"⚠️ 임시 폴더 삭제 실패: {e}")

        # 7. 최종 결과 반환
        return {
            "status": "success",
            "message": f"{len(all_results)}개의 시리즈 분석 및 Orthanc 업로드 시도 완료",
            "results": all_results 
        }