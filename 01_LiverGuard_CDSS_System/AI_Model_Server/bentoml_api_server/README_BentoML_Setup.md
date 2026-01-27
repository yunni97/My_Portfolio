
-----

````markdown
# [Guide] Windows에서 nnU-Net + BentoML 서빙 완벽 구축 가이드

## 1. 개요 (Overview)
본 문서는 Windows 로컬 환경(NVIDIA GPU)에서 **nnU-Net** 모델을 **BentoML**로 서빙할 때 발생하는 호환성 문제와 메모리 이슈(OOM)를 해결하고, 안정적인 파이프라인을 구축하는 방법을 기술합니다.

* **Target OS:** Windows 10/11 (WSL2 사용)
* **Hardware:** NVIDIA GeForce RTX 2060 (VRAM 6GB) / RAM 16GB~32GB
* **Goal:** 대용량 3D CT 이미지를 처리하는 안정적인 AI API 서버 구축

---

## 2. 필수 사전 설정 (Prerequisites)

Windows 환경에서 BentoML을 직접 실행하면 `fork/spawn` 프로세스 호환성 문제가 발생합니다. 따라서 **WSL2(Ubuntu)** 환경을 사용해야 합니다.

### Step 1: WSL2 설치 및 환경 구성
PowerShell(관리자 권한)에서 실행:
```powershell
wsl --install
# 재부팅 후 Microsoft Store에서 'Ubuntu 22.04 LTS' 실행
````

### Step 2: WSL 메모리 제한 해제 (중요 ⭐️)

대용량 CT(`volume-110` 등) 처리 시 WSL이 시스템 메모리를 충분히 쓰지 못해 **Process Killed**가 발생하는 것을 방지합니다.

1.  `C:\Users\사용자명\` 경로에 `.wslconfig` 파일 생성.
2.  아래 내용 작성 후 저장:

<!-- end list -->

```ini
[wsl2]
# 본인 PC RAM 용량에 맞춰 설정 (예: 32GB라면 24GB 할당)
memory=24GB
# 스왑 메모리를 넉넉히 잡아 OOM 방지
swap=32GB
processors=4
```

3.  설정 적용을 위해 PowerShell에서 `wsl --shutdown` 실행 후 다시 Ubuntu 실행.

### Step 3: 필수 라이브러리 설치 (Ubuntu 터미널)

```bash
# 기본 라이브러리
pip install bentoml nnunetv2 torch numpy nibabel

# nnU-Net 최신 의존성 (이거 없으면 에러남)
pip install batchgeneratorsv2 acvl-utils dynamic-network-architectures
```

-----

## 3\. 서버 코드 구현 (service.py)

**핵심 포인트:**

1.  **경로 수정:** Windows 경로(`C:\`)를 WSL 경로(`/mnt/c/`)로 변경.
2.  **Safe Mode:** VRAM 6GB 환경에서 터지지 않도록 `perform_everything_on_gpu=False` 설정.
3.  **Timeout 연장:** 대용량 파일 처리를 위해 타임아웃을 1시간으로 설정.

<!-- end list -->

```python
import os
import bentoml
import numpy as np
import torch
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
import traceback

# [경로 설정] WSL 형식(/mnt/c/...) 사용 필수
BASE_PATH = "/mnt/c/Users/401-14/Downloads/Dataset006_Liver"
os.environ['nnUNet_raw'] = BASE_PATH
os.environ['nnUNet_preprocessed'] = BASE_PATH
os.environ['nnUNet_results'] = BASE_PATH

@bentoml.service(
    name="nnunet_liver_segmentation",
    traffic={"timeout": 3600}  # Timeout 1시간으로 설정 (대용량 파일 대비)
)
class NNUNetService:
    def __init__(self):
        print("Initializing NNUNetService (Safe Mode)...")
        try:
            self.predictor = nnUNetPredictor(
                tile_step_size=0.9,       # 속도 향상 및 메모리 절약 (0.5 -> 0.9)
                use_gaussian=False,       # 메모리 절약을 위해 가우시안 끄기
                use_mirroring=False,      # TTA 끄기 (속도 8배 향상)
                device=torch.device('cuda'),
                verbose=False,
                verbose_preprocessing=False,
                allow_tqdm=True
            )
            
            # [핵심] VRAM OOM 방지: 데이터를 RAM에 두고 필요할 때만 GPU로 이동
            self.predictor.perform_everything_on_gpu = False
            
            model_folder = "/mnt/c/Users/401-14/Downloads/Dataset006_Liver/nnUNetTrainer__nnUNetPlans__3d_fullres"
            
            self.predictor.initialize_from_trained_model_folder(
                model_folder,
                use_folds=('0',),
                checkpoint_name='checkpoint_final.pth'
            )
            print("✅ nnU-Net Predictor initialized successfully.")
            
        except Exception as e:
            print(f"Error initializing service: {e}")
            traceback.print_exc()
            raise e

    @bentoml.api
    def segment(self, input_data: np.ndarray) -> np.ndarray:
        # 추론 로직
        ret = self.predictor.predict_single_npy_array(
            input_data, {'spacing': [1.0, 1.0, 1.0]}, None, None, False
        )
        if isinstance(ret, torch.Tensor):
            ret = ret.cpu().numpy()
        return ret
```

-----

## 4\. 트러블슈팅 로그 (Troubleshooting Log)

오늘 발생했던 주요 에러와 해결 방법입니다.

### Issue 1. 환경 변수 미설정 에러

  * **에러:** `nnUNet_raw is not defined...`
  * **원인:** Python 코드에서 `import nnunetv2`가 `os.environ` 설정보다 먼저 실행됨.
  * **해결:** `os.environ` 설정을 코드 \*\*최상단(import 직후)\*\*으로 이동하거나, 터미널에서 `export` 명령어로 미리 설정.

### Issue 2. 의존성 모듈 누락

  * **에러:** `ModuleNotFoundError: No module named 'batchgeneratorsv2'`
  * **원인:** nnU-Net 최신 버전이 구버전 의존성 라이브러리와 호환되지 않음.
  * **해결:** `pip install batchgeneratorsv2` 실행.

### Issue 3. 포트 충돌 (Zombie Process)

  * **에러:** `OSError: [Errno 98] Address already in use`
  * **원인:** 서버를 껐다고 생각했으나 백그라운드에서 살아있음.
  * **해결:** \`\`\`bash
    sudo fuser -k 3001/tcp  \# 3001번 포트 강제 종료
    ```
    
    ```

### Issue 4. 메모리 폭발 (Killed)

  * **에러:** 로그 없이 프로세스가 `Killed` 됨.
  * **원인:** 대용량 파일(`volume-110`) 처리 시 WSL 기본 램 할당량 초과.
  * **해결:** 1. `service.py`에서 `perform_everything_on_gpu = False` 설정.
    2\. `.wslconfig` 파일로 WSL 메모리 할당량 증설.

### Issue 5. 결과 축 뒤집힘 (Misalignment)

  * **현상:** Segmentation 결과가 원본 CT와 엉뚱한 방향으로 겹침 (좌우 반전 등).
  * **원인:** 데이터마다 저장된 축 방향(RAS vs LPS)이 다름.
  * **해결:** 클라이언트 코드에서 `nibabel.as_closest_canonical()`을 사용하여 강제로 \*\*표준 방향(RAS)\*\*으로 정렬 후 전송.

-----

## 5\. 실행 및 테스트 명령어

### 서버 실행 (Ubuntu Terminal)

```bash
# 프로젝트 폴더로 이동
cd /mnt/c/Users/401-14/.gemini/antigravity/scratch/bentoml_nnunet

# 서버 시작 (3001번 포트)
bentoml serve service.py:NNUNetService --reload --port 3001
```

### 클라이언트 테스트 (Python)

```python
# test_real.py 핵심 요약
import bentoml
import nibabel as nib

# 1. 파일 로드 및 표준 정렬 (축 문제 해결)
nii = nib.as_closest_canonical(nib.load("volume-110.nii"))
data = nii.get_fdata()

# 2. 서버 요청 (Timeout 넉넉하게)
client = bentoml.SyncHTTPClient("http://localhost:3001", timeout=3600)
result = client.segment(input_data=data)

# 3. 결과 저장 (표준 Affine 적용)
nib.save(nib.Nifti1Image(result, nii.affine), "result.nii.gz")
```

```
```