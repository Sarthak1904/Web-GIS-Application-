import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { datasetsApi, type Dataset } from '../api/endpoints'

export default function Dashboard() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    datasetsApi
      .list()
      .then(setDatasets)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-slate-100">Dashboard</h1>
        <p className="text-slate-500 mt-1">
          Overview of your geospatial datasets and platform status
        </p>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
          {error}
        </div>
      )}

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-6">
          <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider">
            Datasets
          </h3>
          <p className="mt-2 text-3xl font-semibold text-slate-100">
            {loading ? '—' : datasets.length}
          </p>
          <Link
            to="/datasets"
            className="mt-4 inline-block text-sm text-primary-400 hover:text-primary-300"
          >
            Manage datasets →
          </Link>
        </div>

        <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-6">
          <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider">
            Map View
          </h3>
          <p className="mt-2 text-slate-400 text-sm">
            Explore features spatially with bbox and proximity queries
          </p>
          <Link
            to="/map"
            className="mt-4 inline-block text-sm text-primary-400 hover:text-primary-300"
          >
            Open map →
          </Link>
        </div>

        <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-6">
          <h3 className="text-sm font-medium text-slate-500 uppercase tracking-wider">
            Upload
          </h3>
          <p className="mt-2 text-slate-400 text-sm">
            Ingest shapefiles (.zip) with CRS validation and reprojection
          </p>
          <Link
            to="/upload"
            className="mt-4 inline-block text-sm text-primary-400 hover:text-primary-300"
          >
            Upload shapefile →
          </Link>
        </div>
      </div>

      {!loading && datasets.length > 0 && (
        <div className="mt-10">
          <h2 className="text-lg font-medium text-slate-200 mb-4">Recent datasets</h2>
          <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700/50">
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Name</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Slug</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Actions</th>
                </tr>
              </thead>
              <tbody>
                {datasets.slice(0, 5).map((ds) => (
                  <tr key={ds.id} className="border-b border-slate-700/30 hover:bg-slate-800/30">
                    <td className="py-3 px-4 text-slate-200">{ds.name}</td>
                    <td className="py-3 px-4 text-slate-500 font-mono text-sm">{ds.slug}</td>
                    <td className="py-3 px-4">
                      <Link
                        to={`/map?dataset=${ds.id}`}
                        className="text-sm text-primary-400 hover:text-primary-300"
                      >
                        View on map
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
