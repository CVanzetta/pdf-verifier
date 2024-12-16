<template>
  <div class="component">
    <div class="grid">
      <!-- PDF Verification Tool -->
      <div class="col-12">
        <Card header="PDF Verification Tool" class="mb-5">
          <template #content>
            <FileUpload
              name="pdf[]"
              accept="application/pdf"
              :maxFileSize="10 * 1024 * 1024"
              custom-upload
              :multiple="false"
              @select="onFileSelect"
              @remove="onRemoveFile"
            >
              <template #header="{ chooseCallback, clearCallback, files }">
                <div class="flex flex-wrap justify-between items-center flex-1 gap-4">
                  <div class="flex gap-2">
                    <Button
                      @click="chooseCallback"
                      icon="pi pi-folder-open"
                      rounded
                      outlined
                      severity="secondary"
                    ></Button>
                    <Button
                      @click="clearCallback"
                      icon="pi pi-trash"
                      rounded
                      outlined
                      severity="danger"
                      :disabled="!files || files.length === 0"
                    ></Button>
                  </div>
                  <span v-if="pdfFile">Selected File: {{ pdfFile.name }}</span>
                </div>
              </template>

              <template #content="{ files }">
                <div v-if="files.length > 0" class="mt-4">
                  <ul>
                    <li
                      v-for="file in files"
                      :key="file.name"
                      class="flex justify-between items-center"
                    >
                      <span>{{ file.name }}</span>
                      <Button
                        icon="pi pi-times"
                        class="p-button-text p-button-danger"
                        @click="$emit('remove', file)"
                      ></Button>
                    </li>
                  </ul>
                </div>
              </template>

              <template #empty>
                <div class="flex flex-col items-center justify-center text-center py-10">
                  <div
                    class="flex items-center justify-center rounded-full border-4 border-gray-300 h-32 w-32"
                    style="margin: 0 auto;"
                  >
                    <i class="pi pi-cloud-upload text-6xl text-gray-500"></i>
                  </div>
                  <p class="mt-6 mb-0 text-lg font-semibold">Drag and drop files here to upload.</p>
                </div>
              </template>
            </FileUpload>

            <Button
              label="Run Selected Tests"
              icon="pi pi-play"
              class="mt-3"
              :loading="loading"
              :disabled="loading || !pdfFile"
              @click="analyzePdf"
            ></Button>
          </template>
        </Card>
      </div>

      <!-- Select Tests to Run -->
      <div class="col-12">
        <Card header="Select Tests to Run" class="mb-5">
          <template #content>
            <Checkbox
              :binary="true"
              v-model="selectAll"
              label="Select All Tests"
              @change="toggleSelectAll"
            ></Checkbox>

            <Accordion :value="['0']" multiple>
              <AccordionPanel
                v-for="(category, index) in editiqueTests.categories"
                :key="index"
                :value="index.toString()"
              >
                <AccordionHeader>{{ category.nom }}</AccordionHeader>
                <AccordionContent>
                  <ul class="list mt-2">
                    <li v-for="test in filterImportantTests(category.tests)" :key="test.id">
                      <Checkbox
                        v-model="selectedTests"
                        :value="test.id"
                        @change="toggleTestSelection"
                      ></Checkbox>
                      <span>{{ test.categorie + ' - ' + test.article }}</span>
                      <i class="pi pi-info-circle" style="margin-left: 10px; color: blue;"></i>
                    </li>
                  </ul>
                </AccordionContent>
              </AccordionPanel>
            </Accordion>
          </template>
        </Card>
      </div>

      <!-- Test Results -->
      <div class="col-12" v-if="results.length > 0">
        <Card header="Test Results" class="mb-5">
          <template #content>
            <DataTable :value="results">
              <Column field="status" header="Status">
                <template #body="{ data }">
                  <i
                    v-if="data.status === 'Passed'"
                    class="pi pi-check-circle"
                    style="color: green;"
                  ></i>
                  <i
                    v-if="data.status === 'Failed'"
                    class="pi pi-times-circle"
                    style="color: red;"
                  ></i>
                </template>
              </Column>
              <Column field="categorie" header="Catégorie"></Column>
              <Column field="article" header="Article"></Column>
              <Column field="comments" header="Comments"></Column>
            </DataTable>
          </template>
        </Card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import FileUpload from 'primevue/fileupload';
import Button from 'primevue/button';
import Checkbox from 'primevue/checkbox';
import Accordion from 'primevue/accordion';
import AccordionPanel from 'primevue/accordionpanel';
import AccordionHeader from 'primevue/accordionheader';
import AccordionContent from 'primevue/accordioncontent';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Card from 'primevue/card';
import 'primeicons/primeicons.css';
import * as pdfjsLib from 'pdfjs-dist';
import testData from '@/assets/Tests.json';

pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

const pdfFile = ref(null);
const editiqueTests = reactive(testData);
const selectedTests = ref([]);
const results = ref([]);
const selectAll = ref(false);
const loading = ref(false);

const normalizeText = (text) => {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // accents
    .replace(/\s+/g, ' ')
    .trim();
};

// Modification pour sélectionner le dernier fichier
const onFileSelect = (event) => {
  if (event.files.length > 0) {
    pdfFile.value = event.files[event.files.length - 1];
    event.files.splice(0, event.files.length, pdfFile.value);
    console.log("File selected:", pdfFile.value.name);
  }
};

const onRemoveFile = () => {
  pdfFile.value = null;
  console.log("File removed");
};

const analyzePdf = async () => {
  console.log("Starting PDF analysis...");
  if (!pdfFile.value) {
    console.error("Please upload a PDF file before running the analysis.");
    return;
  }

  if (pdfFile.value.size > 10 * 1024 * 1024) {
    console.error("The uploaded file is too large. Please upload a file smaller than 10MB.");
    return;
  }

  if (selectedTests.value.length === 0) {
    console.error("No tests selected. Please select at least one test to run.");
    return;
  }

  console.log("Selected Tests:", selectedTests.value);
  loading.value = true;

  try {
    const arrayBuffer = await pdfFile.value.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    console.log(`PDF loaded. Number of pages: ${pdf.numPages}`);

    let textContent = "";
    for (let i = 1; i <= pdf.numPages; i++) {
      console.log(`Analyzing page ${i}/${pdf.numPages}...`);
      const page = await pdf.getPage(i);
      const text = await page.getTextContent();
      const pageText = text.items.map(item => item.str).join(" ");
      textContent += pageText + " ";
    }

    textContent = normalizeText(textContent);
    console.log("Extracted PDF Content:", textContent);

    if (!textContent || textContent.length === 0) {
      console.warn("No text extracted from the PDF. Check if the PDF is selectable or needs OCR.");
    }

    const allTests = editiqueTests.categories.flatMap(cat => cat.tests);
    results.value = selectedTests.value.map((testId) => {
      const test = allTests.find(t => t.id === testId);
      if (!test) {
        console.error(`Test with ID ${testId} not found.`);
        return null;
      }
      const status = evaluateEditique(test, textContent);
      return { ...test, status, comments: status === "Failed" ? generateComments(test) : "" };
    }).filter(r => r !== null);

    console.log("Final results array:", results.value);
  } catch (error) {
    console.error("An error occurred while analyzing the PDF.");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const evaluateEditique = (test, textContent) => {
  console.log("Evaluating test:", test);
  console.log("Text content for test:", textContent);

  if (!test.conditions || test.conditions.length === 0) {
    console.warn("No conditions found for test:", test.id);
    return "Passed";
  }

  for (const condition of test.conditions) {
    const type = condition.type || "";
    console.log("Checking condition:", condition);

    let passed = false;
    switch (type) {
      case "surface_max":
        passed = evaluateSurfaceMax(condition, textContent);
        break;
      case "montant":
        passed = evaluateMontant(condition, textContent);
        break;
      case "date":
        passed = evaluateDate(condition, textContent);
        break;
      case "texte":
      case "texte_present":
        passed = evaluateTexte(condition, textContent);
        break;
      case "texte_multi_colonnes":
        passed = evaluateTexteMultiColonnes(condition, textContent);
        break;
      default:
        console.error("Unknown condition type:", type);
        return "Failed";
    }

    if (!passed) {
      console.log(`Condition failed: ${type}`, condition);
      return "Failed";
    }
  }

  console.log("All conditions passed for test:", test.id);
  return "Passed";
};

const evaluateSurfaceMax = (condition, textContent) => {
  const ref = normalizeText(condition.reference || "");
  const val = normalizeText(condition.value || "");
  const regex = new RegExp(`${ref}.*?(${val})`, "i");
  const result = regex.test(textContent);
  console.log(`Evaluating surface_max with regex ${regex}: ${result}`);
  return result;
};

const evaluateMontant = (condition, textContent) => {
  const ref = normalizeText(condition.reference || "");
  // Ajuster la regex selon vos besoins
  const regex = new RegExp(`${ref}.*?(\\d{1,3}(?:[.,]\\d{3})*(?:[.,]\\d{2})?)`, "i");
  const result = regex.test(textContent);
  console.log(`Evaluating montant with regex ${regex}: ${result}`);
  return result;
};

const evaluateDate = (condition, textContent) => {
  const ref = normalizeText(condition.reference || "");
  const regex = new RegExp(`${ref}.*?(\\d{2}/\\d{2}/\\d{4})`, "i");
  const result = regex.test(textContent);
  console.log(`Evaluating date with regex ${regex}: ${result}`);
  return result;
};

const evaluateTexte = (condition, textContent) => {
  const val = normalizeText(condition.value || "");
  const found = textContent.includes(val);
  console.log(`Evaluating texte: "${val}" in extracted text: ${found}`);
  return found;
};

const evaluateTexteMultiColonnes = (condition, textContent) => {
  const normalizedText = normalizeText(textContent);
  const values = (condition.values || []).map(v => normalizeText(v));

  const allFound = values.every(val => {
    const found = normalizedText.includes(val);
    console.log(`Checking multi-colonnes value "${val}": ${found}`);
    return found;
  });

  return allFound;
};

const generateComments = (test) => {
  return `The condition ${test.article} was not met. Please check the requirements.`;
};

const toggleSelectAll = () => {
  if (selectAll.value) {
    selectedTests.value = editiqueTests.categories.flatMap((category) => category.tests.map(test => test.id));
  } else {
    selectedTests.value = [];
  }
  console.log("Selected Tests after toggle:", selectedTests.value);
};

const toggleTestSelection = (testId) => {
  if (selectedTests.value.includes(testId)) {
    selectedTests.value = selectedTests.value.filter((id) => id !== testId);
  } else {
    selectedTests.value.push(testId);
  }
  console.log("Selected Tests after selection:", selectedTests.value);
};

const filterImportantTests = (tests) => {
  return tests.filter((test) => test.conditions && test.conditions.length > 0);
};
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
