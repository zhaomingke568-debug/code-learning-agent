import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useSessionStore, useLearningStore, useUIStore } from './stores'
import HomePage from './pages/HomePage'
import AssessmentPage from './pages/AssessmentPage'
import DashboardPage from './pages/DashboardPage'
import ExercisePage from './pages/ExercisePage'
import FeedbackPage from './pages/FeedbackPage'
import ReportPage from './pages/ReportPage'
import './App.css'

function App() {
  const threadId = useSessionStore(s => s.threadId)

  return (
    <BrowserRouter>
      <div className="app">
        <header className="app-header">
          <h1>Coding Learning Agent</h1>
          {threadId && <span className="thread-id">Thread: {threadId.slice(0, 8)}...</span>}
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/assessment" element={<AssessmentPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/learn/:milestoneIndex" element={<ExercisePage />} />
            <Route path="/exercise" element={<ExercisePage />} />
            <Route path="/feedback" element={<FeedbackPage />} />
            <Route path="/report" element={<ReportPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App