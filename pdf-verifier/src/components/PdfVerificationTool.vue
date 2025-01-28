<template>
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
        <!-- Header Slot -->
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

        <!-- Content Slot -->
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

        <!-- Empty Slot -->
        <template #empty>
            <div class="flex flex-col items-center justify-center text-center py-10">
            <div class="flex items-center justify-center rounded-full border-4 border-gray-300 h-32 w-32">
                <i class="pi pi-cloud-upload text-gray-500" style="font-size:4rem;"></i>
            </div>
            <p class="mt-6 mb-0 text-lg font-semibold">
                Glissez-déposez les fichiers ici
            </p>
            </div>
        </template>
        </FileUpload>

        <Button
        label="Lancer les tests sélectionnés"
        icon="pi pi-play"
        class="mt-3"
        :loading="loading"
        :disabled="loading || !pdfFile || !selectedTests || selectedTests.length === 0"
        @click="$emit('analyzePdf')"
        />
    </template>
    </Card>
</template>

    <script setup>
import { computed } from 'vue';
import FileUpload from 'primevue/fileupload';
import Button from 'primevue/button';
import Card from 'primevue/card';

  // Props
const props = defineProps({
    pdfFile: {
        type: Object,
        default: null
    },
    loading: {
        type: Boolean,
        default: false
    },
    selectedTests: {
        type: Array,
        default: () => []
    }
});

  // Emits
const emit = defineEmits(['update:pdfFile', 'analyzePdf']);

  // Methods
    function onFileSelect(event) {
    if (event.files.length > 0) {
        const file = event.files[event.files.length - 1];
        emit('update:pdfFile', file);
      // Restrict to only one file
        event.files.splice(0, event.files.length, file);
        console.log('Fichier sélectionné:', file?.name);
    }
}

    function onRemoveFile() {
    emit('update:pdfFile', null);
    console.log('Fichier retiré');
}

</script>