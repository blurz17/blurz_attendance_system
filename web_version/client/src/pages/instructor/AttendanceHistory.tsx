import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { History, ArrowLeft, CheckCircle2, XCircle, User, Calendar, Loader2, Download, Search } from 'lucide-react';
import { attendanceService } from '@/services/attendanceService';
import type { CourseAttendanceMatrix } from '@/types';
import { toast } from 'sonner';
import { Button } from '@/components/ui/Button';

const AttendanceHistory: React.FC = () => {
    const { courseId } = useParams<{ courseId: string }>();
    const navigate = useNavigate();
    const [data, setData] = useState<CourseAttendanceMatrix | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        if (!courseId) return;
        attendanceService.getFullCourseReport(courseId)
            .then(setData)
            .catch(() => toast.error('Failed to load attendance history'))
            .finally(() => setIsLoading(false));
    }, [courseId]);

    const filteredStudents = data?.students.filter(s =>
        s.name.toLowerCase().includes(searchTerm.toLowerCase()) || s.university_id.includes(searchTerm)
    ) || [];

    if (isLoading) return <div className="h-[60vh] flex items-center justify-center"><Loader2 className="w-10 h-10 text-primary-500 animate-spin" /></div>;
    if (!data) return null;

    const initials = (name: string) => name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);

    return (
        <div className="max-w-[95vw] mx-auto space-y-8 px-4">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="text-navy-400 hover:text-white">
                        <ArrowLeft className="w-4 h-4 mr-2" /> Back
                    </Button>
                    <div>
                        <h1 className="text-3xl font-black flex items-center gap-3">
                            <History className="w-8 h-8 text-primary-400" /> Attendance Matrix
                        </h1>
                        <p className="text-navy-400 font-medium">{data.course_name} — Comprehensive Session History</p>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <div className="relative w-64">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-500" />
                        <input type="text" placeholder="Search student..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-primary-500/50" />
                    </div>
                    <Button variant="outline" className="rounded-xl border-white/10 h-11"><Download className="w-4 h-4 mr-2" /> Export CSV</Button>
                </div>
            </div>

            <div className="glass border border-white/5 rounded-[2.5rem] overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-white/5 border-b border-white/5">
                                <th className="sticky left-0 z-20 bg-navy-950/95 backdrop-blur-md px-8 py-6 text-[10px] font-black uppercase tracking-widest text-navy-400 min-w-[280px] border-r border-white/5">
                                    Student Information
                                </th>
                                {data.sessions.map(s => (
                                    <th key={s.id} className="px-6 py-6 text-center border-r border-white/5 min-w-[120px]">
                                        <div className="flex flex-col items-center">
                                            <span className="text-[10px] font-black text-primary-400 uppercase tracking-widest leading-none">Week</span>
                                            <span className="text-xl font-black text-white">{s.week_number}</span>
                                            <span className="text-[9px] font-bold text-navy-500 mt-1 uppercase">
                                                {new Date(s.generated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                                            </span>
                                        </div>
                                    </th>
                                ))}
                                {data.sessions.length === 0 && <th className="px-8 py-6 text-navy-500 text-sm font-medium">No sessions generated yet.</th>}
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {filteredStudents.length > 0 ? filteredStudents.map((student, idx) => (
                                <motion.tr key={student.id} initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: idx * 0.02 }} className="group transition-colors">
                                    <td className="sticky left-0 z-10 bg-navy-950/95 backdrop-blur-md px-8 py-5 border-r border-white/5 group-hover:bg-primary-500/5 transition-colors">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-xl bg-navy-800 flex items-center justify-center text-primary-400 font-black text-[10px] shadow-inner">
                                                {initials(student.name)}
                                            </div>
                                            <div>
                                                <p className="font-bold text-sm text-white group-hover:text-primary-400 transition-colors truncate max-w-[150px]">{student.name}</p>
                                                <p className="text-[10px] font-mono text-navy-500">{student.university_id}</p>
                                            </div>
                                        </div>
                                    </td>
                                    {data.sessions.map(session => {
                                        const present = data.attendance[student.id]?.[session.id];
                                        return (
                                            <td key={session.id} className="px-6 py-5 text-center border-r border-white/5 group-hover:bg-white/[0.01] transition-colors">
                                                <div className="flex justify-center">
                                                    <motion.div whileHover={{ scale: 1.2 }}
                                                        className={`w-8 h-8 rounded-lg flex items-center justify-center ${present
                                                            ? 'bg-success/10 border border-success/20 text-success shadow-lg shadow-success/5'
                                                            : 'bg-error/10 border border-error/20 text-error/60'}`}>
                                                        {present ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                                                    </motion.div>
                                                </div>
                                            </td>
                                        );
                                    })}
                                </motion.tr>
                            )) : (
                                <tr><td colSpan={data.sessions.length + 1} className="px-8 py-20 text-center">
                                    <div className="flex flex-col items-center justify-center space-y-4 text-navy-500">
                                        <User className="w-12 h-12 opacity-10" />
                                        <p className="font-bold uppercase tracking-widest text-xs">No matching students found.</p>
                                    </div>
                                </td></tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Legend & Stats */}
            <div className="flex flex-col md:flex-row gap-8">
                <div className="glass border border-white/5 p-8 rounded-[2rem] flex-1 flex items-center gap-10">
                    <div className="space-y-4">
                        <h4 className="text-[10px] font-black text-navy-400 uppercase tracking-widest">Legend</h4>
                        <div className="flex items-center gap-6">
                            {[{ color: 'bg-success', label: 'Present' }, { color: 'bg-error', label: 'Absent' }].map(({ color, label }) => (
                                <div key={label} className="flex items-center gap-2">
                                    <span className={`w-3 h-3 rounded-full ${color}`}></span>
                                    <span className="text-xs font-bold text-navy-300">{label}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="h-10 w-px bg-white/5"></div>
                    <div className="space-y-1">
                        <h4 className="text-[10px] font-black text-navy-400 uppercase tracking-widest">Quick Insight</h4>
                        <p className="text-xs font-medium text-navy-300">
                            The report shows all <span className="text-white font-bold">{data.students.length}</span> enrolled students.
                        </p>
                    </div>
                </div>
                <div className="glass border border-white/5 p-8 rounded-[2rem] bg-gradient-to-br from-primary-500/5 to-accent-500/5 flex items-center gap-4">
                    <div className="w-12 h-12 rounded-2xl bg-primary-500/10 flex items-center justify-center text-primary-400">
                        <Calendar className="w-6 h-6" />
                    </div>
                    <div>
                        <h4 className="text-xl font-black text-white truncate max-w-[200px]">{data.sessions.length} Sessions</h4>
                        <p className="text-[10px] font-black text-navy-400 uppercase tracking-widest">Total Recorded Weeks</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AttendanceHistory;
