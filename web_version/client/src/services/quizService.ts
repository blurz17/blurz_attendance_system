import api from '@/lib/api';
import type { QuizListItem, QuizDetail, CreateQuizRequest, QuizSubmissionRequest, SubmitQuizResponse, QuizSubmissionsResponse } from '@/types';

export const quizService = {
    getAvailableQuizzes: async () => {
        const response = await api.get<QuizListItem[]>('/quiz/available');
        return response.data;
    },

    getInstructorQuizzes: async () => {
        const response = await api.get<QuizListItem[]>('/quiz/instructor');
        return response.data;
    },

    createQuiz: async (data: CreateQuizRequest) => {
        const response = await api.post('/quiz/create', data);
        return response.data;
    },

    getQuizDetails: async (id: string) => {
        const response = await api.get<QuizDetail>(`/quiz/${id}`);
        return response.data;
    },

    submitQuiz: async (quizId: string, data: QuizSubmissionRequest) => {
        const response = await api.post<SubmitQuizResponse>(`/quiz/${quizId}/submit`, data);
        return response.data;
    },

    getQuizSubmissions: async (quizId: string) => {
        const response = await api.get<QuizSubmissionsResponse>(`/quiz/instructor/submissions/${quizId}`);
        return response.data;
    }
};
