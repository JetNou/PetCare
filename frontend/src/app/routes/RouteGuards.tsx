import type { ReactNode } from 'react';
import { Navigate } from 'react-router';
import { useSessionStore, UserRole } from '@entities/user';

interface GuardProps {
  children: ReactNode;
}

export const PublicRoute = ({ children }: GuardProps) => {
  const user = useSessionStore((s) => s.user);

  if (user) {
    return <Navigate to="/pets" replace />;
  }

  return <>{children}</>;
};

export const PrivateRoute = ({ children }: GuardProps) => {
  const user = useSessionStore((s) => s.user);
  const isLoading = useSessionStore((s) => s.isLoading);

  if (isLoading) {
    return <div className="container mt-10">Загрузка...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const AdminRoute = ({ children }: GuardProps) => {
  const user = useSessionStore((s) => s.user);
  const isLoading = useSessionStore((s) => s.isLoading);

  if (isLoading) {
    return <div className="container mt-10">Загрузка...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role_id !== UserRole.Admin) {
    return <Navigate to="/pets" replace />;
  }

  return <>{children}</>;
};
