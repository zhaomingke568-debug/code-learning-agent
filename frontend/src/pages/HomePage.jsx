import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSessionStore } from '../stores'
import { api } from '../api'

export default function HomePage() {
  const navigate = useNavigate()
  const { setSession, setTopic, setDepthLevel, threadId, setStatus } = useSessionStore()

  const [topicInput, setTopicInput] = useState('')
  const [depthLevel, setDepthLevelLocal] = useState('进阶')
  const [recoverId, setRecoverId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleStart = async () => {
    if (!topicInput.trim()) {
      setError('请输入学习主题')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const session = await api.startSession(topicInput, depthLevel)
      setSession(session)
      setTopic(topicInput)
      setDepthLevel(depthLevel)
      setStatus('running')
      navigate('/assessment')
    } catch (err) {
      setError('启动会话失败: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRecover = async () => {
    if (!recoverId.trim()) {
      setError('请输入会话 ID')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const result = await api.recoverSession(recoverId)
      setSession({ sessionId: result.state.sessionId, threadId: recoverId, status: 'running' })
      setTopic(result.state.topic)
      setDepthLevel(result.state.depthLevel)
      setStatus('running')
      navigate('/dashboard')
    } catch (err) {
      setError('恢复会话失败: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <h2>Welcome to Coding Learning Agent</h2>

      {error && <div className="error" style={{ color: 'red', marginBottom: '1rem' }}>{error}</div>}

      <div className="form-group">
        <label>学习主题</label>
        <input
          type="text"
          placeholder="例如: Python装饰器, FastAPI路由设计"
          value={topicInput}
          onChange={e => setTopicInput(e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>目标级别</label>
        <select value={depthLevel} onChange={e => setDepthLevelLocal(e.target.value)}>
          <option value="入门">入门</option>
          <option value="进阶">进阶</option>
          <option value="专家">专家</option>
        </select>
      </div>

      <button className="btn btn-primary" onClick={handleStart} disabled={loading}>
        {loading ? '启动中...' : '开始学习'}
      </button>

      <hr style={{ margin: '2rem 0' }} />

      <h3>恢复已有会话</h3>
      <div className="form-group">
        <label>会话 ID (Thread ID)</label>
        <input
          type="text"
          placeholder="输入 Thread ID"
          value={recoverId}
          onChange={e => setRecoverId(e.target.value)}
        />
      </div>
      <button className="btn btn-secondary" onClick={handleRecover} disabled={loading}>
        恢复会话
      </button>
    </div>
  )
}