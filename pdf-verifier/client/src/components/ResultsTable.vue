<template>
    <Card header="Résultats des tests" class="mb-5">
      <template #content>
        <DataTable :value="results" class="p-datatable-sm" scrollable scrollHeight="400px">
          <!-- Colonne pour le statut des tests -->
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
              <i
                v-else
                class="pi pi-question-circle"
                style="color: gray;"
                title="Non testé"
              ></i>
            </template>
          </Column>
  
          <!-- Colonne pour la catégorie -->
          <Column field="categorie" header="Catégorie" />
  
          <!-- Colonne pour l'article de référence -->
          <Column field="article" header="Article" />
  
          <!-- Colonne pour afficher les commentaires détaillés -->
          <Column field="comments" header="Commentaires">
            <template #body="{ data }">
              <span v-if="data.comments && data.comments.length > 0">
                {{ data.comments }}
              </span>
              <span v-else class="text-gray-500 italic">Aucun commentaire</span>
            </template>
          </Column>
  
          <!-- Colonne pour afficher les détails de l'erreur -->
          <Column field="errorDetails" header="Détails de l'erreur">
            <template #body="{ data }">
              <span v-if="data.errorDetails">
                {{ data.errorDetails }}
              </span>
              <span v-else class="text-gray-500 italic">Aucun</span>
            </template>
          </Column>
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
  
  <style scoped>
  /* Mise en forme du DataTable */
  .p-datatable-sm {
    font-size: 0.9rem;
  }
  
  /* Style pour les textes d'information */
  .text-gray-500 {
    color: #6b7280;
  }
  </style>
  