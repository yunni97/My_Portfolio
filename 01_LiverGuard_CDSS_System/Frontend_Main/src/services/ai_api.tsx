import { AxiosError } from 'axios';
import { apiClient } from './apiConfig';

interface LassoCoxResponse {
  success: boolean;
  prediction: any;
  input_features: number[];
}

interface ErrorResponse {
  error: string;
}

export const lassoCoxMultimodal = async (): Promise<LassoCoxResponse> => {
  try {
    const response = await apiClient.post<LassoCoxResponse>('/ai/lasso_cox_multimodal/');
    return response.data;
  } catch (error) {
    const axiosError = error as AxiosError<ErrorResponse>;
    throw new Error(axiosError.response?.data?.error || 'API request failed');
  }
};
