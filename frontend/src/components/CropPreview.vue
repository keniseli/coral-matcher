<template>
  <div class="flex min-h-[220px] items-center justify-center overflow-hidden rounded-[24px] border border-slate-800 bg-slate-950/95 p-3 shadow-inner shadow-slate-950/30">
    <div v-if="cropSrc" class="flex h-full w-full items-center justify-center rounded-[20px] bg-slate-900/70 p-2">
      <img :src="cropSrc" class="max-h-[260px] w-full rounded-[16px] object-contain shadow-lg shadow-slate-950/20" />
    </div>
    <div v-else class="rounded-[20px] border border-dashed border-slate-700 bg-slate-900/70 px-6 py-8 text-center text-sm text-slate-500">
      No crop yet.
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({ props: { cropSrc: { type: String, required: false } } })
</script>
