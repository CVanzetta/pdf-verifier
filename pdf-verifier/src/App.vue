<template>
  <div class="component">
    <div class="grid">
      <!-- PDF Verification Tool -->
      <div class="col-12">
        <Card header="PDF Verification Tool" class="mb-5">
          <template #content>
            <FileUpload 
              mode="basic" 
              choose-label="Upload PDF"
              v-model="pdfFile" 
              accept=".pdf">
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
              binary="true" 
              v-model="selectAll" 
              label="Select All Tests" 
              @change="toggleSelectAll">
            </Checkbox>

            <Accordion>
              <AccordionTab 
                v-for="(category, index) in editiqueTests.categories" 
                :key="index" 
                :header="category.nom">
                <ul class="list mt-2">
                  <li v-for="test in filterImportantTests(category.tests)" :key="test.id">
                    <Checkbox 
                      v-model="selectedTests" 
                      :value="test" 
                      @change="toggleTestSelection(test)">
                    </Checkbox>
                    <span>{{ test.categorie + ' - ' + test.article }}</span>
                    <i class="pi pi-info-circle" style="margin-left: 10px; color: blue;"></i>
                  </li>
                </ul>
              </AccordionTab>
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
import AccordionTab from 'primevue/accordiontab';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Card from 'primevue/card';
import * as pdfjsLib from 'pdfjs-dist';
import testData from '@/assets/Tests.json';

pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

const pdfFile = ref(null);
const editiqueTests = reactive(testData);
const selectedTests = ref([]);
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

    results.value = selectedTests.value.map((test) => {
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
    selectedTests.value = editiqueTests.categories.flatMap((category) => category.tests);
  } else {
    selectedTests.value = [];
  }
};

const toggleTestSelection = (test) => {
  if (selectedTests.value.includes(test)) {
    selectedTests.value = selectedTests.value.filter((t) => t !== test);
  } else {
    selectedTests.value.push(test);
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
</style>
