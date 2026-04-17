import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { QrCode, FileEdit, BarChart3, Plus, Clock, ChevronRight, ShieldCheck, Zap, Loader2 } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import { courseService } from '@/services/courseService';
import { quizService } from '@/services/quizService';
import { Course, QuizListItem } from '@/types';

const InstructorDashboard: React.FC = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [courses, setCourses] = useState<Course[]>([]);
    const [quizzes, setQuizzes] = useState<QuizListItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        Promise.all([courseService.getInstructorCourses(), quizService.getInstructorQuizzes()])
            .then(([c, q]) => { setCourses(c); setQuizzes(q); })
            .catch(err => console.error('Failed to fetch instructor dashboard data:', err))
            .finally(() => setIsLoading(false));
    }, []);

    const stats = [
        { label: 'Assigned Courses', value: courses.length.toString().padStart(2, '0'), icon: BarChart3, color: 'text-primary-400', bg: 'bg-primary-500/10' },
        { label: 'Active Quizzes', value: quizzes.length.toString().padStart(2, '0'), icon: FileEdit, color: 'text-accent-400', bg: 'bg-accent-500/10' },
        { label: 'Role', value: user?.role?.toUpperCase() || 'N/A', icon: ShieldCheck, color: 'text-warning', bg: 'bg-warning/10' },
        { label: 'System Status', value: 'Live', icon: Zap, color: 'text-success', bg: 'bg-success/10' },
    ];

    if (isLoading) return <div className="h-[60vh] flex items-center justify-center"><Loader2 className="w-10 h-10 text-primary-500 animate-spin" /></div>;

    return (
        <div className="space-y-10">
            {/* Welcome Banner */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                className="relative rounded-[2rem] overflow-hidden p-10 bg-navy-900 border border-white/5 shadow-2xl">
                <div className="relative z-10">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-400 text-[10px] font-black uppercase tracking-widest mb-4">
                        <ShieldCheck className="w-3 h-3" /> Instructor Portal
                    </div>
                    <h2 className="text-4xl font-black mb-3 text-white">Hello, {user?.full_name.split(' ')[0]}</h2>
                    <p className="text-navy-400 max-w-md leading-relaxed">
                        Welcome to your dashboard. You are currently overseeing {courses.length} courses and have {quizzes.length} active quizzes published.
                    </p>
                    <div className="flex gap-4 mt-8">
                        <Button variant="gradient" className="rounded-xl h-14 px-8 font-bold shadow-xl"><QrCode className="w-5 h-5 mr-3" /> Generate attendance QR</Button>
                        <Button variant="outline" className="rounded-xl h-14 px-8 font-bold border-white/10 hover:bg-white/5 text-white"><Plus className="w-5 h-5 mr-3" /> New Quiz</Button>
                    </div>
                </div>
                <div className="absolute top-[-20%] right-[-10%] w-96 h-96 bg-primary-500/5 rounded-full blur-3xl"></div>
            </motion.div>

            {/* Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat, i) => (
                    <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                        className="p-8 rounded-[2rem] glass border border-white/5 group relative overflow-hidden">
                        <div className={cn("inline-flex w-12 h-12 rounded-2xl items-center justify-center mb-6 transition-transform group-hover:scale-110", stat.bg)}>
                            <stat.icon className={cn("w-6 h-6", stat.color)} />
                        </div>
                        <p className="text-navy-400 text-[10px] font-black uppercase tracking-[0.2em]">{stat.label}</p>
                        <h3 className="text-3xl font-black mt-2 text-white">{stat.value}</h3>
                        <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-primary-500 to-accent-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-500 origin-left"></div>
                    </motion.div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Courses */}
                <div className="lg:col-span-2 space-y-6">
                    <h3 className="text-xl font-black tracking-tight flex items-center gap-3 text-white">
                        <BarChart3 className="w-5 h-5 text-accent-400" /> Assigned Courses
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {courses.length > 0 ? courses.map((course, i) => (
                            <div key={i} className="group p-6 rounded-3xl bg-white/[0.03] border border-white/5 hover:bg-white/[0.06] transition-all cursor-pointer">
                                <div className="flex justify-between items-start mb-4">
                                    <div className="w-10 h-10 bg-navy-800 rounded-xl flex items-center justify-center font-black text-[10px] text-navy-400">ID: {course.id.slice(0, 4)}</div>
                                    <div className="text-right">
                                        <p className="text-[10px] text-navy-500 font-black uppercase">Year</p>
                                        <p className="font-black text-white">{course.year}</p>
                                    </div>
                                </div>
                                <h4 className="font-bold text-lg leading-tight mb-4 group-hover:text-primary-400 transition-colors text-white">{course.name}</h4>
                                <div className="flex items-center gap-2 text-navy-400 text-xs font-medium pt-4 border-t border-white/5">
                                    <Clock className="w-3 h-3" /> Active Course
                                </div>
                            </div>
                        )) : (
                            <div className="col-span-2 group p-10 rounded-3xl bg-white/[0.03] border border-white/5 text-center text-navy-400 font-bold">No assigned courses found.</div>
                        )}
                    </div>
                </div>

                {/* Quizzes */}
                <div className="space-y-6">
                    <h3 className="text-xl font-black text-white">Recent Quizzes</h3>
                    <div className="space-y-3">
                        {quizzes.length > 0 ? quizzes.map((quiz, i) => (
                            <div key={i} className="p-4 rounded-2xl bg-white/[0.03] border border-white/5 hover:border-primary-500/30 flex items-center justify-between group cursor-pointer transition-all">
                                <div>
                                    <h5 className="font-bold text-sm text-white">{quiz.title}</h5>
                                    <p className="text-[10px] text-navy-500 uppercase tracking-wider mt-1">{quiz.course_name} • {quiz.question_count} Qs</p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button variant="ghost" size="sm" className="h-8 px-2 text-[10px] opacity-0 group-hover:opacity-100 transition-opacity"
                                        onClick={(e) => { e.stopPropagation(); navigate(`/instructor/quizzes/${quiz.id}/submissions`); }}>Results</Button>
                                    <ChevronRight className="w-4 h-4 text-navy-500 group-hover:text-primary-400 transition-transform group-hover:translate-x-1" />
                                </div>
                            </div>
                        )) : (
                            <div className="text-sm text-navy-500 italic p-4 bg-white/[0.02] rounded-2xl border border-white/5">No recently created quizzes.</div>
                        )}
                    </div>
                    <div className="mt-10 p-6 rounded-[2rem] bg-gradient-to-br from-accent-600/20 to-primary-600/20 border border-white/5">
                        <h4 className="font-black text-white mb-2 uppercase text-xs tracking-widest">Dashboard Tip 💡</h4>
                        <p className="text-xs text-navy-300 leading-relaxed">Click on a course to view detailed attendance reports and session history.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default InstructorDashboard;
