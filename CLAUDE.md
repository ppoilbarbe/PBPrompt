# CLAUDE.md — PBPrompt

Application PySide6 de gestion et traduction de prompts IA.
Auteur : PBMou. Licence MIT. Python ≥ 3.11.

## État courant

- **Version** : 1.6.0
- **Stockage** : SQLite (`.sqlite`, WAL). YAML = import/export uniquement.
- **Colonnes** : `Column(IntEnum)` AI=0, GROUP=1, NAME=2, IMAGE=3, LOCAL=4, ENGLISH=5
- **Locales compilées** : en, de, fr, es, it, ru, vi, zh_CN

## Commandes essentielles

```
make all              # compile UI + resources + traductions (obligatoire après tout .ui modifié)
make run              # lance l'application (PYTHONPATH=src)
make clean all        # recréation complète depuis les sources
make test             # pytest (pytest-xvfb gère le display virtuel sur Linux)
make test-cov         # pytest --cov --cov-report=html
make lint             # ruff check
make format           # ruff format + check --fix
make docs             # Sphinx (après make clean all)
make dist             # archives dist/pbprompt-x.y.z.tar.gz et .zip
make translations     # compile les .po → .mo
make bump-patch/minor/major  # incrémente la version semver
```

## Règles impératives — code

**Fichiers générés — ne jamais éditer manuellement :**
- `src/pbprompt/gui/ui_*.py` (générés par `pyuic5`)
- `src/pbprompt/gui/resources_rc.py` (généré par `pyrcc5`)
- Toutes les actions `QAction` (y compris les raccourcis) doivent être définies dans le
  fichier `.ui`, jamais ajoutées à la main dans le `.py` généré.

**SQL — `"group"` est un mot-clé réservé :**
Toujours entre guillemets dans toutes les requêtes SQL : `"group"`.

**Bug MRO — raccourcis clavier :**
`MainWindow` hérite de `QMainWindow` ET `Ui_MainWindow`. Python's MRO fait que
`MainWindow.retranslateUi()` masque `Ui_MainWindow.retranslateUi()` → tous les
`setShortcut()` du fichier généré sont du code mort.
→ Tous les raccourcis doivent être définis dans `MainWindow.retranslateUi()` avec le
commentaire : `# Keyboard shortcuts — set here because Ui_MainWindow.retranslateUi is
# shadowed by this override (Python MRO) and therefore never called at runtime.`

**Icônes QRC :**
Toujours vérifier `QFile.exists(path)` AVANT `QIcon(path)`. Ne jamais appeler
`QIcon(":/icons/name.svg")` directement — produit des warnings Qt si le fichier manque.

**Proxy model — `Column(IntEnum)` :**
Convertir explicitement en `int()` avant tout appel à `model.index()`. Certains builds
PySide6/Shiboken retournent silencieusement un `QModelIndex` invalide avec un `IntEnum`.

## Règles impératives — fichiers `.ui` Qt Designer

- **Commentaires XML** : interdits à l'intérieur des éléments `<layout>` ou `<widget>`
  (pyuic5 plante). Autorisés uniquement hors des éléments enfants de widgets.
- **Marges de layout** : utiliser quatre propriétés séparées :
  ```xml
  <property name="leftMargin"><number>6</number></property>
  <property name="topMargin"><number>6</number></property>
  <property name="rightMargin"><number>6</number></property>
  <property name="bottomMargin"><number>4</number></property>
  ```
  Les formes `<contentsMargins>`, `<margins>`, `<number>` seul sont toutes invalides.
- **Sous-classes Qt** : toujours déclarer dans `<customwidgets>` (ex: `PromptTableView`).

## Règles impératives — internationalisation

Quand une chaîne traduite est **ajoutée ou modifiée** :
- Mettre à jour **toutes** les langues dans `locales/*/LC_MESSAGES/messages.po`
- Ne jamais laisser un `msgstr` vide ou inchangé dans un fichier `.po` existant
- Lancer `make translations` pour recompiler les `.mo`

Résolution de la langue : `lang = config.xxx_language or system_language()`.
Ne jamais calculer le chemin de `locales/` via `Path(__file__).parent...` hors de
`i18n.py`. Utiliser `get_locale_dir()` de `i18n.py` (gère PyInstaller).

## Règles impératives — documentation RST (Sphinx)

- Valider chaque `.rst` modifié : `python3 -m docutils <fichier> /dev/null` (code 0, aucun message).
- Utiliser `.. list-table::` exclusivement — jamais de tables en grille (`+----+----+`).
- Indentation dans les directives : **3 espaces**, jamais de tabulation.
- Après toute modification `.rst` ou docstring : `make clean all docs` doit se terminer
  **sans aucun WARNING ni ERROR Sphinx**. Ne pas se contenter de `make docs`.

## Workflow Git

**Avant tout commit :**
```
pre-commit run --all-files
```
Vérifier que tous les hooks passent (code 0, aucun fichier modifié). Ne jamais publier
si cette commande échoue ou modifie des fichiers.

**Avant tout push — squash obligatoire :**
```
git log --oneline origin/main..HEAD   # compter N commits
git reset --soft HEAD~N
git commit -m "..."
```
Un push = un commit. Le message de commit résume **tous** les changements inclus.

**Messages de commit et noms de tags** : toujours en anglais.

**Avant tout tag/release :**
Mettre à jour `CHANGELOG.md` avec une section `## [X.Y.Z] – YYYY-MM-DD` (Added /
Changed / Fixed). Le pipeline CI extrait les notes de release depuis ce fichier.

## Installation (environnement conda)

```
pip install deep-translator
pip install -e . --no-deps    # --no-deps obligatoire : ne pas réinstaller les paquets conda
```

## Maintenance des fichiers de référence — OBLIGATOIRE

À chaque session qui modifie le projet, mettre à jour ces deux fichiers :

**`claude_prompt.txt`** — spécification complète du projet :
- Ajouter toute nouvelle fonctionnalité, contrainte technique ou correction notable
- Maintenir la cohérence avec le code source effectif

**`claude_summary.txt`** — état de l'implémentation actuelle :
- Mettre à jour la version, l'architecture, les modules, les décisions techniques
- Ce fichier permet de reprendre le contexte d'une session à l'autre sans relire le code
- Mettre à jour après chaque modification significative

En cas de divergence entre ces fichiers et le code source, **le code source fait foi**.
