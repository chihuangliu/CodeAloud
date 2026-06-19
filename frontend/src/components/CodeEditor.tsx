import Editor from '@monaco-editor/react'
import type { ExecutionOutput } from '../hooks/useInterview'

interface Props {
  code: string
  onChange: (value: string) => void
  onRun: () => void
  executionOutput: ExecutionOutput | null
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
        <div className="border-t border-gray-700 bg-gray-900 p-3 max-h-48 overflow-auto">
          {executionOutput.stderr && (
            <pre className="text-sm text-red-400 font-mono whitespace-pre-wrap mb-2">
              {executionOutput.stderr}
            </pre>
          )}

          {executionOutput.test_case_results.length > 0 ? (
            <div>
              <p className="text-xs text-gray-500 mb-2">
                Test Cases: {' '}
                <span className={executionOutput.passed_count === executionOutput.total_count ? 'text-green-400' : 'text-red-400'}>
                  {executionOutput.passed_count}/{executionOutput.total_count} passed
                </span>
              </p>
              <div className="space-y-2">
                {executionOutput.test_case_results.map((tc, i) => (
                  <div key={i} className={`text-sm font-mono p-2 rounded ${tc.passed ? 'bg-green-900/30 border border-green-800' : 'bg-red-900/30 border border-red-800'}`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span>{tc.passed ? '✓' : '✗'}</span>
                      <span className="text-gray-400">Case {i + 1}</span>
                    </div>
                    <div className="text-xs text-gray-400">Input: <span className="text-gray-300">{tc.input}</span></div>
                    <div className="text-xs text-gray-400">Expected: <span className="text-gray-300">{tc.expected}</span></div>
                    {!tc.passed && (
                      <div className="text-xs text-gray-400">Got: <span className="text-red-300">{tc.actual || '(no output)'}</span></div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div>
              <p className="text-xs text-gray-500 mb-1">Output</p>
              <pre className="text-sm text-green-400 font-mono whitespace-pre-wrap">
                {executionOutput.stdout || '(no output)'}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
