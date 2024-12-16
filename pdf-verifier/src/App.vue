<template>
  <div class ="mx-4 md:mx-10 lg:mx-20 xl:mx-60">
  <div class="component">
    <div class="grid">
      <!-- Outil de vérification PDF -->
      <div class="col-12">
        <Card header="Outil de vérification PDF" class="mb-5">
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
                  <span v-if="pdfFile">Fichier sélectionné : {{ pdfFile.name }}</span>
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
                  <div class="flex items-center justify-center rounded-full border-4 border-gray-300 h-32 w-32">
                    <i class="pi pi-cloud-upload text-gray-500" style="font-size:4rem;"></i>
                  </div>
                  <p class="mt-6 mb-0 text-lg font-semibold">Glissez-déposez le fichiers ici</p>
                </div>
              </template>
            </FileUpload>

            <Button
              label="Lancer les tests sélectionnés"
              icon="pi pi-play"
              class="mt-3"
              :loading="loading"
              :disabled="loading || !pdfFile || selectedTests.length === 0"
              @click="analyzePdf"
            ></Button>
          </template>
        </Card>
      </div>

      <!-- Sélectionner les tests à exécuter -->
      <div class="col-12">
        <Card header="Sélectionner les tests à exécuter" class="mb-5">
          <template #content>
            <!-- Checkbox globale pour sélectionner tous les tests -->
            <div class="flex items-center gap-2 mb-4">
              <Checkbox
                :binary="true"
                v-model="selectAll"
                @change="toggleSelectAll"
              ></Checkbox>
              <label @click="$emit('click')" class="cursor-pointer select-none">
                Sélectionner tous les tests disponibles
              </label>
            </div>

            <Accordion :value= multiple>
              <AccordionPanel
                v-for="(category, index) in editiqueTests.categories"
                :key="index"
                :value="index.toString()"
              >
                <AccordionHeader>
                  <div class="flex items-center gap-2">
                    <!-- Checkbox pour la catégorie -->
                    <Checkbox
                      v-model="selectedCategories"
                      :value="category.nom"
                      @change="toggleCategorySelection(category)"
                    />
                    <span>{{ category.nom }}</span>
                  </div>
                </AccordionHeader>
                <AccordionContent>
                  <!-- Si la catégorie possède des sous-catégories -->
                  <div v-if="category.sousCategories && category.sousCategories.length > 0">
                    <div
                      v-for="sc in category.sousCategories"
                      :key="sc.nom"
                      class="mt-2 border-t pt-2"
                    >
                      <div class="font-semibold">{{ sc.nom }}</div>
                      <ul class="list mt-2 ml-4">
                        <li v-for="test in filterImportantTests(sc.tests)" :key="test.id" class="flex items-center gap-2">
                          <Checkbox
                            v-model="selectedTests"
                            :value="test.id"
                            @change="toggleTestSelection"
                          />
                          <span>{{ test.categorie + ' - ' + test.article }}</span>
                          <i class="pi pi-info-circle ml-2 text-blue-500"></i>
                        </li>
                      </ul>
                    </div>
                  </div>
                  

                  <!-- Sinon affichage direct des tests -->
                  <div v-else>
                    <ul class="list mt-2">
                      <li v-for="test in filterImportantTests(category.tests)" :key="test.id" class="flex items-center gap-2">
                        <Checkbox
                          v-model="selectedTests"
                          :value="test.id"
                          @change="toggleTestSelection"
                        />
                        <span>{{ test.categorie + ' - ' + test.article }}</span>
                        <i class="pi pi-info-circle ml-2 text-blue-500"></i>
                      </li>
                    </ul>
                  </div>
                </AccordionContent>
              </AccordionPanel>
            </Accordion>
          </template>
        </Card>
      </div>

      <!-- Résultats des tests -->
      <div class="col-12" v-if="results.length > 0">
        <Card header="Résultats des tests" class="mb-5">
          <template #content>
            <DataTable :value="results">
              <Column field="status" header="Statut">
                <template #body="{ data }">
                  <i
                    v-if="data.status === 'Passed'"
                    class="pi pi-check-circle"
                    style="color: green;"
                    title="Réussi"
                  ></i>
                  <i
                    v-if="data.status === 'Failed'"
                    class="pi pi-times-circle"
                    style="color: red;"
                    title="Échoué"
                  ></i>
                </template>
              </Column>
              <Column field="categorie" header="Catégorie"></Column>
              <Column field="article" header="Article"></Column>
              <Column field="comments" header="Commentaires"></Column>
            </DataTable>
          </template>
        </Card>
      </div>
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
const selectedCategories = ref([]);
const selectAll = ref(false);
const results = ref([]);
const loading = ref(false);

const normalizeText = (text) => {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // accents
    .replace(/\s+/g, ' ')
    .trim();
};

const onFileSelect = (event) => {
  if (event.files.length > 0) {
    pdfFile.value = event.files[event.files.length - 1];
    event.files.splice(0, event.files.length, pdfFile.value);
    console.log("Fichier sélectionné :", pdfFile.value.name);
  }
};

const onRemoveFile = () => {
  pdfFile.value = null;
  console.log("Fichier retiré");
};

const analyzePdf = async () => {
  console.log("Analyse du PDF en cours...");
  if (!pdfFile.value) {
    console.error("Veuillez téléverser un fichier PDF avant de lancer l'analyse.");
    return;
  }

  if (pdfFile.value.size > 10 * 1024 * 1024) {
    console.error("Le fichier téléversé est trop volumineux. Veuillez fournir un fichier de moins de 10Mo.");
    return;
  }

  if (selectedTests.value.length === 0) {
    console.error("Aucun test sélectionné. Veuillez sélectionner au moins un test.");
    return;
  }

  console.log("Tests sélectionnés :", selectedTests.value);
  loading.value = true;

  try {
    const arrayBuffer = await pdfFile.value.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
    console.log(`PDF chargé. Nombre de pages : ${pdf.numPages}`);

    let textContent = "";
    for (let i = 1; i <= pdf.numPages; i++) {
      console.log(`Analyse de la page ${i}/${pdf.numPages}...`);
      const page = await pdf.getPage(i);
      const text = await page.getTextContent();
      const pageText = text.items.map(item => item.str).join(" ");
      textContent += pageText + " ";
    }

    textContent = normalizeText(textContent);
    console.log("Texte extrait du PDF :", textContent);

    if (!textContent || textContent.length === 0) {
      console.warn("Aucun texte n'a été extrait du PDF. Vérifiez que le PDF est sélectionnable ou utilisez un OCR.");
    }

    // Récupérer tous les tests (y compris ceux dans les sous-catégories)
    const allTests = [];
    for (const category of editiqueTests.categories) {
      if (category.sousCategories && category.sousCategories.length > 0) {
        for (const sc of category.sousCategories) {
          allTests.push(...sc.tests);
        }
      } else {
        allTests.push(...category.tests);
      }
    }

    results.value = selectedTests.value.map((testId) => {
      const test = allTests.find(t => t.id === testId);
      if (!test) {
        console.error(`Test avec l'ID ${testId} introuvable.`);
        return null;
      }
      const status = evaluateEditique(test, textContent);
      return { ...test, status, comments: status === "Failed" ? generateComments(test) : "" };
    }).filter(r => r !== null);

    console.log("Résultats finaux :", results.value);
  } catch (error) {
    console.error("Une erreur s'est produite lors de l'analyse du PDF.");
    console.error(error);
  } finally {
    loading.value = false;
  }
};

const evaluateEditique = (test, textContent) => {
  console.log("Évaluation du test :", test);
  console.log("Contenu texte pour le test :", textContent);

  if (!test.conditions || test.conditions.length === 0) {
    console.warn("Aucune condition trouvée pour le test :", test.id);
    return "Passed";
  }

  for (const condition of test.conditions) {
    const type = condition.type || "";
    console.log("Vérification de la condition :", condition);

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
        console.error("Type de condition inconnu :", type);
        return "Failed";
    }

    if (!passed) {
      console.log(`Condition échouée : ${type}`, condition);
      return "Failed";
    }
  }

  console.log("Toutes les conditions sont satisfaites pour le test :", test.id);
  return "Passed";
};

const evaluateSurfaceMax = (condition, textContent) => {
  const ref = normalizeText(condition.reference || "");
  const val = normalizeText(condition.value || "");
  const regex = new RegExp(`${ref}.*?(${val})`, "i");
  const result = regex.test(textContent);
  console.log(`Évaluation surface_max avec regex ${regex} : ${result}`);
  return result;
};

const evaluateMontant = (condition, textContent) => {
  const ref = normalizeText(condition.reference || "");
  // Ajustez la regex selon vos besoins
  const regex = new RegExp(`${ref}.*?(\\d{1,3}(?:[.,]\\d{3})*(?:[.,]\\d{2})?)`, "i");
  const result = regex.test(textContent);
  console.log(`Évaluation montant avec regex ${regex} : ${result}`);
  return result;
};

const evaluateDate = (condition, textContent) => {
  const ref = normalizeText(condition.reference || "");
  const regex = new RegExp(`${ref}.*?(\\d{2}/\\d{2}/\\d{4})`, "i");
  const result = regex.test(textContent);
  console.log(`Évaluation date avec regex ${regex} : ${result}`);
  return result;
};

const evaluateTexte = (condition, textContent) => {
  const val = normalizeText(condition.value || "");
  const found = textContent.includes(val);
  console.log(`Évaluation texte : "${val}" dans le texte extrait : ${found}`);
  return found;
};

const evaluateTexteMultiColonnes = (condition, textContent) => {
  const normalizedText = normalizeText(textContent);
  const values = (condition.values || []).map(v => normalizeText(v));

  const allFound = values.every(val => {
    const found = normalizedText.includes(val);
    console.log(`Vérification multi-colonnes pour "${val}" : ${found}`);
    return found;
  });

  return allFound;
};

const generateComments = (test) => {
  return `La condition ${test.article} n'a pas été remplie. Veuillez vérifier les exigences.`;
};

const toggleSelectAll = () => {
  const allTestIds = [];
  for (const category of editiqueTests.categories) {
    if (category.sousCategories && category.sousCategories.length > 0) {
      for (const sc of category.sousCategories) {
        allTestIds.push(...sc.tests.map(t => t.id));
      }
    } else {
      allTestIds.push(...category.tests.map(t => t.id));
    }
  }

  if (selectAll.value) {
    selectedTests.value = allTestIds;
    selectedCategories.value = editiqueTests.categories.map(cat => cat.nom);
  } else {
    selectedTests.value = [];
    selectedCategories.value = [];
  }
  console.log("Tests sélectionnés après sélection globale :", selectedTests.value);
};

const toggleCategorySelection = (category) => {
  const isSelected = selectedCategories.value.includes(category.nom);
  let categoryTests = [];
  if (category.sousCategories && category.sousCategories.length > 0) {
    for (const sc of category.sousCategories) {
      categoryTests.push(...sc.tests.map(t => t.id));
    }
  } else {
    categoryTests = category.tests.map(t => t.id);
  }

  if (isSelected) {
    // Ajouter tous les tests de cette catégorie
    selectedTests.value = Array.from(new Set([...selectedTests.value, ...categoryTests]));
  } else {
    // Retirer tous les tests de cette catégorie
    selectedTests.value = selectedTests.value.filter(id => !categoryTests.includes(id));
  }

  updateSelectAllCheckbox();
  console.log("Tests sélectionnés après sélection de catégorie :", selectedTests.value);
};

const toggleTestSelection = () => {
  updateCategorySelection();
  updateSelectAllCheckbox();
};

const updateSelectAllCheckbox = () => {
  const allTestIds = [];
  for (const category of editiqueTests.categories) {
    if (category.sousCategories) {
      for (const sc of category.sousCategories) {
        allTestIds.push(...sc.tests.map(t => t.id));
      }
    } else {
      allTestIds.push(...category.tests.map(t => t.id));
    }
  }

  selectAll.value = allTestIds.length > 0 && allTestIds.every(id => selectedTests.value.includes(id));
};

const updateCategorySelection = () => {
  // Mettre à jour les catégories sélectionnées
  const newlySelectedCategories = [];
  for (const category of editiqueTests.categories) {
    let categoryTests = [];
    if (category.sousCategories && category.sousCategories.length > 0) {
      for (const sc of category.sousCategories) {
        categoryTests.push(...sc.tests.map(t => t.id));
      }
    } else {
      categoryTests = category.tests.map(t => t.id);
    }
    if (categoryTests.length > 0 && categoryTests.every(id => selectedTests.value.includes(id))) {
      newlySelectedCategories.push(category.nom);
    }
  }
  selectedCategories.value = newlySelectedCategories;
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
