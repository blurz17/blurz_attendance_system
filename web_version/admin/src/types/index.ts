/* ─── TypeScript types mirroring the backend schemas ─── */

export type UserRole = 'student' | 'professor' | 'admin';

// ─── Auth ───
export interface LoginRequest { email: string; password: string; }

export interface TokenResponse {
    message: string;
    access_token: string;
    refresh_token: string;
    user_id: string;
    email: string;
    role: string;
}

export interface AuthUser {
    id: string;
    university_id: string;
    full_name: string;
    email: string;
    role: UserRole;
    is_active: boolean;
    created_at?: string;
}

// ─── User Management ───
export interface CreateUserRequest {
    university_id: string;
    id_card: string;
    full_name: string;
    email: string;
    role: UserRole;
    year?: number;
    section_id?: string;
    department_id?: string;
    course_ids?: string[];
}

export interface UpdateUserRequest {
    full_name?: string;
    email?: string;
    year?: number;
    section_id?: string;
    department_id?: string;
    is_active?: boolean;
}

export interface UserResponse {
    id: string;
    university_id: string;
    id_card: string;
    full_name: string;
    email: string;
    role: UserRole;
    is_active: boolean;
    year?: number;
    section_id?: string;
    department_id?: string;
    created_at?: string;
}

export interface UserListResponse { users: UserResponse[]; total: number; }

// ─── Bulk Upload ───
export interface BulkUploadResponse {
    total_rows: number;
    succeeded: number;
    failed: number;
    results: { row_number: number; university_id?: string; success: boolean; error?: string; }[];
}

// ─── Department & Section ───
export interface DepartmentResponse { id: string; name: string; }
export interface CreateDepartmentRequest { name: string; }
export interface UpdateDepartmentRequest { name: string; }

export interface SectionResponse { id: string; name: string; }
export interface CreateSectionRequest { name: string; }
export interface UpdateSectionRequest { name: string; }

// ─── Course ───
export interface CourseResponse {
    id: string;
    name: string;
    year: number;
    department_id?: string;
    professor_ids: string[];
}

export interface CreateCourseRequest {
    name: string;
    year: number;
    department_id?: string;
    professor_ids: string[];
}

export interface UpdateCourseRequest {
    name?: string;
    year?: number;
    department_id?: string;
    professor_ids?: string[];
}

// ─── Enrollment ───
export interface EnrollStudentRequest { student_id: string; course_id: string; }
