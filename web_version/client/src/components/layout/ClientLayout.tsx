import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    LayoutDashboard,
    BookOpen,
    QrCode,
    FileEdit,
    History,
    LogOut,
    Menu,
    X,
    User,
    Bell,
    Search,
    ChevronRight
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import logoSmall from '../../assets/logo-small.png';

const ClientLayout: React.FC = () => {
    const { user, logout } = useAuth();
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const location = useLocation();
    const navigate = useNavigate();

    const studentLinks = [
        { title: 'Dashboard', icon: LayoutDashboard, path: '/' },
        { title: 'Scan Attendance', icon: QrCode, path: '/scan' },
        { title: 'Attendance', icon: History, path: '/attendance' },
        { title: 'Quizzes', icon: FileEdit, path: '/quizzes' },
    ];

    const instructorLinks = [
        { title: 'Dashboard', icon: LayoutDashboard, path: '/' },
        { title: 'Attendance', icon: QrCode, path: '/instructor/attendance' },
        { title: 'Quiz Lab', icon: FileEdit, path: '/instructor/quizzes' },
        { title: 'Reports', icon: BookOpen, path: '/instructor/reports' },
    ];

    const links = user?.role === 'student' ? studentLinks : instructorLinks;

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    return (
        <div className="min-h-screen bg-navy-950 text-white font-sans overflow-hidden flex">
            {/* Background Decor */}
            <div className="fixed inset-0 pointer-events-none">
                <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary-900/10 rounded-full blur-[120px]"></div>
                <div className="absolute bottom-[-10%] left-[-10%] w-[40%] h-[40%] bg-accent-900/10 rounded-full blur-[120px]"></div>
            </div>

            {/* Sidebar */}
            <motion.aside
                initial={false}
                animate={{ width: isSidebarOpen ? 280 : 80 }}
                className="relative z-30 h-screen glass border-r border-white/5 flex flex-col transition-all duration-300"
            >
                <div className="p-6 flex items-center justify-between">
                    <AnimatePresence mode="wait">
                        {isSidebarOpen && (
                            <motion.div
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -10 }}
                                className="flex items-center gap-2"
                                onClick={() => navigate('/')}
                            >
                                <img src={logoSmall} alt="Logo" className="w-8 h-8 object-contain" />
                                <span className="font-black tracking-tighter text-lg">BLURZ</span>
                            </motion.div>
                        )}
                    </AnimatePresence>
                    <Button
                        variant="ghost"
                        size="icon"
                        className="hover:bg-white/5 text-navy-400"
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    >
                        {isSidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
                    </Button>
                </div>

                <nav className="flex-1 px-4 space-y-2 mt-4">
                    {links.map((link) => {
                        const isActive = location.pathname === link.path;
                        return (
                            <Link key={link.path} to={link.path}>
                                <motion.div
                                    whileHover={{ x: 5 }}
                                    className={cn(
                                        "flex items-center gap-3 px-3 py-3 rounded-xl transition-all group",
                                        isActive
                                            ? "bg-primary-500 text-white shadow-lg shadow-primary-500/20"
                                            : "text-navy-400 hover:bg-white/5 hover:text-white"
                                    )}
                                >
                                    <link.icon className={cn("w-5 h-5", isActive ? "text-white" : "group-hover:text-primary-400")} />
                                    {isSidebarOpen && <span className="font-medium text-sm">{link.title}</span>}
                                    {isSidebarOpen && isActive && (
                                        <motion.div layoutId="active-pill" className="ml-auto">
                                            <ChevronRight className="w-4 h-4 opacity-50" />
                                        </motion.div>
                                    )}
                                </motion.div>
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 border-t border-white/5">
                    <Button
                        variant="ghost"
                        className="w-full justify-start text-error hover:bg-error/10"
                        onClick={handleLogout}
                    >
                        <LogOut className="w-5 h-5 mr-3" />
                        {isSidebarOpen && <span className="font-bold">Sign Out</span>}
                    </Button>
                </div>
            </motion.aside>

            {/* Main Content */}
            <main className="flex-1 h-screen overflow-y-auto relative z-10 flex flex-col">
                {/* Header */}
                <header className="h-20 border-b border-white/5 flex items-center justify-between px-8 bg-navy-950/50 backdrop-blur-md sticky top-0 z-20">
                    <div className="relative group max-w-md w-full hidden md:block">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-500" />
                        <input
                            type="text"
                            placeholder="Search courses, quizzes..."
                            className="w-full bg-white/5 border border-white/5 rounded-xl py-2 pl-10 pr-4 text-sm text-white placeholder:text-navy-500 focus:outline-none focus:border-primary-500/50 transition-all"
                        />
                    </div>

                    <div className="flex items-center gap-6">
                        <button className="relative text-navy-400 hover:text-white transition-colors">
                            <Bell className="w-5 h-5" />
                            <span className="absolute -top-1 -right-1 w-2 h-2 bg-primary-500 rounded-full"></span>
                        </button>
                        <div className="flex items-center gap-3 pl-6 border-l border-white/5">
                            <div className="text-right hidden sm:block">
                                <p className="text-sm font-bold text-white">{user?.full_name}</p>
                                <p className="text-[10px] text-primary-400 font-black uppercase tracking-widest">{user?.role}</p>
                            </div>
                            <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center overflow-hidden">
                                <User className="w-6 h-6 text-navy-400" />
                            </div>
                        </div>
                    </div>
                </header>

                {/* Page Content */}
                <div className="p-8 pb-20">
                    <Outlet />
                </div>
            </main>
        </div>
    );
};

export default ClientLayout;
