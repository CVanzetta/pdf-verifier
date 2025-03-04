<template>
  <div id="app">
    <!-- Composant principal de l'application avec bindings -->
    <RefactoredEditique v-model:pdfFile="pdfFile" :selectedTests="selectedTests" />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import RefactoredEditique from '@/views/RefactoredEditique.vue';

// Variable réactive pour stocker le fichier PDF sélectionné
const pdfFile = ref(null);

// Exemple de tests sélectionnés à appliquer (à adapter selon vos besoins)
const selectedTests = ref([
  { id: 'test1', name: 'Test Vérification Logo' },
  // Ajoutez d'autres tests ici si nécessaire
]);
</script>

<style>
#app {
  max-width: 800px;
  margin: auto;
  padding: 1rem;
}

.p-mb-5 {
  margin-bottom: 2rem;
}
.p-m-3 {
  margin: 1rem;
}
.upload-container {
  border: 2px dashed #007bff;
  padding: 1rem;
  text-align: center;
  background-color: rgba(0, 123, 255, 0.05);
}
.dragging {
  background-color: rgba(0, 123, 255, 0.1);
}
</style>