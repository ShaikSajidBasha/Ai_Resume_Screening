import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Download, FileText, Eye, RefreshCw, ChevronLeft } from 'lucide-react'
import DashboardLayout from '../layouts/DashboardLayout.jsx'
import LoadingState from '../components/LoadingState.jsx'
import { analysisApi, generatedResumeApi } from '../services/api'

const templates = [
  { id: 'ATS Professional', label: 'ATS Professional', description: 'Single-column, recruiter-friendly format.' },
  { id: 'Modern Professional', label: 'Modern Professional', description: 'Polished and ATS-safe with balanced structure.' },
  { id: 'Minimal', label: 'Minimal', description: 'Clean and compact, ideal for concise profiles.' },
]

export default function OptimizedResume() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedTemplate, setSelectedTemplate] = useState('ATS Professional')
  const [downloading, setDownloading] = useState(false)
  const [savingTemplate, setSavingTemplate] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!id) return
    generatedResumeApi.get(id)
      .then((res) => {
        setData(res.data)
        setSelectedTemplate(res.data.template_name || 'ATS Professional')
      })
      .catch((requestError) => setError(requestError?.response?.data?.detail || 'Optimized resume could not be loaded.'))
      .finally(() => setLoading(false))
  }, [id])

  const generateAnotherVersion = async () => {
    if (!data?.analysis_id) return
    setGenerating(true)
    setError('')
    try {
      const response = await analysisApi.generateResume(data.analysis_id)
      navigate(`/optimized/${response.data.generated_resume_id}`)
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'A new resume version could not be generated.')
    } finally {
      setGenerating(false)
    }
  }

  const saveTemplate = async (templateName) => {
    if (templateName === selectedTemplate || savingTemplate) return
    setSavingTemplate(true)
    setError('')
    try {
      await generatedResumeApi.selectTemplate(id, templateName)
      setSelectedTemplate(templateName)
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'The selected template could not be applied.')
    } finally {
      setSavingTemplate(false)
    }
  }

  const downloadFile = async (type) => {
    if (!id) return
    setDownloading(true)
    try {
      const res = await (type === 'pdf' ? generatedResumeApi.downloadPdf(id) : generatedResumeApi.downloadDocx(id))
      const blob = new Blob([res.data], { type: type === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = type === 'pdf' ? 'optimized_resume.pdf' : 'optimized_resume.docx'
      link.click()
      window.setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || `The ${type.toUpperCase()} file could not be downloaded.`)
    } finally {
      setDownloading(false)
    }
  }

  if (loading) return <DashboardLayout><LoadingState message="Loading your optimized resume…" /></DashboardLayout>
  if (!data) return <DashboardLayout><div className="text-sm text-slate-650">Optimized resume not found.</div></DashboardLayout>

  const scoreDelta = {
    ats: Number((data.optimized_ats_score || 0) - (data.original_ats_score || 0)).toFixed(0),
    match: Number((data.optimized_job_match_score || 0) - (data.original_job_match_score || 0)).toFixed(0),
    overall: Number((data.optimized_overall_score || 0) - (data.original_overall_score || 0)).toFixed(0),
  }

  return (
    <DashboardLayout>
      <div className="mb-6 flex items-center justify-between gap-4 flex-wrap">
        <button onClick={() => navigate(-1)} className="inline-flex items-center gap-2 text-sm text-slate-650 hover:text-ink">
          <ChevronLeft size={16} /> Back to results
        </button>
        <button onClick={generateAnotherVersion} disabled={generating || !data?.analysis_id} className="inline-flex items-center gap-2 rounded-md border border-ink/10 bg-white px-3 py-2 text-sm text-ink hover:bg-slate-50 disabled:opacity-60">
          <RefreshCw size={15} /> {generating ? 'Generating...' : 'Generate Another Version'}
        </button>
      </div>

      {error && <div role="alert" className="mb-6 border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger">{error}</div>}

      <div className="mb-8 border border-ink/10 rounded-md bg-white/40 p-6">
        <h1 className="font-display text-3xl text-ink mb-2">Resume Optimization Summary</h1>
        <p className="text-sm text-slate-650">AI-generated resume content is based on the information provided in your original resume. Review all content before submitting your application.</p>
      </div>

      <div className="mb-8 grid md:grid-cols-3 gap-4">
        <div className="border rounded-md p-5 bg-white/40">
          <div className="text-xs text-slate-650">Original ATS</div>
          <div className="mt-2 font-display text-3xl text-ink">{Math.round(data.original_ats_score || 0)}</div>
        </div>
        <div className="border rounded-md p-5 bg-white/40">
          <div className="text-xs text-slate-650">Updated ATS</div>
          <div className="mt-2 font-display text-3xl text-ink">{Math.round(data.optimized_ats_score || 0)}</div>
        </div>
        <div className="border rounded-md p-5 bg-white/40">
          <div className="text-xs text-slate-650">ATS Change</div>
          <div className={`mt-2 font-display text-3xl ${Number(scoreDelta.ats) >= 0 ? 'text-teal' : 'text-danger'}`}>{scoreDelta.ats > 0 ? '+' : ''}{scoreDelta.ats}</div>
        </div>
      </div>

      <div className="mb-8 grid md:grid-cols-3 gap-4">
        <div className="border rounded-md p-5 bg-white/40">
          <div className="text-xs text-slate-650">Original Job Match</div>
          <div className="mt-2 font-display text-3xl text-ink">{Math.round(data.original_job_match_score || 0)}</div>
        </div>
        <div className="border rounded-md p-5 bg-white/40">
          <div className="text-xs text-slate-650">Updated Job Match</div>
          <div className="mt-2 font-display text-3xl text-ink">{Math.round(data.optimized_job_match_score || 0)}</div>
        </div>
        <div className="border rounded-md p-5 bg-white/40">
          <div className="text-xs text-slate-650">Job Match Change</div>
          <div className={`mt-2 font-display text-3xl ${Number(scoreDelta.match) >= 0 ? 'text-teal' : 'text-danger'}`}>{scoreDelta.match > 0 ? '+' : ''}{scoreDelta.match}</div>
        </div>
      </div>

      <div className="mb-8 grid md:grid-cols-3 gap-4">
        <div className="border rounded-md p-5 bg-white/40">
          <div className="text-xs text-slate-650">Original Overall</div>
          <div className="mt-2 font-display text-3xl text-ink">{Math.round(data.original_overall_score || 0)}</div>
        </div>
        <div className="border rounded-md p-5 bg-white/40">
          <div className="text-xs text-slate-650">Updated Overall</div>
          <div className="mt-2 font-display text-3xl text-ink">{Math.round(data.optimized_overall_score || 0)}</div>
        </div>
        <div className="border rounded-md p-5 bg-white/40">
          <div className="text-xs text-slate-650">Overall Change</div>
          <div className={`mt-2 font-display text-3xl ${Number(scoreDelta.overall) >= 0 ? 'text-teal' : 'text-danger'}`}>{scoreDelta.overall > 0 ? '+' : ''}{scoreDelta.overall}</div>
        </div>
      </div>

      <div className="mb-8 border border-ink/10 rounded-md bg-white/40 p-6">
        <h2 className="font-display text-lg text-ink mb-4">Choose Resume Template</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {templates.map((template) => (
            <button
              key={template.id}
              onClick={() => saveTemplate(template.id)}
              disabled={savingTemplate}
              className={`text-left rounded-md border p-4 transition disabled:opacity-60 ${selectedTemplate === template.id ? 'border-teal bg-teal/5 shadow-sm' : 'border-ink/10 bg-white/60'}`}
            >
              <div className="font-medium text-ink">{template.label}</div>
              <div className="mt-2 text-xs text-slate-650">{template.description}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="mb-8 border border-ink/10 rounded-md bg-white/40 p-6">
        <h2 className="font-display text-lg text-ink mb-4">What Was Improved</h2>
        <ul className="space-y-2 list-disc list-inside text-sm text-slate-650">
          <li>Professional summary optimized for job relevance</li>
          <li>Resume section headings standardized for ATS readability</li>
          <li>Relevant existing skills highlighted with clearer grouping</li>
          <li>Project descriptions polished without inventing unsupported facts</li>
          <li>Grammar and formatting improved for professional presentation</li>
        </ul>
      </div>

      <div className="mb-8 grid lg:grid-cols-[1.2fr_0.8fr] gap-6">
        <div className="border border-ink/10 rounded-md bg-white/40 p-4">
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm font-medium text-ink"><Eye size={15} /> Resume Preview</div>
            <div className="text-xs text-slate-650">Template: {selectedTemplate}</div>
          </div>
          <div className="bg-white border border-ink/10 rounded-md p-6 shadow-sm min-h-[760px] whitespace-pre-line text-sm leading-6 text-slate-700">
            {data.optimized_text || 'Resume preview is unavailable.'}
          </div>
        </div>

        <div className="space-y-4">
          <div className="border border-ink/10 rounded-md bg-white/40 p-6">
            <h3 className="font-display text-lg text-ink mb-4">Download Options</h3>
            <div className="space-y-3">
              <button onClick={() => downloadFile('pdf')} disabled={downloading} className="flex w-full items-center justify-center gap-2 rounded-md bg-ink px-4 py-3 text-sm font-medium text-paper hover:bg-ink/90 disabled:opacity-60">
                <Download size={16} /> {downloading ? 'Preparing PDF...' : 'Download PDF'}
              </button>
              <button onClick={() => downloadFile('docx')} disabled={downloading} className="flex w-full items-center justify-center gap-2 rounded-md border border-ink/10 bg-white px-4 py-3 text-sm font-medium text-ink hover:bg-slate-50 disabled:opacity-60">
                <FileText size={16} /> {downloading ? 'Preparing DOCX...' : 'Download Word'}
              </button>
            </div>
          </div>

          <div className="border border-ink/10 rounded-md bg-white/40 p-6">
            <h3 className="font-display text-lg text-ink mb-3">Responsible AI note</h3>
            <p className="text-sm text-slate-650">AI-generated resume content is based on the information provided in your original resume. Review all content before submitting your application.</p>
            <p className="mt-3 text-sm text-slate-650">Do not add skills, experience, certifications, or achievements that you do not actually possess.</p>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
