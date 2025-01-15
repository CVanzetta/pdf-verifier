📝 PDF Test Validator
✨ Description
Cette application permet de vérifier des fichiers PDF en fonction de tests prédéfinis. Elle est développée avec PrimeVue et propose une interface simple pour :

📂 Téléverser un PDF
✅ Exécuter des tests
📊 Afficher les résultats
🚀 Installation
Clonez le projet 🛠️ :

bash
Copier le code
git clone [<URL_DU_DEPOT>](https://github.com/CVanzetta/pdf-verifier.git)
Installez les dépendances 📦 :

bash
Copier le code
npm install
Lancez le serveur 🖥️ :

bash
Copier le code
npm run serve
Accédez à l'application 🌐 :
Ouvrez http://localhost:8080 dans votre navigateur.

➕ Ajouter un test
Les tests sont définis dans le fichier JSON situé à :
src/assets/Tests.json.

Exemple d’ajout :
json
Copier le code
{
  "categories": [
    {
      "nom": "Nouvelle Catégorie",
      "tests": [
        {
          "id": 9,
          "article": "Article Exemple",
          "conditions": [
            {
              "type": "texte",
              "value": "Texte à rechercher"
            }
          ]
        }
      ]
    }
  ]
}
📋 Étapes :
Ouvrez le fichier Tests.json.
Ajoutez une nouvelle catégorie ou un test dans une catégorie existante.
Renseignez les conditions du test :
type : Type de vérification (texte, montant, date, etc.).
value : Valeur à chercher dans le PDF.
Sauvegardez vos modifications.
🛠️ Résolution de l’erreur API version does not match the Worker version
⚠️ Problème :
Si vous voyez cette erreur :

lua
Copier le code
UnknownErrorException: The API version "X" does not match the Worker version "Y".
📝 Solution :
Vérifiez la version installée 📦 :

bash
Copier le code
npm ls pdfjs-dist
Localisez le fichier worker 🗂️ :
Chemin : node_modules/pdfjs-dist/build/pdf.worker.min.js.

Copiez ce fichier dans votre projet (par ex. dans public/).

Modifiez le chemin dans le code 🖊️ :

javascript
Copier le code
import * as pdfjsLib from 'pdfjs-dist';
pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';
Redémarrez l'application 🔄 :

bash
Copier le code
npm run serve
🛠️ Fonctionnalités
📂 Téléverser un fichier PDF.
✅ Sélectionner des tests personnalisés.
🔍 Analyser le contenu textuel du PDF.
📊 Afficher des résultats détaillés.
🎯 Utilité
✔️ Vérifiez la conformité des documents PDF.
⚡ Automatisez des vérifications rapides et efficaces.
📑 Simplifiez la gestion des documents.
