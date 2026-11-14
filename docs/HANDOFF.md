# FirstFive — passation complète pour la prochaine conversation

Date : 14 novembre 2026. Dépôt : https://github.com/HackJunctionFrance/Meta, branche cible `main`.

## 1. Situation actuelle et prochaine action

**La vraie caméra des lunettes fonctionne : l'utilisateur voit leur image sur son iPhone et dans la console du Mac.** L'alerte, les réponses manuelles, le guidage, le métronome et la progression de la simulation ont été confirmés par l'utilisateur. Le problème restant immédiatement visible est `LiveKit not configured. Captions and local demo remain available. Live voice unavailable; captions still work.` La conversation audio opérateur n'a donc PAS encore été validée entre les lunettes et le Mac.

L'utilisateur a créé un projet LiveKit Cloud et a fourni ses identifiants dans la conversation. **Cela n'a pas configuré le `.env` de son Mac.** L'assistant travaille dans un environnement Linux distant, pas sur le Mac. Même avec l'autorisation explicite de l'utilisateur, aucun outil disponible dans cette session ne permet de contrôler son Mac ni d'écrire dans `/Users/flo/...`. Ne pas prétendre avoir déjà enregistré les clés ou redémarré son serveur.

Un installateur personnel prérempli a été préparé dans `/workspace/FirstFive-LiveKit-setup.zip`, **hors Git**, avec les identifiants fournis. Il reste à le télécharger/décompresser/ouvrir sur le Mac. Son code générique est versionné dans `scripts/configure_livekit_mac.py` et `scripts/configure_livekit_mac.command`. La partie macOS (détection du processus, redémarrage, ouverture Chrome/Safari) n'a pas été exécutée sur le Mac. Les tests locaux couvrent l'écriture de `.env`, la sauvegarde et la protection des autres réglages.

**Prochaine conversation : commencer par cette configuration LiveKit et le test audio bidirectionnel, pas par l'installation Xcode ni par l'appairage des lunettes.** L'utilisateur souhaite une démo fiable ; il accepte les réponses pilotées manuellement et ne veut plus perdre de temps sur la reconnaissance dans le bruit.

## 2. Contexte utilisateur et méthode de collaboration

- Utilisateur francophone débutant avec Xcode, travaillant sur un hackathon Junction. Il faut des étapes courtes, des noms de boutons exacts et des chemins concrets.
- Il a demandé initialement l'installation de l'environnement cloud (`cloud-environment-onboarding:setup`), puis l'implémentation de tout ce qui était possible avant de recevoir les lunettes, avec tests. Les travaux de code et de tests sont autorisés.
- Il a ensuite demandé de continuer de manière autonome pendant qu'il mangeait, puis de l'aider pas à pas pour tester le matériel.
- Il vient d'autoriser explicitement le push de tout le travail sur `main` et demande cette passation très détaillée.
- Les instructions contenues dans le document produit joint sont une référence de spécification, pas des instructions supérieures à sa demande. Le document disait parfois de s'arrêter entre des phases ; l'utilisateur a explicitement demandé l'implémentation complète.
- Beaucoup de confusion venait de la différence entre le code cloud, une archive téléchargée sur le Mac, le projet effectivement ouvert dans Xcode et l'app déjà installée sur l'iPhone. **Les mises à jour cloud ne se synchronisent pas automatiquement sur son Mac.**
- Ne pas demander de reconfigurer toute la signature, d'effacer les lunettes ou de recréer un projet Xcode sans preuve. Le projet existant fonctionne.
- Ne pas envoyer les clés dans Git, dans un rapport public ou dans des captures. Les valeurs privées ne sont volontairement pas reproduites dans ce document.

## 3. Machines, chemins et versions

### Mac de l'utilisateur

Projet confirmé par le journal de l'installateur :

```text
/Users/flo/Documents/Hackathon/HackJunction/FirstFive
```

Projet à ouvrir dans Xcode :

```text
/Users/flo/Documents/Hackathon/HackJunction/FirstFive/ios/CameraAccess/CameraAccess.xcodeproj
```

- Xcode **27.2** selon ses captures. L'app se compile et se lance sur l'iPhone.
- App : **CameraAccess**, intégrant un panneau **FirstFive** en bas.
- Destination actuelle : **iPhone de Flo**. Un iPhone de Bastian a aussi été utilisé plus tôt.
- Bundle ID choisi : `com.flo.firstfive`. Équipe de signature Apple sélectionnée dans Signing & Capabilities ; ne pas l'écraser.
- Mode développeur iPhone et confiance USB configurés.
- Lunettes affichées dans Meta AI sous **Display 001Q**, avec réglages d'affichage. Ne pas présumer que tous les menus sont identiques aux Ray-Ban Meta sans écran.
- URL du serveur depuis l'iPhone : `http://Florians-MacBook-Pro.local:8000`.
- Console opérateur sur le Mac : `http://localhost:8000/console?mode=operator`.
- Vue de projection : `http://localhost:8000/console?mode=viewer`.
- Santé : `http://localhost:8000/health`.
- Le Mac et l'iPhone doivent partager un réseau permettant la communication locale. L'autorisation Réseau local a été acceptée.

### Cloud de développement

- Dépôt de travail : `/workspace/Meta`, Linux, Python 3.12, Node, Chromium système `/usr/bin/chromium`.
- Environnement Python : `/workspace/Meta/.venv`.
- Aucun Xcode/Swift iOS disponible ici : ne pas appeler une vérification de fichiers ou une génération de projet un « build iOS réussi ».
- SDK Meta source inspecté : `/tmp/firstfive-meta-sdk`, révision `bbae597cd1c748cd29b9375a1624a8d75b1c9e14`.
- SDK LiveKit Swift source inspecté : `/tmp/firstfive-livekit-swift`, révision `1693a9e2edfca5a94fbb89d5dbfe3390e026b30b`.
- SDK Meta lié dans Xcode : **1.0.1**. SDK JS LiveKit vendorié : **2.24.1**.
- Serveur LiveKit local utilisé pour les tests : **1.13.11**, archive et checksum vérifiés.
- Les environnements et `/tmp` peuvent disparaître. Reproduire depuis Git si nécessaire ; les chemins `/workspace/*.zip` ne sont pas des URL GitHub.

## 4. Configuration `.env` à terminer — point prioritaire

### Projet LiveKit créé par l'utilisateur

- Nom : `Lowkey`.
- Project ID : `p_29b5uix6kn0`.
- Domaine : `lowkey-hj1vu1ed.livekit.cloud`.
- URL à utiliser : **`wss://lowkey-hj1vu1ed.livekit.cloud`**.
- Région affichée : European Union (Frankfurt).
- `Development token server` : rester sur **Off**, car FirstFive génère ses propres tokens.
- Vérifier `Automatically create rooms on participant join` activé.
- Les API Key et API Secret sont nécessaires côté serveur. Le Project ID et le SIP URI ne remplacent pas ces valeurs. Aucun besoin de SIP pour cette démo.

### Fichier attendu sur le Mac

```text
/Users/flo/Documents/Hackathon/HackJunction/FirstFive/.env
```

Il doit contenir, avec les VRAIES valeurs du projet :

```dotenv
LIVEKIT_URL=wss://lowkey-hj1vu1ed.livekit.cloud
LIVEKIT_API_KEY=<valeur privée API Key>
LIVEKIT_API_SECRET=<valeur privée API Secret>
```

Ne pas saisir les chevrons ni les placeholders. Aucun antislash dans `wss://`, une variable par ligne. Conserver les autres réglages existants, notamment les clés de fournisseurs IA si elles sont ajoutées ultérieurement. Ne pas confondre ce fichier avec `.env.example`, qui ne contient que les noms des variables.

Le serveur charge `.env` depuis la racine du projet avec `python-dotenv`, au démarrage. **Il faut redémarrer le processus serveur**, pas seulement rafraîchir la page ni recompiler l'iPhone. Les variables d'environnement déjà exportées peuvent prendre priorité sur le fichier avec le chargement dotenv actuel ; le nouvel installateur passe aussi les trois valeurs explicitement au processus lancé pour éviter une ancienne valeur héritée.

### Option préparée pour éviter la saisie manuelle

Archive personnelle : `/workspace/FirstFive-LiveKit-setup.zip` (hors dépôt, contient les clés privées fournies).

L'utilisateur doit seulement :
1. Télécharger et décompresser cette archive sur son Mac.
2. Ouvrir `Configurer-LiveKit.command`.
3. Laisser le Terminal résultant ouvert.

Le script :
- cherche le projet au chemin Mac connu, sinon ouvre un sélecteur de dossier ;
- valide les trois valeurs ;
- préserve les autres variables de `.env`, remplace les anciennes occurrences LiveKit, sauvegarde l'ancien `.env` dans un dossier `backup-before-update-*` ;
- écrit `.env` atomiquement avec permissions privées ; refuse un `.env` qui est un lien symbolique ;
- avant d'arrêter un serveur sur le port 8000, vérifie que le processus est bien `uvicorn server.main:app` et que son répertoire de travail est celui du projet choisi ; ne tue pas un programme arbitraire ;
- redémarre le serveur via la `.venv` existante ;
- attend `/health`, puis ouvre la console si `livekit` vaut true ;
- n'affiche pas les clés.

Si macOS bloque le fichier `.command`, l'exécuter depuis Terminal avec `bash ` suivi du chemin du fichier glissé depuis Finder. Ne pas désactiver globalement les protections du Mac.

Le script générique dans Git attend `livekit-config.json` à côté du `.command`; ce fichier est ignoré par Git et n'est pas fourni dans le dépôt. Le bundle personnel le contient. Si ce bundle n'est plus accessible dans une autre session, l'utilisateur peut remplir `.env` via ses clés LiveKit Cloud, ou fournir une configuration privée à un environnement ayant réellement accès au Mac. Ne pas fabriquer ni deviner des clés.

### Option manuelle de secours

```bash
cd "/Users/flo/Documents/Hackathon/HackJunction/FirstFive"
touch .env
open -a TextEdit .env
```

Enregistrer les trois variables, puis Ctrl C dans le Terminal du serveur et relancer `scripts/start_mac.command`.

### Validation à effectuer après configuration

1. Ouvrir `http://localhost:8000/health` : `"livekit":true` prouve seulement que les trois variables sont présentes, PAS que les credentials sont acceptés ni que le son fonctionne.
2. Rafraîchir la console opérateur à l'adresse `localhost` (important pour l'autorisation microphone du navigateur).
3. iPhone : FirstFive Connected, Reset, caméra des lunettes active, EMERGENCY.
4. Mac : Answer call, autoriser le microphone ; utiliser un casque et séparer physiquement les appareils pour éviter l'écho.
5. Parler depuis les lunettes et écouter sur le Mac, puis parler sur le Mac et écouter dans les lunettes.
6. Vérifier la création de la salle et les deux participants `caller` / `dispatcher` dans LiveKit Cloud si besoin.
7. Si l'un ne rejoint pas : Retry call côté iPhone ou Join / retry voice côté Mac, puis lire l'erreur réelle.
8. Finir l'appel avant de recharger l'opérateur si l'on souhaite garder ses enregistrements.

Tentative de vérification depuis le cloud : une requête API LiveKit **en lecture seule** a été tentée avec les valeurs fournies. Elle a échoué à la résolution DNS du domaine depuis cet environnement. Les identifiants ne sont donc ni validés ni invalidés par ce résultat. Aucun appel WebRTC Cloud réussi n'a été constaté.

## 5. Architecture et fonctionnalités implémentées

### Serveur Python / FastAPI

- `server/main.py` : application HTTP/WS, gestion d'une session courante, permissions des rôles, diffusion vidéo et événements, génération des tokens LiveKit, upload audio, persistance des rapports.
- `server/domain.py` : machine d'état déterministe, questions fixes, métriques et chronologie horodatées par le serveur.
- `server/llm.py` : adaptateurs Anthropic/Gemini, appel visuel et synthèse du rapport, modèles explicitement configurables. Pas de modèle arbitrairement inventé.
- `server/transcription.py` : OpenAI Whisper, transcription de segments audio avec offsets.
- `server/reporting.py` : rapport MIST avec faits, sources, images, transcription/captions, repli déterministe si les services manquent.
- `server/sim_app.py` : producteur WS avec images synthétiques ou vidéo OpenCV et scénarios automatiques.

Scénario du guide :
1. Alerte -> `ai_guide`, question `responsive` : « Is he responding? ».
2. No -> question `breathing` : « Is he breathing normally? ».
3. Deuxième No -> `cpr`, consigne et métronome à 110 bpm.
4. Yes à une question -> `stay`, surveillance.
5. Pickup/Answer call -> `connected`, arrêt du guide et tentative d'appel LiveKit.
6. End -> rapport ; Reset -> annulation de la session courante.

Les réponses hors étape/après décroché sont refusées. La consigne de massage et son démarrage ne prouvent pas qu'une compression physique a été effectuée. Le système n'est pas cliniquement validé.

### Web

- `/console?mode=operator` : vidéo, alerte, décroché/fin, briefing, chronologie, captions, rapport, commandes de répétition.
- `/console?mode=viewer` : vue sans commandes ; adaptée à la projection.
- `/caller` : vue témoin projetable.
- `/test-caller` : simulateur navigateur, utile sans iPhone/lunettes.
- `/report/{id}` : rapport imprimable.
- `web/app.js` : état et UI, contrôles, WebSocket, TTS/speech navigateur de test.
- `web/voice.js` : LiveKit, publication/souscription audio, MediaRecorder, upload des segments.
- Le client JS LiveKit est stocké sous `web/vendor/`, avec sa licence, sans dépendance CDN au moment de la démo.

Les JPEG sont diffusés après alerte uniquement, à fréquence bornée ; images clés limitées et validées. Les rapports sont sauvegardés en JSON atomique. Les rapports historiques survivent au redémarrage ; la session active n'est pas restaurée.

### iOS

- `ios/prepare.py` génère l'exemple officiel CameraAccess aux révisions épinglées, ajoute les fichiers FirstFive, les références Xcode et LiveKit, les permissions nécessaires, les hooks vidéo/statut/audio et le bouton de mise à jour des lunettes.
- `ios/Sources/FirstFiveClient.swift` : WS, JPEG, guide vocal, reconnaissance, métronome, gestion audio Bluetooth et jonction LiveKit.
- `ios/Sources/FirstFivePanel.swift` : URL serveur, Connect, Enable voice, Reset, Retry call, EMERGENCY, Yes/No, état d'écoute et dernier texte reconnu.
- L'exemple officiel conserve l'association Meta AI, le cycle de session/caméra et MockDeviceKit.
- Le dossier généré `ios/CameraAccess/` est ignoré par Git. Il faut exécuter `python ios/prepare.py` sur un nouveau checkout avant d'ouvrir Xcode. Le script refuse d'écraser un projet existant pour préserver les réglages utilisateur.
- Ne pas régénérer par-dessus le projet signé du Mac pour installer un petit correctif : utiliser l'updater ou copier précisément les sources nécessaires.

### Reconnexions et audio

- Les versions cloud récentes utilisent des générations pour ignorer des callbacks iOS anciens après annulation/reconnexion.
- Les segments audio successifs sont gardés par interlocuteur en cas de changement de piste ; retries d'upload idempotents par index.
- Limites : 32 segments et 24 MB par interlocuteur dans le navigateur ; validations et limites serveur également.
- La transcription conserve les offsets. Si une plage audio n'est pas transcrite, les captions de cette plage peuvent servir de repli au lieu de perdre toutes les captions d'un interlocuteur.
- Budget global de transcription 50 s, concurrence 2 ; les résultats terminés sont conservés si d'autres requêtes sont annulées.
- Rechargement de la page appelant testé avec reconnexion et segments supplémentaires. Rechargement opérateur avant upload : l'audio en mémoire est perdu, limitation connue.

## 6. Historique matériel et corrections importantes

### Mise en route Xcode / iPhone

Au début l'utilisateur était dans un projet SwiftUI vide « MyApp ». Il a ensuite ouvert le projet CameraAccess fourni dans une archive. Xcode téléchargeait les dépendances Meta/LiveKit ; « Checking out meta-wearables-dat-ios » ne signifiait pas que l'app cherchait des lunettes. Le mot de passe du trousseau demandé par Xcode était celui du Mac.

L'iPhone n'apparaissait initialement pas, puis confiance USB et mode développeur iPhone ont été activés. Le message « Screen Sharing Unavailable, iOS 27 required » concernait le partage d'écran, pas nécessairement la compatibilité de notre app (minimum iOS 17.2 prévu par le projet). La signature a été réglée avec l'équipe Apple et le bundle ID de l'utilisateur. External Accessory Communication a été demandé dans les Background Modes pour le lien Meta.

### Test sans lunettes

MockDeviceKit a été activé via le bouton bleu 🐞. Un appareil simulé a été associé avec Power, Donned et Unfolded actifs, et Camera source = Back camera. L'utilisateur a confirmé une image sur l'iPhone avec End session.

Le champ `127.0.0.1:8000` était incorrect sur l'iPhone physique. Le remplacement par l'adresse `.local` du Mac et l'autorisation Réseau local ont permis FirstFive Connected. Une erreur Chrome `ERR_SSL_PROTOCOL_ERROR` venait d'une tentative HTTPS sur notre serveur HTTP.

### Passage aux vraies lunettes

L'utilisateur a reçu les lunettes Display 001Q, les a associées dans Meta AI et a rencontré « Erreur interne » au bouton Connect my glasses. La connexion Bluetooth seule ne constituait pas l'enregistrement de l'app par Meta.

Le mode développeur n'était pas visible dans les menus. La procédure proposée était Général -> À propos/informations -> cinq appuis sur Numéro de série pour faire apparaître le mode ; l'utilisateur est ensuite arrivé aux menus développeur. Ne pas présenter cette navigation comme identique sur toutes les versions Meta AI.

Le formulaire « Associer une application Web » ne correspond pas à l'app native CameraAccess : **ne pas y saisir l'URL du serveur FirstFive**. Une autre erreur explicitait qu'une application sur les lunettes devait être mise à jour via App Connections. Les menus Applications montrés contenaient Google/Spotify/etc., pas le chemin recherché.

Inspection du SDK : la méthode `Wearables.shared.openDATGlassesAppUpdate()` existait déjà via `WearablesViewModel.openDATGlassesAppUpdate()`, mais notre interface CameraAccess ne l'exposait pas. Update 03 ajoute « Update app on glasses » dans ⚙️, au-dessus de Disconnect. L'utilisateur a d'abord relancé une ancienne app/projet ; on l'a fait rouvrir le chemin exact, nettoyer/recompiler. **Il a ensuite confirmé que la vraie caméra filmait à travers ses lunettes.**

Puis EMERGENCY a permis de voir cette vidéo sur le Mac : trajet matériel jusqu'à la console validé par l'utilisateur.

### Crash Enable voice et update 04

Capture puis `bt` LLDB fournis par l'utilisateur :

```text
thread #13, queue = com.apple.root.default-qos
EXC_BREAKPOINT
_dispatch_assert_queue_fail
_swift_task_checkIsolatedSwift
closure #1 in FirstFiveClient.enableListening(result=.authorized)
TCC access request callback
```

Cause confirmée : callback d'autorisation Apple héritant de `@MainActor` dans un projet Swift 6, alors qu'Apple le rappelle hors du thread principal. Un `Task { @MainActor ... }` à l'intérieur ne suffit pas : l'assertion se produit avant son corps.

Correction update 04 : fonctions statiques `nonisolated` pour créer les callbacks d'autorisation, continuation renvoyant des Bool, modification d'état sur MainActor. Même précaution pour le tap audio et le callback Speech ; seuls String/Bool traversent vers l'UI. Garde-fous de générations conservés. Ajout des états Listening / Voice enabled et de `Heard:`.

Après livraison, l'utilisateur a signalé que ses « oui/non » n'étaient pas détectés, possiblement à cause du bruit ambiant. La reconnaissance actuelle est **en-US** et attend **Yes/No** (aussi yeah/yep/nope), pas des phrases françaises libres. Il n'a pas fourni de nouveau backtrace. **Ne pas affirmer une validation complète de la correction audio ni de la reconnaissance sur matériel.** Il a choisi un mode de démonstration manuel et a confirmé que ce parcours fonctionne, sauf LiveKit non configuré.

## 7. Archives livrées et état du Mac

Toutes les archives ci-dessous sont hors Git, sous `/workspace/` dans la session cloud :

- `FirstFive.zip` : premier projet complet avec Xcode généré, serveur, web et scripts. Installé par l'utilisateur.
- `FirstFive-iOS-update.zip` : premier correctif Swift de lifecycle ; installation séparée non confirmée.
- `FirstFive-update-02.zip` : mise à jour plus large serveur/web/Swift, segments audio et reprises. L'utilisateur a explicitement dit ne pas l'avoir installée. Ne pas supposer que les sources serveur/web actuelles du cloud sont identiques à celles de son Mac.
- `FirstFive-update-03.zip` : bouton Update app on glasses et génération correspondante, conserve signature/.env/données. Installé avec succès selon le journal utilisateur, puis bon projet rechargé.
- `FirstFive-update-04.zip` : correction Swift 6 Enable voice + statut d'écoute, inclut le code iOS récent et le bouton update 03. Installation proposée ; comportement ultérieur « ne détecte pas » rapporté, sans preuve détaillée de build/version pour cette archive.
- `FirstFive-LiveKit-setup.zip` : installateur personnel prérempli préparé en fin de conversation, pas encore exécuté sur le Mac. Contient des secrets, volontairement exclu du push.

Les updaters font des sauvegardes `backup-before-update-*` et ne remplacent ni `.xcodeproj`, ni `.env`, ni `.venv`, ni `data/`, ni les réglages de signature. Les mises à jour natives 03/04 peuvent être appliquées directement sur la première archive. L'update 04 ne remplace pas l'ensemble du serveur/web de l'update 02.

## 8. Mode de démonstration manuel choisi

Voir `docs/DEMO_MANUELLE.md`.

- Vraie vidéo des lunettes, vrai serveur et console, guide scripté ; réponses saisies par un coéquipier au moment où le témoin parle.
- Présenter cela honnêtement comme « vidéo réelle, réponses pilotées manuellement pour cette démonstration ».
- Dans Chrome Mac, `/console?mode=operator`, tout en bas sous Intervention timeline : ouvrir **Rehearsal controls**.
- `1 · Trigger` : alerte ; `2 · Yes`, `3 · No` : répondre à la question actuelle ; `4 · Repeat prompt` : répéter ; `0 · Reset` : recommencer.
- Les boutons Yes / No dans le panneau iPhone font la même chose.
- Fermer complètement/réouvrir CameraAccess et ne pas appuyer Enable voice permet de repartir sans reconnaissance active.
- Ne pas cliquer Answer call pendant les questions : cela arrête délibérément le guide.
- Pour le scénario No/No, attendre la fin de chaque question avant un seul clic No, puis montrer briefing et métronome. Ne pas réaliser de compressions sur un volontaire sain ; utiliser un mannequin pour les gestes.
- Après Answer call, End & prepare report est activé. Le bouton End de la console est désactivé avant la prise en charge : une tentative de test l'a confirmé ; ce n'est pas un problème de LiveKit.
- Sans LiveKit, la prise en charge peut être montrée avec des captions manuelles, mais ne constitue pas une conversation audio.
- L'utilisateur a confirmé « oui tout marche sauf LiveKit not configured » après ce parcours.

## 9. Tests : résultats, portée et limites

### Automatisés Python

Suite historique : 26 tests. Trois tests ajoutés pour l'installateur `.env` : préservation des autres variables/sauvegardes/permissions, refus de valeur contenant une injection de ligne, refus de `.env` symlink. Total attendu après ce travail : 29 tests ; voir VALIDATION.md pour le résultat final exécuté.

Couverture : machine d'état, branches Yes/No, réponses tardives/hors ordre, permissions rôles WS, JSON invalide, upload/validation JPEG, clé partagée/origines, coordonnées et double producteur, reconnexion/prompt, rapport persistant et échappement HTML, tokens LiveKit et scopes, validations audio/segments/retries, fournisseurs mockés, offsets et repli captions, annulation/budget de transcription, installateur préservant signature/.env.

### Navigateur Chromium

- Smoke trois pages : producteur navigateur, opérateur, viewer ; images JPEG synthétiques, No/No, décroché, repli sans LiveKit, captions manuelles, reload viewer, rapport et reset, aucune exception JS.
- Réexécution pendant le choix du mode démo : remplacement des réponses du producteur par les boutons manuels opérateur ; même parcours complet réussi.
- Un premier essai voulait cliquer End avant Answer call et a expiré car le bouton était volontairement désactivé ; test corrigé pour suivre le vrai parcours, puis réussi. Aucun changement du produit pour masquer cela.

### Audio LiveKit local

- Serveur local loopback, deux clients Chromium à microphones synthétiques ; pistes WebRTC bidirectionnelles et enregistrements > 1 KB.
- Deux répétitions, dont reload appelant produisant deux segments caller et un segment dispatcher ; offsets/exports vérifiés.
- Cela ne valide pas l'intelligibilité de voix humaines ni la route Bluetooth des lunettes.
- LiveKit Cloud n'est pas validé. Les valeurs du projet existent, mais leur application au serveur du Mac est le travail restant.

### Fournisseurs IA / STT

- SDK officiels Anthropic/Gemini/OpenAI testés par HTTP simulé, pas via modèles réels payants.
- Aucun modèle/clé réel de ces fournisseurs confirmé dans cette conversation.
- Sans configuration, rapports déterministes et captions de repli : ne pas promettre d'analyse visuelle ou de transcription réelle.

### iOS et matériel

- Premier build et lancement : confirmés par utilisateur, pas exécutés dans Linux.
- MockDeviceKit + image téléphone : confirmés utilisateur.
- Signature, association Meta, mise à jour app lunettes, vraie vidéo lunettes -> iPhone -> Mac : confirmés utilisateur.
- Guidage/commandes manuelles/métronome : l'utilisateur dit que tout fonctionne, sans mesures détaillées de latence ni de route audio.
- Swift update 04 : génération et intégration vérifiées, pas de compilation locale possible. Reconnaissance vocale non fiable/non démontrée et abandonnée pour la démo.

## 10. Ce qu'il reste à faire, par priorité

### Priorité immédiate

1. Exécuter l'installateur LiveKit personnel sur le Mac, ou enregistrer les trois valeurs dans `.env` puis redémarrer le serveur.
2. Vérifier `/health`, puis un vrai appel audio aller-retour lunettes/iPhone ↔ navigateur opérateur, avec permissions microphone et casque côté Mac.
3. Si échec, collecter les messages FirstFive/console/Xcode et l'état de salle LiveKit. Différencier auth, réseau/WebRTC/TURN, publication micro et sortie Bluetooth. Ne pas simplement cliquer plusieurs fois Retry sans examiner l'erreur.
4. Répéter la démo complète avec la saisie manuelle choisie, puis End, rapport, Reset et deuxième essai.

### Avant de revendiquer une intégration complète

- Confirmer quelle version serveur/web est installée sur le Mac ; update 02 n'a pas été confirmée. Déployer les améliorations de segments/reconnexion si elles sont nécessaires à la démo, en préservant la signature et `.env`.
- Tester coexistence caméra Meta, micro Bluetooth HFP et LiveKit après pickup, y compris remise en arrière-plan/reconnexion.
- Vérifier enregistrements des deux pistes, uploads, rapport et répétition de session ; sans clé OpenAI, pas de transcription automatique du fichier audio.
- Si l'utilisateur veut la voix naturelle ensuite : reproduire avec « Yes/No » dans le calme, observer Listening/Heard, route micro, permissions Speech, connectivité du service Apple, résultats finaux et erreurs. Ajouter français ou parser contrôlé seulement si demandé ; ne pas attribuer tout au bruit sans preuve.
- Configurer éventuellement un fournisseur LLM et un modèle disponible pour l'analyse visuelle/synthèse, et OpenAI pour la transcription ; tester avec données consenties et sources.

### Limites connues / hors périmètre livré

- Une session en mémoire, un producteur WS, un processus serveur. Pas d'architecture multi-centres ni de reprise d'intervention après redémarrage.
- Pas de guide autonome hors réseau.
- GPS iPhone réel et batterie lunettes réelle non implémentés ; la console peut afficher Location not provided / Camera status unavailable. Le statut caméra est envoyé seulement pendant une intervention et dépend des transitions reçues.
- Pas de vrai appel 112, pas d'envoi hôpital, pas de validation clinique ni de diagnostic indépendant depuis la vidéo.
- Le mode opérateur/vue et une clé partagée optionnelle ne constituent pas une authentification métier multi-utilisateurs ; ne pas exposer le prototype tel quel sur Internet.
- Un reload opérateur perd l'audio en mémoire non envoyé. Reset annule et abandonne cet audio.
- Les métriques sont des horodatages serveur et le démarrage du guidage, pas des mesures physiques de compressions.
- Les références de sources dans les rapports IA sont contrôlées structurellement, sans garantie sémantique contre l'hallucination.
- Les doublons Objective-C entre MWDATMockDevice et MWDATCamera ont produit des avertissements ; ne pas supprimer arbitrairement les frameworks. Le crash Enable voice a été identifié séparément par backtrace.

## 11. Reprendre depuis Git

Lire d'abord ce fichier, `README.md`, `docs/VALIDATION.md`, `docs/DEMO_MANUELLE.md` et `docs/UPDATE_04.md`.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/pytest -q
.venv/bin/ruff check .
node --check web/app.js
node --check web/voice.js
```

Démarrage backend :

```bash
.venv/bin/python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
```

Nouveau projet iOS seulement (pas pour écraser le projet signé existant) :

```bash
python3 ios/prepare.py
```

Tests navigateur : serveur de test dédié et `FIRSTFIVE_TEST_URL`, puis `tests/browser_smoke.py`. Pour l'audio local, voir README et `tests/browser_voice.py`; ne pas utiliser `ws://127.0.0.1:7880` comme adresse LiveKit sur un iPhone physique.

Le push sur main doit contenir le code, les scripts génériques, la documentation, les tests, les dépendances épinglées et les licences nécessaires. Il doit exclure `.env`, les clés, les JSON de configuration privés, les archives personnelles, `.venv`, `data/`, les sauvegardes et le projet Xcode signé/généré. Les secrets et les données locales ne doivent pas être publiés pour satisfaire « push tout ».
