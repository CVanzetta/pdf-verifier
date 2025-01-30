<template>
    <Card header="Sélectionner les tests à exécuter" class="mb-5">
    <template #content>
        <div class="flex items-center gap-2 mb-4">
        <Checkbox v-model="localSelectAll" @change="toggleSelectAll" :binary="true" />
        <label class="cursor-pointer select-none">
            Sélectionner tous les tests disponibles
        </label>
        </div>

        <Accordion :multiple="true">
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
                    <Checkbox v-model="localSelectedTests" :value="test.id" @change="emitLocalData" />
                    <span>{{ test.categorie + ' - ' + test.article }}</span>
                    <i class="pi pi-info-circle ml-2 text-blue-500"></i>
                    </li>
                </ul>
                </div>
            </div>
            <div v-else>
                <ul class="list mt-2">
                <li
                    v-for="test in filterImportantTests(category.tests)"
                    :key="test.id"
                    class="flex items-center gap-2"
                >
                    <Checkbox v-model="localSelectedTests" :value="test.id" @change="emitLocalData" />
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
import { ref, onMounted } from 'vue';
import Card from 'primevue/card';
import Checkbox from 'primevue/checkbox';
import Accordion from 'primevue/accordion';
import AccordionPanel from 'primevue/accordionpanel';
import AccordionHeader from 'primevue/accordionheader';
import AccordionContent from 'primevue/accordioncontent';

const props = defineProps({
    editiqueTests: {
    type: Object,
    default: () => ({ categories: [] })
    },
    // The parent is the single source of truth:
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

const emit = defineEmits(['update:selectedTests','update:selectedCategories','update:selectAll']);

  // Local copies for internal UI state
const localSelectedTests = ref([]);
const localSelectedCategories = ref([]);
const localSelectAll = ref(false);

  // Initialize local states from props exactly once
onMounted(() => {
    localSelectedTests.value = [...props.selectedTests];
    localSelectedCategories.value = [...props.selectedCategories];
    localSelectAll.value = props.selectAll;
});

  // Emit local copies upward anytime they're updated
function emitLocalData() {
    emit('update:selectedTests', localSelectedTests.value);
    emit('update:selectedCategories', localSelectedCategories.value);
    emit('update:selectAll', localSelectAll.value);
}

  // Toggle all tests
function toggleSelectAll() {
    const allTestIds = getAllTestIds();
    if (localSelectAll.value) {
    localSelectedTests.value = allTestIds;
    localSelectedCategories.value = props.editiqueTests.categories.map(c => c.nom);
    } else {
    localSelectedTests.value = [];
    localSelectedCategories.value = [];
    }
    emitLocalData();
    }

function toggleCategorySelection(category) {
    const isSelected = localSelectedCategories.value.includes(category.nom);
    const categoryTests = getCategoryTestIds(category);

    if (isSelected) {
      // add them
      const merged = new Set([...localSelectedTests.value, ...categoryTests]);
      localSelectedTests.value = Array.from(merged);
    } else {
      // remove them
      localSelectedTests.value = localSelectedTests.value.filter(id => !categoryTests.includes(id));
    }
    emitLocalData();
  }
  
  // Helpers
  function filterImportantTests(tests) {
    return tests.filter(test => test.conditions && test.conditions.length > 0);
  }
  
  function getAllTestIds() {
    const ids = [];
    for (const cat of props.editiqueTests.categories) {
      if (cat.sousCategories?.length > 0) {
        for (const sc of cat.sousCategories) {
          ids.push(...sc.tests.map(t => t.id));
        }
      } else {
        ids.push(...cat.tests.map(t => t.id));
      }
    }
    return ids;
  }
  
  function getCategoryTestIds(category) {
    const tests = [];
    if (category.sousCategories?.length > 0) {
      for (const sc of category.sousCategories) {
        tests.push(...sc.tests.map(t => t.id));
      }
    } else {
      tests.push(...category.tests.map(t => t.id));
    }
    return tests;
  }
  </script>