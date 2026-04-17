import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ClipboardList, ArrowLeft, Search, User, Clock, Award, Loader2 } from 'lucide-react';
import { quizService } from '@/services/quizService';
import type { QuizSubmissionsResponse } from '@/types';
import { toast } from 'sonner';
import { Button } from '@/components/ui/Button';

const QuizSubmissions: React.FC = () => {
    const { quizId } = useParams<{ quizId: string }>();
    const navigate = useNavigate();
    const [data, setData] = useState<QuizSubmissionsResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        if (!quizId) return;
        quizService.getQuizSubmissions(quizId)
            .then(setData).catch(() => toast.error('Failed to load submissions'))
            .finally(() => setIsLoading(false));
    }, [quizId]);

    const filtered = data?.submissions.filter(s =>
        s.student_name.toLowerCase().includes(searchTerm.toLowerCase()) || s.university_id.includes(searchTerm)
    ) || [];

    if (isLoading) return <div className="h-[60vh] flex items-center justify-center"><Loader2 className="w-10 h-10 text-primary-500 animate-spin" /></div>;
    if (!data) return null;

    const initials = (name: string) => name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="sm" onClick={() => navigate(-1)} className="text-navy-400 hover:text-white">
                        <ArrowLeft className="w-4 h-4 mr-2" /> Back
                    </Button>
                    <div>
                        <h1 className="text-3xl font-black flex items-center gap-3"><ClipboardList className="w-8 h-8 text-primary-400" /> {data.quiz_title}</h1>
                        <p className="text-navy-400 font-medium">Student Performance & Submissions</p>
                    </div>
                </div>
                <div className="relative w-64">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-500" />
                    <input type="text" placeholder="Search student..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-primary-500/50" />
                </div>
            </div>

            <div className="glass border border-white/5 rounded-[2rem] overflow-hidden">
                <table className="w-full text-left">
                    <thead>
                        <tr className="bg-white/5 border-b border-white/5">
                            {['Student', 'University ID', 'Score', 'Submitted At'].map(h => (
                                <th key={h} className="px-8 py-6 text-[10px] font-black uppercase tracking-widest text-navy-400">{h}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {filtered.length > 0 ? filtered.map((sub, i) => (
                            <motion.tr key={sub.student_id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: i * 0.05 }} className="group hover:bg-white/[0.02] transition-colors">
                                <td className="px-8 py-6">
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 rounded-xl bg-navy-800 flex items-center justify-center text-primary-400 font-black text-xs shadow-inner">{initials(sub.student_name)}</div>
                                        <div>
                                            <p className="font-bold text-white group-hover:text-primary-400 transition-colors">{sub.student_name}</p>
                                            <div className="flex items-center gap-1 text-[10px] text-navy-500 font-black uppercase tracking-tighter"><User className="w-2.5 h-2.5" /> Student</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-8 py-6"><span className="font-mono text-xs text-navy-300 bg-white/5 px-2 py-1 rounded-md">{sub.university_id}</span></td>
                                <td className="px-8 py-6">
                                    <div className="flex items-center gap-3">
                                        <div className="flex-1 max-w-[100px] h-2 bg-navy-800 rounded-full overflow-hidden">
                                            <div className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full transition-all duration-1000" style={{ width: `${sub.score}%` }} />
                                        </div>
                                        <span className="font-black text-accent-400">{sub.score}%</span>
                                    </div>
                                </td>
                                <td className="px-8 py-6">
                                    <div className="flex flex-col">
                                        <span className="text-sm font-medium text-navy-300">{new Date(sub.submitted_at).toLocaleDateString()}</span>
                                        <span className="text-[10px] text-navy-500 font-black uppercase flex items-center gap-1">
                                            <Clock className="w-2.5 h-2.5" /> {new Date(sub.submitted_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    </div>
                                </td>
                            </motion.tr>
                        )) : (
                            <tr><td colSpan={4} className="px-8 py-20 text-center">
                                <div className="flex flex-col items-center justify-center space-y-4 text-navy-500">
                                    <div className="w-16 h-16 bg-white/5 rounded-[1.5rem] flex items-center justify-center"><Award className="w-8 h-8 opacity-20" /></div>
                                    <p className="font-bold">No submissions found.</p>
                                </div>
                            </td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default QuizSubmissions;
