import { createApp } from 'vue';
import App from './App.vue';
import Material from '@primevue/themes/material';
import PrimeVue from 'primevue/config'

const app = createApp(App);

app.use(PrimeVue, { 
    theme: {
        preset: Material,
        options: { 
            prefix: 'p', 
            darkModeSelector: 'false', 
            cssLayer: false 
        }
    } 
    
});


app.mount('#app');