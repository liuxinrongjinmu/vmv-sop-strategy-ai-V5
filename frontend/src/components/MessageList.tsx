import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { MessageResponse } from '../types/message'
import { reportService } from '../services/report'

interface MessageListProps {
  messages: MessageResponse[]
  copiedId: number | null
  onCopyMessage: (content: string, id: number) => void
  onRegenerateMessage: (message: MessageResponse) => void
  isLoading: boolean
  isStreaming: boolean
}

/**
 * 消息列表组件：渲染聊天消息、代码高亮、复制和重新生成操作
 */
const MessageList: React.FC<MessageListProps> = ({
  messages,
  copiedId,
  onCopyMessage,
  onRegenerateMessage,
  isLoading,
  isStreaming
}) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [showSearch, setShowSearch] = useState(false)

  const filteredMessages = searchQuery.trim()
    ? messages.filter(m =>
        m.content.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : messages

  // 搜索结果计数
  const searchCount = searchQuery.trim() ? filteredMessages.length : 0
  const formatMessageTime = (dateStr: string): string => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins}分钟前`
    if (diffHours < 24) return date.toLocaleTimeString()
    if (diffDays < 7) return `${diffDays}天前`
    return date.toLocaleDateString()
  }

  const handleExport = async (reportId: number | undefined, format: 'md' | 'pdf' | 'docx') => {
    if (!reportId) return
    try {
      await reportService.downloadReport(reportId, format)
    } catch (error) {
      console.error('导出报告失败:', error)
    }
  }

  const renderMessage = (message: MessageResponse) => {
    const isUser = message.role === 'user'
    const metadata = message.metadata

    return (
      <div key={message.id} className={`message-item ${isUser ? 'user' : 'assistant'} fade-in`}>
        <div className="message-avatar">
          {isUser ? '👤' : '🤖'}
        </div>
        <div className="message-content">
          {isUser ? (
            <div className="message-text">{message.content}</div>
          ) : (
            <div className="message-markdown">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    return match ? (
                      <SyntaxHighlighter
                        style={oneDark as { [key: string]: React.CSSProperties }}
                        language={match[1]}
                        PreTag="div"
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    )
                  }
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {!isUser && (
            <div className="message-actions">
              <button className="msg-action-btn" onClick={() => onCopyMessage(message.content, message.id)} title={copiedId === message.id ? '已复制' : '复制'}>
                {copiedId === message.id ? (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                ) : (
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                    <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/>
                  </svg>
                )}
                <span>{copiedId === message.id ? '已复制' : '复制'}</span>
              </button>
              <button className="msg-action-btn" onClick={() => onRegenerateMessage(message)} title="重新生成" disabled={isLoading || isStreaming}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="23 4 23 10 17 10"/>
                  <path d="M20.49 15a9 9 0 11-2.12-9.36L23 10"/>
                </svg>
                <span>重新生成</span>
              </button>
            </div>
          )}

          {metadata?.type === 'report' && (
            <div className="report-actions">
              <div className="export-buttons">
                <span className="export-label">下载报告：</span>
                <button
                  className="export-btn"
                  onClick={() => handleExport(metadata.report_id, 'md')}
                  title="导出为Markdown"
                >
                  MD
                </button>
                <button
                  className="export-btn"
                  onClick={() => handleExport(metadata.report_id, 'pdf')}
                  title="导出为PDF"
                >
                  PDF
                </button>
                <button
                  className="export-btn"
                  onClick={() => handleExport(metadata.report_id, 'docx')}
                  title="导出为Word"
                >
                  DOCX
                </button>
              </div>
            </div>
          )}

          <div className="message-time" title={new Date(message.created_at).toLocaleString()}>
            {formatMessageTime(message.created_at)}
          </div>
        </div>
      </div>
    )
  }

  return (
    <>
      {/* 搜索栏 */}
      <div className="message-search-bar">
        {showSearch ? (
          <div className="search-input-wrapper">
            <input
              type="text"
              className="glass-input search-input"
              placeholder="搜索消息..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
            />
            {searchQuery.trim() && (
              <span className="search-count">{searchCount} 条结果</span>
            )}
            <button className="search-close-btn" onClick={() => { setSearchQuery(''); setShowSearch(false) }}>
              ✕
            </button>
          </div>
        ) : (
          <button className="search-toggle-btn" onClick={() => setShowSearch(true)} title="搜索消息">
            🔍
          </button>
        )}
      </div>

      {/* 消息列表 */}
      {filteredMessages.length === 0 && messages.length > 0 && searchQuery.trim() && (
        <div className="no-results">未找到匹配的消息</div>
      )}

      {messages.length === 0 && (
        <div className="welcome-message glass-card-light">
          <h3>欢迎使用战略咨询系统</h3>
          <p>我是您的战略顾问，将帮助您进行十年战略预判分析。</p>
          <p>您可以：</p>
          <ul>
            <li>补充更多企业信息</li>
            <li>提出需要探讨的问题</li>
            <li>直接分享您对赛道的预判（系统将自动生成分析报告）</li>
          </ul>
        </div>
      )}

      {filteredMessages.map(renderMessage)}

      {isLoading && !isStreaming && (
        <div className="message-item assistant">
          <div className="message-avatar">🤖</div>
          <div className="message-content">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default MessageList
