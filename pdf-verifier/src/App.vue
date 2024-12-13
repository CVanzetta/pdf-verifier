<template>
  <div 
    class="component">
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
              @select="onFileSelect" 
              @remove="onRemoveFile">
              <template #header="{ chooseCallback, clearCallback, files }">
                <div class="flex flex-wrap justify-between items-center flex-1 gap-4">
                  <div class="flex gap-2">
                    <Button 
                      @click="chooseCallback" 
                      icon="pi pi-folder-open" 
                      rounded 
                      outlined 
                      severity="secondary">
                    </Button>
                    <Button 
                      @click="clearCallback" 
                      icon="pi pi-trash" 
                      rounded 
                      outlined 
                      severity="danger" 
                      :disabled="!files || files.length === 0">
                    </Button>
                  </div>
                  <span v-if="pdfFile">Selected File: {{ pdfFile.name }}</span>
                </div>
              </template>
              <template #content="{ files }">
                <div v-if="files.length > 0" class="mt-4">
                  <ul>
                    <li v-for="file in files" :key="file.name" class="flex justify-between items-center">
                      <span>{{ file.name }}</span>
                      <Button 
                        icon="pi pi-times" 
                        class="p-button-text p-button-danger" 
                        @click="$emit('remove', file)">
                      </Button>
                    </li>
                  </ul>
                </div>
              </template>
              <template #empty>
                <div class="flex flex-col items-center">
                  <i
                    class="pi pi-cloud-upload !border-2 !rounded-full !p-8 !text-4xl !text-muted-color">
                  </i>
                  <p class="mt-6 mb-0">Drag and drop files to here to upload.</p>
                </div>
              </template>
            </FileUpload>

            <Button 
              label="Run Selected Tests" 
              icon="pi pi-play" 
              class="mt-3"
              :loading="loading" 
              :disabled="loading || !pdfFile" 
              @click="analyzePdf">
            </Button>
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
              @change="toggleSelectAll">
            </Checkbox>

            <Accordion :value="['0']" multiple>
              <AccordionPanel 
                v-for="(category, index) in editiqueTests.categories" 
                :key="index"
                :value="index.toString()">
                <AccordionHeader>{{ category.nom }}</AccordionHeader>
                <AccordionContent>
                  <ul class="list mt-2">
                    <li v-for="test in filterImportantTests(category.tests)" :key="test.id">
                      <Checkbox 
                        v-model="selectedTests" 
                        :value="test.id" 
                        @change="toggleTestSelection">
                      </Checkbox>
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
                    style="color: green;">
                  </i>
                  <i 
                    v-if="data.status === 'Failed'" 
                    class="pi pi-times-circle" 
                    style="color: red;">
                  </i>
                </template>
              </Column>
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
// const isDragging = ref(false);
const editiqueTests = reactive(testData);
const selectedTests = ref([]); // Store selected test IDs
const results = ref([]);
const selectAll = ref(false);
const loading = ref(false);

const preprocessText = (text) => {
  return text
    .toLowerCase()
    .normalize("NFD").replace(/[̀-ͯ]/g, "") // Remove accents
    .replace(/\s+/g, " ") // Normalize spaces
    .trim();
};

const analyzePdf = async () => {
  console.log("PDF analysis started...");

  if (!pdfFile.value) {
    console.error("Please upload a PDF file before running the analysis.");
    return;
  }

  if (pdfFile.value.size > 10 * 1024 * 1024) { // Limit file size to 10MB
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
    let textContent = "";

    for (let i = 1; i <= pdf.numPages; i++) {
      console.log(`Analyzing page ${i} of ${pdf.numPages}...`);
      const page = await pdf.getPage(i);
      const text = await page.getTextContent();
      textContent += text.items.map(item => item.str).join(" ") + " ";
    }

    textContent = preprocessText(textContent);
    console.log("Extracted PDF Content:", textContent);

    results.value = selectedTests.value.map((testId) => {
      const test = editiqueTests.categories.flatMap(cat => cat.tests).find(t => t.id === testId);
      const status = evaluateEditique(test, textContent);
      return { ...test, status, comments: status === "Failed" ? generateComments(test) : "" };
    });
    console.log("Results after analysis:", results.value);
  } catch (error) {
    console.error("An error occurred while analyzing the PDF. Please make sure the file is not corrupted.");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const onFileSelect = (event) => {
  if (event.files.length > 0) {
    pdfFile.value = event.files[0];
    console.log("File selected:", pdfFile.value.name);
  }
};

const onRemoveFile = () => {
  pdfFile.value = null;
  console.log("File removed");
};

const evaluateEditique = (test, textContent) => {
  const conditions = test.conditions;
  for (const condition of conditions) {
    if (condition.type === "surface_max" && !evaluateSurfaceMax(condition, textContent)) {
      return "Failed";
    }
    if (condition.type === "montant" && !evaluateMontant(condition, textContent)) {
      return "Failed";
    }
    if (condition.type === "date" && !evaluateDate(condition, textContent)) {
      return "Failed";
    }
    if (condition.type === "texte" && !evaluateTexte(condition, textContent)) {
      return "Failed";
    }
  }
  return "Passed";
};

const evaluateSurfaceMax = (condition, textContent) => {
  const regex = new RegExp(`${condition.reference}.*?(${condition.value})`, "i");
  return regex.test(textContent);
};

const evaluateMontant = (condition, textContent) => {
  const regex = new RegExp(`${condition.reference}.*?((\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?))\s*FFB`, "i");
  return regex.test(textContent);
};

const evaluateDate = (condition, textContent) => {
  const regex = new RegExp(`${condition.reference}.*?(\d{2}/\d{2}/\d{4})`, "i");
  return regex.test(textContent);
};

const evaluateTexte = (condition, textContent) => {
  return textContent.includes(condition.value);
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
};

const toggleTestSelection = (testId) => {
  if (selectedTests.value.includes(testId)) {
    selectedTests.value = selectedTests.value.filter((id) => id !== testId);
  } else {
    selectedTests.value.push(testId);
  }
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
