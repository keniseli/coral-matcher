<template>
  <g>
    <polygon
      :points="polygonPoints"
      :style="polygonStyle"
      @click.stop.prevent="onToggle"
      @mouseenter="hovered = true"
      @mouseleave="hovered = false"
      style="pointer-events: all; cursor: pointer; transition: all 180ms ease;"
    />
    <g v-if="hovered" class="pointer-events-none">
      <rect :x="labelX" :y="labelY" width="240" height="70" rx="12" fill="#020617e6" stroke="#38bdf8" stroke-width="1.3" />
      <text :x="labelX + 12" :y="labelY + 22" font-size="13" font-weight="700" fill="#f8fafc">ID: {{ segment.id }}</text>
      <text :x="labelX + 12" :y="labelY + 44" font-size="11" fill="#bae6fd">IoU {{ segment.predictedIoU.toFixed(2) }} · Stability {{ segment.stabilityScore.toFixed(2) }}</text>
    </g>
  </g>
</template>

<script lang="ts">
import { defineComponent, computed, ref } from 'vue'
import type { Segment } from '../types/segment'

export default defineComponent({
  props: {
    segment: { type: Object as () => Segment, required: true },
    selected: { type: Boolean, default: false },
    polygonOpacity: { type: Number, default: 0.75 }
  },
  emits: ['toggle'],
  setup(props, { emit }) {
    const hovered = ref(false)

    const polygonPoints = computed(() => {
      const pts = props.segment.polygon || []
      return pts.map((p: any) => `${Array.isArray(p) ? p[0] : p.x},${Array.isArray(p) ? p[1] : p.y}`).join(' ')
    })

    const polygonStyle = computed(() => {
      const strokeWidth = props.selected ? 3.2 : hovered.value ? 2.8 : 2
      const fill = props.selected ? '#43A047' : hovered.value ? '#FFB300' : '#4FC3F7'
      const stroke = props.selected ? '#1B5E20' : hovered.value ? '#EF6C00' : '#0288D1'
      return {
        fill,
        stroke,
        strokeWidth,
        fillOpacity: Math.max(0.2, props.polygonOpacity),
        opacity: 0.98,
      }
    })

    const onToggle = () => emit('toggle')

    const bbox = props.segment.bbox
    const labelX = bbox.x
    const labelY = Math.max(0, bbox.y - 72)

    return { polygonPoints, polygonStyle, onToggle, hovered, labelX, labelY }
  }
})
</script>
