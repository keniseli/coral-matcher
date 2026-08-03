<template>

    <div v-if="metricSeries.size > 0" class="w-max border-collapse text-xs">

        <table>
            <tr v-for="[key, metrics] in metricSeries" :key="key">
                <td class="w-monitoring-metric-label-column">
                    {{ getLabel(key) }}
                </td>
                <td class="w-monitoring-metric-value-column" v-for="metric in metrics">
                    {{ metric.changePercentage }}
                </td>
            </tr>
        </table>
        <VChart :option="chartOption" />
    </div>
    <span v-else>
        Select metrics
    </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

import VChart from "vue-echarts";
import type { EChartsOption } from "echarts";

import { Metric, MetricDefinition, metricDefinitions } from '@/types/monitoring';

const props = defineProps<{
    metricSeries: Map<string, Metric[]>;
    metricDefinitions: MetricDefinition[];
}>();


/*const props = defineProps<{
    graphSeries: {
        name: string;
        values: number[];
    }[];
    observationLabels: string[];
}>();
*/

const chartOption = computed<EChartsOption>(() => ({
    animation: false,
    
    tooltip: {
        trigger: "axis",
    },
    
    legend: {
        top: 0,
    },
    
    grid: {
        left: 60,
        right: 20,
        top: 40,
        bottom: 30,
    },
    
    xAxis: {
        type: "category",
        boundaryGap: false,
        data: ["first", "second", "third"],
//        data: props.observationLabels,
    },
    
    yAxis: {
        type: "value",
        axisLabel: {
            formatter: "{value} %",
        },
    },

    series: Array.from(props.metricSeries, ([metricId, metrics]) => ({
        name: metricId,
        type: "line",
        smooth: false,
        symbol: "circle",
        symbolSize: 6,
        data: metrics,
    })),
}));

function getLabel(metricId: string) {
    return metricDefinitions.find(definition => definition.id == metricId)?.label;
}

</script>