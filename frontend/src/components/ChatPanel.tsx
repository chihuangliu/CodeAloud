import { useEffect, useRef, useState, KeyboardEvent } from 'react'
import Markdown from 'react-markdown'
import type { Message } from '../hooks/useInterview'

interface Props {
  messages: Message[]
  isStreaming: boolean
  onSend: (content: string) => void
}

export function ChatPanel({ messages, isStreaming, onSend }: Props) {
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = () => {
    const text = input.trim()
    if (!text || isStreaming) return
    onSend(text)
    setInput('')
  }

  const handleKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-sm whitespace-pre-wrap'
                  : 'bg-gray-700 text-gray-100 rounded-bl-sm'
              } ${msg.streaming ? 'opacity-90' : ''}`}
            >
              {msg.role === 'user' ? (
                msg.content
              ) : (
                <Markdown
                  components={{
                    pre: ({ children }) => <pre className="bg-gray-900 rounded-md p-3 my-2 overflow-x-auto text-xs">{children}</pre>,
                    code: ({ children, className }) =>
                      className
                        ? <code className={className}>{children}</code>
                        : <code className="bg-gray-900 px-1.5 py-0.5 rounded text-xs">{children}</code>,
                    table: ({ children }) => <table className="border-collapse my-2 w-full text-xs">{children}</table>,
                    th: ({ children }) => <th className="border border-gray-600 px-2 py-1 text-left">{children}</th>,
                    td: ({ children }) => <td className="border border-gray-600 px-2 py-1">{children}</td>,
                    ol: ({ children }) => <ol className="list-decimal list-inside my-1 space-y-0.5">{children}</ol>,
                    ul: ({ children }) => <ul className="list-disc list-inside my-1 space-y-0.5">{children}</ul>,
                    blockquote: ({ children }) => <blockquote className="border-l-2 border-gray-500 pl-3 my-2 italic text-gray-300">{children}</blockquote>,
                    p: ({ children }) => <p className="my-1">{children}</p>,
                  }}
                >
                  {msg.content}
                </Markdown>
              )}
              {msg.streaming && <span className="inline-block w-1.5 h-3.5 ml-0.5 bg-current animate-pulse rounded-sm" />}
            </div>
          </div>
        ))}
        {messages.length === 0 && (
          <p className="text-center text-gray-500 text-sm mt-8">Starting interview...</p>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="border-t border-gray-700 p-3 flex gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          disabled={isStreaming}
          placeholder={isStreaming ? 'Alex is thinking...' : 'Type your message... (Enter to send)'}
          rows={2}
          className="flex-1 bg-gray-800 text-gray-100 rounded-lg px-3 py-2 text-sm resize-none outline-none focus:ring-1 focus:ring-blue-500 placeholder-gray-500 disabled:opacity-50"
        />
        <button
          onClick={send}
          disabled={isStreaming || !input.trim()}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white rounded-lg text-sm font-medium transition-colors self-end"
        >
          Send
        </button>
      </div>
    </div>
  )
}
