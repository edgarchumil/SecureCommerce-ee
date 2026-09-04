import { Eye, EyeOff } from 'lucide-react'
import { forwardRef, useState, type ComponentPropsWithoutRef } from 'react'

type PasswordInputProps = Omit<ComponentPropsWithoutRef<'input'>, 'type'>

export const PasswordInput = forwardRef<HTMLInputElement, PasswordInputProps>(function PasswordInput(
  { className = '', ...props },
  ref,
) {
  const [visible, setVisible] = useState(false)

  return (
    <span className="relative block">
      <input {...props} ref={ref} type={visible ? 'text' : 'password'} className={`${className} pr-11`} />
      <button
        type="button"
        className="absolute bottom-1 right-1 top-1 flex w-10 items-center justify-center rounded-md border-l border-slate-200 bg-white text-blue-800 hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-1"
        onClick={() => setVisible((current) => !current)}
        aria-label={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
        aria-pressed={visible}
        title={visible ? 'Ocultar contraseña' : 'Mostrar contraseña'}
      >
        {visible ? <EyeOff size={19} aria-hidden="true" /> : <Eye size={19} aria-hidden="true" />}
      </button>
    </span>
  )
})
