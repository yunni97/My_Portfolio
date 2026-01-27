import React, { useState, useEffect, useRef } from 'react';
import * as cornerstone from 'cornerstone-core';
import { initializeCornerstone } from '../setupCornerstone';
import {
  getStudies,
  getSeriesByStudy,
  getInstancesBySeries,
  getDicomImageUrl,
  type OrthancStudy,
  type OrthancSeries,
  type OrthancInstance,
} from '../services/orthanc_api';

// Cornerstone 초기화
let isInitialized = false;
if (!isInitialized) {
  initializeCornerstone();
  isInitialized = true;
}

const SegmentationViewer: React.FC = () => {
  const [studies, setStudies] = useState<OrthancStudy[]>([]);
  const [selectedStudy, setSelectedStudy] = useState<OrthancStudy | null>(null);
  const [series, setSeries] = useState<OrthancSeries[]>([]);
  const [selectedSeries, setSelectedSeries] = useState<OrthancSeries | null>(null);
  const [_instances, setInstances] = useState<OrthancInstance[]>([]);
  const [currentSlice, setCurrentSlice] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 3개의 뷰어 (Axial, Sagittal, Coronal)
  const axialRef = useRef<HTMLDivElement>(null);
  const sagittalRef = useRef<HTMLDivElement>(null);
  const coronalRef = useRef<HTMLDivElement>(null);

  const [viewersEnabled, setViewersEnabled] = useState({
    axial: false,
    sagittal: false,
    coronal: false,
  });

  const [volumeData, setVolumeData] = useState<any[]>([]);

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

  // Study 선택 시 Series 로드
  const handleStudySelect = async (study: OrthancStudy) => {
    setSelectedStudy(study);
    setSelectedSeries(null);
    setInstances([]);
    setLoading(true);
    setError(null);

    try {
      const seriesList = await getSeriesByStudy(study.ID);
      setSeries(seriesList);
    } catch (err) {
      setError('Failed to load series');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Series 선택 시 Instance 로드 및 Volume 구성
  const handleSeriesSelect = async (seriesItem: OrthancSeries) => {
    setSelectedSeries(seriesItem);
    setLoading(true);
    setError(null);

    try {
      const instanceList = await getInstancesBySeries(seriesItem.ID);
      setInstances(instanceList);
      setCurrentSlice(Math.floor(instanceList.length / 2));

      // 모든 슬라이스 로드
      await loadVolumeData(instanceList);
    } catch (err) {
      setError('Failed to load instances');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Viewer 초기화
  useEffect(() => {
    if (axialRef.current && !viewersEnabled.axial) {
      try {
        cornerstone.enable(axialRef.current);
        setViewersEnabled((prev) => ({ ...prev, axial: true }));
      } catch (err) {
        console.error('Failed to enable axial viewer:', err);
      }
    }
    if (sagittalRef.current && !viewersEnabled.sagittal) {
      try {
        cornerstone.enable(sagittalRef.current);
        setViewersEnabled((prev) => ({ ...prev, sagittal: true }));
      } catch (err) {
        console.error('Failed to enable sagittal viewer:', err);
      }
    }
    if (coronalRef.current && !viewersEnabled.coronal) {
      try {
        cornerstone.enable(coronalRef.current);
        setViewersEnabled((prev) => ({ ...prev, coronal: true }));
      } catch (err) {
        console.error('Failed to enable coronal viewer:', err);
      }
    }

    return () => {
      if (axialRef.current && viewersEnabled.axial) {
        try {
          cornerstone.disable(axialRef.current);
        } catch (err) {
          console.error('Failed to disable axial viewer:', err);
        }
      }
      if (sagittalRef.current && viewersEnabled.sagittal) {
        try {
          cornerstone.disable(sagittalRef.current);
        } catch (err) {
          console.error('Failed to disable sagittal viewer:', err);
        }
      }
      if (coronalRef.current && viewersEnabled.coronal) {
        try {
          cornerstone.disable(coronalRef.current);
        } catch (err) {
          console.error('Failed to disable coronal viewer:', err);
        }
      }
    };
  }, [viewersEnabled]);

  // Volume 데이터 로드
  const loadVolumeData = async (instanceList: OrthancInstance[]) => {
    const loadedImages = [];

    for (const instance of instanceList) {
      try {
        const imageUrl = getDicomImageUrl(instance.ID);
        const imageId = `wadouri:${imageUrl}`;
        const image = await cornerstone.loadImage(imageId);
        loadedImages.push(image);
      } catch (err) {
        console.error('Failed to load slice:', err);
      }
    }

    setVolumeData(loadedImages);

    // 첫 번째 이미지를 axial view에 표시
    if (loadedImages.length > 0 && axialRef.current) {
      displayAxialSlice(Math.floor(loadedImages.length / 2));
    }
  };

  // Axial slice 표시
  const displayAxialSlice = (sliceIndex: number) => {
    if (!axialRef.current || !volumeData.length || !viewersEnabled.axial) return;

    try {
      const image = volumeData[sliceIndex];
      cornerstone.displayImage(axialRef.current, image);
      const viewport = cornerstone.getDefaultViewportForImage(axialRef.current, image);
      cornerstone.setViewport(axialRef.current, viewport);
      cornerstone.resize(axialRef.current);
      setCurrentSlice(sliceIndex);
    } catch (err) {
      console.error('Failed to display axial slice:', err);
    }
  };

  // 슬라이스 변경
  const handleSliceChange = (delta: number) => {
    const newSlice = Math.max(0, Math.min(volumeData.length - 1, currentSlice + delta));
    displayAxialSlice(newSlice);
  };

  return (
    <div style={{ padding: '20px', width: '100%', height: '100%', display: 'flex', flexDirection: 'column', boxSizing: 'border-box' }}>
      <h1 style={{ margin: '0 0 20px 0' }}>3D Segmentation Viewer</h1>

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

      <div style={{ display: 'grid', gridTemplateColumns: '280px 280px 1fr', gap: '20px', flex: 1, minHeight: 0 }}>
        {/* Study List */}
        <div
          style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '15px',
            backgroundColor: '#fff',
            maxHeight: '100%',
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
            </div>
          ))}
        </div>

        {/* Series List */}
        <div
          style={{
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            padding: '15px',
            backgroundColor: '#fff',
            maxHeight: '100%',
            overflowY: 'auto',
          }}
        >
          <h3>Series</h3>
          {selectedStudy ? (
            series.length > 0 ? (
              series.map((seriesItem) => (
                <div
                  key={seriesItem.ID}
                  onClick={() => handleSeriesSelect(seriesItem)}
                  style={{
                    padding: '10px',
                    margin: '5px 0',
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    backgroundColor: selectedSeries?.ID === seriesItem.ID ? '#e7f3ff' : '#f8f9fa',
                  }}
                >
                  <div style={{ fontSize: '12px', fontWeight: 'bold' }}>
                    {seriesItem.MainDicomTags.Modality || 'Unknown'}
                  </div>
                  <div style={{ fontSize: '11px', color: '#666' }}>
                    {seriesItem.MainDicomTags.SeriesDescription || 'No description'}
                  </div>
                </div>
              ))
            ) : (
              <p style={{ color: '#666', fontSize: '12px' }}>No series available</p>
            )
          ) : (
            <p style={{ color: '#666', fontSize: '12px' }}>Select a study</p>
          )}
        </div>

        {/* 3D Viewer Grid */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '15px',
            minHeight: 0,
          }}
        >
          {/* Controls */}
          {volumeData.length > 0 && (
            <div
              style={{
                backgroundColor: '#fff',
                padding: '10px 15px',
                borderRadius: '8px',
                border: '1px solid #dee2e6',
                display: 'flex',
                alignItems: 'center',
                gap: '15px',
              }}
            >
              <span style={{ fontWeight: 'bold', color: '#333' }}>Slice Navigation:</span>
              <button
                onClick={() => handleSliceChange(-10)}
                style={{
                  padding: '5px 15px',
                  cursor: currentSlice < 10 ? 'not-allowed' : 'pointer',
                  backgroundColor: '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                }}
                disabled={currentSlice < 10}
              >
                -10
              </button>
              <button
                onClick={() => handleSliceChange(-1)}
                style={{
                  padding: '5px 15px',
                  cursor: currentSlice === 0 ? 'not-allowed' : 'pointer',
                  backgroundColor: '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                }}
                disabled={currentSlice === 0}
              >
                -1
              </button>
              <span style={{ margin: '0 10px', minWidth: '100px', textAlign: 'center' }}>
                {currentSlice + 1} / {volumeData.length}
              </span>
              <button
                onClick={() => handleSliceChange(1)}
                style={{
                  padding: '5px 15px',
                  cursor: currentSlice === volumeData.length - 1 ? 'not-allowed' : 'pointer',
                  backgroundColor: '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                }}
                disabled={currentSlice === volumeData.length - 1}
              >
                +1
              </button>
              <button
                onClick={() => handleSliceChange(10)}
                style={{
                  padding: '5px 15px',
                  cursor: currentSlice >= volumeData.length - 10 ? 'not-allowed' : 'pointer',
                  backgroundColor: '#667eea',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                }}
                disabled={currentSlice >= volumeData.length - 10}
              >
                +10
              </button>
              <input
                type="range"
                min="0"
                max={volumeData.length - 1}
                value={currentSlice}
                onChange={(e) => displayAxialSlice(parseInt(e.target.value))}
                style={{ flex: 1 }}
              />
            </div>
          )}

          {/* Axial View (Main) */}
          <div
            style={{
              border: '1px solid #dee2e6',
              borderRadius: '8px',
              padding: '15px',
              backgroundColor: '#000',
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              minHeight: 0,
            }}
          >
            <h3 style={{ margin: '0 0 10px 0', color: '#fff' }}>Axial View</h3>
            <div
              ref={axialRef}
              style={{
                width: '100%',
                flex: 1,
                backgroundColor: '#000',
                position: 'relative',
                minHeight: 0,
              }}
            >
              {!selectedSeries && (
                <div
                  style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: 'translate(-50%, -50%)',
                    color: '#666',
                  }}
                >
                  Select a series to view segmentation
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SegmentationViewer;
