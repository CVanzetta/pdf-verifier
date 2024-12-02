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
          <v-expansion-panels>
            <v-expansion-panel v-for="(category, index) in editiqueTests.categories" :key="index">
              <v-expansion-panel-title>{{ category.nom }}</v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-list>
                  <v-list-item-group>
                    <v-list-item v-for="test in filterImportantTests(category.tests)" :key="test.id">
                      <v-checkbox :label="test.categorie + ' - ' + test.article" :value="test" v-model="selectedTests"></v-checkbox>
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
import * as pdfjsLib from 'pdfjs-dist/build/pdf';
import editiqueTestsData from '@/assets/editiqueTests.json';

// Configurez le worker depuis un CDN
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;

export default {
  name: "App",
  setup() {
    const pdfFile = ref(null);
    const editiqueTests = reactive(editiqueTestsData);
    const selectedTests = ref([]);
    const results = ref([]);
    const loading = ref(false);
    const tableHeaders = [
      { text: 'Test', value: 'categorie' },
      { text: 'Status', value: 'status' },
      { text: 'Comments', value: 'comments' },
    ];

    const handleFileUpload = (event) => {
      if (event && event instanceof File) {
        pdfFile.value = event;
      }
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

    const filterImportantTests = (tests) => {
      const importantTests = [
        "Frais réels justifiés dans la limite de 300 FFB sans excéder pour les honoraires d'expert 5% de l'indemnité jusqu’à 250 fois l’indice et 2,5% au-delà de 250 fois l’indice, pour les pertes indirectes 10% de l’indemnité",
        "25% du capital assuré en Incendie, porté à 35% si les locaux professionnels sont protégés conformément aux clauses 15, 15A, 16A, 17 ou 17A, avec un minimum de 25 FFB et un maximum de 155 FFB, sans excéder ni les sous-limites prévues ci-dessus en Incendie, Dégâts des eaux, Tempête… ni celles fixées ci-après :",
        "Risques environnementaux : 400 000 € non indexés, tous dommages confondus, par sinistre et par année d'assurance, avec des sous-limites spécifiques pour chaque type de dommage.",
        "Perte d’exploitation – art.19 :",
        "Profession libérale : 200 FFB (jusqu'à 1000 FFB), franchise relative de 3 jours ouvrés, période d’indemnisation de 12 mois",
        "Entreprise : 500 FFB (jusqu'à 1500 FFB)",
        "Perte d’exploitation étendue – art 32A :",
        "Même limite que celle de la perte d’exploitation de base – art.19 – sans excéder en cas de :",
        "Interdiction, difficultés ou impossibilité d’accès aux locaux professionnels : 10% de la limite ci-dessus, franchise relative de 3 jours ouvrés, période d’indemnisation de 18 mois"
      ];
      return tests.filter(test => importantTests.includes(test.article));
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
      tableHeaders,
      handleFileUpload,
      analyzePdf,
      filterImportantTests,
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
