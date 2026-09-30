export interface SystemStatistics {
  total_users: number;
  active_users: number;
  total_pets: number;
  active_pets: number;
  medical_events_by_status: Record<string, number>;
}
