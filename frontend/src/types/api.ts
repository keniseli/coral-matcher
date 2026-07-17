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
  coralName: string
  monitoringSessionDate: string
  visualSimilarity: number
  diveSite: string
  // backend returns the cropped image to save a bit of bandwith 
  // and show more relevant content in small space of candidate card
  imageUrl?: string
}
