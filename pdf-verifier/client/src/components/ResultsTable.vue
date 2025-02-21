<template>
    <Card header="Résultats des tests" class="mb-5">
      <template #content>
        <DataTable :value="results" class="p-datatable-sm">
          <Column field="status" header="Statut">
            <template #body="{ data }">
              <i
                v-if="data.status === 'Passed'"
                class="pi pi-check-circle"
                style="color: green;"
                title="Réussi"
              ></i>
              <i
                v-else-if="data.status === 'Failed'"
                class="pi pi-times-circle"
                style="color: red;"
                title="Échoué"
              ></i>
            </template>
          </Column>
          <Column field="categorie" header="Catégorie" />
          <Column field="article" header="Article" />
          <Column field="comments" header="Commentaires" />
        </DataTable>
      </template>
    </Card>
</template>

<script setup>
import Card from 'primevue/card';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';

const props = defineProps({
    results: {
    type: Array,
    default: () => [],
    },
});
</script>
