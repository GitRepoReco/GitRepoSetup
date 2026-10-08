# Dossier de sauvegarde / restauration automatique

Déposez dans ce dossier vos fichiers de sauvegarde `.sql` ou `.dump` issus de l'ancien système (ex: `legacy_github_data.sql`).

Au démarrage du conteneur `gitreporeco-init` :
- Si la base de données est vide, le script détectera automatiquement les fichiers `.sql` présents dans ce dossier et les appliquera pour restaurer vos dépôts, snapshots et readmes existants.

