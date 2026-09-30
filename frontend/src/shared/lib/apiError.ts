import { isAxiosError } from 'axios';
import type { ValidationError } from '@shared/types/api-error';

function detailToMessage(detail: string | ValidationError[]): string {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((d) => d.msg).join('. ');
  }
  return '';
}


export function getApiErrorMessage(err: unknown, fallback = 'Произошла ошибка'): string {
  if (isAxiosError(err)) {
    const data = err.response?.data as Record<string, unknown> | undefined;
    if (!data) return err.message || fallback;

    const nested = data.error as { message?: string } | undefined;
    if (nested?.message) return nested.message;

    const detail = data.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      const msg = detailToMessage(detail as ValidationError[]);
      if (msg) return msg;
    }
  }
  if (err instanceof Error) return err.message;
  return fallback;
}
