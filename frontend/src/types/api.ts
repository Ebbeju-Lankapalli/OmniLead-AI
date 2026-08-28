/* OmniLead AI - Backend API Contracts & Data Types */

export enum UserRole {
  ADMIN = 'ADMIN',
  SALES = 'SALES',
}

export enum LeadSource {
  INSTAGRAM = 'INSTAGRAM',
  WHATSAPP = 'WHATSAPP',
  META_AD_WHATSAPP = 'META_AD_WHATSAPP',
  PHONE = 'PHONE',
  REFERRAL = 'REFERRAL',
  WALK_IN = 'WALK_IN',
  MANUAL = 'MANUAL',
  OTHER = 'OTHER',
}

export enum ConversationChannel {
  INSTAGRAM = 'INSTAGRAM',
  WHATSAPP = 'WHATSAPP',
  PHONE = 'PHONE',
  MANUAL = 'MANUAL',
  OTHER = 'OTHER',
}

export enum PurchaseIntent {
  GENERAL_ENQUIRY = 'GENERAL_ENQUIRY',
  POTENTIAL_LEAD = 'POTENTIAL_LEAD',
  HIGH_INTENT = 'HIGH_INTENT',
  NOT_INTERESTED = 'NOT_INTERESTED',
  UNCERTAIN = 'UNCERTAIN',
}

export enum EnquiryStatus {
  NEW = 'NEW',
  AI_ANALYZED = 'AI_ANALYZED',
  NEEDS_REVIEW = 'NEEDS_REVIEW',
  CONVERTED_TO_LEAD = 'CONVERTED_TO_LEAD',
  GENERAL_ENQUIRY = 'GENERAL_ENQUIRY',
  REJECTED = 'REJECTED',
  ARCHIVED = 'ARCHIVED',
}

export enum InteractionDirection {
  INBOUND = 'INBOUND',
  OUTBOUND = 'OUTBOUND',
  INTERNAL = 'INTERNAL',
}

export enum InteractionType {
  MESSAGE = 'MESSAGE',
  CALL = 'CALL',
  CALL_NOTE = 'CALL_NOTE',
  NOTE = 'NOTE',
  STATUS_CHANGE = 'STATUS_CHANGE',
  ASSIGNMENT = 'ASSIGNMENT',
  FOLLOWUP_SCHEDULED = 'FOLLOWUP_SCHEDULED',
  FOLLOWUP_COMPLETED = 'FOLLOWUP_COMPLETED',
  EMAIL = 'EMAIL',
  LEAD_CREATED = 'LEAD_CREATED',
  AI_REVIEW = 'AI_REVIEW',
}

export enum FollowUpType {
  CALL = 'CALL',
  WHATSAPP = 'WHATSAPP',
  INSTAGRAM = 'INSTAGRAM',
  EMAIL = 'EMAIL',
  MEETING = 'MEETING',
  OTHER = 'OTHER',
}

export enum FollowUpStatus {
  SCHEDULED = 'SCHEDULED',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED',
  RESCHEDULED = 'RESCHEDULED',
  OVERDUE = 'OVERDUE',
}

export enum NotificationChannel {
  IN_APP = 'IN_APP',
  EMAIL = 'EMAIL',
  WHATSAPP = 'WHATSAPP',
}

export enum NotificationStatus {
  PENDING = 'PENDING',
  SENT = 'SENT',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED',
}

export enum AIReviewDecision {
  ACCEPTED = 'ACCEPTED',
  EDITED = 'EDITED',
  REJECTED = 'REJECTED',
}

/* User & Auth */
export interface AuthenticatedUser {
  id: string;
  auth_user_id: string;
  organization_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface AuthSessionResponse {
  user: AuthenticatedUser;
  access_token?: string | null;
  refresh_token?: string | null;
  token_type: string;
  expires_in?: number | null;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
  expires_in?: number | null;
  refresh_token?: string | null;
}

/* Organization */
export interface OrganizationResponse {
  id: string;
  name: string;
  slug: string;
  currency: string;
  timezone: string;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface OrganizationUpdate {
  name?: string;
  currency?: string;
  timezone?: string;
  settings?: Record<string, any>;
}

/* Lead Status */
export interface LeadStatusResponse {
  id: string;
  organization_id: string;
  name: string;
  key: string;
  description?: string | null;
  display_order: number;
  is_terminal: boolean;
  is_won: boolean;
  is_lost: boolean;
  is_active: boolean;
}

export interface LeadStatusOption {
  id: string;
  key: string;
  name: string;
}

/* Lead */
export interface LeadResponse {
  id: string;
  organization_id: string;
  customer_id: string;
  source_enquiry_id?: string | null;
  product_id?: string | null;
  status_id: string;
  assigned_to_user_id?: string | null;
  source: LeadSource;
  original_source?: LeadSource | null;
  campaign_id?: string | null;
  ad_id?: string | null;
  requirement?: string | null;
  original_enquiry?: string | null;
  purchase_intent?: PurchaseIntent | null;
  lead_score?: number | null;
  priority_score?: number | null;
  followup_risk_score?: number | null;
  followup_risk?: number;
  score_breakdown: Record<string, any>;
  qualification_summary?: string | null;
  conversation_summary?: string | null;
  ai_summary?: string | null;
  notes?: string | null;
  next_best_action?: string | null;
  next_best_action_reason?: string | null;
  tags: string[];
  last_contact_at?: string | null;
  next_followup_at?: string | null;
  closed_at?: string | null;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;

  /* Relation objects populated by API or UI */
  customer?: CustomerResponse | null;
  product?: ProductResponse | null;
  status?: LeadStatusResponse | null;
  assigned_user?: UserResponse | null;
}

export interface LeadCreateRequest {
  customer_id: string;
  status_id: string;
  source: LeadSource;
  original_source?: LeadSource | null;
  source_enquiry_id?: string | null;
  product_id?: string | null;
  assigned_to_user_id?: string | null;
  campaign_id?: string | null;
  ad_id?: string | null;
  requirement?: string | null;
  original_enquiry?: string | null;
  purchase_intent?: PurchaseIntent | null;
  lead_score?: number | null;
  priority_score?: number | null;
  followup_risk_score?: number | null;
  score_breakdown?: Record<string, any>;
  qualification_summary?: string | null;
  conversation_summary?: string | null;
  next_best_action?: string | null;
  next_best_action_reason?: string | null;
  tags?: string[];
  last_contact_at?: string | null;
  next_followup_at?: string | null;
}

export interface LeadUpdate {
  source_enquiry_id?: string | null;
  product_id?: string | null;
  status_id?: string | null;
  assigned_to_user_id?: string | null;
  source?: LeadSource | null;
  original_source?: LeadSource | null;
  campaign_id?: string | null;
  ad_id?: string | null;
  requirement?: string | null;
  original_enquiry?: string | null;
  purchase_intent?: PurchaseIntent | null;
  lead_score?: number | null;
  priority_score?: number | null;
  followup_risk_score?: number | null;
  score_breakdown?: Record<string, any>;
  qualification_summary?: string | null;
  conversation_summary?: string | null;
  next_best_action?: string | null;
  next_best_action_reason?: string | null;
  tags?: string[];
  last_contact_at?: string | null;
  next_followup_at?: string | null;
  closed_at?: string | null;
  archived_at?: string | null;
}

/* Customer */
export interface CustomerResponse {
  id: string;
  organization_id: string;
  full_name?: string | null;
  company_name?: string | null;
  primary_phone?: string | null;
  primary_email?: string | null;
  location?: string | null;
  customer_type?: string | null;
  notes_summary?: string | null;
  first_seen_at: string;
  last_seen_at: string;
  archived_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerCreateRequest {
  full_name?: string | null;
  company_name?: string | null;
  primary_phone?: string | null;
  primary_email?: string | null;
  location?: string | null;
  customer_type?: string | null;
  notes_summary?: string | null;
}

export interface CustomerUpdate {
  full_name?: string | null;
  company_name?: string | null;
  primary_phone?: string | null;
  primary_email?: string | null;
  location?: string | null;
  customer_type?: string | null;
  notes_summary?: string | null;
  archived_at?: string | null;
}

/* Enquiry */
export interface EnquiryResponse {
  id: string;
  organization_id: string;
  customer_id?: string | null;
  conversation_id?: string | null;
  interaction_id?: string | null;
  source: LeadSource;
  original_source?: LeadSource | null;
  external_reference_id?: string | null;
  customer_name_raw?: string | null;
  contact_raw?: string | null;
  message_text?: string | null;
  status: EnquiryStatus;
  received_at: string;
  campaign_id?: string | null;
  ad_id?: string | null;
  ad_name?: string | null;
  enquiry_metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface EnquiryCreateRequest {
  source: LeadSource;
  original_source?: LeadSource | null;
  external_reference_id?: string | null;
  customer_name_raw?: string | null;
  contact_raw?: string | null;
  message_text?: string | null;
  status?: EnquiryStatus;
  received_at?: string | null;
  campaign_id?: string | null;
  ad_id?: string | null;
  ad_name?: string | null;
  enquiry_metadata?: Record<string, any>;
  customer_id?: string | null;
  conversation_id?: string | null;
  interaction_id?: string | null;
}

export interface EnquiryConvertRequest {
  status_id: string;
  source: LeadSource;
  product_id?: string | null;
  assigned_to_user_id?: string | null;
  original_source?: LeadSource | null;
  campaign_id?: string | null;
  ad_id?: string | null;
  requirement?: string | null;
  original_enquiry?: string | null;
  purchase_intent?: PurchaseIntent | null;
  lead_score?: number | null;
  priority_score?: number | null;
  followup_risk_score?: number | null;
  score_breakdown?: Record<string, any>;
  qualification_summary?: string | null;
  conversation_summary?: string | null;
  next_best_action?: string | null;
  next_best_action_reason?: string | null;
  tags?: string[];
}

/* Follow-up */
export interface FollowUpResponse {
  id: string;
  organization_id: string;
  lead_id: string;
  customer_id: string;
  assigned_to_user_id: string;
  created_by_user_id?: string | null;
  followup_type: FollowUpType;
  scheduled_at: string;
  status: FollowUpStatus;
  reminder_minutes_before: number;
  reminder_sent_at?: string | null;
  completed_at?: string | null;
  outcome?: string | null;
  notes?: string | null;
  rescheduled_from_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface FollowUpCreateRequest {
  lead_id: string;
  customer_id: string;
  assigned_to_user_id: string;
  followup_type: FollowUpType;
  scheduled_at: string;
  reminder_minutes_before?: number;
  notes?: string | null;
}

export interface FollowUpUpdateRequest {
  assigned_to_user_id?: string | null;
  followup_type?: FollowUpType | null;
  scheduled_at?: string | null;
  reminder_minutes_before?: number | null;
  notes?: string | null;
}

export interface FollowUpCompleteRequest {
  completed_at: string;
  outcome?: string | null;
  notes?: string | null;
}

export interface FollowUpRescheduleRequest {
  scheduled_at: string;
  assigned_to_user_id?: string | null;
  followup_type?: FollowUpType | null;
  reminder_minutes_before?: number | null;
  notes?: string | null;
}

/* Dashboard */
export interface DashboardMetrics {
  total_leads: number;
  active_leads: number;
  high_priority_leads: number;
  new_enquiries: number;
  enquiries_needing_review: number;
  followups_due_today: number;
  overdue_followups: number;
  converted_leads: number;
  conversion_rate: number;
  average_lead_score?: number | null;
  average_priority_score?: number | null;
}

export interface DashboardSourceMetric {
  source: LeadSource;
  count: number;
  percentage: number;
}

export interface DashboardStatusMetric {
  status_id: string;
  status_key: string;
  status_name: string;
  count: number;
  percentage: number;
}

export interface DashboardIntentMetric {
  purchase_intent: PurchaseIntent;
  count: number;
  percentage: number;
}

export interface DashboardPriorityLead {
  lead_id: string;
  customer_id: string;
  customer_name?: string | null;
  company_name?: string | null;
  product_id?: string | null;
  product_name?: string | null;
  assigned_to_user_id?: string | null;
  assigned_to_name?: string | null;
  status_id: string;
  status_name: string;
  source: LeadSource;
  purchase_intent?: PurchaseIntent | null;
  lead_score?: number | null;
  priority_score?: number | null;
  followup_risk_score?: number | null;
  next_best_action?: string | null;
  next_followup_at?: string | null;
  last_contact_at?: string | null;
}

export interface DashboardFollowUp {
  followup_id: string;
  lead_id: string;
  customer_id: string;
  assigned_to_user_id: string;
  customer_name?: string | null;
  assigned_to_name?: string | null;
  followup_type: FollowUpType;
  status: FollowUpStatus;
  scheduled_at: string;
  reminder_minutes_before: number;
  notes?: string | null;
}

export interface DashboardRecentActivity {
  interaction_id: string;
  customer_id: string;
  lead_id?: string | null;
  conversation_id?: string | null;
  actor_user_id?: string | null;
  customer_name?: string | null;
  actor_name?: string | null;
  interaction_type: InteractionType;
  direction?: InteractionDirection | null;
  channel: ConversationChannel;
  content?: string | null;
  occurred_at: string;
}

export interface DashboardAIReviewMetrics {
  total_analyses: number;
  completed_analyses: number;
  failed_analyses: number;
  pending_reviews: number;
  accepted_reviews: number;
  edited_reviews: number;
  rejected_reviews: number;
}

export interface DashboardTeamMetric {
  user_id: string;
  full_name: string;
  active_leads: number;
  due_followups: number;
  completed_followups: number;
  converted_leads: number;
}

export interface DashboardResponse {
  generated_at: string;
  metrics: DashboardMetrics;
  source_breakdown: DashboardSourceMetric[];
  status_breakdown: DashboardStatusMetric[];
  purchase_intent_breakdown: DashboardIntentMetric[];
  priority_leads: DashboardPriorityLead[];
  upcoming_followups: DashboardFollowUp[];
  recent_activity: DashboardRecentActivity[];
  ai_review_metrics: DashboardAIReviewMetrics;
  team_metrics: DashboardTeamMetric[];
}

/* AI Intelligence & Review Queue */
export interface AIAnalysisSummary {
  id: string;
  customer_id?: string | null;
  lead_id?: string | null;
  enquiry_id?: string | null;
  conversation_id?: string | null;
  interaction_id?: string | null;
  call_recording_id?: string | null;
  analysis_type: string;
  model_provider: string;
  model_name: string;
  model_confidence?: number | null;
  status: string;
  latency_ms?: number | null;
  created_at: string;
}

export interface AIAnalysisResponse extends AIAnalysisSummary {
  organization_id: string;
  prompt_name: string;
  prompt_version: string;
  input_hash?: string | null;
  result: Record<string, any>;
  input_tokens?: number | null;
  output_tokens?: number | null;
  error_code?: string | null;
  error_message?: string | null;
}

export interface AIReviewQueueItem {
  analysis: AIAnalysisSummary;
  customer_name?: string | null;
  lead_status_name?: string | null;
  result: Record<string, any>;
  has_feedback: boolean;
  feedback_decision?: AIReviewDecision | null;
  requires_review: boolean;
  review_reason?: string | null;
}

export interface AIReviewQueueResponse {
  items: AIReviewQueueItem[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
}

export interface AIFeedbackCreate {
  organization_id: string;
  ai_analysis_id: string;
  reviewed_by_user_id: string;
  decision: AIReviewDecision;
  original_result: Record<string, any>;
  final_result?: Record<string, any> | null;
  changed_fields?: string[];
  feedback_notes?: string | null;
}

export interface AIFeedbackResponse {
  id: string;
  organization_id: string;
  ai_analysis_id: string;
  reviewed_by_user_id: string;
  decision: AIReviewDecision;
  original_result: Record<string, any>;
  final_result?: Record<string, any> | null;
  changed_fields: string[];
  feedback_notes?: string | null;
  reviewed_at: string;
}

/* Call Intelligence */
export interface CallIntelligenceResponse {
  analysis_id: string;

  summary?: string | null;

  purchase_intent?: PurchaseIntent | null;

  sentiment?: string | null;

  requirement?: string | null;

  objections: string[];

  commitments: string[];

  action_items: string[];

  customer_questions: string[];

  key_moments: string[];

  confidence?: number | null;

  requires_review: boolean;
}

export interface CallUploadProcessingResponse {
  call_recording_id: string;
  storage_path: string;
  transcription_status: string;
  transcript: string;
  transcript_language?: string | null;
  duration_seconds?: number | null;
  intelligence: CallIntelligenceResponse;
}

/* Conversations & Interactions */
export interface ConversationResponse {
  id: string;
  organization_id: string;
  customer_id: string;
  lead_id?: string | null;
  channel: ConversationChannel;
  external_conversation_id?: string | null;
  title?: string | null;
  started_at?: string | null;
  last_message_at?: string | null;
  closed_at?: string | null;
  status?: string;
  summary?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationCreateRequest {
  customer_id: string;
  lead_id?: string | null;
  channel: ConversationChannel;
  external_thread_id?: string | null;
  subject?: string | null;
}

export interface InteractionResponse {
  id: string;
  organization_id: string;
  customer_id: string;
  lead_id?: string | null;
  conversation_id?: string | null;
  actor_user_id?: string | null;
  channel: ConversationChannel;
  direction?: InteractionDirection | null;
  type: InteractionType;
  interaction_type?: string;
  content?: string | null;
  summary?: string | null;
  metadata: Record<string, any>;
  occurred_at: string;
  created_at: string;
}

export interface InteractionCreateRequest {
  customer_id: string;
  lead_id?: string | null;
  conversation_id?: string | null;
  channel: ConversationChannel;
  direction?: InteractionDirection | null;
  type: InteractionType;
  content?: string | null;
  metadata?: Record<string, any>;
}

/* Search */
export interface SearchScoreRange {
  minimum?: number | null;
  maximum?: number | null;
}

export interface SearchDateRange {
  start?: string | null;
  end?: string | null;
}

export interface LeadSearchFilters {
  sources: LeadSource[];
  original_sources: LeadSource[];
  purchase_intents: PurchaseIntent[];
  status_ids: string[];
  assigned_to_user_ids: string[];
  product_ids: string[];
  customer_ids: string[];
  lead_score?: SearchScoreRange | null;
  priority_score?: SearchScoreRange | null;
  followup_risk_score?: SearchScoreRange | null;
  next_followup_at?: SearchDateRange | null;
  last_contact_at?: SearchDateRange | null;
  tags: string[];
  has_assignee?: boolean | null;
  has_next_followup?: boolean | null;
  is_archived?: boolean | null;
}

export interface SearchSort {
  field: string;
  direction: 'asc' | 'desc';
}

export interface SearchRequest {
  query?: string | null;
  filters?: Partial<LeadSearchFilters>;
  semantic_search?: boolean;
  semantic_limit?: number;
  sort?: Partial<SearchSort>;
  page?: number;
  page_size?: number;
}

export interface LeadSearchResult {
  lead_id: string;
  customer_id: string;
  customer_name?: string | null;
  company_name?: string | null;
  primary_phone?: string | null;
  primary_email?: string | null;
  product_id?: string | null;
  product_name?: string | null;
  status_id: string;
  status_name: string;
  assigned_to_user_id?: string | null;
  assigned_to_name?: string | null;
  source: LeadSource;
  original_source?: LeadSource | null;
  purchase_intent?: PurchaseIntent | null;
  requirement?: string | null;
  qualification_summary?: string | null;
  conversation_summary?: string | null;
  lead_score?: number | null;
  priority_score?: number | null;
  followup_risk_score?: number | null;
  next_best_action?: string | null;
  next_followup_at?: string | null;
  last_contact_at?: string | null;
  tags: string[];
  semantic_similarity?: number | null;
}

export interface SearchResponse {
  query?: string | null;
  filters: LeadSearchFilters;
  sort: SearchSort;
  results: LeadSearchResult[];
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  semantic_search_used: boolean;
  metadata: Record<string, any>;
}

export interface NaturalLanguageSearchRequest {
  query: string;
}

export interface ParsedSearchResponse {
  original_query: string;
  interpreted_query?: string | null;
  filters: LeadSearchFilters;
  sort: SearchSort;
  semantic_search: boolean;
  confidence?: number | null;
  explanation?: string | null;
}

/* Analytics */
export interface AnalyticsDateRange {
  start_date: string;
  end_date: string;
}

export interface AnalyticsOverview {
  total_enquiries: number;
  total_leads: number;
  total_converted_leads: number;
  conversion_rate: number;
  average_lead_score?: number | null;
  average_priority_score?: number | null;
  average_followup_risk_score?: number | null;
  total_followups: number;
  completed_followups: number;
  overdue_followups: number;
  followup_completion_rate: number;
}

export interface AnalyticsTrendPoint {
  period_start: string;
  enquiries: number;
  leads: number;
  converted_leads: number;
  completed_followups: number;
}

export interface SourceAnalytics {
  source: LeadSource;
  enquiries: number;
  leads: number;
  converted_leads: number;
  lead_conversion_rate: number;
  average_lead_score?: number | null;
  average_priority_score?: number | null;
}

export interface PurchaseIntentAnalytics {
  purchase_intent: PurchaseIntent;
  count: number;
  percentage: number;
  average_lead_score?: number | null;
}

export interface LeadStatusAnalytics {
  status_id: string;
  status_key: string;
  status_name: string;
  count: number;
  percentage: number;
}

export interface ProductAnalytics {
  product_id: string;
  product_name: string;
  lead_count: number;
  converted_leads: number;
  conversion_rate: number;
  average_lead_score?: number | null;
}

export interface FollowUpTypeAnalytics {
  followup_type: FollowUpType;
  total: number;
  completed: number;
  overdue: number;
  completion_rate: number;
}

export interface FollowUpStatusAnalytics {
  status: FollowUpStatus;
  count: number;
  percentage: number;
}

export interface TeamAnalytics {
  user_id: string;
  full_name: string;
  assigned_leads: number;
  active_leads: number;
  converted_leads: number;
  conversion_rate: number;
  scheduled_followups: number;
  completed_followups: number;
  overdue_followups: number;
  followup_completion_rate: number;
  average_lead_score?: number | null;
}

export interface AIAnalytics {
  total_analyses: number;
  completed_analyses: number;
  failed_analyses: number;
  total_reviews: number;
  accepted_reviews: number;
  edited_reviews: number;
  rejected_reviews: number;
  acceptance_rate: number;
  edit_rate: number;
  rejection_rate: number;
}

export interface ConversionAnalytics {
  total_leads: number;
  converted_leads: number;
  conversion_rate: number;
  average_days_to_conversion?: number | null;
}

export interface AnalyticsResponse {
  generated_at: string;
  date_range: AnalyticsDateRange;
  overview: AnalyticsOverview;
  conversion: ConversionAnalytics;
  trend: AnalyticsTrendPoint[];
  source_performance: SourceAnalytics[];
  purchase_intent_breakdown: PurchaseIntentAnalytics[];
  lead_status_breakdown: LeadStatusAnalytics[];
  product_performance: ProductAnalytics[];
  followup_type_performance: FollowUpTypeAnalytics[];
  followup_status_breakdown: FollowUpStatusAnalytics[];
  team_performance: TeamAnalytics[];
  ai_metrics: AIAnalytics;
}

/* Products & Team */
export interface ProductResponse {
  id: string;
  organization_id: string;
  name: string;
  code?: string | null;
  description?: string | null;
  category?: string | null;
  price?: number | null;
  currency?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductCreateRequest {
  name: string;
  code?: string | null;
  description?: string | null;
  category?: string | null;
  price?: number | null;
  currency?: string | null;
  is_active?: boolean;
}

export interface ProductUpdate {
  name?: string | null;
  code?: string | null;
  description?: string | null;
  category?: string | null;
  price?: number | null;
  currency?: string | null;
  is_active?: boolean | null;
}

export interface UserResponse {
  id: string;
  organization_id: string;
  auth_user_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  avatar_url?: string | null;
  phone?: string | null;
  is_active: boolean;
  last_active_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface TeamMemberUpdate {
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
}

/* Notifications */
export interface NotificationResponse {
  id: string;
  organization_id: string;
  user_id: string;
  channel: NotificationChannel;
  title: string;
  body: string;
  message?: string;
  status: NotificationStatus;
  read_at?: string | null;
  data: Record<string, any>;
  created_at: string;
}

export interface NotificationCountResponse {
  total: number;
  unread: number;
  pending: number;
}

/* Standard API Error Format */
export interface OmniLeadApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
}
