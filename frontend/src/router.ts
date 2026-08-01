import { createRouter, createWebHistory } from "vue-router";
import SegmentationPage from "./pages/SegmentationPage.vue";
import MonitoringPage from "./pages/MonitoringPage.vue";

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: "/",
            component: SegmentationPage,
        },
        {
            path: "/observe",
            component: SegmentationPage,
        },
        {
            path: "/monitor",
            component: MonitoringPage,
        },
    ],
});

export default router;