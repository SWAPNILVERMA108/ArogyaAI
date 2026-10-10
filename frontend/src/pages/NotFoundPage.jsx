import { Link } from 'react-router-dom'
import { Button } from '../components/ui'

export default function NotFoundPage() {
  return (
    <div className="py-20 text-center">
      <h1 className="text-3xl font-bold">Page not found</h1>
      <p className="mb-6 mt-2 text-slate-600">The page you are looking for does not exist.</p>
      <Link to="/"><Button>Go to home</Button></Link>
    </div>
  )
}
