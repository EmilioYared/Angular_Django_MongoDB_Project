export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string | null;
}

export interface UserProfile {
  id: string;
  user_id: string;
  full_name: string;
  profile_email: string;
  joined_date: string | null;
  profile_image_url: string | null;
}

export interface AuthResponse {
  token: string;
  user: User;
  profile: UserProfile | null;
}

export interface Tag {
  id: string;
  name: string;
  created_at: string | null;
}

export interface ProjectMember {
  id: string;
  project_id: string;
  user_id: string | null;
  username: string | null;
  email: string | null;
  role: string;
  added_at: string | null;
}

export interface Project {
  id: string;
  title: string;
  description: string;
  created_at: string | null;
  updated_at: string | null;
  owner_id: string;
  owner_email: string | null;
  visibility_status: string;
  cover_image_url: string | null;
  access_role: string;
  members_count: number;
  tags: Tag[];
}

export interface ProjectDetail extends Project {
  members: ProjectMember[];
}

export interface ProjectListResponse {
  projects: Project[];
}

export interface ProjectDetailResponse {
  project: ProjectDetail;
}

export interface DocumentRecord {
  id: string;
  project_id: string;
  uploaded_by_user_id: string;
  title: string;
  original_filename: string | null;
  document_type: string | null;
  uploaded_at: string | null;
  updated_at: string | null;
  chunk_count: number;
  indexing_status: string;
  file_url: string | null;
  thumbnail_image_url: string | null;
  excerpt: string;
}

export interface DocumentsResponse {
  documents: DocumentRecord[];
}

export interface SemanticMatch {
  chunk_id: string;
  document_id: string;
  document_title: string;
  snippet: string;
  score: number;
  chunk_index: number;
  model_name: string;
}

export interface SemanticSearchResponse {
  project_id: string;
  question: string;
  message: string;
  matches: SemanticMatch[];
  generated_answer: string | null;
}

export interface QueryLog {
  id: string;
  project_id: string;
  user_id: string;
  query_text: string;
  top_k: number;
  created_at: string | null;
}

export interface QueryHistoryResponse {
  queries: QueryLog[];
}
