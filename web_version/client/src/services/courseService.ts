import api from '@/lib/api';
import type { Course } from '@/types';

export interface StudentCourse extends Course {
    enrolled_at: string;
}

export const courseService = {
    getStudentCourses: async () => {
        const response = await api.get<StudentCourse[]>('/student/courses');
        return response.data;
    },

    getInstructorCourses: async () => {
        const response = await api.get<Course[]>('/instructor/courses');
        return response.data;
    },

    getSections: async () => {
        const response = await api.get<{ id: string; name: string }[]>('/sections');
        return response.data;
    }
};
