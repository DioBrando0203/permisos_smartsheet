import { useRef, useState } from 'react'
import { Button, Dialog, StatusAlert } from '../../components/ui'
import { accessLevels } from '../../lib/accessLevels'
import type { AccessLevel, Group } from '../../lib/types'
import { useContacts, useGroups } from './hooks'
import type { CreateShareInput } from './mutations'
import { parseRecipientEmails } from './lib/recipients'

type Props = {
  open: boolean
  sheetName: string
  pending: boolean
  error: Error | null
  onClose: () => void
  onCreate: (input: CreateShareInput) => void
}
const levels = (Object.keys(accessLevels) as AccessLevel[]).filter((level) => level !== 'OWNER')

export function ShareDialog({ open, sheetName, pending, error, onClose, onCreate }: Props) {
  const input = useRef<HTMLInputElement>(null)
  const [value, setValue] = useState('')
  const [level, setLevel] = useState<Exclude<AccessLevel, 'OWNER'>>('EDITOR')
  const [sendEmail, setSendEmail] = useState(false)
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [selectedGroups, setSelectedGroups] = useState<Group[]>([])
  const contacts = useContacts(open)
  const groups = useGroups(open)
  const parsed = parseRecipientEmails(value)
  const search = value.trim().toLocaleLowerCase()
  const suggestions =
    search.length > 1
      ? (contacts.data
          ?.filter((contact) => `${contact.name} ${contact.email}`.toLocaleLowerCase().includes(search))
          .slice(0, 5) ?? [])
      : []
  const groupSuggestions =
    search.length > 1
      ? (groups.data?.filter((group) => group.name.toLocaleLowerCase().includes(search)).slice(0, 5) ?? [])
      : []
  const count = parsed.emails.length + selectedGroups.length
  const canSubmit = count > 0 && parsed.invalid.length === 0 && !pending
  const submit = () => {
    if (!canSubmit) return
    onCreate({
      recipients: [
        ...parsed.emails.map((email) => ({ email })),
        ...selectedGroups.map((group) => ({ groupId: group.id })),
      ],
      accessLevel: level,
      sendEmail,
      subject,
      message,
    })
  }
  return (
    <Dialog
      open={open}
      title={`Compartir ${sheetName}`}
      initialFocusRef={input}
      onClose={onClose}
      footer={
        <>
          <Button appearance="secondary" onClick={onClose} disabled={pending}>
            Cancelar
          </Button>
          <Button onClick={submit} disabled={!canSubmit}>
            {pending ? 'Dando acceso…' : `Dar acceso a ${count} personas`}
          </Button>
        </>
      }
    >
      <div className="share-dialog">
        <label>
          Destinatarios
          <input
            ref={input}
            value={value}
            onChange={(event) => setValue(event.target.value)}
            onBlur={() => setValue(value.trim())}
            placeholder="correo@ejemplo.com; otro@ejemplo.com"
          />
        </label>
        {(suggestions.length > 0 || groupSuggestions.length > 0) && (
          <ul className="recipient-suggestions" aria-label="Sugerencias de destinatarios">
            {suggestions.map((contact) => (
              <li key={contact.id}>
                <Button appearance="subtle" size="sm" onClick={() => setValue(contact.email)}>
                  {contact.name || contact.email} · {contact.email}
                </Button>
              </li>
            ))}
            {groupSuggestions.map((group) => (
              <li key={group.id}>
                <Button
                  appearance="subtle"
                  size="sm"
                  onClick={() => {
                    setSelectedGroups((current) =>
                      current.some((item) => item.id === group.id) ? current : [...current, group],
                    )
                    setValue('')
                  }}
                >
                  Grupo · {group.name}
                </Button>
              </li>
            ))}
          </ul>
        )}
        {selectedGroups.length > 0 && (
          <ul className="recipient-chips">
            {selectedGroups.map((group) => (
              <li key={group.id}>
                {group.name}
                <Button
                  appearance="subtle"
                  size="sm"
                  onClick={() =>
                    setSelectedGroups((current) => current.filter((item) => item.id !== group.id))
                  }
                  aria-label={`Quitar grupo ${group.name}`}
                >
                  Quitar
                </Button>
              </li>
            ))}
          </ul>
        )}
        <p>Separe correos con coma, punto y coma, espacio o salto de línea.</p>
        {parsed.duplicates.length > 0 && (
          <StatusAlert tone="warning">Se omitieron destinatarios repetidos.</StatusAlert>
        )}
        {parsed.invalid.length > 0 && (
          <StatusAlert tone="error">Escriba un correo válido, por ejemplo nombre@empresa.com.</StatusAlert>
        )}
        <label>
          Nivel
          <select
            value={level}
            onChange={(event) => setLevel(event.target.value as Exclude<AccessLevel, 'OWNER'>)}
          >
            {levels.map((item) => (
              <option key={item} value={item}>
                {accessLevels[item].label} · {accessLevels[item].description}
              </option>
            ))}
          </select>
        </label>
        <label className="check-label">
          <input
            type="checkbox"
            checked={sendEmail}
            onChange={(event) => setSendEmail(event.target.checked)}
          />
          Avisar por correo
        </label>
        {sendEmail && (
          <>
            <label>
              Asunto
              <input value={subject} maxLength={200} onChange={(event) => setSubject(event.target.value)} />
            </label>
            <label>
              Mensaje
              <textarea
                value={message}
                maxLength={2000}
                onChange={(event) => setMessage(event.target.value)}
              />
            </label>
          </>
        )}
        {error && <StatusAlert tone="error">{error.message}</StatusAlert>}
      </div>
    </Dialog>
  )
}
