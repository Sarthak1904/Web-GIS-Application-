import { useState, useRef, useEffect } from 'react'
import { datasetsApi, uploadApi, type Dataset } from '../api/endpoints'

export default function Upload() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [selectedDataset, setSelectedDataset] = useState<number | null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState<{ job_id: number; task_id: string; status: string } | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    datasetsApi.list().then(setDatasets).catch(() => {})
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedDataset || !file) {
      setError('Select a dataset and file')
      return
    }
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = await uploadApi.shapefile(selectedDataset, file)
      setResult(res)
      setFile(null)
      if (fileRef.current) fileRef.current.value = ''
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-slate-100">Upload shapefile</h1>
        <p className="text-slate-500 mt-1">
          Upload a .zip containing .shp, .shx, .dbf. CRS validated, reprojected to EPSG:4326.
        </p>
        <p className="text-amber-500/80 text-sm mt-2">
          Requires Celery worker running. Full stack: <code className="text-amber-400">docker compose up -d</code>. Quick: <code className="text-amber-400">docker compose -f docker-compose.quick.yml up -d</code>
        </p>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-6"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1.5">Dataset</label>
            <select
              value={selectedDataset ?? ''}
              onChange={(e) => setSelectedDataset(e.target.value ? parseInt(e.target.value, 10) : null)}
              className="w-full px-4 py-2 bg-slate-800/50 border border-slate-600/50 rounded-lg text-slate-200"
            >
              <option value="">Select dataset...</option>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.slug})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1.5">Shapefile (.zip)</label>
            <input
              ref={fileRef}
              type="file"
              accept=".zip"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="w-full px-4 py-2 bg-slate-800/50 border border-slate-600/50 rounded-lg text-slate-200 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:bg-primary-500 file:text-white file:font-medium"
            />
          </div>
        </div>

        {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
        {result && (
          <div className="mt-3 p-3 bg-primary-500/10 border border-primary-500/30 rounded-lg text-primary-400 text-sm">
            Job queued. ID: {result.job_id}. Poll /v1/process/jobs/{result.job_id} for status.
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !selectedDataset || !file}
          className="mt-6 px-6 py-2.5 bg-primary-500 hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
        >
          {loading ? 'Uploading...' : 'Upload'}
        </button>
      </form>

      {datasets.length === 0 && (
        <p className="mt-4 text-sm text-slate-500">
          No datasets yet. Create one in <a href="/datasets" className="text-primary-400 hover:underline">Datasets</a>.
        </p>
      )}
    </div>
  )
}
