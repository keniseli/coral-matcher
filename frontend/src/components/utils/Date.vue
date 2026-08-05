<template>
    {{ formatDate(timestamp) }}
</template>

<script setup lang="ts">
import { format } from 'date-fns';


const props = defineProps<{
    timestamp: string | number | Date;
}>();

const formatDate = (timestamp: string | number | Date) => {
    const date = new Date(timestamp);
    return format(date, "dd. MMM yyyy 'at' p");
}


</script>