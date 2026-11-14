# FirstFive — correctif 04 : Enable voice / Swift 6

Cause confirmée sur l’iPhone : EXC_BREAKPOINT dans _dispatch_assert_queue_fail, closure #1 in FirstFiveClient.enableListening, appelée par TCC sur com.apple.root.default-qos après autorisation. Le callback héritait de MainActor, mais Apple l’exécute sur une autre queue.

Les callbacks d’autorisation sont maintenant construits dans des fonctions explicitement nonisolated et renvoient un Bool via continuation. L’état UI est modifié sur MainActor. Les callbacks du microphone audio et de Speech sont également construits hors MainActor ; seules des valeurs texte/bool rejoignent l’UI. Le panneau affiche l’état d’écoute et la dernière phrase reconnue. Les garde-fous contre les anciens callbacks annulés de la mise à jour 02 sont inclus, ainsi que le bouton Update app on glasses de la mise à jour 03.

## Installation
1. Dans Xcode, Stop (carré). Ne poursuis pas l’exécution de l’app arrêtée sur l’assertion.
2. Décompresse cette archive et lance Installer-sur-Mac.command. Choisis ton dossier FirstFive existant, pas un dossier FirstFive-update.
3. Le script ouvre le projet mis à jour. Sélectionne iPhone de Flo et clique sur ▶.
4. Laisse le serveur ouvert. Dans FirstFive, Connect puis Reset, puis Enable voice avant Start session / Preview.
5. Vérifie Listening dans le panneau, puis Start session / Preview, EMERGENCY. Attends la fin de la question et dis Yes ou No, sans cliquer Answer call sur le Mac. Vérifie Heard puis le changement de question.
6. Si cela bloque encore, capture la nouvelle erreur et le résultat de bt dans LLDB.

Si macOS bloque le script, lance-le dans Terminal avec bash suivi du chemin du fichier (glisser-déposer après avoir tapé `bash `).

La signature Xcode, .env, le serveur et les données sont conservés ; les fichiers remplacés sont sauvegardés. Installation possible directement sur la première archive ou après les mises à jour 02/03. Aucun réglage LiveKit n’est ajouté : le guide local et la conversation opérateur sont distincts.

## Validation
Vérification de la génération du projet et de l’installation sur une copie de l’archive initiale (sauvegarde, signature et .env conservés). Pas de Xcode dans l’environnement Linux : compilation Swift et résolution du crash à confirmer sur l’iPhone. La simultanéité caméra/Bluetooth/reconnaissance vocale reste un test matériel.
