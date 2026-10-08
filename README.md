# GitRepoReco

Plateforme de recommandation de dépôts GitHub (GitRepoReco). Ce projet orchestre la collecte de données (`Analyse-github`), l'initialisation centralisée de la base de données PostgreSQL (avec support vectoriel `pgvector`), et fournit un environnement réseau prêt à accueillir de nouveaux microservices / conteneurs (moteur de recommandation, API, interface utilisateur, etc.).

---

## Architecture globale

```
                                  [ Réseau Docker : gitreporeco-net ]
                                                  │
                 ┌────────────────────────────────┼────────────────────────────────┐
                 │                                │                                │
                 ▼                                ▼                                ▼
       ┌───────────────────┐            ┌───────────────────┐            ┌───────────────────┐
       │     postgres      │            │  gitreporeco-init │            │   analyse-github  │
       │  (PostgreSQL 16   │ ◄───────── │   (Initialisation │            │    (Collecteur    │
       │   + pgvector)     │            │    schémas/tables)│            │      GitHub)      │
       └───────────────────┘            └───────────────────┘            └───────────────────┘
                 ▲                                │                                │
                 │                                │                                │
                 │ 1. Démarre & healthy           │ 2. Exécute SQL & s'arrête (0)  │ 3. Démarre
                 │                                │                                │
                 └────────────────────────────────┴────────────────────────────────┘
                                                  │
                                                  ▼
                                     ┌─────────────────────────┐
                                     │    Futurs conteneurs    │
                                     │  (ex: Reco API, ML, UI) │
                                     └─────────────────────────┘
```

---

## Structure de la base de données

L'initialisation crée automatiquement les extensions et schémas suivants :

1. **Extensions PostgreSQL** :
   - `uuid-ossp` : Génération d'identifiants uniques UUID.
   - `pg_trgm` : Recherche floue et similarité textuelle sur les noms de dépôts et topics.
   - `vector` : Support des vecteurs et embeddings (`pgvector`) pour les modèles de recommandation.

2. **Schéma `github`** (utilisé par `Analyse-github`) :
   - `repositories` : Informations complètes sur les dépôts collectés (stars, forks, langage, topics, etc.).
   - `readmes` : Contenu des README versionnés par commit.
   - `repository_snapshots` : Suivi temporel de l'évolution des métriques de chaque dépôt.
   - `collection_progress` : Reprise sur panne et pagination de l'historique de collecte.

3. **Schéma `monitoring`** :
   - `rate_limit_usage` : Suivi de la consommation des quotas GraphQL GitHub.

4. **Schéma `recommendation`** (préparé pour les futurs services) :
   - `repo_features` : Features calculées (scores de popularité, activité, mots-clés normalisés).
   - `repo_embeddings` : Embeddings vectoriels (JSONB et type natif `vector`).
   - `repo_similarities` : Graphe des similarités entre dépôts.
   - `recommendation_cache` : Cache des requêtes et recommandations.

5. **Utilisateurs et sécurité (Moindre Privilège)** :
   - **`postgres`** (administrateur) : Utilisé uniquement par `gitreporeco-init` pour créer les schémas, tables, extensions et rôles.
   - Les rôles applicatifs sont initialisés par des scripts Python versionnés dans `app/init-users/` (fonction `apply(conn)` obligatoire).
   - **`github_collector`** (utilisateur applicatif pour `Analyse-github`) :
     - ✅ Droits de lecture/écriture DML (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) sur le schéma `github`.
     - ✅ Droits d'écriture/lecture sur le schéma `monitoring`.
     - ✅ Droits `USAGE` sur les séquences d'auto-incrémentation.
     - ❌ **Aucun droit DDL** (`CREATE TABLE`, `ALTER`, `DROP`).
     - ❌ **Aucun accès** au schéma `recommendation` ni au schéma `public`.

---

## Démarrage rapide

### 1. Configuration

Copiez le fichier d'exemple et renseignez votre token GitHub :

```bash
cp .env.example .env
```

Dans `.env` :
```env
GITHUB_TOKEN=ghp_votre_token_ici
```

### 2. Lancement des conteneurs

```bash
docker compose up --build
```

**Ce qui se produit :**
1. Le conteneur `postgres` démarre et effectue ses vérifications d'état (`healthcheck`).
2. Dès que PostgreSQL est prêt, `gitreporeco-init` démarre, applique les scripts SQL dans `init-scripts/`, puis les scripts utilisateurs Python dans `init-users/`, valide les tables créées, puis se termine avec succès.
3. `analyse-github` démarre et lance la collecte des dépôts GitHub.

Pour lancer en arrière-plan :

```bash
docker compose up --build -d
```

Pour voir les logs d'un conteneur en particulier :

```bash
docker compose logs -f gitreporeco-init
docker compose logs -f analyse-github
```

### 3. Ajouter un utilisateur PostgreSQL via script Python

Créez un fichier dans `app/init-users/` (ordre d'exécution alphanumérique) avec une fonction `apply(conn)`.

Le projet inclut déjà :
- `00_postgres_admin.py` pour l'admin PostgreSQL (`POSTGRES_USER`)
- `10_collector_user.py` pour le rôle applicatif collector
- `_role_utils.py` pour mutualiser la création de rôles et l'attribution des droits
  - `grant_schema_read_only(...)` : lecture seule sur un schéma
  - `grant_schema_read_insert(...)` : lecture + ajout (sans update/delete)
  - `grant_schema_dml(...)` : lecture + ajout + update + suppression

Exemple minimal :

```python
from psycopg2 import sql

def apply(conn):
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("CREATE ROLE {role} WITH LOGIN PASSWORD {pwd};").format(
                role=sql.Identifier("my_app_user"),
                pwd=sql.Literal("change_me"),
            )
        )
```

Règles importantes :
- `gitreporeco-init` s'exécute avec le compte admin PostgreSQL.
- Les tables/schémas sont créés par l'admin au bootstrap.
- Les utilisateurs applicatifs reçoivent ensuite uniquement les droits nécessaires (principe du moindre privilège).
- En cas d'erreur sur un script utilisateur, l'initialisation échoue immédiatement et la transaction est annulée.

---

## Comment greffer un nouveau conteneur au projet

Tous les conteneurs partagent le réseau Docker `gitreporeco-net`.

### Option A : Ajouter un service directement dans `docker-compose.yml`

Exemple pour ajouter une API de recommandation (ex: FastAPI ou Flask) :

```yaml
  reco-api:
    build:
      context: ./reco-api
    container_name: gitreporeco_api
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      gitreporeco-init:
        condition: service_completed_successfully
    environment:
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_DB: ${POSTGRES_DB:-github_data}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
    ports:
      - "8000:8000"
    networks:
      - gitreporeco-net
```

### Option B : Lancer un conteneur indépendant ou depuis un autre projet

Depuis la ligne de commande, il suffit de le rattacher au réseau `gitreporeco-net` :

```bash
docker run -d \
  --name mon_service \
  --network gitreporeco-net \
  -e POSTGRES_HOST=postgres \
  -e POSTGRES_DB=github_data \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  mon_image:latest
```

Ou dans un `docker-compose.yml` externe :

```yaml
services:
  mon-service:
    image: mon_image:latest
    networks:
      - gitreporeco-net

networks:
  gitreporeco-net:
    external: true
```

---

## Migration depuis l'ancien système (Analyse-github)

`GitRepoReco` prend en charge la migration de vos données et de vos schémas existants de trois manières complémentaires :

### 1. Réutilisation directe de l'ancien volume Docker (Recommandé)
Si vous utilisiez déjà `docker compose` dans le sous-dossier `Analyse-github`, vos données sont stockées dans le volume Docker nommé `analyse-github_postgres_data`.

Pour le réutiliser sans rien recopier, modifiez simplement votre fichier `.env` à la racine :
```env
POSTGRES_DATA_VOLUME=analyse-github_postgres_data
```
Au démarrage, `gitreporeco-init` détectera la base existante, appliquera automatiquement les migrations de schéma (mise à niveau de `collection_progress`, déplacement éventuel de tables depuis `public`, resynchronisation des séquences), activera les extensions vectorielles et configurera le nouvel utilisateur `github_collector`.

### 2. Restauration automatique d'un dump SQL
Si vous possédez un export ou une sauvegarde `.sql` de votre base :
1. Placez votre fichier (ex: `ancien_dump.sql`) dans le dossier `backups/`.
2. Lancez `docker compose up --build`.
3. Si la base est neuve, `gitreporeco-init` importera automatiquement vos données et appliquera toutes les migrations et permissions.

### 3. Migration réseau depuis une ancienne base active
Si votre ancienne base de données tourne sur une autre machine ou un autre port :
Dans `.env` :
```env
MIGRATE_FROM_OLD_DB=true
OLD_POSTGRES_HOST=192.168.1.50 # ou localhost
OLD_POSTGRES_PORT=5432
OLD_POSTGRES_DB=github_data
OLD_POSTGRES_USER=postgres
OLD_POSTGRES_PASSWORD=postgres
```
Au démarrage, `gitreporeco-init` copiera l'intégralité des tables (`repositories`, `readmes`, `repository_snapshots`, `collection_progress`, `rate_limit_usage`) en streaming direct vers la nouvelle base.

### 4. Mises à niveau automatiques du schéma (`04_migrations_legacy.sql`)
Même avec une base historique, `gitreporeco-init` effectue automatiquement :
- Le déplacement des tables historiques créées dans `public` vers `github` et `monitoring`.
- L'ajout des colonnes dynamiques de pagination (`segment_key`, `date_low`, `date_high`).
- La suppression de l'ancienne contrainte d'unicité et le dédoublonnage propre des lignes.
- La resynchronisation de toutes les séquences (`id_seq`) pour éviter les conflits lors des futures insertions de `Analyse-github`.
- L'attribution des droits d'accès à l'utilisateur applicatif `github_collector`.
- L'enregistrement dans la table de suivi `monitoring.schema_migrations`.
