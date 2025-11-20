import { useEffect, useState } from 'react'
import { datasetsApi, type Dataset } from '../api/endpoints'

export default function Datasets() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [description, setDescription] = useState('')
  const [creating, setCreating] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [showDeleted, setShowDeleted] = useState(false)

  const load = () => {
    datasetsApi
      .list(showDeleted)
      .then(setDatasets)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [showDeleted])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    setError('')
    try {
      await datasetsApi.create({ name, slug, description: description || undefined })
      setName('')
      setSlug('')
      setDescription('')
      setShowCreate(false)
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create')
    } finally {
      setCreating(false)
    }
  }

  const slugFromName = (n: string) =>
    n
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '')

  const handleDelete = async (ds: Dataset, permanent: boolean) => {
    const msg = permanent
      ? `Permanently delete "${ds.name}"? This will remove all data from the database and cannot be undone.`
      : `Delete dataset "${ds.name}"? It will be hidden from the list.`
    if (!window.confirm(msg)) return
    setDeletingId(ds.id)
    setError('')
    try {
      await datasetsApi.delete(ds.id, permanent)
      load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-slate-100">Datasets</h1>
          <p className="text-slate-500 mt-1">Manage versioned geospatial datasets</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={showDeleted}
              onChange={(e) => setShowDeleted(e.target.checked)}
              className="rounded border-slate-600 bg-slate-800 text-primary-500"
            />
            Show deleted
          </label>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="px-4 py-2 bg-primary-500 hover:bg-primary-600 text-white font-medium rounded-lg transition-colors"
          >
            {showCreate ? 'Cancel' : 'New dataset'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {showCreate && (
        <form
          onSubmit={handleCreate}
          className="mb-8 p-6 bg-slate-900/50 border border-slate-700/50 rounded-xl"
        >
          <h3 className="text-lg font-medium text-slate-200 mb-4">Create dataset</h3>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1.5">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => {
                  setName(e.target.value)
                  if (!slug || slug === slugFromName(name)) setSlug(slugFromName(e.target.value))
                }}
                className="w-full px-4 py-2 bg-slate-800/50 border border-slate-600/50 rounded-lg text-slate-200"
                placeholder="Flood Zones"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-400 mb-1.5">Slug</label>
              <input
                type="text"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                className="w-full px-4 py-2 bg-slate-800/50 border border-slate-600/50 rounded-lg text-slate-200 font-mono"
                placeholder="flood-zones"
                required
              />
            </div>
          </div>
          <div className="mt-4">
            <label className="block text-sm font-medium text-slate-400 mb-1.5">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800/50 border border-slate-600/50 rounded-lg text-slate-200"
              rows={2}
              placeholder="FEMA flood hazard areas"
            />
          </div>
          <button
            type="submit"
            disabled={creating}
            className="mt-4 px-4 py-2 bg-primary-500 hover:bg-primary-600 disabled:opacity-50 text-white font-medium rounded-lg"
          >
            {creating ? 'Creating...' : 'Create'}
          </button>
        </form>
      )}

      {loading ? (
        <p className="text-slate-500">Loading...</p>
      ) : datasets.length === 0 ? (
        <div className="p-12 text-center bg-slate-900/50 border border-slate-700/50 rounded-xl">
          <p className="text-slate-500">No datasets yet</p>
          <p className="text-slate-600 text-sm mt-1">Create one to get started</p>
        </div>
      ) : (
        <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700/50">
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Name</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Slug</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-slate-500">Description</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-slate-500 w-48">Actions</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((ds) => (
                <tr key={ds.id} className="border-b border-slate-700/30 hover:bg-slate-800/30">
                  <td className="py-3 px-4 text-slate-200">{ds.name}</td>
                  <td className="py-3 px-4 text-slate-500 font-mono text-sm">{ds.slug}</td>
                  <td className="py-3 px-4 text-slate-500 text-sm">
                    {ds.description || '—'}
                  </td>
                  <td className="py-3 px-4 text-right space-x-2">
                    <button
                      type="button"
                      onClick={() => handleDelete(ds, false)}
                      disabled={deletingId === ds.id}
                      className="px-3 py-1.5 text-sm text-amber-400 hover:text-amber-300 hover:bg-amber-500/10 rounded-lg transition-colors disabled:opacity-50"
                      title="Soft delete (hide from list)"
                    >
                      {deletingId === ds.id ? 'Deleting...' : 'Delete'}
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(ds, true)}
                      disabled={deletingId === ds.id}
                      className="px-3 py-1.5 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
                      title="Permanently remove from database"
                    >
                      {deletingId === ds.id ? 'Deleting...' : 'Permanent delete'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
