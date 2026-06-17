import Editor from '@monaco-editor/react'

interface Props {
  code: string
  onChange: (value: string) => void
  onRun: () => void
  executionOutput: string | null
  language?: string
}

export function CodeEditor({ code, onChange, onRun, executionOutput, language = 'python' }: Props) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-3 py-2 bg-gray-800 border-b border-gray-700">
        <span className="text-sm text-gray-400 font-mono">{language}</span>
        <button
          onClick={onRun}
          className="px-4 py-1.5 bg-green-600 hover:bg-green-500 text-white text-sm rounded font-medium transition-colors"
        >
          Run Code
        </button>
      </div>

      <div className="flex-1 min-h-0">
        <Editor
          height="100%"
          language={language}
          value={code}
          onChange={(v) => onChange(v ?? '')}
          theme="vs-dark"
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            tabSize: 4,
          }}
        />
      </div>

      {executionOutput !== null && (
        <div className="border-t border-gray-700 bg-gray-900 p-3 max-h-36 overflow-auto">
          <p className="text-xs text-gray-500 mb-1">Output</p>
          <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap">
            {executionOutput || '(no output)'}
          </pre>
        </div>
      )}
    </div>
  )
}
