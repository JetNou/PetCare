import { create } from 'zustand';
import type { UserProfile } from './types';

interface SessionState {
  user: UserProfile | null;
  isLoading: boolean;
  setUser: (user: UserProfile | null) => void;
  setLoading: (isLoading: boolean) => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  user: null,
  isLoading: true,
  setUser: (user) => set({ user }),
  setLoading: (isLoading) => set({ isLoading }),
}));
