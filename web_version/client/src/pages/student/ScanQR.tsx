import React, { useState, useEffect } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { motion, AnimatePresence } from 'framer-motion';
import { QrCode, Camera, Keyboard, Loader2, CheckCircle2, AlertCircle, ArrowLeft } from 'lucide-react';
import { attendanceService } from '@/services/attendanceService';
import { Button } from '@/components/ui/Button';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const ScanQR: React.FC = () => {
    const navigate = useNavigate();
    const [scanMethod, setScanMethod] = useState<'camera' | 'manual'>('camera');
    const [manualToken, setManualToken] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    useEffect(() => {
        if (scanMethod !== 'camera' || isSuccess) return;
        const scanner = new Html5QrcodeScanner("reader", { fps: 10, qrbox: { width: 250, height: 250 } }, false);
        scanner.render(async (decodedText) => {
            if (isProcessing) return;
            handleScan(decodedText);
            scanner.clear();
        }, () => { /* ignore scan failures */ });
        return () => { scanner.clear().catch(() => {}); };
    }, [scanMethod, isSuccess]);

    const handleScan = async (token: string) => {
        setIsProcessing(true);
        try {
            await attendanceService.scanQR(token);
            setIsSuccess(true);
            toast.success('Attendance recorded successfully!');
            setTimeout(() => navigate('/attendance'), 2000);
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Scanning failed. Invalid or expired token.');
            setIsProcessing(false);
        }
    };

    const methods = [
        { key: 'camera' as const, icon: Camera, label: 'Camera Scan' },
        { key: 'manual' as const, icon: Keyboard, label: 'Manual Entry' },
    ];

    return (
        <div className="max-w-2xl mx-auto space-y-8">
            <div className="flex items-center gap-4">
                <Button variant="ghost" size="icon" onClick={() => navigate(-1)} className="rounded-full"><ArrowLeft className="w-5 h-5" /></Button>
                <div>
                    <h1 className="text-3xl font-black flex items-center gap-3"><QrCode className="w-8 h-8 text-primary-400" /> Scan Attendance</h1>
                    <p className="text-navy-400 font-medium">Mark your presence for today's session.</p>
                </div>
            </div>

            <div className="glass border border-white/5 rounded-[2.5rem] overflow-hidden">
                <div className="flex p-2 bg-navy-950/50 border-b border-white/5">
                    {methods.map(m => (
                        <button key={m.key} onClick={() => setScanMethod(m.key)}
                            className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl font-bold transition-all ${scanMethod === m.key ? 'bg-primary-500 text-white shadow-lg' : 'text-navy-400 hover:text-white'}`}>
                            <m.icon className="w-4 h-4" /> {m.label}
                        </button>
                    ))}
                </div>

                <div className="p-10">
                    <AnimatePresence mode="wait">
                        {isSuccess ? (
                            <motion.div key="success" initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="text-center space-y-6">
                                <div className="w-24 h-24 bg-success/20 rounded-[2.5rem] flex items-center justify-center mx-auto border border-success/30">
                                    <CheckCircle2 className="w-12 h-12 text-success" />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-black">Attendance Confirmed!</h2>
                                    <p className="text-navy-400 mt-2">Redirecting to your records...</p>
                                </div>
                            </motion.div>
                        ) : scanMethod === 'camera' ? (
                            <motion.div key="camera" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
                                <div id="reader" className="overflow-hidden rounded-3xl border border-white/10 bg-black/20 aspect-square max-w-[400px] mx-auto"></div>
                                <div className="text-center text-xs text-navy-500 font-medium flex items-center justify-center gap-2">
                                    <AlertCircle className="w-3 h-3" /> Point your camera at the instructor's screen
                                </div>
                            </motion.div>
                        ) : (
                            <motion.div key="manual" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-6">
                                <form onSubmit={(e) => { e.preventDefault(); if (manualToken.trim()) handleScan(manualToken.trim()); }} className="space-y-4">
                                    <div className="space-y-2">
                                        <label className="text-sm font-bold text-navy-400 ml-1 uppercase tracking-widest text-[10px]">Security Token</label>
                                        <input type="text" placeholder="Enter the code shown below the QR..." value={manualToken} onChange={(e) => setManualToken(e.target.value)}
                                            className="w-full bg-navy-950/50 border border-white/10 rounded-2xl py-4 px-6 text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50 text-center font-mono tracking-widest uppercase transition-all" />
                                    </div>
                                    <Button type="submit" variant="gradient" className="w-full h-14 rounded-2xl font-bold shadow-xl" disabled={isProcessing || !manualToken.trim()}>
                                        {isProcessing ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Confirm Attendance'}
                                    </Button>
                                </form>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>

            <div className="p-6 bg-primary-500/5 border border-primary-500/10 rounded-[2rem] flex gap-4 items-start">
                <div className="w-10 h-10 rounded-xl bg-primary-500/10 flex items-center justify-center shrink-0"><QrCode className="w-5 h-5 text-primary-400" /></div>
                <div>
                    <h4 className="font-bold text-sm mb-1">How it works</h4>
                    <p className="text-xs text-navy-400 leading-relaxed">
                        Scanning the QR code automatically validates your location and enrollment status to record your attendance for the current session.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ScanQR;
