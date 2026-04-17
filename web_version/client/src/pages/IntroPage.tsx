import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { QrCode, FileCheck, ShieldCheck, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import logo from '@/assets/logo.png';

const IntroPage: React.FC = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-navy-950 text-white selection:bg-primary-500/30 overflow-hidden relative font-sans">
            {/* Background Decor */}
            <div className="absolute top-0 left-0 w-full h-full">
                <div className="absolute top-[-10%] right-[-10%] w-[50%] h-[50%] bg-primary-900/10 rounded-full blur-[120px]"></div>
                <div className="absolute bottom-[-10%] left-[-10%] w-[50%] h-[50%] bg-accent-900/10 rounded-full blur-[120px]"></div>
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full h-full opacity-[0.03] pointer-events-none"
                    style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '40px 40px' }}></div>
            </div>

            {/* Navigation */}
            <nav className="relative z-20 flex items-center justify-between px-8 py-6 max-w-7xl mx-auto">
                <div className="flex items-center gap-3 group cursor-pointer" onClick={() => navigate('/')}>
                    <img src={logo} alt="Blurz Logo" className="w-10 h-10 object-contain transition-transform group-hover:scale-110" />
                    <span className="text-xl font-black tracking-tighter">BLURZ</span>
                </div>
                <Button variant="ghost" className="text-navy-200 hover:text-white" onClick={() => navigate('/login')}>
                    Sign In
                </Button>
            </nav>

            {/* Hero Section */}
            <div className="relative z-10 max-w-7xl mx-auto px-8 pt-20 pb-32">
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
                    <motion.div
                        initial={{ opacity: 0, x: -30 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.8 }}
                    >
                        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-400 text-xs font-bold uppercase tracking-wider mb-6">
                            <ShieldCheck className="w-3 h-3" />
                            Smart Campus Solution
                        </div>
                        <h1 className="text-6xl lg:text-8xl font-black tracking-tight leading-[0.9] mb-8">
                            Attendance <br />
                            <span className="text-gradient">Redefined.</span>
                        </h1>
                        <p className="text-xl text-navy-300 mb-10 leading-relaxed max-w-lg">
                            The next-generation smart attendance and quiz management system for modern universities. Secure, fast, and stunning.
                        </p>
                        <div className="flex flex-col sm:flex-row gap-4">
                            <Button
                                variant="gradient"
                                size="lg"
                                className="h-16 px-8 text-lg font-bold rounded-2xl group"
                                onClick={() => navigate('/login')}
                            >
                                Get Started
                                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
                            </Button>
                            <Button
                                variant="outline"
                                size="lg"
                                className="h-16 px-8 text-lg font-bold rounded-2xl border-white/10 hover:bg-white/5"
                            >
                                View Features
                            </Button>
                        </div>
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className="relative"
                    >
                        <div className="relative z-10 rounded-[2.5rem] overflow-hidden border border-white/10 p-4 bg-white/5 backdrop-blur-3xl shadow-2xl">
                            <div className="rounded-[1.5rem] overflow-hidden bg-navy-950 aspect-[4/3] flex items-center justify-center relative">
                                <div className="absolute inset-0 bg-gradient-to-tr from-primary-600/20 to-accent-600/20"></div>
                                <div className="relative z-10 flex flex-col items-center">
                                    <img src={logo} alt="Blurz Logo" className="w-40 h-40 object-contain drop-shadow-[0_0_30px_rgba(139,92,246,0.3)]" />
                                    <p className="mt-8 text-navy-500 text-sm font-black uppercase tracking-[0.3em] opacity-50">Secure Smart Attendance</p>
                                </div>
                            </div>
                        </div>
                        {/* Floating Elements */}
                        <motion.div
                            animate={{ y: [0, -20, 0] }}
                            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                            className="absolute top-10 -right-10 glass p-6 rounded-2xl border-white/10 shadow-2xl"
                        >
                            <div className="flex items-center gap-4">
                                <div className="w-12 h-12 bg-success/20 rounded-full flex items-center justify-center">
                                    <FileCheck className="w-6 h-6 text-success" />
                                </div>
                                <div>
                                    <p className="text-xs text-navy-400 font-bold uppercase tracking-widest">Attendance</p>
                                    <p className="text-xl font-bold">Verified</p>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                </div>

                {/* Features List */}
                <div className="mt-40 grid grid-cols-1 md:grid-cols-3 gap-8">
                    {[
                        { icon: QrCode, title: "QR Scan", desc: "Instant attendance tracking with secure HMAC-signed tokens." },
                        { icon: FileCheck, title: "Smart Quizzes", desc: "Real-time quiz submissions and automated grading." },
                        { icon: ShieldCheck, title: "Secure Access", desc: "Role-based control with JWT rotation and active monitoring." }
                    ].map((feature, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.1 }}
                            className="p-8 rounded-3xl bg-white/[0.03] border border-white/5 border-b-primary-500/30 hover:bg-white/[0.05] transition-colors"
                        >
                            <div className="w-12 h-12 bg-primary-500/20 rounded-2xl flex items-center justify-center mb-6">
                                <feature.icon className="w-6 h-6 text-primary-400" />
                            </div>
                            <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
                            <p className="text-navy-400 leading-relaxed">{feature.desc}</p>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default IntroPage;
