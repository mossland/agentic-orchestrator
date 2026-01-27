import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

type User = {
  id: number;
  name: string;
};

type Portfolio = {
  id: number;
  userId: number;
  assets: Record<string, number>;
};

enum ApiErrorCodes {
  Unauthorized = 401,
  Forbidden = 403,
  NotFound = 404,
}

class ApiError extends Error {
  constructor(public status: number, message?: string) {
    super(message);
    this.name = 'ApiError';
  }
}

const client: AxiosInstance = axios.create({
  baseURL: process.env.API_BASE_URL || 'http://localhost:3000',
});

client.interceptors.request.use((config: AxiosRequestConfig) => {
  const token = localStorage.getItem('authToken');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, error => Promise.reject(error));

client.interceptors.response.use(
  response => response,
  (error) => {
    if (!error.response) throw error;

    const { status } = error.response;
    let message: string | undefined;
    switch (status) {
      case ApiErrorCodes.Unauthorized:
        message = 'Unauthorized';
        break;
      case ApiErrorCodes.Forbidden:
        message = 'Forbidden';
        break;
      case ApiErrorCodes.NotFound:
        message = 'Not Found';
        break;
      default:
        message = error.message;
    }
    throw new ApiError(status, message);
  },
);

export const getUsers = async (): Promise<User[]> => {
  const response: AxiosResponse<User[]> = await client.get('/api/users');
  return response.data;
};

export const createPortfolio = async (portfolio: Omit<Portfolio, 'id'>): Promise<Portfolio> => {
  const response: AxiosResponse<Portfolio> = await client.post('/api/portfolios', portfolio);
  return response.data;
};

export const rebalancePortfolio = async (portfolioId: number): Promise<void> => {
  await client.put(`/api/portfolios/${portfolioId}/rebalance`);
};