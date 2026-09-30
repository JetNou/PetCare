// ─── Enums ───

export const MedicalHistoryStatus = {
  Planned: 'planned',
  Overdue: 'overdue',
  Completed: 'completed',
} as const;

export type MedicalHistoryStatusValue =
  (typeof MedicalHistoryStatus)[keyof typeof MedicalHistoryStatus];

export const TypeAction = {
  Inspection: 'inspection',
  Tests: 'tests',
  Diagnostics: 'diagnostics',
  Complex: 'complex',
  ParasiteTreatment: 'parasite_treatment',
  Surgery: 'surgery',
  TreatmentCourse: 'treatment_course',
  Dentistry: 'dentistry',
  Grooming: 'grooming',
  Other: 'other',
} as const;

export type TypeActionValue = (typeof TypeAction)[keyof typeof TypeAction];

// ─── Pets ───

export interface PetCreate {
  name: string;
  weight: number;
  gender?: string | null;
  date_birth?: string | null;
  breed?: string | null;
  color?: string | null;
  chip?: string | null;
}

export interface PetResponse {
  pet_id: number;
  name: string;
  breed: string | null;
  color: string | null;
  gender: string | null;
  date_birth: string | null;
  chip: string | null;
  photo: string;
  weight: number | null;
  user_id: number;
}

export interface UpdatePetDto {
  name?: string | null;
  breed?: string | null;
  color?: string | null;
  gender?: string | null;
  date_birth?: string | null;
  chip?: string | null;
  weight?: number | null;
}

// ─── Medical Events ───

export interface MedicalEventCreate {
  type_action: TypeActionValue;
  date: string;
  description?: string | null;
  notes?: string | null;
  status?: MedicalHistoryStatusValue;
  interval_period?: number;
}

export interface MedicalEventResponse {
  medical_history_id: number;
  medical_action_id: number;
  pet_id: number | null;
  type_action: TypeActionValue | null;
  description: string | null;
  date: string;
  status: MedicalHistoryStatusValue;
  notes: string | null;
  interval_period: number | null;
}

export interface MedicalHistoryResponse {
  pet_id: number;
  pet_name: string;
  events: MedicalEventResponse[];
  total_events: number;
}

export interface UpdateMedicalEventDto {
  type_action?: TypeActionValue | null;
  description?: string | null;
  date?: string | null;
  notes?: string | null;
  status?: MedicalHistoryStatusValue | null;
  interval_period?: number | null;
}
