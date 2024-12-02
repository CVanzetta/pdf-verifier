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
VListItemGroup,
VSubheader,
VCheckbox,
VIcon,
VSimpleTable,
VExpansionPanels,
VExpansionPanel,
VExpansionPanelHeader,
VExpansionPanelContent,
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
    VListItemGroup,
    VSubheader,
    VCheckbox,
    VIcon,
    VSimpleTable,
    VExpansionPanels,
    VExpansionPanel,
    VExpansionPanelHeader,
    VExpansionPanelContent,
},
});

createApp(App).use(vuetify).mount('#app');
