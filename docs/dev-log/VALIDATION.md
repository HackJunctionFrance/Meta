# Validation effectuée

Exécution dans le cloud Linux, le 14 novembre 2026. Python 3.12, Chromium système, SDK LiveKit JS 2.24.1 et serveur local LiveKit 1.13.11 vérifié par SHA256.

| Contrôle | Résultat |
| --- | --- |
| Suite Python | 29 tests réussis lors de la passation finale : 26 existants + 3 tests de configuration LiveKit |
| Scénario serveur | Alerte, réponses, guidage, décroché, captions, fin, rapport persistant |
| Branches / erreurs | Oui à chaque question, réponse hors ordre/après décroché, commandes viewer refusées, JSON invalide, coordonnées invalides, double producteur refusé |
| Images | JPEG valide/invalide, diffusion, image clé, réaffichage à la reconnexion, remise à zéro |
| Sécurité de base | Clé d'accès, refus origine WebSocket externe, échappement HTML du rapport, paramètres d'upload |
| Reprise | Session/prompt récupérés après reconnexion app ; rapports lisibles après nouveau processus |
| Fournisseurs IA/STT | SDK officiels Anthropic, Gemini et OpenAI exercés avec réponses HTTP simulées ; offsets et références de sources vérifiés |
| Parcours Chromium | Trois pages, vidéo synthétique visible, réponses, passage de relais, captions manuelles, reload viewer, rapport et reset ; aucune exception JavaScript |
| Voix réelle locale | Deux répétitions consécutives : deux pistes WebRTC LiveKit bidirectionnelles avec micros Chromium synthétiques ; deux enregistrements MediaRecorder > 1 KB, offsets, upload, rapport sans transcription configurée |
| Simulateur Python | Scénario auto complet avec images synthétiques et avec MP4 généré ; rapport obtenu |
| iOS / lunettes | Build et lancement utilisateur confirmés ; vraie vidéo lunettes → iPhone → Mac confirmée ; guidage manuel confirmé. Reconnaissance vocale non validée et LiveKit Cloud restant à configurer |
| Dépendances / syntaxe | pip check, Ruff et node --check réussis |

## Ce qui n'a pas été validé

- Aucune requête payante réelle aux modèles ou au service de transcription ; aucun modèle choisi à la place de l'utilisateur. La qualité de la synthèse et de la transcription doit être évaluée avec les clés et de la parole humaine.
- LiveKit Cloud et le réseau entre appareils/hotspot ; la validation LiveKit est locale. Le test confirme des pistes WebRTC et des fichiers audio, pas leur intelligibilité pour un humain.
- Reconnaissance vocale Chrome réelle : test des captions par saisie et du repli ; le service Speech de Chrome dépend du navigateur, du micro et de sa connexion.
- Aucun build Xcode dans le cloud Linux. Les builds et le flux réel ont été confirmés par l’utilisateur sur son Mac/iPhone (voir HANDOFF.md). La compilation précise du correctif 04 et la résolution matérielle du crash n’ont pas de validation reproductible ici. Reconnaissance vocale, route audio Bluetooth/LiveKit, caméra + HFP simultanés, GPS et batterie réels restent à vérifier ou implémenter.
- Pas de validation clinique des consignes. Pas d'intégration avec le vrai 112 ou un hôpital. Les métriques ne mesurent pas des compressions physiques.

## Limites connues

Une seule session courante et un seul processus serveur. Pas de guide autonome hors réseau. Une reconnexion vocale conserve désormais plusieurs segments horodatés par interlocuteur. Le rechargement de la page appelant pendant un appel a été testé avec deux segments audio caller conservés dans le rapport. Un rechargement de la page opérateur perd ses enregistrements non téléversés : ne pas recharger pendant l'appel. End termine l'envoi avant la génération du rapport ; Reset annule la session et jette l'audio encore en mémoire du navigateur.

Les rapports sont des brouillons à vérifier. Le filtrage des références de source n'est pas une garantie sémantique contre une hallucination du modèle ; conserver les événements, les images et la transcription comme preuves primaires.

## Retour appareil et mise à jour 02

Le premier projet a été compilé et lancé par l’utilisateur sur son iPhone avec Xcode 27.2 ; le Mock Device Kit a ensuite été configuré. Cela valide le premier build et le lancement, pas encore l’appel complet avec les lunettes. Le correctif Swift plus récent est généré mais reste à compiler sur Mac. Les lignes iOS ci-dessus décrivent les contrôles réalisés dans le cloud, pas cette confirmation utilisateur. Voir UPDATE_02.md.

## Dernière passation — 14 novembre 2026

- 29 tests Python : PASS (3,63 s). Ruff : PASS. `pip check` : aucune dépendance cassée. Syntaxe JS et shell : PASS.
- Génération du projet aux pins Meta/LiveKit : PASS. Cela ne constitue pas un build iOS.
- Update 03 testée sur l’archive initiale : sauvegarde et préservation de la signature et de `.env`, puis confirmation utilisateur de la vraie caméra.
- Update 04 : installation cumulative et correspondance des sources générées vérifiées ; diagnostic du crash par backtrace utilisateur. Reconnaissance vocale humaine toujours non validée.
- Démo manuelle dans Chromium : commandes opérateur No/No, vidéo synthétique, passage de relais, captions, rapport et reset ; zéro exception JS. L’utilisateur a confirmé le parcours avec la vraie vidéo.
- Installation `.env` : tests de préservation des autres valeurs, remplacement des doublons, sauvegarde, permissions 0600, refus d’injection de ligne et de symlink. Le redémarrage automatisé macOS reste à exécuter sur le Mac.
- Tentative API LiveKit Cloud en lecture seule : échec de résolution DNS depuis le cloud ; aucune conclusion sur la validité des clés. Le `.env` du Mac n’a pas été modifié à distance.

Les premiers paragraphes historiques décrivent les étapes antérieures. La référence actuelle complète est [HANDOFF.md](HANDOFF.md).
