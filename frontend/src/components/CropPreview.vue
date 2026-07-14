<template>
  <div class="border rounded p-2 min-h-[160px] flex items-center justify-center">
    <div v-if="cropSrc">
      <img :src="cropSrc" class="max-w-full h-auto" />
    </div>
    <div v-else class="text-gray-400">No crop yet.</div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'

export default defineComponent({ props: { cropSrc: { type: String, required: false } } })
</script>
