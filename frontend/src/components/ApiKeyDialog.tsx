import { useState } from 'react'
import { setApiKey } from '../services/api'
import './ApiKeyDialog.css'

interface ApiKeyDialogProps {
  onConfirm: () => void
  onSkip: () => void
}

/**
 * API Key 配置对话框
 * 首次访问时如果未配置 API Key，弹出此对话框让用户输入
 */
export default function ApiKeyDialog({ onConfirm, onSkip }: ApiKeyDialogProps) {
  const [key, setKey] = useState('')
  const [showKey, setShowKey] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (key.trim()) {
      setApiKey(key.trim())
      onConfirm()
    }
  }

  return (
    <div className="api-key-overlay">
      <div className="api-key-dialog glass-card">
        <div className="api-key-icon">🔑</div>
        <h2>连接到战略咨询系统</h2>
        <p>请输入服务端提供的 API Key 以访问系统功能</p>
        <div className="api-key-hint">
          <p>💡 如果您不知道 API Key，请联系系统管理员获取</p>
          <p>如果服务端未启用认证，可直接跳过此步骤</p>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="api-key-input-wrapper">
            <input
              type={showKey ? 'text' : 'password'}
              className="glass-input"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="请输入 API Key"
              autoFocus
              aria-label="API Key"
            />
            <button
              type="button"
              className="toggle-visibility-btn"
              onClick={() => setShowKey(!showKey)}
              title={showKey ? '隐藏' : '显示'}
            >
              {showKey ? '🙈' : '👁️'}
            </button>
          </div>
          <button type="submit" className="glass-button primary-btn" disabled={!key.trim()}>
            确认连接
          </button>
        </form>
        <button className="skip-btn" onClick={onSkip}>
          跳过，直接使用（无需认证时）
        </button>
      </div>
    </div>
  )
}
