import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Plus, Edit, Trash2, BookOpen, Search } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent } from '@/components/ui/Card';
import {
    Badge, Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
    Dialog, Select, MultiSelect, Skeleton, EmptyState,
} from '@/components/ui/index';
import { courseService, departmentService, userService } from '@/services/adminService';
import type { CourseResponse, DepartmentResponse, UserResponse, CreateCourseRequest } from '@/types';
import { toast } from 'sonner';

const emptyForm: CreateCourseRequest = { name: '', year: 1, professor_ids: [] };
const getErrMsg = (err: unknown) =>
    (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Operation failed';

export default function CoursesPage() {
    const [courses, setCourses] = useState<CourseResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [departments, setDepartments] = useState<DepartmentResponse[]>([]);
    const [professors, setProfessors] = useState<UserResponse[]>([]);
    const [search, setSearch] = useState('');
    const [yearFilter, setYearFilter] = useState('');

    const [dialogOpen, setDialogOpen] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [form, setForm] = useState<CreateCourseRequest>({ ...emptyForm });
    const [saving, setSaving] = useState(false);
    const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

    const fetchCourses = useCallback(async () => {
        setLoading(true);
        try { setCourses(await courseService.list({ year: yearFilter ? Number(yearFilter) : undefined })); }
        catch { toast.error('Failed to load courses'); }
        finally { setLoading(false); }
    }, [yearFilter]);

    useEffect(() => { fetchCourses(); }, [fetchCourses]);

    useEffect(() => {
        Promise.all([departmentService.list(), userService.list({ role: 'professor', limit: 100 })])
            .then(([d, p]) => { setDepartments(d); setProfessors(p.users); })
            .catch(() => { });
    }, []);

    const getDeptName = (id?: string) => departments.find(d => d.id === id)?.name || '—';

    const resetAndClose = () => { setDialogOpen(false); setEditingId(null); setForm({ ...emptyForm }); };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        try {
            const data = { ...form };
            if (data.year <= 2) {
                const general = departments.find(d => d.name === 'General');
                if (general) data.department_id = general.id;
            }
            editingId ? await courseService.update(editingId, data) : await courseService.create(data);
            toast.success(editingId ? 'Course updated' : 'Course created');
            resetAndClose();
            fetchCourses();
        } catch (err) { toast.error(getErrMsg(err)); }
        finally { setSaving(false); }
    };

    const handleEdit = (course: CourseResponse) => {
        setEditingId(course.id);
        setForm({ name: course.name, year: course.year, department_id: course.department_id || undefined, professor_ids: course.professor_ids || [] });
        setDialogOpen(true);
    };

    const handleDelete = async (id: string) => {
        try { await courseService.delete(id); toast.success('Course deleted'); setDeleteConfirm(null); fetchCourses(); }
        catch { toast.error('Failed to delete. Course may have enrollments.'); }
    };

    const filtered = courses.filter(c => c.name.toLowerCase().includes(search.toLowerCase()));

    return (
        <div className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-text-primary">Courses</h1>
                    <p className="text-text-secondary mt-1">Manage academic courses and assignments</p>
                </div>
                <Button onClick={() => { setEditingId(null); setForm({ ...emptyForm }); setDialogOpen(true); }}>
                    <Plus size={16} /> Add Course
                </Button>
            </div>

            <Card><CardContent className="p-4">
                <div className="flex flex-col sm:flex-row gap-3">
                    <div className="flex-1">
                        <Input placeholder="Search courses..." value={search} onChange={(e) => setSearch(e.target.value)} icon={<Search size={16} />} />
                    </div>
                    <Select value={yearFilter} onChange={(e) => setYearFilter(e.target.value)} className="w-full sm:w-36"
                        options={[{ value: '', label: 'All Years' }, ...([1,2,3,4].map(y => ({ value: String(y), label: `Year ${y}` })))]} />
                </div>
            </CardContent></Card>

            <Card>
                {loading ? (
                    <CardContent className="p-6 space-y-3">
                        {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
                    </CardContent>
                ) : filtered.length === 0 ? (
                    <EmptyState icon={<BookOpen size={48} />} title="No courses found" description="Create a new course or adjust your filters."
                        action={<Button onClick={() => setDialogOpen(true)}><Plus size={16} /> Add Course</Button>} />
                ) : (
                    <Table>
                        <TableHeader><TableRow>
                            <TableHead>Course Name</TableHead><TableHead>Year</TableHead><TableHead>Department</TableHead>
                            <TableHead>Professors</TableHead><TableHead className="text-right">Actions</TableHead>
                        </TableRow></TableHeader>
                        <TableBody>
                            {filtered.map((course, i) => (
                                <motion.tr key={course.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: i * 0.03 }} className="border-b border-border hover:bg-surface-muted/50">
                                    <TableCell className="font-medium">{course.name}</TableCell>
                                    <TableCell><Badge variant="info">Year {course.year}</Badge></TableCell>
                                    <TableCell className="text-text-secondary">{getDeptName(course.department_id)}</TableCell>
                                    <TableCell>
                                        <div className="flex flex-wrap gap-1">
                                            {course.professor_ids?.length ? course.professor_ids.map(id => (
                                                <Badge key={id} variant="outline" className="text-[10px] py-0 px-1.5 whitespace-nowrap">
                                                    {professors.find(p => p.id === id)?.full_name || 'Professor'}
                                                </Badge>
                                            )) : <span className="text-text-muted">—</span>}
                                        </div>
                                    </TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex items-center justify-end gap-1">
                                            <Button variant="ghost" size="icon" onClick={() => handleEdit(course)} title="Edit"><Edit size={16} /></Button>
                                            <Button variant="ghost" size="icon" onClick={() => setDeleteConfirm(course.id)} title="Delete"
                                                className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"><Trash2 size={16} /></Button>
                                        </div>
                                    </TableCell>
                                </motion.tr>
                            ))}
                        </TableBody>
                    </Table>
                )}
            </Card>

            <Dialog open={dialogOpen} onClose={resetAndClose} title={editingId ? 'Edit Course' : 'Add Course'} size="lg">
                <form onSubmit={handleSave} className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <Input label="Course Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="e.g. Data Structures" required />
                        <Select label="Year" value={String(form.year)}
                            onChange={(e) => setForm({ ...form, year: Number(e.target.value), department_id: Number(e.target.value) <= 2 ? undefined : form.department_id })}
                            options={[1,2,3,4].map(y => ({ value: String(y), label: `Year ${y}` }))} />
                        {form.year >= 3 && (
                            <Select label="Department" value={form.department_id || ''}
                                onChange={(e) => setForm({ ...form, department_id: e.target.value || undefined })}
                                options={departments.filter(d => d.name !== 'General').map(d => ({ value: d.id, label: d.name }))} placeholder="Select department" />
                        )}
                        <MultiSelect label="Assign Professors" value={form.professor_ids || []}
                            onChange={(vals) => setForm({ ...form, professor_ids: vals })}
                            options={professors.map(p => ({ value: p.id, label: p.full_name }))} placeholder="Select professors" />
                    </div>
                    {form.year <= 2 && (
                        <div className="text-sm text-text-secondary bg-surface-muted p-3 rounded-lg">
                            ℹ️ Year 1 & 2 courses are automatically assigned to the "General" department.
                        </div>
                    )}
                    <div className="flex justify-end gap-2 pt-2">
                        <Button type="button" variant="outline" onClick={resetAndClose}>Cancel</Button>
                        <Button type="submit" isLoading={saving}>{editingId ? 'Update' : 'Create'}</Button>
                    </div>
                </form>
            </Dialog>

            <Dialog open={!!deleteConfirm} onClose={() => setDeleteConfirm(null)} title="Delete Course"
                description="This will remove the course and all related data. Are you sure?" size="sm">
                <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setDeleteConfirm(null)}>Cancel</Button>
                    <Button variant="destructive" onClick={() => deleteConfirm && handleDelete(deleteConfirm)}>Delete</Button>
                </div>
            </Dialog>
        </div>
    );
}
