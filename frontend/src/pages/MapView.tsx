import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { MapContainer, TileLayer, GeoJSON, useMap } from 'react-leaflet'
import { datasetsApi, featuresApi, type Dataset, type DatasetVersion } from '../api/endpoints'

function MapController({
  setBounds,
}: {
  setBounds: (b: [number, number, number, number]) => void
}) {
  const map = useMap()

  useEffect(() => {
    if (!map) return
    const handler = () => {
      const b = map.getBounds()
      setBounds([b.getWest(), b.getSouth(), b.getEast(), b.getNorth()])
    }
    map.on('moveend', handler)
    handler()
    return () => {
      map.off('moveend', handler)
    }
  }, [map, setBounds])

  return null
}

export default function MapView() {
  const [searchParams] = useSearchParams()
  const preselectedId = searchParams.get('dataset')

  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [versions, setVersions] = useState<DatasetVersion[]>([])
  const [selectedDataset, setSelectedDataset] = useState<number | null>(
    preselectedId ? parseInt(preselectedId, 10) : null
  )
  const [selectedVersion, setSelectedVersion] = useState<number | null>(null)
  const [features, setFeatures] = useState<GeoJSON.FeatureCollection | null>(null)
  const [bounds, setBounds] = useState<[number, number, number, number] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    datasetsApi.list().then(setDatasets).catch(() => {})
  }, [])

  useEffect(() => {
    if (!selectedDataset) {
      setVersions([])
      setSelectedVersion(null)
      return
    }
    datasetsApi
      .versions(selectedDataset)
      .then((v) => {
        setVersions(v)
        const active = v.find((x) => x.status === 'active')
        setSelectedVersion(active?.id ?? v[0]?.id ?? null)
      })
      .catch(() => setVersions([]))
  }, [selectedDataset])

  useEffect(() => {
    if (!selectedVersion || !bounds) {
      setFeatures(null)
      return
    }
    setLoading(true)
    const [minX, minY, maxX, maxY] = bounds
    const bbox = `${minX},${minY},${maxX},${maxY}`
    featuresApi
      .query({ dataset_version_id: selectedVersion, bbox, limit: 500 })
      .then((res) => {
        setFeatures({
          type: 'FeatureCollection',
          features: res.features,
        })
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [selectedVersion, bounds])

  const style = () => ({
    color: '#22c55e',
    weight: 2,
    opacity: 0.8,
    fillColor: '#22c55e',
    fillOpacity: 0.2,
  })

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col">
      <div className="flex items-center gap-4 px-4 py-3 bg-slate-900/50 border-b border-slate-700/50">
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-500">Dataset</label>
          <select
            value={selectedDataset ?? ''}
            onChange={(e) => setSelectedDataset(e.target.value ? parseInt(e.target.value, 10) : null)}
            className="px-3 py-1.5 bg-slate-800 border border-slate-600 rounded text-slate-200 text-sm"
          >
            <option value="">Select...</option>
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-500">Version</label>
          <select
            value={selectedVersion ?? ''}
            onChange={(e) => setSelectedVersion(e.target.value ? parseInt(e.target.value, 10) : null)}
            className="px-3 py-1.5 bg-slate-800 border border-slate-600 rounded text-slate-200 text-sm"
          >
            <option value="">Select...</option>
            {versions.map((v) => (
              <option key={v.id} value={v.id}>
                v{v.version} ({v.status})
              </option>
            ))}
          </select>
        </div>
        {loading && <span className="text-sm text-slate-500">Loading features...</span>}
        {selectedVersion && versions.find((v) => v.id === selectedVersion)?.status === 'ingesting' && (
          <span className="text-sm text-amber-400">Ingesting... (Celery worker must be running)</span>
        )}
        {features && features.features?.length === 0 && !loading && selectedVersion && (
          <span className="text-sm text-slate-500">No features in view. Zoom to Indiana or wait for ingestion.</span>
        )}
        {error && <span className="text-sm text-red-400">{error}</span>}
      </div>

      <div className="flex-1 relative">
        <MapContainer
          center={[39.5, -98.5]}
          zoom={4}
          className="w-full h-full"
          style={{ background: '#0f172a' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          <MapController setBounds={setBounds} />
          {features?.features && features.features.length > 0 && (
            <GeoJSON data={features} style={style} />
          )}
        </MapContainer>
      </div>
    </div>
  )
}
