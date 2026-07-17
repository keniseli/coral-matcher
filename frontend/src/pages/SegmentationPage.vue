<template>
  <main class="min-h-screen overflow-auto bg-[#071116] p-5 text-slate-100
              xl:h-screen xl:overflow-hidden">
    <div class="mx-auto flex h-full max-w-[1800px] min-h-0 flex-col">
      <header class="mb-4 flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h1 class="text-3xl font-bold">Coral Matcher</h1>
          <p class=" text-xs text-slate-500">
            Identify and find monitored colonies
          </p>
        </div>
        <div>
          <div v-if="error" class="
              relative mb-3 rounded-md border border-red-400 bg-red-950 px-4 py-3 pr-10 text-sm text-red-100
              ">
            <span>{{ error }}</span>
            <button @click="error = ''" class="absolute right-3 top-3 text-red-200 transition hover:text-white"
              aria-label="Dismiss">
              ✕
            </button>
          </div>
          <div v-if="info" class="
              relative mb-3 rounded-md border border-white-400 bg-blue-950 px-4 py-3 pr-10 text-sm text-red-100
              ">
            <span>{{ info }}</span>
            <button @click="info = ''" class="absolute right-3 top-3 text-white-200 transition hover:text-white"
              aria-label="Dismiss">
              ✕
            </button>
          </div>
          <div v-if="success" class="
              relative mb-3 rounded-md border border-green-400 bg-green-95 px-4 py-3 pr-10 text-sm text-red-100
              ">
            <span>{{ success }}</span>
            <button @click="success = ''" class="absolute right-3 top-3 text-green-200 transition hover:text-white"
              aria-label="Dismiss">
              ✕
            </button>
          </div>
        </div>
      </header>
      <div class="grid min-h-0 flex-1 gap-4 xl:grid-cols-[3fr_2fr]">
        <section class="flex min-h-0 flex-col overflow-hidden rounded-xl border border-slate-800 bg-[#0b181e]">
          <div class="flex items-center justify-between border-b border-slate-800 px-4 py-3
                      grid grid-cols-[2fr_2fr_1fr_1fr] text-xs">
            <div>
              <p class="text-xs text-slate-500">
                Select every segment that belongs to one colony or choose from past observations. Drop image to start
              </p>
            </div>
            <div class="flex flex-col items-center gap-3">
              <span class="text-slate-400">
                <b class="text-slate-200">{{ selected.size }}</b> of
                {{ segments.length }} segments selected
              </span>
              <button :disabled="!selected.size || loading.identify"
                class="rounded bg-teal-400 px-3 py-2 font-semibold text-[#062126] disabled:opacity-40"
                @click="identify">
                {{
                  loading.identify
                    ? "Finding candidates..."
                    : "Find coral colony for selection"
                }}
              </button>
            </div>
            <div class="flex flex-col text-slate-400 gap-3">
              <label>Opacity: <span class="text-slate-200"><b>{{ Math.round(opacity * 100) }}%</b></span></label>
              <input v-model.number="opacity" type="range" min="0" max="1" step=".05" class="w-20 accent-teal-400" />
            </div>
            <div class="ml-auto">
              <button class="rounded border border-slate-700 px-3 py-1.5 hover:bg-slate-800" @click="picker?.click()">
                New Image</button>
              <input ref="picker" class="hidden" type="file" accept="image/*" @change="picked" />
            </div>
          </div>
          <div class="relative flex min-h-[540px] flex-1 items-center justify-center bg-black/40 p-3" @dragover.prevent
            @drop.prevent="dropped">
            <CoralImageViewer v-if="imageUrl" :image-src="imageUrl" :segments="segments" :selected="selected"
              :opacity="opacity" @toggle="toggle" />
            <div v-else class="text-center">
              <p class="text-base">Drop an image here</p>
              <p class="mt-2 text-sm text-slate-500">
                Segmentation overlays appear after segmentation results are calculated.
              </p>
              <button class="mt-4 rounded bg-teal-400 px-4 py-2 text-sm font-semibold text-[#062126]"
                @click="picker?.click()">
                Browse image
              </button>
            </div>
            <div v-if="loading.segment" class="absolute inset-0 flex items-center justify-center bg-[#071116]/45">
              <div class="rounded border border-slate-700 bg-[#0d1b21] px-5 py-4 text-center">
                <i class="mx-auto block h-5 w-5 rounded-full border-2 border-teal-300 border-t-transparent"></i>
                <p class="mt-2 text-sm">Segmenting image</p>
                <p class="text-xs text-slate-400">
                  This may take several minutes.
                </p>
              </div>
            </div>
          </div>
        </section>
        <aside class="flex min-h-0 flex-col overflow-hidden rounded-xl border border-slate-800 bg-[#0b181e]">
          <div class="border-b border-slate-800 bg-[#0e1d23] p-4">
            <h2 class="text-sm font-semibold">Potential matches</h2>
            <p class="mt-1 text-xs text-slate-500">
              Compare uploaded image with past observations
            </p>
            <div class="mt-3 grid grid-cols-2 gap-2 text-xs">
              <label>Dive site<select v-model="site"
                  class="mt-1 block w-full rounded border border-slate-700 bg-[#091419] p-2 text-slate-200">
                  <option>Isla Larga</option>
                  <option>Olohuita</option>
                </select></label><label>Coral Colony name<input v-model="name"
                  class="mt-1 w-full rounded border border-slate-700 bg-[#091419] p-2 text-slate-200" /></label>
            </div>
            <div
              class="mt-3 flex items-center justify-between rounded border border-slate-700 bg-[#091419] p-2 text-xs">
              <span>Selection:
                <b>{{ active?.coralName || "New Coral Colony" }}</b></span><button
                :disabled="!selected.size || loading.confirm"
                class="rounded bg-teal-400 px-3 py-1.5 font-semibold text-[#062126] disabled:opacity-40"
                @click="confirm">
                {{
                  loading.confirm
                    ? "Saving..."
                    : active
                      ? "Confirm match"
                      : "Save as new"
                }}
              </button>
            </div>
            <button v-if="active" class="mt-2 text-xs text-teal-300" @click="activeId = ''">
              Save as new coral instead
            </button>
          </div>
          <div class="min-h-0 flex-1 overflow-y-auto p-3">
            <div v-if="loading.segment || loading.identify"
              class="flex h-full min-h-[180px] flex-col items-center justify-center text-sm text-slate-400">
              <i class="h-5 w-5 rounded-full border-2 border-teal-300 border-t-transparent"></i>
              <p class="mt-3">Calculating possible matches...</p>
            </div>
            <p v-else-if="!imageUrl" class="mt-20 text-center text-sm text-slate-500">
              Upload an image to begin comparison.
            </p>
            <p v-else-if="!candidates.length" class="mt-20 text-center text-sm text-slate-500">
              No matching colonies found. You can save this observation as a new
              colony.
            </p>
            <button v-for="c in candidates" v-else :key="c.id"
              class="mb-2 grid w-full grid-cols-[130px_1fr] overflow-hidden rounded-lg border text-left" :class="activeId === c.id
                ? 'border-teal-400 bg-teal-400/10'
                : 'border-slate-800 bg-[#091419]'
                " @click="
                  activeId === c.id
                    ? activeId = ''
                    : activeId = c.id">
              <div class="flex h-[108px] items-center justify-center bg-slate-900">
                <img v-if="c.imageUrl" :src="c.imageUrl" class="h-full w-full object-contain" /><span v-else
                  class="text-xs text-slate-600">No preview</span>
              </div>
              <div class="p-3 text-xs">
                <b class="text-sm">{{ c.coralName }}</b>
                <p class="mt-2 text-teal-300">
                  Visual similarity {{ Math.round(c.visualSimilarity * 100) }}%
                </p>
                <p class="mt-1 text-slate-400">
                  Session {{ c.monitoringSessionDate }}
                </p>
                <p class="mt-1 text-slate-400">{{ c.diveSite }}</p>
              </div>
            </button>
          </div>
        </aside>
      </div>
    </div>
  </main>
</template>
<script setup lang="ts">
import { computed, reactive, ref } from "vue";
import CoralImageViewer from "../components/CoralImageViewer.vue";
import segmentation from "../services/segmentationService";
import identifyService from "../services/identificationService";
import type { Segment } from "../types/segment";
import type { CoralCandidate } from "../types/api";
const picker = ref<HTMLInputElement>();
const image = ref<File>();
const imageUrl = ref("");
const segments = ref<Segment[]>([]);
const selected = ref(new Set<number>());
const candidates = ref<CoralCandidate[]>([]);
const activeId = ref("");
const active = computed(() =>
  candidates.value.find((c) => c.id === activeId.value),
);
const opacity = ref(0.55);
const error = ref("");
const info = ref("");
const success = ref("");
const site = ref("Isla Larga");
const name = ref(`Coral-${crypto.randomUUID().slice(0, 5).toUpperCase()}`);
const loading = reactive({ segment: false, identify: false, confirm: false });
const toggle = (id: number) => {
  const next = new Set(selected.value);
  next.has(id) ? next.delete(id) : next.add(id);
  selected.value = next;
};
const MESSAGE_TYPE_INFO = "info";
const MESSAGE_TYPE_ERROR = "error";
const MESSAGE_TYPE_SUCCESS = "success";

const notify = (message: string, type: string) => {
  success.value = "";
  info.value = "";
  error.value = "";
  if (type === "error")
    error.value = message;
  else if (type === "success") {
    success.value = message;
  } else {
    info.value = message;
  }
}
const upload = async (file: File) => {
  if (!file.type.startsWith("image/"))
    return (error.value = "Please select an image file.");
  image.value = file;
  imageUrl.value = URL.createObjectURL(file);
  segments.value = [];
  selected.value = new Set();
  candidates.value = [];
  loading.segment = true;
  notify("Calculating Segments...", MESSAGE_TYPE_INFO);
  try {
    const uploadResult = await segmentation.segmentImage(file);
    segments.value = uploadResult.segments;
    candidates.value = uploadResult.observationCandidates
    notify("Segments Calculated", MESSAGE_TYPE_SUCCESS);
  } catch (e) {
    notify(e instanceof Error ? e.message : "Segmentation failed.", MESSAGE_TYPE_ERROR)
  } finally {
    loading.segment = false;
  }
};
const picked = (e: Event) => {
  const f = (e.target as HTMLInputElement).files?.[0];
  if (f) void upload(f);
};
const dropped = (e: DragEvent) => {
  const f = e.dataTransfer?.files[0];
  if (f) void upload(f);
};
const identify = async () => {
  if (!image.value) return;
  loading.identify = true;
  candidates.value = [];
  activeId.value = "";
  notify("Finding Candidates...", MESSAGE_TYPE_INFO);
  try {
    const r = await identifyService.identifyCoral(
      segments.value.filter((s) => selected.value.has(s.id)),
      image.value,
    );
    candidates.value = r.candidates ?? [];
    notify("Found " + candidates.value.length + " Candidates", MESSAGE_TYPE_SUCCESS);
  } catch (e) {
    notify(e instanceof Error ? e.message : "Could not find matches.", MESSAGE_TYPE_ERROR);
  } finally {
    loading.identify = false;
  }
};
const confirm = async () => {
  if (!image.value) return;
  loading.confirm = true;
  const tmpCandidates = candidates.value;
  const tmpActiveId = activeId.value;
  const tmpSelected = selected.value;
  notify("Saving Observation...", MESSAGE_TYPE_INFO);
  try {
    candidates.value = [];
    activeId.value = "";
    selected.value = new Set();
    await identifyService.confirmCoral({
      image: image.value,
      selectedSegments: segments.value.filter((s) => tmpSelected.has(s.id)),
      selectedCandidateId: tmpActiveId || null,
      diveSite: site.value,
      coralName: name.value,
    });
    notify("Coral " + name.value + " has been successfully saved", MESSAGE_TYPE_SUCCESS);
    name.value = `Coral-${crypto.randomUUID().slice(0, 5).toUpperCase()}`;
  } catch (e) {
    notify(e instanceof Error ? e.message : "Could not save Observation", MESSAGE_TYPE_ERROR);
    candidates.value = tmpCandidates;
    activeId.value = tmpActiveId;
    selected.value = tmpSelected;
  } finally {
    loading.confirm = false;
  }
};
</script>
