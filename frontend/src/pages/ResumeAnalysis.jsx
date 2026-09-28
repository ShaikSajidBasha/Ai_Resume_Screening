import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { UploadCloud, CheckCircle2, Circle, Loader2 } from 'lucide-react'
import DashboardLayout from '../layouts/DashboardLayout.jsx'
import { resumeApi, jobApi, analysisApi, getApiErrorMessage } from '../services/api'

const STAGES = [
  'Resume Parsing',
  'Job Description Analysis',
  'ATS Analysis',
  'Skill Matching',
  'Keyword Matching',
  'Experience Analysis',
  'Scoring',
  'Recommendations',
  'Final Report',
]

export default function ResumeAnalysis() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [jobTitle, setJobTitle] = useState('')
  const [company, setCompany] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [stageIndex, setStageIndex] = useState(-1)

  const handleFileChange = (e) => {
    const f = e.target.files?.[0]
    if (f) setFile(f)
  }

  const runStageAnimation = () => {
    // Purely cosmetic progress indicator — the real work happens in one API call,
    // but showing each agent stage in sequence makes the multi-agent pipeline visible.
    let i = 0
    const interval = setInterval(() => {
      setStageIndex(i)
      i += 1
      if (i >= STAGES.length) clearInterval(interval)
    }, 450)
    return interval
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!file) {
      setError('Please upload a resume file (PDF or DOCX).')
      return
    }
    if (!jobTitle || description.trim().length < 20) {
      setError('Please provide a job title and a Job Description (at least 20 characters).')
      return
    }

    setAnalyzing(true)
    const stageInterval = runStageAnimation()

    try {
      const resumeRes = await resumeApi.upload(file)
      const jobRes = await jobApi.create({ title: jobTitle, company, description })
      const analysisRes = await analysisApi.analyze({
        resume_id: resumeRes.data.id,
        job_description_id: jobRes.data.id,
      })
      clearInterval(stageInterval)
      setStageIndex(STAGES.length)
      navigate(`/results/${analysisRes.data.analysis_id}`)
    } catch (err) {
      clearInterval(stageInterval)
      setAnalyzing(false)
      setStageIndex(-1)
      setError(getApiErrorMessage(err, 'AI analysis is temporarily unavailable. Please try again.'))
    }
  }

  if (analyzing) {
    return (
      <DashboardLayout>
        <div className="max-w-md mx-auto py-16">
          <h1 className="font-display text-2xl text-ink text-center mb-1">Analyzing your resume</h1>
          <p className="text-sm text-slate-650 text-center mb-8">AI agents are analyzing your resume…</p>
          <ul className="space-y-3">
            {STAGES.map((stage, i) => (
              <li key={stage} className="flex items-center gap-3 text-sm">
                {i < stageIndex ? (
                  <CheckCircle2 size={18} className="text-teal shrink-0" />
                ) : i === stageIndex ? (
                  <Loader2 size={18} className="text-signal shrink-0 animate-spin" />
                ) : (
                  <Circle size={18} className="text-ink/15 shrink-0" />
                )}
                <span className={i <= stageIndex ? 'text-ink' : 'text-slate-650'}>{stage}</span>
              </li>
            ))}
          </ul>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <h1 className="font-display text-3xl text-ink mb-1">New analysis</h1>
      <p className="text-sm text-slate-650 mb-8">Upload a resume and paste the job description to compare them.</p>

      {error && (
        <div className="mb-6 px-4 py-3 rounded-sm bg-[#F7E9E3] border border-danger/30 text-danger text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="grid md:grid-cols-2 gap-8">
        <div>
          <h2 className="font-display text-lg text-ink mb-3">Resume</h2>
          <label
            htmlFor="resume-upload"
            className="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-ink/15 rounded-md py-12 cursor-pointer hover:border-teal/50 transition-colors bg-white/40"
          >
            <UploadCloud size={28} className="text-teal" />
            <span className="text-sm text-ink">{file ? file.name : 'Click to upload your resume'}</span>
            <span className="text-xs text-slate-650">Supported formats: PDF, DOCX</span>
          </label>
          <input id="resume-upload" type="file" accept=".pdf,.docx" className="hidden" onChange={handleFileChange} />
        </div>

        <div>
          <h2 className="font-display text-lg text-ink mb-3">Job description</h2>
          <div className="space-y-3">
            <input
              required value={jobTitle} onChange={(e) => setJobTitle(e.target.value)}
              placeholder="Job title (e.g. Software Developer)"
              className="w-full px-3 py-2.5 rounded-sm border border-ink/15 bg-white focus:border-teal outline-none text-sm"
            />
            <input
              value={company} onChange={(e) => setCompany(e.target.value)}
              placeholder="Company (optional)"
              className="w-full px-3 py-2.5 rounded-sm border border-ink/15 bg-white focus:border-teal outline-none text-sm"
            />
            <textarea
              required value={description} onChange={(e) => setDescription(e.target.value)}
              placeholder="Paste the full job description here…"
              rows={8}
              className="w-full px-3 py-2.5 rounded-sm border border-ink/15 bg-white focus:border-teal outline-none text-sm resize-none"
            />
          </div>
        </div>

        <div className="md:col-span-2">
          <button
            type="submit"
            className="px-6 py-3 rounded-md bg-ink text-paper text-sm hover:bg-ink-800 transition-colors"
          >
            Analyze resume
          </button>
        </div>
      </form>
    </DashboardLayout>
  )
}
