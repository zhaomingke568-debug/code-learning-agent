import { create } from 'zustand'

export const useSessionStore = create((set) => ({
  sessionId: null,
  threadId: null,
  topic: null,
  depthLevel: '进阶',
  status: 'idle',
  createdAt: null,

  setSession: (session) => set({
    sessionId: session.sessionId,
    threadId: session.threadId,
    status: session.status || 'running',
    createdAt: session.createdAt
  }),

  setTopic: (topic) => set({ topic }),
  setDepthLevel: (level) => set({ depthLevel: level }),
  setStatus: (status) => set({ status }),

  reset: () => set({
    sessionId: null,
    threadId: null,
    topic: null,
    depthLevel: '进阶',
    status: 'idle',
    createdAt: null
  })
}))

export const useLearningStore = create((set) => ({
  currentMilestoneIndex: 0,
  learningPath: null,
  milestones: [],
  currentExplanation: null,
  currentExercise: null,
  userCode: null,
  codeExecutionResult: null,
  reviewResult: null,
  assessmentResult: null,
  reviewType: null,
  waitingForInput: null,
  inputPrompt: null,

  setLearningPath: (path) => set({
    learningPath: path,
    milestones: path?.milestones || []
  }),

  setCurrentMilestoneIndex: (index) => set({ currentMilestoneIndex: index }),
  setExplanation: (explanation) => set({ currentExplanation: explanation }),
  setExercise: (exercise) => set({ currentExercise: exercise }),
  setUserCode: (code) => set({ userCode: code }),
  setExecutionResult: (result) => set({ codeExecutionResult: result }),
  setReviewResult: (result) => set({ reviewResult: result }),
  setAssessmentResult: (result) => set({ assessmentResult: result }),
  setWaitingForInput: (type, prompt) => set({ waitingForInput: type, inputPrompt: prompt }),

  advanceMilestone: () => set((state) => ({
    currentMilestoneIndex: state.currentMilestoneIndex + 1
  })),

  reset: () => set({
    currentMilestoneIndex: 0,
    learningPath: null,
    milestones: [],
    currentExplanation: null,
    currentExercise: null,
    userCode: null,
    codeExecutionResult: null,
    reviewResult: null,
    assessmentResult: null,
    reviewType: null,
    waitingForInput: null,
    inputPrompt: null
  })
}))

export const useUIStore = create((set) => ({
  isLoading: false,
  error: null,

  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error: error }),
  clearError: () => set({ error: null })
}))