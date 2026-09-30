export function resolveMediaUrl(storedPath: string | null | undefined): string | undefined {
  if (!storedPath) return undefined;
  const base = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1';
  const normalized = storedPath.replace(/^\/+/, '');
  const file = normalized.includes('/') ? normalized.split('/').pop()! : normalized;
  if (file.startsWith('user-')) {
    return `${base}/images/private/avatars/${encodeURIComponent(file)}`;
  }
  return `${base}/images/private/${encodeURIComponent(normalized)}`;
}
