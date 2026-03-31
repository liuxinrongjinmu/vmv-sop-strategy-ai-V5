import { create } from 'zustand'
import { SessionDetail } from '../types/session'
import { MessageResponse } from '../types/message'

interface AppState {
  sessionId: string | null
  sessionInfo: SessionDetail | null
  messages: MessageResponse[]
  currentStage: number
  isLoading: boolean
  
  setSessionId: (id: string) => void
  setSessionInfo: (info: SessionDetail) => void
  setMessages: (messages: MessageResponse[]) => void
  addMessage: (message: MessageResponse) => void
  setCurrentStage: (stage: number) => void
  setIsLoading: (loading: boolean) => void
  reset: () => void
}

export const useAppStore = create<AppState>((set) => ({
  sessionId: null,
  sessionInfo: null,
  messages: [],
  currentStage: 1,
  isLoading: false,
  
  setSessionId: (id) => set({ sessionId: id }),
  setSessionInfo: (info) => set({ sessionInfo: info, currentStage: info.current_stage }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setCurrentStage: (stage) => set({ currentStage: stage }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  reset: () => set({
    sessionId: null,
    sessionInfo: null,
    messages: [],
    currentStage: 1,
    isLoading: false
  })
}))
