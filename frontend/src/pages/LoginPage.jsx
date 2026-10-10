import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Alert, Button, Card, Field, inputClass } from '../components/ui'
import { HOME_BY_ROLE } from '../constants'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'
import { getErrorMessage } from '../utils/errors'

export default function LoginPage() {
  const { login, user } = useAuth()
  const { t } = useLanguage()
  const navigate = useNavigate()
  const location = useLocation()
  const [serverError, setServerError] = useState('')
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm()

  if (user) return <Navigate to={HOME_BY_ROLE[user.role]} replace />

  const onSubmit = async (values) => {
    setServerError('')
    try {
      const signedIn = await login(values)
      navigate(location.state?.from || HOME_BY_ROLE[signedIn.role], { replace: true })
    } catch (error) {
      setServerError(getErrorMessage(error))
    }
  }

  return (
    <Card className="mx-auto mt-6 max-w-md">
      <h1 className="mb-5 text-2xl font-bold">{t('auth.loginTitle')}</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {serverError && <Alert tone="error">{serverError}</Alert>}
        <Field id="email" label={t('auth.email')} error={errors.email?.message}>
          <input id="email" type="email" autoComplete="email" className={inputClass}
            {...register('email', { required: 'Email is required.' })} />
        </Field>
        <Field id="password" label={t('auth.password')} error={errors.password?.message}>
          <input id="password" type="password" autoComplete="current-password" className={inputClass}
            {...register('password', { required: 'Password is required.' })} />
        </Field>
        <Button type="submit" loading={isSubmitting} className="w-full">{t('nav.login')}</Button>
      </form>
      <p className="mt-5 text-center">{t('auth.noAccount')} <Link className="font-semibold text-brand-700 underline" to="/register">{t('nav.register')}</Link></p>
    </Card>
  )
}
