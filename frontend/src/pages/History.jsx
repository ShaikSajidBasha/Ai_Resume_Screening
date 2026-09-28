import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { Search, Trash2, Eye } from 'lucide-react'
import DashboardLayout from '../layouts/DashboardLayout.jsx'
import LoadingState from '../components/LoadingState.jsx'
import { analysisApi } from '../services/api'

export default function History() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [sortKey, setSortKey] = useState('created_at')

  const load = () => {
    setLoading(true)
    analysisApi.history().then((res) => setItems(res.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this analysis? This cannot be undone.')) return
    await analysisApi.remove(id)
    setItems((prev) => prev.filter((i) => i.id !== id))
  }

  const filtered = useMemo(() => {
    let rows = items.filter((i) =>
      i.resume_file_name.toLowerCase().includes(query.toLowerCase()) ||
      i.job_title.toLowerCase().includes(query.toLowerCase())
    )
    rows = [...rows].sort((a, b) => {
      if (sortKey === 'created_at') return new Date(b.created_at) - new Date(a.created_at)
      return (b[sortKey] ?? 0) - (a[sortKey] ?? 0)
    })
    return rows
  }, [items, query, sortKey])

  if (loading) return <DashboardLayout><LoadingState message="Loading history…" /></DashboardLayout>

  return (
    <DashboardLayout>
      <h1 className="font-display text-3xl text-ink mb-1">Analysis history</h1>
      <p className="text-sm text-slate-650 mb-6">Every resume screening you've run, in one place.</p>

      <div className="flex items-center gap-3 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-650" />
          <input
            value={query} onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by resume or job title…"
            className="w-full pl-9 pr-3 py-2.5 rounded-sm border border-ink/15 bg-white text-sm focus:border-teal outline-none"
          />
        </div>
        <select
          value={sortKey} onChange={(e) => setSortKey(e.target.value)}
          className="px-3 py-2.5 rounded-sm border border-ink/15 bg-white text-sm outline-none"
        >
          <option value="created_at">Sort: Newest first</option>
          <option value="overall_score">Sort: Overall score</option>
          <option value="ats_score">Sort: ATS score</option>
          <option value="job_match_score">Sort: Job match score</option>
        </select>
      </div>

      {filtered.length === 0 ? (
        <div className="border border-ink/10 rounded-md p-12 text-center bg-white/40">
          <p className="text-slate-650 mb-4">No analyses yet.</p>
          <Link to="/analyze" className="text-teal hover:underline text-sm">Run your first analysis</Link>
        </div>
      ) : (
        <div className="border border-ink/10 rounded-md bg-white/40 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-650 border-b border-ink/10 bg-ink/[0.02]">
                <th className="px-5 py-3 font-normal">Resume</th>
                <th className="px-5 py-3 font-normal">Job title</th>
                <th className="px-5 py-3 font-normal">ATS</th>
                <th className="px-5 py-3 font-normal">Match</th>
                <th className="px-5 py-3 font-normal">Overall</th>
                <th className="px-5 py-3 font-normal">Date</th>
                <th className="px-5 py-3 font-normal"></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((row) => (
                <tr key={row.id} className="border-b border-ink/5 last:border-0">
                  <td className="px-5 py-3 text-ink">{row.resume_file_name}</td>
                  <td className="px-5 py-3 text-slate-650">{row.job_title}</td>
                  <td className="px-5 py-3 tabular-nums">{Math.round(row.ats_score)}</td>
                  <td className="px-5 py-3 tabular-nums">{Math.round(row.job_match_score)}</td>
                  <td className="px-5 py-3 tabular-nums font-medium">{Math.round(row.overall_score)}</td>
                  <td className="px-5 py-3 text-slate-650 text-xs">{new Date(row.created_at).toLocaleDateString()}</td>
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-3">
                      <Link to={`/results/${row.id}`} className="text-teal hover:text-teal/70"><Eye size={16} /></Link>
                      <button onClick={() => handleDelete(row.id)} className="text-danger hover:text-danger/70">
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </DashboardLayout>
  )
}
