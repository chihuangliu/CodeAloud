import { useState, useEffect } from 'react'
import { useInterview } from './hooks/useInterview'
import { InterviewSession } from './components/InterviewSession'
import { EvalReport } from './components/EvalReport'

interface Question {
  id: string
  title: string
  difficulty: string
  tags: string[]
}

const DIFFICULTY_COLOR: Record<string, string> = {
  easy: 'text-green-400',
  medium: 'text-yellow-400',
  hard: 'text-red-400',
}

function Lobby({ onStart }: { onStart: (id: string) => void }) {
  const [questions, setQuestions] = useState<Question[]>([])
  const [filter, setFilter] = useState<string>('all')

  useEffect(() => {
    fetch('/api/questions').then((r) => r.json()).then(setQuestions)
  }, [])

  const filtered = filter === 'all' ? questions : questions.filter((q) => q.difficulty === filter)

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-white mb-1">CodeAloud</h1>
        <p className="text-gray-400 mb-8">Practice coding interviews with a conversational AI interviewer</p>

        <div className="flex gap-2 mb-6">
          {['all', 'easy', 'medium', 'hard'].map((d) => (
            <button
              key={d}
              onClick={() => setFilter(d)}
              className={`px-4 py-1.5 rounded-full text-sm capitalize transition-colors ${
                filter === d
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              {d}
            </button>
          ))}
        </div>

        <div className="space-y-2">
          {filtered.map((q) => (
            <button
              key={q.id}
              onClick={() => onStart(q.id)}
              className="w-full flex items-center justify-between px-5 py-4 bg-gray-800 hover:bg-gray-700 rounded-xl transition-colors text-left"
            >
              <div>
                <span className="text-white font-medium">{q.title}</span>
                <div className="flex gap-2 mt-1">
                  {q.tags.slice(0, 3).map((t) => (
                    <span key={t} className="text-xs text-gray-500 bg-gray-700 px-2 py-0.5 rounded">
                      {t}
                    </span>
                  ))}
                </div>
              </div>
              <span className={`text-sm font-medium capitalize ${DIFFICULTY_COLOR[q.difficulty] ?? 'text-gray-400'}`}>
                {q.difficulty}
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const {
    phase, messages, code, setCode, executionOutput,
    evalReport, isStreaming, formatTimer,
    startInterview, sendMessage, runCode, endInterview,
  } = useInterview()

  if (phase === 'lobby') return <Lobby onStart={startInterview} />

  if (phase === 'eval' && evalReport) {
    return <EvalReport report={evalReport} onRestart={() => window.location.reload()} />
  }

  return (
    <InterviewSession
      messages={messages}
      code={code}
      executionOutput={executionOutput}
      isStreaming={isStreaming}
      timer={formatTimer()}
      onCodeChange={setCode}
      onRun={runCode}
      onSend={sendMessage}
      onEnd={endInterview}
    />
  )
}
