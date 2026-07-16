import type { Segment } from './segment'

export interface SegmentApiResponse {
  segmentationId: string
  image: { width: number; height: number }
  segments: Segment[]
}

export interface IdentifyApiResponse {
  image?: { width: number; height: number }
  imageData?: string
  candidates?: CoralCandidate[]
}

export interface CoralCandidate {
  id: string
  coralId: string
  monitoringSessionDate: string
  visualSimilarity: number
  diveSite: string
  imageUrl?: string
}
