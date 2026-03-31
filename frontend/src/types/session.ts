export interface SessionCreate {
  vision: string
  mission: string
  values: string[]
  company_name: string
  industry: string
  stage: string
  team_size?: string
  selected_track: string
  additional_info?: string
}

export interface SessionResponse {
  session_id: string
  current_stage: number
  status: string
  created_at: string
}

export interface SessionDetail extends SessionResponse {
  vision?: string
  mission?: string
  values?: string[]
  company_name?: string
  industry?: string
  stage?: string
  team_size?: string
  selected_track?: string
  additional_info?: string
}
