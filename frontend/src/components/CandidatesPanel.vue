<template>
  <aside
    class="flex min-h-0 flex-col overflow-hidden rounded-xl border border-slate-800 bg-[#0b181e]"
  >
    <!-- Candidate controls -->
    <div class="border-b border-slate-800 bg-[#0e1d23] p-4">
      <h2 class="text-sm font-semibold">
        Candidates
      </h2>

      <p class="mt-1 text-xs text-slate-500">
        Compare uploaded image with past observations
      </p>

      <div class="mt-3 grid grid-cols-2 gap-2 text-xs">
        <label>
          Dive site

          <select
            v-model="site"
            class="mt-1 block w-full rounded border border-slate-700 bg-[#091419] p-2 text-slate-200"
          >
            <option>Isla Larga</option>
            <option>Olohuita</option>
          </select>
        </label>

        <label>
          Coral Colony name

          <input
            v-model="name"
            class="mt-1 w-full rounded border border-slate-700 bg-[#091419] p-2 text-slate-200"
          />
        </label>
      </div>

      <div
        class="mt-3 flex items-center justify-between rounded border border-slate-700 bg-[#091419] p-2 text-xs"
      >
        <span>
          Selection:
          <b>
            {{ active?.coralName || "New Coral Colony" }}
          </b>
        </span>

        <button
          :disabled="!selectedCount || loadingConfirm"
          class="rounded bg-teal-400 px-3 py-1.5 font-semibold text-[#062126] disabled:opacity-40"
          @click="confirm"
        >
          {{
            loadingConfirm
              ? "Saving..."
              : active
                ? "Confirm match"
                : "Save as new"
          }}
        </button>
      </div>

      <button v-if="active" class="mt-2 text-xs text-teal-300" @click="deselectCandidate">
        Deselect Candidate
      </button>
    </div>

    <!-- Candidate list -->
    <div class="min-h-0 flex-1 overflow-y-auto p-3">
      <div
        v-if="loadingSegment || loadingIdentify"
        class="flex h-full min-h-[180px] flex-col items-center justify-center text-sm text-slate-400"
      >
        <i
          class="h-5 w-5 rounded-full border-2 border-teal-300 border-t-transparent animate-spin"
        ></i>

        <p class="mt-3">
          Calculating possible matches...
        </p>
      </div>

      <p
        v-else-if="!imageUrl"
        class="mt-20 text-center text-sm text-slate-500"
      >
        Upload an image to begin comparison.
      </p>

      <p
        v-else-if="!coralObservations.length"
        class="mt-20 text-center text-sm text-slate-500"
      >
        No matching colonies found. You can save this observation as a new
        colony.
      </p>

      <button
        v-for="coralObservation in coralObservations"
        v-else
        :key="coralObservation.coralName"
        class="mb-1 w-full overflow-hidden rounded-lg border text-left"
        :class="
          activeId === coralObservation.coralName
            ? 'border-teal-400 bg-teal-400/10'
            : 'border-slate-800 bg-[#091419]'
        "
        @click="selectCandidate(coralObservation.coralName)"
      >
        <div class="mt-2 flex">
          <span class="p-3 text-sm font-bold">
            {{ coralObservation.coralName }}
          </span>

          <div
            v-if="hasHighSimilarity(coralObservation.candidates)"
            class="ml-3 inline-flex items-center rounded-md bg-teal-600/20 px-1.5 text-xs font-medium"
          >
            <svg
              fill="#ffffff"
              width="24px"
              height="24px"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M21 4h-3V3a1 1 0 0 0-1-1H7a1 1 0 0 0-1 1v1H3a1 1 0 0 0-1 1v3a4 4 0 0 0 4 4h1.54A6 6 0 0 0 11 13.91V16h-1a3 3 0 0 0-3 3v2a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-2a3 3 0 0 0-3-3h-1v-2.09A6 6 0 0 0 16.46 12H18a4 4 0 0 0 4-4V5a1 1 0 0 0-1-1M6 10a2 2 0 0 1-2-2V6h2v2a6 6 0 0 0 .35 2Zm8 8a1 1 0 0 1 1 1v1H9v-1a1 1 0 0 1 1-1Zm2-10a4 4 0 0 1-8 0V4h8Zm4 0a2 2 0 0 1-2 2h-.35A6 6 0 0 0 18 8V6h2Z"
              />
            </svg>

            <span class="ml-1">
              Great Match
            </span>
          </div>
        </div>

        <div class="grid grid-cols-3">
          <div
            v-for="candidate in coralObservation.candidates"
            :key="candidate.id"
            class="mb-2 text-center"
          >
            <div class="flex h-[150px] items-center justify-center">
              <img
                v-if="candidate.imageUrl"
                :src="candidate.imageUrl"
                class="h-full w-full object-contain mix-blend-screen"
              />

              <span
                v-else
                class="text-xs text-slate-600"
              >
                No preview
              </span>
            </div>

            <div class="text-xs">
              <p class="text-teal-300">
                {{ similarityLabel(candidate.visualSimilarity) }}
              </p>

              <p class="text-slate-400">
                Session {{ candidate.monitoringSessionDate }}
              </p>

              <p class="text-slate-400">
                {{ candidate.diveSite }}
              </p>
            </div>
          </div>
        </div>
      </button>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type {
  CoralCandidate,
  CoralObservations,
} from "../types/api";

type Props = {
  imageUrl: string;
  candidates: CoralCandidate[];
  selectedCount: number;
  loadingSegment: boolean;
  loadingIdentify: boolean;
  loadingConfirm: boolean;
};

const props = defineProps<Props>();

const emit = defineEmits<{
  confirm: [payload: {
    selectedCandidateId: string | null;
    diveSite: string;
    coralName: string;
  }];
}>();

const site = ref("Isla Larga");

const name = ref(`Coral-${crypto.randomUUID().slice(0, 5).toUpperCase()}`);

const activeId = ref("");

const coralObservations = computed<CoralObservations[]>(() => {
  const grouped = Object.groupBy(props.candidates, (candidate) => candidate.coralName);

  return Object.entries(grouped).map(
    ([coralName, candidates]) => ({coralName, candidates: candidates ?? []}));
});

const active = computed(() =>
  coralObservations.value.find(
    (coralObservation) =>
      coralObservation.coralName === activeId.value,
  ),
);

const createNewCoralName = () => {
  return `Coral-${crypto.randomUUID().slice(0, 5).toUpperCase()}`;
};

const selectCandidate = (coralName: string) => {
  if (activeId.value === coralName) {
    deselectCandidate();
    return;
  }

  activeId.value = coralName;
  name.value = coralName;
};

const deselectCandidate = () => {
  activeId.value = "";
  name.value = createNewCoralName();
};

const confirm = () => {
  emit("confirm", {
    selectedCandidateId: activeId.value || null,
    diveSite: site.value,
    coralName: name.value,
  });
  activeId.value = '';

};

const hasHighSimilarity = (
  candidates: CoralCandidate[],
) => {
  return candidates.some(
    (candidate) =>
      candidate.visualSimilarity >= 0.95,
  );
};

const similarityLabel = (
  similarity: number,
) => {
  if (similarity === 1) {
    return "Identical";
  } else if (similarity >= 0.95) {
    return "Very strong match";
  } else if (similarity >= 0.90) {
    return "Strong match";
  } else if (similarity >= 0.85) {
    return "Possible match";
  } else if (similarity >= 0.70) {
    return "Weak match";
  } else {
    return "Low similarity";
  }
};
</script>