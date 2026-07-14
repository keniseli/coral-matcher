import type { Point, BoundingBox } from './geometry'

export interface Segment {
  id: number
  polygon: Point[]
  bbox: BoundingBox
  predictedIoU: number
  stabilityScore: number
}
