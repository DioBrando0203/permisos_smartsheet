import { useOutletContext } from 'react-router'
import type { Me } from '../../lib/types'

export type ShellContext = { me: Me | null; readOnly: boolean }

export function useShellContext(): ShellContext {
  return useOutletContext<ShellContext>()
}
