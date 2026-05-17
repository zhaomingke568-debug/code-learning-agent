import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSessionStore, useLearningStore } from '../stores'
import { api } from '../api'

export default function FeedbackPage() {
  const navigate = useNavigate()
  const { threadId } = useSessionStore()
  const { currentMilestoneIndex, milestones } = useLearningStore()

  const [submitting, setSubmitting] = useState(false)

  const hasNext = currentMilestoneIndex + 1 < milestones.length

  const handleFeedback = async (feedback) => {
    setSubmitting(true)
    try {
      const result = await api.submitFeedback(threadId, feedback)

      if (feedback === 'end' || !hasNext) {
        navigate('/report')
      } else if (feedback === 'continue') {
        navigate('/learn', { replace: true })
      } else if (feedback === 'relearn') {
        navigate('/assessment', { replace: true })
      } else if (feedback === 'adjust_path') {
        navigate('/dashboard', { replace: true })
      }
    } catch (err) {
      alert('提交反馈失败: ' + err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page">
      <h2>学习反馈</h2>

      <p>已完成第 {currentMilestoneIndex + 1} 个里程碑的学习。</p>

      <div className="card" style={{ marginTop: '1.5rem' }}>
        <h3>接下来你想做什么？</h3>

        <button
          className="btn btn-primary"
          onClick={() => handleFeedback('continue')}
          disabled={submitting || !hasNext}
          style={{ marginRight: '1rem', marginTop: '0.5rem' }}
        >
          继续下一个里程碑
        </button>

        <button
          className="btn btn-secondary"
          onClick={() => handleFeedback('relearn')}
          disabled={submitting}
          style={{ marginRight: '1rem', marginTop: '0.5rem' }}
        >
          重新评估
        </button>

        <button
          className="btn btn-secondary"
          onClick={() => handleFeedback('adjust_path')}
          disabled={submitting}
          style={{ marginRight: '1rem', marginTop: '0.5rem' }}
        >
          调整学习路径
        </button>

        <button
          className="btn btn-secondary"
          onClick={() => handleFeedback('end')}
          disabled={submitting}
          style={{ marginTop: '0.5rem' }}
        >
          结束学习
        </button>
      </div>

      {submitting && <p style={{ marginTop: '1rem' }}>提交中...</p>}
    </div>
  )
}