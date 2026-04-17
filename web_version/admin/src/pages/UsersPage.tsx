import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Plus, Search, Upload, Trash2, Edit, Eye, UserPlus, Download } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent } from '@/components/ui/Card';
import {
    Badge, Table, TableHeader, TableBody, TableRow, TableHead, TableCell,
    Dialog, Select, Skeleton, EmptyState,
} from '@/components/ui/index';
import { userService, departmentService, sectionService } from '@/services/adminService';
import type { UserResponse, DepartmentResponse, SectionResponse, CreateUserRequest, UserRole } from '@/types';
import { toast } from 'sonner';

const roleColors: Record<string, 'default' | 'success' | 'info' | 'warning'> = {
    student: 'info', professor: 'success', admin: 'default',
};

const emptyForm: CreateUserRequest = {
    university_id: '', id_card: '', full_name: '', email: '',
    role: 'student', year: 1, section_id: undefined, department_id: undefined, course_ids: [],
};

const getErrMsg = (err: unknown) =>
    (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Operation failed';

export default function UsersPage() {
    const [users, setUsers] = useState<UserResponse[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');
    const [roleFilter, setRoleFilter] = useState('');
    const [page, setPage] = useState(0);
    const limit = 20;

    const [departments, setDepartments] = useState<DepartmentResponse[]>([]);
    const [sections, setSections] = useState<SectionResponse[]>([]);

    const [createOpen, setCreateOpen] = useState(false);
    const [editOpen, setEditOpen] = useState(false);
    const [bulkOpen, setBulkOpen] = useState(false);
    const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

    const [form, setForm] = useState<CreateUserRequest>({ ...emptyForm });
    const [editingUserId, setEditingUserId] = useState<string | null>(null);
    const [formLoading, setFormLoading] = useState(false);
    const [bulkFile, setBulkFile] = useState<File | null>(null);

    const fetchUsers = useCallback(async () => {
        setLoading(true);
        try {
            const data = await userService.list({ role: roleFilter || undefined, skip: page * limit, limit });
            setUsers(data.users);
            setTotal(data.total);
        } catch { toast.error('Failed to load users'); }
        finally { setLoading(false); }
    }, [roleFilter, page]);

    useEffect(() => { fetchUsers(); }, [fetchUsers]);

    useEffect(() => {
        Promise.all([departmentService.list(), sectionService.list()])
            .then(([d, s]) => { setDepartments(d); setSections(s); })
            .catch(() => { });
    }, []);

    const resetAndClose = () => {
        setCreateOpen(false); setEditOpen(false); setEditingUserId(null);
        setForm({ ...emptyForm });
    };

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setFormLoading(true);
        try {
            await userService.create(form);
            toast.success('User created successfully! Activation email sent.');
            resetAndClose();
            fetchUsers();
        } catch (err) { toast.error(getErrMsg(err)); }
        finally { setFormLoading(false); }
    };

    const handleEdit = (user: UserResponse) => {
        setEditingUserId(user.id);
        setForm({
            university_id: user.university_id, id_card: user.id_card,
            full_name: user.full_name, email: user.email,
            role: user.role, year: user.year,
            section_id: user.section_id, department_id: user.department_id, course_ids: [],
        });
        setEditOpen(true);
    };

    const handleUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingUserId) return;
        setFormLoading(true);
        try {
            const payload: any = {
                university_id: form.university_id, id_card: form.id_card,
                full_name: form.full_name, email: form.email, role: form.role,
            };
            if (form.role === 'student') {
                payload.year = form.year;
                payload.section_id = form.section_id;
                payload.department_id = form.department_id;
            }
            await userService.update(editingUserId, payload);
            toast.success('User updated successfully!');
            resetAndClose();
            fetchUsers();
        } catch (err) { toast.error(getErrMsg(err)); }
        finally { setFormLoading(false); }
    };

    const handleDelete = async (id: string) => {
        try {
            await userService.deactivate(id);
            toast.success('User deactivated');
            setDeleteConfirm(null);
            fetchUsers();
        } catch { toast.error('Failed to deactivate user'); }
    };

    const handleBulkUpload = async () => {
        if (!bulkFile) return;
        setFormLoading(true);
        try {
            const result = await userService.bulkUpload(bulkFile);
            toast.success(`Bulk upload: ${result.succeeded} succeeded, ${result.failed} failed`);
            setBulkOpen(false); setBulkFile(null);
            fetchUsers();
        } catch { toast.error('Bulk upload failed'); }
        finally { setFormLoading(false); }
    };

    const filteredUsers = users.filter(u =>
        u.full_name.toLowerCase().includes(search.toLowerCase()) ||
        u.email.toLowerCase().includes(search.toLowerCase()) ||
        u.university_id.toLowerCase().includes(search.toLowerCase())
    );

    const totalPages = Math.ceil(total / limit);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-text-primary">Users</h1>
                    <p className="text-text-secondary mt-1">Manage students and professors</p>
                </div>
                <div className="flex gap-2">
                    <Button variant="outline" onClick={() => setBulkOpen(true)}>
                        <Upload size={16} /> Bulk Upload
                    </Button>
                    <Button onClick={() => { setEditingUserId(null); setForm({ ...emptyForm }); setCreateOpen(true); }}>
                        <Plus size={16} /> Add User
                    </Button>
                </div>
            </div>

            {/* Filters */}
            <Card><CardContent className="p-4">
                <div className="flex flex-col sm:flex-row gap-3">
                    <div className="flex-1">
                        <Input placeholder="Search by name, email, or university ID..." value={search} onChange={(e) => setSearch(e.target.value)} icon={<Search size={16} />} />
                    </div>
                    <Select
                        value={roleFilter}
                        onChange={(e) => { setRoleFilter(e.target.value); setPage(0); }}
                        options={[{ value: '', label: 'All Roles' }, { value: 'student', label: 'Students' }, { value: 'professor', label: 'Professors' }]}
                        className="w-full sm:w-44"
                    />
                </div>
            </CardContent></Card>

            {/* Table */}
            <Card>
                {loading ? (
                    <CardContent className="p-6 space-y-3">
                        {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-12 w-full rounded-lg" />)}
                    </CardContent>
                ) : filteredUsers.length === 0 ? (
                    <EmptyState icon={<UserPlus size={48} />} title="No users found" description="Create a new user or adjust your search filters."
                        action={<Button onClick={() => setCreateOpen(true)}><Plus size={16} /> Add User</Button>} />
                ) : (<>
                    <Table>
                        <TableHeader><TableRow>
                            <TableHead>Name</TableHead><TableHead>University ID</TableHead><TableHead>Email</TableHead>
                            <TableHead>Role</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Actions</TableHead>
                        </TableRow></TableHeader>
                        <TableBody>
                            {filteredUsers.map((user, index) => (
                                <motion.tr key={user.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.03 }} className="border-b border-border hover:bg-surface-muted/50 transition-colors">
                                    <TableCell className="font-medium">{user.full_name}</TableCell>
                                    <TableCell className="text-text-secondary font-mono text-xs">{user.university_id}</TableCell>
                                    <TableCell className="text-text-secondary">{user.email}</TableCell>
                                    <TableCell><Badge variant={roleColors[user.role]}>{user.role}</Badge></TableCell>
                                    <TableCell><Badge variant={user.is_active ? 'success' : 'error'}>{user.is_active ? 'Active' : 'Inactive'}</Badge></TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex items-center justify-end gap-1">
                                            <Button variant="ghost" size="icon" title="View"><Eye size={16} /></Button>
                                            <Button variant="ghost" size="icon" title="Edit" onClick={() => handleEdit(user)}><Edit size={16} /></Button>
                                            <Button variant="ghost" size="icon" title="Deactivate" onClick={() => setDeleteConfirm(user.id)}
                                                className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"><Trash2 size={16} /></Button>
                                        </div>
                                    </TableCell>
                                </motion.tr>
                            ))}
                        </TableBody>
                    </Table>

                    {/* Pagination */}
                    <div className="flex items-center justify-between p-4 border-t border-border">
                        <p className="text-sm text-text-secondary">
                            Showing {page * limit + 1}–{Math.min((page + 1) * limit, total)} of {total}
                        </p>
                        <div className="flex gap-1">
                            <Button variant="outline" size="sm" onClick={() => setPage(p => p - 1)} disabled={page === 0}>Previous</Button>
                            <Button variant="outline" size="sm" onClick={() => setPage(p => p + 1)} disabled={page >= totalPages - 1}>Next</Button>
                        </div>
                    </div>
                </>)}
            </Card>

            {/* Create/Edit User Dialog */}
            <Dialog open={createOpen || editOpen} onClose={resetAndClose}
                title={editOpen ? "Update User" : "Add New User"}
                description={editOpen ? "Update user information." : "Create a new user account and send them an activation email."}
                size="lg">
                <form onSubmit={editOpen ? handleUpdate : handleCreate} className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <Input label="University ID" value={form.university_id} onChange={(e) => setForm({ ...form, university_id: e.target.value })} required />
                        <Input label="ID Card" value={form.id_card} onChange={(e) => setForm({ ...form, id_card: e.target.value })} required />
                        <Input label="Full Name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
                        <Input label="Email" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
                        <Select label="Role" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })}
                            options={[{ value: 'student', label: 'Student' }, { value: 'professor', label: 'Professor' }]} />
                        {form.role === 'student' && (<>
                            <Select label="Year" value={String(form.year || 1)} onChange={(e) => setForm({ ...form, year: Number(e.target.value) })}
                                options={[1, 2, 3, 4].map(y => ({ value: String(y), label: `Year ${y}` }))} />
                            {(form.year === 3 || form.year === 4) && (
                                <Select label="Department" value={form.department_id || ''}
                                    onChange={(e) => setForm({ ...form, department_id: e.target.value || undefined })}
                                    options={departments.filter(d => d.name !== 'General').map(d => ({ value: d.id, label: d.name }))}
                                    placeholder="Select department" />
                            )}
                            <Select label="Section" value={form.section_id || ''}
                                onChange={(e) => setForm({ ...form, section_id: e.target.value || undefined })}
                                options={sections.map(s => ({ value: s.id, label: s.name }))} placeholder="Select section" />
                        </>)}
                    </div>
                    {form.role === 'professor' && (
                        <div className="text-sm text-text-secondary bg-surface-muted p-3 rounded-lg">
                            <p>💡 Course assignments can be managed after creating the user via the Courses page.</p>
                        </div>
                    )}
                    <div className="flex justify-end gap-2 pt-2">
                        <Button type="button" variant="outline" onClick={resetAndClose}>Cancel</Button>
                        <Button type="submit" isLoading={formLoading}>{editOpen ? 'Update User' : 'Create User'}</Button>
                    </div>
                </form>
            </Dialog>

            {/* Bulk Upload Dialog */}
            <Dialog open={bulkOpen} onClose={() => setBulkOpen(false)} title="Bulk Upload Users" description="Upload a CSV file to create multiple users at once.">
                <div className="space-y-4">
                    <div className="border-2 border-dashed border-border rounded-xl p-8 text-center hover:border-primary-400 transition-colors">
                        <Download size={32} className="mx-auto text-text-muted mb-3" />
                        <p className="text-sm text-text-secondary mb-2">Drop your CSV file here or click to browse</p>
                        <p className="text-xs text-text-muted mb-4">Format: universityId, idCard, name, email, role, year, departmentId, section, courseIds</p>
                        <input type="file" accept=".csv" onChange={(e) => setBulkFile(e.target.files?.[0] || null)}
                            className="block mx-auto text-sm text-text-secondary file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 dark:file:bg-primary-900/30 dark:file:text-primary-300" />
                    </div>
                    {bulkFile && <p className="text-sm text-text-secondary">Selected: <span className="font-medium text-text-primary">{bulkFile.name}</span></p>}
                    <div className="flex justify-end gap-2">
                        <Button variant="outline" onClick={() => { setBulkOpen(false); setBulkFile(null); }}>Cancel</Button>
                        <Button onClick={handleBulkUpload} disabled={!bulkFile} isLoading={formLoading}>Upload</Button>
                    </div>
                </div>
            </Dialog>

            {/* Delete Confirmation */}
            <Dialog open={!!deleteConfirm} onClose={() => setDeleteConfirm(null)} title="Deactivate User" description="Are you sure? This will disable the user's account." size="sm">
                <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setDeleteConfirm(null)}>Cancel</Button>
                    <Button variant="destructive" onClick={() => deleteConfirm && handleDelete(deleteConfirm)}>Deactivate</Button>
                </div>
            </Dialog>
        </div>
    );
}
