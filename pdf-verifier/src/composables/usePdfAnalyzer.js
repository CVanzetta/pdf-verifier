// usePdfAnalyzer.js
import * as pdfjsLib from 'pdfjs-dist';

// Make sure you correctly provide the worker path
pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';

export default function usePdfAnalyzer() {
  const analyzePdfFile = async (pdfFile, selectedTests, editiqueTests) => {
    if (!pdfFile) {
      console.error('Veuillez téléverser un fichier PDF avant de lancer l\'analyse.');
      return [];
    }

    if (pdfFile.size > 10 * 1024 * 1024) {
      console.error('Le fichier téléversé est trop volumineux (max 10Mo).');
      return [];
    }

    if (selectedTests.length === 0) {
      console.error('Aucun test sélectionné. Veuillez sélectionner au moins un test.');
      return [];
    }

    try {
      const arrayBuffer = await pdfFile.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      console.log(`PDF chargé. Nombre de pages : ${pdf.numPages}`);

      // Extract text from PDF
      let textContent = '';
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const text = await page.getTextContent();
        const pageText = text.items.map((item) => item.str).join(' ');
        textContent += pageText + ' ';
      }
      textContent = normalizeText(textContent);

      // Flatten all tests
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

      // Evaluate
      const results = selectedTests.map((testId) => {
        const test = allTests.find((t) => t.id === testId);
        if (!test) {
          console.error(`Test avec l'ID ${testId} introuvable.`);
          return null;
        }
        const status = evaluateEditique(test, textContent);
        return {
          ...test,
          status,
          comments: status === 'Failed' ? generateComments(test) : ''
        };
      }).filter((r) => r !== null);

      return results;
    } catch (error) {
      console.error('Une erreur s\'est produite lors de l\'analyse du PDF:', error);
      throw error;
    }
  };

  const normalizeText = (text) => {
    return text
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\\u0300-\\u036f]/g, '') // accents
      .replace(/\\s+/g, ' ')
      .trim();
  };

  // Main test evaluation logic
  const evaluateEditique = (test, textContent) => {
    if (!test.conditions || test.conditions.length === 0) {
      console.warn('Aucune condition trouvée pour le test:', test.id);
      return 'Passed';
    }

    for (const condition of test.conditions) {
      const type = condition.type || '';
      let passed = false;

      switch (type) {
        case 'surface_max':
          passed = evaluateSurfaceMax(condition, textContent);
          break;
        case 'montant':
          passed = evaluateMontant(condition, textContent);
          break;
        case 'date':
          passed = evaluateDate(condition, textContent);
          break;
        case 'texte':
        case 'texte_present':
          passed = evaluateTexte(condition, textContent);
          break;
        case 'texte_multi_colonnes':
          passed = evaluateTexteMultiColonnes(condition, textContent);
          break;
        default:
          console.error('Type de condition inconnu :', type);
          return 'Failed';
      }

      if (!passed) {
        return 'Failed';
      }
    }

    return 'Passed';
  };

  // Condition evaluations
  const evaluateSurfaceMax = (condition, textContent) => {
    const ref = normalizeText(condition.reference || '');
    const val = normalizeText(condition.value || '');
    const regex = new RegExp(`${ref}.*?(${val})`, 'i');
    return regex.test(textContent);
  };

  const evaluateMontant = (condition, textContent) => {
    const ref = normalizeText(condition.reference || '');
    // Adjust the regex to suit your needs
    const regex = new RegExp(`${ref}.*?(\\d{1,3}(?:[.,]\\d{3})*(?:[.,]\\d{2})?)`, 'i');
    return regex.test(textContent);
  };

  const evaluateDate = (condition, textContent) => {
    const ref = normalizeText(condition.reference || '');
    const regex = new RegExp(`${ref}.*?(\\d{2}/\\d{2}/\\d{4})`, 'i');
    return regex.test(textContent);
  };

  const evaluateTexte = (condition, textContent) => {
    const val = normalizeText(condition.value || '');
    return textContent.includes(val);
  };

  const evaluateTexteMultiColonnes = (condition, textContent) => {
    const normalizedText = normalizeText(textContent);
    const values = (condition.values || []).map((v) => normalizeText(v));

    return values.every((val) => normalizedText.includes(val));
  };

  // Fail comment
  const generateComments = (test) => {
    return `La condition ${test.article} n'a pas été remplie. Veuillez vérifier les exigences.`;
  };

  return {
    analyzePdfFile
  };
}
