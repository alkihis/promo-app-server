# promo-app-server

## Introduction

Partie serveur du projet à destination du suivi des étudiants des promos du master bio-informatique de Lyon.

Cette documentation expliquera:
- Quelles technologies ont été utilisées dans ce projet
- Comment configurer le projet depuis un clone git
- Comment lancer le serveur de manière autonome
- Quelle est l'architechture du projet (organisation & fonctionnement)
- Comment créer une nouvelle vue
- Comment créer un nouveau fichier contenant des vues
- Quels outils sont disponibles via la ligne de commande sur ce serveur

Ce serveur est conçu pour répondre à des requêtes dans un modèle client serveur reposant sur une API: Il servira un client statique (renvoyant son index.html dans tous les cas sans traitement) et ses routes seront des vues commençant par `/api/`. Le format de retour (et d'entrée) des requêtes est `JSON`.

## Technologies

Ce serveur est développé dans le langage Python. La version **3.6** est requise au minimum (utilisation des f-string).

### Flask

L'utilisation du framework [Flask](https://flask.palletsprojects.com/en/1.1.x/) a été choisie pour sa simplicité d'utilisation.

Le serveur Flask est défini dans le fichier `./src/server.py`.

Les vues liées au serveur Flask sont dans `./src/Vues/`.
Celles-ci sont déclarées pour être liées au serveur Flask dans le fichier `./src/modules_main.py` (plus d'informations dans *Comment ajouter une vue*).

### SQLAlchemy

[SQLAlchemy](https://www.sqlalchemy.org/) est un ORM autour de base SQL-compatible (ici, SQLite). Il permet de définir des modèles (mappant des entités dans des tables) pouvant être en relation avec d'autres modèles. Ces modèles sont définis dans `./src/Models/`.

**Le fichier `db.db` sera utilisé en tant que base de données**.

## Premier démarrage

La première opération sera de cloner le dépôt git.

Ensuite, lancer la création de l'environnement virtuel via la commande, puis entrez dedans:
```bash
./deploy.sh
source .envs/bin/activate
```

### Configuration des identifiants Gmail

Le serveur doit comporter un fichier `credentials.json` à la racine du projet contenant les clés d'accès à l'application Gmail lié au compte duquel vous souhaitez envoyer des e-mails.

Ce fichier peut être obtenu depuis le tableau de bord API Google.

Une fois ce fichier présent, au premier démarrage, vous devez accepter par votre navigateur web l'accès à votre compte Gmail par l'application. L'accès autorisé, un fichier `gmail_token.pickle` sera créé.

**Attention**: Si l'ordinateur utilisé n'a pas d'interface graphique, vous devez générer ce fichier `.pickle` sur un autre ordinateur avec les mêmes clés d'accès et sur le même compte Gmail, puis insérer ce fichier dans le dossier du projet.

### Configuration du mot de passe enseignant

Les enseignants partagent un mot de passe pour se connecter à la plateforme. Vous **devez** l'initialiser avec `python src/app.py --password`. Un fichier `settings.json` contenant le mot de passe hashé en bcrypt sera généré.

### Si vous n'avez pas de base de données
Vous devez initialiser la base de données avec la commande `--init`.

Les tables seront créées en lien avec les modèles importés dans `./src/server.py`.

```bash
python src/app.py --init
```

### Pour importer des données de l'ancienne base
La base de données doit être initialisée.

Si vous souhaitez importer une base de données antérieure (= de l'ancien projet de suivi des étudiants), vous pouvez utiliser la commande `--upgrade <old-db>`.
```bash
python src/app.py --upgrade old.db
```

## Utilisation

Pour lancer le serveur de développement, utilisez cette commande.
```bash
source .envs/bin/activate
python src/app.py --debug
```

## Fonctionnement

Le serveur repose sur un modèle client-server par API dont les requêtes et réponses doivent/sont formatées en JSON.

### Authentification

L'authentification des utilisateurs s'effectue par des tokens situés dans la table `Token` de la base de données. Ces tokens sont une chaîne de caractères aléatoire de la norme `uuid-v4`. Dans la table `Token`, il est indiqué sur le token est lié à un étudiant (et si oui lequel) ou un enseignant.

Pour chaque requête, le token doit être joint dans le header HTTP `Authorization` sous la forme `Bearer <token>`.

### Vues

Les vues sont à déclarer dans un fichier du dossier `./src/Vues/`.
Il est préférable de regrouper ses vues par catégories (étudiant, emploi, authentification...) et de créer un fichier par catégorie.

Lors de la création d'un nouveau fichier de vue, toutes les déclarations de routes doivent être faites dans une **fonction qui prend l'application Flask en paramètre**. Les vues ne doivent **pas** importer `app` !

```py
# Ma fonction englobant mes routes et recevant app
def define_my_category_routes(app: flask.Blueprint):

  # Déclaration d'une route...
  # Le préfixe ne contient pas /api !
  @app.route('/category/create', methods=["POST"])
  def make_emploi():
```

Ce nouveau fichier doit être importé à la suite des autres dans le fichier de déclaration des vues `./src/modules_main.py`.

```py
...
# Les anciennes déclarations
from Vues.ask_creation import define_ask_creation_routes
define_ask_creation_routes(bp)


## Mon nouveau fichier de vues !
# L'import doit être réalisé ici, pas avant
from Vues.my_category import define_my_category_routes
# On définit les vues
define_my_category_routes(bp)


# !! Bien laisser cette ligne APRÈS les définitions !!
app.register_blueprint(bp, url_prefix='/api')
```

### Erreurs

Les erreurs sont définies dans le fichier `./src/errors.py`. Il expose une variable `ERRORS` pouvant être utilisée pour générer une erreur au format JSON renvoyable par flask.

```py
from errors import ERRORS

my_error = ERRORS.PAGE_NOT_FOUND
# my_error => (flask.Response, 404)

# Dans une vue..
return ERRORS.INVALID_INPUT_TYPE
```

Une erreur se compose d'un code (numérique), d'un message et d'un code HTTP lié.

Le code numérique est lié à une constante textuelle en Python (comme `PAGE_NOT_FOUND` ou `SERVER_ERROR`).

La définition des erreurs se fait dans `./src/errors.py`, dans la classe `Errors`.
 
`self.codes` lie code numérique d'erreur à un tuple `(message, code HTTP)`. `self.relations` définit les macros textuelles liées aux codes définis dans `self.codes`.


Vous pouvez ajouter des données supplémentaires à une erreur en appelant `.error()`.
```py
return ERRORS.error("SERVER_ERROR", {'detail': 'SQL request failed'})
```

### Constantes et accès à Gmail

Les constantes se trouvent dans `./src/const.py`.
Les constantes liées à l'utilisation de Gmail (service, user) sont situées dans `./src/gmail.py`.

### Fonctions d'aide

Les fonctions d'aide sont réparties dans deux fichiers: `./src/helpers.py` qui regroupent des fonctions qui n'ont pas accès aux entités SQL et `./src/models_helpers.py` regroupant toutes les fonctions y ayant accès.

### Structure des fichiers d'entrée

Le fichier `./src/app.py` est le point d'entrée: il prend en charge les arguments en ligne de commande et lance le serveur Flask à la fin du fichier.

`./src/modules_main.py` est le fichier de déclaration des vues.

`./src/server.py` définit le serveur Flask et la connexion à la base de données. Il lit les modèles définis par l'utilisateur, lie Flask à l'ORM et exporte `db_session`, une variable permettant de **commit** ou **rollback** les changements faits dans la BDD.


Enfin, `./src/login_handler.py` définit ce qui est nécessaire pour que le module flask_login authentifie les utilisateurs via le header HTTP `Authorization`.

## Création d'une vue

Pour créer une vue, nous utilisons les outils mis à disposition par flask.
La vue doit être déclarée dans une fonction recevant `app` en paramètre, tel vu dans *Vues*.

Ne préfixez pas l'URL de la route par `/api`, cela sera fait automatiquement.

```py
@app.route('/teacher/home')
@login_required  # Connexion requise pour accéder
@teacher_login_required  # Connexion enseignante requise
def teacher_home():
  # Traitements...
```

Pour aider le traitement dans votre vue, voici quelques fonctions/variables utiles à importer:

- `get_student_or_none` de `models_helpers`: Récupère l'étudiant lié à la requête.

  Un étudiant est lié à la requête si :
  1) Un étudiant est connecté
  2) Si enseignant connecté, un étudiant est lié à la requête si celle-ci contient une clé `user_id`. Cette clé est la référence d'un ID étudiant.

  Si une de ces deux conditions sont remplies, renvoie l'objet `Etudiant` lié, sinon `None`.

  Vous pouvez remplacer l'appel à cette fonction en utilisant le décorateur `@student_object` présent dans le même fichier. Avec celui-ci, la vue prendra un paramètre `stu` de type `Etudiant`.
  Si l'étudiant n'est pas présent dans la requête, une erreur `STUDENT_NOT_FOUND` sera renvoyée.

- `is_teacher` de `helpers`: Renvoie vrai si l'utilisateur connecté est enseignant.

  Vous pouvez remplacer l'appel à cette fonction par le décorateur `@teacher_login_required` du fichier `models_helpers`. **Attention**: Ce décorateur ne vous dispense pas d'utiliser `@login_required` !

- `get_request` de `helpers`: Renvoie la requête flask (même chose que le proxy `request` de flask mais typé correctement)

- `db_session` de `server`: Accès à la session ORM (utile pour commit et rollback)

- `ERRORS` de `errors`: Envoi d'erreurs au client au format JSON (voir *Erreurs*)

## Outils

### Changer le mot de passe enseignant

Utilisez l'argument `--password`.

```bash
python src/app.py --password
```

### Reconstruire la base de données

Utilisez l'argument `--init`.

Les données existantes seront perdues !

```bash
python src/app.py --init
```

### Actualisation la localisation de chacune des entreprises

Utilisez l'argument `--locations`.

```bash
python src/app.py --locations
```

### Demander aux étudiants d'actualiser leur profil

Cette fonctionnalité permet d'envoyer un e-mail aux étudiants n'ayant pas actualisé leur profil depuis `x` mois.

Cette commande est faite pour être lancée automatiquement ! (via un cron par exemple).

Utilisez l'argument `--askrefresh <x>`.

```bash
# Cible les étudiants n'ayant pas actualisé leur profil depuis 3 mois ou plus
python src/app.py --askrefresh 3
```

