<template>
  <div class="flex items-center gap-4">
    <label class="inline-flex cursor-pointer items-center gap-3 rounded-full border border-emerald-400/30 bg-gradient-to-r from-emerald-500 to-cyan-400 px-4 py-2 text-sm font-semibold text-slate-950 shadow-lg shadow-emerald-500/20 transition hover:scale-[1.01] hover:shadow-emerald-500/30">
      <input class="hidden" type="file" accept="image/*" @change="onFileChange" />
      <span>Upload image</span>
      <span class="inline-flex h-7 w-7 items-center justify-center rounded-full bg-white/90 text-emerald-600">+</span>
    </label>
    <div v-if="loading" class="text-sm text-slate-400">Processing image…</div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({
  props: {
    loading: { type: Boolean, default: false }
  },
  emits: ['on-file'],
  methods: {
    onFileChange(e: Event) {
      const target = e.target as HTMLInputElement
      if (!target.files || !target.files[0]) return
      this.$emit('on-file', target.files[0])
    }
  }
})
</script>
