export const UserRole = {
  Admin: 1,
  User: 2,
} as const;

export type UserRoleKey = keyof typeof UserRole;
export type UserRoleId = (typeof UserRole)[UserRoleKey];
