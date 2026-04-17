/* ─── TypeScript types mirroring the backend schemas ─── */

export type UserRole = 'student' | 'professor' | 'admin';

// ─── Auth ───
export interface LoginRequest { email: string; password: string; }
export interface ActivationRequest { password: string; confirm_password: string; }

export interface TokenResponse {
    message: string;
    access_token: string;
    refresh_token: string;
    user_id: string;
    email: string;
    role: UserRole;
}

export interface AuthUser {
    id: string;
    university_id: string;
    full_name: string;
    email: string;
    role: UserRole;
    is_active: boolean;
    year?: number;
    section_id?: string;
    department_id?: string;
}

// ─── Academic ───
export interface Course {
    id: string;
    name: string;
    year: number;
    department_id: string | null;
    enrolled_at?: string;
}

export interface Department { id: string; name: string; }
export interface Section { id: string; name: string; }

// ─── Attendance ───
export interface AttendanceRecord {
    id: string;
    scanned_at: string;
    week_number: number;
    course_name: string;
}

export interface GenerateQRRequest {
    course_id: string;
    week_number: number;
    expiry_minutes: number;
    section_id?: string;
}

export interface GenerateQRResponse {
    qr_code_id: string;
    token: string;
    expires_at: string;
    course_id: string;
    week_number: number;
    section_id?: string;
}

export interface ScanQRRequest { token: string; }
export interface ScanQRResponse { message: string; }

export interface AttendeeInfo { id: string; name: string; university_id: string; }
export interface SessionInfo { id: string; week_number: number; generated_at: string; }

export interface CourseAttendanceMatrix {
    course_id: string;
    course_name: string;
    students: AttendeeInfo[];
    sessions: SessionInfo[];
    attendance: Record<string, Record<string, boolean>>;
}

// ─── Quiz ───
export interface Choice { id: string; text: string; is_correct: boolean; }

export interface Question {
    id: string;
    text: string;
    order_index: number;
    choices: Choice[];
}

export interface Quiz {
    id: string;
    title: string;
    course_id: string;
    course_name: string;
    created_at: string;
    due_date: string | null;
}

export interface QuizListItem {
    id: string;
    title: string;
    course_id: string;
    course_name: string;
    due_date: string | null;
    question_count: number;
    is_submitted: boolean;
    score: number | null;
}

export interface QuizDetail extends Quiz { questions: Question[]; }

export interface CreateQuizRequest {
    title: string;
    course_id: string;
    due_date?: string | null;
    target_section_id?: string | null;
    questions: {
        text: string;
        order_index: number;
        choices: { text: string; is_correct: boolean; }[];
    }[];
}

// Unified submission types (merged duplicates)
export interface QuizSubmissionRequest {
    answers: { question_id: string; chosen_choice_id: string; }[];
}

export interface SubmitQuizResponse {
    message: string;
    submission_id: string;
    score: number;
}

export interface InstructorQuizSubmission {
    student_id: string;
    student_name: string;
    university_id: string;
    score: number;
    submitted_at: string;
}

export interface QuizSubmissionsResponse {
    quiz_id: string;
    quiz_title: string;
    submissions: InstructorQuizSubmission[];
}
