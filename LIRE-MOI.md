# Collage Smart — ton template A4, 10 photos

Extraire le ZIP d'installation, puis double-cliquer sur **Lancer.cmd**. Python 3.12 doit être installé. Le premier lancement crée un environnement Python et installe les bibliothèques ; les modèles sont inclus. **Installer.cmd** permet aussi d'installer les dépendances séparément. L'interface s'ouvre dans le navigateur, sur cet ordinateur uniquement. Une connexion Internet est nécessaire à la première installation.

1. Ton template est déjà intégré : son rendu et ses dix emplacements ont été extraits du PSD fourni. Le PSD de 313 Mo n'est pas nécessaire au lancement. Le champ facultatif permet de relire le PSD original si tu le modifies, à condition de conserver la même organisation des calques et des cadres noirs.
2. Choisir des fichiers JPG, PNG, WEBP ou TIFF et/ou des vidéos MP4, MOV, AVI, MKV, WEBM ou M4V, ou saisir un dossier local. Pour chaque vidéo, **seule la première image décodée** est utilisée, sans recherche d'une meilleure image ni lecture de la suite. Si cette première image est noire, elle reste l'image utilisée. Les images sont réparties par groupes de 10, avec toutes les planches affichées dès le départ. Les cadres restants de la dernière planche sont blancs. L'ordre initial est celui des noms, par exemple `01.jpg` à `10.jpg`. Un codec non disponible provoque un message d'erreur explicite.
3. L'application retire les bandes noires uniformes et les paires de bandes colorées uniformes typiques des captures. Elle combine ensuite un détecteur de silhouettes NanoDet et un détecteur de visages YuNet. Le zoom automatique réduit les zones vides tout en préservant les sujets détectés.
4. Saisir le **nom du client dans le panneau gauche**, puis cliquer sur **Appliquer le nom**. Il remplace le texte du modèle sur chaque planche et détermine les noms des exports. Le texte dans l'image d'aperçu n'est pas un champ éditable. Pour 30 images et le nom `Amina`, les trois planches portent `Amina`, `Amina 1`, `Amina 2`.
5. Modifier directement l'aperçu A4 compact : cliquer sur une photo pour la sélectionner (contour bleu), puis la faire glisser à la souris. La molette ou le déplacement d'un coin changent son zoom. Faire glisser la poignée ↻ située en haut de la photo pour la tourner ; Maj pendant la rotation permet des pas de 15°. Les flèches du clavier affinent la position. Un double-clic revient au cadrage automatique et annule la rotation. Il n'y a pas de boutons de zoom ou rotation séparés. La planche et les rectangles restent fixes et masquent ce qui dépasse. Les réglages sont enregistrés après chaque geste, conservés pour chaque planche et appliqués aux exports. Toutes les planches sont affichées dans la même page, deux par ligne sur grand écran et empilées sur petit écran. Chaque A4 possède son propre éditeur ; il suffit de faire défiler la galerie pour modifier une autre planche. Les anciens curseurs restent disponibles sous « Réglages numériques (facultatif) ». Un fond flouté remplit les bords si la photo ne couvre pas le rectangle.
6. Choisir JPG, PDF et/ou PNG, puis cliquer sur **Préparer toutes les planches**. Télécharger le ZIP d'exports : il contient les fichiers `Amina.jpg`, `Amina.pdf`, `Amina 1.jpg`, `Amina 1.pdf`, etc., ainsi qu'un dossier `Apercus` portant les mêmes noms. Les aperçus de toutes les pages sont aussi affichés dans l'application et téléchargeables séparément. Imprimer les PDF à **100 % / taille réelle**. Le ZIP d'exports est distinct du ZIP d'installation.

Le bouton **Afficher la photo entière** agit uniquement sur la photo sélectionnée. Il conserve sa rotation, recentre l'image et ajuste son zoom pour tout montrer dans le rectangle fixe. Les zones restantes sont remplies par le fond flouté ; ce réglage est aussi appliqué aux exports.

Le logiciel lit le rendu enregistré par Photoshop dans le PSD, conserve les bordures et les repères, remplace les rectangles photo et inscrit le nom du client dans la zone du texte d'origine. Il est adapté aux dix groupes du template fourni, contenant chacun `Rectangle 2` et `Rectangle 2 copy`, avec la zone de nom à son emplacement d'origine. Les chemins des calques permettent de localiser les emplacements, puis les limites sont alignées sur les rectangles noirs du rendu. Il ne modifie pas le PSD original et n'exporte pas un PSD éditable.

Le nom utilise la police Windows Lucida Handwriting du modèle quand elle est disponible, sinon Segoe Print ou une police de secours. La taille diminue automatiquement pour les noms longs. Les caractères interdits dans les noms de fichiers Windows sont remplacés par `_` ; le texte affiché garde le nom saisi. Un nom vide devient `Nom client`.

Les exports sont en RVB et en 8 bits. Le rendu CMJN 16 bits est converti : une identité colorimétrique absolue avec une impression CMJN Photoshop ne peut pas être garantie. La mise en page et les éléments du rendu intégré sont conservés.

Les nouveaux exports utilisent un canevas A4 de 3564 × 2520 pixels, soit 304,8 dpi. L'analyse de tout le dossier conserve uniquement les coordonnées de cadrage et de détection. Les photos sont ensuite décodées une à une pour composer chaque page ; le cache ne conserve plus les photographies décodées. Les statistiques des bandes sont calculées par blocs de 32 lignes pour éviter les grands tableaux temporaires en mémoire.

## Comment fonctionne le cadrage

**Visages :** réseau neuronal préentraîné YuNet, exécuté par OpenCV DNN. Une marge est ajoutée au-dessus et autour des visages ; le cadrage tente de garder tous les visages détectés. Aucun entraînement ou envoi de photos n'est nécessaire.

**Personnes :** réseau neuronal NanoDet préentraîné sur COCO, exécuté localement avec OpenCV DNN. Les personnes détectées avec une confiance suffisante guident le cadrage de la silhouette entière. Les visages de taille comparable sont protégés même si le détecteur manque leur corps. Les petits visages lointains peuvent être écartés. Pour les selfies horizontaux en gros plan, le cadrage suit les visages plutôt que les bras et la silhouette entière. Ces règles restent heuristiques et peuvent échouer sur une autre image. HOG/SVM est conservé en secours si aucun corps ni visage fiable n'est trouvé. Ce n'est pas une segmentation universelle de tous les objets.

**Bandes :** traitement d'image, pas un modèle ML. Il cherche des lignes ou colonnes presque uniformes, très sombres et reliées aux bords. Il reconnaît aussi deux bandes colorées opposées, y compris un dégradé vertical, si la transition avec le contenu est suffisamment marquée. Les bandes trop épaisses et les scènes presque entièrement noires sont conservées par prudence. Les interfaces de téléphone, horloges, boutons, sous-titres et cadres noirs internes ne sont pas effacés. Désactiver l'option si un fond uni est rogné à tort.

Chaque photo occupe exactement son rectangle du template, sans étirement. Si un recadrage plein cadre couperait un sujet protégé, les zones restantes sont remplies avec un fond flouté provenant de la même photo. Les emplacements sans photo sur la dernière page restent blancs. Le zoom et le déplacement permettent de reprendre la main ; un avertissement signale alors un sujet détecté qui dépasse le cadre. Une détection manquée ne peut pas être signalée automatiquement : toujours vérifier l'aperçu.

## Validation avec le dossier fourni

Testé sur les 19 JPG du dossier `pic` : deux captures avec bandes colorées reconnues, silhouettes et visages utilisés pour 18 images, cadrage centré pour la photo de la main tenant un verre. La première image du MP4 est ajoutée comme vingtième image ; sa correspondance exacte avec la première lecture du décodeur a été vérifiée. Les deux planches de 10 images ont été inspectées visuellement et exportées en PDF A4. La photo devant l'affiche est cadrée sur la personne principale. Les réglages sont conservés indépendamment pour chaque cadre et chaque page. Cela ne garantit pas une détection parfaite sur de nouvelles images.

## Sources et composants

- YuNet et modèle ONNX : https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet (licence et fichiers associés dans ce dépôt).
- NanoDet, modèle ONNX et adaptateur Python : https://github.com/opencv/opencv_zoo/tree/main/models/object_detection_nanodet (Apache-2.0, licence incluse dans `models/LICENSE-NanoDet.txt`).
- Détecteur HOG/SVM : https://docs.opencv.org/4.x/d5/d33/structcv_1_1HOGDescriptor.html
- Lecture PSD : https://psd-tools.readthedocs.io/
- Interface : https://docs.streamlit.io/

Les images ne sont pas envoyées à un service externe. Internet est utilisé pour l'installation et le téléchargement initial du modèle. Pour un usage sans réseau, préparer ces éléments une première fois.


## Atelier de retouche
Interface sombre et compacte : commande et import dans le panneau gauche, toutes les planches au centre, accès direct à l’export en haut. Le guide visuel reste repliable.

Annuler / Rétablir agit sur la photo sélectionnée, pour les gestes effectués dans le canvas (50 états maximum). Ctrl+Z et Ctrl+Maj+Z fonctionnent lorsque le canvas a le focus. L’historique est conservé pendant la session de l’éditeur ; rechargez la page uniquement après avoir exporté vos retouches. Les réglages numériques ne font pas partie de cet historique.

Conception guidée par UI/UX Pro Max : https://github.com/nextlevelbuilder/ui-ux-pro-max-skill ; adaptation à un atelier photo, contraste sombre, focus visible, contrôles libellés et aide progressive.


## Guide de première visite
Le guide photo apparaît automatiquement au premier accès dans chaque navigateur. Six étapes expliquent l’import, le recadrage, le zoom, la rotation, la photo entière et l’export. Suivant / Précédent permettent de naviguer ; Passer le guide et Commencer le ferment. Revoir le guide photo permet de le relancer. La fermeture est mémorisée localement dans le navigateur, sans compte et sans transfert de photos. Si le stockage du navigateur est bloqué ou effacé, le guide peut réapparaître.

Trois photographies de démonstration ont été créées avec ImageGen (outil intégré) et sont incluses dans onboarding/. Les prompts exacts sont dans onboarding/prompts.json. L’interface est affichée à 80 % sur ordinateur (largeur ≥900 px) ; les petits écrans gardent une taille lisible.
