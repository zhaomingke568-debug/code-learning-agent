import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSessionStore, useLearningStore } from '../stores'
import { api } from '../api'

export default function DashboardPage() {
  const navigate = useNavigate()
  const { threadId, topic } = useSessionStore()
  const { learningPath, milestones, currentMilestoneIndex, setLearningPath } = useLearningStore()

  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!threadId) {
      navigate('/')
      return
    }

    const fetchData = async () => {
      try {
        const path = await api.getLearningPath(threadId)
        setLearningPath(path)
      } catch (err) {
        console.error('Failed to fetch learning path:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [threadId])

  const handleStartLearning = () => {
    navigate('/learn/0')
  }

  if (loading) return <div className="page">加载中...</div>

  return (
    <div className="page">
      <h2>学习面板</h2>
      <p>主题: <strong>{topic}</strong></p>

      {learningPath && (
        <div className="card" style={{ marginTop: '1rem' }}>
          <h3>学习路径</h3>
          <p>共 {milestones.length} 个里程碑</p>

          <div style={{ marginTop: '1rem' }}>
            {milestones.map((m, i) => (
              <div
                key={i}
                style={{
                  padding: '0.75rem',
                  margin: '0.5rem 0',
                  background: i < currentMilestoneIndex ? '#d4edda' : i === currentMilestoneIndex ? '#fff3cd' : '#f8f9fa',
                  borderRadius: '4px',
                  borderLeft: `4px solid ${i < currentMilestoneIndex ? '#28a745' : i === currentMilestoneIndex ? '#ffc107' : '#ddd'}`
                }}
              >
                <strong>{i + 1}. {m.topic}</strong>
                <p style={{ margin: '0.25rem 0 0 0', color: '#666', fontSize: '0.9rem' }}>{m.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        className="btn btn-primary"
        onClick={handleStartLearning}
        style={{ marginTop: '1.5rem' }}
      >
        开始学习第 {currentMilestoneIndex + 1} 个里程碑
      </button>
    </div>
  )
}