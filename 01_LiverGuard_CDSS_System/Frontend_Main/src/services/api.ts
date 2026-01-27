// API 기본 URL - apiConfig.ts에서 가져오기
import { API_BASE_URL } from './apiConfig';
export { API_BASE_URL };

// API 응답 타입 정의
export interface LoginResponse {
  success: boolean;
  message: string;
  data?: {
    doctor_id: number;
    name: string;
    email: string;
    phone: string;
    department: string | null;
    department_code: string | null;
    position: string | null;
    status: string;
    sex: string;
  };
}

// 로그인 API 호출
export const loginAPI = async (userId: string, password: string): Promise<LoginResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userId,
        password,
      }),
    });

    const data: LoginResponse = await response.json();

    if (!response.ok) {
      throw new Error(data.message || '로그인에 실패했습니다.');
    }

    return data;
  } catch (error) {
    if (error instanceof Error) {
      throw error;
    }
    throw new Error('네트워크 오류가 발생했습니다.');
  }
};
