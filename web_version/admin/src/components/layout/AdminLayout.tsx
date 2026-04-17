import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Users,
    BookOpen,
    Building2,
    Layers,
    LayoutDashboard,
    LogOut,
    Menu,
    X,
    Moon,
    Sun,
    ChevronLeft,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { useTheme } from '@/context/ThemeContext';
import { cn } from '@/lib/utils';

const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/users', icon: Users, label: 'Users' },
    { to: '/departments', icon: Building2, label: 'Departments' },
    { to: '/sections', icon: Layers, label: 'Sections' },
    { to: '/courses', icon: BookOpen, label: 'Courses' },
];

export default function AdminLayout() {
    const [sidebarOpen, setSidebarOpen] = useState(true);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const { user, logout } = useAuth();
    const { theme, toggleTheme } = useTheme();
    const navigate = useNavigate();

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <div className="flex h-screen overflow-hidden bg-surface">
            {/* Desktop Sidebar */}
            <motion.aside
                initial={false}
                animate={{ width: sidebarOpen ? 260 : 72 }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className="hidden lg:flex flex-col border-r border-border bg-surface-elevated relative z-20"
            >
                {/* Logo Area */}
                <div className="flex items-center h-16 px-4 border-b border-border">
                    <div className="flex items-center gap-3 overflow-hidden">
                        <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center flex-shrink-0 overflow-hidden shadow-lg shadow-primary-600/20">
                            <img src="/apple-touch-icon.png" alt="Logo" className="w-full h-full object-cover p-1.5" />
                        </div>
                        <AnimatePresence>
                            {sidebarOpen && (
                                <motion.div
                                    initial={{ opacity: 0, width: 0 }}
                                    animate={{ opacity: 1, width: 'auto' }}
                                    exit={{ opacity: 0, width: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="overflow-hidden whitespace-nowrap"
                                >
                                    <h1 className="font-bold text-text-primary text-sm">Blurz Admin</h1>
                                    <p className="text-xs text-text-muted">Management Portal</p>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>

                {/* Nav Items */}
                <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
                    {navItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            end={item.to === '/'}
                            className={({ isActive }) =>
                                cn(
                                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200',
                                    isActive
                                        ? 'bg-primary-600 text-white shadow-md shadow-primary-600/20'
                                        : 'text-text-secondary hover:bg-surface-muted hover:text-text-primary'
                                )
                            }
                        >
                            <item.icon size={20} className="flex-shrink-0" />
                            <AnimatePresence>
                                {sidebarOpen && (
                                    <motion.span
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        className="overflow-hidden whitespace-nowrap"
                                    >
                                        {item.label}
                                    </motion.span>
                                )}
                            </AnimatePresence>
                        </NavLink>
                    ))}
                </nav>

                {/* Bottom Actions */}
                <div className="p-3 border-t border-border space-y-1">
                    <button
                        onClick={toggleTheme}
                        className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-text-secondary hover:bg-surface-muted hover:text-text-primary transition-all duration-200"
                    >
                        {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                        <AnimatePresence>
                            {sidebarOpen && (
                                <motion.span
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                >
                                    {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
                                </motion.span>
                            )}
                        </AnimatePresence>
                    </button>
                    <button
                        onClick={handleLogout}
                        className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all duration-200"
                    >
                        <LogOut size={20} />
                        <AnimatePresence>
                            {sidebarOpen && (
                                <motion.span
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                >
                                    Logout
                                </motion.span>
                            )}
                        </AnimatePresence>
                    </button>
                </div>

                {/* Collapse Button */}
                <button
                    onClick={() => setSidebarOpen(!sidebarOpen)}
                    className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-surface border border-border shadow-sm flex items-center justify-center hover:bg-surface-muted transition-colors z-30"
                >
                    <ChevronLeft
                        size={14}
                        className={cn('text-text-secondary transition-transform duration-300', !sidebarOpen && 'rotate-180')}
                    />
                </button>
            </motion.aside>

            {/* Mobile Menu Overlay */}
            <AnimatePresence>
                {mobileMenuOpen && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
                            onClick={() => setMobileMenuOpen(false)}
                        />
                        <motion.aside
                            initial={{ x: -300 }}
                            animate={{ x: 0 }}
                            exit={{ x: -300 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="fixed inset-y-0 left-0 w-72 bg-surface-elevated border-r border-border z-50 lg:hidden flex flex-col"
                        >
                            <div className="flex items-center justify-between h-16 px-4 border-b border-border">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl gradient-primary flex items-center justify-center flex-shrink-0 overflow-hidden shadow-lg shadow-primary-600/20">
                                        <img src="/apple-touch-icon.png" alt="Logo" className="w-full h-full object-cover p-1.5" />
                                    </div>
                                    <div>
                                        <h1 className="font-bold text-text-primary text-sm">Blurz Admin</h1>
                                        <p className="text-xs text-text-muted">Management Portal</p>
                                    </div>
                                </div>
                                <button onClick={() => setMobileMenuOpen(false)} className="text-text-secondary">
                                    <X size={20} />
                                </button>
                            </div>
                            <nav className="flex-1 p-3 space-y-1">
                                {navItems.map((item) => (
                                    <NavLink
                                        key={item.to}
                                        to={item.to}
                                        end={item.to === '/'}
                                        onClick={() => setMobileMenuOpen(false)}
                                        className={({ isActive }) =>
                                            cn(
                                                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all',
                                                isActive
                                                    ? 'bg-primary-600 text-white shadow-md'
                                                    : 'text-text-secondary hover:bg-surface-muted'
                                            )
                                        }
                                    >
                                        <item.icon size={20} />
                                        <span>{item.label}</span>
                                    </NavLink>
                                ))}
                            </nav>
                            <div className="p-3 border-t border-border space-y-1">
                                <button onClick={toggleTheme} className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-text-secondary hover:bg-surface-muted">
                                    {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                                    <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
                                </button>
                                <button onClick={handleLogout} className="flex items-center gap-3 w-full px-3 py-2.5 rounded-lg text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20">
                                    <LogOut size={20} />
                                    <span>Logout</span>
                                </button>
                            </div>
                        </motion.aside>
                    </>
                )}
            </AnimatePresence>

            {/* Main Content */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Top Bar */}
                <header className="h-16 border-b border-border bg-surface-elevated/80 backdrop-blur-sm flex items-center justify-between px-4 lg:px-6 flex-shrink-0">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setMobileMenuOpen(true)}
                            className="lg:hidden text-text-secondary hover:text-text-primary"
                        >
                            <Menu size={22} />
                        </button>
                    </div>

                    <div className="flex items-center gap-3">
                        <div className="text-right hidden sm:block">
                            <p className="text-sm font-medium text-text-primary">{user?.full_name}</p>
                            <p className="text-xs text-text-muted">{user?.email}</p>
                        </div>
                        <div className="w-10 h-10 rounded-full overflow-hidden border-2 border-primary-100 dark:border-primary-900/50 shadow-sm flex-shrink-0">
                            <img src="/apple-touch-icon.png" alt="User Logo" className="w-full h-full object-cover p-1" />
                        </div>
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-y-auto p-4 lg:p-6">
                    <motion.div
                        key={location.pathname}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.3 }}
                    >
                        <Outlet />
                    </motion.div>
                </main>
            </div>
        </div>
    );
}
