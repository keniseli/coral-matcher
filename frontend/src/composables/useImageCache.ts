import observationMonitoringService from '@/services/observationMonitoringService';
import { ObservationVisualization } from '@/types/monitoring';
import { ref } from 'vue';
import { useNotificationStore } from '@/stores/notification';
import ObservationPage from '@/pages/ObservationPage.vue';

// Module-level cache so it survives component unmounts
const imageCache = new Map<string, ObservationVisualization>();
const notificationStore = useNotificationStore();

export function useImageCache() {
    const getOrFetchVisualizations = async (observationId: string): Promise<ObservationVisualization> => {

        if (imageCache.has(observationId)) {
            return imageCache.get(observationId)!;
        }

        const observationVisualization = await observationMonitoringService.loadVisualizations(observationId);
        imageCache.set(observationId, observationVisualization);
        return observationVisualization;
    };

    return { getOrFetchVisualizations };
}