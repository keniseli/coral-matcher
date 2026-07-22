<template>
  <main class="min-h-screen overflow-auto bg-[#071116] p-5 text-slate-100 xl:h-screen xl:overflow-hidden">
    <div class="mx-auto flex h-full max-w-[1800px] min-h-0 flex-col">
      <header class="flex items-center justify-between border-slate-800 pb-2">
        <div>
          <h1 class="text-3xl font-bold">
            Coral Matcher
          </h1>

          <p class="text-xs text-slate-500">
            Identify and find monitored coral colonies
          </p>
        </div>

        <div>
          <div v-if="error"
            class="relative mb-3 rounded-md border border-red-400 bg-red-600/20 px-4 py-3 pr-10 text-sm text-red-100">
            <span>
              {{ error }}
            </span>

            <button class="absolute right-3 top-3 text-red-200 transition hover:text-white" aria-label="Dismiss"
              @click="error = ''">
              ✕
            </button>
          </div>

          <div v-if="info"
            class="relative mb-3 rounded-md border border-white-400 bg-slate-100/10 px-4 py-3 pr-10 text-sm text-red-100">
            <span>
              {{ info }}
            </span>

            <button class="absolute right-3 top-3 text-white-200 transition hover:text-white" aria-label="Dismiss"
              @click="info = ''">
              ✕
            </button>
          </div>

          <div v-if="success"
            class="relative mb-3 rounded-md border border-teal-400 bg-teal-600/20 px-4 py-3 pr-10 text-sm text-red-100">
            <span>
              {{ success }}
            </span>

            <button class="absolute right-3 top-3 text-green-200 transition hover:text-white" aria-label="Dismiss"
              @click="success = ''">
              ✕
            </button>
          </div>
        </div>
      </header>
      <div class="grid min-h-0 flex-1 gap-4 xl:grid-cols-[3fr_2fr]">
        <!-- Image / segmentation panel -->
        <section class="flex min-h-0 flex-col overflow-hidden rounded-xl border border-slate-800 bg-[#0b181e]">
          <div class="grid grid-cols-[2fr_2fr_1fr_1fr] items-center gap-4 border-b border-slate-800 px-4 py-3 text-xs">
            <div>
              <p class="text-xs text-slate-500">
                Select every segment that belongs to one colony or choose from
                past observations. Drop image to start
              </p>
            </div>

            <div class="flex flex-col items-center gap-3">
              <span class="text-slate-400">
                <b class="text-slate-200">
                  {{ selected.size }}
                </b>
                of
                {{ segments.length }}
                segments selected
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

            <div class="flex flex-col gap-3 text-slate-400">
              <label>
                Opacity:
                <span class="text-slate-200">
                  <b>
                    {{ Math.round(opacity * 100) }}%
                  </b>
                </span>
              </label>

              <input v-model.number="opacity" type="range" min="0" max="1" step=".05" class="w-20 accent-teal-400" />
            </div>

            <div class="ml-auto">
              <button class="rounded border border-slate-700 px-3 py-1.5 hover:bg-slate-800" @click="picker?.click()">
                New Image
              </button>

              <input ref="picker" class="hidden" type="file" accept="image/*" @change="picked" />
            </div>
          </div>

          <div class="relative flex min-h-[540px] flex-1 items-center justify-center bg-black/40 p-3" @dragover.prevent
            @drop.prevent="dropped">
            <CoralImageViewer v-if="imageUrl" :image-src="imageUrl" :segments="segments" :selected="selected"
              :opacity="opacity" @toggle="toggle" />

            <div v-else class="text-center">
              <p class="text-base">
                Drop an image here
              </p>

              <p class="mt-2 text-sm text-slate-500">
                Segmentation overlays appear after segmentation results are
                calculated.
              </p>

              <button class="mt-4 rounded bg-teal-400 px-4 py-2 text-sm font-semibold text-[#062126]"
                @click="picker?.click()">
                Browse image
              </button>
            </div>

            <div v-if="loading.segment || loading.identify"
              class="absolute inset-0 flex items-center justify-center bg-[#071116]/45">
              <div class="rounded border border-slate-700 bg-[#0d1b21] px-5 py-4 text-center">
                <i
                  class="mx-auto block h-5 w-5 rounded-full border-2 border-teal-300 border-t-transparent animate-spin"></i>

                <p class="mt-2 text-sm">
                  Segmenting image
                </p>

                <p class="text-xs text-slate-400">
                  This may take several minutes.
                </p>
              </div>
            </div>
          </div>
        </section>

        <!-- Monitoring Session Selector-->
        <div>
          <MonitoringSessionSelector v-model="selectedMonitoringSession" class="mb-2" />
          <!-- Candidates -->
          <CandidatesPanel :image-url="imageUrl" :candidates="candidates" :selected-count="selected.size"
            :loading-segment="loading.segment" :loading-identify="loading.identify" :loading-confirm="loading.confirm"
            @confirm="confirm" />
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import {
  reactive,
  ref,
} from "vue";

import CoralImageViewer from "../components/CoralImageViewer.vue";
import CandidatesPanel from "../components/CandidatesPanel.vue";
import MonitoringSessionSelector from "../components/MonitoringSessionSelector.vue";

import segmentation from "../services/segmentationService";
import identifyService from "../services/identificationService";

import type { Segment } from "../types/segment";
import type { CoralCandidate } from "../types/api";
import type { MonitoringSession } from "../types/monitoringSession.js";

const picker = ref<HTMLInputElement>();

const image = ref<File>();
const imageUrl = ref("");

const segments = ref<Segment[]>([]);
const selected = ref(new Set<number>());

const candidates = ref<CoralCandidate[]>([]);

const opacity = ref(0.55);

const error = ref("");
const info = ref("");
const success = ref("");

const loading = reactive({
  segment: false,
  identify: false,
  confirm: false,
});

const selectedMonitoringSession = ref<MonitoringSession | null>(null);

const toggle = (id: number) => {
  const next = new Set(selected.value);

  next.has(id)
    ? next.delete(id)
    : next.add(id);

  selected.value = next;
};

const MESSAGE_TYPE_INFO = "info";
const MESSAGE_TYPE_ERROR = "error";
const MESSAGE_TYPE_SUCCESS = "success";

const notify = (
  message: string,
  type: string,
) => {
  success.value = "";
  info.value = "";
  error.value = "";

  if (type === MESSAGE_TYPE_ERROR) {
    error.value = message;
  } else if (type === MESSAGE_TYPE_SUCCESS) {
    success.value = message;
  } else {
    info.value = message;
  }
};

const updateCandidates = (
  nextCandidates: CoralCandidate[],
) => {
  candidates.value = nextCandidates;
};

const upload = async (
  file: File,
) => {
  if (!file.type.startsWith("image/")) {
    error.value = "Please select an image file.";
    return;
  }

  image.value = file;
  imageUrl.value = URL.createObjectURL(file);

  segments.value = [];
  selected.value = new Set();
  candidates.value = [];

  loading.segment = true;

  notify(
    "Calculating Segments...",
    MESSAGE_TYPE_INFO,
  );

  try {
    const uploadResult =
      await segmentation.segmentImage(file);

    segments.value =
      uploadResult.segments;

    updateCandidates(
      uploadResult.observationCandidates,
    );

    notify(
      "Segments Calculated",
      MESSAGE_TYPE_SUCCESS,
    );
  } catch (e) {
    notify(
      e instanceof Error
        ? e.message
        : "Segmentation failed.",
      MESSAGE_TYPE_ERROR,
    );
  } finally {
    loading.segment = false;
  }
};

const picked = (
  e: Event,
) => {
  const file =
    (e.target as HTMLInputElement)
      .files?.[0];

  if (file) {
    void upload(file);
  }
};

const dropped = (
  e: DragEvent,
) => {
  const file =
    e.dataTransfer?.files[0];

  if (file) {
    void upload(file);
  }
};

const identify = async () => {
  if (!image.value) {
    return;
  }

  loading.identify = true;

  notify(
    `Finding Candidates for ${selected.value.size} Segments...`,
    MESSAGE_TYPE_INFO,
  );

  try {
    const result =
      await identifyService.identifyCoralBySegments(
        segments.value.filter(
          (segment) =>
            selected.value.has(segment.id),
        ),
        image.value,
      );

    updateCandidates(
      result.candidates ?? [],
    );

    notify(`Found ${result.candidates?.length ?? 0} Candidates`, MESSAGE_TYPE_SUCCESS);
  } catch (e) {
    notify(e instanceof Error ? e.message : "Could not find matches.", MESSAGE_TYPE_ERROR);
  } finally {
    loading.identify = false;
  }
};

type ConfirmPayload = {
  selectedCandidateId: string | null;
  diveSite: string;
  coralName: string;
};

const confirm = async (
  payload: ConfirmPayload,
) => {
  if (!image.value) {
    return;
  }

  loading.confirm = true;

  const previousCandidates = candidates.value;
  const previousSelected = selected.value;

  notify("Saving Observation...", MESSAGE_TYPE_INFO);

  try {
    candidates.value = [];
    selected.value = new Set();

    await identifyService.confirmCoral({
      image: image.value,
      selectedSegments: segments.value.filter((segment) => previousSelected.has(segment.id)),
      selectedCandidateId: payload.selectedCandidateId,
      diveSite: payload.diveSite,
      coralName: payload.coralName,
    });

    notify(`Observation for ${payload.coralName} has been successfully saved`, MESSAGE_TYPE_SUCCESS);
  } catch (e) {
    notify(e instanceof Error ? e.message : "Could not save Observation", MESSAGE_TYPE_ERROR);
    candidates.value = previousCandidates;
    selected.value = previousSelected;
  } finally {
    loading.confirm = false;
  }
};
</script>