import * as cornerstone from 'cornerstone-core';
import * as cornerstoneWADOImageLoader from 'cornerstone-wado-image-loader';
import * as dicomParser from 'dicom-parser';

let isInitialized = false;

export const initializeCornerstone = () => {
  if (isInitialized) {
    console.log('Cornerstone already initialized');
    return;
  }

  console.log('Initializing Cornerstone...');

  // External dependencies 설정
  cornerstoneWADOImageLoader.external.cornerstone = cornerstone;
  cornerstoneWADOImageLoader.external.dicomParser = dicomParser;

  // WADO Image Loader 설정
  cornerstoneWADOImageLoader.configure({
    beforeSend: (xhr: XMLHttpRequest) => {
      // Orthanc 인증 설정 (필요한 경우)
      // const auth = btoa('orthanc:orthanc');
      // xhr.setRequestHeader('Authorization', `Basic ${auth}`);
      console.log('Fetching DICOM from:', xhr.responseURL || 'unknown');
    },
    useWebWorkers: false, // WebWorker 비활성화 (안정성)
  });

  // Image Loader 등록 (타입 단언 사용)
  (cornerstone as any).registerImageLoader('wadouri', (cornerstoneWADOImageLoader as any).wadouri.loadImage);

  isInitialized = true;
  console.log('Cornerstone initialization complete');
};
