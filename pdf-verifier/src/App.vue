// App.vue
<template>
  <div id="app">
    <h1>PDF Verification Tool</h1>
    <div class="upload-section">
      <input type="file" @change="handleFileUpload" />
      <button @click="analyzePdf">Run Selected Tests</button>
    </div>
    <div class="test-section">
      <h2>Select Tests to Run</h2>
      <ul>
        <li v-for="test in editiqueTests" :key="test.id">
          <input type="checkbox" :value="test" v-model="selectedTests" /> {{ test.categorie }} - {{ test.article }}
        </li>
      </ul>
    </div>
    <div class="results-section" v-if="results.length > 0">
      <h2>Test Results</h2>
      <table>
        <tr>
          <th>Test</th>
          <th>Status</th>
          <th>Comments</th>
        </tr>
        <tr v-for="result in results" :key="result.id">
          <td>{{ result.categorie }} - {{ result.article }}</td>
          <td>{{ result.status }}</td>
          <td>{{ result.comments }}</td>
        </tr>
      </table>
    </div>
  </div>
</template>

<script>
import pdfjsLib from "pdfjs-dist/build/pdf";
import pdfjsWorker from "pdfjs-dist/build/pdf.worker.entry";
import editiqueTestsData from "@/assets/editiqueTests.json";

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;

export default {
  name: "App",
  data() {
    return {
      pdfFile: null,
      editiqueTests: [],
      selectedTests: [],
      results: [],
      loading: false,
    };
  },
  methods: {
    handleFileUpload(event) {
      this.pdfFile = event.target.files[0];
    },
    async analyzePdf() {
      if (!this.pdfFile) {
        alert("Please upload a PDF file before running the analysis.");
        return;
      }

      if (this.pdfFile.size > 10 * 1024 * 1024) { // Limit file size to 10MB
        alert("The uploaded file is too large. Please upload a file smaller than 10MB.");
        return;
      }

      this.loading = true;

      try {
        const arrayBuffer = await this.pdfFile.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        let textContent = "";

        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const text = await page.getTextContent();
          textContent += text.items.map(item => item.str).join(" ") + " ";
        }

        textContent = this.preprocessText(textContent);

        this.results = this.selectedTests.map((test) => {
          const status = this.evaluateEditique(test, textContent);
          return { ...test, status, comments: status === "Failed" ? this.generateComments(test) : "" };
        });
      } catch (error) {
        alert("An error occurred while analyzing the PDF. Please make sure the file is not corrupted.");
        console.error(error);
      } finally {
        this.loading = false;
      }
    },
    preprocessText(text) {
      return text
        .toLowerCase()
        .normalize("NFD").replace(/[̀-ͯ]/g, "") // Remove accents
        .replace(/\s+/g, " ") // Normalize spaces
        .trim();
    },
    evaluateEditique(test, textContent) {
      const conditions = test.conditions;
      for (const condition of conditions) {
        if (condition.type === "surface_max") {
          if (!this.evaluateSurfaceMax(condition, textContent)) {
            return "Failed";
          }
        } else if (condition.type === "montant") {
          if (!this.evaluateMontant(condition, textContent)) {
            return "Failed";
          }
        } else if (condition.type === "date") {
          if (!this.evaluateDate(condition, textContent)) {
            return "Failed";
          }
        } else if (condition.type === "texte") {
          if (!this.evaluateTexte(condition, textContent)) {
            return "Failed";
          }
        }
      }
      return "Passed";
    },
    evaluateSurfaceMax(condition, textContent) {
      const regex = new RegExp(`${condition.reference}.*?(${condition.value})`, "i");
      return regex.test(textContent);
    },
    evaluateMontant(condition, textContent) {
      const regex = new RegExp(`${condition.reference}.*?(${condition.value})`, "i");
      return regex.test(textContent);
    },
    evaluateDate(condition, textContent) {
      const regex = new RegExp(`${condition.reference}.*?(\d{2}/\d{2}/\d{4})`, "i");
      return regex.test(textContent);
    },
    evaluateTexte(condition, textContent) {
      return textContent.includes(condition.value);
    },
    generateComments(test) {
      return `The condition ${test.article} was not met. Please check the requirements.`;
    },
    async getEditiques() {
      return editiqueTestsData;
    },
  },
  async created() {
    this.editiqueTests = await this.getEditiques();
  },
};
</script>

<style>
#app {
  font-family: Arial, sans-serif;
  text-align: center;
  color: #333;
  margin-top: 50px;
}
.upload-section {
  margin-bottom: 20px;
}
.results-section {
  margin-top: 20px;
}
.loading {
  font-weight: bold;
  color: #007bff;
}
</style>