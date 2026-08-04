<template>

    <div v-if="metricsSeries.length > 0" class="w-full">
        <div class="flex text-xs">

            <div class="w-monitoring-metric-label-column shrink-0" />

            <div class="shrink-0" :style="{ width: `${metricsSeries[0].observations.length * 240}px` }">
                <VChart :option="chartOption" class="w-full h-60"
                    :key="metricsSeries[0]?.observations.length" />
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import VChart from "vue-echarts";
import type { EChartsOption } from "echarts";
import { format } from "date-fns";

import { MetricDefinition, metricDefinitions, MetricSeries } from '@/types/monitoring';

const props = defineProps<{
    metricsSeries: MetricSeries[];
    metricDefinitions: MetricDefinition[];
}>();

const chartOption = computed<EChartsOption>(() => ({
    animation: false,

    tooltip: {
        trigger: "axis",
    },

    legend: {
        type: "scroll",
        bottom: 10,
    },

    grid: {
        left: 60,
        right: 20,
        top: 20,
        bottom: 40,
    },

    xAxis: {
        type: "category",
        boundaryGap: false,
        data: props.metricsSeries.reduce(_ => _).observations.map(comparison => comparison.observation.observedAt),
        axisLabel: {
            formatter: _ => ""
        }
    },

    yAxis: {
        type: "value",
        axisLabel: {
            formatter: "{value} %",
        },
    },

    series: props.metricsSeries.map(metricSeries => ({
        name: metricDefinitions.find(definition => definition.id == metricSeries.metricId)?.label,
        type: "line",
        smooth: false,
        symbol: "circle",
        symbolSize: 6,
        data: metricSeries.metrics.map((metric) => metric.changePercentage),
    })),
}));

function getLabel(metricId: string) {
    return metricDefinitions.find(definition => definition.id == metricId)?.label;
}

</script>