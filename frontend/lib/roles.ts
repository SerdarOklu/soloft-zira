export const ROLES = ['admin', 'agronomist', 'cooperative_user', 'farmer'] as const;
export type Role = (typeof ROLES)[number];

export interface SessionUser {
  id: string;
  email: string;
  name: string;
  role: Role;
  organization_id: string | null;
}

export function isRole(value: unknown): value is Role {
  return typeof value === 'string' && (ROLES as readonly string[]).includes(value);
}
