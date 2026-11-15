# Correctif iPhone : connexions et reconnaissance vocale

La relecture a identifié trois risques dans la première archive : les callbacks d'une reconnaissance annulée pouvaient arrêter celle qui venait de la remplacer ; une connexion réseau retardée pouvait continuer après Reset ; une entrée micro sans format audio valide pouvait provoquer une erreur lors de la pose du tap.

Le correctif invalide les anciennes opérations, vérifie la session du jeton LiveKit avant de publier le micro, empêche l'envoi d'une image de l'intervention précédente et refuse de démarrer la reconnaissance tant que l'entrée audio n'est pas prête. Il construit aussi l'URL du jeton correctement si l'adresse serveur se termine par `/`.

Pour appliquer le correctif à l'archive déjà ouverte sur Mac : remplacer uniquement `FirstFive/ios/CameraAccess/CameraAccess/FirstFiveClient.swift` par le fichier fourni dans FirstFive-iOS-update.zip. Conserver le projet Xcode et ses réglages de signature. Copier également le fichier dans `FirstFive/ios/Sources/FirstFiveClient.swift` pour conserver la correction lors d'une future génération.

Validation : relecture des modifications et génération du projet avec le fichier corrigé. Compilation iOS et exécution toujours à effectuer dans Xcode ; aucun test iPhone ou Bluetooth n'est revendiqué depuis Linux.

À vérifier après compilation : lancer/recommencer une session, répondre No/No, décrocher et vérifier l'arrêt de la reconnaissance, Reset pendant une tentative de connexion, puis démarrer une nouvelle session. Vérifier que l'ancien appel ne se réactive pas et que le microphone n'est publié que pour l'intervention actuelle.
