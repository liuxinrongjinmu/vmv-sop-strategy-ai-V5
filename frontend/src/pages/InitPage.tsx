import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../stores/appStore'
import { sessionService } from '../services/session'
import { useToast } from '../components/Toast'
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
const STORAGE_EXPIRY_MS = 7 * 24 * 60 * 60 * 1000 // 7天过期

interface StorageData {
  formData: typeof formDataInitial
  savedAt: number
}

const formDataInitial = {
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
}

const InitPage: React.FC = () => {
  const navigate = useNavigate()
  const { setSessionId, setSessionInfo } = useAppStore()
  const toast = useToast()

  const [step, setStep] = useState(1)
  const [formData, setFormData] = useState(formDataInitial)
  const [touched, setTouched] = useState<Record<string, boolean>>({})
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const loadHistory = () => {
      try {
        const savedData = localStorage.getItem(STORAGE_KEY)
        if (savedData) {
          const parsed: StorageData = JSON.parse(savedData)
          // 检查是否过期
          if (parsed.savedAt && Date.now() - parsed.savedAt < STORAGE_EXPIRY_MS) {
            setFormData(prev => ({
              ...prev,
              ...parsed.formData
            }))
          } else {
            // 过期则清除
            localStorage.removeItem(STORAGE_KEY)
          }
        }
      } catch (error) {
        console.error('加载历史数据失败:', error)
        localStorage.removeItem(STORAGE_KEY)
      }
    }
    loadHistory()
  }, [])

  const saveToStorage = (data: any) => {
    try {
      const storageData: StorageData = {
        formData: data,
        savedAt: Date.now()
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(storageData))
    } catch (error) {
      console.error('保存数据失败:', error)
    }
  }

  const handleInputChange = (field: string, value: string | number | undefined) => {
    const newData = { ...formData, [field]: value }
    setFormData(newData)
    saveToStorage(newData)
  }

  const handleBlur = (field: string) => {
    setTouched(prev => ({ ...prev, [field]: true }))
  }

  const getFieldError = (field: string): string | null => {
    if (!touched[field]) return null
    switch (field) {
      case 'company_name':
        return !formData.company_name.trim() ? '请输入项目名称' : null
      case 'industry':
        return !formData.industry.trim() ? '请输入所属行业' : null
      case 'current_size':
        return !formData.current_size ? '请选择当前规模' : null
      case 'stage':
        return !formData.stage ? '请选择当前阶段' : null
      case 'selected_track':
        return !formData.selected_track.trim() ? '请输入细分赛道' : null
      case 'vision':
        return !formData.vision.trim() ? '请输入愿景' : null
      case 'mission':
        return !formData.mission.trim() ? '请输入使命' : null
      default:
        return null
    }
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

  const validateStep = (s: number): boolean => {
    switch (s) {
      case 1:
        if (!formData.company_name || !formData.industry || !formData.current_size || !formData.stage || !formData.selected_track) {
          toast.warning('请填写所有必填项')
          setTouched(prev => ({
            ...prev,
            company_name: true,
            industry: true,
            current_size: true,
            stage: true,
            selected_track: true
          }))
          return false
        }
        return true
      case 2:
        if (!formData.vision || !formData.mission) {
          toast.warning('请填写愿景和使命')
          setTouched(prev => ({ ...prev, vision: true, mission: true }))
          return false
        }
        return true
      case 3:
        if (!formData.values.some(v => v.trim())) {
          toast.warning('请至少填写一个价值观')
          return false
        }
        return true
      default:
        return true
    }
  }

  const handleNext = () => {
    if (validateStep(step)) {
      setStep(step + 1)
    }
  }

  const handlePrev = () => {
    setStep(Math.max(1, step - 1))
  }

  const handleSubmit = async () => {
    if (!validateStep(step)) return

    setLoading(true)
    try {
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

      const data = await sessionService.create(sessionData)

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

      navigate('/chat')
    } catch (error: any) {
      console.error('创建会话失败:', error)
      toast.error(`创建会话失败: ${error.message}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="init-page">
      <div className="init-container glass-card">
        <div className="init-header">
          <h1>VMV-SOP战略咨询系统</h1>
          <p>基于From VMV to SOP方法论，为企业提供专业的战略分析</p>
        </div>

        {/* 步骤指示器 */}
        <div className="step-indicator">
          <div className={`step-dot ${step >= 1 ? (step > 1 ? 'completed' : 'active') : ''}`}>{step > 1 ? '✓' : '1'}</div>
          <div className={`step-line ${step > 1 ? 'completed' : ''}`}></div>
          <div className={`step-dot ${step >= 2 ? (step > 2 ? 'completed' : 'active') : ''}`}>{step > 2 ? '✓' : '2'}</div>
          <div className={`step-line ${step > 2 ? 'completed' : ''}`}></div>
          <div className={`step-dot ${step >= 3 ? 'active' : ''}`}>3</div>
        </div>

        <div className="form-content">
          {step === 1 && (
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
                    className={`glass-input ${getFieldError('company_name') ? 'input-error' : ''}`}
                    placeholder="例如：智慧零售解决方案"
                    value={formData.company_name}
                    onChange={(e) => handleInputChange('company_name', e.target.value)}
                    onBlur={() => handleBlur('company_name')}
                  />
                  {getFieldError('company_name') && <div className="field-error">{getFieldError('company_name')}</div>}
                </div>

                <div className="form-group">
                  <label>所属行业 <span className="required">*</span></label>
                  <input
                    type="text"
                    className={`glass-input ${getFieldError('industry') ? 'input-error' : ''}`}
                    placeholder="例如：人工智能、互联网、金融科技"
                    value={formData.industry}
                    onChange={(e) => handleInputChange('industry', e.target.value)}
                    onBlur={() => handleBlur('industry')}
                  />
                  {getFieldError('industry') && <div className="field-error">{getFieldError('industry')}</div>}
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>当前规模 <span className="required">*</span></label>
                  <select
                    className={`glass-select ${getFieldError('current_size') ? 'input-error' : ''}`}
                    value={formData.current_size}
                    onChange={(e) => handleInputChange('current_size', e.target.value)}
                    onBlur={() => handleBlur('current_size')}
                  >
                    <option value="">请选择规模</option>
                    {teamSizes.map(size => (
                      <option key={size.value} value={size.value}>{size.label}</option>
                    ))}
                  </select>
                  {getFieldError('current_size') && <div className="field-error">{getFieldError('current_size')}</div>}
                </div>

                <div className="form-group">
                  <label>当前阶段 <span className="required">*</span></label>
                  <select
                    className={`glass-select ${getFieldError('stage') ? 'input-error' : ''}`}
                    value={formData.stage}
                    onChange={(e) => handleInputChange('stage', e.target.value)}
                    onBlur={() => handleBlur('stage')}
                  >
                    <option value="">请选择阶段</option>
                    {stages.map(s => (
                      <option key={s.value} value={s.value}>{s.label}</option>
                    ))}
                  </select>
                  {getFieldError('stage') && <div className="field-error">{getFieldError('stage')}</div>}
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
                  className={`glass-input ${getFieldError('selected_track') ? 'input-error' : ''}`}
                  placeholder="例如：国产平行游戏改编动画"
                  value={formData.selected_track}
                  onChange={(e) => handleInputChange('selected_track', e.target.value)}
                  onBlur={() => handleBlur('selected_track')}
                />
                {getFieldError('selected_track') && <div className="field-error">{getFieldError('selected_track')}</div>}
              </div>

              <div className="step-actions">
                <button className="glass-button primary-btn" onClick={handleNext}>
                  下一步：愿景与使命 →
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="form-section glass-card-dark">
              <div className="section-header">
                <span className="section-icon">🎯</span>
                <h2>愿景与使命</h2>
              </div>

              <div className="concept-card">
                <h4>💡 什么是愿景 (Vision)？</h4>
                <p>愿景是企业成功时的样貌，是创始人内心最真实的驱动力。它回答"我想成为什么"，不需要高大上，真实才是唯一标准。</p>
                <div className="concept-example">示例：成为中小团队能力放大的技术方案提供商</div>
              </div>

              <div className="form-group">
                <label>愿景 (Vision) <span className="required">*</span></label>
                <input
                  type="text"
                  className={`glass-input ${getFieldError('vision') ? 'input-error' : ''}`}
                  placeholder="例如：成为中小团队能力放大的技术方案提供商"
                  value={formData.vision}
                  onChange={(e) => handleInputChange('vision', e.target.value)}
                  onBlur={() => handleBlur('vision')}
                />
                {getFieldError('vision') && <div className="field-error">{getFieldError('vision')}</div>}
              </div>

              <div className="concept-card">
                <h4>💡 什么是使命 (Mission)？</h4>
                <p>使命是为了实现愿景，需要为谁创造什么价值。它是利他的，是决策的第一依据。当使命达成，愿景应大概率实现。</p>
                <div className="concept-example">示例：为中小微企业提供性价比高的数字化转型工具</div>
              </div>

              <div className="form-group">
                <label>使命 (Mission) <span className="required">*</span></label>
                <input
                  type="text"
                  className={`glass-input ${getFieldError('mission') ? 'input-error' : ''}`}
                  placeholder="例如：为中小微企业提供性价比高的数字化转型工具"
                  value={formData.mission}
                  onChange={(e) => handleInputChange('mission', e.target.value)}
                  onBlur={() => handleBlur('mission')}
                />
                {getFieldError('mission') && <div className="field-error">{getFieldError('mission')}</div>}
              </div>

              <div className="step-actions">
                <button className="glass-button" onClick={handlePrev}>← 上一步</button>
                <button className="glass-button primary-btn" onClick={handleNext}>下一步：价值观 →</button>
              </div>
            </div>
          )}

          {step === 3 && (
            <div className="form-section glass-card-dark">
              <div className="section-header">
                <span className="section-icon">⭐</span>
                <h2>价值观</h2>
              </div>

              <div className="concept-card">
                <h4>💡 什么是价值观 (Values)？</h4>
                <p>价值观是达成使命过程中的行动准则，是从创始团队已具备的特质中提炼出来的，不是凭空设计的。它不是道德观，而是对达成使命有帮助的元素。</p>
                <div className="concept-example">示例：客户至上、持续创新、极客精神、坦诚直接</div>
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

              <div className="step-actions">
                <button className="glass-button" onClick={handlePrev}>← 上一步</button>
                <button className="glass-button primary-btn" onClick={handleSubmit} disabled={loading}>
                  {loading ? '提交中...' : '完成初始化，进入对话'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default InitPage
