# PDF Test Validator

## Description
PDF Test Validator est une application permettant de vérifier des fichiers PDF en fonction de tests prédéfinis. Elle est développée avec PrimeVue et propose une interface intuitive pour :

- 📂 **Téléverser un PDF**
- ✅ **Exécuter des tests personnalisés**
- 📊 **Afficher les résultats détaillés**

---

## 🚀 Installation

### 1. Cloner le projet
```bash
# Clonez le dépôt Git
git clone https://github.com/CVanzetta/pdf-verifier.git
```

### 2. Installer les dépendances
```bash
# Installez les dépendances du projet
npm install
```

### 3. Lancer le serveur
```bash
# Lancez le serveur de développement
npm run serve
```

### 4. Accéder à l'application
Ouvrez votre navigateur à l'adresse suivante :
```
http://localhost:8080
```

---

## ➕ Ajouter un test

Les tests sont définis dans le fichier JSON situé à : `src/assets/Tests.json`.

### Exemple d’ajout
Voici un exemple de structure pour ajouter un nouveau test :
```json
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
```

### 🔖 Étapes pour ajouter un test :
1. **Ouvrez le fichier `Tests.json`.**
2. **Ajoutez une nouvelle catégorie** ou un nouveau test dans une catégorie existante.
3. **Définissez les conditions du test** :
   - **type** : Type de vérification (texte, montant, date, etc.).
   - **value** : Valeur à chercher dans le PDF.
4. **Sauvegardez vos modifications.**

---

## 🔧 Résolution de l’erreur : "API version does not match the Worker version"

### ⚠ Problème
Si vous rencontrez l’erreur suivante :
```
UnknownErrorException: The API version "X" does not match the Worker version "Y".
```

### 🔧 Solution
1. **Vérifiez la version installée** :
   ```bash
   npm ls pdfjs-dist
   ```

2. **Localisez le fichier worker** :
   - Chemin : `node_modules/pdfjs-dist/build/pdf.worker.min.js`

3. **Copiez ce fichier dans votre projet** :
   - Placez-le dans le dossier `public/`.

4. **Modifiez le chemin dans le code** :
   ```javascript
   import * as pdfjsLib from 'pdfjs-dist';
   pdfjsLib.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.js';
   ```

5. **Redémarrez l’application** :
   ```bash
   npm run serve
   ```

---

## 🔨 Fonctionnalités
- 📂 **Téléverser un fichier PDF.**
- ✅ **Sélectionner des tests personnalisés.**
- 🔍 **Analyser le contenu textuel du PDF.**
- 📊 **Afficher des résultats détaillés.**

---

## 🔍 Utilité
- ✔️ **Vérifiez la conformité des documents PDF.**
- ⚡️ **Automatisez des vérifications rapides et efficaces.**
- 📝 **Simplifiez la gestion des documents.**

