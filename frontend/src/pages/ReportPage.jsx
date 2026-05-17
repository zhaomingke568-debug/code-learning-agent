import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSessionStore, useLearningStore } from '../stores'
import { api } from '../api'

export default function ReportPage() {
  const navigate = useNavigate()
  const { threadId, topic } = useSessionStore()
  const { reset: resetLearning } = useLearningStore()
  const { reset: resetSession } = useSessionStore()

  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!threadId) {
      navigate('/')
      return
    }

    const fetchReport = async () => {
      try {
        const data = await api.getReport(threadId)
        setReport(data)
      } catch (err) {
        console.error('Failed to fetch report:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchReport()
  }, [threadId])

  const handleNewSession = () => {
    resetLearning()
    resetSession()
    navigate('/')
  }

  if (loading) return <div className="page">加载中...</div>

  return (
    <div className="page">
      <h2>📊 学习报告</h2>

      <div className="card">
        <h3>学习主题</h3>
        <p>{topic}</p>
        <p>目标级别: {report?.depthLevel}</p>
      </div>

      {report?.assessmentResult && (
        <div className="card">
          <h3>能力评估结果</h3>
          <p>级别: <strong>{report.assessmentResult.level}</strong></p>
          {report.assessmentResult.strengths?.length > 0 && (
            <p>强项: {report.assessmentResult.strengths.join(', ')}</p>
          )}
          {report.assessmentResult.weaknesses?.length > 0 && (
            <p>薄弱点: {report.assessmentResult.weaknesses.join(', ')}</p>
          )}
        </div>
      )}

      <div className="card">
        <h3>代码执行结果</h3>
        <p>状态: {report?.codeExecutionResult?.passed ? '✅ 通过' : '❌ 未通过'}</p>
        <p>摘要: {report?.codeExecutionResult?.summary || 'N/A'}</p>
      </div>

      {report?.weakPoints?.length > 0 && (
        <div className="card" style={{ background: '#fff3cd' }}>
          <h3>⚠️ 薄弱点</h3>
          <ul>
            {report.weakPoints.map((wp, i) => (
              <li key={i}>{wp}</li>
            ))}
          </ul>
        </div>
      )}

      {report?.strongPoints?.length > 0 && (
        <div className="card" style={{ background: '#d4edda' }}>
          <h3>✅ 强项</h3>
          <ul>
            {report.strongPoints.map((sp, i) => (
              <li key={i}>{sp}</li>
            ))}
          </ul>
        </div>
      )}

      <button
        className="btn btn-primary"
        onClick={handleNewSession}
        style={{ marginTop: '1.5rem' }}
      >
        开始新的学习会话
      </button>
    </div>
  )
}