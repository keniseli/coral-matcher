import type { IdentifyApiResponse } from '../types/api'
import type { Segment } from '../types/segment'

async function identifyCoralBySegments(selectedSegments: Segment[], file: File): Promise<IdentifyApiResponse> {
  const apiBase = import.meta.env.VITE_API_BASE as string
  const url = apiBase ? `${apiBase}/api/identify-by-segments` : '/api/identify-by-segments'
  const form = new FormData()
  form.append('image', file)
  form.append('segments', JSON.stringify({ selectedSegments }))
  const res = await fetch(url, { method: 'POST', body: form })
  if (!res.ok) throw new Error('Identify request failed.')
  return await res.json()
}

interface ConfirmCoralRequest {
  image: File
  selectedSegments: Segment[]
  selectedCandidateId: string | null
  diveSite: string
  coralName: string
}

async function confirmCoral(request: ConfirmCoralRequest): Promise<void> {
  const apiBase = import.meta.env.VITE_API_BASE as string
  const url = apiBase ? `${apiBase}/api/confirm-coral` : '/api/confirm-coral'
  const form = new FormData()
  form.append('image', request.image)
  form.append('segments', JSON.stringify({ selectedSegments: request.selectedSegments }))
  form.append('selectedCandidateId', request.selectedCandidateId ?? '')
  form.append('diveSite', request.diveSite)
  form.append('coralName', request.coralName)
  const res = await fetch(url, { method: 'POST', body: form })
  if (!res.ok) throw new Error('Confirmation request failed.')
  return res.json()
}

export default { identifyCoralBySegments, confirmCoral }
