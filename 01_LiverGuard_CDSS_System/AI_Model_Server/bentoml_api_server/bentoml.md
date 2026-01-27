

-----

````markdown
# Windows 환경에서 nnU-Net + BentoML 서빙 트러블슈팅 가이드

## 1. 배경 (Background)
Windows 로컬 환경(NVIDIA GPU 보유)에서 학습된 **nnU-Net** 모델을 **BentoML**을 사용하여 서빙하려 함.

* **OS:** Windows 10/11
* **Hardware:** NVIDIA GPU (RTX 2060 등)
* **Frameworks:** PyTorch, nnU-Net v2, BentoML

## 2. 문제 상황 (The Problem)
Windows 터미널(PowerShell/CMD)에서 `bentoml serve` 명령어로 서비스를 실행할 때 지속적인 오류 발생.

### 주요 증상
* BentoML의 프로세스 관리 방식(Fork)이 Windows의 프로세스 생성 방식(Spawn)과 충돌하여 호환성 문제 발생.
* `Flask`를 사용한 임시 서버는 작동하지만, BentoML의 핵심 기능(Adaptive Batching, Model Management, Docker Packaging)을 사용할 수 없음.
* 특히 멀티 모델(Multi-model) 서빙 확장 시 관리가 어려움.

## 3. 해결 방법 (Solution): WSL2 활용
Windows Subsystem for Linux 2 (WSL2)를 사용하여 **Windows 안에 리눅스(Ubuntu) 환경**을 구축하여 해결.
* BentoML은 리눅스 환경에서 가장 안정적으로 동작함.
* WSL2는 Windows의 GPU 드라이버를 그대로 인식하므로 **추론 성능(CUDA 가속) 저하가 없음.**

---

## 4. 단계별 적용 가이드 (Step-by-Step)

### Step 1: WSL2 및 Ubuntu 설치
Windows PowerShell(관리자 권한)에서 아래 명령어 실행 후 재부팅.
```bash
wsl --install
````

이후 Microsoft Store에서 'Ubuntu 22.04 LTS' 설치 및 실행.

### Step 2: 프로젝트 경로 접근

WSL2(Ubuntu) 터미널에서는 Windows의 C드라이브가 `/mnt/c/` 경로로 마운트됨.
별도의 파일 복사 없이 Windows에 있는 프로젝트 폴더로 바로 이동 가능.

```bash
# 예시: Windows의 사용자 폴더 내 프로젝트로 이동
cd /mnt/c/Users/사용자명/Documents/MyProject
```

### Step 3: 리눅스 환경에 라이브러리 설치

WSL2 내부의 파이썬 환경에 필요한 패키지 설치.

```bash
pip install bentoml nnunetv2 torch numpy
```

### Step 4: 서비스 코드(service.py) 경로 수정 **(핵심)**

Windows 스타일의 경로(`C:\Users\...`)를 리눅스 스타일(`/mnt/c/Users/...`)로 변경해야 함.
또한 경로 구분자를 역슬래시(`\`)에서 슬래시(`/`)로 변경.

**수정 전 (Windows):**

```python
os.environ['nnUNet_raw'] = r"C:\Users\User\Downloads\Dataset006"
model_folder = r"C:\Users\User\Downloads\Dataset006\nnUNetTrainer..."
```

**수정 후 (WSL2/Linux):**

```python
os.environ['nnUNet_raw'] = "/mnt/c/Users/User/Downloads/Dataset006"
model_folder = "/mnt/c/Users/User/Downloads/Dataset006/nnUNetTrainer..."
```

### Step 5: 서버 실행

Ubuntu 터미널에서 실행.

```bash
bentoml serve service.py:svc --reload
```

-----

## 5\. 최종 코드 예시 (service.py)

```python
import os
import bentoml
import numpy as np
import torch
from nnunetv2.inference.predict_from_raw_data import nnUNetPredictor
import traceback

# [중요] 경로를 WSL 형식(/mnt/c/...)으로 설정
BASE_PATH = "/mnt/c/Users/401-14/Downloads/Dataset006_Liver"
os.environ['nnUNet_raw'] = BASE_PATH
os.environ['nnUNet_preprocessed'] = BASE_PATH
os.environ['nnUNet_results'] = BASE_PATH

@bentoml.service(name="nnunet_liver_segmentation")
class NNUNetService:
    def __init__(self):
        print("Initializing NNUNetService on WSL2...")
        try:
            self.predictor = nnUNetPredictor(
                tile_step_size=0.5,
                use_gaussian=True,
                use_mirroring=True,
                device=torch.device('cuda'), # WSL2에서도 CUDA 사용 가능
                verbose=False,
                verbose_preprocessing=False,
                allow_tqdm=False
            )
            
            # 모델 폴더 경로 (WSL 형식)
            model_folder = f"{BASE_PATH}/nnUNetTrainer__nnUNetPlans__3d_fullres"
            
            self.predictor.initialize_from_trained_model_folder(
                model_folder,
                use_folds=('0',),
                checkpoint_name='checkpoint_final.pth'
            )
            print("✅ nnU-Net Predictor initialized successfully on GPU.")
        except Exception as e:
            print(f"❌ Error initializing service: {e}")
            traceback.print_exc()
            raise e

    @bentoml.api
    def segment(self, input_data: np.ndarray) -> np.ndarray:
        # 추론 로직 (생략)
        pass
```

## 6\. 결론

Windows에서 BentoML 서빙 시 발생하는 복잡한 환경 설정 문제와 싸우지 말고, **WSL2**를 사용하는 것이 정신 건강과 프로젝트 진행 속도에 훨씬 유리함.

```
```