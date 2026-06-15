import React, { useRef } from 'react'

interface ChatInputProps {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  onStop: () => void
  onFileUpload: (file: File) => void
  isLoading: boolean
  isStreaming: boolean
}

/**
 * 聊天输入区域组件：文本输入、文件上传和发送按钮
 */
const ChatInput: React.FC<ChatInputProps> = ({
  value,
  onChange,
  onSend,
  onStop,
  onFileUpload,
  isLoading,
  isStreaming
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return
    onFileUpload(files[0])
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="input-container">
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept=".pdf,.docx,.doc,.md"
        style={{ display: 'none' }}
      />

      <button
        className="upload-icon-btn"
        onClick={() => fileInputRef.current?.click()}
        title="上传文件（支持PDF、DOCX、MD）"
      >
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"/>
        </svg>
      </button>

      <textarea
        className="input-textarea"
        placeholder="输入消息... （直接分享您的预判即可生成报告）"
        value={value}
        onChange={(e) => {
          onChange(e.target.value)
          // 自动调整高度
          e.target.style.height = 'auto'
          e.target.style.height = Math.min(e.target.scrollHeight, 140) + 'px'
        }}
        onKeyDown={handleKeyDown}
        disabled={isStreaming}
        rows={1}
      />

      {isStreaming ? (
        <button
          className="stop-circle-btn"
          onClick={onStop}
          title="停止生成"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <rect x="6" y="6" width="12" height="12" rx="2"/>
          </svg>
        </button>
      ) : value.trim() ? (
        <button
          className="send-circle-btn"
          onClick={onSend}
          disabled={!value.trim() || isStreaming}
          title="发送"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/>
            <polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      ) : (
        <div className="voice-circle-btn" title="语音输入（即将支持）">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
            <line x1="12" y1="19" x2="12" y2="23"/>
            <line x1="8" y1="23" x2="16" y2="23"/>
          </svg>
        </div>
      )}
    </div>
  )
}

export default ChatInput
