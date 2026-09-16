# Modèles d'images locaux

Créez un dossier `reference_models` à côté de ce fichier puis placez-y vos propres images PNG ou JPEG. Le dossier est volontairement ignoré par Git afin que les logos, signatures, filigranes et autres éléments propres à une organisation ne soient jamais publiés.

Pour contrôler leur position, créez également un fichier local `reference_bboxes.json` :

```json
{
  "exemple.png": {"left": 10, "top": 10, "width": 200, "height": 80}
}
```
