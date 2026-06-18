import { CodeEditor } from './CodeEditor'
import { ChatPanel } from './ChatPanel'
import type { Message } from '../hooks/useInterview'

interface Props {
  messages: Message[]
  code: string
  executionOutput: string | null
  isStreaming: boolean
  timer: string
  onCodeChange: (code: string) => void
  onRun: () => void
  onSend: (content: string) => void
  onEnd: () => void
}

export function InterviewSession({
  messages, code, executionOutput, isStreaming, timer,
  onCodeChange, onRun, onSend, onEnd,
}: Props) {
  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="flex items-center justify-between px-5 py-3 bg-gray-800 border-b border-gray-700 shrink-0">
        <div className="flex items-center gap-3">
          <span className="text-blue-400 font-bold text-lg">CodeAloud</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="font-mono text-gray-300">{timer}</span>
          <button
            onClick={onEnd}
            className="px-4 py-1.5 bg-red-700 hover:bg-red-600 text-white text-sm rounded-lg transition-colors"
          >
            End Interview
          </button>
        </div>
      </header>

      {/* Main split pane */}
      <div className="flex flex-1 min-h-0">
        {/* Left: code editor */}
        <div className="flex-1 min-w-0 border-r border-gray-700">
          <CodeEditor
            code={code}
            onChange={onCodeChange}
            onRun={onRun}
            executionOutput={executionOutput}
          />
        </div>

        {/* Right: chat */}
        <div className="w-[400px] shrink-0">
          <ChatPanel messages={messages} isStreaming={isStreaming} onSend={onSend} />
        </div>
      </div>
    </div>
  )
}
