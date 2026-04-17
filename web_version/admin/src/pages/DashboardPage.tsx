import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Users, BookOpen, Building2, Layers, UserCheck, UserPlus, TrendingUp } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/index';
import { userService, departmentService, sectionService, courseService } from '@/services/adminService';

interface StatCard {
    label: string; value: number; icon: React.ElementType; color: string; gradient: string;
}

export default function DashboardPage() {
    const [stats, setStats] = useState<StatCard[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        (async () => {
            try {
                const [usersData, departments, sections, courses] = await Promise.all([
                    userService.list({ limit: 1 }), departmentService.list(),
                    sectionService.list(), courseService.list(),
                ]);
                const [students, professors] = await Promise.all([
                    userService.list({ role: 'student', limit: 1 }),
                    userService.list({ role: 'professor', limit: 1 }),
                ]);
                setStats([
                    { label: 'Total Users', value: usersData.total, icon: Users, color: 'text-primary-600', gradient: 'from-primary-500/10 to-primary-600/5' },
                    { label: 'Students', value: students.total, icon: UserCheck, color: 'text-accent-600', gradient: 'from-accent-500/10 to-accent-600/5' },
                    { label: 'Professors', value: professors.total, icon: UserPlus, color: 'text-emerald-600', gradient: 'from-emerald-500/10 to-emerald-600/5' },
                    { label: 'Courses', value: courses.length, icon: BookOpen, color: 'text-rose-600', gradient: 'from-rose-500/10 to-rose-600/5' },
                    { label: 'Departments', value: departments.length, icon: Building2, color: 'text-indigo-600', gradient: 'from-indigo-500/10 to-indigo-600/5' },
                    { label: 'Sections', value: sections.length, icon: Layers, color: 'text-cyan-600', gradient: 'from-cyan-500/10 to-cyan-600/5' },
                    { label: 'Growth', value: 0, icon: TrendingUp, color: 'text-violet-600', gradient: 'from-violet-500/10 to-violet-600/5' },
                ]);
            } catch (error) {
                console.error('Failed to fetch stats:', error);
            } finally {
                setLoading(false);
            }
        })();
    }, []);

    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-text-primary">Dashboard</h1>
                <p className="text-text-secondary mt-1">Overview of your university management system</p>
            </div>

            {loading ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {Array.from({ length: 8 }).map((_, i) => (
                        <Card key={i}><CardContent className="p-6">
                            <Skeleton className="h-10 w-10 rounded-xl mb-3" />
                            <Skeleton className="h-8 w-20 mb-1" />
                            <Skeleton className="h-4 w-24" />
                        </CardContent></Card>
                    ))}
                </div>
            ) : (
                <motion.div
                    initial="hidden" animate="show"
                    variants={{ hidden: {}, show: { transition: { staggerChildren: 0.08 } } }}
                    className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
                >
                    {stats.map((stat) => (
                        <motion.div key={stat.label} variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }}>
                            <Card className="group hover:border-primary-200 dark:hover:border-primary-800 hover:shadow-lg transition-all duration-300">
                                <CardContent className="p-6">
                                    <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${stat.gradient} flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-300`}>
                                        <stat.icon size={22} className={stat.color} />
                                    </div>
                                    <p className="text-3xl font-bold text-text-primary">{stat.value.toLocaleString()}</p>
                                    <p className="text-sm text-text-secondary mt-0.5">{stat.label}</p>
                                </CardContent>
                            </Card>
                        </motion.div>
                    ))}
                </motion.div>
            )}

            {/* Quick Actions */}
            <div>
                <h2 className="text-lg font-semibold text-text-primary mb-4">Quick Actions</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {[
                        { href: '/users', icon: UserPlus, title: 'Add New User', desc: 'Create student or professor', bg: 'gradient-primary' },
                        { href: '/courses', icon: BookOpen, title: 'Manage Courses', desc: 'Create and assign courses', bg: 'bg-accent-600' },
                        { href: '/users', icon: Users, title: 'Bulk Upload', desc: 'Import users from CSV file', bg: 'bg-emerald-600' },
                    ].map(({ href, icon: Icon, title, desc, bg }) => (
                        <a key={title} href={href} className="group">
                            <Card className="hover:shadow-lg transition-all duration-300">
                                <CardContent className="p-5 flex items-center gap-4">
                                    <div className={`w-12 h-12 rounded-xl ${bg} flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform`}>
                                        <Icon size={24} className="text-white" />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-text-primary">{title}</h3>
                                        <p className="text-sm text-text-secondary">{desc}</p>
                                    </div>
                                </CardContent>
                            </Card>
                        </a>
                    ))}
                </div>
            </div>
        </div>
    );
}
