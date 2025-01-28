<template>
  <div class="mx-4 md:mx-10 lg:mx-20 xl:mx-60">
    <div class="component">
      <div class="grid">
        <!-- Outil de vérification PDF -->
        <div class="col-12">
          <PdfVerificationTool
            :pdfFile="pdfFile"
            :loading="loading"
            :selectedTests="selectedTests"
            @update:pdfFile="(val) => pdfFile = val"
            @analyzePdf="analyzePdf"
          />
        </div>

        <!-- Sélectionner les tests à exécuter -->
        <div class="col-12">
          <TestsSelection
            :editiqueTests="editiqueTests"
            :selectedTests="selectedTests"
            :selectedCategories="selectedCategories"
            :selectAll="selectAll"
            @update:selectedTests="(val) => (selectedTests = val)"
            @update:selectedCategories="(val) => (selectedCategories = val)"
            @update:selectAll="(val) => (selectAll = val)"
          />
        </div>

        <!-- Résultats des tests -->
        <div class="col-12" v-if="results.length > 0">
          <ResultsTable :results="results" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import testData from '@/assets/Tests.json';

// Import child components
import PdfVerificationTool from '@/components/PdfVerificationTool.vue';
import TestsSelection from '@/components/TestsSelection.vue';
import ResultsTable from '@/components/ResultsTable.vue';

// Import composable or helper for PDF analysis
import usePdfAnalyzer from '@/composables/usePdfAnalyzer';

// Reactive references / data
const pdfFile = ref(null);
const editiqueTests = reactive(testData);
const selectedTests = ref([]);
const selectedCategories = ref([]);
const selectAll = ref(false);
const results = ref([]);
const loading = ref(false);

// Get methods from the composable
const {
  analyzePdfFile
} = usePdfAnalyzer();

// The actual method that triggers PDF analysis
async function analyzePdf () {
  loading.value = true;
  try {
    results.value = await analyzePdfFile(pdfFile.value, selectedTests.value, editiqueTests);
  } catch (error) {
    console.error("Erreur lors de l'analyse du PDF.", error);
  } finally {
    loading.value = false;
  }
}
</script>

<style>
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

<!-- EXPLANATION OF STRUCTURE:
1) This is the main container component that organizes the layout.
2) The PdfVerificationTool handles PDF file upload and triggers the analyzePdf event.
3) The TestsSelection component handles categories and test selection.
4) The ResultsTable displays the final results.
5) The usePdfAnalyzer composable centralizes the PDF reading and conditions logic.
-->
