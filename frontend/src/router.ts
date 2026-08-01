import { createRouter, createWebHistory } from "vue-router";
import ObservationPage from "./pages/ObservationPage.vue";
import MonitoringPage from "./pages/MonitoringPage.vue";

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: "/",
            redirect: '/observe',
        },
        {
            path: "/observe",
            component: ObservationPage,
        },
        {
            path: "/monitor",
            component: MonitoringPage,
        },
    ],
});

export default router;