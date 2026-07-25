import type { BoundingBox, Point } from "./geometry";

export type SegmentPoint = Point | [number, number];

export interface Segment {
  id: number;
  polygon: SegmentPoint[];
  bbox: BoundingBox;
  predictedIoU: number;
  stabilityScore: number;
}
