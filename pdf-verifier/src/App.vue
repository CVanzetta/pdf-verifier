<template>
  <div id="app">
    <!-- Use only the main container or main view here. -->
    <RefactoredEditique />
  </div>
</template>

<script>
import RefactoredEditique from '@/views/RefactoredEditique.vue';

export default {
  name: 'App',
  components: {
    RefactoredEditique
  }
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