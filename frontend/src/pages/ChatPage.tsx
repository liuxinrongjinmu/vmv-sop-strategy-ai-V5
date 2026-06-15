import React, { useState, useRef, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { chatService, StreamEvent } from '../services/chat'
import { reportService } from '../services/report'
import { useAppStore } from '../stores/appStore'
import { MessageResponse } from '../types/message'
import { ReportType, REPORT_TYPE_INFO } from '../types/report'
import Sidebar from '../components/Sidebar'
import MessageList from '../components/MessageList'
import ChatInput from '../components/ChatInput'
import './ChatPage.css'

const ChatPage: React.FC = () => {
  const navigate = useNavigate()
  const { sessionId, sessionInfo, messages, currentStage, addMessage, updateLastAssistantMessage, updateLastAssistantMetadata, setMessages, setCurrentStage, setIsLoading, setIsStreaming, isLoading, isStreaming } = useAppStore()

  const [inputValue, setInputValue] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(window.innerWidth > 768)
  const [copiedId, setCopiedId] = useState<number | null>(null)
  const [isGeneratingReport, setIsGeneratingReport] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

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

  const handleStopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsStreaming(false)
    setIsLoading(false)
  }

  const handleSend = useCallback(async (overrideContent?: string) => {
    const contentToSend = overrideContent || inputValue.trim()
    if (!contentToSend || isLoading || isStreaming || !sessionId) return

    setInputValue('')

    addMessage({
      id: Date.now(),
      role: 'user',
      content: contentToSend,
      stage: currentStage,
      created_at: new Date().toISOString(),
      metadata: {}
    })

    // 创建AI占位消息
    const assistantId = Date.now() + 1
    addMessage({
      id: assistantId,
      role: 'assistant',
      content: '',
      stage: currentStage,
      created_at: new Date().toISOString(),
      metadata: {}
    })

    setIsLoading(true)
    setIsStreaming(true)
    let accumulatedContent = ''

    // 创建 AbortController
    const abortController = new AbortController()
    abortControllerRef.current = abortController

    try {
      await chatService.sendStream(
        { session_id: sessionId, content: contentToSend },
        (event: StreamEvent) => {
          switch (event.type) {
            case 'text':
              accumulatedContent += event.content || ''
              updateLastAssistantMessage(accumulatedContent)
              break
            case 'stage':
              if (event.stage) {
                setCurrentStage(event.stage)
              }
              break
            case 'report':
              if (event.content) {
                accumulatedContent = event.content
                updateLastAssistantMessage(accumulatedContent)
              }
              if (event.stage) {
                setCurrentStage(event.stage)
              }
              // 触发异步报告生成
              setCurrentStage(4)
              handleReportGeneration(contentToSend, (event as any).report_type || 'ten_year')
              break
            case 'meta':
              if (event.stage) {
                setCurrentStage(event.stage)
              }
              if (event.sources) {
                updateLastAssistantMetadata({ sources: event.sources })
              }
              break
            case 'error':
              accumulatedContent = event.content || '内容生成失败，请重试'
              updateLastAssistantMessage(accumulatedContent)
              break
          }
        },
        () => {
          // onDone
          setIsStreaming(false)
          setIsLoading(false)
          abortControllerRef.current = null
        },
        (error: string) => {
          // onError
          updateLastAssistantMessage('抱歉，处理您的消息时出现错误: ' + error)
          setIsStreaming(false)
          setIsLoading(false)
          abortControllerRef.current = null
        },
        abortController.signal
      )
    } catch (error: any) {
      if (error.name === 'AbortError') {
        // 用户主动停止
        if (!accumulatedContent) {
          updateLastAssistantMessage('[已停止生成]')
        }
      } else {
        updateLastAssistantMessage('抱歉，处理您的消息时出现错误: ' + (error.message || '未知错误'))
      }
      setIsStreaming(false)
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }, [inputValue, isLoading, isStreaming, sessionId, currentStage])

  const handleReportGeneration = async (prediction: string, reportType: string = 'ten_year') => {
    const typeInfo = REPORT_TYPE_INFO[reportType as ReportType] || REPORT_TYPE_INFO.ten_year

    // 请求浏览器通知权限
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }

    setIsGeneratingReport(true)

    // 添加进度占位消息
    addMessage({
      id: Date.now(),
      role: 'assistant',
      content: `📊 正在生成${typeInfo.label}报告，请稍候...\n\n💡 您可以继续对话，报告将在后台生成。完成后会在此处显示。`,
      stage: 4,
      created_at: new Date().toISOString(),
      metadata: { type: 'progress' }
    })

    try {
      const reportResponse = await reportService.generate(
        {
          session_id: sessionId!,
          prediction: prediction,
          report_type: reportType
        },
        (progress: number, message: string) => {
          updateLastAssistantMessage(`📊 ${message} (${progress}%)\n\n💡 您可以继续对话，报告将在后台生成。`)
        }
      )

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

      // 浏览器通知
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification('VMV-SOP 战略咨询', {
          body: `${typeInfo.label}报告已生成完成！`,
          icon: '/favicon.ico'
        })
      }
    } catch (reportError: any) {
      console.error('报告生成失败:', reportError)
      const errorMsg = reportError.response?.data?.detail || reportError.message || '未知错误'
      updateLastAssistantMessage('❌ 报告生成失败: ' + errorMsg)
      setCurrentStage(3)
    } finally {
      setIsGeneratingReport(false)
    }
  }

  const handleFileUpload = async (file: File) => {
    if (!sessionId) {
      sendSystemMessage('请先创建会话')
      return
    }

    const MAX_SIZE = 10 * 1024 * 1024
    if (file.size > MAX_SIZE) {
      sendSystemMessage(`文件过大(${(file.size / 1024 / 1024).toFixed(1)}MB)，请选择10MB以内的文件`)
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
    } catch (error: any) {
      console.error('文件上传失败:', error)
      let errorMsg = '文件上传失败'
      if (error.code === 'ERR_NETWORK' || !error.response) {
        errorMsg = '网络连接失败，请检查网络后重试'
      } else if (error.response) {
        const status = error.response.status
        const detail = error.response.data?.detail || error.message
        if (status === 413) {
          errorMsg = '文件过大，请选择更小的文件（最大10MB）'
        } else if (status === 400) {
          errorMsg = `文件格式不支持: ${detail}`
        } else if (status === 500) {
          errorMsg = `文件解析失败: ${detail}`
        } else {
          errorMsg = `上传失败(${status}): ${detail}`
        }
      } else {
        errorMsg = `上传失败: ${error.message || '未知错误'}`
      }
      sendSystemMessage(errorMsg + '，请重试。')
    } finally {
      setIsLoading(false)
    }
  }

  const copyMessage = async (content: string, messageId: number) => {
    try {
      await navigator.clipboard.writeText(content)
      setCopiedId(messageId)
      setTimeout(() => setCopiedId(null), 2000)
    } catch {
      const textarea = document.createElement('textarea')
      textarea.value = content
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
      setCopiedId(messageId)
      setTimeout(() => setCopiedId(null), 2000)
    }
  }

  /**
   * 重新生成消息：找到对应的用户消息，删除当前assistant消息后重新发送
   */
  const regenerateMessage = async (message: MessageResponse) => {
    if (isLoading || isStreaming) return
    const msgIndex = messages.findIndex(m => m.id === message.id)
    let userMsg = ''
    for (let i = msgIndex - 1; i >= 0; i--) {
      if (messages[i].role === 'user') {
        userMsg = messages[i].content
        break
      }
    }
    if (!userMsg) return

    // 删除当前assistant消息
    const newMessages = messages.filter(m => m.id !== message.id)
    setMessages(newMessages)

    // 直接调用发送逻辑
    setTimeout(() => handleSend(userMsg), 0)
  }

  return (
    <div className="chat-page">
      <div className="chat-container">
        <Sidebar
          sessionInfo={sessionInfo}
          currentStage={currentStage}
          isLoading={isLoading || isGeneratingReport}
          isStreaming={isStreaming}
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onReportGenerate={(prediction, reportType) => handleReportGeneration(prediction || inputValue, reportType)}
          onNewSession={() => {
            useAppStore.getState().reset()
            navigate('/')
          }}
          onNavigateSessions={() => navigate('/sessions')}
        />

        <div className="chat-main">
          <div className="messages-container">
            <MessageList
              messages={messages}
              copiedId={copiedId}
              onCopyMessage={copyMessage}
              onRegenerateMessage={regenerateMessage}
              isLoading={isLoading}
              isStreaming={isStreaming}
            />

            <div ref={messagesEndRef} />
          </div>

          <ChatInput
            value={inputValue}
            onChange={setInputValue}
            onSend={() => handleSend()}
            onStop={handleStopGeneration}
            onFileUpload={handleFileUpload}
            isLoading={isLoading}
            isStreaming={isStreaming}
          />
        </div>
      </div>
    </div>
  )
}

export default ChatPage
