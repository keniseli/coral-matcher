import type { IdentifyApiResponse } from '../types/api'
import type { Segment } from '../types/segment'

async function identifyCoral(selectedSegments: Segment[], file: File): Promise<IdentifyApiResponse> {
  const apiBase = import.meta.env.PROD ? (import.meta.env.VITE_API_BASE as string) : ''
  const url = apiBase ? `${apiBase}/api/identify-coral` : '/api/identify-coral'

  const form = new FormData()
  form.append('image', file)
  form.append('segments', JSON.stringify({selectedSegments: selectedSegments }))

  const res = await fetch(url, { method: 'POST', body: form })
  if (!res.ok) throw new Error('Identify request failed.')
  return await res.json()
}

export default { identifyCoral }
