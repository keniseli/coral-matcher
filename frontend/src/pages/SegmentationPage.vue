<template>
  <div class="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(16,185,129,0.18),_transparent_30%),linear-gradient(135deg,_#020617_0%,_#0f172a_100%)] p-4 text-slate-100 sm:p-6 lg:p-8">
    <div class="mx-auto max-w-7xl">
      <section class="rounded-[32px] border border-slate-800 bg-slate-900/85 p-6 shadow-[0_24px_80px_-32px_rgba(2,6,23,0.95)] backdrop-blur-xl">
        <div class="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div class="max-w-2xl">
            <p class="text-sm font-semibold uppercase tracking-[0.35em] text-emerald-400">Coral Matcher</p>
            <h1 class="mt-2 text-3xl font-semibold tracking-tight text-white sm:text-4xl">Interactive segmentation workspace</h1>
            <p class="mt-3 text-sm leading-6 text-slate-400 sm:text-base">Drop an image into the workspace, inspect every polygon overlay, and pick the best coral geometry with a polished, dark-mode flow.</p>
          </div>

          <div class="grid gap-3 sm:grid-cols-2">
            <div class="rounded-2xl border border-slate-800 bg-slate-950/90 px-4 py-3 text-sm text-slate-100">
              <p class="text-[11px] uppercase tracking-[0.3em] text-slate-500">Session</p>
              <p class="mt-2 font-semibold">{{ segmentationId || 'Waiting for upload' }}</p>
            </div>
            <div class="rounded-2xl border border-slate-800 bg-slate-950/90 px-4 py-3 text-sm text-slate-100">
              <p class="text-[11px] uppercase tracking-[0.3em] text-slate-500">Selection</p>
              <p class="mt-2 font-semibold">{{ selectedSegmentIds.size }} / {{ segments.length }}</p>
            </div>
          </div>
        </div>
      </section>

      <div class="mt-6 grid gap-6 xl:grid-cols-[1.55fr_0.9fr]">
        <section class="overflow-hidden rounded-[32px] border border-slate-800 bg-slate-900/85 p-5 shadow-[0_20px_70px_-35px_rgba(2,6,23,0.95)] backdrop-blur-xl">
          <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h2 class="text-xl font-semibold text-white">Coral image workspace</h2>
              <p class="mt-1 text-sm text-slate-400">Drag and drop an image into the canvas, hover polygons for readable details, and click to select or deselect them.</p>
            </div>

            <div class="flex flex-wrap items-center gap-3">
              <label class="flex items-center gap-3 rounded-full border border-slate-700 bg-slate-950/90 px-3 py-2 text-sm font-medium text-slate-200 shadow-sm">
                <span>Opacity</span>
                <input v-model.number="polygonOpacity" class="h-2 w-24 cursor-pointer appearance-none rounded-full bg-slate-800 accent-emerald-500" type="range" min="0.2" max="1" step="0.05" />
                <span class="min-w-[3rem] text-right text-emerald-400">{{ polygonOpacity.toFixed(2) }}</span>
              </label>
              <upload-toolbar @on-file="handleFile" :loading="loading.segmenting" />
            </div>
          </div>

          <div
            class="relative mt-6 overflow-hidden rounded-[30px] border border-slate-800 bg-slate-950/95 p-4 min-h-[560px]"
            @dragover.prevent="handleDragOver"
            @dragleave.prevent="handleDragLeave"
            @drop.prevent="handleDrop"
          >
            <div v-if="isDragging" class="absolute inset-4 z-20 flex items-center justify-center rounded-[24px] border border-dashed border-emerald-400/70 bg-slate-950/95 text-center shadow-2xl shadow-emerald-500/10">
              <div class="space-y-2">
                <p class="text-lg font-semibold text-white">Drop image here</p>
                <p class="text-sm text-slate-400">The segmentation overlays appear directly in this workspace.</p>
              </div>
            </div>

            <coral-image-viewer
              :imageSrc="imageSrc || undefined"
              :segments="segments"
              :selectedSegmentIds="selectedSegmentIds"
              :polygonOpacity="polygonOpacity"
              @toggleSegment="toggleSegment"
            />

            <div v-if="!imageSrc && !loading.segmenting" class="absolute inset-0 flex items-center justify-center bg-slate-950/80 p-6">
              <div class="max-w-md rounded-[28px] border border-slate-800 bg-slate-900/90 p-8 text-center shadow-2xl shadow-slate-950/40">
                <div class="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-300">
                  <span class="text-2xl">⬆</span>
                </div>
                <p class="mt-4 text-base font-medium text-white">Drop an image into this workspace</p>
                <p class="mt-2 text-sm text-slate-400">Polygons appear here after the backend finishes segmentation.</p>
                <button class="mt-5 rounded-2xl bg-emerald-500 px-4 py-2 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400" @click="openFilePicker" type="button">
                  Choose image
                </button>
                <input ref="fileInput" class="hidden" type="file" accept="image/*" @change="handleInputChange" />
              </div>
            </div>

            <div v-if="loading.segmenting" class="absolute inset-0 flex items-center justify-center bg-slate-950/75">
              <div class="rounded-3xl border border-slate-800 bg-slate-900/90 px-6 py-5 text-center text-slate-300 shadow-2xl shadow-slate-950/40">
                <div class="mx-auto inline-flex h-10 w-10 items-center justify-center rounded-full bg-slate-800 text-emerald-400">
                  <span class="block h-4 w-4 animate-pulse rounded-full bg-current"></span>
                </div>
                <p class="mt-4 text-sm">Processing the image and extracting segment polygons…</p>
              </div>
            </div>
          </div>
        </section>

        <aside class="space-y-6">
          <section class="rounded-[32px] border border-slate-800 bg-slate-900/85 p-5 shadow-[0_20px_70px_-35px_rgba(2,6,23,0.95)] backdrop-blur-xl">
            <h2 class="text-lg font-semibold text-white">Selection summary</h2>
            <p class="mt-2 text-sm leading-6 text-slate-400">Pick the segment geometry that best matches the coral before confirming the crop.</p>
            <div class="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
              <div class="rounded-2xl border border-slate-800 bg-slate-950/90 p-4 text-slate-100">
                <p class="text-[11px] uppercase tracking-[0.3em] text-slate-500">Total segments</p>
                <p class="mt-2 text-3xl font-semibold text-white">{{ segments.length }}</p>
              </div>
              <div class="rounded-2xl border border-slate-800 bg-slate-950/90 p-4 text-slate-100">
                <p class="text-[11px] uppercase tracking-[0.3em] text-slate-500">Image size</p>
                <p class="mt-2 text-sm text-slate-300">{{ imageWidth }} × {{ imageHeight }}</p>
              </div>
            </div>
          </section>

          <section class="rounded-[32px] border border-slate-800 bg-slate-900/85 p-5 shadow-[0_20px_70px_-35px_rgba(2,6,23,0.95)] backdrop-blur-xl">
            <div class="flex items-center justify-between gap-3">
              <div>
                <h2 class="text-lg font-semibold text-white">Crop preview</h2>
                <p class="mt-1 text-sm text-slate-400">The selected crop appears instantly after confirmation.</p>
              </div>
            </div>
            <div class="mt-5 rounded-[24px] border border-slate-800 bg-slate-950/90 p-3">
              <crop-preview :cropSrc="cropSrc || undefined" />
            </div>
            <div v-if="error" class="mt-4 rounded-2xl border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-200">{{ error }}</div>
            <button
              class="mt-5 w-full rounded-2xl bg-emerald-500 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-60"
              :disabled="!canIdentify || loading.identifying"
              @click="confirmSelection"
            >
              {{ loading.identifying ? 'Identifying…' : 'Confirm selection' }}
            </button>
          </section>
        </aside>
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
    const imageSize = ref({ width: 0, height: 0 })
    const isDragging = ref(false)
    const fileInput = ref<HTMLInputElement | null>(null)
    const polygonOpacity = ref(0.75)

    const handleFile = async (file: File) => {
      error.value = null
      loading.segmenting = true
      segments.value = []
      imageSrc.value = null
      segmentationId.value = null
      selectedSegmentIds.value = new Set()
      cropSrc.value = null
      imageSize.value = { width: 0, height: 0 }

      try {
        const res = await segmentationService.segmentImage(file)
        segmentationId.value = res.segmentationId
        imageSrc.value = URL.createObjectURL(file)
        segments.value = res.segments
        imageSize.value = {
          width: res.image.width,
          height: res.image.height,
        }
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
      selectedSegmentIds.value = new Set(s)
    }

    const canIdentify = computed(() => !!segmentationId.value && selectedSegmentIds.value.size > 0)

    const confirmSelection = async () => {
      if (!segmentationId.value) return
      loading.identifying = true
      error.value = null
      cropSrc.value = null

      try {
        const selected = Array.from(selectedSegmentIds.value)
        const res = await identificationService.identifyCoral(segmentationId.value, selected)
        cropSrc.value = (res as any).cropDataUrl ?? null
      } catch (err: any) {
        error.value = err?.message || 'Identification failed.'
      } finally {
        loading.identifying = false
      }
    }

    const imageWidth = computed(() => imageSize.value.width || 0)
    const imageHeight = computed(() => imageSize.value.height || 0)

    const openFilePicker = () => fileInput.value?.click()
    const handleDragOver = () => { isDragging.value = true }
    const handleDragLeave = () => { isDragging.value = false }
    const handleDrop = (event: DragEvent) => {
      isDragging.value = false
      const file = event.dataTransfer?.files?.[0]
      if (file && file.type.startsWith('image/')) void handleFile(file)
    }
    const handleInputChange = (event: Event) => {
      const target = event.target as HTMLInputElement
      const file = target.files?.[0]
      if (file) void handleFile(file)
      target.value = ''
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
      imageWidth,
      imageHeight,
      segmentationId,
      isDragging,
      fileInput,
      polygonOpacity,
      openFilePicker,
      handleDragOver,
      handleDragLeave,
      handleDrop,
      handleInputChange,
    }
  }
})
</script>
