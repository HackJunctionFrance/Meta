# FirstFive — update 05 : diagnostic et routage audio de l'appel opérateur

Symptôme signalé : appel LiveKit actif (`/health` → `"livekit":true`), mais la voix de l'opérateur n'est pas entendue dans les lunettes et le micro capte mal.

Changements iOS (`ios/Sources/FirstFiveClient.swift`, `FirstFivePanel.swift`) :
- Après `setMicrophone(enabled: true)`, LiveKit reconfigure la session audio ; l'app réapplique alors l'entrée Bluetooth HFP des lunettes et annule toute sortie forcée.
- Ligne d'état actualisée chaque seconde : `Call`, `Operator` (absent / pas d'audio / silencieux / parle), `My mic` (off / on / parle).
- Ligne `Mic / Sound` : ports réellement utilisés par iOS (notification de changement de route).
- Boutons `Audio → glasses` et `Audio → iPhone speaker` (secours).

Installation : archive `FirstFive-update-05.zip` (hors Git), `Installer-sur-Mac.command`, sauvegarde automatique, signature/.env/serveur conservés.

Validation : non compilé ici (pas de Xcode sous Linux) ; noms d'API vérifiés dans le SDK LiveKit Swift 2.19.0 épinglé. Installation testée sur une copie factice.
