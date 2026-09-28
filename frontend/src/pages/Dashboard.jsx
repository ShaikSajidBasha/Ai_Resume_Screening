import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { ArrowUpRight, FileText, Briefcase } from 'lucide-react'
import DashboardLayout from '../layouts/DashboardLayout.jsx'
import LoadingState from '../components/LoadingState.jsx'
import { dashboardApi } from '../services/api'

export default function Dashboard() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    dashboardApi.get()
      .then((res) => setData(res.data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <DashboardLayout><LoadingState message="Loading your dashboard…" /></DashboardLayout>

  const stats = [
    { label: 'Total analyses', value: data?.total_analyses ?? 0 },
    { label: 'Average ATS score', value: `${data?.average_ats_score ?? 0}` },
    { label: 'Average job match', value: `${data?.average_job_match_score ?? 0}` },
    { label: 'Average overall score', value: `${data?.average_overall_score ?? 0}` },
  ]

  return (
    <DashboardLayout>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display text-3xl text-ink">Overview</h1>
          <p className="text-sm text-slate-650 mt-1">Your resume screening activity at a glance.</p>
        </div>
        <Link to="/analyze" className="flex items-center gap-2 px-4 py-2.5 rounded-md bg-teal text-paper text-sm hover:bg-teal/90 transition-colors">
          New analysis <ArrowUpRight size={16} />
        </Link>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        {stats.map((s) => (
          <div key={s.label} className="border border-ink/10 rounded-md p-5 bg-white/40">
            <div className="font-display text-3xl text-ink tabular-nums">{s.value}</div>
            <div className="text-xs text-slate-650 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {data?.score_trend?.length > 0 && (
        <div className="border border-ink/10 rounded-md p-6 bg-white/40 mb-10">
          <h2 className="font-display text-lg text-ink mb-4">Score trend</h2>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={data.score_trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E7E2D6" />
              <XAxis dataKey="date" tick={{ fontSize: 12, fill: '#4B5768' }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#4B5768' }} />
              <Tooltip contentStyle={{ borderRadius: 8, border: '1px solid #E7E2D6', fontSize: 13 }} />
              <Line type="monotone" dataKey="overall_score" stroke="#0E7C7B" strokeWidth={2} name="Overall" dot={false} />
              <Line type="monotone" dataKey="ats_score" stroke="#E8A33D" strokeWidth={2} name="ATS" dot={false} />
              <Line type="monotone" dataKey="job_match_score" stroke="#0F1B2D" strokeWidth={2} name="Job Match" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6">
        <div className="border border-ink/10 rounded-md p-6 bg-white/40">
          <h2 className="font-display text-lg text-ink mb-4 flex items-center gap-2"><FileText size={17} /> Recent resumes</h2>
          {data?.recent_resumes?.length ? (
            <ul className="space-y-3">
              {data.recent_resumes.map((r) => (
                <li key={r.id} className="text-sm text-slate-650 flex justify-between">
                  <span>{r.file_name}</span>
                  <span className="text-xs">{new Date(r.uploaded_at).toLocaleDateString()}</span>
                </li>
              ))}
            </ul>
          ) : <p className="text-sm text-slate-650">No resumes uploaded yet.</p>}
        </div>
        <div className="border border-ink/10 rounded-md p-6 bg-white/40">
          <h2 className="font-display text-lg text-ink mb-4 flex items-center gap-2"><Briefcase size={17} /> Recent job descriptions</h2>
          {data?.recent_job_descriptions?.length ? (
            <ul className="space-y-3">
              {data.recent_job_descriptions.map((j) => (
                <li key={j.id} className="text-sm text-slate-650 flex justify-between">
                  <span>{j.title}</span>
                  <span className="text-xs">{j.company}</span>
                </li>
              ))}
            </ul>
          ) : <p className="text-sm text-slate-650">No job descriptions added yet.</p>}
        </div>
      </div>
    </DashboardLayout>
  )
}
