import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Alert, Button, Card, Field, inputClass } from '../components/ui'
import { HOME_BY_ROLE } from '../constants'
import { useAuth } from '../context/AuthContext'
import { useLanguage } from '../context/LanguageContext'
import { getErrorMessage, getFieldErrors } from '../utils/errors'

export default function RegisterPage() {
  const { register: registerUser, user } = useAuth()
  const { t } = useLanguage()
  const navigate = useNavigate()
  const [serverError, setServerError] = useState('')
  const { register, handleSubmit, setError, formState: { errors, isSubmitting } } = useForm()

  if (user) return <Navigate to={HOME_BY_ROLE[user.role]} replace />

  const onSubmit = async (values) => {
    setServerError('')
    try {
      const created = await registerUser(values)
      navigate(HOME_BY_ROLE[created.role], { replace: true })
    } catch (error) {
      const fieldErrors = getFieldErrors(error)
      const known = ['name', 'email', 'phone', 'password'].filter((field) => fieldErrors[field])
      known.forEach((field) => setError(field, { message: fieldErrors[field] }))
      if (!known.length) setServerError(getErrorMessage(error))
    }
  }

  return (
    <Card className="mx-auto mt-6 max-w-md">
      <h1 className="mb-5 text-2xl font-bold">{t('auth.registerTitle')}</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
        {serverError && <Alert tone="error">{serverError}</Alert>}
        <Field id="name" label={t('auth.name')} error={errors.name?.message}>
          <input id="name" autoComplete="name" className={inputClass} {...register('name', { required: 'Name is required.' })} />
        </Field>
        <Field id="email" label={t('auth.email')} error={errors.email?.message}>
          <input id="email" type="email" autoComplete="email" className={inputClass}
            {...register('email', { required: 'Email is required.' })} />
        </Field>
        <Field id="phone" label={t('auth.phone')} error={errors.phone?.message}>
          <input id="phone" type="tel" autoComplete="tel" className={inputClass} {...register('phone')} />
        </Field>
        <Field id="password" label={t('auth.password')} hint="At least 8 characters; avoid common passwords." error={errors.password?.message}>
          <input id="password" type="password" autoComplete="new-password" className={inputClass}
            {...register('password', { required: 'Password is required.', minLength: { value: 8, message: 'Use at least 8 characters.' } })} />
        </Field>
        <Button type="submit" loading={isSubmitting} className="w-full">{t('nav.register')}</Button>
      </form>
      <p className="mt-5 text-center">{t('auth.haveAccount')} <Link className="font-semibold text-brand-700 underline" to="/login">{t('nav.login')}</Link></p>
    </Card>
  )
}
