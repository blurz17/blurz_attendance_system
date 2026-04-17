import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { BookOpen, Calendar, CheckCircle2, Clock, TrendingUp, ArrowUpRight, ClipboardList, Loader2 } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import { courseService, StudentCourse } from '@/services/courseService';
import { quizService } from '@/services/quizService';
import { attendanceService } from '@/services/attendanceService';
import { QuizListItem, AttendanceRecord } from '@/types';

const StudentDashboard: React.FC = () => {
    const { user } = useAuth();
    const [courses, setCourses] = useState<StudentCourse[]>([]);
    const [quizzes, setQuizzes] = useState<QuizListItem[]>([]);
    const [attendance, setAttendance] = useState<AttendanceRecord[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        Promise.all([courseService.getStudentCourses(), quizService.getAvailableQuizzes(), attendanceService.getMyRecords()])
            .then(([c, q, a]) => { setCourses(c); setQuizzes(q); setAttendance(a); })
            .catch(err => console.error('Failed to fetch dashboard data:', err))
            .finally(() => setIsLoading(false));
    }, []);

    const displayAttendance = Math.min(courses.length > 0 ? Math.round((attendance.length / (courses.length * 12)) * 100) : 0, 100);

    const stats = [
        { label: 'Avg. Attendance', value: `${displayAttendance}%`, icon: CheckCircle2, color: 'text-success', bg: 'bg-success/10' },
        { label: 'Active Quizzes', value: quizzes.length.toString().padStart(2, '0'), icon: ClipboardList, color: 'text-primary-400', bg: 'bg-primary-500/10' },
        { label: 'Total Courses', value: courses.length.toString().padStart(2, '0'), icon: BookOpen, color: 'text-accent-400', bg: 'bg-accent-500/10' },
        { label: 'Classes Attended', value: attendance.length.toString().padStart(2, '0'), icon: Calendar, color: 'text-navy-300', bg: 'bg-navy-500/10' },
    ];

    if (isLoading) return <div className="h-[60vh] flex items-center justify-center"><Loader2 className="w-10 h-10 text-primary-500 animate-spin" /></div>;

    return (
        <div className="space-y-10">
            {/* Welcome Banner */}
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                className="relative rounded-[2rem] overflow-hidden p-10 bg-gradient-to-br from-primary-600 to-accent-700 shadow-2xl">
                <div className="relative z-10">
                    <h2 className="text-4xl font-black mb-3">Welcome back, {user?.full_name.split(' ')[0]}! 👋</h2>
                    <p className="text-white/80 max-w-lg leading-relaxed font-medium">
                        {quizzes.length > 0
                            ? `You have ${quizzes.length} available quizzes. Your overall attendance is currently at ${displayAttendance}%.`
                            : `You're all caught up! Your overall attendance is currently at ${displayAttendance}%.`}
                    </p>
                    <div className="flex gap-4 mt-8">
                        <Button variant="secondary" className="rounded-xl h-12 px-6 font-bold shadow-xl"><BookOpen className="w-4 h-4 mr-2" /> View My Courses</Button>
                        <Button variant="ghost" className="rounded-xl h-12 px-6 font-bold text-white hover:bg-white/10">Check Records</Button>
                    </div>
                </div>
                <div className="absolute top-[-20%] right-[-10%] w-96 h-96 bg-white/10 rounded-full blur-3xl"></div>
                <div className="absolute bottom-[-20%] left-[20%] w-64 h-64 bg-primary-400/20 rounded-full blur-2xl"></div>
            </motion.div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat, i) => (
                    <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}
                        className="glass border border-white/5 p-6 rounded-3xl hover:border-white/10 transition-colors group">
                        <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center mb-4 transition-transform group-hover:scale-110", stat.bg)}>
                            <stat.icon className={cn("w-6 h-6", stat.color)} />
                        </div>
                        <p className="text-navy-400 text-xs font-black uppercase tracking-widest">{stat.label}</p>
                        <h3 className="text-2xl font-black mt-1">{stat.value}</h3>
                    </motion.div>
                ))}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Active Courses */}
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="lg:col-span-2 space-y-6">
                    <div className="flex justify-between items-end">
                        <div>
                            <h3 className="text-xl font-black tracking-tight flex items-center gap-2"><TrendingUp className="w-5 h-5 text-primary-400" /> Active Courses</h3>
                            <p className="text-navy-400 text-sm">Courses you are currently enrolled in.</p>
                        </div>
                        <Button variant="link" className="text-primary-400 p-0">View All</Button>
                    </div>
                    <div className="space-y-4">
                        {courses.length > 0 ? courses.map((course, i) => {
                            const pct = Math.min(Math.round((attendance.filter(a => a.course_name === course.name).length / 12) * 100), 100);
                            return (
                                <div key={i} className="glass border border-white/5 p-5 rounded-2xl flex items-center gap-5 hover:bg-white/5 transition-all cursor-pointer">
                                    <div className="w-12 h-12 bg-navy-800 rounded-xl flex items-center justify-center font-black text-[10px] text-navy-400">{course.id.slice(0, 5).toUpperCase()}</div>
                                    <div className="flex-1">
                                        <h4 className="font-bold">{course.name}</h4>
                                        <p className="text-xs text-navy-400">Year {course.year}</p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-xs font-black text-navy-500 uppercase tracking-tighter">Attendance</p>
                                        <p className={cn("font-black", pct > 75 ? "text-success" : "text-warning")}>{pct}%</p>
                                    </div>
                                    <div className="w-8 h-8 rounded-lg border border-white/5 flex items-center justify-center hover:bg-primary-500 hover:text-white transition-colors">
                                        <ArrowUpRight className="w-4 h-4" />
                                    </div>
                                </div>
                            );
                        }) : (
                            <div className="glass border border-white/5 p-10 rounded-2xl text-center text-navy-400">No active courses found.</div>
                        )}
                    </div>
                </motion.div>

                {/* Quizzes */}
                <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} className="glass border border-white/5 p-8 rounded-[2rem] h-fit">
                    <h3 className="text-xl font-black mb-6">Available Quizzes</h3>
                    <div className="space-y-6">
                        {quizzes.length > 0 ? quizzes.map((quiz, i) => (
                            <div key={i} className="flex gap-4 group cursor-pointer">
                                <div className="shrink-0 w-2 h-2 rounded-full bg-primary-400 mt-2 shadow-[0_0_8px_rgba(139,92,246,0.5)] transition-transform group-hover:scale-150"></div>
                                <div>
                                    <h5 className="font-bold text-sm group-hover:text-primary-400 transition-colors">{quiz.title}</h5>
                                    <p className="text-xs text-navy-400 mt-1">{quiz.course_name}</p>
                                    <div className="flex items-center gap-2 mt-2 text-[10px] font-black text-navy-500">
                                        <Clock className="w-3 h-3" />
                                        {quiz.due_date ? `DUE: ${new Date(quiz.due_date).toLocaleDateString()}` : 'NO DUE DATE'}
                                    </div>
                                </div>
                            </div>
                        )) : (
                            <div className="text-sm text-navy-500 italic pb-4">No quizzes currently available.</div>
                        )}
                    </div>
                    <Button variant="outline" className="w-full mt-10 rounded-xl border-white/10" disabled={quizzes.length === 0}>Visit Quiz Center</Button>
                </motion.div>
            </div>
        </div>
    );
};

export default StudentDashboard;
