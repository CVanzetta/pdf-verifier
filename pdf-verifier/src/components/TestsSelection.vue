<template>
    <Card header="Sélectionner les tests à exécuter" class="mb-5">
      <template #content>
  
        <!-- Checkbox globale pour sélectionner tous les tests -->
        <div class="flex items-center gap-2 mb-4">
          <Checkbox
            :binary="true"
            v-model="localSelectAll"
            @change="toggleSelectAll"
          />
          <label @click="$emit('click')" class="cursor-pointer select-none">
            Sélectionner tous les tests disponibles
          </label>
        </div>
  
        <!-- Accordions for categories and sub-categories -->
        <Accordion :value="multiple">
          <AccordionPanel
            v-for="(category, index) in editiqueTests.categories"
            :key="index"
            :value="index.toString()"
          >
            <AccordionHeader>
              <div class="flex items-center gap-2">
                <Checkbox
                  v-model="localSelectedCategories"
                  :value="category.nom"
                  @change="() => toggleCategorySelection(category)"
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
                    <li
                      v-for="test in filterImportantTests(sc.tests)"
                      :key="test.id"
                      class="flex items-center gap-2"
                    >
                      <Checkbox
                        v-model="localSelectedTests"
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
                  <li
                    v-for="test in filterImportantTests(category.tests)"
                    :key="test.id"
                    class="flex items-center gap-2"
                  >
                    <Checkbox
                      v-model="localSelectedTests"
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
  </template>
  
  <script setup>
  import { ref, watch, computed } from 'vue';
  import Card from 'primevue/card';
  import Checkbox from 'primevue/checkbox';
  import Accordion from 'primevue/accordion';
  import AccordionPanel from 'primevue/accordionpanel';
  import AccordionHeader from 'primevue/accordionheader';
  import AccordionContent from 'primevue/accordioncontent';
  
  // Props
  const props = defineProps({
    editiqueTests: {
      type: Object,
      default: () => ({ categories: [] })
    },
    selectedTests: {
      type: Array,
      default: () => []
    },
    selectedCategories: {
      type: Array,
      default: () => []
    },
    selectAll: {
      type: Boolean,
      default: false
    }
  });
  
  // Emits
  const emit = defineEmits([
    'update:selectedTests',
    'update:selectedCategories',
    'update:selectAll'
  ]);
  
  // Local refs to track internal states & watchers
  const localSelectedTests = ref([...props.selectedTests]);
  const localSelectedCategories = ref([...props.selectedCategories]);
  const localSelectAll = ref(props.selectAll);
  
  // Watch for prop changes from parent
  watch(
    () => props.selectedTests,
    (newVal) => {
      localSelectedTests.value = [...newVal];
    }
  );
  watch(
    () => props.selectedCategories,
    (newVal) => {
      localSelectedCategories.value = [...newVal];
    }
  );
  watch(
    () => props.selectAll,
    (newVal) => {
      localSelectAll.value = newVal;
    }
  );
  
  // Watch for local changes to update parent
  watch(localSelectedTests, (newVal) => {
    emit('update:selectedTests', newVal);
    updateCategorySelection();
    updateSelectAllCheckbox();
  });
  watch(localSelectedCategories, (newVal) => {
    emit('update:selectedCategories', newVal);
    updateSelectAllCheckbox();
  });
  watch(localSelectAll, (newVal) => {
    emit('update:selectAll', newVal);
  });
  
  // Methods
  function toggleSelectAll() {
    const allTestIds = getAllTestIds();
    if (localSelectAll.value) {
      localSelectedTests.value = [...allTestIds];
      localSelectedCategories.value = props.editiqueTests.categories.map((cat) => cat.nom);
    } else {
      localSelectedTests.value = [];
      localSelectedCategories.value = [];
    }
  }
  
  function toggleCategorySelection(category) {
    const isSelected = localSelectedCategories.value.includes(category.nom);
    let categoryTests = [];
  
    if (category.sousCategories && category.sousCategories.length > 0) {
      for (const sc of category.sousCategories) {
        categoryTests.push(...sc.tests.map((t) => t.id));
      }
    } else {
      categoryTests = category.tests.map((t) => t.id);
    }
  
    if (isSelected) {
      // Add all tests of this category
      localSelectedTests.value = Array.from(new Set([...localSelectedTests.value, ...categoryTests]));
    } else {
      // Remove all tests of this category
      localSelectedTests.value = localSelectedTests.value.filter((id) => !categoryTests.includes(id));
    }
    updateSelectAllCheckbox();
  }
  
  function toggleTestSelection() {
    updateCategorySelection();
    updateSelectAllCheckbox();
  }
  
  function updateSelectAllCheckbox() {
    const allTestIds = getAllTestIds();
    localSelectAll.value =
      allTestIds.length > 0 && allTestIds.every((id) => localSelectedTests.value.includes(id));
  }
  
  function updateCategorySelection() {
    const newlySelectedCategories = [];
    for (const category of props.editiqueTests.categories) {
      let categoryTests = [];
      if (category.sousCategories && category.sousCategories.length > 0) {
        for (const sc of category.sousCategories) {
          categoryTests.push(...sc.tests.map((t) => t.id));
        }
      } else {
        categoryTests = category.tests.map((t) => t.id);
      }
      if (
        categoryTests.length > 0 &&
        categoryTests.every((id) => localSelectedTests.value.includes(id))
      ) {
        newlySelectedCategories.push(category.nom);
      }
    }
    localSelectedCategories.value = newlySelectedCategories;
  }
  
  function filterImportantTests(tests) {
    return tests.filter((test) => test.conditions && test.conditions.length > 0);
  }
  
  function getAllTestIds() {
    const allTestIds = [];
    for (const category of props.editiqueTests.categories) {
      if (category.sousCategories && category.sousCategories.length > 0) {
        for (const sc of category.sousCategories) {
          allTestIds.push(...sc.tests.map((t) => t.id));
        }
      } else {
        allTestIds.push(...category.tests.map((t) => t.id));
      }
    }
    return allTestIds;
  }
  </script>
  