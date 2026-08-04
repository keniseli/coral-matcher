import type { IdentifyApiResponse } from '../types/api'
import type { Segment } from '../types/segment'
import monitoringSessionService from './monitoringSessionService'
import type { ObservationSummary } from "../types/observationSummary";

const apiBase = import.meta.env.VITE_API_BASE as string

async function identifyCoralBySegments(selectedSegments: Segment[], file: File): Promise<IdentifyApiResponse> {
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
  monitoringSessionId: string
}

async function confirmCoral(request: ConfirmCoralRequest): Promise<void> {
  const url = apiBase ? `${apiBase}/api/confirm-coral` : '/api/confirm-coral'
  const form = new FormData()
  form.append('image', request.image)
  form.append('segments', JSON.stringify({ selectedSegments: request.selectedSegments }))
  form.append('selectedCandidateId', request.selectedCandidateId ?? '')
  form.append('diveSite', request.diveSite)
  form.append('coralName', request.coralName)
  form.append('monitoringSessionId', request.monitoringSessionId)
  const res = await fetch(url, { method: 'POST', body: form })
  if (!res.ok) throw new Error('Confirmation request failed.')
  return res.json()
}
async function getObservationSummaries(): Promise<ObservationSummary[]> {
    const url = apiBase ? `${apiBase}/api/observation-summaries` : '/api/observation-summaries'
    const res = await fetch(url, { method: 'GET' })
    if (!res.ok) throw new Error('Observation summaries request failed.')
    return await res.json();

}

export const mockObservations: ObservationSummary[] = [
  {
    id: "1",
    coralName: "C001",
    monitoringSessionSummary: "07. July 2026 at 9:30 AM",
    diveSite: "Isla Larga",
    observedAt: "2026-07-07",
    imagePath: "https://storage.googleapis.com/coral-matcher-media/Isla larga/c004/cropped_2026-07-24 20:28:02.795031",
  }, {
    id: "2",
    coralName: "Bongo",
    monitoringSessionSummary: "21. July 2026 at 10:30 AM · Anne's Monitoring",
    diveSite: "Isla Larga",
    observedAt: "2026-07-21",
    
    imagePath: "https://storage.googleapis.com/coral-matcher-media/Isla larga/c004/cropped_2026-07-24 20:28:02.795031",
  }, {
    id: "3",
    coralName: "C002",
    monitoringSessionSummary: "21. July 2026 at 9:30 AM",
    diveSite: "Olohuita",
    observedAt: "2026-07-21",
    
    imagePath: "https://storage.googleapis.com/coral-matcher-media/Isla larga/c004/cropped_2026-07-24 20:28:02.795031",
  }, {
    id: "4",
    coralName: "C003",
    monitoringSessionSummary: "21. July 2026 at 9:30 AM",
    diveSite: "Olohuita",
    observedAt: "2026-07-21",
    
    imagePath: "https://storage.googleapis.com/coral-matcher-media/Isla larga/c004/cropped_2026-07-24 20:28:02.795031",
  }, {
    id: "5",
    coralName: "C004",
    monitoringSessionSummary: "07. July 2026 at 9:30 AM",
    diveSite: "Isla Larga",
    observedAt: "2026-07-07",
    
    imagePath: "https://storage.googleapis.com/coral-matcher-media/Isla larga/c004/cropped_2026-07-24 20:28:02.795031",
  }, {
    id: "6",
    coralName: "Love",
    monitoringSessionSummary: "21. July 2026 at 9:30 AM",
    diveSite: "Olohuita",
    observedAt: "2026-07-21",
    
    imagePath: "https://storage.googleapis.com/coral-matcher-media/Isla larga/c004/cropped_2026-07-24 20:28:02.795031",
  }, {
    id: "7",
    coralName: "Twins",
    monitoringSessionSummary: "07. July 2026 at 10:30 AM · Anne's Monitoring",
    diveSite: "Isla Larga",
    observedAt: "2026-07-21",
    
    imagePath: "https://storage.googleapis.com/coral-matcher-media/Isla larga/c004/cropped_2026-07-24 20:28:02.795031",
  }

];

export default { identifyCoralBySegments, confirmCoral, getObservationSummaries }
