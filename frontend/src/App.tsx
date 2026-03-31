import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import InitPage from './pages/InitPage'
import ChatPage from './pages/ChatPage'
import './styles/glassmorphism.css'

const App: React.FC = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<InitPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  )
}

export default App
