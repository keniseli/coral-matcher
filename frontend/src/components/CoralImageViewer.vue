<template>
  <div class="relative overflow-hidden rounded-[28px] border border-slate-800 bg-slate-950/95 shadow-inner shadow-slate-950">
    <img
      v-if="imageSrc"
      :src="imageSrc"
      ref="imgRef"
      class="block h-auto w-full object-contain"
      @load="onLoad"
      alt="Uploaded coral"
    />

    <div v-else class="flex h-[560px] items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(52,211,153,0.16),_transparent_55%),#0f172a] text-slate-400">
      <div class="space-y-2 text-center">
        <p class="text-lg font-semibold text-slate-100">Upload an image to begin</p>
        <p class="text-sm text-slate-400">Segment polygons will appear over the image canvas.</p>
      </div>
    </div>

    <svg
      v-if="imageSize.width && imageSize.height && segments.length"
      :viewBox="`0 0 ${imageSize.width} ${imageSize.height}`"
      class="absolute inset-0 h-full w-full"
    >
      <g>
        <segment-polygon
          v-for="seg in orderedSegments"
          :key="seg.id"
          :segment="seg"
          :selected="selectedSegmentIds.has(seg.id)"
          :polygonOpacity="polygonOpacity"
          @toggle="() => $emit('toggleSegment', seg.id)"
        />
      </g>
    </svg>
  </div>
</template>

<script lang="ts">
import { computed, defineComponent, ref } from 'vue'
import SegmentPolygon from './SegmentPolygon.vue'
import type { Segment } from '../types/segment'
import type { Point } from '../types/geometry'

export default defineComponent({
  components: { SegmentPolygon },
  props: {
    imageSrc: { type: String, required: false },
    segments: { type: Array as () => Segment[], default: () => [] },
    selectedSegmentIds: { type: Object as () => Set<number>, required: true },
    polygonOpacity: { type: Number, default: 0.75 }
  },
  emits: ['toggleSegment'],
  setup(props) {
    const imgRef = ref<HTMLImageElement | null>(null)
    const imageSize = ref({ width: 0, height: 0 })

    const onLoad = () => {
      if (!imgRef.value) return
      imageSize.value.width = imgRef.value.naturalWidth
      imageSize.value.height = imgRef.value.naturalHeight
    }

    const polygonArea = (polygon: Point[]) => {
      if (!polygon || polygon.length < 3) return 0
      let area = 0
      for (let i = 0; i < polygon.length; i += 1) {
        const current = polygon[i]
        const next = polygon[(i + 1) % polygon.length]
        area += current.x * next.y - next.x * current.y
      }
      return Math.abs(area / 2)
    }

    const orderedSegments = computed(() => {
      return [...props.segments].sort((a, b) => polygonArea(a.polygon as Point[]) - polygonArea(b.polygon as Point[]))
    })

    return { imgRef, imageSize, onLoad, orderedSegments }
  }
})
</script>
