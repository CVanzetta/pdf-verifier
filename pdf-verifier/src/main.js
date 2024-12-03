import { createApp } from 'vue';
import App from './App.vue';
import { createVuetify } from 'vuetify';
import 'vuetify/styles';
import '@mdi/font/css/materialdesignicons.css';

import {
VApp,
VContainer,
VCard,
VCardTitle,
VCardText,
VFileInput,
VBtn,
VList,
VListItem,
VExpansionPanels,
VExpansionPanel,
VExpansionPanelTitle,
VExpansionPanelText,
VCheckbox,
VIcon,
VDataTable,
} from 'vuetify/components';

const vuetify = createVuetify({
components: {
    VApp,
    VContainer,
    VCard,
    VCardTitle,
    VCardText,
    VFileInput,
    VBtn,
    VList,
    VListItem,
    VExpansionPanels,
    VExpansionPanel,
    VExpansionPanelTitle,
    VExpansionPanelText,
    VCheckbox,
    VIcon,
    VDataTable,
},
});

createApp(App).use(vuetify).mount('#app');
