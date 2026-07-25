<template>
  <polygon
    :points="points"
    :fill="color.fill"
    :stroke="color.stroke"
    :stroke-width="color.width"
    :fill-opacity="opacity"
    style="cursor: pointer"
    @click.stop="$emit('toggle')"
    @mouseenter="hover = true"
    @mouseleave="hover = false"
  />
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { SegmentPoint } from "../types/segment";

const props = defineProps<{
  segment: { polygon: SegmentPoint[] };
  selected: boolean;
  opacity: number;
}>();

defineEmits<{ toggle: [] }>();

const hover = ref(false);
const pointCoordinates = (point: SegmentPoint) =>
  Array.isArray(point) ? point : [point.x, point.y];

const points = computed(() =>
  props.segment.polygon
    .map((point) => pointCoordinates(point).join(","))
    .join(" "),
);

const color = computed(() =>
  props.selected
    ? { fill: "rgb(13 148 136)", stroke: "rgb(45 212 191)", width: 3.2 }
    : hover.value
      ? { fill: "#F26419", stroke: "#D4520C", width: 2.8 }
      : { fill: "#E5E1EE", stroke: "#5B4983", width: 2 },
);
</script>
