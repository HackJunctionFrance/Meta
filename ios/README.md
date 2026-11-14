# FirstFive sur CameraAccess

## Ce qui est livré

`Sources/FirstFiveClient.swift` et `FirstFivePanel.swift` + un générateur reproductible `prepare.py`.

Le générateur prend le sample officiel à `bbae597cd1c748cd29b9375a1624a8d75b1c9e14`, DAT **1.0.1** tel que fixé par son projet Xcode, et ajoute LiveKit Swift à `1693a9e2edfca5a94fbb89d5dbfe3390e026b30b`. Il conserve les crédits/licences Meta, la registration via Meta AI, le sélecteur d'appareil, le décodage HEVC et le Mock Device Kit. Il refuse d'écraser un projet existant.

Le panneau ajoute adresse serveur mémorisée, clé d'accès en mémoire, état serveur, Emergency, Yes/No, Reset, écoute et retry LiveKit. Le JPEG vient de l'image décodée du sample, limité à 3/s, compressé hors du thread UI. Audio HFP préparé avant Preview ; guide parlé via AVSpeechSynthesizer ; reconnaissance Apple anglaise avec renouvellement à 50 secondes et suspension pendant la synthèse ; métronome 110/min ; rappel 20 s ; arrêt du guide et du micro de reconnaissance lors du décroché, puis publication du micro dans LiveKit. La batterie n'est pas inventée : non disponible tant que le sample ne la fournit pas.

## Sur le Mac, avant les lunettes

1. Installer Xcode **26.4+**, ses composants iOS, signer avec votre équipe Apple. Cible iOS **17.2+**. Ne pas déduire la compatibilité du numéro de version local : vérifier dans Xcode.
2. Depuis la racine : `python3 ios/prepare.py`, puis `open ios/CameraAccess/CameraAccess.xcodeproj`.
3. Choisir un Bundle ID propre sans tiret, vérifier les réglages de signature. Le mode Developer Meta ne demande pas de MetaAppID de production (voir README officiel inclus).
4. Lancer en Debug. Utiliser le bouton de debug du sample pour créer/allumer des lunettes simulées et choisir une vidéo consentie dans le Mock Device Kit. Le sample conserve son flux d'enregistrement/appairage.
5. Ouvrir le panneau FirstFive, saisir l'adresse serveur (pas localhost sur un iPhone), connecter. Activer Voice pour autoriser micro et Speech. Start Session puis Preview dans CameraAccess. L'audio est préparé avant Preview.
6. Emergency, No, No ; vérifier vidéo/carte dans la console. Answer coupe le guide et rejoint LiveKit ; la vidéo doit continuer. End produit le rapport et ferme l'audio.
7. Garder l'app au premier plan. Le sample arrête sa session vidéo lorsqu'il passe en arrière-plan ; au retour, relancer session/Preview.

Pour un simulateur iOS sur le Mac, le serveur local est accessible depuis le simulateur. Pour l'iPhone, privilégier un nom local ou HTTPS approuvé ; adapter ATS explicitement si votre configuration le nécessite, sans désactiver TLS globalement. Les entrées d'autorisation Speech/Microphone/réseau local sont générées.

## Vérification sur les vraies lunettes

Dans cet ordre : sample non modifié → vidéo de notre app → TTS dans les lunettes → reconnaissance de 10 yes/no en bruit → **caméra + LiveKit simultanés** → deux pistes dans le rapport → trois répétitions → batterie/chauffe.

L'intégration Swift est **non compilée dans cet environnement Linux**. Ne pas la présenter comme validée sur iPhone. En particulier : la session audio peut être reconfigurée par LiveKit ; confirmer le routage HFP à la connexion. Le son système du métronome doit être vérifié dans les lunettes. La coexistence caméra/voix, les permissions, le mode développeur et les callbacks Meta se valident sur appareil.

Ne pas utiliser la fonction Record du sample pendant l'appel FirstFive : le régulateur enregistre déjà les deux pistes et une seconde capture du micro peut entrer en conflit.

Le guidage est piloté par le serveur (mêmes règles pour navigateur et iOS). Pas de mode premiers secours autonome en cas de coupure réseau. Une reconnexion récupère l'étape courante et redemande la consigne ; les envois échoués ne sont pas rejoués aveuglément.

## Modifier les sources

Le projet généré `ios/CameraAccess/` est ignoré par Git. Modifier les sources versionnées dans `ios/Sources/` et les points d'injection dans `prepare.py`. Préserver vos réglages Xcode/signature avant toute régénération. `--destination /chemin/neuf` permet de générer une copie de comparaison sans toucher au projet courant.
