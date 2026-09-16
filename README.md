# PDF Verifier

Application générique de contrôle de fichiers PDF. Elle permet de sélectionner des règles, d'extraire le texte d'un document et de vérifier la présence de contenus attendus. Le serveur FastAPI fournit aussi des fonctions d'OCR et de comparaison d'images de référence.

Le dépôt ne contient aucun document métier, logo, signature, fichier téléversé ou résultat d'analyse. Ajoutez vos propres jeux de tests et modèles locaux sans les versionner.

## Prérequis

- Node.js et npm
- Python 3.10 ou supérieur
- Tesseract et Poppler pour les routes OCR

## Cloner le dépôt privé

```bash
git clone https://github.com/CVanzetta/pdf-verifier.git
```

Ce dépôt est la copie personnelle assainie du projet. Aucun commit ne doit être poussé vers le dépôt GitLab de l'entreprise.

## Lancer le client

```bash
cd pdf-verifier/client
npm install
npm run serve
```

L'interface est alors disponible sur `http://localhost:8080`.

## Lancer l'API

```bash
cd pdf-verifier/server
python -m venv .venv
# Windows : .venv\Scripts\activate
# macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

La documentation interactive est disponible sur `http://127.0.0.1:8000/docs`.

## Configurer les contrôles

Les règles de démonstration se trouvent dans `pdf-verifier/client/src/assets/Tests.json`. Leur structure prend en charge les contrôles de texte, de montant, de date et de valeurs réparties sur plusieurs colonnes.

Pour la détection visuelle, placez vos propres images dans `pdf-verifier/server/reference_models/`. Ce dossier est ignoré par Git afin d'éviter de publier des logos, signatures ou autres éléments confidentiels.

## Vérifications

```bash
cd pdf-verifier/client
npm run lint
npm run build
```
