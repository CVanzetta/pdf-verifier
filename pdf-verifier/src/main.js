// main.js
import { createApp } from 'vue';
import App from './App.vue';

// Importation de Vuetify
import { createVuetify } from 'vuetify';
import 'vuetify/styles'; // Styles de Vuetify
import '@mdi/font/css/materialdesignicons.css'; // Icônes (optionnel)

// Création de l'instance Vuetify
const vuetify = createVuetify({
  // Options personnalisées
});

const app = createApp(App);

app.use(vuetify);

app.mount('#app');
