# FirstFive

**Reprise de conversation : lire [la passation détaillée](docs/HANDOFF.md).** Elle décrit l’état réel des lunettes, les tests effectués et la configuration LiveKit `.env` encore à terminer sur le Mac. Pour la démo : [réponses manuelles](docs/DEMO_MANUELLE.md).

Prototype Junction : un témoin déclenche une alerte, un guide fixe pose deux questions, une console reçoit la vidéo et les faits, puis un régulateur prend le relais par LiveKit. Le rapport conserve chronologie, images, dialogue et transmission MIST.

**Démonstration uniquement.** Aucun appel au vrai 112 et aucun envoi à un hôpital. Répéter avec des participants consentants et un coussin/mannequin. Le temps affiché est le démarrage du **guidage**, pas une compression mesurée.

## Démarrer sans lunettes ni clés

Python 3.11+ (validé ici avec 3.12). Depuis la racine du dépôt :

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.lock
cp .env.example .env  # seulement si .env n'existe pas déjà
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

Sur le Mac, ouvrir les chemins suivants à l'adresse du serveur :

| Chemin | Usage |
| --- | --- |
| `/console?mode=operator` | Régulateur : décrocher, micro, captions, terminer |
| `/console?mode=viewer` | Projection sans commandes ni micro |
| `/caller` | Écran projeté du témoin |
| `/test-caller` | Remplace l'iPhone : bouton Emergency, oui/non, voix, caméra |
| `/report/{id}` | Rapport imprimable |
| `/health` | État et présence des intégrations, sans exposer les clés |

Option terminal, dans une seconde fenêtre :

```sh
.venv/bin/python -m server.sim_app --auto-pickup
# Générer un MP4 synthétique pour OpenCV ou le Mock Device Kit :
.venv/bin/python scripts/make_sample.py
# Vidéo de répétition consentie ; sinon images synthétiques clairement marquées.
.venv/bin/python -m server.sim_app --video sample.mp4 --auto-pickup
# Échantillons audio facultatifs, offset de début du décroché dans ce scénario :
.venv/bin/python -m server.sim_app --auto-pickup --caller-audio caller.webm --dispatcher-audio dispatcher.webm
```

N'utiliser qu'un producteur `/ws/app` à la fois : simulateur Python, page test-caller **ou** iPhone. Les consoles peuvent être multiples. Un seul opérateur doit piloter et enregistrer la démo.

Sur la page test-caller : Emergency → No → No ; sur la console : Answer → parler ou saisir une caption → End. Les permissions de micro/caméra nécessitent **localhost ou HTTPS avec certificat approuvé**. Un simple `http://IP-du-Mac` ne suffit pas pour le micro de l'ordinateur du régulateur ou du téléphone. Utiliser HTTPS local approuvé sur les appareils, ou faire tourner/projeter les deux navigateurs sur le Mac pour la première répétition. Ne pas désactiver les vérifications TLS. Le partage de connexion doit permettre les flux LiveKit.

Touches opérateur : `1` déclencher, `2` oui, `3` non, `4` répéter la consigne, `0` réinitialiser. `4` ne fabrique jamais une réponse médicale pour forcer une étape.

## Voix réelle avant les lunettes

Dans `.env`, renseigner `LIVEKIT_URL` (`wss://...`), `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`, puis redémarrer le serveur. Ces valeurs restent côté serveur ; seuls des jetons de salle valables 30 minutes sont transmis aux clients. Tester `/test-caller` + console avec casques. Answer active le micro et l'enregistrement ; End téléverse les deux pistes avant de lancer le rapport. Une erreur d'envoi permet de réessayer End sans jeter les enregistrements.

Un LiveKit **local** est également utilisable sans compte pour la répétition sur une seule machine :

```sh
python3 scripts/install_livekit.py
.tools/livekit-server --dev --bind 127.0.0.1 --node-ip 127.0.0.1 --rtc.enable_loopback_candidate
```

Dans un autre terminal :

```sh
LIVEKIT_URL=ws://127.0.0.1:7880 LIVEKIT_API_KEY=devkey LIVEKIT_API_SECRET=secret \
  .venv/bin/uvicorn server.main:app --host 127.0.0.1 --port 8001
```

Ces identifiants sont les **valeurs publiques du mode développement** de LiveKit, uniquement sur loopback. Utiliser les vraies clés LiveKit Cloud pour les appareils en réseau. Le mode local a été testé sous Linux avec Chromium et des micros synthétiques ; l'écoute humaine reste à vérifier.

## IA et transcription facultatives

- `LLM_PROVIDER=anthropic` avec `ANTHROPIC_API_KEY`, ou `LLM_PROVIDER=gemini` avec `GEMINI_API_KEY`.
- `LLM_MODEL` doit être un identifiant exact disponible dans **votre** console fournisseur. Aucun modèle supposé n'est codé en dur.
- `OPENAI_API_KEY` active la transcription horodatée ; `TRANSCRIPTION_MODEL=whisper-1` utilise `verbose_json` + segments.
- Sans clés ou en cas d'erreur : faits déterministes, chronologie, images et captions sont conservés. Une transcription manquante n'est jamais inventée.
- Ligne visuelle : timeout 5 s ; rapport : 20 s ; transcription : 40 s par requête, avec un budget global de 50 s et deux requêtes simultanées. Le modèle reçoit des images/données uniquement après une alerte. Une synthèse IA est un brouillon à vérifier contre les sources, pas une observation médicale validée.

Destinations réseau utiles : `api.anthropic.com`, `generativelanguage.googleapis.com`, `api.openai.com`, votre domaine LiveKit et ses destinations WebRTC/TURN. Ici les appels payants n'ont **pas** été exécutés : leurs SDK sont testés avec réponses HTTP simulées. Configurer les valeurs dans `.env` local ou les paramètres sécurisés de l'environnement, jamais dans Git ou dans le chat.

## iPhone / Meta

Voir [ios/README.md](ios/README.md). `ios/prepare.py` génère CameraAccess officiel à une révision précise, conserve son appairage et Mock Device Kit, puis ajoute le panneau FirstFive, WebSocket, JPEG, parole/écoute et LiveKit.

```sh
python3 ios/prepare.py
open ios/CameraAccess/CameraAccess.xcodeproj
```

Le premier projet a été compilé et lancé par l’utilisateur sur son iPhone avec Xcode 27.2. Les correctifs Swift ajoutés depuis doivent être recompilés sur ce Mac. Le routage Bluetooth et la caméra réelle restent à tester avec les lunettes.

## Vérifications

```sh
.venv/bin/pytest -q
# Facultatif pour les tests de navigateur :
.venv/bin/pip install -r requirements-dev.txt
# Installer Chromium via Playwright si aucun navigateur système disponible :
.venv/bin/playwright install chromium
CHROMIUM_PATH=/chemin/vers/chromium .venv/bin/python tests/browser_smoke.py
# Avec les deux serveurs LiveKit/FastAPI locaux décrits plus haut :
CHROMIUM_PATH=/chemin/vers/chromium .venv/bin/python tests/browser_voice.py
```

Les tests utilisent `/usr/bin/chromium` par défaut ; `FIRSTFIVE_TEST_URL` permet de changer le serveur. Chaque test navigateur réinitialise **le serveur de démo choisi**, ne pas le lancer pendant une intervention à conserver. [Résultats et limites](docs/VALIDATION.md).

## Architecture et données

- Un processus FastAPI, une intervention courante, WebSockets JSON + JPEG limités à 3/s et 2 MB/image ; données dans `data/<id>/`.
- Le serveur fait autorité sur l'étape et les heures. iPhone/navigateur parlent les messages reçus. Cette centralisation évite une double progression et permet les overrides ; **le guidage autonome hors connexion n'est pas implémenté**. La perte du serveur arrête le guide et est affichée.
- Aucune image n'est persistée avant l'alerte ou après End. JPEG vérifiés, images clés bornées, enregistrements limités à 24 MB/piste. Les rapports antérieurs restent consultables après redémarrage ; une intervention interrompue n'est pas reprise automatiquement.
- Les deux pistes ont chacune leur offset relatif à l'alerte ; les segments sont fusionnés chronologiquement. Les captions sont un repli uniquement pour les pistes sans transcription réussie.
- Guide et métronome s'arrêtent au décroché ; caméra continue. « Oui » termine le questionnement automatique. Reconnaissance anglaise ; boutons de secours toujours accessibles.
- Le mode viewer est en lecture seule au niveau du protocole, mais ce prototype n'a pas d'identités opérateur indépendantes. Sur un réseau partagé, définir `FIRSTFIVE_ACCESS_KEY` ; ouvrir une fois `/?key=...` pour le cookie HTTP-only, puis naviguer normalement. iPhone/simulateur utilisent `X-FirstFive-Key`. Ne pas exposer ce prototype sur Internet.
- Les fichiers sont locaux et exclus de Git ; pas de suppression automatique. Effacer les dossiers de session après la répétition selon le consentement obtenu. Aucun mécanisme d'envoi aux hôpitaux n'est présent.

Le guide fourni est conservé comme [référence produit](docs/REFERENCE.md). Le présent README décrit le comportement implémenté, notamment les différences explicites ci-dessus.

## Mise à jour après installation sur Mac

Voir [la mise à jour 02](docs/UPDATE_02.md) pour conserver la signature Xcode, les clés et les données. Les enregistrements supportent plusieurs segments par interlocuteur après reconnexion, avec offsets distincts et reprise des téléversements.
