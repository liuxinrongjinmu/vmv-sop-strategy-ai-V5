import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../stores/appStore'
import { sessionService } from '../services/session'
import './InitPage.css'

const stages = [
  { value: '0-1', label: '0-1阶段（初创期）' },
  { value: '1-10', label: '1-10阶段（成长期）' },
  { value: '10-N', label: '10-N阶段（成熟期）' }
]

const teamSizes = [
  { value: '1-10', label: '1-10人' },
  { value: '11-50', label: '11-50人' },
  { value: '51-100', label: '51-100人' },
  { value: '101-500', label: '101-500人' },
  { value: '501-1000', label: '501-1000人' },
  { value: '1000+', label: '1000人以上' }
]

const STORAGE_KEY = 'vmv_sop_init_data'

const InitPage: React.FC = () => {
  const navigate = useNavigate()
  const { setSessionId, setSessionInfo } = useAppStore()
  
  const [formData, setFormData] = useState({
    company_name: '',
    industry: '',
    current_size: '',
    stage: '',
    core_business: '',
    selected_track: '',
    vision: '',
    mission: '',
    values: [''],
    additional_info: ''
  })
  
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const loadHistory = () => {
      try {
        const savedData = localStorage.getItem(STORAGE_KEY)
        if (savedData) {
          const parsedData = JSON.parse(savedData)
          setFormData(prev => ({
            ...prev,
            ...parsedData
          }))
        }
      } catch (error) {
        console.error('加载历史数据失败:', error)
      }
    }
    loadHistory()
  }, [])

  const saveToStorage = (data: any) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    } catch (error) {
      console.error('保存数据失败:', error)
    }
  }

  const handleInputChange = (field: string, value: string | number | undefined) => {
    const newData = { ...formData, [field]: value }
    setFormData(newData)
    saveToStorage(newData)
  }

  const handleValueChange = (index: number, value: string) => {
    const newValues = [...formData.values]
    newValues[index] = value
    const newData = { ...formData, values: newValues }
    setFormData(newData)
    saveToStorage(newData)
  }

  const addValue = () => {
    const newValues = [...formData.values, '']
    const newData = { ...formData, values: newValues }
    setFormData(newData)
    saveToStorage(newData)
  }

  const removeValue = (index: number) => {
    if (formData.values.length > 1) {
      const newValues = formData.values.filter((_, i) => i !== index)
      const newData = { ...formData, values: newValues }
      setFormData(newData)
      saveToStorage(newData)
    }
  }

  const handleSubmit = async () => {
    const hasValidValues = formData.values.some(v => v.trim() !== '')
    
    if (!formData.company_name || !formData.industry || !formData.current_size ||
        !formData.stage || !formData.selected_track || !formData.vision || !formData.mission || !hasValidValues) {
      alert('请填写所有必填项（包括至少一个价值观）')
      return
    }

    setLoading(true)
    try {
      console.log('开始提交表单...')
      
      const sessionData = {
        vision: formData.vision,
        mission: formData.mission,
        values: formData.values.filter(v => v.trim()),
        company_name: formData.company_name,
        industry: formData.industry,
        stage: formData.stage,
        team_size: formData.current_size,
        selected_track: formData.selected_track,
        additional_info: formData.additional_info || formData.core_business
      }

      console.log('发送请求到后端...')
      const data = await sessionService.create(sessionData)

      console.log('响应数据:', data)
      
      setSessionId(data.session_id)
      setSessionInfo({
        vision: formData.vision,
        mission: formData.mission,
        values: formData.values.filter(v => v.trim()),
        company_name: formData.company_name,
        industry: formData.industry,
        stage: formData.stage,
        team_size: formData.current_size,
        selected_track: formData.selected_track,
        additional_info: formData.additional_info || formData.core_business,
        session_id: data.session_id,
        current_stage: data.current_stage,
        status: data.status,
        created_at: data.created_at
      })
      
      console.log('导航到聊天页面...')
      navigate('/chat')
    } catch (error: any) {
      console.error('创建会话失败:', error)
      alert(`创建会话失败: ${error.message}`)
    } finally {
      console.log('提交完成')
      setLoading(false)
    }
  }

  return (
    <div className="init-page">
      <div className="init-container glass-card">
        <div className="init-header">
          <h1>VMV-SOP战略咨询系统</h1>
          <p>基于From VMV to SOP方法论，为企业提供专业的十年战略分析</p>
        </div>

        <div className="form-content">
          <div className="form-section glass-card-dark">
            <div className="section-header">
              <span className="section-icon">📋</span>
              <h2>企业/项目基础信息</h2>
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label>项目名称 <span className="required">*</span></label>
                <input
                  type="text"
                  className="glass-input"
                  placeholder="例如：智慧零售解决方案"
                  value={formData.company_name}
                  onChange={(e) => handleInputChange('company_name', e.target.value)}
                />
              </div>
              
              <div className="form-group">
                <label>所属行业 <span className="required">*</span></label>
                <input
                  type="text"
                  className="glass-input"
                  placeholder="例如：人工智能、互联网、金融科技"
                  value={formData.industry}
                  onChange={(e) => handleInputChange('industry', e.target.value)}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>当前规模 <span className="required">*</span></label>
                <select
                  className="glass-select"
                  value={formData.current_size}
                  onChange={(e) => handleInputChange('current_size', e.target.value)}
                >
                  <option value="">请选择规模</option>
                  {teamSizes.map(size => (
                    <option key={size.value} value={size.value}>{size.label}</option>
                  ))}
                </select>
              </div>
              
              <div className="form-group">
                <label>当前阶段 <span className="required">*</span></label>
                <select
                  className="glass-select"
                  value={formData.stage}
                  onChange={(e) => handleInputChange('stage', e.target.value)}
                >
                  <option value="">请选择阶段</option>
                  {stages.map(s => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label>核心业务</label>
              <input
                type="text"
                className="glass-input"
                placeholder="简要描述您的核心业务模式、产品/服务、目标客户群体"
                value={formData.core_business}
                onChange={(e) => handleInputChange('core_business', e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>细分赛道 <span className="required">*</span></label>
              <input
                type="text"
                className="glass-input"
                placeholder="例如：国产平行游戏改编动画"
                value={formData.selected_track}
                onChange={(e) => handleInputChange('selected_track', e.target.value)}
              />
            </div>
          </div>

          <div className="form-section glass-card-dark">
            <div className="section-header">
              <span className="section-icon">🎯</span>
              <h2>VMV（愿景 / 使命 / 价值观）</h2>
            </div>
            
            <div className="form-group">
              <label>愿景 (Vision) <span className="required">*</span></label>
              <input
                type="text"
                className="glass-input"
                placeholder="例如：成为中小团队能力放大的技术方案提供商"
                value={formData.vision}
                onChange={(e) => handleInputChange('vision', e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>使命 (Mission) <span className="required">*</span></label>
              <input
                type="text"
                className="glass-input"
                placeholder="例如：为中小微企业提供性价比高的数字化转型工具"
                value={formData.mission}
                onChange={(e) => handleInputChange('mission', e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>价值观 (Values) <span className="required">*</span></label>
              {formData.values.map((value, index) => (
                <div key={index} className="value-input-row">
                  <input
                    type="text"
                    className="glass-input"
                    placeholder={`价值观 ${index + 1}，例如：客户至上、持续创新、诚信负责`}
                    value={value}
                    onChange={(e) => handleValueChange(index, e.target.value)}
                  />
                  {formData.values.length > 1 && (
                    <button 
                      className="remove-btn"
                      onClick={() => removeValue(index)}
                    >
                      ×
                    </button>
                  )}
                </div>
              ))}
              <button className="add-value-btn" onClick={addValue}>
                + 添加价值观
              </button>
            </div>
          </div>

          <div className="form-actions">
            <button 
              className="submit-btn"
              onClick={handleSubmit}
              disabled={loading}
            >
              {loading ? '提交中...' : '完成初始化，进入对话'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InitPage
