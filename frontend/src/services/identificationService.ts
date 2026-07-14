export interface IdentifyResponse {
  cropDataUrl?: string
  cropWidth?: number
  cropHeight?: number
  selectedSegments?: number[]
}

async function identifyCoral(segmentationId: string, selectedSegmentIds: number[]): Promise<IdentifyResponse> {
  const apiBase = import.meta.env.PROD ? (import.meta.env.VITE_API_BASE as string) : ''
  const url = apiBase ? `${apiBase}/api/identify-coral` : '/api/identify-coral'

  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ segmentationId, selectedSegments: selectedSegmentIds })
  })
  if (!res.ok) throw new Error('Identify request failed.')
  return await res.json()
}

export default { identifyCoral }
