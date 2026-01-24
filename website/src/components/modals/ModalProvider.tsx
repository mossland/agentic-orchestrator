'use client';

import { createContext, useState, useCallback, type ReactNode } from 'react';
import { TerminalModal } from './TerminalModal';

// Modal types for different detail views
export type ModalType =
  | 'signal'
  | 'trend'
  | 'idea'
  | 'debate'
  | 'plan'
  | 'project'
  | 'agent'
  | 'stats'
  | 'pipeline';

// Data passed to modals
export interface ModalData {
  id: string;
  title?: string;
  [key: string]: unknown;
}

interface ModalState {
  isOpen: boolean;
  type: ModalType | null;
  data: ModalData | null;
}

interface ModalContextType {
  isOpen: boolean;
  type: ModalType | null;
  data: ModalData | null;
  openModal: (type: ModalType, data: ModalData) => void;
  closeModal: () => void;
}

export const ModalContext = createContext<ModalContextType | null>(null);

interface ModalProviderProps {
  children: ReactNode;
}

export function ModalProvider({ children }: ModalProviderProps) {
  const [state, setState] = useState<ModalState>({
    isOpen: false,
    type: null,
    data: null,
  });

  const openModal = useCallback((type: ModalType, data: ModalData) => {
    setState({ isOpen: true, type, data });
    // Prevent body scroll when modal is open
    document.body.style.overflow = 'hidden';
  }, []);

  const closeModal = useCallback(() => {
    setState({ isOpen: false, type: null, data: null });
    // Restore body scroll
    document.body.style.overflow = '';
  }, []);

  return (
    <ModalContext.Provider
      value={{
        isOpen: state.isOpen,
        type: state.type,
        data: state.data,
        openModal,
        closeModal,
      }}
    >
      {children}
      {state.isOpen && state.type && state.data && (
        <TerminalModal
          type={state.type}
          data={state.data}
          onClose={closeModal}
        />
      )}
    </ModalContext.Provider>
  );
}
