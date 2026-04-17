import api from '@/lib/api';
import type { ActivationRequest } from '@/types';

export const authService = {
    activateAccount: async (token: string, data: ActivationRequest) => {
        const response = await api.post(`/auth/verify/${token}`, data);
        return response.data;
    },

    resendVerification: async (email: string) => {
        const response = await api.post('/auth/resend-verification', { email });
        return response.data;
    }
};
