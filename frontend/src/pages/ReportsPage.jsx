import { FileText, ScanText, Trash2, Upload } from 'lucide-react'
import { useRef, useState } from 'react'
import Disclaimer from '../components/Disclaimer'
import { Alert, AsyncBoundary, Button, Card, EmptyState, PageHeader } from '../components/ui'
import { MAX_REPORT_BYTES } from '../constants'
import { useAsync } from '../hooks/useAsync'
import { reportService } from '../services/reportService'
import { getErrorMessage } from '../utils/errors'
import { formatBytes, formatDateTime } from '../utils/format'

const ALLOWED_EXTENSIONS = ['pdf', 'png', 'jpg', 'jpeg']
const STATUS_STYLE = {
  PENDING: 'bg-amber-100 text-amber-900',
  COMPLETED: 'bg-emerald-100 text-emerald-900',
  FAILED: 'bg-red-100 text-red-900',
}

function validateFile(file) {
  const extension = file.name.split('.').pop().toLowerCase()
  if (!ALLOWED_EXTENSIONS.includes(extension)) return 'Only PDF, PNG, JPG and JPEG files are allowed.'
  if (file.size > MAX_REPORT_BYTES) return 'The file is larger than 10 MB.'
  if (file.size === 0) return 'The file is empty.'
  return ''
}

function ValueList({ values }) {
  if (!Array.isArray(values) || !values.length) return null
  return (
    <ul className="mt-2 list-disc space-y-1 pl-5">
      {values.map((value, index) => (
        <li key={index}>{typeof value === 'string' ? value : Object.values(value).join(' · ')}</li>
      ))}
    </ul>
  )
}

function ReportCard({ report, busy, onProcess, onDelete }) {
  const analysis = report.analysis
  const status = analysis?.status || 'PENDING'
  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <FileText className="mt-1 size-7 shrink-0 text-brand-700" aria-hidden />
          <div className="min-w-0">
            <h2 className="break-all text-lg font-bold">{report.original_filename}</h2>
            <p className="text-sm text-slate-600">{report.file_type} · {formatBytes(report.file_size)} · {formatDateTime(report.uploaded_at)}</p>
          </div>
        </div>
        <span className={`rounded-full px-3 py-1 text-sm font-semibold ${STATUS_STYLE[status]}`}>{status === 'PENDING' ? 'Not read yet' : status === 'COMPLETED' ? 'Text extracted' : 'Failed'}</span>
      </div>

      {analysis?.error_message && <Alert tone="error" className="mt-3">{analysis.error_message}</Alert>}
      {analysis?.summary && <p className="mt-3 whitespace-pre-wrap"><strong>Summary: </strong>{analysis.summary}</p>}
      <ValueList values={analysis?.important_values} />
      {analysis?.extracted_text && (
        <details className="mt-3 rounded-xl bg-slate-50 p-3">
          <summary className="cursor-pointer font-semibold">Text read from the file</summary>
          <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap break-words text-sm">{analysis.extracted_text}</pre>
          <p className="mt-2 text-sm text-slate-600">This is text recognised from your file. It may contain mistakes and is not a medical diagnosis.</p>
        </details>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        <Button variant="secondary" loading={busy === 'process'} disabled={Boolean(busy)} onClick={() => onProcess(report)}>
          <ScanText className="size-5" aria-hidden /> {status === 'COMPLETED' ? 'Read again' : 'Read text'}
        </Button>
        <Button variant="ghost" disabled={Boolean(busy)} onClick={() => onDelete(report)} className="text-red-700"><Trash2 className="size-5" aria-hidden /> Delete</Button>
      </div>
    </Card>
  )
}

export default function ReportsPage() {
  const reports = useAsync(() => reportService.list(), [])
  const inputRef = useRef(null)
  const [uploading, setUploading] = useState(false)
  const [busy, setBusy] = useState({})
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  const upload = async (file) => {
    setError(''); setNotice('')
    const problem = validateFile(file)
    if (problem) return setError(problem)
    setUploading(true)
    try {
      const created = await reportService.upload(file)
      reports.setData((current) => [created, ...(current || [])])
      setNotice('Uploaded. Choose "Read text" to extract the text from it.')
    } catch (err) { setError(getErrorMessage(err)) } finally { setUploading(false); if (inputRef.current) inputRef.current.value = '' }
  }

  const process = async (report) => {
    setError(''); setNotice('')
    setBusy((current) => ({ ...current, [report.id]: 'process' }))
    try {
      const updated = await reportService.process(report.id)
      reports.setData((current) => current.map((item) => (item.id === report.id ? updated : item)))
    } catch (err) { setError(getErrorMessage(err)); reports.reload() } finally { setBusy((current) => ({ ...current, [report.id]: null })) }
  }

  const remove = async (report) => {
    if (!window.confirm(`Delete "${report.original_filename}"?`)) return
    setBusy((current) => ({ ...current, [report.id]: 'delete' }))
    try {
      await reportService.remove(report.id)
      reports.setData((current) => current.filter((item) => item.id !== report.id))
    } catch (err) { setError(getErrorMessage(err)) } finally { setBusy((current) => ({ ...current, [report.id]: null })) }
  }

  return (
    <div>
      <PageHeader title="Reports and prescriptions" subtitle="Upload a PDF or photo to read the text from it." />
      <Card className="mb-6">
        <input ref={inputRef} id="report-file" type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" className="sr-only"
          onChange={(e) => e.target.files[0] && upload(e.target.files[0])} />
        <label htmlFor="report-file" className="flex min-h-32 cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-brand-600 bg-brand-50 p-4 text-center focus-within:outline">
          <Upload className="size-9 text-brand-700" aria-hidden />
          <span className="text-lg font-bold">{uploading ? 'Uploading…' : 'Tap to choose a report or prescription'}</span>
          <span className="text-sm text-slate-600">PDF, PNG, JPG or JPEG · up to 10 MB</span>
        </label>
      </Card>

      {error && <Alert tone="error" className="mb-4">{error}</Alert>}
      {notice && <Alert tone="success" className="mb-4">{notice}</Alert>}

      <AsyncBoundary loading={reports.loading} error={reports.error} onRetry={reports.reload}>
        {reports.data?.length ? (
          <div className="space-y-4">
            {reports.data.map((report) => (
              <ReportCard key={report.id} report={report} busy={busy[report.id]} onProcess={process} onDelete={remove} />
            ))}
          </div>
        ) : <EmptyState icon={FileText} title="No reports yet">Upload your first report above.</EmptyState>}
      </AsyncBoundary>
      <Disclaimer className="mt-6" text="Text recognition can make mistakes and is not a medical interpretation. Please show your original report to a doctor." />
    </div>
  )
}
