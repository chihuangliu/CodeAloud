import { useState, useRef, useCallback, useEffect } from 'react'

export interface Message {
  role: 'user' | 'assistant'
  content: string
  streaming?: boolean
}

export interface EvalReport {
  time_complexity: string
  space_complexity: string
  communication_score: number
  approach_score: number
  improvements: string[]
  follow_up_quality: string | null
}

type Phase = 'lobby' | 'interview' | 'eval'

const API = '/api'

export function useInterview() {
  const [phase, setPhase] = useState<Phase>('lobby')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [code, setCode] = useState('# Write your solution here\n')
  const [executionOutput, setExecutionOutput] = useState<string | null>(null)
  const [evalReport, setEvalReport] = useState<EvalReport | null>(null)
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [isStreaming, setIsStreaming] = useState(false)

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const startTimer = useCallback(() => {
    timerRef.current = setInterval(() => setElapsedSeconds((s) => s + 1), 1000)
  }, [])

  const stopTimer = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current)
  }, [])

  useEffect(() => () => stopTimer(), [stopTimer])

  const appendStreaming = useCallback((chunk: string) => {
    setMessages((prev) => {
      const last = prev[prev.length - 1]
      if (last?.streaming) {
        return [...prev.slice(0, -1), { ...last, content: last.content + chunk }]
      }
      return [...prev, { role: 'assistant', content: chunk, streaming: true }]
    })
  }, [])

  const finaliseStreaming = useCallback(() => {
    setMessages((prev) =>
      prev.map((m, i) => (i === prev.length - 1 ? { ...m, streaming: false } : m))
    )
    setIsStreaming(false)
  }, [])

  const startInterview = useCallback(async (questionId: string) => {
    setIsStreaming(true)
    setPhase('interview')
    startTimer()

    const res = await fetch(`${API}/interview/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question_id: questionId }),
    })

    const reader = res.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let sid = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        buffer += decoder.decode()
      } else {
        buffer += decoder.decode(value, { stream: true })
      }
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const raw = line.slice(6).trim()
        if (!raw) continue
        const parsed = JSON.parse(raw)
        if (parsed.text) appendStreaming(parsed.text)
        if (parsed.done) {
          sid = parsed.session_id
          finaliseStreaming()
        }
      }
      if (done) break
    }

    setSessionId(sid)
  }, [appendStreaming, finaliseStreaming, startTimer])

  const sendMessage = useCallback(async (content: string, injectCode = false) => {
    if (!sessionId || isStreaming) return
    setMessages((prev) => [...prev, { role: 'user', content }])
    setIsStreaming(true)

    const res = await fetch(`${API}/interview/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, content, inject_code: injectCode }),
    })

    const reader = res.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        buffer += decoder.decode()
      } else {
        buffer += decoder.decode(value, { stream: true })
      }
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const raw = line.slice(6).trim()
        if (!raw) continue
        const parsed = JSON.parse(raw)
        if (parsed.text) appendStreaming(parsed.text)
        if (parsed.done) finaliseStreaming()
      }
      if (done) break
    }
  }, [sessionId, isStreaming, appendStreaming, finaliseStreaming])

  const runCode = useCallback(async () => {
    if (!sessionId) {
      setExecutionOutput('[Error: no session — start an interview first]')
      return
    }
    setExecutionOutput('Running...')
    try {
      const res = await fetch(`${API}/code/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, code, language: 'python' }),
      })
      const data = await res.json()
      if (!res.ok) {
        setExecutionOutput(`[Error: ${data.detail ?? res.statusText}]`)
        return
      }
      const output = data.stdout || data.stderr || `[${data.status}]`
      setExecutionOutput(output)
      await sendMessage("I just ran my code.", true)
    } catch (err) {
      setExecutionOutput(`[Error: ${err instanceof Error ? err.message : 'unknown'}]`)
    }
  }, [sessionId, code, sendMessage])

  const endInterview = useCallback(async () => {
    if (!sessionId) return
    stopTimer()
    setPhase('eval')
    const res = await fetch(`${API}/interview/end`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId, content: 'End interview' }),
    })
    const report = await res.json()
    setEvalReport(report)
  }, [sessionId, stopTimer])

  const formatTimer = useCallback(() => {
    const m = Math.floor(elapsedSeconds / 60).toString().padStart(2, '0')
    const s = (elapsedSeconds % 60).toString().padStart(2, '0')
    return `${m}:${s}`
  }, [elapsedSeconds])

  return {
    phase, messages, code, setCode, executionOutput,
    evalReport, isStreaming, formatTimer,
    startInterview, sendMessage, runCode, endInterview,
  }
}
