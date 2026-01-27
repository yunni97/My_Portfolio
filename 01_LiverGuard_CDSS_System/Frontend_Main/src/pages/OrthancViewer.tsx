import React, { useState, useEffect, useRef } from 'react';
import * as cornerstone from 'cornerstone-core';
import { initializeCornerstone } from '../setupCornerstone';
import {
  getStudies,
  getSeriesByStudy,
  getInstancesBySeries,
  getDicomImageUrl,
  getSegmentationMetadata,
  type OrthancStudy,
  type OrthancSeries,
  type OrthancInstance,
  type SegmentationMetadata,
  type SegmentInfo,
} from '../services/orthanc_api';

// Cornerstone 초기화 (컴포넌트 외부에서 한 번만 실행)
let isInitialized = false;
if (!isInitialized) {
  initializeCornerstone();
  isInitialized = true;
}

const OrthancViewer: React.FC = () => {
  const [studies, setStudies] = useState<OrthancStudy[]>([]);
  const [selectedStudy, setSelectedStudy] = useState<OrthancStudy | null>(null);
  const [ctSeries, setCtSeries] = useState<OrthancSeries[]>([]);
  const [segSeries, setSegSeries] = useState<OrthancSeries[]>([]);
  const [filteredSegSeries, setFilteredSegSeries] = useState<OrthancSeries[]>([]); // 선택된 CT와 연관된 SEG만
  const [selectedCT, setSelectedCT] = useState<OrthancSeries | null>(null);
  const [selectedMask, setSelectedMask] = useState<OrthancSeries | null>(null);
  const [instances, setInstances] = useState<OrthancInstance[]>([]);
  const [currentInstanceIndex, setCurrentInstanceIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');
  const [showOverlay, setShowOverlay] = useState(false);

  const viewerRef = useRef<HTMLDivElement>(null);
  const overlayCanvasRef = useRef<HTMLCanvasElement>(null);
  const [viewerEnabled, setViewerEnabled] = useState(false);

  // 이미지 캐시 (CT와 SEG 분리)
  const ctImageCache = useRef<Map<string, any>>(new Map());
  const segImageCache = useRef<Map<string, any>>(new Map());
  const [preloadProgress, setPreloadProgress] = useState(0);
  const [segInstances, setSegInstances] = useState<OrthancInstance[]>([]);

  // SEG 메타데이터 및 세그먼트 제어
  const [segMetadata, setSegMetadata] = useState<SegmentationMetadata | null>(null);
  const [enabledSegments, setEnabledSegments] = useState<Set<number>>(new Set());

  // Study 목록 로드
  useEffect(() => {
    loadStudies();
  }, []);

  const loadStudies = async () => {
    setLoading(true);
    setError(null);
    try {
      const studyList = await getStudies();
      setStudies(studyList);
    } catch (err) {
      setError('Failed to load studies from Orthanc');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Study 선택 시 Series 로드 (CT와 SEG 분리)
  const handleStudySelect = async (study: OrthancStudy) => {
    setSelectedStudy(study);
    setSelectedCT(null);
    setSelectedMask(null);
    setInstances([]);
    setLoading(true);
    setError(null);
    setViewMode('2d');

    try {
      const seriesList = await getSeriesByStudy(study.ID);

      // CT와 SEG 분리
      const ctList = seriesList.filter(s => s.MainDicomTags.Modality === 'CT');
      const segList = seriesList.filter(s => s.MainDicomTags.Modality === 'SEG');

      console.log('CT Series:', ctList.length, 'SEG Series:', segList.length);

      setCtSeries(ctList);
      setSegSeries(segList);
    } catch (err) {
      setError('Failed to load series');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // CT 선택 시 2D 뷰어로 표시 및 연관된 SEG 필터링
  const handleCTSelect = async (ctSeries: OrthancSeries) => {
    setSelectedCT(ctSeries);
    setSelectedMask(null);
    setViewMode('2d');
    setLoading(true);
    setError(null);
    setPreloadProgress(0);
    setShowOverlay(false);

    // CT 캐시 클리어
    ctImageCache.current.clear();

    try {
      const instanceList = await getInstancesBySeries(ctSeries.ID);

      // InstanceNumber로 정렬
      const sortedInstances = instanceList.sort((a, b) => {
        const numA = parseInt(a.MainDicomTags.InstanceNumber || '0');
        const numB = parseInt(b.MainDicomTags.InstanceNumber || '0');
        return numA - numB;
      });

      console.log('Sorted CT instances:', sortedInstances.map(i => i.MainDicomTags.InstanceNumber));

      setInstances(sortedInstances);
      setCurrentInstanceIndex(0);

      // 선택된 CT의 SeriesInstanceUID
      const ctSeriesInstanceUID = ctSeries.MainDicomTags.SeriesInstanceUID;

      // SEG 시리즈 중에서 이 CT를 참조하는 것만 필터링
      const relatedSegs: OrthancSeries[] = [];
      if (ctSeriesInstanceUID) {
        for (const seg of segSeries) {
          const metadata = await getSegmentationMetadata(seg.ID);
          if (metadata?.ReferencedSeriesSequence) {
            const referencedUIDs = metadata.ReferencedSeriesSequence.map(
              (ref: { SeriesInstanceUID?: string }) => ref.SeriesInstanceUID
            ).filter((uid): uid is string => uid !== undefined);

            if (referencedUIDs.includes(ctSeriesInstanceUID)) {
              relatedSegs.push(seg);
            }
          }
        }
      }

      console.log(`Found ${relatedSegs.length} segmentation(s) related to CT series ${ctSeriesInstanceUID || 'unknown'}`);
      setFilteredSegSeries(relatedSegs);

      if (sortedInstances.length > 0) {
        // 첫 번째 이미지 즉시 표시
        await loadAndDisplayCTImage(sortedInstances[0].ID, 0);
        setLoading(false);

        // 백그라운드에서 나머지 이미지 프리로드
        preloadCTImages(sortedInstances);
      }
    } catch (err) {
      setError('Failed to load instances');
      console.error(err);
      setLoading(false);
    }
  };

  // Mask 선택 시 Overlay 활성화 또는 3D 뷰어로 표시
  const handleMaskSelect = async (segSeries: OrthancSeries) => {
    setSelectedMask(segSeries);
    setLoading(true);
    setError(null);
    setPreloadProgress(0);

    // SEG 캐시 클리어
    segImageCache.current.clear();

    try {
      // SEG 메타데이터 가져오기
      const metadata = await getSegmentationMetadata(segSeries.ID);
      setSegMetadata(metadata);

      // 모든 세그먼트 활성화
      if (metadata?.SegmentSequence) {
        const allSegmentNumbers = new Set(
          metadata.SegmentSequence.map(seg => Number(seg.SegmentNumber))
        );
        setEnabledSegments(allSegmentNumbers);
        console.log('Enabled segments (numbers):', Array.from(allSegmentNumbers));
      }

      const instanceList = await getInstancesBySeries(segSeries.ID);

      // InstanceNumber로 정렬
      const sortedInstances = instanceList.sort((a, b) => {
        const numA = parseInt(a.MainDicomTags.InstanceNumber || '0');
        const numB = parseInt(b.MainDicomTags.InstanceNumber || '0');
        return numA - numB;
      });

      console.log('SEG instances:', sortedInstances.length);

      setSegInstances(sortedInstances);

      // CT가 선택되어 있으면 overlay 모드, 아니면 3D 모드
      if (selectedCT && instances.length > 0) {
        setViewMode('2d');
        setShowOverlay(true);

        // SEG 이미지 프리로드
        await preloadSegImages(sortedInstances);

        // 현재 CT 이미지에 overlay 표시
        renderOverlay(currentInstanceIndex);
      } else {
        setViewMode('3d');
        setInstances(sortedInstances);
        setCurrentInstanceIndex(0);

        if (sortedInstances.length > 0) {
          await loadAndDisplaySegImage(sortedInstances[0].ID, 0);
          setLoading(false);
          preloadSegImages(sortedInstances);
        }
      }

      setLoading(false);
    } catch (err) {
      setError('Failed to load instances');
      console.error(err);
      setLoading(false);
    }
  };

  // CT 이미지 프리로드 (병렬 처리로 속도 개선)
  const preloadCTImages = async (instanceList: OrthancInstance[]) => {
    console.log('Starting CT preload of', instanceList.length, 'images in parallel');

    const loadPromises = instanceList.slice(1).map(async (instance, index) => {
      try {
        const imageUrl = getDicomImageUrl(instance.ID);
        const imageId = `wadouri:${imageUrl}`;

        // 이미지 로드 및 캐시
        const image = await cornerstone.loadImage(imageId);
        ctImageCache.current.set(instance.ID, image);

        // 진행률 업데이트
        const progress = Math.round(((index + 1) / (instanceList.length - 1)) * 100);
        setPreloadProgress(progress);
      } catch (err) {
        console.error('Failed to preload CT image:', instance.ID, err);
      }
    });

    // 모든 이미지를 병렬로 로드
    await Promise.all(loadPromises);

    console.log('CT preload complete');
    setPreloadProgress(100);
  };

  // SEG 이미지 프리로드
  const preloadSegImages = async (instanceList: OrthancInstance[]) => {
    console.log('Starting SEG preload of', instanceList.length, 'images');

    for (let i = 0; i < instanceList.length; i++) {
      try {
        const instanceId = instanceList[i].ID;
        const imageUrl = getDicomImageUrl(instanceId);
        const imageId = `wadouri:${imageUrl}`;

        // 이미지 로드 및 캐시
        const image = await cornerstone.loadImage(imageId);
        segImageCache.current.set(instanceId, image);

        // 진행률 업데이트
        const progress = Math.round(((i + 1) / instanceList.length) * 100);
        setPreloadProgress(progress);
      } catch (err) {
        console.error('Failed to preload SEG image:', err);
      }
    }

    console.log('SEG preload complete');
    setPreloadProgress(100);
  };

  // Cornerstone Viewer 초기화
  useEffect(() => {
    if (viewerRef.current && !viewerEnabled) {
      try {
        cornerstone.enable(viewerRef.current);
        setViewerEnabled(true);
        console.log('Cornerstone viewer enabled');
      } catch (err) {
        console.error('Failed to enable cornerstone viewer:', err);
        setError('Failed to initialize DICOM viewer');
      }
    }

    return () => {
      if (viewerRef.current && viewerEnabled) {
        try {
          cornerstone.disable(viewerRef.current);
        } catch (err) {
          console.error('Failed to disable cornerstone viewer:', err);
        }
      }
    };
  }, [viewerEnabled]);

  // enabledSegments 변경 시 오버레이 다시 렌더링
  useEffect(() => {
    if (showOverlay && selectedMask && segInstances.length > 0 && segMetadata) {
      console.log('enabledSegments changed, re-rendering overlay');
      renderOverlay(currentInstanceIndex);
    }
  }, [enabledSegments]);

  // 마우스 휠 이벤트로 이미지 스크롤
  useEffect(() => {
    const element = viewerRef.current;
    if (!element || instances.length === 0) return;

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();

      // 휠 방향에 따라 이미지 변경
      if (e.deltaY < 0 && currentInstanceIndex > 0) {
        // 휠 위로 = 이전 이미지
        const newIndex = currentInstanceIndex - 1;
        setCurrentInstanceIndex(newIndex);
        if (viewMode === '2d') {
          loadAndDisplayCTImage(instances[newIndex].ID, newIndex);
        } else {
          loadAndDisplaySegImage(instances[newIndex].ID, newIndex);
        }
      } else if (e.deltaY > 0 && currentInstanceIndex < instances.length - 1) {
        // 휠 아래로 = 다음 이미지
        const newIndex = currentInstanceIndex + 1;
        setCurrentInstanceIndex(newIndex);
        if (viewMode === '2d') {
          loadAndDisplayCTImage(instances[newIndex].ID, newIndex);
        } else {
          loadAndDisplaySegImage(instances[newIndex].ID, newIndex);
        }
      }
    };

    element.addEventListener('wheel', handleWheel, { passive: false });

    return () => {
      element.removeEventListener('wheel', handleWheel);
    };
  }, [instances, currentInstanceIndex, viewMode, showOverlay, selectedMask, segInstances]);

  // CT 이미지 로드 및 표시 (캐시 사용)
  const loadAndDisplayCTImage = async (instanceId: string, index: number) => {
    if (!viewerRef.current) {
      console.error('Viewer ref is not available');
      return;
    }

    if (!viewerEnabled) {
      console.error('Viewer is not enabled yet');
      setError('Viewer is not initialized. Please wait and try again.');
      return;
    }

    try {
      setError(null);
      const element = viewerRef.current;

      let image;

      // 캐시에서 이미지 찾기
      if (ctImageCache.current.has(instanceId)) {
        console.log('Using cached CT image for instance:', instanceId);
        image = ctImageCache.current.get(instanceId);
      } else {
        // 캐시에 없으면 로드
        console.log('Loading CT image for instance:', instanceId);
        const imageUrl = getDicomImageUrl(instanceId);
        const imageId = `wadouri:${imageUrl}`;
        image = await cornerstone.loadImage(imageId);

        // 캐시에 저장
        ctImageCache.current.set(instanceId, image);
      }

      // 뷰어에 표시
      cornerstone.displayImage(element, image);

      // 윈도우 레벨 자동 조정
      const viewport = cornerstone.getDefaultViewportForImage(element, image);
      cornerstone.setViewport(element, viewport);

      // 강제 resize (렌더링 문제 해결)
      cornerstone.resize(element);

      console.log(`CT Image ${index + 1} displayed successfully`);

      // Overlay가 활성화되어 있으면 overlay 렌더링
      if (showOverlay && selectedMask) {
        renderOverlay(index);
      }
    } catch (err: any) {
      const errorMessage = `Failed to load CT image: ${err.message || err}`;
      setError(errorMessage);
      console.error('CT load error:', err);
      console.error('Error stack:', err.stack);
    }
  };

  // SEG 이미지 로드 및 표시 (3D 뷰 용)
  const loadAndDisplaySegImage = async (instanceId: string, index: number) => {
    if (!viewerRef.current) {
      console.error('Viewer ref is not available');
      return;
    }

    if (!viewerEnabled) {
      console.error('Viewer is not enabled yet');
      setError('Viewer is not initialized. Please wait and try again.');
      return;
    }

    try {
      setError(null);
      const element = viewerRef.current;

      let image;

      // 캐시에서 이미지 찾기
      if (segImageCache.current.has(instanceId)) {
        console.log('Using cached SEG image for instance:', instanceId);
        image = segImageCache.current.get(instanceId);
      } else {
        // 캐시에 없으면 로드
        console.log('Loading SEG image for instance:', instanceId);
        const imageUrl = getDicomImageUrl(instanceId);
        const imageId = `wadouri:${imageUrl}`;
        image = await cornerstone.loadImage(imageId);

        // 캐시에 저장
        segImageCache.current.set(instanceId, image);
      }

      // 뷰어에 표시
      cornerstone.displayImage(element, image);

      // 윈도우 레벨 자동 조정
      const viewport = cornerstone.getDefaultViewportForImage(element, image);
      cornerstone.setViewport(element, viewport);

      // 강제 resize (렌더링 문제 해결)
      cornerstone.resize(element);

      console.log(`SEG Image ${index + 1} displayed successfully`);
    } catch (err: any) {
      const errorMessage = `Failed to load SEG image: ${err.message || err}`;
      setError(errorMessage);
      console.error('SEG load error:', err);
      console.error('Error stack:', err.stack);
    }
  };

  // Overlay 렌더링 (ReferencedSOPInstanceUID 기반 정확한 매칭)
  const renderOverlay = async (ctInstanceIndex: number) => {
    console.log('renderOverlay called with CT instance index:', ctInstanceIndex);

    if (!overlayCanvasRef.current || !viewerRef.current || !segInstances || segInstances.length === 0 || !segMetadata) {
      return;
    }

    const canvas = overlayCanvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Cornerstone의 현재 viewport 정보 가져오기
    const viewerElement = viewerRef.current;
    const viewport = cornerstone.getViewport(viewerElement);

    // Canvas 크기를 viewer 크기와 동일하게 설정
    canvas.width = viewerElement.clientWidth;
    canvas.height = viewerElement.clientHeight;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    console.log('Viewport info:', {
      scale: viewport.scale,
      translation: viewport.translation,
      canvasWidth: canvas.width,
      canvasHeight: canvas.height
    });

    try {
      // 현재 CT 인스턴스의 SOPInstanceUID 가져오기
      const currentCTInstance = instances[ctInstanceIndex];
      const currentSOPInstanceUID = currentCTInstance.MainDicomTags.SOPInstanceUID;

      if (!currentSOPInstanceUID) {
        console.warn('Current CT instance has no SOPInstanceUID');
        return;
      }

      console.log('Current CT SOPInstanceUID:', currentSOPInstanceUID);

      // PerFrameFunctionalGroupsSequence에서 매칭되는 프레임 찾기
      const perFrameSeq = segMetadata.PerFrameFunctionalGroupsSequence;
      if (!perFrameSeq) {
        console.warn('No PerFrameFunctionalGroupsSequence found in SEG metadata');
        return;
      }

      // 현재 CT에 매칭되는 모든 SEG 프레임 찾기 (여러 세그먼트가 있을 수 있음)
      const matchedFrameIndices: number[] = [];
      for (let frameIndex = 0; frameIndex < perFrameSeq.length; frameIndex++) {
        const frame = perFrameSeq[frameIndex];
        const derivationSeq = frame.DerivationImageSequence;

        if (derivationSeq && derivationSeq.length > 0) {
          const sourceSeq = derivationSeq[0].SourceImageSequence;

          if (sourceSeq) {
            // 여러 source image가 있을 수 있으므로 모두 확인
            for (const source of sourceSeq) {
              if (source.ReferencedSOPInstanceUID === currentSOPInstanceUID) {
                matchedFrameIndices.push(frameIndex);
                console.log(`Found matching SEG frame ${frameIndex} for CT SOPInstanceUID ${currentSOPInstanceUID}`);
                break;
              }
            }
          }
        }
      }

      if (matchedFrameIndices.length === 0) {
        console.warn('No matching SEG frames found for current CT instance');
        return;
      }

      console.log(`Total ${matchedFrameIndices.length} SEG frame(s) found for this CT slice`);

      // 모든 매칭된 프레임을 로드하고 합치기
      const segInstanceId = segInstances[0].ID;
      const imageUrl = getDicomImageUrl(segInstanceId);

      // 첫 번째 프레임으로 크기 확인
      const firstFrameId = `wadouri:${imageUrl}?frame=${matchedFrameIndices[0]}`;
      const firstImage = await cornerstone.loadImage(firstFrameId);
      const width = firstImage.width;
      const height = firstImage.height;

      // 합쳐진 픽셀 데이터 (모든 프레임의 세그먼트를 하나로 합침)
      const combinedPixelData = new Uint8Array(width * height);

      // 각 프레임을 로드하고 합치기
      for (const frameIndex of matchedFrameIndices) {
        const imageId = `wadouri:${imageUrl}?frame=${frameIndex}`;
        console.log('Loading SEG frame:', frameIndex);

        const segImage = await cornerstone.loadImage(imageId);
        const pixelData = segImage.getPixelData();

        // 메타데이터에서 이 프레임의 실제 세그먼트 번호 가져오기
        const frame = perFrameSeq[frameIndex];
        const segmentIdSeq = frame.SegmentIdentificationSequence;
        const segmentNumber = segmentIdSeq?.[0]?.ReferencedSegmentNumber || 1;

        console.log(`Frame ${frameIndex} segment number from metadata:`, segmentNumber);

        // 픽셀 데이터를 combinedPixelData에 합치기 (binary mask에 실제 세그먼트 번호 적용)
        for (let i = 0; i < pixelData.length; i++) {
          if (pixelData[i] > 0) {
            combinedPixelData[i] = segmentNumber; // 메타데이터의 세그먼트 번호 사용
          }
        }
      }

      // 합쳐진 픽셀 데이터 분석
      let minVal = Infinity;
      let maxVal = -Infinity;
      let nonZeroCount = 0;
      const segmentCounts: { [key: number]: number } = {};

      for (let i = 0; i < combinedPixelData.length; i++) {
        const val = combinedPixelData[i];
        if (val > 0) {
          nonZeroCount++;
          segmentCounts[val] = (segmentCounts[val] || 0) + 1;
        }
        if (val < minVal) minVal = val;
        if (val > maxVal) maxVal = val;
      }

      console.log('Combined pixel value range:', minVal, '-', maxVal);
      console.log('Combined non-zero pixels:', nonZeroCount);
      console.log('Combined segment pixel counts:', segmentCounts);
      console.log('Enabled segments:', Array.from(enabledSegments));

      if (nonZeroCount === 0) {
        console.warn('No segmentation data in combined frames');
        return;
      }

      // ImageData 생성 (RGBA)
      const imageData = ctx.createImageData(width, height);
      const data = imageData.data;

      // 세그먼트별 색상 매핑 (SegmentSequence 기반)
      const getSegmentColor = (segmentNumber: number): [number, number, number] => {
        if (segMetadata.SegmentSequence) {
          const segment = segMetadata.SegmentSequence.find(seg => seg.SegmentNumber === segmentNumber);
          if (segment?.RecommendedDisplayCIELabValue) {
            // CIELab to RGB 변환 (간단한 근사값 사용)
            // 실제로는 복잡한 변환이 필요하지만, 여기서는 기본 색상 사용
            console.log(`Segment ${segmentNumber} (${segment.SegmentLabel}): CIELab ${segment.RecommendedDisplayCIELabValue}`);
          }
        }

        // 기본 색상 매핑
        const colorMap: { [key: number]: [number, number, number] } = {
          1: [255, 0, 0],     // Red
          2: [0, 255, 0],     // Green
          3: [0, 0, 255],     // Blue
          4: [255, 255, 0],   // Yellow
          5: [255, 0, 255],   // Magenta
          6: [0, 255, 255],   // Cyan
        };

        return colorMap[segmentNumber] || [255, 255, 255]; // White for unknown segments
      };

      // 합쳐진 픽셀 데이터를 RGBA로 변환 (활성화된 세그먼트만 표시)
      for (let i = 0; i < combinedPixelData.length; i++) {
        const pixelValue = combinedPixelData[i];
        const idx = i * 4;

        if (pixelValue > 0 && enabledSegments.has(pixelValue)) {
          const [r, g, b] = getSegmentColor(pixelValue);
          data[idx] = r;
          data[idx + 1] = g;
          data[idx + 2] = b;
          data[idx + 3] = 180; // 70% 투명도
        } else {
          // 투명
          data[idx] = 0;
          data[idx + 1] = 0;
          data[idx + 2] = 0;
          data[idx + 3] = 0;
        }
      }

      // Canvas에 overlay 그리기 (Cornerstone viewport 변환 적용)
      const tempCanvas = document.createElement('canvas');
      tempCanvas.width = width;
      tempCanvas.height = height;
      const tempCtx = tempCanvas.getContext('2d');
      if (tempCtx) {
        tempCtx.putImageData(imageData, 0, 0);

        // Cornerstone의 viewport 변환을 적용하여 정확한 위치에 그리기
        ctx.save();
        ctx.imageSmoothingEnabled = false;

        // Viewport의 변환 적용 (scale, translation)
        const scale = viewport.scale;
        const translation = viewport.translation;

        // Canvas 중심점
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;

        // 변환 적용: 이동 -> 스케일
        ctx.translate(centerX, centerY);
        ctx.translate(translation.x, translation.y);
        ctx.scale(scale, scale);

        // 이미지를 중앙 기준으로 그리기
        ctx.drawImage(tempCanvas, -width / 2, -height / 2, width, height);

        ctx.restore();
        console.log('Overlay successfully rendered for frames:', matchedFrameIndices, 'with scale:', scale);
      }
    } catch (err) {
      console.error('Failed to render overlay:', err);
    }
  };

  // 이전/다음 이미지
  const handlePreviousImage = () => {
    if (currentInstanceIndex > 0) {
      const newIndex = currentInstanceIndex - 1;
      setCurrentInstanceIndex(newIndex);
      if (viewMode === '2d') {
        loadAndDisplayCTImage(instances[newIndex].ID, newIndex);
      } else {
        loadAndDisplaySegImage(instances[newIndex].ID, newIndex);
      }
    }
  };

  const handleNextImage = () => {
    if (currentInstanceIndex < instances.length - 1) {
      const newIndex = currentInstanceIndex + 1;
      setCurrentInstanceIndex(newIndex);
      if (viewMode === '2d') {
        loadAndDisplayCTImage(instances[newIndex].ID, newIndex);
      } else {
        loadAndDisplaySegImage(instances[newIndex].ID, newIndex);
      }
    }
  };

  // Overlay 토글
  const toggleOverlay = () => {
    const newShowOverlay = !showOverlay;
    setShowOverlay(newShowOverlay);

    if (newShowOverlay && selectedMask && segInstances.length > 0) {
      // Overlay 활성화 - 현재 슬라이스에 overlay 렌더링
      renderOverlay(currentInstanceIndex);
    } else if (!newShowOverlay && overlayCanvasRef.current) {
      // Overlay 비활성화 - canvas 클리어
      const canvas = overlayCanvasRef.current;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
  };

  // 세그먼트 토글
  const toggleSegment = (segmentNumber: number) => {
    setEnabledSegments((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(segmentNumber)) {
        newSet.delete(segmentNumber);
      } else {
        newSet.add(segmentNumber);
      }
      console.log('Toggled segment:', segmentNumber, 'New enabled segments:', Array.from(newSet));
      return newSet;
    });
  };

  return (
    <div style={{ padding: '20px', width: '100%', height: '100%', display: 'flex', flexDirection: 'column', boxSizing: 'border-box' }}>
      <h1 style={{ margin: '0 0 20px 0' }}>Orthanc DICOM Viewer</h1>

      {error && (
        <div
          style={{
            padding: '12px',
            backgroundColor: '#f8d7da',
            color: '#721c24',
            borderRadius: '4px',
            marginBottom: '20px',
          }}
        >
          Error: {error}
        </div>
      )}

      {preloadProgress > 0 && preloadProgress < 100 && (
        <div
          style={{
            padding: '12px',
            backgroundColor: '#d1ecf1',
            color: '#0c5460',
            borderRadius: '4px',
            marginBottom: '20px',
          }}
        >
          <div style={{ marginBottom: '8px' }}>Loading images: {preloadProgress}%</div>
          <div
            style={{
              width: '100%',
              height: '8px',
              backgroundColor: '#bee5eb',
              borderRadius: '4px',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                width: `${preloadProgress}%`,
                height: '100%',
                backgroundColor: '#17a2b8',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '280px 280px 1fr', gap: '20px', flex: 1, minHeight: 0 }}>
        {/* Study List */}
        <div
          style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '15px',
            backgroundColor: '#fff',
            maxHeight: '600px',
            overflowY: 'auto',
          }}
        >
          <h3>Studies</h3>
          {loading && studies.length === 0 && <p>Loading studies...</p>}
          {studies.map((study) => (
            <div
              key={study.ID}
              onClick={() => handleStudySelect(study)}
              style={{
                padding: '10px',
                margin: '5px 0',
                border: '1px solid #ddd',
                borderRadius: '4px',
                cursor: 'pointer',
                backgroundColor: selectedStudy?.ID === study.ID ? '#e7f3ff' : '#f8f9fa',
              }}
            >
              <div style={{ fontSize: '12px', fontWeight: 'bold' }}>
                {study.PatientMainDicomTags.PatientName || 'Unknown Patient'}
              </div>
              <div style={{ fontSize: '11px', color: '#666' }}>
                {study.MainDicomTags.StudyDate || 'N/A'}
              </div>
              <div style={{ fontSize: '11px', color: '#666' }}>
                {study.MainDicomTags.StudyDescription || 'No description'}
              </div>
            </div>
          ))}
        </div>

        {/* CT Series & Mask List */}
        <div
          style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '15px',
            backgroundColor: '#fff',
            maxHeight: '600px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '15px',
          }}
        >
          {/* CT Series */}
          <div>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '14px', fontWeight: 'bold' }}>CT Series</h3>
            {selectedStudy ? (
              ctSeries.length > 0 ? (
                ctSeries.map((ctItem) => (
                  <div
                    key={ctItem.ID}
                    onClick={() => handleCTSelect(ctItem)}
                    style={{
                      padding: '10px',
                      margin: '5px 0',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      backgroundColor: selectedCT?.ID === ctItem.ID ? '#e7f3ff' : '#f8f9fa',
                    }}
                  >
                    <div style={{ fontSize: '12px', fontWeight: 'bold' }}>
                      {ctItem.MainDicomTags.Modality || 'CT'}
                    </div>
                    <div style={{ fontSize: '11px', color: '#666' }}>
                      {ctItem.MainDicomTags.SeriesDescription || 'No description'}
                    </div>
                    <div style={{ fontSize: '11px', color: '#666' }}>
                      Series #{ctItem.MainDicomTags.SeriesNumber || 'N/A'}
                    </div>
                  </div>
                ))
              ) : (
                <p style={{ color: '#666', fontSize: '12px', margin: '5px 0' }}>No CT series</p>
              )
            ) : (
              <p style={{ color: '#666', fontSize: '12px', margin: '5px 0' }}>Select a study</p>
            )}
          </div>

          {/* Mask List - 선택된 CT와 연관된 SEG만 표시 */}
          <div style={{ borderTop: '1px solid #dee2e6', paddingTop: '15px' }}>
            <h3 style={{ margin: '0 0 10px 0', fontSize: '14px', fontWeight: 'bold' }}>Segmentation Masks</h3>
            {selectedCT && filteredSegSeries.length > 0 ? (
              filteredSegSeries.map((segItem) => (
                <div
                  key={segItem.ID}
                  onClick={() => handleMaskSelect(segItem)}
                  style={{
                    padding: '10px',
                    margin: '5px 0',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    backgroundColor: selectedMask?.ID === segItem.ID ? '#fff3cd' : '#f8f9fa',
                  }}
                >
                  <div style={{ fontSize: '12px', fontWeight: 'bold' }}>
                    {segItem.MainDicomTags.Modality || 'SEG'}
                  </div>
                  <div style={{ fontSize: '11px', color: '#666' }}>
                    {segItem.MainDicomTags.SeriesDescription || 'Segmentation'}
                  </div>
                </div>
              ))
            ) : (
              <p style={{ color: '#666', fontSize: '12px', margin: '5px 0' }}>
                {selectedCT ? 'No related segmentation masks' : 'Select CT first'}
              </p>
            )}
          </div>

          {/* Segment Controls - SEG가 선택되었을 때만 표시 */}
          {selectedMask && segMetadata?.SegmentSequence && segMetadata.SegmentSequence.length > 0 && (
            <div style={{ borderTop: '1px solid #dee2e6', paddingTop: '15px', marginTop: '15px' }}>
              <h3 style={{ margin: '0 0 10px 0', fontSize: '14px', fontWeight: 'bold' }}>Segment Labels</h3>
              {segMetadata.SegmentSequence.map((segment: SegmentInfo) => {
                const segmentNum = Number(segment.SegmentNumber);
                const isEnabled = enabledSegments.has(segmentNum);
                const colorMap: { [key: number]: string } = {
                  1: '#ff0000',
                  2: '#00ff00',
                  3: '#0000ff',
                  4: '#ffff00',
                  5: '#ff00ff',
                  6: '#00ffff',
                };
                const segmentColor = colorMap[segmentNum] || '#ffffff';

                return (
                  <div
                    key={segmentNum}
                    onClick={() => toggleSegment(segmentNum)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '8px',
                      margin: '5px 0',
                      border: '1px solid #ddd',
                      borderRadius: '4px',
                      cursor: 'pointer',
                      backgroundColor: isEnabled ? '#f0f8ff' : '#f8f9fa',
                      opacity: isEnabled ? 1 : 0.5,
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isEnabled}
                      onChange={() => toggleSegment(segmentNum)}
                      onClick={(e) => e.stopPropagation()}
                      style={{ marginRight: '8px', cursor: 'pointer' }}
                    />
                    <div
                      style={{
                        width: '16px',
                        height: '16px',
                        backgroundColor: segmentColor,
                        border: '1px solid #999',
                        marginRight: '8px',
                        borderRadius: '2px',
                      }}
                    />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '12px', fontWeight: 'bold' }}>
                        {segment.SegmentLabel}
                      </div>
                      {segment.SegmentDescription && (
                        <div style={{ fontSize: '10px', color: '#666' }}>
                          {segment.SegmentDescription}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* DICOM Viewer */}
        <div
          style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '15px',
            backgroundColor: '#000',
            display: 'flex',
            flexDirection: 'column',
            minHeight: 0,
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '10px',
              color: '#fff',
            }}
          >
            <h3 style={{ margin: 0, color: '#fff' }}>
              {viewMode === '2d' ? 'CT Image (2D)' : 'Segmentation Mask (3D)'}
              {showOverlay && <span style={{ fontSize: '14px', marginLeft: '10px', color: '#4ade80' }}>(Overlay Active)</span>}
            </h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {/* Overlay 토글 버튼 - CT와 Mask가 모두 선택되었을 때만 표시 */}
              {selectedCT && selectedMask && viewMode === '2d' && (
                <button
                  onClick={toggleOverlay}
                  style={{
                    padding: '5px 15px',
                    cursor: 'pointer',
                    backgroundColor: showOverlay ? '#f59e0b' : '#667eea',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    fontWeight: showOverlay ? 'bold' : 'normal',
                  }}
                >
                  {showOverlay ? 'Hide Overlay' : 'Show Overlay'}
                </button>
              )}

              {instances.length > 0 && (
                <div>
                  <button
                    onClick={handlePreviousImage}
                    disabled={currentInstanceIndex === 0}
                    style={{
                      padding: '5px 15px',
                      marginRight: '5px',
                      cursor: currentInstanceIndex === 0 ? 'not-allowed' : 'pointer',
                      backgroundColor: '#667eea',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                    }}
                  >
                    Previous
                  </button>
                  <span style={{ margin: '0 10px' }}>
                    {currentInstanceIndex + 1} / {instances.length}
                  </span>
                  <button
                    onClick={handleNextImage}
                    disabled={currentInstanceIndex === instances.length - 1}
                    style={{
                      padding: '5px 15px',
                      cursor: currentInstanceIndex === instances.length - 1 ? 'not-allowed' : 'pointer',
                      backgroundColor: '#667eea',
                      color: 'white',
                      border: 'none',
                      borderRadius: '4px',
                    }}
                  >
                    Next
                  </button>
                </div>
              )}
            </div>
          </div>

          <div
            ref={viewerRef}
            style={{
              width: '100%',
              flex: 1,
              backgroundColor: '#000',
              position: 'relative',
              minHeight: 0,
            }}
          >
            {/* Overlay Canvas - CT 이미지 위에 세그먼트 마스크 표시 */}
            <canvas
              ref={overlayCanvasRef}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none',
                zIndex: 10,
              }}
            />

            {!selectedCT && !selectedMask && (
              <div
                style={{
                  position: 'absolute',
                  top: '50%',
                  left: '50%',
                  transform: 'translate(-50%, -50%)',
                  color: '#666',
                  textAlign: 'center',
                  zIndex: 5,
                }}
              >
                <div>Select CT series for 2D view</div>
                <div style={{ marginTop: '10px' }}>or Segmentation mask for 3D view</div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OrthancViewer;
