import { useState, useRef, useLayoutEffect, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { cn } from '@shared/utils/utils';

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  label?: string;
  id?: string;
  options: SelectOption[];
  value?: string;
  onChange?: (value: string) => void;
  onBlur?: () => void;
  error?: string;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
}

export const Select = ({
  label,
  id,
  options,
  value,
  onChange,
  onBlur,
  error,
  placeholder = 'Выберите...',
  className,
  disabled,
}: SelectProps) => {
  const [open, setOpen] = useState(false);
  const [dropdownStyle, setDropdownStyle] = useState<React.CSSProperties | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const selected = options.find((o) => o.value === value);

  useLayoutEffect(() => {
    if (!open || !triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    setDropdownStyle({
      position: 'fixed',
      top: rect.bottom + 4,
      left: rect.left,
      width: rect.width,
      zIndex: 9999,
    });
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
        onBlur?.();
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [open, onBlur]);

  const handleSelect = (val: string) => {
    onChange?.(val);
    setOpen(false);
    onBlur?.();
  };

  return (
    <div className={cn('flex flex-col', className)} ref={containerRef}>
      {label && (
        <label htmlFor={id} className="text-base font-semibold text-brand-slate ml-1">
          {label}
        </label>
      )}

      <button
        ref={triggerRef}
        id={id}
        type="button"
        disabled={disabled}
        className={cn(
          'flex h-12 w-full items-center justify-between px-4 rounded-xl bg-brand-cream text-black',
          'transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-brand-primary',
          open && 'ring-2 ring-brand-primary',
          disabled && 'opacity-50 cursor-not-allowed',
        )}
        onClick={() => setOpen((v) => !v)}
      >
        <span className={cn(!selected && 'text-black')}>
          {selected ? selected.label : placeholder}
        </span>
        <svg
          className={cn('w-4 h-4 text-brand-slate transition-transform duration-200 shrink-0', open && 'rotate-180')}
          viewBox="0 0 24 24"
          fill="none"
        >
          <path d="M6 9L12 15L18 9" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && dropdownStyle && createPortal(
        <ul
          style={dropdownStyle}
          className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-y-auto max-h-60 animate-in fade-in slide-in-from-top-1 duration-200"
          onMouseDown={(e) => e.stopPropagation()}
        >
          {options.map((opt) => (
            <li key={opt.value}>
              <button
                type="button"
                className={cn(
                  'w-full text-left px-4 py-2.5 text-sm transition-colors duration-150',
                  'hover:bg-brand-cream',
                  opt.value === value && 'font-semibold text-brand-primary bg-brand-cream',
                )}
                onClick={() => handleSelect(opt.value)}
              >
                {opt.label}
              </button>
            </li>
          ))}
        </ul>,
        document.body,
      )}

      {error && <p className="text-red-500 text-sm mt-1 ml-1">{error}</p>}
    </div>
  );
};