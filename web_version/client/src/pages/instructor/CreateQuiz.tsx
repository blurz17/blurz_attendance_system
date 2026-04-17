import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileEdit, Plus, Trash2, CheckCircle2, AlertCircle, Loader2, Save, Layers, X } from 'lucide-react';
import api from '@/lib/api';
import { quizService } from '@/services/quizService';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import type { Course, CreateQuizRequest } from '@/types';
import { toast } from 'sonner';

const defaultQuestion = () => ({
    text: '', order_index: 0,
    choices: [{ text: '', is_correct: true }, { text: '', is_correct: false }],
});

const CreateQuizPage: React.FC = () => {
    const [courses, setCourses] = useState<Course[]>([]);
    const [sections, setSections] = useState<{ id: string; name: string }[]>([]);
    const [title, setTitle] = useState('');
    const [selectedCourse, setSelectedCourse] = useState('');
    const [selectedSection, setSelectedSection] = useState('');
    const [dueDate, setDueDate] = useState('');
    const [questions, setQuestions] = useState<CreateQuizRequest['questions']>([defaultQuestion()]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        Promise.all([api.get<Course[]>('/instructor/courses'), api.get<{ id: string; name: string }[]>('/sections')])
            .then(([c, s]) => { setCourses(c.data); setSections(s.data); if (c.data.length > 0) setSelectedCourse(c.data[0].id); })
            .catch(() => toast.error('Failed to load initial data'));
    }, []);

    const updateQuestion = (qIndex: number, updates: Partial<CreateQuizRequest['questions'][0]>) => {
        setQuestions(qs => qs.map((q, i) => i === qIndex ? { ...q, ...updates } : q));
    };

    const handleCreate = async () => {
        if (!title || !selectedCourse) { toast.error('Please fill in all required fields'); return; }
        if (questions.find(q => !q.choices.some(c => c.is_correct))) { toast.error('Each question must have at least one correct answer'); return; }

        setIsLoading(true);
        try {
            await quizService.createQuiz({ title, course_id: selectedCourse, due_date: dueDate || null, target_section_id: selectedSection || null, questions });
            toast.success('Quiz created successfully!');
            setTitle(''); setQuestions([defaultQuestion()]);
        } catch (err: any) { toast.error(err.response?.data?.detail || 'Failed to create quiz'); }
        finally { setIsLoading(false); }
    };

    const inputClass = "w-full bg-navy-950/50 border border-white/10 rounded-xl py-3 px-4 text-white focus:outline-none focus:ring-2 focus:ring-primary-500/50 transition-all";

    return (
        <div className="max-w-5xl mx-auto space-y-10">
            <div className="flex items-end justify-between">
                <div>
                    <h1 className="text-3xl font-black flex items-center gap-3">
                        <FileEdit className="w-8 h-8 text-primary-400" /> Quiz Creator
                    </h1>
                    <p className="text-navy-400 mt-2 font-medium">Design engaging quizzes for your students.</p>
                </div>
                <Button variant="gradient" className="rounded-xl h-12 px-8 font-bold shadow-xl" onClick={handleCreate} disabled={isLoading}>
                    {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <><Save className="w-4 h-4 mr-2" /> Publish Quiz</>}
                </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Sidebar */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="glass border border-white/5 p-8 rounded-[2rem] space-y-6">
                        <h3 className="text-lg font-bold flex items-center gap-2">
                            <Layers className="w-4 h-4 text-primary-400" /> General Settings
                        </h3>
                        <div className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-xs font-black text-navy-500 uppercase ml-1">Quiz Title</label>
                                <input type="text" placeholder="e.g. Midterm Assessment" value={title}
                                    onChange={(e) => setTitle(e.target.value)} className={inputClass} />
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-black text-navy-500 uppercase ml-1">Select Course</label>
                                <select value={selectedCourse} onChange={(e) => setSelectedCourse(e.target.value)} className={`${inputClass} appearance-none`}>
                                    {courses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-black text-navy-500 uppercase ml-1">Target Section (Optional)</label>
                                <select value={selectedSection} onChange={(e) => setSelectedSection(e.target.value)} className={`${inputClass} appearance-none`}>
                                    <option value="">All Sections</option>
                                    {sections.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                                </select>
                            </div>
                            <div className="space-y-2">
                                <label className="text-xs font-black text-navy-500 uppercase ml-1">Due Date</label>
                                <input type="datetime-local" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className={`${inputClass} font-sans`} />
                            </div>
                        </div>
                    </div>
                    <div className="p-6 rounded-3xl bg-primary-500/5 border border-primary-500/10 text-xs text-navy-400 leading-relaxed font-medium">
                        <AlertCircle className="w-4 h-4 mb-2 text-primary-400" />
                        Ensure each question has at least one correct answer. The quiz will be automatically graded upon student submission.
                    </div>
                </div>

                {/* Questions Builder */}
                <div className="lg:col-span-2 space-y-6">
                    <AnimatePresence mode="popLayout">
                        {questions.map((question, qIndex) => (
                            <motion.div key={qIndex} initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.95 }} className="glass border border-white/5 p-8 rounded-[2rem] space-y-6 relative group">
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-8 h-8 rounded-lg bg-navy-800 flex items-center justify-center text-xs font-black text-primary-400">{qIndex + 1}</div>
                                        <h4 className="font-bold">Question</h4>
                                    </div>
                                    <Button variant="ghost" size="icon" className="text-navy-600 hover:text-error" onClick={() => setQuestions(qs => qs.filter((_, i) => i !== qIndex))}>
                                        <Trash2 className="w-4 h-4" />
                                    </Button>
                                </div>

                                <textarea placeholder="Enter your question text here..." value={question.text}
                                    onChange={(e) => updateQuestion(qIndex, { text: e.target.value })}
                                    className="w-full h-24 bg-navy-950/50 border border-white/10 rounded-2xl p-4 text-white resize-none focus:outline-none focus:ring-2 focus:ring-primary-500/50" />

                                <div className="space-y-3">
                                    <p className="text-[10px] font-black text-navy-500 uppercase tracking-widest ml-1">Choices</p>
                                    {question.choices.map((choice, cIndex) => (
                                        <div key={cIndex} className="flex items-center gap-3 group/choice">
                                            <button
                                                onClick={() => updateQuestion(qIndex, {
                                                    choices: question.choices.map((c, i) => ({ ...c, is_correct: i === cIndex }))
                                                })}
                                                className={cn("w-6 h-6 rounded-full flex items-center justify-center border transition-all",
                                                    choice.is_correct ? "bg-success border-success text-white shadow-lg shadow-success/20" : "border-white/10 text-transparent")}>
                                                <CheckCircle2 className="w-4 h-4" />
                                            </button>
                                            <input type="text" placeholder={`Choice ${cIndex + 1}`} value={choice.text}
                                                onChange={(e) => {
                                                    const newChoices = [...question.choices];
                                                    newChoices[cIndex] = { ...newChoices[cIndex], text: e.target.value };
                                                    updateQuestion(qIndex, { choices: newChoices });
                                                }}
                                                className="flex-1 bg-white/5 border border-white/5 rounded-xl py-2 px-4 text-sm text-white focus:outline-none focus:border-primary-500/30" />
                                            <Button variant="ghost" size="icon" className="h-8 w-8 text-navy-700 opacity-0 group-hover/choice:opacity-100"
                                                onClick={() => updateQuestion(qIndex, { choices: question.choices.filter((_, i) => i !== cIndex) })}>
                                                <X className="w-3 h-3" />
                                            </Button>
                                        </div>
                                    ))}
                                    <Button variant="ghost" size="sm" className="text-primary-400 font-bold hover:bg-primary-500/10"
                                        onClick={() => updateQuestion(qIndex, { choices: [...question.choices, { text: '', is_correct: false }] })}>
                                        <Plus className="w-3 h-3 mr-2" /> Add Choice
                                    </Button>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>

                    <Button variant="outline" className="w-full h-16 rounded-[1.5rem] border-dashed border-white/10 bg-white/5 hover:bg-white/10 text-navy-400 font-bold"
                        onClick={() => setQuestions([...questions, { ...defaultQuestion(), order_index: questions.length }])}>
                        <Plus className="w-5 h-5 mr-3" /> Add New Question
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default CreateQuizPage;
