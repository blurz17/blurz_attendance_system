import api from '@/lib/api';
import type {
    GenerateQRRequest,
    GenerateQRResponse,
    ScanQRResponse,
    AttendanceRecord,
    CourseAttendanceMatrix
} from '@/types';

export const attendanceService = {
    generateQR: async (data: GenerateQRRequest) => {
        const response = await api.post<GenerateQRResponse>('/attendance/generate', data);
        return response.data;
    },

    scanQR: async (token: string) => {
        const response = await api.post<ScanQRResponse>('/attendance/scan', { token });
        return response.data;
    },

    getMyRecords: async (courseId?: string) => {
        const response = await api.get<AttendanceRecord[]>('/attendance/my-records', {
            params: { course_id: courseId }
        });
        return response.data;
    },

    getCourseReport: async (courseId: string) => {
        const response = await api.get(`/attendance/report/${courseId}`);
        return response.data;
    },

    getFullCourseReport: async (courseId: string) => {
        const response = await api.get<CourseAttendanceMatrix>(`/attendance/report/full/${courseId}`);
        return response.data;
    }
};
