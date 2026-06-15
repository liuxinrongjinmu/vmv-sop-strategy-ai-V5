import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import { SessionDetail } from '../types/session'
import { MessageResponse } from '../types/message'

interface AppState {
  sessionId: string | null
  sessionInfo: SessionDetail | null
  messages: MessageResponse[]
  currentStage: number
  isLoading: boolean
  isStreaming: boolean

  setSessionId: (id: string) => void
  setSessionInfo: (info: SessionDetail) => void
  setMessages: (messages: MessageResponse[]) => void
  addMessage: (message: MessageResponse) => void
  updateLastAssistantMessage: (content: string) => void
  updateLastAssistantMetadata: (metadata: Record<string, unknown>) => void
  setCurrentStage: (stage: number) => void
  setIsLoading: (loading: boolean) => void
  setIsStreaming: (streaming: boolean) => void
  reset: () => void
}

/**
 * 自定义 localStorage 实现，包含溢出保护
 * 当 localStorage 写入失败时，自动裁剪旧消息
 */
const safeStorage = {
  getItem: (name: string): string | null => {
    try {
      return localStorage.getItem(name)
    } catch {
      return null
    }
  },
  setItem: (name: string, value: string): void => {
    try {
      localStorage.setItem(name, value)
    } catch {
      // localStorage 溢出，清理旧消息
      console.warn('localStorage overflow, cleaning old messages')
      try {
        const data = JSON.parse(value)
        // 只保留最近50条消息
        if (data?.state?.messages && Array.isArray(data.state.messages)) {
          data.state.messages = data.state.messages.slice(-50)
        }
        localStorage.setItem(name, JSON.stringify(data))
      } catch {
        // 最终兜底：清除所有持久化数据
        localStorage.removeItem(name)
      }
    }
  },
  removeItem: (name: string): void => {
    localStorage.removeItem(name)
  }
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      sessionId: null,
      sessionInfo: null,
      messages: [],
      currentStage: 1,
      isLoading: false,
      isStreaming: false,

      setSessionId: (id) => set({ sessionId: id }),
      setSessionInfo: (info) => set({ sessionInfo: info, currentStage: info.current_stage }),
      setMessages: (messages) => set({ messages }),
      addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
      updateLastAssistantMessage: (content) => set((state) => {
        const msgs = [...state.messages]
        for (let i = msgs.length - 1; i >= 0; i--) {
          if (msgs[i].role === 'assistant') {
            msgs[i] = { ...msgs[i], content }
            break
          }
        }
        return { messages: msgs }
      }),
      updateLastAssistantMetadata: (metadata) => set((state) => {
        const msgs = [...state.messages]
        for (let i = msgs.length - 1; i >= 0; i--) {
          if (msgs[i].role === 'assistant') {
            msgs[i] = { ...msgs[i], metadata: { ...msgs[i].metadata, ...metadata } as any }
            break
          }
        }
        return { messages: msgs }
      }),
      setCurrentStage: (stage) => set({ currentStage: stage }),
      setIsLoading: (loading) => set({ isLoading: loading }),
      setIsStreaming: (streaming) => set({ isStreaming: streaming }),
      reset: () => set({
        sessionId: null,
        sessionInfo: null,
        messages: [],
        currentStage: 1,
        isLoading: false,
        isStreaming: false
      })
    }),
    {
      name: 'vmv-sop-storage',
      storage: createJSONStorage(() => safeStorage),
      partialize: (state) => ({
        sessionId: state.sessionId,
        sessionInfo: state.sessionInfo,
        currentStage: state.currentStage,
        messages: state.messages
      }),
      onRehydrateStorage: () => (state) => {
        // rehydrate后确保isLoading和isStreaming为false
        if (state) {
          state.isLoading = false
          state.isStreaming = false
        }
      }
    }
  )
)
