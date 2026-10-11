export interface User {
  id: string;
  email: string;
  name: string;
  role: 'member' | 'admin' | 'superadmin';
}
export interface Membership {
  active: boolean;
  expires_at: string | null;
  source: string | null;
}
export interface AuthResponse {
  user: User | null;
  csrf_token: string | null;
  membership: Membership | null;
}
export interface Publication {
  id: string;
  revision_id: string;
  start_month: string;
  end_month: string;
  row_count?: number;
}
export interface Schema {
  columns: { key: string; english: string; khmer: string; required: boolean }[];
  units: { weight: string; value: string };
  formats: string[];
}
export interface RegistryEntry {
  kind: 'hs4' | 'hs8' | 'country';
  code: string;
  name_en: string;
  name_km: string;
  parent_code: string | null;
  iso3: string | null;
  aliases: string[];
}
export interface TradeImport {
  id: string;
  filename: string;
  storage_name?: string | null;
  mode: 'complete' | 'partial';
  status: 'staged' | 'committed' | 'invalid';
  start_month: string;
  end_month: string;
  row_count: number;
  duplicate_count: number;
  errors: { row: number; message: string }[];
  unknowns: RegistryEntry[];
  preview: { inserted: number; updated: number; removed: number; unchanged: number };
  column_mapping: Record<string, unknown>;
  created_at: string;
  revision_id: string | null;
}
export interface Revision {
  id: string;
  created_at: string;
  row_count: number;
  status: 'ready' | 'failed';
  source_import_id: string;
  start_month?: string | null;
  end_month?: string | null;
  available_months?: string[];
}
export interface Plan {
  id: string;
  name: string;
  description: string;
  amount: string;
  currency: 'USD' | 'KHR';
  duration_unit: 'month' | 'year';
  duration_count: number;
  display_order: number;
  active: boolean;
}
export interface Payment {
  id: string;
  user_id: string;
  user_name: string;
  user_email: string;
  plan_id: string;
  plan_name: string;
  amount: string;
  currency: 'USD' | 'KHR';
  duration_unit: 'month' | 'year';
  duration_count: number;
  payer_name: string;
  status: 'created' | 'submitted' | 'approved' | 'rejected' | 'cancelled';
  created_at: string;
  confirmed_at: string | null;
  approved_at: string | null;
  paid_at: string | null;
  expires_at: string | null;
  bank_reference: string | null;
  rejection_reason: string | null;
  checkout_ip: string;
  device_type: string;
  user_agent: string;
  qr_url: string | null;
  delayed_reported_at: string | null;
  receipt_id: string | null;
  is_access_granted?: boolean;
  access_status?: string;
  access_expires_at?: string | null;
  access_source?: string | null;
}
export interface AdminUser extends User {
  disabled: boolean;
  membership: Membership | null;
  created_at?: string;
}
export interface PrivateDocument {
  id: string;
  title: string;
  description: string;
  language: 'en' | 'km' | 'both';
  filename: string;
  content_type: string;
  size_bytes: number;
  status: 'draft' | 'published';
  publication_id: string | null;
  created_at: string;
  preview_status: 'ready' | 'unavailable' | 'pending' | 'failed';
}
export interface AdminStatus {
  current_revision_id: string | null;
  publication: Publication | null;
  uploads: unknown[];
  [key: string]: unknown;
}
export interface AuditEvent {
  id: string;
  actor_id: string | null;
  actor_name?: string | null;
  actor_email?: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  details: Record<string, unknown> | null;
  created_at: string;
}
export interface Job {
  id: string;
  kind: string;
  entity_id: string;
  status: 'pending' | 'processing' | 'done' | 'failed' | string;
  attempts: number;
  last_error: string | null;
  available_at: string;
  created_at: string;
  completed_at: string | null;
  [key: string]: unknown;
}
