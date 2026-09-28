import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Sparkles } from 'lucide-react'
import DashboardLayout from '../layouts/DashboardLayout.jsx'
import LoadingState from '../components/LoadingState.jsx'
import ScoreDial from '../components/ScoreDial.jsx'
import SkillBadge from '../components/SkillBadge.jsx'
import PriorityTag from '../components/PriorityTag.jsx'
import { analysisApi } from '../services/api'

const statusStyles = {
  'Strong Match': 'bg-teal-light text-teal border-teal/30',
  'Moderate Match': 'bg-signal/10 text-signal-dark border-signal/30',
  'Needs Improvement': 'bg-[#F7E9E3] text-danger border-danger/30',
  'Low Match': 'bg-[#F7E9E3] text-danger border-danger/30',
}

export default function Results() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    analysisApi.get(id).then((res) => setResult(res.data)).finally(() => setLoading(false))
  }, [id])

  const handleGenerateResume = async () => {
    setGenerating(true)
    try {
      const res = await analysisApi.generateResume(id)
      navigate(`/optimized/${res.data.generated_resume_id}`)
    } catch (error) {
      alert(error?.response?.data?.detail || 'Resume optimization could not be completed.')
    } finally {
      setGenerating(false)
    }
  }

  if (loading) return <DashboardLayout><LoadingState message="Loading analysis…" /></DashboardLayout>
  if (!result) return <DashboardLayout><p className="text-slate-650">Analysis not found.</p></DashboardLayout>

  const { scores } = result
  const subScores = [
    { label: 'ATS Score', value: scores.ats_score },
    { label: 'Skill Match', value: scores.skill_score },
    { label: 'Keyword Match', value: scores.keyword_score },
    { label: 'Experience Match', value: scores.experience_score },
    { label: 'Education Match', value: scores.education_score },
    { label: 'Resume Quality', value: scores.resume_quality_score },
  ]

  return (
    <DashboardLayout>
      <Link to="/history" className="flex items-center gap-1.5 text-sm text-slate-650 hover:text-ink mb-6">
        <ArrowLeft size={15} /> Back to history
      </Link>

      {/* Top score summary */}
      <div className="border border-ink/10 rounded-md bg-white/40 p-8 mb-8">
        <div className="flex items-start justify-between flex-wrap gap-6">
          <div className="flex gap-10">
            <ScoreDial score={scores.ats_score} label="ATS score (AI-estimated)" accent="#E8A33D" />
            <ScoreDial score={scores.job_match_score} label="Job match" accent="#0E7C7B" />
            <ScoreDial score={scores.overall_score} label="Overall score" accent="#0F1B2D" />
          </div>
          <span className={`px-3 py-1.5 rounded-sm text-sm border ${statusStyles[result.status] || statusStyles['Low Match']}`}>
            {result.status}
          </span>
        </div>
        <p className="text-sm text-slate-650 leading-relaxed mt-6 max-w-3xl">{result.final_summary}</p>
      </div>

      {/* Sub-score breakdown */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-10">
        {subScores.map((s) => (
          <div key={s.label} className="border border-ink/10 rounded-md p-5 bg-white/40">
            <div className="font-display text-2xl text-ink tabular-nums">{Math.round(s.value)}%</div>
            <div className="text-xs text-slate-650 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Skills */}
      <div className="grid md:grid-cols-2 gap-6 mb-10">
        <div className="border border-ink/10 rounded-md p-6 bg-white/40">
          <h2 className="font-display text-lg text-ink mb-4">Matching skills</h2>
          <div className="flex flex-wrap gap-2">
            {result.matching_skills.length ? result.matching_skills.map((s) => (
              <SkillBadge key={s} variant="match">{s}</SkillBadge>
            )) : <p className="text-sm text-slate-650">Not enough information detected.</p>}
          </div>
        </div>
        <div className="border border-ink/10 rounded-md p-6 bg-white/40">
          <h2 className="font-display text-lg text-ink mb-4">Missing skills</h2>
          <div className="flex flex-wrap gap-2">
            {result.missing_skills.length ? result.missing_skills.map((s) => (
              <SkillBadge key={s} variant="missing">{s}</SkillBadge>
            )) : <p className="text-sm text-slate-650">No missing required skills detected.</p>}
          </div>
        </div>
      </div>

      {/* Keywords table */}
      <div className="border border-ink/10 rounded-md bg-white/40 p-6 mb-10">
        <h2 className="font-display text-lg text-ink mb-4">Keyword analysis</h2>
        {result.missing_keywords.length || result.matching_keywords.length ? (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-650 border-b border-ink/10">
                <th className="pb-2 font-normal">Keyword</th>
                <th className="pb-2 font-normal">Status</th>
                <th className="pb-2 font-normal">Importance</th>
              </tr>
            </thead>
            <tbody>
              {result.matching_keywords.map((k) => (
                <tr key={k} className="border-b border-ink/5">
                  <td className="py-2 text-ink">{k}</td>
                  <td className="py-2 text-teal">Found</td>
                  <td className="py-2 text-slate-650">—</td>
                </tr>
              ))}
              {result.missing_keywords.map((k, idx) => (
                <tr key={`${k.keyword}-${idx}`} className="border-b border-ink/5">
                  <td className="py-2 text-ink">{k.keyword}</td>
                  <td className="py-2 text-danger">{k.status || 'Missing'}</td>
                  <td className="py-2 text-slate-650">{k.importance}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : <p className="text-sm text-slate-650">Not enough information detected.</p>}
      </div>

      {/* ATS analysis */}
      <div className="grid md:grid-cols-2 gap-6 mb-10">
        <div className="border border-ink/10 rounded-md p-6 bg-white/40">
          <h2 className="font-display text-lg text-ink mb-4">Strengths</h2>
          {result.strengths.length ? (
            <ul className="space-y-2 text-sm text-slate-650 list-disc list-inside">
              {result.strengths.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          ) : <p className="text-sm text-slate-650">Not enough information detected.</p>}
        </div>
        <div className="border border-ink/10 rounded-md p-6 bg-white/40">
          <h2 className="font-display text-lg text-ink mb-4">ATS issues</h2>
          {result.ats_issues.length ? (
            <ul className="space-y-2 text-sm text-slate-650 list-disc list-inside">
              {result.ats_issues.map((s, i) => <li key={i}>{s}</li>)}
            </ul>
          ) : <p className="text-sm text-slate-650">No major ATS issues detected.</p>}
        </div>
      </div>

      {/* Recommendations */}
      <div className="border border-ink/10 rounded-md bg-white/40 p-6 mb-8">
        <h2 className="font-display text-lg text-ink mb-4">Recommendations</h2>
        <div className="space-y-3">
          {result.recommendations.map((r, i) => (
            <div key={i} className="flex items-start justify-between gap-4 border border-ink/10 rounded-sm p-4">
              <div>
                <p className="text-xs text-slate-650 mb-1">{r.category}</p>
                <p className="text-sm text-ink">{r.recommendation}</p>
              </div>
              <PriorityTag priority={r.priority} />
            </div>
          ))}
        </div>
      </div>

      <div className="mb-10">
        <button
          onClick={handleGenerateResume}
          disabled={generating}
          className="inline-flex items-center gap-2 rounded-md bg-teal px-5 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-teal/90 disabled:opacity-70"
        >
          <Sparkles size={16} />
          {generating ? 'AI Agents are optimizing your resume...' : 'Generate Optimized Resume'}
        </button>
      </div>

      <p className="text-xs text-slate-650">{result.disclaimer}</p>
    </DashboardLayout>
  )
}
