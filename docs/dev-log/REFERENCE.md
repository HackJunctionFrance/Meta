# FirstFive — guide d'implémentation (version finale)

Nov 14, 2026 · @Florian

Ce doc contient tout le contexte nécessaire pour démarrer une nouvelle discussion avec Claude Code.

**Mise à jour 18h30** : (1) la conversation appelant ↔ régulateur passe par notre système (LiveKit), est enregistrée et transcrite, et le rapport contient une synthèse pour l'hôpital ; (2) plus de WhatsApp ; (3) le modèle d'IA est au choix (Claude ou Gemini) via un seul module ; (4) l'appairage des lunettes prêtées et le mode développeur sont confirmés, et une paire est réservée pour la démo.

## 1. Contexte

On participe à Junction 2026 (Helsinki, 13–15 novembre 2026), sur la piste Meta « AI Glasses for Everyone, Everyday ». On rend dimanche matin un prototype qui marche, une démo et un deck. **L'heure exacte de soumission est à vérifier sur la plateforme** ; ce guide vise une soumission vers 7h00, heure d'Helsinki.

**Ce que Meta demande dans le brief** : un problème du quotidien bien ciblé, un prototype fonctionnel et un deck, un pilote crédible, du consentement et des données sûres, la gestion des permissions, des erreurs, de la connectivité et de l'état de l'appareil.

**Ce que le mentor Meta nous a dit** : ils veulent un usage grand public, utilisable par beaucoup de gens. On peut partir d'une niche si on montre comment elle s'étend.

**Les critères du jury (25 % chacun)** : créativité et cas d'usage ; exécution technique ; valeur réelle et faisabilité ; expérience utilisateur, accessibilité et confiance.

**Notre matériel** : un iPhone 13, un MacBook Pro M5, et des lunettes Meta prêtées par le stand (Ray-Ban Meta Gen 2 ou Meta Ray-Ban Display). Les lunettes arrivent environ 1 heure après le début de l'implémentation : tout ce qui précède doit pouvoir avancer sans elles. Je les aurais pour 2h.

## 2. Le produit

**En une phrase** : face à une urgence, tu dis « Emergency » ; une IA te fait agir tout de suite, une autre prépare le dossier pour le 112, le régulateur voit en direct ce que voient tes lunettes et te guide, et un rapport complet part aux secours à la fin.

**Le problème, chiffré**

- Le 112 finlandais décroche vite : 5 secondes en moyenne au premier semestre 2026, 99 % en moins de 30 secondes ([source](https://verkkouutiset.fi/a/hatanumeroon-lahetettyjen-tekstiviestien-maara-kasvoi-400-prosenttia)).
- Mais le régulateur doit ensuite poser ses questions avant de guider. Dans une étude américaine, il fallait 75 secondes en médiane pour reconnaître l'arrêt cardiaque, et 176 secondes jusqu'à la première compression guidée ([source](https://bvbvf1.bib-bvb.de/vufind/PrimoRecord/cdi_proquest_miscellaneous_1443384391)). Une autre étude trouve 240 secondes ([source](https://rcastoragev2.blob.core.windows.net/44893c4071fb172b777b3ee00ed3dba6/PMC9076962.pdf)).
- Chaque minute sans massage fait baisser la survie de 7 à 10 % ([source](https://www.ibtimes.co.uk/cardiac-arrest-early-cpr-doubles-chances-survival-two-major-studies-show-1505733)).
- Le régulateur est aveugle : il guide à la voix. Guidés par vidéo via des lunettes, 9 témoins sur 14 ont fait la procédure correctement, contre 0 sur 14 au téléphone ([source](https://pubmed.ncbi.nlm.nih.gov/37418840/)).
- En Finlande, la vidéo vers le 112 n'existe pas encore, mais la loi prévoit déjà le cas ([source](https://www.edilex.fi/he/20250063)).

**Les quatre briques**

| Brique | Forme | Rôle |
| --- | --- | --- |
| **IA guide** | Une voix dans les lunettes | Te fait agir dès la première seconde (« Il te répond ? Il respire ? Appuie au centre de la poitrine »). Tu réponds juste « oui » ou « non ». Elle se tait dès que le régulateur décroche |
| **IA messager** | Un message écrit sur l'écran du régulateur, jamais de voix | Résume la situation, les réponses déjà données et les heures. Le régulateur n'a plus à poser ces questions |
| **Console du régulateur** | Une page web (simulation de son poste) | Vidéo des lunettes en direct, message de l'IA, chronologie. Le régulateur et l'appelant se parlent de vive voix |
| **Rapport** | Une page générée à la fin | Chronologie, images clés légendées, résumé, heure de la première compression, transcription du régulateur |

**Ce qui nous différencie** : d'autres projets de hackathon font du guidage premiers secours sur Ray-Ban Meta ([Aegis Vision](https://devpost.com/software/aegis-vision), [FirstSight](https://github.com/dtseng123/firstsight)). Nous, on relie le témoin à toute la chaîne de secours : l'IA comble les minutes avant le premier geste, le régulateur voit la scène, et les secours reçoivent un rapport. L'IA ne remplace jamais le régulateur, elle lui fait gagner du temps.

## 3. Le scénario de démo

Un seul scénario, bien joué : une personne s'effondre, arrêt cardiaque. La démo est en anglais, car le jury parle anglais.

**Qui est où**

- **Sur scène** : toi avec les lunettes, un coéquipier qui joue la victime, un coussin pour le massage.
- **En coulisses** : le coéquipier « régulateur », avec son ordinateur, Chrome et un casque micro. Il ne doit pas être visible ni audible dans la salle.
- **Deux écrans côte à côte** (deux fenêtres de ton Mac sur le projecteur, ou deux écrans) :
  - **Écran 1 — « Ce que vit l'appelant »** : la vue des lunettes en grand, ce que l'appelant entend en sous-titres (phrases de l'IA guide, puis du régulateur), et l'état (« AI guide » → « Connected to 112 »).
  - **Écran 2 — « Ce que voit le régulateur »** : sa console en lecture seule (vidéo, message de l'IA messager, chronologie, sous-titres, puis le rapport).

**Seconde par seconde (indicatif)**

| Temps | Toi | Ce que tu entends | Écran 2 (régulateur) |
| --- | --- | --- | --- |
| 0 s | La victime s'effondre. Tu dis « Emergency » | IA guide : « Calling emergency services. Is he responding? Shake his shoulders. » | La console sonne : appel entrant, position |
| 3 s | Tu secoues ses épaules : « No » | IA guide : « Is he breathing normally? Look at his chest. » | Message IA : « Not responding — 0:03 » |
| 6 s | « No » | IA guide : « Put your hands in the center of his chest. Push hard and fast, follow the beat. » + métronome | Message IA : « Not breathing — 0:06 · CPR guided since 0:08 » |
| \~10 s | Tu masses le coussin | — | Le régulateur clique « Answer » : vidéo en direct |
| \~12 s | Tu continues | **La voix du régulateur** : « Emergency services, I can see your video. Keep pushing, a bit faster. » (l'IA guide s'est tue) | Ses phrases s'affichent en sous-titres |
| \~1 min 30 | « Paramedics are here » | — | Le régulateur clique « End » : le rapport s'affiche |

**La phrase de conclusion** : « Today it takes about 3 minutes before the first guided compression. With FirstFive, CPR started 8 seconds after the collapse — and the dispatcher saw everything. »

## 4. Les décisions techniques, et pourquoi

Chaque choix vise la même chose : une démo qui marche à coup sûr, construite en une nuit, testable sans lunettes jusqu'au dernier moment.

| Décision | Pourquoi |
| --- | --- |
| **Lunettes utilisées en audio seul (pas d'écran, pas de bracelet)** | Même code sur la Gen 2 et la Display, donc on prend la paire disponible. On évite la combinaison caméra + écran, que Meta déconseille sur la Display ([problèmes connus](https://wearables.developer.meta.com/docs/develop/dat/knownissues/)). Et le jury ne voit pas l'écran du verre de toute façon |
| **App iPhone native en Swift, lancée depuis Xcode** | Seul le kit Meta (DAT) donne accès à la caméra et au micro des lunettes. Pas de publication sur l'App Store : on installe directement sur l'iPhone |
| **On part de l'app d'exemple « CameraAccess » de Meta** | La connexion aux lunettes et le flux vidéo sont déjà faits. On ajoute seulement nos morceaux |
| **L'app est petite, le serveur fait le reste** | Le Swift est ce qui prend le plus de temps à déboguer. On y met le minimum : capter, parler, écouter, envoyer, et rejoindre l'appel LiveKit |
| **Serveur Python FastAPI sur le Mac, un seul processus** | Rapide à écrire avec Claude Code, facile à relancer. L'état tient en mémoire, avec un fichier JSON de sauvegarde |
| **Pages web en HTML + JavaScript simple, sans framework** | Pas de compilation, pas de dépendances : on recharge la page et c'est à jour |
| **Vidéo = 2 à 3 images JPEG par seconde via WebSocket** | Beaucoup plus simple qu'un vrai flux vidéo, largement suffisant pour une console |
| **IA guide = liste fixe d'étapes, pas une IA qui improvise** | Aucun risque de consigne inventée, comportement identique à chaque répétition. La reconnaissance vocale ne doit comprendre que « yes », « no » et « emergency » |
| **IA messager = texte construit par le code + une ligne du modèle d'IA sur l'image** | Les faits (réponses, heures) viennent du code, donc ils sont exacts. Le modèle ajoute seulement une description visuelle |
| **Rapport : chiffres calculés par le code, texte par le modèle d'IA** | L'heure de la première compression et les durées sont calculées, jamais demandées au modèle |
| **Modèle d'IA interchangeable : Claude (Anthropic) ou Gemini** | Un seul module `llm.py`, le fournisseur se choisit dans `.env`. Les deux acceptent des images. On décide plus tard sans toucher au reste du code |
| **Voix régulateur ↔ appelant : LiveKit, dans notre app et notre console** | Pas de WhatsApp pour une urgence. La conversation passe par notre système, ce qui permet de l'enregistrer et de la transcrire pour le rapport aux secours et à l'hôpital. LiveKit fournit les bibliothèques iPhone et navigateur, avec une offre gratuite |
| **Enregistrement côté console, transcription à la fin** | La console enregistre deux pistes séparées (le régulateur, l'appelant) et les envoie au serveur au clic sur End. Le serveur les transcrit avec l'heure, puis le modèle en fait la synthèse. Pas d'agent en temps réel à coder |
| **Sous-titres en direct du régulateur : reconnaissance vocale de Chrome sur son ordinateur** | Gratuit, immédiat, sans serveur. Tu es sur scène, donc ta voix s'entend sans sous-titres |
| **Un simulateur d'app en Python** | Un script imite l'iPhone (alerte, réponses, images d'une vidéo enregistrée). Toutes les pages et le rapport se construisent et se testent sans téléphone ni lunettes |
| **Boutons de secours cachés dans la console** | Déclencher, injecter « yes » ou « no », forcer une étape : si la reconnaissance vocale rate sur scène, le coéquipier rattrape sans que le jury le voie |
| **Réseau : partage de connexion de l'iPhone** | Le Wi-Fi des hackathons bloque souvent les connexions entre appareils. Avec le partage de connexion, le Mac et l'ordinateur du régulateur sont sur le même réseau que l'iPhone, avec Internet pour le modèle d'IA et LiveKit |

## 5. Architecture

Tout passe par le serveur sur ton Mac : l'iPhone lui envoie l'alerte, les réponses et les images ; le serveur les diffuse aux pages web et appelle le modèle d'IA. La voix entre toi et le régulateur passe par LiveKit (un service en ligne) ; la console l'enregistre et l'envoie au serveur à la fin, pour la transcription et le rapport.

&#91;embedded content: architecture · 6 composants\]

La ligne pointillée est la conversation de vive voix (LiveKit). La console l'enregistre et l'envoie au serveur à la fin, pour la transcription et le rapport.

**Les appareils**

| Appareil | Ce qui tourne dessus |
| --- | --- |
| Lunettes Meta | Caméra, micro, haut-parleurs (rien à installer à part le kit Meta, via l'app Meta AI) |
| iPhone 13 | Notre app FirstFive (Swift + kit Meta + LiveKit) et l'app Meta AI. Il partage sa connexion |
| Ton Mac (sur scène) | Le serveur, et deux fenêtres de navigateur projetées : Écran 1 et Écran 2 (console en lecture seule) |
| Ordinateur du régulateur (coulisses) | La console en mode opérateur dans Chrome : vidéo, voix LiveKit, sous-titres, enregistrement de l'appel |

**Le réseau** : l'iPhone active son partage de connexion ; le Mac et l'ordinateur du régulateur s'y connectent. Tout le monde voit le serveur à l'adresse locale du Mac (par exemple `http://172.20.10.2:8000`). L'adresse du serveur se règle dans l'app, sans recompiler.

**Les pages servies par le serveur**

- `/console?mode=operator` : la console du régulateur (boutons, micro, sous-titres).
- `/console?mode=viewer` : la même console sans boutons, pour l'Écran 2.
- `/caller` : l'Écran 1, « ce que vit l'appelant ».
- `/report/{session_id}` : le rapport.

## 6. Le protocole de messages

Une seule intervention à la fois (c'est une démo) : le serveur garde une « session courante ». Tous les échanges passent par WebSocket en JSON, sauf les images, envoyées en binaire. Chaque message porte `ts` (heure du client en millisecondes) ; le serveur ajoute sa propre heure, qui fait foi pour la chronologie.

**Connexions**

- App iPhone → `ws://<mac>:8000/ws/app`
- Pages web → `ws://<mac>:8000/ws/ui?role=operator|viewer|caller`
- Images : messages **binaires** sur `/ws/app` (JPEG brut). Le serveur garde la dernière image et la renvoie en binaire à toutes les pages.

**De l'app vers le serveur**

```json
{"type": "alert", "ts": 0, "lat": 60.18, "lon": 24.83, "trigger": "voice|button"}
{"type": "guide_step", "ts": 0, "step_id": "responsive", "spoken": "Is he responding? Shake his shoulders."}
{"type": "answer", "ts": 0, "step_id": "responsive", "value": "no", "heard": "no"}
{"type": "cpr_started", "ts": 0}
{"type": "status", "ts": 0, "glasses": "connected|disconnected", "battery": 72, "stream": "streaming|paused|stopped"}
```

**Des pages vers le serveur** (console en mode opérateur seulement)

```json
{"type": "pickup", "ts": 0}
{"type": "dispatcher_said", "ts": 0, "text": "Keep pushing, a bit faster.", "final": true}
{"type": "end", "ts": 0}
{"type": "override", "action": "trigger|answer_yes|answer_no|next_step|reset"}
```

**Du serveur vers l'app**

```json
{"type": "pickup"}
{"type": "override", "action": "trigger|answer_yes|answer_no|next_step|reset"}
{"type": "end"}
```

**Du serveur vers les pages**

```json
{"type": "state", "phase": "idle|alerting|ai_guide|connected|ended", "session_id": "...", "started_at": 0}
{"type": "timeline", "event": {"t": 3.2, "kind": "answer", "label": "Not responding"}}
{"type": "messenger", "card": {"location": "...", "situation": "...", "facts": [{"t": 3.2, "text": "Not responding"}], "scene": "Person lying on the floor, indoors"}}
{"type": "caller_heard", "source": "ai_guide|dispatcher", "text": "..."}
{"type": "report_ready", "url": "/report/abc123"}
```

**Les phases** : `idle` → (alert) `alerting` + `ai_guide` en parallèle → (pickup) `connected` → (end) `ended`. Un bouton `reset` remet tout à zéro entre deux répétitions.

**Ajouts pour la voix et le rapport**

- `GET /livekit/token?role=caller|dispatcher` : le serveur crée la salle de la session et renvoie un jeton d'accès LiveKit. L'app et la console le demandent au moment du décroché.
- `POST /session/{id}/audio?track=dispatcher|caller` : la console envoie les deux enregistrements (fichiers WebM) au clic sur End. Le serveur les transcrit, puis génère le rapport.
- Message serveur → pages : `{"type": "report_progress", "step": "transcribing|summarizing|done"}`, pour afficher l'avancement du rapport.

## 7. Le détail de chaque composant

### 7.1 Serveur (`server/`, Python 3.11+, FastAPI + uvicorn)

- **Session courante** en mémoire : phase, heure de début, chronologie, réponses, transcription, images clés. Sauvegardée dans `data/<session_id>/session.json` à chaque événement.
- **Images** : garder la dernière image reçue et la diffuser aux pages (limiter à 3 par seconde). Sauvegarder une image clé à chaque événement de la chronologie, plus une toutes les 10 secondes, dans `data/<session_id>/frames/`.
- **IA messager** : à chaque réponse, reconstruire la carte (`location`, `situation`, liste de faits avec l'heure relative). Toutes les 8 secondes pendant les phases `ai_guide` et `connected`, envoyer la dernière image au modèle d'IA avec la consigne : « Décris la scène en une ligne factuelle, sans diagnostic », et mettre le résultat dans `scene`. Si le modèle ne répond pas en 5 secondes, garder la ligne précédente.
- **Situation** : déduite des réponses par le code. Ne répond pas + ne respire pas = « Suspected cardiac arrest — CPR guided ». Jamais par le modèle.
- **LiveKit** : générer les jetons d'accès avec le SDK Python officiel de LiveKit (clés dans `.env`). Une salle par session.
- **Transcription** : à la réception des deux enregistrements, les transcrire avec l'heure de chaque segment (fournisseur de reconnaissance vocale au choix, par exemple ElevenLabs Speech-to-Text, sponsor du hackathon, ou l'API de transcription d'OpenAI ; vérifier qu'il renvoie l'horodatage par segment). Fusionner les deux pistes en un dialogue ordonné par l'heure : « \[0:42\] Dispatcher : … », « \[0:45\] Caller : … ».
- **Rapport** (après la transcription) :
  1. Le code calcule les chiffres : durée totale, délai alerte → première compression, délai alerte → décroché, durée du massage.
  2. Il choisit 4 à 6 images clés (une par événement important).
  3. Il envoie au modèle la chronologie, les images et la transcription complète, et demande un JSON : `summary` (5 phrases maximum), `captions` (une légende par image), `observations` (ce qui est visible, sans diagnostic) et `handover` : la synthèse pour l'hôpital au format MIST (circonstances, lésions ou état constaté, signes, gestes faits), **uniquement à partir de ce qui a été dit ou vu**, avec l'heure de la source pour chaque élément.
  4. Il assemble la page HTML du rapport. Si le modèle ou la transcription échoue, il produit quand même le rapport avec les chiffres, la chronologie, les images et les sous-titres en direct.
- **Modèle d'IA** : un module `llm.py` avec deux implémentations interchangeables, Anthropic Claude et Google Gemini (SDK officiels, images acceptées en entrée). Choix par `LLM_PROVIDER=anthropic|gemini` dans `.env`. Sortie JSON structurée, délai maximal et repli pour chaque appel. Les identifiants exacts des modèles sont à vérifier dans les consoles des fournisseurs.
- **Simulateur** (`server/sim_app.py`) : imite l'iPhone. Il envoie l'alerte, déroule les réponses avec les bons délais et envoie les images d'une vidéo enregistrée (`sample.mp4`, lue avec OpenCV). Option `--auto-pickup` pour tester tout le scénario seul, et option pour envoyer deux petits fichiers audio enregistrés à l'avance afin de tester le rapport sans appel.

### 7.2 Console (`web/console.html`)

- **Disposition** : bandeau d'état en haut (« INCOMING EMERGENCY » clignotant, puis « CONNECTED 00:42 »), vidéo au centre, carte de l'IA messager à droite, chronologie en bas, sous-titres sous la vidéo.
- **Mode opérateur** : un son d'appel à l'alerte ; un bouton **Answer** (envoie `pickup`, demande un jeton LiveKit et rejoint la salle avec le micro) ; un bouton **End** (arrête les enregistrements, envoie les deux fichiers, puis envoie `end`) ; la reconnaissance vocale de Chrome (`webkitSpeechRecognition`, anglais) pour les sous-titres en direct, chaque phrase finale envoyée en `dispatcher_said`, avec relance automatique quand elle s'arrête.
- **Enregistrement** : dès **Answer**, deux `MediaRecorder` : un sur le micro du régulateur, un sur la piste audio de l'appelant reçue de LiveKit. Ils s'arrêtent à **End**.
- **Boutons cachés** (touches clavier, par exemple 1 = trigger, 2 = yes, 3 = no, 4 = next, 0 = reset) qui envoient `override`.
- **Mode lecture seule** : même affichage, sans boutons ni micro, sans rejoindre l'appel. Il lit à voix haute les phrases du régulateur (synthèse vocale du navigateur, désactivable), pour que la salle les entende.
- **Fin** : afficher l'avancement (`report_progress`), puis le rapport à la place de la vidéo quand `report_ready` arrive.
- **Style** : fond sombre, gros caractères lisibles au projecteur, rouge pour l'alerte, vert pour « connected ».

### 7.3 Écran 1 (`web/caller.html`)

- La vue des lunettes en plein écran.
- En bas, en grand sous-titre : ce que l'appelant entend, avec la source (« AI guide » en bleu, « 112 dispatcher » en vert).
- En haut : l'état (« AI guide active » → « Connected to 112 »), un chronomètre depuis l'alerte et, pendant le massage, le rythme du métronome.
- Un petit voyant « Glasses connected / battery », pour la note « état de l'appareil ».

### 7.4 Rapport (`/report/{id}`)

En-tête (heure, position, type, durée) · quatre chiffres en grand (alerte → 1re compression, alerte → décroché, durée du massage, durée totale) · chronologie horodatée · images clés légendées · résumé · transcription du régulateur · mention « Generated automatically from the glasses video — to be verified by responders » · bouton « Print / PDF » (impression du navigateur).

### 7.5 App iPhone (`ios/`, Swift, à partir de l'exemple CameraAccess)

- **Prérequis Meta** : Xcode 26.4+, Swift 6.3+, iOS 17.2 minimum ([AGENTS.md du kit](https://github.com/facebook/meta-wearables-dat-ios/blob/main/AGENTS.md)). L'iPhone 13 convient.
- **LiveKit** : ajouter le SDK Swift officiel de LiveKit (Swift Package Manager).
- **Écran unique** : statut des lunettes (connectées, batterie, flux), statut serveur, champ « adresse du serveur » (mémorisé), gros bouton rouge **EMERGENCY**, bouton **Reset**. Garder l'écran allumé (`isIdleTimerDisabled = true`).
- **Ordre de démarrage** : d'abord l'audio Bluetooth, ensuite la caméra. La doc Meta prévient que démarrer le flux avant que l'audio soit prêt peut faire échouer le son sans erreur ([doc audio](https://wearables.developer.meta.com/llms.txt?product=all&version=1.0&document=products/dat/sections/guides/microphones-and-speakers)).
- **Flux caméra** : résolution `low` ou `medium`, 15 images/s depuis les lunettes ; l'app convertit en JPEG (qualité 0,5) et envoie au plus 3 images/s.
- **Écoute** : le module Speech du kit (testable avec les lunettes simulées). Mots reconnus : « emergency », « yes/yeah/yep », « no/nope ». Problème connu : la reconnaissance s'arrête sans prévenir au bout d'une minute, donc la relancer toutes les 50 secondes. Solution de repli si le module pose problème : la reconnaissance vocale d'Apple (`SFSpeechRecognizer`) sur l'entrée Bluetooth.
- **Voix** : `AVSpeechSynthesizer` en anglais. Le son sort dans les lunettes, car elles sont le casque Bluetooth du téléphone. Ne pas écouter pendant que l'app parle, pour ne pas s'entendre soi-même.
- **IA guide** (machine à états) : `responsive?` → `breathing?` → `cpr` (métronome à 110/min : un clic toutes les 545 ms, plus un rappel vocal toutes les 20 s). Si la réponse est « yes » à `responsive` ou `breathing` : une phrase de fin simple (« Stay with him, help is coming »).
- **Au message `pickup`** : arrêter l'IA guide, la reconnaissance vocale et le métronome ; demander un jeton LiveKit au serveur et rejoindre la salle (micro des lunettes publié, voix du régulateur jouée dans les lunettes). Le flux vidéo continue. À `end` : quitter la salle.
- **Audio de l'appel** : session audio iOS en mode conversation, Bluetooth autorisé, pour que micro et son passent par les lunettes. Vérifier que le flux caméra du kit continue pendant l'appel (test 6).
- **Reconnexion** : si le WebSocket tombe, réessayer toutes les 2 secondes ; si les lunettes se déconnectent, l'afficher et le signaler au serveur (`status`).

## 8. Plan d'implémentation par phases

Les phases 1 et 2 ne demandent ni iPhone ni lunettes : on les lance tout de suite. La phase 3 utilise les lunettes simulées. Les vraies lunettes n'arrivent qu'en phase 4, quand tout le reste marche déjà. Avec Claude Code : une phase à la fois, et on vérifie le critère « fini quand » avant de passer à la suivante.

| Phase | Ce qu'on construit | Fini quand | Durée visée |
| --- | --- | --- | --- |
| **0. Squelette** | Dépôt `firstfive/` avec `server/`, `web/`, `ios/`, `README.md`, `.env.example`. Serveur FastAPI qui sert les pages et les deux WebSockets | `uvicorn` démarre, les 3 pages s'ouvrent depuis un autre appareil du réseau | 20 min |
| **1. Serveur + pages + simulateur** | Session et phases, diffusion des images, console (opérateur et lecture seule), Écran 1, `sim_app.py` avec la vidéo enregistrée, boutons cachés | Le simulateur déclenche une alerte, les deux écrans affichent la vidéo et les réponses, **Answer** passe en « connected », **Reset** remet à zéro | 1 h 30 |
| **2. IA messager + sous-titres + rapport** | `llm.py` (Claude ou Gemini selon `LLM_PROVIDER`), ligne de scène dans la carte de l'IA messager, reconnaissance vocale de Chrome dans la console, rapport (chiffres, chronologie, images, résumé) | Avec le simulateur, la carte se remplit, tes phrases au micro s'affichent en sous-titres, **End** produit le rapport. Changer `LLM_PROVIDER` et relancer donne un rapport équivalent | 1 h 30 |
| **3. Voix LiveKit sans lunettes** | Jetons LiveKit, **Answer** rejoint la salle, page de test `/test-caller` (un navigateur joue l'appelant), deux enregistrements dans la console, envoi à **End**, transcription, dialogue et synthèse pour l'hôpital dans le rapport | Depuis `/test-caller` sur le téléphone et la console, vous vous parlez ; **End** produit un rapport avec la transcription horodatée et la synthèse MIST | 1 h 30 |
| **4. App iPhone (lunettes simulées)** | À partir de CameraAccess : adresse du serveur, WebSocket, envoi des images, IA guide (voix + écoute), bouton EMERGENCY, `pickup` et `override`, puis entrée dans l'appel LiveKit au `pickup` | Sur l'iPhone, avec le Mock Device Kit : l'alerte arrive sur la console, l'IA guide parle, **Answer** la fait taire et l'iPhone rejoint l'appel | 2 h 30 |
| **5. Vraies lunettes** | Tests de la section 10, dans l'ordre, dont le test 6 (voix + caméra en même temps). Ajustements (résolution, délais, mots reconnus) | Le scénario complet tourne avec les lunettes, voix et vidéo ensemble | 1 h |
| **6. Finitions et répétitions** | Style des écrans, sons, textes, 3 répétitions chronométrées, vidéo de secours filmée, deck | La démo tient en 2 min sans accroc, la vidéo de secours est prête | 1 h 30 |

**Ordre de coupe si on est en retard** (on retire dans cet ordre) : la lecture à voix haute dans l'Écran 2 → la ligne de scène dans l'IA messager → la carte GPS → le voyant batterie. **Ne jamais couper** : l'IA guide, la vidéo sur la console, le passage de relais, la voix LiveKit, le rapport avec la synthèse pour l'hôpital.

**Si le réseau pose problème** : le serveur doit aussi marcher en `localhost`, avec le simulateur, pour au moins démontrer les écrans.

## 9. Setup manuel à faire maintenant

Ce sont les étapes que Claude Code ne peut pas faire à ta place : comptes, téléchargements, réglages du téléphone. Fais-les pendant que Claude Code attaque les phases 0 à 2, pour être prêt dès que les lunettes arrivent. **Commence par Xcode** : c'est le plus long à télécharger.

**Mac**

- [ ] Installer **Xcode 26.4 ou plus** (App Store), l'ouvrir une fois, accepter la licence et installer les composants iOS proposés.
- [ ] Dans Xcode → Réglages → Comptes : se connecter avec ton identifiant Apple (le compte gratuit suffit pour installer sur ton iPhone).
- [ ] Installer **Claude Code** si ce n'est pas déjà fait, et **Python 3.11+** (Claude Code peut s'en charger avec ta permission).
- [ ] Installer **Chrome** sur le Mac et sur l'ordinateur du régulateur (la reconnaissance vocale de la console n'existe que dans Chrome).

**Clés et comptes**

- [ ] Créer une clé API pour le **modèle d'IA** : Anthropic (console.anthropic.com) et/ou Gemini (Google AI Studio). Avoir les deux permet de basculer en 10 secondes si l'un est lent. Noter l'identifiant exact du modèle choisi.
- [ ] Créer une clé pour la **transcription** : ElevenLabs (sponsor du hackathon, demander s'il y a des crédits) ou OpenAI. Vérifier que l'API renvoie l'heure de chaque segment.
- [ ] Créer un compte gratuit **LiveKit Cloud** (obligatoire maintenant : c'est la voix de l'appel) et noter l'URL du projet, la clé et le secret API.
- [ ] Créer un compte développeur sur le **Wearables Developer Center** de Meta, et y créer une app iOS si le README de l'exemple le demande. Attention : si tu es connecté à developers.meta.com (Horizon), déconnecte-toi d'abord, sinon les liens peuvent échouer ([problèmes connus](https://wearables.developer.meta.com/docs/develop/dat/knownissues/)). Attention aussi : pas de tiret « - » dans le Bundle ID iOS.

**iPhone 13**

- [ ] Brancher l'iPhone au Mac, faire « Se fier à cet ordinateur », puis activer le **Mode développeur** (Réglages → Confidentialité et sécurité → Mode développeur ; le téléphone redémarre). L'option n'apparaît qu'après le premier branchement à Xcode.
- [ ] Installer l'app **Meta AI** et s'y connecter.
- [ ] Vérifier que le **partage de connexion** marche : activer, y connecter le Mac et l'ordinateur du régulateur, noter l'adresse IP du Mac. LiveKit Cloud passe par Internet : vérifier que le partage donne bien accès à Internet.

**Au stand Meta (à demander tout de suite)**

- [x] Appairer les lunettes prêtées à ton app Meta AI et y activer le mode développeur : **confirmé**.
- [ ] Le kit (DAT) est-il déjà installé sur les paires, ou faut-il l'installer ? Pour l'installer, il faut porter les lunettes, avoir la batterie au-dessus de 10 % et garder l'app Meta AI ouverte quelques secondes.
- [x] Une paire pour la démo finale : **confirmé**. Demander aussi si on peut la garder un moment pour filmer la vidéo de secours.

**Matériel et contenu pour la démo**

- [ ] **Filmer maintenant une vidéo de 30 à 60 secondes**, téléphone à hauteur des yeux : un coéquipier allongé au sol, quelqu'un qui le secoue, puis qui masse un coussin posé sur sa poitrine. Elle sert pour le simulateur, le Mock Device Kit et comme vidéo de secours.
- [ ] Un coussin ou un mannequin, et un casque micro pour le régulateur.

## 10. Tests dès que les lunettes arrivent

Ces tests sont dans l'ordre des risques : chacun débloque le suivant, et les plus graves passent en premier. Note le résultat de chacun et colle-le dans Claude Code, il ajustera le code. Prévois environ 1 heure.

| # | Test | Ce qu'on regarde | Si ça échoue |
| --- | --- | --- | --- |
| 1 | Appairage à ton app Meta AI + mode développeur | Les lunettes apparaissent, le mode développeur est actif | Demander de l'aide au stand Meta. Sinon : démo avec le Mock Device Kit et la vidéo enregistrée (section 11) |
| 2 | L'exemple CameraAccess **non modifié** | La vidéo des lunettes s'affiche sur l'iPhone | Relire le README (versions de l'app Meta AI et du micrologiciel), redémarrer les lunettes |
| 3 | Notre app : vidéo vers la console | Les images arrivent sur les deux écrans, avec quel délai | Baisser la résolution ou le nombre d'images par seconde |
| 4 | Voix de l'app dans les lunettes | Tu entends l'IA guide dans les lunettes, pas dans le téléphone | Vérifier la sortie audio Bluetooth ; démarrer l'audio avant la caméra |
| 5 | Écoute de « yes », « no » et « emergency » par le micro des lunettes, **avec le bruit de la salle** | Taux de reconnaissance sur 10 essais | Changer de module de reconnaissance, ajouter des variantes de mots ; sur scène, le coéquipier rattrape avec les touches cachées |
| 6 | **Le test décisif** : vidéo en cours, le coéquipier clique **Answer**, l'app rejoint l'appel **LiveKit** | La vidéo continue-t-elle d'arriver pendant l'appel ? Vous entendez-vous bien, voix dans les lunettes ? Les deux enregistrements arrivent-ils dans le rapport ? | Si la vidéo se coupe : pendant l'appel, une photo toutes les 2 s à la place du flux. Si le son ne passe pas par les lunettes : revoir la session audio iOS (mode conversation, Bluetooth) |
| 7 | Le scénario complet, 3 fois de suite | Tout enchaîne, le rapport sort avec la transcription et la synthèse pour l'hôpital | Noter ce qui casse et corriger |
| 8 | Endurance | Batterie des lunettes après 20 minutes de flux, chauffe | Réduire la résolution, recharger avant la démo |

**À retenir des problèmes connus de Meta** ([source](https://wearables.developer.meta.com/docs/develop/dat/knownissues/)) :

- Après une mise à jour des lunettes, si la caméra ne marche plus : redémarrer les lunettes.
- Si tu enlèves les lunettes et les remets, les entrées peuvent cesser de marcher : il faut relancer la capacité.
- Fermer les branches arrête la session : il faut en redémarrer une.
- La reconnaissance vocale du kit s'arrête au bout d'une minute sans prévenir : la relancer régulièrement.

## 11. Risques et plans B

Le plus gros risque technique : que l'appel vocal LiveKit et le flux caméra des lunettes ne marchent pas en même temps (test 6). Chaque plan B est décidé d'avance, sans WhatsApp.

| Risque | Plan B |
| --- | --- |
| Impossible de connecter les lunettes à notre app | Mock Device Kit sur l'iPhone avec la vidéo enregistrée : tout le reste du système est identique. On le dit honnêtement au jury. En dernier recours, la vidéo de secours |
| L'appel LiveKit coupe la vidéo des lunettes | Pendant l'appel, une photo toutes les 2 s à la place du flux vidéo. Sinon, la voix de l'appel passe par le haut-parleur de l'iPhone au lieu des lunettes |
| LiveKit Cloud injoignable | Le régulateur parle quand même dans la console : ses phrases (sous-titres Chrome) s'affichent sur les deux écrans et l'Écran 2 les lit à voix haute ; le rapport utilise les sous-titres |
| La reconnaissance vocale rate sur scène | Touches cachées dans la console (1 = trigger, 2 = yes, 3 = no, 4 = next) ; gros bouton EMERGENCY sur l'iPhone |
| Le Wi-Fi bloque les connexions entre appareils | Partage de connexion de l'iPhone (prévu par défaut) |
| Modèle d'IA lent ou en panne | Changer `LLM_PROVIDER` et relancer le serveur. L'IA messager garde ses faits calculés par le code ; le rapport sort sans légendes ni résumé si les deux échouent |
| Transcription en échec | Le rapport utilise les sous-titres en direct (côté régulateur) ; deuxième fournisseur en réserve |
| Lunettes déchargées ou déconnectées pendant la démo | Vidéo de secours filmée pendant les répétitions (Écran 1 + Écran 2 côte à côte), prête à lancer |
| Retard général | Ordre de coupe de la section 8 |
| Le jury dit « ça existe déjà » ou « c'est juste un appel vidéo » | Section 12 : la chaîne complète, les 3 minutes gagnées avant la première compression, et la synthèse envoyée à l'hôpital avant l'arrivée |
| Le jury s'inquiète de la confidentialité (la conversation passe par nos serveurs) | Rien n'est enregistré hors d'une alerte déclenchée par l'utilisateur ; en vrai, le serveur serait hébergé par le centre d'urgence, qui enregistre déjà ses appels ; la synthèse ne va qu'aux secours et à l'hôpital |

## 12. Pitch : phrases clés et cadrage honnête

L'argument central : on fait gagner les minutes qui comptent, sans jamais remplacer l'humain. Il faut le dire avec des chiffres, et dire honnêtement ce qui est simulé.

**Les phrases clés**

- « Today it takes around 3 minutes before a dispatcher gets a bystander to start chest compressions. Every minute costs up to 10% survival. »
- « FirstFive starts guiding you in the first second, gives the dispatcher eyes on the scene, and hands paramedics a full report. »
- « The AI never replaces the dispatcher. It fills the gap before they pick up, writes the briefing, and goes silent the moment a human takes over. »
- « It works on any Meta AI glasses, with voice only : everyone, everyday. »

**Le cadrage honnête (à dire, pas à cacher)**

- Le 112 est **simulé** : la console est notre maquette du poste du régulateur.
- En vrai, la vidéo se brancherait sur les systèmes vidéo des centres d'urgence. Ces systèmes existent déjà au Danemark et en Norvège ; en Finlande, la loi prévoit déjà le cas.
- Les consignes de l'IA guide suivent les recommandations officielles de réanimation. Le rapport est marqué « à vérifier par les secours ».

**L'extension « niche puis tout le monde »**

1. L'arrêt cardiaque devant témoin, aujourd'hui.
2. Les autres urgences du quotidien (étouffement, convulsions, hémorragie) : même moteur, autres étapes.
3. Quand le 112 ne répond pas : catastrophes, réseau saturé, mode autonome.
4. La traduction des consignes pour les touristes et les personnes qui ne parlent pas la langue.

**Le pilote** : avec le centre d'urgence finlandais (Hätäkeskuslaitos), sur des équipes déjà équipées (sécurité, gares). On mesure le délai jusqu'à la première compression et le temps gagné par le régulateur.

**Confiance et données** : la vidéo ne part que pendant une alerte déclenchée par l'utilisateur ; pas de reconnaissance faciale ni d'analyse d'émotions ; le rapport ne va qu'aux secours.

## 13. Le message de démarrage pour Claude Code

Colle ce message dans Claude Code, puis colle tout ce document (export en Markdown) juste après, ou enregistre-le dans le dépôt sous `docs/PLAN.md` et dis-lui de le lire. Il travaillera phase par phase.

```text
You are my senior engineer for a hackathon (Junction 2026, Meta AI glasses track).
Submission is ~07:00 Helsinki time tomorrow; the demo must work reliably. Read docs/PLAN.md fully
before writing code: it is the source of truth (product, demo script, architecture, message protocol,
component specs, phases, tests, fallbacks).

Project: FirstFive. A witness says "Emergency" to an iPhone app connected to Meta Ray-Ban glasses.
An "AI guide" (fixed state machine, iOS TTS + speech recognition of yes/no) coaches first actions
(responsive? breathing? CPR with a 110 bpm metronome). In parallel an "AI messenger" builds a written
briefing card for a simulated 112 dispatcher console (facts computed by code + one AI scene line).
The glasses camera frames (JPEG, ~3 fps) stream via WebSocket to a FastAPI server on my Mac, which
rebroadcasts them to web pages: console (operator/viewer modes) and a "caller view" screen.
When the dispatcher clicks Answer, the AI guide goes silent and both join a LiveKit room (LiveKit
Cloud; server issues tokens): real two-way voice, glasses mic and speaker on the caller side, while
the video keeps streaming. The console records both audio tracks (MediaRecorder) and uploads them
on End. The server transcribes them (timestamped segments), merges a dialogue, then builds a report
page: metrics computed by code, timeline, key frames, AI summary and captions, and a MIST hospital
handover built only from what was said or seen, each item with its source timestamp.
Hidden keyboard overrides exist for the demo.

Rules:
- Work in the phases of PLAN.md section 8, in order. After each phase, stop and tell me exactly how
  to run and verify it (the "done when" criterion). Do not start the next phase until I confirm.
- Phases 1-3 must run without iPhone or glasses, using server/sim_app.py, a sample.mp4 and the
  /test-caller page.
- Keep it simple: Python FastAPI + plain HTML/JS (no build step). iOS: start from Meta's official
  CameraAccess sample (meta-wearables-dat-ios), Xcode 26.4+, iOS 17.2+, plus the LiveKit Swift SDK.
- The AI model is pluggable: server/llm.py with Anthropic Claude and Google Gemini implementations,
  chosen by LLM_PROVIDER in .env. Check current model ids in the provider docs; do not guess them.
- Never let the model produce facts or numbers; it only describes images and writes summaries.
  Every model or transcription call has a timeout and a fallback.
- Server URL is configurable in the iOS app (no rebuild when the IP changes).
- Before any iOS work, check the DAT docs (https://wearables.developer.meta.com/docs/develop/ and the
  repo's AGENTS.md) for the exact APIs; start Bluetooth HFP audio before the camera stream.
- No WhatsApp anywhere.

Start with phase 0, then phase 1.
```

**Bon à savoir** : le kit Meta propose un serveur de documentation que Claude Code peut interroger directement, `https://mcp.developer.meta.com/wearables` ([dépôt du kit](https://www.gitlink.org.cn/mirrors/meta-wearables-dat-ios)). Ajoute-le à Claude Code avant la phase 3 : il lira la doc à jour au lieu de deviner les API.
