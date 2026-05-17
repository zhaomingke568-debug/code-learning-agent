import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSessionStore, useLearningStore } from '../stores'
import { api } from '../api'

export default function AssessmentPage() {
  const navigate = useNavigate()
  const { threadId, topic } = useSessionStore()
  const { setAssessmentResult, setLearningPath } = useLearningStore()

  const [questions, setQuestions] = useState([])
  const [answers, setAnswers] = useState({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!threadId) {
      navigate('/')
      return
    }
    // In real implementation, fetch questions from API
    // For now, mock questions
    setQuestions([
      {
        questionId: 'q1',
        question: '关于 ' + topic + '，你之前有过相关学习或实践经验吗？',
        options: ['A. 完全没接触过', 'B. 看过一些基础概念', 'C. 有过实际项目经验', 'D. 非常熟悉']
      }
    ])
    setLoading(false)
  }, [threadId, topic])

  const handleAnswer = (questionId, answer) => {
    setAnswers(prev => ({ ...prev, [questionId]: answer }))
  }

  const handleSubmit = async () => {
    if (Object.keys(answers).length < questions.length) {
      alert('请回答所有问题')
      return
    }

    setSubmitting(true)
    try {
      const answerList = Object.entries(answers).map(([questionId, answer]) => ({
        questionId,
        answer
      }))

      const result = await api.submitAssessment(threadId, answerList)
      setAssessmentResult(result.assessmentResult)
      setLearningPath(result.learningPath)
      navigate('/dashboard')
    } catch (err) {
      alert('提交失败: ' + err.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="page">加载中...</div>

  return (
    <div className="page">
      <h2>能力评估</h2>
      <p>请回答以下问题，帮助我们了解你的 {topic} 水平。</p>

      {questions.map((q, i) => (
        <div key={q.questionId} className="card" style={{ marginTop: '1rem' }}>
          <p><strong>Q{i + 1}. {q.question}</strong></p>
          {q.options.map((opt, j) => (
            <label key={j} style={{ display: 'block', margin: '0.5rem 0' }}>
              <input
                type="radio"
                name={q.questionId}
                value={opt[0]}
                checked={answers[q.questionId] === opt[0]}
                onChange={() => handleAnswer(q.questionId, opt[0])}
              />
              {opt}
            </label>
          ))}
        </div>
      ))}

      <button
        className="btn btn-primary"
        onClick={handleSubmit}
        disabled={submitting}
        style={{ marginTop: '1.5rem' }}
      >
        {submitting ? '提交中...' : '提交评估'}
      </button>
    </div>
  )
}