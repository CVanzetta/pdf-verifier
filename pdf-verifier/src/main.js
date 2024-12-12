import { createApp } from 'vue';
import App from './App.vue';
import Material from '@primevue/themes/material';
import PrimeVue from 'primevue/config'


import Button from 'primevue/button';        
import Card from 'primevue/card';            
import Checkbox from 'primevue/checkbox';    
import Accordion from 'primevue/accordion';  
import AccordionTab from 'primevue/accordiontab'; 

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
app.component('Button', Button);       
app.component('Card', Card);           
app.component('Checkbox', Checkbox);   
app.component('Accordion', Accordion); 
app.component('AccordionTab', AccordionTab);

app.mount('#app');