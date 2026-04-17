import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { LogIn, Mail, Lock, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/Button';
import { authService } from '@/services/authService';
import { toast } from 'sonner';
import logo from '../assets/logo.png';

const inputClass = "w-full bg-navy-900/50 border border-white/10 rounded-xl py-3 pl-10 pr-4 text-white placeholder:text-navy-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50 transition-all";

const LoginPage: React.FC = () => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showResend, setShowResend] = useState(false);

    const { login } = useAuth();
    const navigate = useNavigate();
    const from = useLocation().state?.from?.pathname || '/';

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true); setError(''); setShowResend(false);
        try {
            await login({ email, password });
            navigate(from, { replace: true });
        } catch (err: any) {
            const detail = err.response?.data?.detail;
            setError(detail || 'Invalid email or password');
            if (detail?.toLowerCase().includes('not activated')) setShowResend(true);
        } finally { setIsLoading(false); }
    };

    const handleResend = async () => {
        try { await authService.resendVerification(email); toast.success('Verification link sent!', { description: 'Please check your email.' }); }
        catch { toast.error('Failed to resend link'); }
    };

    return (
        <div className="min-h-screen w-full flex items-center justify-center bg-navy-950 relative overflow-hidden font-sans">
            <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary-900/20 rounded-full blur-[120px] animate-pulse"></div>
            <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-accent-900/20 rounded-full blur-[120px] animate-pulse"></div>

            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="z-10 w-full max-w-md p-8">
                <div className="flex flex-col items-center mb-8">
                    <motion.div whileHover={{ scale: 1.05 }} className="mb-6">
                        <img src={logo} alt="Blurz Logo" className="w-24 h-24 object-contain drop-shadow-[0_0_15px_rgba(139,92,246,0.3)]" />
                    </motion.div>
                    <h1 className="text-3xl font-black text-white tracking-tighter uppercase">Smart Attendance</h1>
                    <p className="text-navy-300 mt-2">Welcome back! Please login to your account.</p>
                </div>

                <motion.div className="glass border border-white/10 p-8 rounded-3xl shadow-2xl" whileHover={{ boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)" }}>
                    <form onSubmit={handleSubmit} className="space-y-5">
                        <AnimatePresence mode="wait">
                            {error && (
                                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                                    className="bg-error/10 border border-error/20 p-3 rounded-xl flex items-center gap-3 text-error text-sm font-medium">
                                    <AlertCircle className="w-4 h-4 shrink-0" /><span>{error}</span>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-navy-100 ml-1">Email Address</label>
                            <div className="relative group">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400 group-focus-within:text-primary-400 transition-colors" />
                                <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="name@university.edu" className={inputClass} />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <div className="flex justify-between items-center ml-1">
                                <label className="text-sm font-medium text-navy-100">Password</label>
                                <button type="button" className="text-xs text-primary-400 hover:text-primary-300 font-medium">Forgot Password?</button>
                            </div>
                            <div className="relative group">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400 group-focus-within:text-primary-400 transition-colors" />
                                <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} placeholder="••••••••" className={inputClass} />
                            </div>
                        </div>

                        <Button type="submit" disabled={isLoading} variant="gradient" className="w-full py-6 text-base font-semibold rounded-xl mt-4">
                            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <><LogIn className="w-5 h-5" /> Sign In</>}
                        </Button>
                    </form>

                    <div className="mt-8 pt-6 border-t border-white/5 text-center space-y-4">
                        {showResend && (
                            <Button variant="outline" size="sm" className="w-full border-primary-500/30 text-primary-400 hover:bg-primary-500/5" onClick={handleResend}>
                                Resend Verification Link
                            </Button>
                        )}
                        <p className="text-navy-400 text-sm">
                            Don't have an account? <span className="text-primary-400 font-semibold cursor-pointer hover:text-primary-300">Contact Admin</span>
                        </p>
                    </div>
                </motion.div>
            </motion.div>

            <p className="absolute bottom-8 text-navy-600 text-xs tracking-widest uppercase font-bold">
                Blurz Smart Attendance & Quiz System &copy; 2026
            </p>
        </div>
    );
};

export default LoginPage;
