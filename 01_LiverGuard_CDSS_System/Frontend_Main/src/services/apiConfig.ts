import axios from 'axios';

// 환경 변수에서 API URL 가져오기
export const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9000';
export const API_BASE_URL = `${API_BASE}/api`;
export const ADMIN_URL = `${API_BASE}/admin/`;
export const BENTOML_URL = import.meta.env.VITE_BENTOML_URL || 'http://localhost:3000';
export const ORTHANC_URL = import.meta.env.VITE_ORTHANC_URL || 'http://localhost:8042';

// axios 인스턴스 생성
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 (필요시 토큰 추가 등)
apiClient.interceptors.request.use(
  (config) => {
    // 예: Authorization 헤더 추가
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 (에러 핸들링)
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // 서버가 응답을 반환한 경우
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      // 요청이 전송되었지만 응답이 없는 경우
      console.error('No response received:', error.request);
    } else {
      // 요청 설정 중 오류 발생
      console.error('Error setting up request:', error.message);
    }
    return Promise.reject(error);
  }
);
