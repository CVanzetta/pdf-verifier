<template>
  <v-app>
    <v-container>
      <v-card class="ma-5">
        <v-card-title>
          Outil de Vérification de PDF
        </v-card-title>
        <v-card-text>
          <v-file-input label="Télécharger un PDF" v-model="pdfFile" outlined></v-file-input>
          <v-btn color="primary" @click="analyzePdf" :loading="loading" :disabled="loading || !pdfFile">
            Exécuter les Tests Sélectionnés
          </v-btn>
        </v-card-text>
      </v-card>

      <v-card class="ma-5">
        <v-card-title>
          Sélectionner les Tests à Exécuter
        </v-card-title>
        <v-card-text>
          <v-checkbox
            label="Sélectionner Tous les Tests"
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
          Résultats des Tests
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
      { text: 'Statut', value: 'status' },
      { text: 'Commentaires', value: 'comments' },
    ];

    const analyzePdf = async () => {
      console.log("Analyse du PDF commencée...");

      if (!pdfFile.value) {
        console.error("Veuillez télécharger un fichier PDF avant de lancer l'analyse.");
        return;
      }

      if (pdfFile.value.size > 10 * 1024 * 1024) { // Limite de taille de fichier à 10 Mo
        console.error("Le fichier téléchargé est trop volumineux. Veuillez télécharger un fichier de moins de 10 Mo.");
        return;
      }

      if (selectedTests.value.length === 0) {
        console.error("Aucun test sélectionné. Veuillez sélectionner au moins un test à exécuter.");
        return;
      }

      console.log("Tests sélectionnés :", selectedTests.value);
      loading.value = true;

      try {
        const arrayBuffer = await pdfFile.value.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        let textContent = "";

        for (let i = 1; i <= pdf.numPages; i++) {
          console.log(`Analyse de la page ${i} sur ${pdf.numPages}...`);
          const page = await pdf.getPage(i);
          const text = await page.getTextContent();
          textContent += text.items.map(item => item.str).join(" ") + " ";
        }

        textContent = preprocessText(textContent);
        console.log("Contenu extrait du PDF :", textContent);

        results.value = selectedTests.value.map((test) => {
          const status = evaluateEditique(test, textContent);
          return { ...test, status, comments: status === "Failed" ? generateComments(test) : "" };
        });
        console.log("Résultats après analyse :", results.value);
      } catch (error) {
        console.error("Une erreur est survenue lors de l'analyse du PDF. Veuillez vous assurer que le fichier n'est pas corrompu.");
        console.error(error);
      } finally {
        loading.value = false;
      }
    };

    const preprocessText = (text) => {
      return text
        .toLowerCase()
        .normalize("NFD").replace(/[̀-ͯ]/g, "") // Suppression des accents
        .replace(/\s+/g, " ") // Normalisation des espaces
        .trim();
    };

    const evaluateEditique = (test, textContent) => {
      console.log(`Évaluation du test : ${test.article}`);
      const conditions = test.conditions;
      for (const condition of conditions) {
        console.log(`Vérification du type de condition : ${condition.type}`);
        if (condition.type === "surface_max") {
          if (!evaluateSurfaceMax(condition, textContent)) {
            console.log(`Échec de la condition surface_max pour le test : ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "montant_max") {
          if (!evaluateMontantMax(condition, textContent)) {
            console.log(`Échec de la condition montant_max pour le test : ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "texte_present") {
          if (!evaluateTextePresent(condition, textContent)) {
            console.log(`Échec de la condition texte_present pour le test : ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "garantie") {
          if (!evaluateGarantie(condition, textContent)) {
            console.log(`Échec de la condition garantie pour le test : ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "engagement_max") {
          if (!evaluateEngagementMax(condition, textContent)) {
            console.log(`Échec de la condition engagement_max pour le test : ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "valeur_max") {
          if (!evaluateValeurMax(condition, textContent)) {
            console.log(`Échec de la condition valeur_max pour le test : ${test.article}`);
            return "Failed";
          }
        } else if (condition.type === "specific_text_presence") {
          if (!evaluateSpecificTextPresence(condition, textContent)) {
            console.log(`Échec de la condition specific_text_presence pour le test : ${test.article}`);
            return "Failed";
          }
        } else {
          console.warn(`Type de condition inconnu : ${condition.type}`);
          return "Failed";
        }
      }
      console.log(`Toutes les conditions sont validées pour le test : ${test.article}`);
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

    const evaluateSpecificTextPresence = (condition, textContent) => {
      return condition.values.every(val => textContent.includes(val.toLowerCase()));
    };

    const generateComments = (test) => {
      return `La condition ${test.article} n'a pas été respectée. Veuillez vérifier les exigences.`;
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
      console.log("Tests sélectionnés après toggleSelectAll :", selectedTests.value);
    };

    const toggleTestSelection = (test) => {
      const index = selectedTests.value.findIndex(selectedTest => selectedTest.id === test.id);
      if (index === -1) {
        selectedTests.value.push(test);
      } else {
        selectedTests.value.splice(index, 1);
      }
      console.log("Tests sélectionnés mis à jour après toggleTestSelection :", selectedTests.value);
    };

    onMounted(async () => {
      console.log("Monté et chargement des tests d'édition...");
      editiqueTests.categories = await testData.categories;
      console.log("Tests d'édition chargés :", editiqueTests.categories);
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
