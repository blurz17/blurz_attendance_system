import { Navigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

interface ProtectedRouteProps {
    children: React.ReactNode;
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
    const { isAuthenticated, isLoading } = useAuth();

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen bg-surface">
                <div className="flex flex-col items-center gap-4">
                    <div className="w-12 h-12 rounded-xl gradient-primary animate-pulse flex items-center justify-center">
                        <span className="text-white font-bold">B</span>
                    </div>
                    <div className="flex gap-1">
                        <div className="w-2 h-2 rounded-full bg-primary-500 animate-bounce [animation-delay:0ms]" />
                        <div className="w-2 h-2 rounded-full bg-primary-500 animate-bounce [animation-delay:150ms]" />
                        <div className="w-2 h-2 rounded-full bg-primary-500 animate-bounce [animation-delay:300ms]" />
                    </div>
                </div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    return <>{children}</>;
}
