<template>
  <g>
    <polygon
      :points="polygonPoints"
      :class="baseClass"
      @click.stop.prevent="onToggle"
      @mouseenter="hovered = true"
      @mouseleave="hovered = false"
      style="pointer-events: all; transition: all 150ms ease;"
    />
    <g v-if="hovered" class="pointer-events-none">
      <rect :x="labelX" :y="labelY" width="140" height="32" rx="4" fill="#ffffffcc" stroke="#0ea5e9" />
      <text :x="labelX + 8" :y="labelY + 16" font-size="12" fill="#0b1224">ID: {{ segment.id }}</text>
    </g>
  </g>
</template>

<script lang="ts">
import { defineComponent, computed, ref } from 'vue'
import type { Segment } from '../types/segment'

export default defineComponent({
  props: {
    segment: { type: Object as () => Segment, required: true },
    selected: { type: Boolean, default: false }
  },
  emits: ['toggle'],
  setup(props, { emit }) {
    const hovered = ref(false)
    // API returns polygon as array of [x, y] pairs. Keep this simple and fast.
    const polygonPoints = computed(() => {
      const pts = props.segment.polygon || []
      return pts.map((p: number[]) => `${p[0]},${p[1]}`).join(' ')
    })

    const baseClass = computed(() => {
      if (props.selected) return 'fill-green-400 stroke-green-700 stroke-2 opacity-60'
      if (hovered.value) return 'fill-blue-400 stroke-blue-700 stroke-2 opacity-40'
      return 'fill-blue-300 stroke-blue-500 stroke-1 opacity-25'
    })

    const onToggle = () => emit('toggle')

    const bbox = props.segment.bbox
    const labelX = bbox.x
    const labelY = Math.max(0, bbox.y - 36)

    return { polygonPoints, baseClass, onToggle, hovered, labelX, labelY }
  }
})
</script>
