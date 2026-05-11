export default function ProgressHUD({ steps, isAnalyzing, streamingText }) {
  const isStreaming = isAnalyzing && streamingText.length > 0

  return (
    <div className="absolute top-4 left-4 bg-black/85 text-green-400 rounded-xl p-4 font-mono text-sm max-w-xs shadow-2xl backdrop-blur flex flex-col gap-2">

      {/* Status dot + label */}
      <div className="flex items-center gap-2">
        {isAnalyzing && (
          <span className="relative flex h-2.5 w-2.5 shrink-0">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
          </span>
        )}
        <span className="text-white font-semibold text-xs uppercase tracking-wider">
          {isAnalyzing ? 'Analysing…' : 'Complete'}
        </span>
      </div>

      {/* Step log */}
      <ul className="space-y-1">
        {steps.map((msg, i) => (
          <li key={i} className="flex items-start gap-2 text-xs leading-snug">
            <span className="text-green-500 mt-0.5 shrink-0">✓</span>
            <span className="text-green-300">{msg}</span>
          </li>
        ))}
      </ul>

      {/* Live Claude streaming preview */}
      {isStreaming && (
        <div className="mt-1 border-t border-white/10 pt-2">
          <p className="text-white/50 text-xs mb-1">Claude is writing…</p>
          <p className="text-green-200 text-xs leading-snug line-clamp-4 whitespace-pre-wrap">
            {streamingText}
            <span className="animate-pulse">▍</span>
          </p>
        </div>
      )}
    </div>
  )
}
