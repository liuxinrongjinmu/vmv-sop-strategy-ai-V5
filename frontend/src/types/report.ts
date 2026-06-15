import { SourceItem } from './message'

export type ReportType = 'ten_year' | 'five_year' | 'three_year' | 'one_year'

export const REPORT_TYPE_INFO: Record<ReportType, { label: string; description: string }> = {
  ten_year: { label: '十年战略预判', description: '赛道预判分析，正反论据和综合判断' },
  five_year: { label: '五年关键驱动因素', description: '识别关键驱动因素，分析与企业距离' },
  three_year: { label: '三年阶段性目标', description: '设定阶段性目标，确立里程碑' },
  one_year: { label: '一年任务分解', description: '战略屋拆解，组织战与财务验算' }
}

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
