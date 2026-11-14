# Mise à jour 02 — après le premier lancement sur iPhone

## Installer sur le Mac en gardant la signature Xcode

1. Arrêter le serveur dans son terminal (Ctrl+C) et arrêter l'app dans Xcode (■).
2. Extraire `FirstFive-update-02.zip`.
3. Double-cliquer sur `Installer-sur-Mac.command`. Choisir le dossier **FirstFive** déjà téléchargé (celui qui contient `server`, `web` et `ios`).
4. Le programme sauvegarde les fichiers qu'il remplace dans `backup-before-update-…`. Il conserve `.env`, les données, l'environnement Python et tout le projet `.xcodeproj`, donc le compte Apple et le Bundle Identifier configurés dans Xcode.
5. Si macOS refuse d'ouvrir le fichier téléchargé, ouvrir Terminal, taper `bash `, glisser `Installer-sur-Mac.command` dans Terminal, puis Entrée. Ne pas supprimer les protections macOS globalement.
6. Relancer le serveur avec `bash scripts/start_mac.command` depuis FirstFive et recharger les pages web. Le terminal affiche l'adresse `.local` du Mac à saisir dans le panneau FirstFive de l'iPhone. Les deux appareils doivent être sur le même réseau.
7. Dans le projet Xcode déjà ouvert, cliquer sur ▶. Le correctif iOS est inclus ; pas besoin de recréer le projet ou la signature.

Si le sélecteur de dossier n'est pas disponible : `python3 apply_update.py /chemin/vers/FirstFive`, depuis le dossier de la mise à jour. L'installateur requiert Python 3.9+ ; le serveur requiert toujours Python 3.11+.

## Changements

- Une reconnexion LiveKit crée un nouveau segment d'enregistrement pour le même interlocuteur ; le segment précédent est conservé. Limites : 32 segments et 24 MB au total par interlocuteur.
- L'envoi répété du même segment remplace son contenu sans dupliquer les données. Après un échec, End réessaie uniquement les segments non envoyés.
- Le rapport fusionne les segments selon leurs offsets. Les sous-titres restent présents dans les intervalles où l'enregistrement manque ou ne peut pas être transcrit.
- La transcription utilise au plus deux requêtes simultanées et un budget global de 50 secondes, puis produit un rapport avec les données disponibles. La synthèse IA conserve son timeout de 20 secondes.
- Une reconnexion du WebSocket ne coupe plus l'appel LiveKit du navigateur. Si la page appelant est rechargée, elle rejoint l'appel en cours. L'opérateur conserve les morceaux audio déjà enregistrés.
- Correctif iPhone inclus : invalidation des anciennes reconnaissances/connexions après Reset, protection contre les formats micro non prêts, URL serveur avec ou sans slash final.

## Validation et limites

Le parcours de reconnexion a été exercé dans Chromium avec un vrai serveur LiveKit local et des micros synthétiques : rechargement de l'appelant pendant l'appel, deux segments caller, un segment dispatcher, téléversement et rapport.

Le premier projet iOS a été compilé et lancé par l'utilisateur sur son iPhone (capture Xcode « Running CameraAccess »). Le mode Mock Device Kit a ensuite été configuré par l'utilisateur. Le nouveau correctif Swift reste à recompiler et tester sur ce Mac ; Linux ne permet pas de le valider.

Le rechargement de la page **opérateur** perd toujours ses enregistrements qui ne sont pas encore envoyés : garder cet onglet ouvert pendant l'appel. Les données ne sont pas conservées dans le stockage du navigateur. Une coupure audio produit un intervalle manquant : nous ne fabriquons pas de paroles pour le combler.

À valider avec les lunettes : appairage, permissions, vidéo réelle, voix et reconnaissance via Bluetooth, caméra + LiveKit simultanés. À configurer pour les vrais services cloud : LiveKit et fournisseur IA/transcription, avec les valeurs dans `.env`. Le prototype ne contacte pas le vrai 112 et n'envoie rien à un hôpital.
