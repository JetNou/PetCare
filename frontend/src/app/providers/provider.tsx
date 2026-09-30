
import { type ReactNode } from 'react';
import { ConfirmModal } from '@/features/confirm/ui/confirm-modal';

interface ProvidersProps {
  children: ReactNode;
}

export function Provider({ children }: ProvidersProps) {
  return (
    <>
      {children}

      <ConfirmModal />
    </>
  );
}