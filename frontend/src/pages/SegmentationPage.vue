<template>
  <div class="min-h-screen bg-slate-50 p-6">
    <div class="max-w-6xl mx-auto">
      <upload-toolbar @on-file="handleFile" :loading="loading.segmenting" />

      <div class="mt-6 grid grid-cols-3 gap-4">
        <div class="col-span-2 bg-white rounded shadow p-4">
          <coral-image-viewer
            :imageSrc="imageSrc"
            :segments="segments"
            :selectedSegmentIds="selectedSegmentIds"
            @toggleSegment="toggleSegment"
          />
        </div>

        <div class="col-span-1 bg-white rounded shadow p-4">
          <h3 class="font-semibold mb-2">Candidate Area</h3>
          <crop-preview :cropSrc="cropSrc" />
          <div class="mt-4">
            <button
              class="px-4 py-2 rounded bg-green-500 text-white disabled:opacity-50"
              :disabled="!canIdentify || loading.identifying"
              @click="confirmSelection"
            >
              {{ loading.identifying ? 'Identifying…' : 'Confirm Selection' }}
            </button>
          </div>
          <div v-if="error" class="mt-4 text-red-600">{{ error }}</div>
          <div class="mt-4 text-sm text-gray-400">Candidate matches will appear here.</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, computed } from 'vue'
import UploadToolbar from '../components/UploadToolbar.vue'
import CoralImageViewer from '../components/CoralImageViewer.vue'
import CropPreview from '../components/CropPreview.vue'
import segmentationService from '../services/segmentationService'
import identificationService from '../services/identificationService'
import type { Segment } from '../types/segment'

export default defineComponent({
  components: { UploadToolbar, CoralImageViewer, CropPreview },
  setup() {
    const segments = ref<Segment[]>([])
    const imageSrc = ref<string | null>(null)
    const segmentationId = ref<string | null>(null)
    const selectedSegmentIds = ref(new Set<number>())
    const cropSrc = ref<string | null>(null)
    const loading = reactive({ segmenting: false, identifying: false })
    const error = ref<string | null>(null)

    const handleFile = async (file: File) => {
      error.value = null
      loading.segmenting = true
      segments.value = []
      imageSrc.value = null
      segmentationId.value = null
      selectedSegmentIds.value = new Set()
      cropSrc.value = null

      try {
        const res = await segmentationService.segmentImage(file)
        segmentationId.value = res.segmentationId
        imageSrc.value = URL.createObjectURL(file)
        segments.value = res.segments
      } catch (err: any) {
        error.value = err?.message || 'Segmentation failed.'
      } finally {
        loading.segmenting = false
      }
    }

    const toggleSegment = (id: number) => {
      const s = selectedSegmentIds.value
      if (s.has(id)) s.delete(id)
      else s.add(id)
      // trigger ref update
      selectedSegmentIds.value = new Set(s)
    }

    const canIdentify = computed(() => {
      return !!segmentationId.value && selectedSegmentIds.value.size > 0
    })

    const confirmSelection = async () => {
      if (!segmentationId.value) return
      loading.identifying = true
      error.value = null
      cropSrc.value = null
      try {
        const selected = Array.from(selectedSegmentIds.value)
        const res = await identificationService.identifyCoral(segmentationId.value, selected)
        // If API returns a data URL or path, show it. Otherwise show a placeholder.
        if ((res as any).cropDataUrl) cropSrc.value = (res as any).cropDataUrl
        else cropSrc.value = null
      } catch (err: any) {
        error.value = err?.message || 'Identification failed.'
      } finally {
        loading.identifying = false
      }
    }

    return {
      segments,
      imageSrc,
      selectedSegmentIds,
      cropSrc,
      loading,
      error,
      handleFile,
      toggleSegment,
      confirmSelection,
      canIdentify,
    }
  }
})
</script>
