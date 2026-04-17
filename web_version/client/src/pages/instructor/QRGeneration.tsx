import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { QrCode, Sparkles, AlertCircle, Loader2, Play } from 'lucide-react';
import { attendanceService } from '@/services/attendanceService';
import api from '@/lib/api';
import { Button } from '@/components/ui/Button';
import type { Course, GenerateQRResponse } from '@/types';
import { toast } from 'sonner';
import { QRCodeSVG } from 'qrcode.react';
import logo from '../../assets/logo-small.png';

const inputClass = "w-full bg-navy-950/50 border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50 transition-all";

const QRGenerationPage: React.FC = () => {
    const [courses, setCourses] = useState<Course[]>([]);
    const [selectedCourse, setSelectedCourse] = useState('');
    const [weekNumber, setWeekNumber] = useState(1);
    const [expiry, setExpiry] = useState(15);
    const [isLoading, setIsLoading] = useState(false);
    const [qrData, setQrData] = useState<GenerateQRResponse | null>(null);

    useEffect(() => {
        api.get<Course[]>('/instructor/courses')
            .then(res => { setCourses(res.data); if (res.data.length > 0) setSelectedCourse(res.data[0].id); })
            .catch(() => toast.error('Failed to load courses'));
    }, []);

    const handleGenerate = async () => {
        if (!selectedCourse) return;
        setIsLoading(true);
        try {
            const data = await attendanceService.generateQR({ course_id: selectedCourse, week_number: weekNumber, expiry_minutes: expiry });
            setQrData(data);
            toast.success('QR Code generated successfully!');
        } catch (err: any) { toast.error(err.response?.data?.detail || 'Generation failed'); }
        finally { setIsLoading(false); }
    };

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div>
                <h1 className="text-3xl font-black flex items-center gap-3"><QrCode className="w-8 h-8 text-primary-400" /> Attendance Generator</h1>
                <p className="text-navy-400 mt-2 font-medium">Create a new attendance session for your students.</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Settings */}
                <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} className="lg:col-span-1 space-y-6">
                    <div className="glass border border-white/5 p-8 rounded-[2rem] space-y-6">
                        <h3 className="text-lg font-bold flex items-center gap-2"><Sparkles className="w-4 h-4 text-primary-400" /> Session Configuration</h3>
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-sm font-bold text-navy-400 ml-1">SELECT COURSE</label>
                                <select value={selectedCourse} onChange={(e) => setSelectedCourse(e.target.value)} className={`${inputClass} font-medium appearance-none`}>
                                    {courses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                                </select>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-navy-400 ml-1">WEEK NO.</label>
                                    <input type="number" min="1" max="16" value={weekNumber} onChange={(e) => setWeekNumber(parseInt(e.target.value))} className={inputClass} />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-sm font-bold text-navy-400 ml-1">EXPIRY (MIN)</label>
                                    <input type="number" min="1" value={expiry} onChange={(e) => setExpiry(parseInt(e.target.value))} className={inputClass} />
                                </div>
                            </div>
                        </div>
                        <Button variant="gradient" className="w-full h-14 rounded-2xl font-bold mt-4" onClick={handleGenerate} disabled={isLoading}>
                            {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Play className="w-5 h-5 mr-3 fill-white" /> Start Session</>}
                        </Button>
                        <div className="bg-primary-500/5 border border-primary-500/10 p-4 rounded-2xl flex gap-3 items-start">
                            <AlertCircle className="w-4 h-4 text-primary-400 shrink-0 mt-0.5" />
                            <p className="text-[10px] text-navy-300 leading-relaxed font-medium">
                                The QR code remains active until the expiry time or until you manually close the session.
                            </p>
                        </div>
                    </div>
                </motion.div>

                {/* Display */}
                <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="lg:col-span-2">
                    <div className="glass border border-white/5 rounded-[2.5rem] h-full flex flex-col items-center justify-center p-12 min-h-[500px] relative overflow-hidden group">
                        <AnimatePresence mode="wait">
                            {!qrData ? (
                                <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="text-center space-y-4">
                                    <div className="w-24 h-24 bg-white/5 rounded-[2rem] flex items-center justify-center mx-auto mb-6">
                                        <QrCode className="w-10 h-10 text-navy-600" />
                                    </div>
                                    <h4 className="text-xl font-bold text-navy-400">Ready to Generate</h4>
                                    <p className="text-navy-500 max-w-[280px] text-sm">Select a course and click start to display the attendance QR code.</p>
                                </motion.div>
                            ) : (
                                <motion.div key="active" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="flex flex-col items-center space-y-8">
                                    <div className="relative p-6 bg-white rounded-[2rem] shadow-[0_0_50px_rgba(255,255,255,0.1)]">
                                        <div className="w-64 h-64 bg-white flex items-center justify-center">
                                            <QRCodeSVG value={qrData.token} size={256} level="H" includeMargin={false}
                                                imageSettings={{ src: logo, x: undefined, y: undefined, height: 48, width: 48, excavate: true }} />
                                        </div>
                                    </div>
                                    <div className="text-center">
                                        <div className="flex items-center justify-center gap-2 mb-2">
                                            <span className="relative flex h-3 w-3">
                                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-success opacity-75"></span>
                                                <span className="relative inline-flex rounded-full h-3 w-3 bg-success"></span>
                                            </span>
                                            <span className="text-success font-black text-xs uppercase tracking-[0.2em]">Session Active</span>
                                        </div>
                                        <h3 className="text-2xl font-black">Week {qrData.week_number}</h3>
                                        <p className="text-navy-400 font-medium">Expires at {new Date(qrData.expires_at).toLocaleTimeString()}</p>
                                    </div>
                                    <Button variant="outline" className="rounded-xl border-white/10 hover:bg-error/10 hover:text-error hover:border-error/20" onClick={() => setQrData(null)}>
                                        Close Session
                                    </Button>
                                </motion.div>
                            )}
                        </AnimatePresence>
                        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary-900/10 rounded-full blur-[100px] pointer-events-none"></div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
};

export default QRGenerationPage;
