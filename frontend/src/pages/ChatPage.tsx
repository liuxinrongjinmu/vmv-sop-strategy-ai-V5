import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { chatService } from '../services/chat'
import { reportService } from '../services/report'
import { useAppStore } from '../stores/appStore'
import { MessageResponse } from '../types/message'
import './ChatPage.css'

const stageNames = ['信息补充', '自由提问', '预判采集', '报告生成', '报告反馈']

const ChatPage: React.FC = () => {
  const navigate = useNavigate()
  const { sessionId, sessionInfo, messages, currentStage, addMessage, setMessages, setCurrentStage, setIsLoading, isLoading } = useAppStore()
  
  const [inputValue, setInputValue] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!sessionId) {
      navigate('/')
      return
    }
    
    loadHistory()
  }, [sessionId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    if (messages.length === 0 && sessionId && sessionInfo) {
      const welcomeMessage = `您好，我是您的战略顾问，将帮助您进行十年战略预判分析。

基于您提供的信息，我已了解到：
- 企业/项目名称：${sessionInfo.company_name}
- 所属行业：${sessionInfo.industry || '未提供'}
- 当前规模：${sessionInfo.team_size || '未提供'}
- 当前阶段：${sessionInfo.stage || '未提供'}
- 核心业务：${sessionInfo.additional_info || '未提供'}
- 细分赛道：${sessionInfo.selected_track || '未提供'}
- 愿景：${sessionInfo.vision || '未提供'}
- 使命：${sessionInfo.mission || '未提供'}
- 价值观：${sessionInfo.values?.join('、') || '未提供'}

您可以：
1. 补充更多信息
2. 提出需要探讨的问题
3. 直接分享您对赛道的预判（系统将自动生成分析报告）`
      sendSystemMessage(welcomeMessage)
    }
  }, [messages.length, sessionId])

  const loadHistory = async () => {
    if (!sessionId) return
    
    try {
      const history = await chatService.getHistory(sessionId)
      setMessages(history)
    } catch (error) {
      console.error('加载历史消息失败:', error)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const sendSystemMessage = (content: string) => {
    addMessage({
      id: Date.now(),
      role: 'assistant',
      content: content,
      stage: currentStage,
      created_at: new Date().toISOString(),
      metadata: {}
    })
  }

  const handleSend = async () => {
    if (!inputValue.trim() || isLoading || !sessionId) return

    const userMessage = inputValue.trim()
    setInputValue('')
    
    addMessage({
      id: Date.now(),
      role: 'user',
      content: userMessage,
      stage: currentStage,
      created_at: new Date().toISOString(),
      metadata: {}
    })
    
    setIsLoading(true)
    
    try {
      const isPrediction = userMessage.length > 50 || 
        userMessage.includes('预判') || 
        userMessage.includes('预测') || 
        userMessage.includes('我认为') ||
        userMessage.includes('前景') ||
        userMessage.includes('趋势') ||
        userMessage.includes('增长')
      
      if (isPrediction && currentStage <= 3) {
        setCurrentStage(4)
        sendSystemMessage('感谢您的分享，我将基于您提供的所有信息生成一份详细的分析报告。请稍候...')
        
        try {
          const reportResponse = await reportService.generate({
            session_id: sessionId,
            prediction: userMessage
          })
          
          console.log('报告生成成功:', reportResponse)
          
          addMessage({
            id: Date.now(),
            role: 'assistant',
            content: reportResponse.content,
            stage: 4,
            created_at: new Date().toISOString(),
            metadata: {
              type: 'report',
              report_id: reportResponse.id,
              sources: reportResponse.sources
            }
          })
          
          setCurrentStage(5)
          sendSystemMessage('报告已为您生成，请问您对这份报告，还有需要交流、探讨的地方吗？')
        } catch (reportError: any) {
          console.error('报告生成失败:', reportError)
          const errorMsg = reportError.response?.data?.detail || reportError.message || '未知错误'
          sendSystemMessage('报告生成失败: ' + errorMsg)
          setCurrentStage(3)
        }
      } else if (userMessage.includes('不需要') || userMessage.includes('不用') || userMessage.includes('没有') || userMessage.includes('满意')) {
        if (currentStage === 5) {
          sendSystemMessage('非常感谢您的参与，希望这份分析报告对您有所帮助。如果后续有任何问题，随时可以再次咨询。')
        } else {
          sendSystemMessage('好的，如果您准备好了预判，请直接分享您对赛道的看法和预测。')
        }
      } else {
        const response = await chatService.send({
          session_id: sessionId,
          content: userMessage
        })
        addMessage(response)
        
        if (response.stage) {
          setCurrentStage(response.stage)
        }
      }
    } catch (error: any) {
      console.error('处理消息失败:', error)
      sendSystemMessage('抱歉，处理您的消息时出现错误: ' + (error.response?.data?.detail || error.message || '未知错误'))
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    const file = files[0]
    
    if (!sessionId) {
      sendSystemMessage('请先创建会话')
      return
    }
    
    try {
      setIsLoading(true)
      const response = await chatService.uploadFile(file, sessionId)
      
      const summaryMessage = `请帮我分析总结刚刚上传的文件"${response.filename}"的核心内容。文件内容摘要如下：\n\n${response.content}\n\n请详细总结这份文件的核心要点，并分析其与我们当前战略讨论的关联性。`
      
      addMessage({
        id: Date.now(),
        role: 'user',
        content: `上传文件: ${response.filename}`,
        stage: currentStage,
        created_at: new Date().toISOString(),
        metadata: {}
      })
      
      const aiResponse = await chatService.send({
        session_id: sessionId,
        content: summaryMessage
      })
      
      addMessage(aiResponse)
      setCurrentStage(aiResponse.stage)
    } catch (error) {
      console.error('文件上传失败:', error)
      sendSystemMessage('文件上传失败，请重试。')
    } finally {
      setIsLoading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleExport = (reportId: number, format: 'md' | 'pdf' | 'docx') => {
    const url = reportService.getExportUrl(reportId, format)
    window.open(url, '_blank')
  }

  const renderMessage = (message: MessageResponse) => {
    const isUser = message.role === 'user'
    const metadata = message.metadata as any

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
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
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
          
          <div className="message-time">
            {new Date(message.created_at).toLocaleTimeString()}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="chat-page">
      <div className="chat-container">
        <div className="sidebar">
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
                  <div className="info-value">{sessionInfo.values}</div>
                </div>
              )}
            </div>
          )}
          
          <div className="stage-indicator">
            <div className="stage-title">分析阶段</div>
            {stageNames.map((name, index) => (
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
        </div>

        <div className="chat-main">
          <div className="messages-container">
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
            
            {messages.map(renderMessage)}
            
            {isLoading && (
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
            
            <div ref={messagesEndRef} />
          </div>

          <div className="input-container">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.docx,.doc"
              style={{ display: 'none' }}
            />
            
            <button 
              className="upload-btn"
              onClick={() => fileInputRef.current?.click()}
              title="上传文件"
            >
              📎
            </button>
            
            <textarea
              className="input-textarea"
              placeholder="输入消息... (直接分享您的预判即可生成报告)"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              rows={1}
            />
            
            <button 
              className="send-btn glass-button"
              onClick={handleSend}
              disabled={!inputValue.trim() || isLoading}
            >
              发送
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatPage
