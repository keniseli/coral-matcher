<template>
  <div
    class="relative h-full w-full overflow-hidden rounded-lg border border-slate-800"
  >
    <img
      v-if="imageSrc"
      ref="image"
      :src="imageSrc"
      class="block h-full w-full object-contain"
      @load="loaded"
    />
    <svg
      v-if="size.width"
      class="pointer-events-none absolute inset-0 h-full w-full"
      :viewBox="`0 0 ${size.width} ${size.height}`"
    >
      <SegmentPolygon
        v-for="segment in ordered"
        :key="segment.id"
        :segment="segment"
        :selected="selected.has(segment.id)"
        :opacity="opacity"
        class="pointer-events-auto"
        @toggle="$emit('toggle', segment.id)"
      />
    </svg>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import SegmentPolygon from "./SegmentPolygon.vue";
import type { Segment, SegmentPoint } from "../types/segment";

const props = defineProps<{
  imageSrc?: string;
  segments: Segment[];
  selected: Set<number>;
  opacity: number;
}>();

defineEmits<{ toggle: [id: number] }>();

const image = ref<HTMLImageElement>();
const size = ref({ width: 0, height: 0 });

const loaded = () => {
  size.value = {
    width: image.value!.naturalWidth,
    height: image.value!.naturalHeight,
  };
};

const coordinates = (point: SegmentPoint) =>
  Array.isArray(point) ? point : [point.x, point.y];

const area = (segment: Segment) =>
  Math.abs(
    segment.polygon.reduce((sum, point, index) => {
      const next = segment.polygon[(index + 1) % segment.polygon.length];
      const [x1, y1] = coordinates(point);
      const [x2, y2] = coordinates(next);
      return sum + x1 * y2 - x2 * y1;
    }, 0) / 2,
  );

const ordered = computed(() =>
  [...props.segments].sort((first, second) => area(first) - area(second)),
);
</script>
