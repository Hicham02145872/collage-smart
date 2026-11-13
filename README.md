# Collage Smart

Application locale de collage photo sur planches **A4 paysage**, avec **10 photos par page**, cadrage automatique et retouche manuelle directement dans les aperçus.

## Fonctionnalités

- Analyse locale des visages (YuNet) et des personnes (NanoDet).
- Retrait des bandes noires ou colorées uniformes, avec option de désactivation.
- Photos et vidéos : seule la **première image décodée** de chaque vidéo est utilisée.
- Nombre de photos libre : création automatique de plusieurs A4, toutes visibles et modifiables ensemble.
- Déplacement, zoom et rotation à l’intérieur de rectangles fixes ; aucun étirement des photos.
- Affichage de la photo entière avec fond flouté, Annuler / Rétablir et avertissements de cadrage.
- Nom du client sur chaque planche et noms de fichiers incrémentés.
- Exports JPG, PNG et PDF, regroupés dans un ZIP avec leurs aperçus.
- Interface sombre à 80 % sur ordinateur et guide de première visite en six étapes avec photos de démonstration générées par IA.

## Installation rapide sous Windows

**Prérequis :** Windows, Python **3.12** avec le lanceur `py`, et une connexion Internet pour installer les dépendances. Git est nécessaire uniquement pour cloner le dépôt.

```powershell
git clone https://github.com/Hicham02145872/collage-smart.git
cd collage-smart
.\Lancer.cmd
```

Vous pouvez aussi télécharger le dépôt via **Code → Download ZIP**, l’extraire et double-cliquer sur **Lancer.cmd**.

Le lanceur crée `.venv`, installe les dépendances puis ouvre l’application dans le navigateur. L’adresse habituelle est **http://127.0.0.1:8501**. Gardez la fenêtre du lanceur ouverte pendant l’utilisation. Pour arrêter le serveur, appuyez sur **Ctrl+C** dans cette fenêtre.

`Installer.cmd` installe les dépendances sans démarrer l’interface.

## Installation et lancement manuels

Depuis le dossier du projet :

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false --theme.base dark
```

Aucune activation PowerShell de l’environnement n’est nécessaire avec ces commandes. Les modèles ONNX et le template sont inclus ; le PSD original n’est pas nécessaire.

## Utilisation

1. Dans le panneau gauche, entrez le **nom du client** et cliquez sur **Appliquer le nom**.
2. Importez des photos / vidéos, ou indiquez un dossier local. Les fichiers sont classés par nom : utilisez `01.jpg`, `02.jpg`, etc. pour fixer l’ordre.
3. Attendez l’analyse. Chaque groupe de dix images produit une A4 ; les emplacements inutilisés de la dernière page restent blancs.
4. Vérifiez toutes les planches et ajustez les photos si nécessaire.
5. Ouvrez **Exporter**, choisissez les formats et cliquez sur **Préparer toutes les planches**, puis **Télécharger tous les exports (ZIP)**.

Pour 30 photos avec le client `Amina`, les planches et fichiers portent les noms `Amina`, `Amina 1`, `Amina 2`. Pour imprimer les PDF, choisissez **100 % / taille réelle**.

### Gestes de retouche

| Action | Geste |
| --- | --- |
| Sélectionner une photo | Clic sur la photo |
| Déplacer son contenu | Cliquer-glisser dans la photo |
| Agrandir / réduire | Molette au-dessus de la photo sélectionnée, ou tirer un coin bleu |
| Tourner | Glisser la poignée ↻ ; maintenir Maj pour des pas de 15° |
| Affiner la position | Flèches du clavier, lorsque le canvas a le focus |
| Voir toute la photo | Bouton **Afficher la photo entière** |
| Revenir au cadrage automatique | Double-clic sur la photo |
| Annuler / rétablir | Boutons dédiés, ou Ctrl+Z / Ctrl+Maj+Z dans le canvas |

L’historique concerne les gestes du canvas, jusqu’à 50 états par photo. Les réglages numériques n’en font pas partie. Les retouches sont conservées dans la session : **exportez avant de recharger ou de fermer la page**.

Le guide s’ouvre au premier accès dans chaque navigateur. **Passer le guide** ou **Commencer** mémorise sa fermeture localement. **Revoir le guide photo** permet de le rouvrir.

## Génération sans interface

Après installation des dépendances :

```powershell
.\.venv\Scripts\python.exe batch.py --folder "C:\Photos\Commande" --client "Amina" --output "exports\Amina"
```

Cette commande analyse les médias puis génère les JPG, PDF, aperçus et ZIP dans le dossier indiqué. Elle utilise le cadrage automatique, sans les retouches de la session du navigateur.

## Formats et limites

- Photos : JPG/JPEG, PNG, WEBP, TIFF.
- Vidéos : MP4, MOV, AVI, MKV, WEBM, M4V, selon les codecs disponibles dans OpenCV.
- Sortie : RVB 8 bits ; canevas intégré de 3564 × 2520 pixels, environ 304,8 dpi.
- Le cadrage automatique peut manquer un visage ou une personne. Toujours vérifier les aperçus avant impression.
- Le retrait des bandes n’efface pas les boutons, horloges ou sous-titres des captures d’écran.
- Le template est spécifique aux dix emplacements fournis. Un autre PSD doit conserver la structure attendue. Aucun export PSD éditable n’est produit.
- Les polices disponibles sur Windows peuvent modifier légèrement le rendu du nom client sur une autre machine.

## Confidentialité

L’analyse et la composition se font sur votre ordinateur. Les photos ne sont pas envoyées à un service d’IA. Internet sert à installer les dépendances et, si nécessaire, à récupérer les modèles manquants. Le serveur écoute sur `127.0.0.1`.

Le dépôt contient le code, les modèles, leurs licences, le template et les images de démonstration. Placez vos médias privés dans `photos/` ou `pic/`, et les exports dans `exports/` : ces dossiers sont ignorés par Git.

## Structure du projet

```text
app.py                 Interface Streamlit et gestion des commandes
ui.py                  Thème, guide et messages utilisateur
core.py                Lecture des médias, détection et composition
exporting.py           Noms client, formats et archive ZIP
batch.py               Génération en ligne de commande
canvas_editor/         Éditeur interactif HTML / JavaScript
onboarding/            Guide photo et prompts ImageGen
assets/                Logo et ressources graphiques
models/                Modèles ONNX et licences associées
template/              Rendu du modèle et coordonnées des cadres
.streamlit/config.toml Thème Streamlit
Lancer.cmd             Installation puis lancement sous Windows
Installer.cmd          Installation uniquement
test_cadrage.py        Tests de régression du cadrage
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest test_cadrage.py
```

## Dépannage

- **`py` introuvable** : installez Python 3.12 avec le lanceur Python, puis rouvrez le terminal.
- **Port 8501 occupé** : fermez l’ancienne instance ou ajoutez `--server.port 8502` à la commande Streamlit et ouvrez le port correspondant.
- **Dossier vide** : vérifiez le chemin et les extensions des fichiers. L’import de fichiers reste disponible.
- **Vidéo illisible** : le codec peut ne pas être disponible ; utilisez une vidéo compatible ou fournissez une image extraite.
- **Sujet potentiellement coupé** : sélectionnez la photo et utilisez **Afficher la photo entière**, ou ajustez son cadrage.

## Sources

- [OpenCV Zoo — YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)
- [OpenCV Zoo — NanoDet](https://github.com/opencv/opencv_zoo/tree/main/models/object_detection_nanodet)
- [Streamlit](https://docs.streamlit.io/) et [psd-tools](https://psd-tools.readthedocs.io/)

Les licences des modèles tiers se trouvent dans `models/`. Les images du guide et le logo ont été générés avec ImageGen ; leurs prompts sont inclus. Voir aussi [le guide détaillé](LIRE-MOI.md).
