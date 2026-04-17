import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Plus, Edit, Trash2, Layers } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent } from '@/components/ui/Card';
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell, Dialog, Skeleton, EmptyState } from '@/components/ui/index';
import { sectionService } from '@/services/adminService';
import type { SectionResponse } from '@/types';
import { toast } from 'sonner';

const getErrMsg = (err: unknown) =>
    (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Operation failed';

export default function SectionsPage() {
    const [sections, setSections] = useState<SectionResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [dialogOpen, setDialogOpen] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);
    const [name, setName] = useState('');
    const [saving, setSaving] = useState(false);
    const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

    const fetchSections = useCallback(async () => {
        setLoading(true);
        try { setSections(await sectionService.list()); }
        catch { toast.error('Failed to load sections'); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { fetchSections(); }, [fetchSections]);

    const resetAndClose = () => { setDialogOpen(false); setEditingId(null); setName(''); };

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        try {
            editingId ? await sectionService.update(editingId, { name }) : await sectionService.create({ name });
            toast.success(editingId ? 'Section updated' : 'Section created');
            resetAndClose(); fetchSections();
        } catch (err) { toast.error(getErrMsg(err)); }
        finally { setSaving(false); }
    };

    const handleDelete = async (id: string) => {
        try { await sectionService.delete(id); toast.success('Section deleted'); setDeleteConfirm(null); fetchSections(); }
        catch { toast.error('Failed to delete. Section may be in use.'); }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-text-primary">Sections</h1>
                    <p className="text-text-secondary mt-1">Manage course sections</p>
                </div>
                <Button onClick={() => { setEditingId(null); setName(''); setDialogOpen(true); }}>
                    <Plus size={16} /> Add Section
                </Button>
            </div>

            <Card>
                {loading ? (
                    <CardContent className="p-6 space-y-3">
                        {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
                    </CardContent>
                ) : sections.length === 0 ? (
                    <EmptyState icon={<Layers size={48} />} title="No sections yet" description="Create your first section to get started."
                        action={<Button onClick={() => setDialogOpen(true)}><Plus size={16} /> Add Section</Button>} />
                ) : (
                    <Table>
                        <TableHeader><TableRow>
                            <TableHead>Name</TableHead><TableHead>ID</TableHead><TableHead className="text-right">Actions</TableHead>
                        </TableRow></TableHeader>
                        <TableBody>
                            {sections.map((section, i) => (
                                <motion.tr key={section.id} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: i * 0.05 }} className="border-b border-border hover:bg-surface-muted/50">
                                    <TableCell className="font-medium">{section.name}</TableCell>
                                    <TableCell className="text-text-muted font-mono text-xs">{section.id.slice(0, 8)}...</TableCell>
                                    <TableCell className="text-right">
                                        <div className="flex items-center justify-end gap-1">
                                            <Button variant="ghost" size="icon" onClick={() => { setEditingId(section.id); setName(section.name); setDialogOpen(true); }} title="Edit"><Edit size={16} /></Button>
                                            <Button variant="ghost" size="icon" onClick={() => setDeleteConfirm(section.id)} title="Delete"
                                                className="text-red-500 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"><Trash2 size={16} /></Button>
                                        </div>
                                    </TableCell>
                                </motion.tr>
                            ))}
                        </TableBody>
                    </Table>
                )}
            </Card>

            <Dialog open={dialogOpen} onClose={resetAndClose} title={editingId ? 'Edit Section' : 'Add Section'} size="sm">
                <form onSubmit={handleSave} className="space-y-4">
                    <Input label="Section Name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Section A" required autoFocus />
                    <div className="flex justify-end gap-2">
                        <Button type="button" variant="outline" onClick={resetAndClose}>Cancel</Button>
                        <Button type="submit" isLoading={saving}>{editingId ? 'Update' : 'Create'}</Button>
                    </div>
                </form>
            </Dialog>

            <Dialog open={!!deleteConfirm} onClose={() => setDeleteConfirm(null)} title="Delete Section" description="This action cannot be undone. Are you sure?" size="sm">
                <div className="flex justify-end gap-2">
                    <Button variant="outline" onClick={() => setDeleteConfirm(null)}>Cancel</Button>
                    <Button variant="destructive" onClick={() => deleteConfirm && handleDelete(deleteConfirm)}>Delete</Button>
                </div>
            </Dialog>
        </div>
    );
}
