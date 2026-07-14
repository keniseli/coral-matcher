import type { Segment } from './segment'

export interface SegmentApiResponse {
  segmentationId: string
  image: { width: number; height: number }
  segments: Segment[]
}

export interface IdentifyApiResponse {
  cropDataUrl?: string
  cropWidth?: number
  cropHeight?: number
  selectedSegments?: number[]
}
