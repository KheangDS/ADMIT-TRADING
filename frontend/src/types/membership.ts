export type Currency = 'USD' | 'KHR';
export interface User { id: string; email: string; name: string; role: 'member' | 'admin' | 'superadmin' }
export interface Membership { active: boolean; expires_at: string | null; source: string | null }
export interface AuthMetadata { user: User | null; csrf_token: string | null; membership: Membership | null }
export interface Plan { id: string; name: string; description: string; amount: string; currency: Currency; duration_unit: 'month' | 'year'; duration_count: number; display_order: number; active: boolean }
export interface Payment {
  id: string; user_id: string; user_name: string; user_email: string; plan_id: string; plan_name: string;
  amount: string; currency: Currency; duration_unit: 'month' | 'year'; duration_count: number; payer_name: string;
  status: 'created' | 'submitted' | 'approved' | 'rejected' | 'cancelled'; created_at: string;
  confirmed_at: string | null; approved_at: string | null; paid_at: string | null; expires_at: string | null;
  qr_expires_at: string | null; bank_reference: string | null; rejection_reason: string | null; checkout_ip: string; device_type: string;
  user_agent: string; qr_url: string | null; delayed_reported_at: string | null; receipt_id: string | null;
}
export interface Receipt {
  id: string; payment_id: string; number: string; user_name: string; amount: string; currency: Currency;
  paid_at: string; approved_at: string; expires_at: string;
  pdf_status: 'pending' | 'ready' | 'failed'; email_status: 'pending' | 'sent' | 'failed';
}
export interface MemberDocument {
  id: string; title: string; description: string; language: 'en' | 'km' | 'both'; filename: string;
  content_type: string; size_bytes: number; status: 'draft' | 'published'; publication_id: string | null;
  created_at: string; preview_status: 'ready' | 'unavailable' | 'pending' | 'failed';
}
