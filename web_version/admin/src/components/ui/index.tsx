import * as React from 'react';
import { cn } from '@/lib/utils';

// ─── Badge ───
const badgeVariants = {
    default: 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300',
    success: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300',
    warning: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
    error: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
    info: 'bg-accent-100 text-accent-700 dark:bg-accent-900/30 dark:text-accent-300',
    accent: 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300',
    outline: 'border border-border text-text-secondary',
};

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    variant?: keyof typeof badgeVariants;
}

const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
    ({ className, variant = 'default', ...props }, ref) => (
        <span
            ref={ref}
            className={cn(
                'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors',
                badgeVariants[variant],
                className
            )}
            {...props}
        />
    )
);
Badge.displayName = 'Badge';

// ─── Table ───
const Table = React.forwardRef<HTMLTableElement, React.HTMLAttributes<HTMLTableElement>>(
    ({ className, ...props }, ref) => (
        <div className="relative w-full overflow-auto rounded-lg border border-border">
            <table
                ref={ref}
                className={cn('w-full caption-bottom text-sm', className)}
                {...props}
            />
        </div>
    )
);
Table.displayName = 'Table';

const TableHeader = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
    ({ className, ...props }, ref) => (
        <thead ref={ref} className={cn('bg-surface-muted [&_tr]:border-b', className)} {...props} />
    )
);
TableHeader.displayName = 'TableHeader';

const TableBody = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
    ({ className, ...props }, ref) => (
        <tbody ref={ref} className={cn('[&_tr:last-child]:border-0', className)} {...props} />
    )
);
TableBody.displayName = 'TableBody';

const TableRow = React.forwardRef<HTMLTableRowElement, React.HTMLAttributes<HTMLTableRowElement>>(
    ({ className, ...props }, ref) => (
        <tr
            ref={ref}
            className={cn(
                'border-b border-border transition-colors hover:bg-surface-muted/50',
                className
            )}
            {...props}
        />
    )
);
TableRow.displayName = 'TableRow';

const TableHead = React.forwardRef<HTMLTableCellElement, React.ThHTMLAttributes<HTMLTableCellElement>>(
    ({ className, ...props }, ref) => (
        <th
            ref={ref}
            className={cn(
                'h-12 px-4 text-left align-middle font-semibold text-text-secondary [&:has([role=checkbox])]:pr-0',
                className
            )}
            {...props}
        />
    )
);
TableHead.displayName = 'TableHead';

const TableCell = React.forwardRef<HTMLTableCellElement, React.TdHTMLAttributes<HTMLTableCellElement>>(
    ({ className, ...props }, ref) => (
        <td
            ref={ref}
            className={cn('px-4 py-3 align-middle text-text-primary [&:has([role=checkbox])]:pr-0', className)}
            {...props}
        />
    )
);
TableCell.displayName = 'TableCell';

// ─── Select ───
interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
    label?: string;
    error?: string;
    options: { value: string; label: string }[];
    placeholder?: string;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
    ({ className, label, error, options, placeholder, id, ...props }, ref) => {
        const selectId = id || label?.toLowerCase().replace(/\s+/g, '-');

        return (
            <div className="space-y-1.5">
                {label && (
                    <label htmlFor={selectId} className="block text-sm font-medium text-text-secondary">
                        {label}
                    </label>
                )}
                <select
                    id={selectId}
                    ref={ref}
                    className={cn(
                        'flex h-10 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text-primary',
                        'focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-primary-400',
                        'disabled:cursor-not-allowed disabled:opacity-50',
                        'transition-all duration-200',
                        error && 'border-error focus:ring-error',
                        className
                    )}
                    {...props}
                >
                    {placeholder && (
                        <option value="" disabled>
                            {placeholder}
                        </option>
                    )}
                    {options.map((opt) => (
                        <option key={opt.value} value={opt.value}>
                            {opt.label}
                        </option>
                    ))}
                </select>
                {error && <p className="text-xs text-error mt-1">{error}</p>}
            </div>
        );
    }
);
Select.displayName = 'Select';

// ─── MultiSelect ───
interface MultiSelectProps {
    label?: string;
    error?: string;
    options: { value: string; label: string }[];
    value: string[];
    onChange: (value: string[]) => void;
    placeholder?: string;
}

const MultiSelect = ({ label, error, options, value, onChange, placeholder }: MultiSelectProps) => {
    const toggleOption = (id: string) => {
        if (value.includes(id)) {
            onChange(value.filter(v => v !== id));
        } else {
            onChange([...value, id]);
        }
    };

    return (
        <div className="space-y-1.5">
            {label && <label className="block text-sm font-medium text-text-secondary">{label}</label>}
            <div className="min-h-[2.5rem] w-full rounded-lg border border-border bg-surface p-1.5 flex flex-wrap gap-1.5 focus-within:ring-2 focus-within:ring-primary-400">
                {value.length === 0 && <span className="text-sm text-text-muted px-2 py-1">{placeholder}</span>}
                {value.map(id => {
                    const option = options.find(o => o.value === id);
                    return (
                        <Badge key={id} variant="accent" className="gap-1 pr-1 font-normal bg-accent-100 text-accent-700">
                            {option?.label || id}
                            <button
                                type="button"
                                onClick={(e) => { e.preventDefault(); toggleOption(id); }}
                                className="hover:bg-primary-200 rounded-full p-0.5"
                            >
                                <svg width="12" height="12" viewBox="0 0 20 20" fill="currentColor"><path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" /></svg>
                            </button>
                        </Badge>
                    );
                })}
            </div>
            <div className="max-h-32 overflow-y-auto mt-2 border border-border rounded-lg bg-surface divide-y divide-border">
                {options.map(opt => (
                    <button
                        key={opt.value}
                        type="button"
                        onClick={() => toggleOption(opt.value)}
                        className={cn(
                            "w-full text-left px-3 py-2 text-sm transition-colors hover:bg-surface-muted",
                            value.includes(opt.value) && "bg-primary-50 text-primary-700 font-medium"
                        )}
                    >
                        {opt.label}
                    </button>
                ))}
            </div>
            {error && <p className="text-xs text-error mt-1">{error}</p>}
        </div>
    );
};

// ─── Dialog / Modal ───
interface DialogProps {
    open: boolean;
    onClose: () => void;
    title: string;
    description?: string;
    children: React.ReactNode;
    size?: 'sm' | 'md' | 'lg' | 'xl';
}

const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
};

function Dialog({ open, onClose, title, description, children, size = 'md' }: DialogProps) {
    React.useEffect(() => {
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        if (open) {
            document.addEventListener('keydown', handleEscape);
            document.body.style.overflow = 'hidden';
        }
        return () => {
            document.removeEventListener('keydown', handleEscape);
            document.body.style.overflow = '';
        };
    }, [open, onClose]);

    if (!open) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            <div
                className="fixed inset-0 bg-black/50 backdrop-blur-sm animate-fade-in"
                onClick={onClose}
            />
            <div
                className={cn(
                    'relative z-10 w-full mx-4 bg-surface rounded-2xl shadow-2xl border border-border animate-slide-up',
                    sizeClasses[size]
                )}
            >
                <div className="p-6 border-b border-border">
                    <h2 className="text-lg font-semibold text-text-primary">{title}</h2>
                    {description && (
                        <p className="text-sm text-text-secondary mt-1">{description}</p>
                    )}
                </div>
                <div className="p-6">{children}</div>
            </div>
        </div>
    );
}

// ─── Loading Skeleton ───
function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
    return (
        <div
            className={cn('animate-pulse rounded-lg bg-surface-muted', className)}
            {...props}
        />
    );
}

// ─── Empty State ───
interface EmptyStateProps {
    icon?: React.ReactNode;
    title: string;
    description?: string;
    action?: React.ReactNode;
}

function EmptyState({ icon, title, description, action }: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
            {icon && <div className="text-text-muted mb-4">{icon}</div>}
            <h3 className="text-lg font-semibold text-text-primary mb-1">{title}</h3>
            {description && <p className="text-sm text-text-secondary mb-6 max-w-sm">{description}</p>}
            {action}
        </div>
    );
}

export {
    Badge,
    Table,
    TableHeader,
    TableBody,
    TableRow,
    TableHead,
    TableCell,
    Select,
    MultiSelect,
    Dialog,
    Skeleton,
    EmptyState,
};
