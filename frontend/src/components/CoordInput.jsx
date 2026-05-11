import { useState } from 'react'

export default function CoordInput({ onAnalyse }) {
  const [lat, setLat] = useState('')
  const [lon, setLon] = useState('')
  const [error, setError] = useState('')

  const handle = (e) => {
    e.preventDefault()
    const latN = parseFloat(lat)
    const lonN = parseFloat(lon)

    if (isNaN(latN) || latN < -90 || latN > 90) {
      setError('Latitude must be between -90 and 90')
      return
    }
    if (isNaN(lonN) || lonN < -180 || lonN > 180) {
      setError('Longitude must be between -180 and 180')
      return
    }

    setError('')
    onAnalyse(latN, lonN)
  }

  return (
    <div className="absolute top-4 right-4 bg-black/80 backdrop-blur rounded-xl p-3 shadow-2xl w-60">
      <p className="text-white text-xs font-semibold uppercase tracking-wider mb-2">
        Enter Coordinates
      </p>
      <form onSubmit={handle} className="flex flex-col gap-2">
        <div className="flex gap-2">
          <input
            type="number"
            step="any"
            placeholder="Latitude"
            value={lat}
            onChange={(e) => setLat(e.target.value)}
            className="w-full bg-white/10 text-white text-xs rounded-lg px-2 py-1.5 placeholder-white/40 focus:outline-none focus:ring-1 focus:ring-green-400"
          />
          <input
            type="number"
            step="any"
            placeholder="Longitude"
            value={lon}
            onChange={(e) => setLon(e.target.value)}
            className="w-full bg-white/10 text-white text-xs rounded-lg px-2 py-1.5 placeholder-white/40 focus:outline-none focus:ring-1 focus:ring-green-400"
          />
        </div>
        {error && <p className="text-red-400 text-xs">{error}</p>}
        <button
          type="submit"
          className="bg-green-500 hover:bg-green-400 text-white text-xs font-semibold rounded-lg py-1.5 transition-colors"
        >
          Analyse Location
        </button>
      </form>
      <p className="text-white/30 text-xs mt-2 leading-tight">
        Or click anywhere on the map to drop a pin.
      </p>
    </div>
  )
}
