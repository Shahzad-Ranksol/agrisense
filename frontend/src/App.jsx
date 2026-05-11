import { useState, useCallback, useRef } from 'react'
import Map, { Marker } from 'react-map-gl'
import 'mapbox-gl/dist/mapbox-gl.css'
import ProgressHUD from './components/ProgressHUD'
import ResultCard from './components/ResultCard'
import CoordInput from './components/CoordInput'

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN
// In dev: empty string → Vite proxy handles /api
// In prod: set VITE_API_BASE_URL to your Railway backend URL
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

export default function App() {
  const [pin, setPin] = useState(null)
  const [steps, setSteps] = useState([])
  const [streamingText, setStreamingText] = useState('')  // live Claude tokens
  const [result, setResult] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState(null)
  const [showResult, setShowResult] = useState(false)
  const esRef = useRef(null)
  const mapRef = useRef(null)
  const gotResultRef = useRef(false)

  const startAnalysis = useCallback((lat, lon) => {
    if (esRef.current) esRef.current.close()

    gotResultRef.current = false
    setPin({ lat, lon })
    setSteps([])
    setStreamingText('')
    setResult(null)
    setError(null)
    setShowResult(false)
    setIsAnalyzing(true)

    const es = new EventSource(`${API_BASE}/api/analyze/stream?lat=${lat}&lon=${lon}`)
    esRef.current = es

    es.addEventListener('step', (e) => {
      const data = JSON.parse(e.data)
      setSteps((prev) => [...prev, data.message])
    })

    // Live token stream — append each chunk as Claude types
    es.addEventListener('token', (e) => {
      const { text } = JSON.parse(e.data)
      setStreamingText((prev) => prev + text)
    })

    es.addEventListener('result', (e) => {
      gotResultRef.current = true
      setResult(JSON.parse(e.data))
      setStreamingText('')
      setIsAnalyzing(false)
      setShowResult(true)   // auto-open the report card
      es.close()
    })

    es.addEventListener('error', (e) => {
      if (gotResultRef.current) return
      const msg = e.data
        ? JSON.parse(e.data).message
        : 'Analysis failed. Check API keys and try again.'
      setError(msg)
      setIsAnalyzing(false)
      es.close()
    })
  }, [])

  const handleCoordAnalyse = useCallback(
    (lat, lon) => {
      if (mapRef.current) {
        mapRef.current.flyTo({ center: [lon, lat], zoom: 12, duration: 1200 })
      }
      startAnalysis(lat, lon)
    },
    [startAnalysis],
  )

  const handleMapClick = useCallback(
    (e) => {
      const { lat, lng } = e.lngLat
      startAnalysis(lat, lng)
    },
    [startAnalysis],
  )

  const isStreaming = isAnalyzing && streamingText.length > 0

  return (
    <div className="h-screen w-screen relative">
      <Map
        ref={mapRef}
        mapboxAccessToken={MAPBOX_TOKEN}
        initialViewState={{ longitude: 74.35, latitude: 31.52, zoom: 6 }}
        style={{ width: '100%', height: '100%' }}
        mapStyle="mapbox://styles/mapbox/satellite-streets-v12"
        onClick={handleMapClick}
        cursor="crosshair"
      >
        {pin && <Marker latitude={pin.lat} longitude={pin.lon} color="#22c55e" />}
      </Map>

      {!pin && !isAnalyzing && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-black/70 text-white text-sm px-4 py-2 rounded-full pointer-events-none">
          Click anywhere on the map to analyse a location
        </div>
      )}

      <CoordInput onAnalyse={handleCoordAnalyse} />

      {/* Progress log + live streaming preview */}
      {(isAnalyzing || (steps.length > 0 && !result)) && !error && (
        <ProgressHUD steps={steps} isAnalyzing={isAnalyzing} streamingText={streamingText} />
      )}

      {error && (
        <div className="absolute top-20 left-4 bg-red-900/90 text-red-100 rounded-lg p-4 max-w-sm text-sm">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Report card — opens automatically when result arrives */}
      {result && showResult && (
        <ResultCard
          result={result}
          onClose={() => setShowResult(false)}
        />
      )}

      {/* Re-open button if card was closed */}
      {result && !showResult && (
        <button
          onClick={() => setShowResult(true)}
          className="absolute bottom-6 left-1/2 -translate-x-1/2 bg-green-500 hover:bg-green-400 text-white font-semibold px-6 py-3 rounded-full shadow-2xl flex items-center gap-2 transition-colors"
        >
          View Planting Report ↑
        </button>
      )}
    </div>
  )
}
