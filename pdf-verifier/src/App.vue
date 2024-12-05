<template>
  <v-app>
    <v-container>
      <v-card class="ma-5">
        <v-card-title>
          PDF Verification Tool
        </v-card-title>
        <v-card-text>
          <v-file-input label="Upload PDF" v-model="pdfFile" outlined></v-file-input>
          <v-btn color="primary" @click="analyzePdf" :loading="loading" :disabled="loading || !pdfFile">
            Run Selected Tests
          </v-btn>
        </v-card-text>
      </v-card>

      <v-card class="ma-5">
        <v-card-title>
          Select Tests to Run
        </v-card-title>
        <v-card-text>
          <v-checkbox
            label="Select All Tests"
            v-model="selectAll"
            @change="toggleSelectAll"
          ></v-checkbox>
          <v-expansion-panels>
            <v-expansion-panel v-for="(category, index) in editiqueTests.categories" :key="index">
              <v-expansion-panel-title>{{ category.nom }}</v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-list>
                  <v-list-item-group multiple>
                    <v-list-item v-for="test in filterImportantTests(category.tests)" :key="test.id">
                      <v-checkbox :label="test.categorie + ' - ' + test.article" :value="test" v-model="selectedTests" @change="toggleTestSelection(test)"></v-checkbox>
                      <v-icon color="blue" class="ml-2">mdi-information</v-icon>
                    </v-list-item>
                  </v-list-item-group>
                </v-list>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
      </v-card>

      <v-card v-if="results.length > 0" class="ma-5">
        <v-card-title>
          Test Results
        </v-card-title>
        <v-card-text>
          <v-data-table :headers="tableHeaders" :items="results" class="elevation-1">
            <template v-slot:item.status="{ item }">
              <v-icon v-if="item.status === 'Passed'" color="green">mdi-check-circle</v-icon>
              <v-icon v-if="item.status === 'Failed'" color="red">mdi-close-circle</v-icon>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-container>
  </v-app>
</template>

<script>
import { ref, reactive, onMounted } from 'vue';
import * as pdfjsLib from 'pdfjs-dist';
import testData from '@/assets/Tests.json';

pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

export default {
  name: "App",
  setup() {
    const pdfFile = ref(null);
    const editiqueTests = reactive(testData);
    const selectedTests = ref([]);
    const results = ref([]);
    const loading = ref(false);
    const selectAll = ref(false);
    const tableHeaders = [
      { text: 'Test', value: 'categorie' },
      { text: 'Status', value: 'status' },
      { text: 'Comments', value: 'comments' },
    ];

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

    const preprocessText = (text) => {
      return text
        .toLowerCase()
        .normalize("NFD").replace(/[̀-ͯ]/g, "") // Remove accents
        .replace(/\s+/g, " ") // Normalize spaces
        .trim();
    };

    const evaluateEditique = (test, textContent) => {
      console.log(`Evaluating test: ${test.article}`);
      const conditions = test.conditions;
      for (const condition of conditions) {
        console.log(`Checking condition type: ${condition.type}`);
        if (condition.type === "surface_max") {
          if (!evaluateSurfaceMax(condition, textContent)) {
            console.log(`Failed surface_max condition for test: ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "montant_max") {
          if (!evaluateMontantMax(condition, textContent)) {
            console.log(`Failed montant_max condition for test: ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "date_presence") {
          if (!evaluateDatePresence(condition, textContent)) {
            console.log(`Failed date_presence condition for test: ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "texte_present") {
          if (!evaluateTextePresent(condition, textContent)) {
            console.log(`Failed texte_present condition for test: ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "garantie") {
          if (!evaluateGarantie(condition, textContent)) {
            console.log(`Failed garantie condition for test: ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "engagement_max") {
          if (!evaluateEngagementMax(condition, textContent)) {
            console.log(`Failed engagement_max condition for test: ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "franchise") {
          if (!evaluateFranchise(condition, textContent)) {
            console.log(`Failed franchise condition for test: ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "aménagements") {
          if (!evaluateAmenagements(condition, textContent)) {
            console.log(`Failed aménagements condition for test: ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "exclusion") {
          if (!evaluateExclusion(condition, textContent)) {
            console.log(`Failed exclusion condition for test: ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "valeur_max") {
          if (!evaluateValeurMax(condition, textContent)) {
            console.log(`Failed valeur_max condition for test: ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "dommages_max") {
          if (!evaluateDommagesMax(condition, textContent)) {
            console.log(`Failed dommages_max condition for test: ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "protection_locaux") {
          if (!evaluateProtectionLocaux(condition, textContent)) {
            console.log(`Failed protection_locaux condition for test: ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "sous_limites") {
          if (!evaluateSousLimites(condition, textContent)) {
            console.log(`Failed sous_limites condition for test: ${test.article}`);
            return "Failed";
          }
        } else {
          console.warn(`Unknown condition type: ${condition.type}`);
          return "Failed";
        }
      }
      console.log(`Passed all conditions for test: ${test.article}`);
      return "Passed";
    };

    const evaluateSurfaceMax = (condition, textContent) => {
      const regex = new RegExp(`${condition.reference}.*?(\d+)\s*m²`, "i");
      const match = textContent.match(regex);
      if (match) {
        const actualSurface = parseInt(match[1], 10);
        const conditionSurface = parseInt(condition.value, 10);
        return condition.operator === "<=" ? actualSurface <= conditionSurface : false;
      }
      return false;
    };

    const evaluateMontantMax = (condition, textContent) => {
      const regex = new RegExp(`${condition.reference}.*?(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)\s*FFB`, "i");
      const match = textContent.match(regex);
      if (match) {
        const actualAmount = parseFloat(match[1].replace(/[,]/g, ''));
        const conditionAmount = parseFloat(condition.value);
        return condition.operator === "<=" ? actualAmount <= conditionAmount : false;
      }
      return false;
    };

    const evaluateDatePresence = (condition, textContent) => {
      const regex = new RegExp(`${condition.reference}.*?(\d{2}/\d{2}/\d{4})`, "i");
      return regex.test(textContent);
    };

    const evaluateTextePresent = (condition, textContent) => {
      return textContent.includes(condition.value);
    };

    const evaluateGarantie = (condition, textContent) => {
      const garantie = condition.value.toLowerCase();
      return textContent.includes(garantie);
    };

    const evaluateEngagementMax = (condition, textContent) => {
      const engagement = condition.value.toLowerCase();
      const reference = condition.reference.toLowerCase();
      return textContent.includes(engagement) && textContent.includes(reference);
    };

    const evaluateFranchise = (condition, textContent) => {
      const franchise = condition.value.toLowerCase();
      return textContent.includes(franchise);
    };

    const evaluateAmenagements = (condition, textContent) => {
      const amenagements = condition.value.toLowerCase();
      return textContent.includes(amenagements);
    };

    const evaluateExclusion = (condition, textContent) => {
      const exclusion = condition.value.toLowerCase();
      return !textContent.includes(exclusion);
    };

    const evaluateValeurMax = (condition, textContent) => {
      const regex = new RegExp(`${condition.reference}.*?(\d+(?:[.,]\d+)?)\s*€`, "i");
      const match = textContent.match(regex);
      if (match) {
        const actualValue = parseFloat(match[1].replace(',', '.'));
        const conditionValue = parseFloat(condition.value.replace(',', '.'));
        return condition.operator === "<=" ? actualValue <= conditionValue : false;
      }
      return false;
    };

    const evaluateDommagesMax = (condition, textContent) => {
      const dommages = condition.value.toLowerCase();
      return textContent.includes(dommages);
    };

    const evaluateProtectionLocaux = (condition, textContent) => {
      const protections = condition.reference.toLowerCase().split(',').map(s => s.trim());
      return protections.some(protection => textContent.includes(protection));
    };

    const evaluateSousLimites = (condition, textContent) => {
      const sousLimites = condition.value.toLowerCase();
      return textContent.includes(sousLimites);
    };

    const generateComments = (test) => {
      return `The condition ${test.article} was not met. Please check the requirements.`;
    };

    const filterImportantTests = (tests) => {
      return tests.filter(test => test.conditions && test.conditions.length > 0);
    };

    const toggleSelectAll = () => {
      if (selectAll.value) {
        selectedTests.value = editiqueTests.categories.flatMap(category => filterImportantTests(category.tests));
      } else {
        selectedTests.value = [];
      }
      console.log("Selected Tests after toggleSelectAll:", selectedTests.value);
    };

    const toggleTestSelection = (test) => {
      const index = selectedTests.value.findIndex(selectedTest => selectedTest.id === test.id);
      if (index === -1) {
        selectedTests.value.push(test);
      } else {
        selectedTests.value.splice(index, 1);
      }
      console.log("Updated Selected Tests after toggleTestSelection:", selectedTests.value);
    };

    onMounted(async () => {
      console.log("Mounted and loading editique tests...");
      editiqueTests.categories = await testData.categories;
      console.log("Loaded editique tests:", editiqueTests.categories);
    });

    return {
      pdfFile,
      editiqueTests,
      selectedTests,
      results,
      loading,
      tableHeaders,
      analyzePdf,
      filterImportantTests,
      selectAll,
      toggleSelectAll,
      toggleTestSelection,
    };
  },
};
</script>

<style>
@import "vuetify/styles";

#app {
  font-family: Arial, sans-serif;
  text-align: center;
  color: #333;
  margin-top: 50px;
}
.success-row {
  background-color: #e8f5e9;
}
.failed-row {
  background-color: #ffebee;
}
.loading {
  font-weight: bold;
  color: #007bff;
}
</style>
