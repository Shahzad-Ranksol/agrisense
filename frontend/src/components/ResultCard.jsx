import ReactMarkdown from 'react-markdown'

export default function ResultCard({ result, onClose }) {
  const pct = Math.round(result.confidence * 100)
  const top = result.scores?.[0]
  const confColor = pct >= 70 ? 'text-green-600' : pct >= 45 ? 'text-yellow-600' : 'text-red-500'

  return (
    <div className="absolute inset-0 bg-black/50 flex items-end justify-center z-50 animate-fade-in">
      <div className="bg-white w-full max-w-2xl mx-auto rounded-t-2xl shadow-2xl flex flex-col max-h-[85vh] animate-slide-up">

        {/* Header */}
        <div className="flex items-start justify-between px-5 pt-4 pb-3 border-b shrink-0">
          <div>
            <h2 className="text-lg font-bold text-green-700">Seasonal Planting Report</h2>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-0.5 mt-1 text-xs text-gray-500">
              <span>
                Confidence:{' '}
                <span className={`font-semibold ${confColor}`}>{pct}%</span>
              </span>
              {top && (
                <span>
                  Top crop: <span className="font-semibold text-gray-700">{top.crop}</span>
                </span>
              )}
              <span>{result.weather?.season}</span>
              <span>{result.weather?.avg_temp_c}°C · {result.weather?.forecasted_rainfall_mm}mm rain</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="ml-4 text-gray-400 hover:text-gray-700 text-2xl leading-none shrink-0"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        {/* Soil + crop scores quick-glance bar */}
        <div className="flex gap-4 px-5 py-2.5 bg-gray-50 border-b text-xs text-gray-600 overflow-x-auto shrink-0">
          <span>N <strong>{result.soil?.N} g/kg</strong></span>
          <span>P <strong>{result.soil?.P} mg/kg</strong></span>
          <span>K <strong>{result.soil?.K} mg/kg</strong></span>
          <span>pH <strong>{result.soil?.pH}</strong></span>
          <span className="ml-auto shrink-0">
            {result.scores?.slice(0, 3).map((s) => (
              <span key={s.crop} className="mr-3">
                {s.crop} <strong className="text-green-600">{Math.round(s.score * 100)}pts</strong>
              </span>
            ))}
          </span>
        </div>

        {/* Scrollable Markdown report */}
        <div className="overflow-y-auto px-5 py-4 prose prose-sm max-w-none text-gray-800 flex-1">
          <ReactMarkdown>{result.report}</ReactMarkdown>
        </div>

        {/* Footer close */}
        <div className="px-5 py-3 border-t shrink-0 flex justify-end">
          <button
            onClick={onClose}
            className="text-sm text-gray-500 hover:text-gray-700 font-medium"
          >
            Close Report
          </button>
        </div>
      </div>
    </div>
  )
}
