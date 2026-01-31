import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import { InsurancePolicy, Trade, NewInsurancePolicy } from './models';

type ErrorResponse = {
    message: string;
};

enum ApiErrorType {
    NetworkError,
    ServerError,
}

class ApiError extends Error {
    type: ApiErrorType;

    constructor(message: string, type: ApiErrorType) {
        super(message);
        this.type = type;
    }
}

const axiosInstance: AxiosInstance = axios.create({
    baseURL: process.env.API_BASE_URL || 'http://localhost:3000',
});

axiosInstance.interceptors.request.use((config: AxiosRequestConfig) => {
    const token = localStorage.getItem('authToken');
    if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, error => Promise.reject(error));

axiosInstance.interceptors.response.use(response => response, error => {
    if (!error.response) {
        throw new ApiError('Network Error', ApiErrorType.NetworkError);
    } else {
        const { status } = error.response;
        let message: string;

        try {
            message = (error.response.data as ErrorResponse).message;
        } catch (_) {
            message = 'Unknown Server Error';
        }

        if (status >= 500) {
            throw new ApiError(message, ApiErrorType.ServerError);
        }
    }
});

class ApiService {
    private userId: string;

    constructor(userId: string) {
        this.userId = userId;
    }

    async getInsurancePolicies(): Promise<InsurancePolicy[]> {
        const response = await axiosInstance.get(`/api/users/${this.userId}/insurance-policies`);
        return response.data as InsurancePolicy[];
    }

    async purchaseInsurancePolicy(policy: NewInsurancePolicy): Promise<InsurancePolicy> {
        const response = await axiosInstance.post(`/api/users/${this.userId}/insurance-policies`, policy);
        return response.data as InsurancePolicy;
    }

    async getTrades(): Promise<Trade[]> {
        const response = await axiosInstance.get(`/api/users/${this.userId}/trades`);
        return response.data as Trade[];
    }
}

export default ApiService;