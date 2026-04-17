import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FileEdit, ClipboardList, Clock, CheckCircle2, BookOpen, Timer, Loader2, ArrowRight } from 'lucide-react';
import { quizService } from '@/services/quizService';
import { Button } from '@/components/ui/Button';
import type { QuizListItem, QuizDetail } from '@/types';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

const QuizCenter: React.FC = () => {
    const [quizzes, setQuizzes] = useState<QuizListItem[]>([]);
    const [activeQuiz, setActiveQuiz] = useState<QuizDetail | null>(null);
    const [answers, setAnswers] = useState<Record<string, string>>({});
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [activeTab, setActiveTab] = useState<'available' | 'completed'>('available');

    useEffect(() => {
        quizService.getAvailableQuizzes()
            .then(setQuizzes).catch(() => toast.error('Failed to load quizzes'))
            .finally(() => setIsLoading(false));
    }, []);

    const handleStartQuiz = async (id: string) => {
        setIsLoading(true);
        try { setActiveQuiz(await quizService.getQuizDetails(id)); setAnswers({}); }
        catch { toast.error('Failed to load quiz details'); }
        finally { setIsLoading(false); }
    };

    const handleSubmit = async () => {
        if (!activeQuiz) return;
        if (Object.keys(answers).length < activeQuiz.questions.length) { toast.warning('Please answer all questions before submitting.'); return; }

        setIsSubmitting(true);
        try {
            const response = await quizService.submitQuiz(activeQuiz.id, {
                answers: Object.entries(answers).map(([qId, choiceId]) => ({ question_id: qId, chosen_choice_id: choiceId }))
            });
            toast.success(`${response.message}! Score: ${response.score}/${activeQuiz.questions.length}`);
            setActiveQuiz(null);
            setQuizzes(await quizService.getAvailableQuizzes());
        } catch (err: any) { toast.error(err.response?.data?.detail || 'Submission failed'); }
        finally { setIsSubmitting(false); }
    };

    // ─── Active Quiz View ───
    if (activeQuiz) {
        return (
            <div className="max-w-4xl mx-auto space-y-8">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" onClick={() => setActiveQuiz(null)} className="text-navy-400">Cancel</Button>
                        <h2 className="text-2xl font-black">{activeQuiz.title}</h2>
                    </div>
                    <div className="flex items-center gap-2 px-4 py-2 bg-primary-500/10 border border-primary-500/20 rounded-xl text-primary-400 font-bold">
                        <Timer className="w-4 h-4" /><span>TIME SENSITIVE</span>
                    </div>
                </div>

                <div className="space-y-6 pb-20">
                    {activeQuiz.questions.map((q, i) => (
                        <motion.div key={q.id} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1 }} className="glass border border-white/5 p-8 rounded-[2rem] space-y-6">
                            <div className="flex items-start gap-4">
                                <div className="w-8 h-8 rounded-lg bg-navy-800 flex items-center justify-center text-xs font-black text-primary-400 shrink-0">{i + 1}</div>
                                <h4 className="text-lg font-bold leading-tight">{q.text}</h4>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pl-12">
                                {q.choices.map(choice => (
                                    <button key={choice.id} onClick={() => setAnswers(prev => ({ ...prev, [q.id]: choice.id }))}
                                        className={cn("p-4 rounded-xl border text-left transition-all font-medium text-sm flex items-center justify-between group",
                                            answers[q.id] === choice.id
                                                ? "bg-primary-500 border-primary-500 text-white shadow-lg shadow-primary-500/20"
                                                : "bg-white/5 border-white/5 text-navy-300 hover:bg-white/10 hover:border-white/10")}>
                                        {choice.text}
                                        {answers[q.id] === choice.id && <CheckCircle2 className="w-4 h-4" />}
                                    </button>
                                ))}
                            </div>
                        </motion.div>
                    ))}
                </div>

                <div className="fixed bottom-8 left-[280px] right-0 px-8 flex justify-center z-30">
                    <Button variant="gradient" size="lg" className="w-full max-w-md h-16 rounded-2xl font-bold shadow-2xl" onClick={handleSubmit} disabled={isSubmitting}>
                        {isSubmitting ? <Loader2 className="w-6 h-6 animate-spin" /> : 'Finalize Submission'}
                    </Button>
                </div>
            </div>
        );
    }

    // ─── Quiz List View ───
    const tabs = [
        { key: 'available' as const, label: 'Available', active: 'bg-primary-500 text-white shadow-lg shadow-primary-500/20' },
        { key: 'completed' as const, label: 'Completed', active: 'bg-accent-500 text-white shadow-lg shadow-accent-500/20' },
    ];

    const filteredQuizzes = quizzes.filter(q => activeTab === 'available' ? !q.is_submitted : q.is_submitted);

    return (
        <div className="max-w-6xl mx-auto space-y-10">
            <div>
                <h1 className="text-3xl font-black flex items-center gap-3"><ClipboardList className="w-8 h-8 text-primary-400" /> Quiz Center</h1>
                <p className="text-navy-400 mt-2 font-medium">Test your knowledge and track your performance.</p>
            </div>

            <div className="flex gap-4 p-1 bg-white/5 rounded-2xl w-fit">
                {tabs.map(tab => (
                    <button key={tab.key} onClick={() => setActiveTab(tab.key)}
                        className={cn("px-6 py-2.5 rounded-xl text-sm font-bold transition-all", activeTab === tab.key ? tab.active : "text-navy-400 hover:text-white")}>
                        {tab.label}
                    </button>
                ))}
            </div>

            <div className="grid grid-cols-1 gap-6">
                {isLoading ? (
                    Array(3).fill(0).map((_, i) => <div key={i} className="h-32 glass rounded-2xl animate-pulse"></div>)
                ) : filteredQuizzes.length === 0 ? (
                    <div className="glass rounded-[2rem] p-20 flex flex-col items-center justify-center text-center space-y-4">
                        <div className="w-20 h-20 bg-white/5 rounded-3xl flex items-center justify-center"><FileEdit className="w-10 h-10 text-navy-700" /></div>
                        <h3 className="text-xl font-bold">No {activeTab === 'available' ? 'Active' : 'Completed'} Quizzes</h3>
                        <p className="text-navy-500 max-w-xs">
                            {activeTab === 'available' ? "You're all caught up! There are no quizzes available for your courses right now." : "You haven't completed any quizzes yet."}
                        </p>
                    </div>
                ) : (
                    filteredQuizzes.map((quiz, i) => (
                        <motion.div key={quiz.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }}
                            className="p-8 rounded-[2rem] glass border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-6 hover:bg-white/[0.04] transition-all group">
                            <div className="flex items-center gap-6">
                                <div className={cn("w-16 h-16 rounded-2xl flex items-center justify-center shadow-inner",
                                    quiz.is_submitted ? "bg-accent-500/10 text-accent-400" : "bg-navy-800 text-primary-400")}>
                                    <BookOpen className="w-8 h-8" />
                                </div>
                                <div className="space-y-1">
                                    <h3 className="text-xl font-bold group-hover:text-primary-400 transition-colors uppercase tracking-tight">{quiz.title}</h3>
                                    <div className="flex items-center gap-4 text-xs font-bold text-navy-500 uppercase tracking-widest">
                                        {quiz.is_submitted
                                            ? <span className="flex items-center gap-1.5 text-accent-400"><CheckCircle2 className="w-3.5 h-3.5" /> Score: {quiz.score}%</span>
                                            : <span className="flex items-center gap-1.5 text-navy-400"><Clock className="w-3.5 h-3.5" /> Due soon</span>}
                                        <span className="w-1 h-1 bg-navy-800 rounded-full"></span>
                                        <span>{quiz.course_name}</span>
                                    </div>
                                </div>
                            </div>
                            {!quiz.is_submitted ? (
                                <Button variant="outline" onClick={() => handleStartQuiz(quiz.id)}
                                    className="h-14 px-8 rounded-xl border-white/10 group-hover:bg-primary-500 group-hover:text-white group-hover:border-primary-500 transition-all font-bold">
                                    Take Quiz <ArrowRight className="ml-3 w-4 h-4" />
                                </Button>
                            ) : (
                                <div className="flex items-center gap-2 px-6 py-3 rounded-xl bg-accent-500/10 border border-accent-500/20 text-accent-400 text-sm font-black uppercase tracking-widest">
                                    <CheckCircle2 className="w-4 h-4" /> Submitted
                                </div>
                            )}
                        </motion.div>
                    ))
                )}
            </div>
        </div>
    );
};

export default QuizCenter;
