<template>
  <div class="flex items-center gap-4">
    <label class="cursor-pointer inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded">
      <input class="hidden" type="file" accept="image/*" @change="onFileChange" />
      Upload Image
    </label>
    <div v-if="loading" class="text-sm text-gray-600">Processing…</div>
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
