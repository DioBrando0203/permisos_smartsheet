import { Spinner } from './Spinner'

export function LoadingNotice({ children }: { children: string }) {
  return (
    <div className="loading-notice" role="status">
      <Spinner size="sm" />
      {children}
    </div>
  )
}
