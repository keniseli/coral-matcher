<template>
  <div class="relative">
    <img v-if="imageSrc" :src="imageSrc" ref="imgRef" class="max-w-full h-auto block" @load="onLoad" />
    <div v-else class="w-full h-96 bg-gray-100 flex items-center justify-center text-gray-400">No image</div>

    <svg v-if="imageSize.width && imageSize.height && segments.length" :viewBox="`0 0 ${imageSize.width} ${imageSize.height}`" class="absolute inset-0 w-full h-full pointer-events-none">
      <g>
        <segment-polygon
          v-for="seg in segments"
          :key="seg.id"
          :segment="seg"
          :selected="selectedSegmentIds.has(seg.id)"
          @toggle="() => $emit('toggleSegment', seg.id)"
        />
      </g>
    </svg>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, watch, onMounted } from 'vue'
import SegmentPolygon from './SegmentPolygon.vue'
import type { Segment } from '../types/segment'

export default defineComponent({
  components: { SegmentPolygon },
  props: {
    imageSrc: { type: String, required: false },
    segments: { type: Array as () => Segment[], default: () => [] },
    selectedSegmentIds: { type: Object as () => Set<number>, required: true }
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

    return { imgRef, imageSize, onLoad }
  }
})
</script>
