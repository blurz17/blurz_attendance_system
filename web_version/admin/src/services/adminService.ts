/* ─── Admin API Service ─── */
import api from '@/lib/api';
import type {
    UserListResponse, CreateUserRequest, UpdateUserRequest, BulkUploadResponse,
    DepartmentResponse, CreateDepartmentRequest, UpdateDepartmentRequest,
    SectionResponse, CreateSectionRequest, UpdateSectionRequest,
    CourseResponse, CreateCourseRequest, UpdateCourseRequest,
    EnrollStudentRequest,
} from '@/types';

// Helper to unwrap axios response
const get = <T>(url: string, params?: object) => api.get<T>(url, { params }).then(r => r.data);
const post = <T>(url: string, data?: any, config?: any) => api.post<T>(url, data, config).then(r => r.data);
const put = <T>(url: string, data: any) => api.put<T>(url, data).then(r => r.data);
const del = (url: string) => api.delete(url).then(r => r.data);

// ─── Users ───
export const userService = {
    list: (params?: { role?: string; skip?: number; limit?: number }) => get<UserListResponse>('/admin/users', params),
    get: (id: string) => get<any>(`/admin/users/${id}`),
    create: (data: CreateUserRequest) => post('/admin/users', data),
    update: (id: string, data: UpdateUserRequest) => put(`/admin/users/${id}`, data),
    deactivate: (id: string) => del(`/admin/users/${id}`),
    bulkUpload: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return post<BulkUploadResponse>('/admin/users/bulk', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
    },
};

// ─── Departments ───
export const departmentService = {
    list: () => get<DepartmentResponse[]>('/admin/departments'),
    get: (id: string) => get<DepartmentResponse>(`/admin/departments/${id}`),
    create: (data: CreateDepartmentRequest) => post('/admin/departments', data),
    update: (id: string, data: UpdateDepartmentRequest) => put(`/admin/departments/${id}`, data),
    delete: (id: string) => del(`/admin/departments/${id}`),
};

// ─── Sections ───
export const sectionService = {
    list: () => get<SectionResponse[]>('/admin/sections'),
    get: (id: string) => get<SectionResponse>(`/admin/sections/${id}`),
    create: (data: CreateSectionRequest) => post('/admin/sections', data),
    update: (id: string, data: UpdateSectionRequest) => put(`/admin/sections/${id}`, data),
    delete: (id: string) => del(`/admin/sections/${id}`),
};

// ─── Courses ───
export const courseService = {
    list: (params?: { year?: number; department_id?: string }) => get<CourseResponse[]>('/admin/courses', params),
    get: (id: string) => get<CourseResponse>(`/admin/courses/${id}`),
    create: (data: CreateCourseRequest) => post('/admin/courses', data),
    update: (id: string, data: UpdateCourseRequest) => put(`/admin/courses/${id}`, data),
    delete: (id: string) => del(`/admin/courses/${id}`),
};

// ─── Enrollment ───
export const enrollmentService = {
    enroll: (data: EnrollStudentRequest) => post('/admin/enrollments', data),
};
