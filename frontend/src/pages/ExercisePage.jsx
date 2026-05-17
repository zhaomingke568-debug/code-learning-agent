import React, { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Editor from '@monaco-editor/react'
import { useSessionStore, useLearningStore } from '../stores'
import { api } from '../api'

export default function ExercisePage() {
  const navigate = useNavigate()
  const params = useParams()
  const milestoneIndex = parseInt(params.milestoneIndex || '0')

  const { threadId } = useSessionStore()
  const { setExplanation, setExercise, currentExercise, setExecutionResult, advanceMilestone } = useLearningStore()

  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [showHints, setShowHints] = useState(false)
  const [executionResult, setLocalResult] = useState(null)

  useEffect(() => {
    if (!threadId) {
      navigate('/')
      return
    }

    const fetchData = async () => {
      try {
        // Fetch explanation and exercise
        const explanation = await api.getExplanation(threadId)
        setExplanation(explanation.explanation)

        try {
          const exercise = await api.getExercise(threadId)
          setExercise(exercise)
          setCode(exercise.starterCode || '')
        } catch (err) {
          console.error('No exercise available yet:', err)
        }
      } catch (err) {
        console.error('Failed to fetch:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [threadId, milestoneIndex])

  const handleSubmit = async () => {
    setSubmitting(true)
    try {
      const result = await api.submitCode(threadId, code)
      setLocalResult(result)
      setExecutionResult(result)
    } catch (err) {
      alert('提交失败: ' + err.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleContinue = () => {
    advanceMilestone()
    navigate('/feedback')
  }

  if (loading) return <div className="page">加载中...</div>

  return (
    <div className="page">
      <h2>练习</h2>

      {currentExercise && (
        <div className="card">
          <h3>{currentExercise.title}</h3>
          <p>{currentExercise.description}</p>
          <p>难度: {currentExercise.difficulty}</p>
        </div>
      )}

      <div style={{ margin: '1.5rem 0' }}>
        <label>代码编辑器</label>
        <div style={{ height: '300px', border: '1px solid #ddd', borderRadius: '4px' }}>
          <Editor
            height="300px"
            language="python"
            value={code}
            onChange={value => setCode(value || '')}
            theme="vs-dark"
          />
        </div>
      </div>

      {currentExercise?.hints?.length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <button
            className="btn btn-secondary"
            onClick={() => setShowHints(!showHints)}
          >
            {showHints ? '隐藏提示' : '显示提示'}
          </button>
          {showHints && (
            <ul style={{ marginTop: '0.5rem', paddingLeft: '1.5rem' }}>
              {currentExercise.hints.map((hint, i) => (
                <li key={i}>{hint}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <button
        className="btn btn-primary"
        onClick={handleSubmit}
        disabled={submitting}
      >
        {submitting ? '执行中...' : '提交代码'}
      </button>

      {executionResult && (
        <div className="card" style={{ marginTop: '1.5rem', background: executionResult.passed ? '#d4edda' : '#f8d7da' }}>
          <h3>执行结果</h3>
          <p>状态: {executionResult.passed ? '✅ 通过' : '❌ 未通过'}</p>
          <p>输出: {executionResult.output}</p>
          {executionResult.errorMessage && (
            <p style={{ color: 'red' }}>错误: {executionResult.errorMessage}</p>
          )}
          {executionResult.fixSuggestions && (
            <div style={{ marginTop: '0.5rem', padding: '0.75rem', background: '#fff3cd', borderRadius: '4px' }}>
              <strong>💡 修复建议:</strong> {executionResult.fixSuggestions}
            </div>
          )}
        </div>
      )}

      {executionResult?.passed && (
        <button
          className="btn btn-success"
          onClick={handleContinue}
          style={{ marginTop: '1rem' }}
        >
          继续下一步
        </button>
      )}
    </div>
  )
}