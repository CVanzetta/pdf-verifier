// App.vue
<template>
  <v-app>
    <v-container>
      <v-card class="ma-5">
        <v-card-title>
          PDF Verification Tool
        </v-card-title>
        <v-card-text>
          <v-file-input label="Upload PDF" @change="handleFileUpload" outlined></v-file-input>
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
          <v-list>
            <v-list-item-group v-for="(category, index) in editiqueTests.categories" :key="index">
              <v-subheader>{{ category.name }}</v-subheader>
              <v-list-item v-for="test in category.tests" :key="test.id">
                <v-checkbox :label="test.categorie + ' - ' + test.article" :value="test" v-model="selectedTests"></v-checkbox>
                <v-icon color="blue" class="ml-2" v-tooltip="test.commentaires">mdi-information</v-icon>
              </v-list-item>
            </v-list-item-group>
          </v-list>
        </v-card-text>
      </v-card>

      <v-card v-if="results.length > 0" class="ma-5">
        <v-card-title>
          Test Results
        </v-card-title>
        <v-card-text>
          <v-simple-table>
            <thead>
              <tr>
                <th>Test</th>
                <th>Status</th>
                <th>Comments</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="result in results" :key="result.id" :class="{'success-row': result.status === 'Passed', 'failed-row': result.status === 'Failed'}">
                <td>{{ result.categorie }} - {{ result.article }}</td>
                <td>
                  <v-icon v-if="result.status === 'Passed'" color="green">mdi-check-circle</v-icon>
                  <v-icon v-if="result.status === 'Failed'" color="red">mdi-close-circle</v-icon>
                </td>
                <td>{{ result.comments }}</td>
              </tr>
            </tbody>
          </v-simple-table>
        </v-card-text>
      </v-card>
    </v-container>
  </v-app>
</template>

<script>
import { ref, reactive, onMounted } from 'vue';
import pdfjsLib from 'pdfjs-dist';
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.entry';
import editiqueTestsData from '@/assets/editiqueTests.json';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;

export default {
  name: "App",
  setup() {
    const pdfFile = ref(null);
    const editiqueTests = reactive(editiqueTestsData);
    const selectedTests = ref([]);
    const results = ref([]);
    const loading = ref(false);

    const handleFileUpload = (event) => {
      pdfFile.value = event;
    };

    const analyzePdf = async () => {
      if (!pdfFile.value) {
        console.error("Please upload a PDF file before running the analysis.");
        return;
      }

      if (pdfFile.value.size > 10 * 1024 * 1024) { // Limit file size to 10MB
        console.error("The uploaded file is too large. Please upload a file smaller than 10MB.");
        return;
      }

      loading.value = true;

      try {
        const arrayBuffer = await pdfFile.value.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        let textContent = "";

        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const text = await page.getTextContent();
          textContent += text.items.map(item => item.str).join(" ") + " ";
        }

        textContent = preprocessText(textContent);

        results.value = selectedTests.value.map((test) => {
          const status = evaluateEditique(test, textContent);
          return { ...test, status, comments: status === "Failed" ? generateComments(test) : "" };
        });
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
      const conditions = test.conditions;
      for (const condition of conditions) {
        if (condition.type === "surface_max") {
          if (!evaluateSurfaceMax(condition, textContent)) {
            return "Failed";
          }
        } else if (condition.type === "montant") {
          if (!evaluateMontant(condition, textContent)) {
            return "Failed";
          }
        } else if (condition.type === "date") {
          if (!evaluateDate(condition, textContent)) {
            return "Failed";
          }
        } else if (condition.type === "texte") {
          if (!evaluateTexte(condition, textContent)) {
            return "Failed";
          }
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

    onMounted(async () => {
      editiqueTests.categories = await editiqueTestsData.categories;
    });

    return {
      pdfFile,
      editiqueTests,
      selectedTests,
      results,
      loading,
      handleFileUpload,
      analyzePdf,
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