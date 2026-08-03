import { createApp } from 'vue'
import App from './App.vue'
import './styles/tailwind.css'
import { createPinia } from "pinia";
import router from "./router";
import "./plugins/echarts";

createApp(App)
    .use(createPinia())
    .use(router)
    .mount('#app');
