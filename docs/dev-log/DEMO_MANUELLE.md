# Démo FirstFive avec réponses pilotées manuellement

La vidéo vient des vraies lunettes. Le guide suit le script existant. Un coéquipier saisit les réponses entendues au lieu de la reconnaissance vocale. Présenter ce mode comme « vidéo réelle, réponses pilotées manuellement pour la démo ».

## Préparation
- Fermer complètement puis rouvrir CameraAccess pour repartir sans écoute vocale. Ne pas toucher Enable voice.
- Dans FirstFive, Connect au serveur, puis Reset. Relancer la session et la caméra des vraies lunettes.
- Sur le Mac : http://localhost:8000/console?mode=operator. Ouvrir Rehearsal controls tout en bas.
- Pour une projection séparée : http://localhost:8000/console?mode=viewer (pas de commandes opérateur).

## Scène de 60 à 90 secondes
1. Le témoin appuie sur EMERGENCY sur l’iPhone. Alternative : le coéquipier clique 1 · Trigger sur le Mac.
2. Attendre la fin de « Is he responding? ». Le témoin dit « No » ; le coéquipier clique une fois 3 · No.
3. Attendre la fin de « Is he breathing normally? ». Le témoin dit « No » ; le coéquipier clique une fois 3 · No.
4. Le guide et le métronome démarrent. Montrer la vraie vidéo et les deux faits remontés dans le briefing. Pour montrer les gestes, utiliser un mannequin.
5. Si l’on montre la prise en charge : cliquer Answer call seulement à ce moment. Cela arrête le guide. Sans LiveKit, aucun appel audio opérateur n’est établi ; le bandeau l’indique. Un texte saisi dans Manual dispatcher caption puis Send caption apparaît dans les vues.
6. Après Answer call, cliquer End & prepare report, puis Open incident report. Vérifier le compte rendu comme un brouillon de simulation.
7. Pour recommencer : 0 · Reset. Le flux caméra peut rester actif.

## Commandes
- 2 · Yes : réponse positive à la question courante ; mène à la consigne de surveillance.
- 3 · No : réponse négative à la question courante ; attendre la nouvelle question avant le second clic.
- 4 · Repeat prompt : répète la question ou consigne actuelle.
- 0 · Reset : annule la simulation courante.

Ces commandes existent déjà dans la première version : aucune installation supplémentaire n’est nécessaire. Les boutons Yes / No dans le panneau iPhone ont le même effet.
