import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FileSearch } from 'lucide-react'
import { useAuth } from '../context/AuthContext.jsx'
import { getApiErrorMessage } from '../services/api'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirmPassword: '' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setLoading(true)
    try {
      await register(form.name, form.email, form.password, form.confirmPassword)
      navigate('/dashboard')
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to create account.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-paper flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-sm">
        <Link to="/" className="flex items-center gap-2 justify-center mb-8">
          <FileSearch size={22} className="text-teal" />
          <span className="font-display text-lg text-ink">Screenline</span>
        </Link>
        <div className="border border-ink/10 rounded-md p-8 bg-white/40">
          <h1 className="font-display text-2xl text-ink mb-1">Create your account</h1>
          <p className="text-sm text-slate-650 mb-6">Start analyzing your resume in minutes.</p>

          {error && (
            <div className="mb-4 px-3 py-2 rounded-sm bg-[#F7E9E3] border border-danger/30 text-danger text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-slate-650 mb-1.5">Full name</label>
              <input
                required value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="w-full px-3 py-2.5 rounded-sm border border-ink/15 bg-white focus:border-teal outline-none text-sm"
                placeholder="Priya Sharma"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-650 mb-1.5">Email</label>
              <input
                type="email" required value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-3 py-2.5 rounded-sm border border-ink/15 bg-white focus:border-teal outline-none text-sm"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-650 mb-1.5">Password</label>
              <input
                type="password" required value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full px-3 py-2.5 rounded-sm border border-ink/15 bg-white focus:border-teal outline-none text-sm"
                placeholder="At least 8 characters"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-650 mb-1.5">Confirm password</label>
              <input
                type="password" required value={form.confirmPassword}
                onChange={(e) => setForm({ ...form, confirmPassword: e.target.value })}
                className="w-full px-3 py-2.5 rounded-sm border border-ink/15 bg-white focus:border-teal outline-none text-sm"
                placeholder="Re-enter password"
              />
            </div>
            <button
              type="submit" disabled={loading}
              className="w-full py-2.5 rounded-md bg-ink text-paper text-sm hover:bg-ink-800 transition-colors disabled:opacity-50"
            >
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className="text-sm text-slate-650 text-center mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-teal hover:underline">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
