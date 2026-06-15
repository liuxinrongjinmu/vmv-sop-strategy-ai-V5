import api from './api'
import { ReportCreate, ReportResponse } from '../types/report'

export const reportService = {
  async generate(data: ReportCreate, onProgress?: (progress: number, message: string) => void): Promise<ReportResponse> {
    const startResponse = await api.post('/report/generate', data)
    const taskId = startResponse.data.task_id
    
    if (!taskId) {
      throw new Error('未获取到任务ID')
    }
    
    const maxAttempts = 240  // 延长到12分钟
    const interval = 3000
    
    for (let i = 0; i < maxAttempts; i++) {
      await new Promise(resolve => setTimeout(resolve, interval))
      
      try {
        const statusResponse = await api.get(`/report/task/${taskId}`)
        const status = statusResponse.data
        
        if (onProgress && status.progress !== undefined) {
          onProgress(status.progress, status.message || '正在生成报告...')
        }
        
        if (status.status === 'completed' && status.report) {
          return {
            id: status.report.id,
            title: status.report.title,
            content: status.report.content,
            sources: status.report.sources,
            created_at: status.report.created_at
          }
        }
        
        if (status.status === 'failed') {
          throw new Error(status.message || '报告生成失败')
        }
      } catch (error: any) {
        if (error.message && error.message !== '报告生成失败') {
          continue
        }
        throw error
      }
    }
    
    throw new Error('报告生成超时，请稍后重试')
  },

  async get(reportId: number): Promise<ReportResponse> {
    const response = await api.get(`/report/${reportId}`)
    return response.data
  },

  async downloadReport(reportId: number, format: 'md' | 'pdf' | 'docx'): Promise<void> {
    const response = await api.get(`/report/${reportId}/export`, {
      params: { format },
      responseType: 'blob'
    })

    // 从 Content-Disposition 提取文件名，或使用默认名
    const contentDisposition = response.headers['content-disposition']
    let downloadFilename = `战略分析报告.${format}`
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename\*=UTF-8''(.+)/)
      if (filenameMatch) {
        downloadFilename = decodeURIComponent(filenameMatch[1])
      }
    }

    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = downloadFilename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
  }
}
