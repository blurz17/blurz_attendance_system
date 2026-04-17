import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import api from '@/lib/api';
import type { AuthUser, TokenResponse, LoginRequest } from '@/types';

interface AuthContextType {
    user: AuthUser | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;
    login: (credentials: LoginRequest) => Promise<void>;
    logout: () => Promise<void>;
    clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<AuthUser | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Check for existing session on mount
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (!token) { setIsLoading(false); return; }

        api.get<AuthUser>('/admin/auth/me')
            .then(res => setUser(res.data))
            .catch(() => localStorage.clear())
            .finally(() => setIsLoading(false));
    }, []);

    const login = async (credentials: LoginRequest) => {
        setIsLoading(true);
        setError(null);
        try {
            const res = await api.post<TokenResponse>('/admin/auth/login', credentials);
            localStorage.setItem('access_token', res.data.access_token);
            localStorage.setItem('refresh_token', res.data.refresh_token);
            const userRes = await api.get<AuthUser>('/admin/auth/me');
            setUser(userRes.data);
        } catch (err: unknown) {
            const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
                || 'Login failed. Please check your credentials.';
            setError(msg);
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    };

    const logout = async () => {
        try { await api.post('/admin/auth/logout'); } catch { /* ignore */ }
        localStorage.clear();
        setUser(null);
        setError(null);
    };

    return (
        <AuthContext.Provider value={{
            user, isAuthenticated: !!user, isLoading, error,
            login, logout, clearError: () => setError(null),
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
    return ctx;
}
