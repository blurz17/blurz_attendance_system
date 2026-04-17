import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { History, Calendar, BookOpen, CheckCircle2, ChevronRight, Search, Filter } from 'lucide-react';
import { attendanceService } from '@/services/attendanceService';
import { Button } from '@/components/ui/Button';
import type { AttendanceRecord } from '@/types';
import { toast } from 'sonner';

const AttendanceHistoryPage: React.FC = () => {
    const [records, setRecords] = useState<AttendanceRecord[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchRecords = async () => {
            try {
                const data = await attendanceService.getMyRecords();
                setRecords(data);
            } catch (err) {
                toast.error('Failed to load attendance records');
            } finally {
                setIsLoading(false);
            }
        };
        fetchRecords();
    }, []);

    return (
        <div className="max-w-6xl mx-auto space-y-10">
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <h1 className="text-3xl font-black flex items-center gap-3">
                        <History className="w-8 h-8 text-primary-400" />
                        My Attendance
                    </h1>
                    <p className="text-navy-400 mt-2 font-medium">Review your lecture attendance records week by week.</p>
                </div>

                <div className="flex gap-3">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-500" />
                        <input type="text" placeholder="Search course..." className="bg-white/5 border border-white/10 rounded-xl py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-primary-500/50" />
                    </div>
                    <Button variant="outline" className="rounded-xl border-white/10">
                        <Filter className="w-4 h-4 mr-2" />
                        Filter
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 gap-4">
                {isLoading ? (
                    Array(5).fill(0).map((_, i) => (
                        <div key={i} className="h-20 glass rounded-2xl animate-pulse"></div>
                    ))
                ) : records.length === 0 ? (
                    <div className="glass rounded-[2rem] p-20 flex flex-col items-center justify-center text-center space-y-4">
                        <div className="w-20 h-20 bg-white/5 rounded-3xl flex items-center justify-center">
                            <Calendar className="w-10 h-10 text-navy-700" />
                        </div>
                        <h3 className="text-xl font-bold">No Records Found</h3>
                        <p className="text-navy-500 max-w-xs">You haven't scanned any QR codes yet. Start attending lectures to see your records here.</p>
                    </div>
                ) : (
                    records.map((record, i) => (
                        <motion.div
                            key={record.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.05 }}
                            className="glass border border-white/5 p-6 rounded-2xl flex items-center gap-6 group hover:bg-white/5 transition-all"
                        >
                            <div className="w-14 h-14 bg-success/10 rounded-2xl flex flex-col items-center justify-center font-black">
                                <span className="text-xs text-success/60 uppercase leading-none">Wk</span>
                                <span className="text-xl text-success">{record.week_number}</span>
                            </div>

                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <BookOpen className="w-3.5 h-3.5 text-primary-400" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-navy-500">Course</span>
                                </div>
                                <h4 className="font-bold text-lg group-hover:text-primary-400 transition-colors">{record.course_name}</h4>
                            </div>

                            <div className="hidden md:block px-8 border-l border-white/5">
                                <div className="flex items-center gap-2 mb-1">
                                    <Calendar className="w-3.5 h-3.5 text-navy-500" />
                                    <span className="text-[10px] font-black uppercase tracking-widest text-navy-500">Date & Time</span>
                                </div>
                                <p className="font-medium text-sm text-navy-300">
                                    {new Date(record.scanned_at).toLocaleDateString()} at {new Date(record.scanned_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </p>
                            </div>

                            <div className="flex items-center gap-4 pl-8 border-l border-white/5">
                                <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-success/10 border border-success/20 text-success text-[10px] font-black uppercase tracking-widest">
                                    <CheckCircle2 className="w-3 h-3" />
                                    Verified
                                </div>
                                <ChevronRight className="w-5 h-5 text-navy-600 group-hover:text-white transition-transform group-hover:translate-x-1" />
                            </div>
                        </motion.div>
                    ))
                )}
            </div>
        </div>
    );
};

export default AttendanceHistoryPage;
