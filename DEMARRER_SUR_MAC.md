# FirstFive — à faire pendant la mise à jour de l'iPhone

1. Extraire FirstFive.zip. Le dossier obtenu s'appelle FirstFive.
2. Ouvrir `ios/CameraAccess/CameraAccess.xcodeproj` avec Xcode. Le projet est déjà généré dans cette archive : inutile de lancer prepare.py.
3. Laisser Xcode télécharger les dépendances Meta et LiveKit. Garder le projet ouvert.
4. Dans Xcode : sélectionner le projet CameraAccess (icône bleue) → target CameraAccess → Signing & Capabilities. Activer Automatically manage signing et choisir votre équipe Apple. Donner un Bundle Identifier unique, par exemple `com.flo.firstfive` (sans tiret).
5. Pour lancer le serveur, ouvrir Terminal. Taper `cd ` (avec l'espace), glisser le dossier FirstFive dans Terminal et appuyer sur Entrée. Exécuter ensuite `bash scripts/start_mac.command`.
6. Le script nécessite Python 3.11+. S'il n'est pas installé, suivre son message ; les téléchargements Xcode peuvent continuer pendant ce temps.
7. Laisser Terminal ouvert. Dans Chrome, saisir `http://localhost:8000/test-caller`, puis ouvrir un autre onglet `http://localhost:8000/console?mode=operator`.
8. Page appelant : Emergency → No → No. Console : Answer → saisir un sous-titre → Send caption → End. Sans clés LiveKit Cloud, l'absence de voix est indiquée ; la vidéo synthétique et le rapport fonctionnent.

Quand l'iPhone a terminé : le reconnecter/déverrouiller, vérifier le mode développeur, le choisir comme destination Xcode et lancer CameraAccess (▶). La première compilation iOS n'a pas pu être réalisée dans le cloud Linux : garder le texte exact de toute erreur pour la corriger.

Les appels cloud IA, transcription et LiveKit sont facultatifs pour cette première répétition. Les instructions pour les activer sont dans README.md. Les valeurs se renseignent dans un fichier `.env` local, jamais dans Git ou dans le chat.

L'archive contient le code, les licences et le projet Xcode généré. Elle ne contient ni environnement Python Linux, ni clés, ni enregistrements de démonstration. Le ZIP n'a pas été compilé ou exécuté sur macOS.
