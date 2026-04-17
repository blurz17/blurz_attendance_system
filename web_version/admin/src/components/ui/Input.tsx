import * as React from 'react';
import { cn } from '@/lib/utils';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    icon?: React.ReactNode;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
    ({ className, type, label, error, icon, id, ...props }, ref) => {
        const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

        return (
            <div className="space-y-1.5">
                {label && (
                    <label htmlFor={inputId} className="block text-sm font-medium text-text-secondary">
                        {label}
                    </label>
                )}
                <div className="relative">
                    {icon && (
                        <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted">
                            {icon}
                        </div>
                    )}
                    <input
                        type={type}
                        id={inputId}
                        className={cn(
                            'flex h-10 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-text-primary',
                            'placeholder:text-text-muted',
                            'focus:outline-none focus:ring-2 focus:ring-primary-400 focus:border-primary-400',
                            'disabled:cursor-not-allowed disabled:opacity-50',
                            'transition-all duration-200',
                            icon && 'pl-10',
                            error && 'border-error focus:ring-error',
                            className
                        )}
                        ref={ref}
                        {...props}
                    />
                </div>
                {error && (
                    <p className="text-xs text-error mt-1">{error}</p>
                )}
            </div>
        );
    }
);
Input.displayName = 'Input';

export { Input };
