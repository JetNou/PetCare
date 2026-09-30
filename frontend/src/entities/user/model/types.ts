// ─── Enums ───

export const UserStatus = {
  Registered: 'registered',
  Active: 'active',
  Banned: 'banned',
} as const;

export type UserStatusValue = (typeof UserStatus)[keyof typeof UserStatus];

// ─── Auth ───

export interface UserCreate {
  user_login: string;
  user_full_name: string;
  user_email: string;
  user_password: string;
}

export interface UserLogin {
  user_identifier: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface TokenResponse {
  detail: string;
  refresh_token: string;
}

export interface ResetPasswordConfirm {
  token: string;
  new_password: string;
}

// ─── Users ───

export interface UserProfile {
  user_id: number;
  user_login: string;
  user_full_name: string;
  user_email: string;
  user_avatar: string | null;
  role_id: number;
  registered_at: string;
  is_deleted: boolean;
  status: UserStatusValue;
  ban_reason: string | null;
  banned_at: string | null;
}

export interface UpdateProfileDto {
  user_login?: string | null;
  user_full_name?: string | null;
  user_email?: string | null;
  photo?: File | null;
}
