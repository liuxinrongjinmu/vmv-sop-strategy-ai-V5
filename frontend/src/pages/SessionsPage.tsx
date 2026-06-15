import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { sessionService } from '../services/session'
import { useAppStore } from '../stores/appStore'
import { useToast } from '../components/Toast'
import { SessionResponse, SessionDetail } from '../types/session'
import { STAGE_NAMES } from '../constants/stages'
import './SessionsPage.css'

/**
 * 会话历史列表页面
 * 展示所有历史会话，支持恢复会话和删除会话
 */
const SessionsPage: React.FC = () => {
  const navigate = useNavigate()
  const { setSessionId, setSessionInfo } = useAppStore()
  const toast = useToast()

  const [sessions, setSessions] = useState<SessionDetail[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<string | null>(null)

  useEffect(() => {
    loadSessions()
  }, [])

  /**
   * 加载会话列表，逐个获取完整详情
   */
  const loadSessions = async () => {
    setLoading(true)
    try {
      const list = await sessionService.list()
      const details = await Promise.all(
        list.map((s: SessionResponse) => sessionService.get(s.session_id))
      )
      setSessions(details)
    } catch (error: any) {
      console.error('加载会话列表失败:', error)
      toast.error('加载会话列表失败')
    } finally {
      setLoading(false)
    }
  }

  /**
   * 恢复会话：设置sessionId和sessionInfo到store，跳转到/chat
   */
  const handleResume = async (sessionId: string) => {
    try {
      const detail = await sessionService.get(sessionId)
      setSessionId(detail.session_id)
      setSessionInfo(detail)
      navigate('/chat')
    } catch (error: any) {
      console.error('恢复会话失败:', error)
      toast.error('恢复会话失败')
    }
  }

  /**
   * 删除会话：确认后调用删除接口
   */
  const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation()
    if (!window.confirm('确定要删除该会话吗？删除后不可恢复。')) return

    setDeleting(sessionId)
    try {
      await sessionService.delete(sessionId)
      setSessions(prev => prev.filter(s => s.session_id !== sessionId))
      toast.success('会话已删除')
    } catch (error: any) {
      console.error('删除会话失败:', error)
      toast.error('删除会话失败')
    } finally {
      setDeleting(null)
    }
  }

  /**
   * 获取阶段标签样式类名
   */
  const getStageClass = (stage: number) => {
    if (stage >= 4) return 'stage-tag stage-tag-success'
    if (stage >= 2) return 'stage-tag stage-tag-warning'
    return 'stage-tag stage-tag-info'
  }

  /**
   * 获取状态标签文本
   */
  const getStatusText = (status: string) => {
    const map: Record<string, string> = {
      active: '进行中',
      completed: '已完成',
      archived: '已归档'
    }
    return map[status] || status
  }

  /**
   * 格式化时间
   */
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMin = Math.floor(diffMs / 60000)
    const diffHour = Math.floor(diffMs / 3600000)
    const diffDay = Math.floor(diffMs / 86400000)

    if (diffMin < 1) return '刚刚'
    if (diffMin < 60) return `${diffMin}分钟前`
    if (diffHour < 24) return `${diffHour}小时前`
    if (diffDay < 7) return `${diffDay}天前`
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className="sessions-page">
      <div className="sessions-container">
        <div className="sessions-header">
          <h1>会话历史</h1>
          <button
            className="glass-button new-session-btn"
            onClick={() => navigate('/')}
            title="开始新的咨询会话"
          >
            + 新建会话
          </button>
        </div>

        {loading ? (
          <div className="sessions-loading">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <p>加载中...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="sessions-empty glass-card-light">
            <div className="empty-icon">📭</div>
            <h3>暂无会话记录</h3>
            <p>开始您的第一次战略咨询吧</p>
            <button
              className="glass-button"
              onClick={() => navigate('/')}
            >
              创建新会话
            </button>
          </div>
        ) : (
          <div className="sessions-grid">
            {sessions.map(session => (
              <div
                key={session.session_id}
                className="session-card glass-card fade-in"
                onClick={() => handleResume(session.session_id)}
                title="点击恢复该会话"
              >
                <button
                  className="delete-btn"
                  onClick={(e) => handleDelete(e, session.session_id)}
                  disabled={deleting === session.session_id}
                  title="删除会话"
                >
                  ×
                </button>

                <div className="session-card-header">
                  <h3 className="company-name">{session.company_name || '未命名企业'}</h3>
                  <span className={getStageClass(session.current_stage)}>
                    {STAGE_NAMES[session.current_stage - 1] || `阶段${session.current_stage}`}
                  </span>
                </div>

                <div className="session-card-body">
                  {session.industry && (
                    <div className="session-info-row">
                      <span className="info-label">行业</span>
                      <span className="info-value">{session.industry}</span>
                    </div>
                  )}
                  {session.selected_track && (
                    <div className="session-info-row">
                      <span className="info-label">赛道</span>
                      <span className="info-value">{session.selected_track}</span>
                    </div>
                  )}
                  {session.stage && (
                    <div className="session-info-row">
                      <span className="info-label">阶段</span>
                      <span className="info-value">{session.stage}</span>
                    </div>
                  )}
                </div>

                <div className="session-card-footer">
                  <span className="session-status">{getStatusText(session.status)}</span>
                  <span className="session-time">{formatDate(session.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default SessionsPage
