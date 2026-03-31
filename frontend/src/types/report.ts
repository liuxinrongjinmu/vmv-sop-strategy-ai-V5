export interface ReportCreate {
  session_id: string
  report_type?: string
  prediction: string
}

export interface ReportResponse {
  id: number
  title: string
  content: string
  sources?: SourceItem[]
  created_at: string
}

export interface SourceItem {
  title: string
  url: string
  snippet: string
}
