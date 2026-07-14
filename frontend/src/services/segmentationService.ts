import type { Segment } from '../types/segment'

export interface SegmentResponse {
  segmentationId: string
  image: { width: number; height: number }
  segments: Segment[]
}

async function segmentImage(file: File): Promise<SegmentResponse> {
  const form = new FormData()
  form.append('image', file)
  const apiBase = import.meta.env.PROD ? (import.meta.env.VITE_API_BASE as string) : ''
  const url = apiBase ? `${apiBase}/api/segment-image` : '/api/segment-image'

  const res = await fetch(url, { method: 'POST', body: form })
  if (!res.ok) throw new Error('Segmentation request failed.')
  return await res.json()
}

export default { segmentImage }
