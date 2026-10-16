import { forwardRef } from 'react'
import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode
  appearance?: 'primary' | 'secondary' | 'subtle' | 'danger'
  size?: 'md' | 'sm'
  iconOnly?: boolean
}

export const Button = forwardRef<HTMLButtonElement, Props>(function Button(
  {
    children,
    className = '',
    appearance = 'primary',
    size = 'md',
    iconOnly = false,
    type = 'button',
    ...props
  },
  ref,
) {
  const classes = [
    'button',
    `button--${appearance}`,
    `button--${size}`,
    iconOnly && 'button--icon',
    className,
  ]
  return (
    <button ref={ref} type={type} className={classes.filter(Boolean).join(' ')} {...props}>
      {children}
    </button>
  )
})
