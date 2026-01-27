import axios from 'axios';
import { API_BASE } from './apiConfig';

// Orthanc 서버 URL
const ORTHANC_URL = `${API_BASE}/orthanc`;

// Axios 클라이언트 (인증 제거)
const orthancClient = axios.create({
  baseURL: ORTHANC_URL,
});

/* ----------------------------------------
   Interfaces
---------------------------------------- */
export interface OrthancStudy {
  ID: string;
  MainDicomTags: {
    StudyDate?: string;
    StudyDescription?: string;
    StudyInstanceUID?: string;
    PatientID?: string;
    PatientName?: string;
  };
  PatientMainDicomTags: {
    PatientID?: string;
    PatientName?: string;
    PatientBirthDate?: string;
    PatientSex?: string;
  };
  Series?: string[];
}

export interface OrthancSeries {
  ID: string;
  MainDicomTags: {
    Modality?: string;
    SeriesDescription?: string;
    SeriesInstanceUID?: string;
    SeriesNumber?: string;
  };
  Instances?: string[];
}

export interface SegmentInfo {
  SegmentNumber: number;
  SegmentLabel: string;
  SegmentDescription?: string;
  RecommendedDisplayCIELabValue?: string;
}

export interface PerFrameFunctionalGroupsSequence {
  DerivationImageSequence?: Array<{
    SourceImageSequence?: Array<{
      ReferencedSOPInstanceUID?: string;
    }>;
  }>;
  SegmentIdentificationSequence?: Array<{
    ReferencedSegmentNumber?: number;
  }>;
}

export interface SegmentationMetadata {
  ReferencedSeriesSequence?: Array<{
    SeriesInstanceUID?: string;
  }>;
  SegmentSequence?: SegmentInfo[];
  PerFrameFunctionalGroupsSequence?: PerFrameFunctionalGroupsSequence[];
}

export interface OrthancInstance {
  ID: string;
  MainDicomTags: {
    InstanceNumber?: string;
    SOPInstanceUID?: string;
  };
  FileSize?: number;
}

/* ----------------------------------------
   1) 모든 Study 목록 가져오기
---------------------------------------- */
export const getStudies = async (): Promise<OrthancStudy[]> => {
  try {
    const response = await orthancClient.get(`/studies`);
    const studyIds: string[] = response.data;

    const studies = await Promise.all(
      studyIds.map(async (id) => {
        const detail = await orthancClient.get(`/studies/${id}`);
        return detail.data;
      })
    );

    return studies;
  } catch (error) {
    console.error('Failed to fetch studies:', error);
    throw error;
  }
};

/* ----------------------------------------
   2) 특정 Study의 Series 목록 가져오기
---------------------------------------- */
export const getSeriesByStudy = async (studyId: string): Promise<OrthancSeries[]> => {
  try {
    const response = await orthancClient.get(`/studies/${studyId}`);
    const seriesIds: string[] = response.data.Series || [];

    const series = await Promise.all(
      seriesIds.map(async (id) => {
        const detail = await orthancClient.get(`/series/${id}`);
        return detail.data;
      })
    );

    return series;
  } catch (error) {
    console.error('Failed to fetch series:', error);
    throw error;
  }
};

/* ----------------------------------------
   3) 특정 Series의 Instance 목록 가져오기
---------------------------------------- */
export const getInstancesBySeries = async (seriesId: string): Promise<OrthancInstance[]> => {
  try {
    const response = await orthancClient.get(`/series/${seriesId}`);
    const instanceIds: string[] = response.data.Instances || [];

    const instances = await Promise.all(
      instanceIds.map(async (id) => {
        const detail = await orthancClient.get(`/instances/${id}`);
        return detail.data;
      })
    );

    return instances;
  } catch (error) {
    console.error('Failed to fetch instances:', error);
    throw error;
  }
};

/* ----------------------------------------
   4) DICOM 파일 다운로드 URL
---------------------------------------- */
export const getDicomImageUrl = (instanceId: string): string => {
  return `${ORTHANC_URL}/instances/${instanceId}/file`;
};

/* ----------------------------------------
   5) Preview PNG URL
---------------------------------------- */
export const getPreviewImageUrl = (instanceId: string): string => {
  return `${ORTHANC_URL}/instances/${instanceId}/preview`;
};

/* ----------------------------------------
   6) SEG Series의 전체 메타데이터 가져오기
---------------------------------------- */
export const getSegmentationMetadata = async (seriesId: string): Promise<SegmentationMetadata | null> => {
  try {
    const response = await orthancClient.get(`/series/${seriesId}`);
    const instanceIds: string[] = response.data.Instances || [];

    if (instanceIds.length === 0) {
      return null;
    }

    // 첫 번째 instance의 simplified tags에서 전체 메타데이터 가져오기
    const instanceDetail = await orthancClient.get(`/instances/${instanceIds[0]}/simplified-tags`);
    const tags = instanceDetail.data;

    const metadata: SegmentationMetadata = {};

    // ReferencedSeriesSequence 추출
    if (tags.ReferencedSeriesSequence) {
      metadata.ReferencedSeriesSequence = Array.isArray(tags.ReferencedSeriesSequence)
        ? tags.ReferencedSeriesSequence
        : [tags.ReferencedSeriesSequence];
    }

    // SegmentSequence 추출
    if (tags.SegmentSequence) {
      const segmentSequence = Array.isArray(tags.SegmentSequence)
        ? tags.SegmentSequence
        : [tags.SegmentSequence];

      metadata.SegmentSequence = segmentSequence.map((seg: any) => ({
        SegmentNumber: Number(seg.SegmentNumber),
        SegmentLabel: seg.SegmentLabel || '',
        SegmentDescription: seg.SegmentDescription,
        RecommendedDisplayCIELabValue: seg.RecommendedDisplayCIELabValue,
      }));
    }

    // PerFrameFunctionalGroupsSequence 추출
    if (tags.PerFrameFunctionalGroupsSequence) {
      const perFrameSequence = Array.isArray(tags.PerFrameFunctionalGroupsSequence)
        ? tags.PerFrameFunctionalGroupsSequence
        : [tags.PerFrameFunctionalGroupsSequence];

      metadata.PerFrameFunctionalGroupsSequence = perFrameSequence.map((frame: any) => {
        const result: PerFrameFunctionalGroupsSequence = {};

        // DerivationImageSequence 추출
        const derivationSeq = frame.DerivationImageSequence;
        if (derivationSeq) {
          const derivationArray = Array.isArray(derivationSeq) ? derivationSeq : [derivationSeq];

          result.DerivationImageSequence = derivationArray.map((deriv: any) => {
            const sourceSeq = deriv.SourceImageSequence;

            if (sourceSeq) {
              const sourceArray = Array.isArray(sourceSeq) ? sourceSeq : [sourceSeq];

              return {
                SourceImageSequence: sourceArray.map((source: any) => ({
                  ReferencedSOPInstanceUID: source.ReferencedSOPInstanceUID,
                })),
              };
            }

            return { SourceImageSequence: [] };
          });
        } else {
          result.DerivationImageSequence = [];
        }

        // SegmentIdentificationSequence 추출
        const segmentIdSeq = frame.SegmentIdentificationSequence;
        if (segmentIdSeq) {
          const segmentIdArray = Array.isArray(segmentIdSeq) ? segmentIdSeq : [segmentIdSeq];

          result.SegmentIdentificationSequence = segmentIdArray.map((segId: any) => ({
            ReferencedSegmentNumber: Number(segId.ReferencedSegmentNumber),
          }));
        }

        return result;
      });
    }

    console.log('Segmentation metadata extracted:', metadata);
    return Object.keys(metadata).length > 0 ? metadata : null;
  } catch (error) {
    console.error('Failed to fetch segmentation metadata:', error);
    return null;
  }
};
