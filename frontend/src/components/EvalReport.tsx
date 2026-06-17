import type { EvalReport as Report } from '../hooks/useInterview'

interface Props {
  report: Report
  onRestart: () => void
}

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 8 ? 'bg-green-600' : score >= 5 ? 'bg-yellow-600' : 'bg-red-600'
  return (
    <span className={`${color} text-white text-lg font-bold px-3 py-1 rounded-lg`}>
      {score}/10
    </span>
  )
}

export function EvalReport({ report, onRestart }: Props) {
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-6">
      <div className="bg-gray-800 rounded-2xl p-8 max-w-xl w-full space-y-6">
        <h1 className="text-2xl font-bold text-white">Interview Complete</h1>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-700 rounded-xl p-4">
            <p className="text-gray-400 text-xs mb-1">Time Complexity</p>
            <p className="text-white font-mono text-lg">{report.time_complexity}</p>
          </div>
          <div className="bg-gray-700 rounded-xl p-4">
            <p className="text-gray-400 text-xs mb-1">Space Complexity</p>
            <p className="text-white font-mono text-lg">{report.space_complexity}</p>
          </div>
        </div>

        <div className="flex gap-6">
          <div>
            <p className="text-gray-400 text-sm mb-2">Communication</p>
            <ScoreBadge score={report.communication_score} />
          </div>
          <div>
            <p className="text-gray-400 text-sm mb-2">Approach</p>
            <ScoreBadge score={report.approach_score} />
          </div>
        </div>

        {report.improvements.length > 0 && (
          <div>
            <p className="text-gray-400 text-sm mb-2">Improvement Areas</p>
            <ul className="space-y-1">
              {report.improvements.map((item, i) => (
                <li key={i} className="flex gap-2 text-sm text-gray-200">
                  <span className="text-yellow-400 mt-0.5">•</span>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

        {report.follow_up_quality && (
          <div className="bg-gray-700 rounded-xl p-4">
            <p className="text-gray-400 text-xs mb-1">Follow-up Response</p>
            <p className="text-gray-200 text-sm">{report.follow_up_quality}</p>
          </div>
        )}

        <button
          onClick={onRestart}
          className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-colors"
        >
          Start New Interview
        </button>
      </div>
    </div>
  )
}
