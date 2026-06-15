import React from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../stores/appStore'
import { useThemeStore } from '../stores/themeStore'
import { SessionDetail } from '../types/session'
import { STAGE_NAMES } from '../constants/stages'

interface SidebarProps {
  sessionInfo: SessionDetail | null
  currentStage: number
  isLoading: boolean
  isStreaming: boolean
  sidebarOpen: boolean
  onToggleSidebar: () => void
  onReportGenerate: (prediction: string, reportType: string) => void
  onNewSession: () => void
  onNavigateSessions: () => void
}

/**
 * 侧边栏组件：展示企业信息、战略工具箱、阶段指示器和操作按钮
 */
const Sidebar: React.FC<SidebarProps> = ({
  sessionInfo,
  currentStage,
  isLoading,
  isStreaming,
  sidebarOpen,
  onToggleSidebar,
  onReportGenerate,
  onNewSession,
  onNavigateSessions
}) => {
  const { theme, toggleTheme } = useThemeStore()

  return (
    <>
      <button
        className="hamburger-btn"
        onClick={onToggleSidebar}
        title="切换侧边栏"
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="3" y1="6" x2="21" y2="6"/>
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>

      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={onToggleSidebar} />
      )}

      <div className={`sidebar ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}>
        <div className="header-left">
          <h2>{sessionInfo?.company_name || '战略咨询'}</h2>
        </div>

        {sessionInfo && (
          <div className="company-info">
            {sessionInfo.selected_track && (
              <div className="info-item">
                <div className="info-label">赛道</div>
                <div className="info-value">{sessionInfo.selected_track}</div>
              </div>
            )}
            {sessionInfo.vision && (
              <div className="info-item">
                <div className="info-label">愿景</div>
                <div className="info-value">{sessionInfo.vision}</div>
              </div>
            )}
            {sessionInfo.mission && (
              <div className="info-item">
                <div className="info-label">使命</div>
                <div className="info-value">{sessionInfo.mission}</div>
              </div>
            )}
            {sessionInfo.values && (
              <div className="info-item">
                <div className="info-label">价值观</div>
                <div className="info-value">
                  {Array.isArray(sessionInfo.values)
                    ? sessionInfo.values.map((v, i) => (
                        <span key={i} className="value-tag">{v}</span>
                      ))
                    : String(sessionInfo.values)
                  }
                </div>
              </div>
            )}
          </div>
        )}

        <div className="strategy-toolbox">
          <div className="toolbox-title">战略分析工具箱</div>
          <div className="toolbox-hint">按顺序使用，后者基于前者结论</div>
          <div className="toolbox-buttons">
            <button
              className="toolbox-btn"
              onClick={() => onReportGenerate('请基于已有信息生成十年战略预判分析', 'ten_year')}
              disabled={isLoading || isStreaming}
              title="对赛道未来十年进行正反论证预判"
            >
              🔭 十年预判
              <span className="toolbox-desc">赛道趋势预判</span>
            </button>
            <button
              className="toolbox-btn"
              onClick={() => onReportGenerate('请基于已有信息生成五年关键驱动因素分析', 'five_year')}
              disabled={isLoading || isStreaming}
              title="识别五年内关键驱动因素及距离分析"
            >
              🔍 五年驱动
              <span className="toolbox-desc">关键驱动因素</span>
            </button>
            <button
              className="toolbox-btn"
              onClick={() => onReportGenerate('请基于已有信息生成三年阶段性目标', 'three_year')}
              disabled={isLoading || isStreaming}
              title="设定三年定性定量阶段性目标"
            >
              🎯 三年目标
              <span className="toolbox-desc">阶段性目标</span>
            </button>
            <button
              className="toolbox-btn"
              onClick={() => onReportGenerate('请基于已有信息生成一年任务分解与战略屋', 'one_year')}
              disabled={isLoading || isStreaming}
              title="分解年度任务，构建战略屋和SOP框架"
            >
              📋 一年分解
              <span className="toolbox-desc">战略屋+SOP</span>
            </button>
          </div>
        </div>

        <div className="stage-indicator">
          <div className="stage-title">分析阶段</div>
          {STAGE_NAMES.map((name, index) => (
            <div
              key={index}
              className={`stage-item ${currentStage === index + 1 ? 'active' : ''} ${currentStage > index + 1 ? 'completed' : ''}`}
            >
              <div className="stage-dot">{index + 1}</div>
              <span className="stage-name">{name}</span>
              {currentStage > index + 1 && (
                <div className="stage-check">✓</div>
              )}
            </div>
          ))}
        </div>

        <div className="sidebar-actions">
          <button
            className="glass-button theme-toggle-btn"
            onClick={toggleTheme}
            title={theme === 'dark' ? '切换到浅色模式' : '切换到深色模式'}
          >
            {theme === 'dark' ? '☀️ 浅色模式' : '🌙 深色模式'}
          </button>
          <button
            className="glass-button history-btn"
            onClick={onNavigateSessions}
            title="查看历史会话"
          >
            📋 历史会话
          </button>
          <button
            className="glass-button new-session-btn"
            onClick={onNewSession}
            title="开始新的咨询会话"
          >
            + 新建会话
          </button>
        </div>
      </div>
    </>
  )
}

export default Sidebar
