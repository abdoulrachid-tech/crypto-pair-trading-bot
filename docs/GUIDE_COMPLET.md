# Guide complet — Bot de Pair Trading BTC/ETH

*Document de référence technique et administratif. Objectif : que n'importe
qui — développeur, opérationnel, ou décideur non-technique — puisse
comprendre ce que fait l'application, comment elle est construite, et
comment l'exploiter en toute sécurité.*

---

## 1. Résumé exécutif

Cette application est un **bot de trading automatisé** qui applique une
stratégie appelée *pair trading* (arbitrage statistique) sur deux
cryptomonnaies, Bitcoin (BTC) et Ethereum (ETH). Elle se compose de trois
programmes qui communiquent entre eux, plus deux bases de données, et
s'utilise via un tableau de bord web (navigateur).

**Ce que fait l'application concrètement :**
- Elle observe en continu les prix de BTC et ETH.
- Elle calcule si leur relation de prix s'écarte anormalement de sa norme
  statistique habituelle.
- Si oui, elle peut ouvrir une position (acheter l'un, vendre l'autre) en
  pariant sur un retour à la normale, puis la refermer une fois ce retour
  constaté.
- Par défaut, elle fait cela **en simulation** (aucun argent réel engagé).
  Le passage en argent réel nécessite une action explicite et volontaire
  (voir section 5).

**Pourquoi c'est structuré ainsi (en bref) :** séparer "calculer/décider"
(le bot), "stocker/sécuriser l'accès" (le backend) et "afficher"
(le frontend) permet de faire évoluer, surveiller et sécuriser chaque
partie indépendamment — une pratique standard en ingénierie logicielle.

**Niveau de risque à garder en tête :** dès lors que le mode réel est
activé, cette application engage de l'argent réel sur des marchés
volatils. Aucun garde-fou logiciel ne remplace une supervision humaine
active, en particulier dans les premières heures suivant une mise en
production. Ceci n'est pas un conseil financier — c'est une description
technique du fonctionnement du système.

---

## 2. Vue d'ensemble de l'architecture

```text
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   trading-bot/       │     │      backend/         │     │     frontend/        │
│   (Python)           │     │      (Node.js)        │     │      (React)         │
│                       │     │                        │     │                     │
│  Calcule, décide,     │────▶│  Reçoit et stocke,     │────▶│  Affiche le          │
│  exécute (ou simule)  │ API │  authentifie,          │ API │  dashboard,          │
│  les ordres           │HTTP │  sert les données      │HTTP │  formulaires de      │
│                       │     │                        │     │  connexion/réglages  │
└──────────┬────────────┘     └──────────┬─────────────┘     └─────────────────────┘
           │                              │
           ▼                              ▼
   ┌───────────────┐             ┌────────────────┐
   │  PostgreSQL    │             │    MongoDB      │
   │  (recherche/    │             │  (opérationnel : │
   │  historique)    │             │  logs, trades,   │
   │                │             │  statut, config) │
   └───────────────┘             └────────────────┘
```

**Les trois programmes tournent séparément** (trois process différents,
qu'on lance chacun de son côté), et communiquent uniquement via des appels
réseau (HTTP). C'est pour cela qu'il faut par exemple démarrer le backend
*et* le bot pour que le dashboard affiche des données : si l'un des deux
manque, la chaîne est coupée.

**Pourquoi deux bases de données différentes ?**
- **PostgreSQL** : conçue pour l'analyse de données structurées en volume
  (séries de prix, calculs statistiques). Utilisée par le bot pour son
  historique de recherche/backtest.
- **MongoDB** : conçue pour stocker des documents flexibles rapidement,
  bien adaptée aux logs, trades, et à l'état courant du bot que le backend
  sert au frontend. Son schéma est plus facile à faire évoluer (on l'a
  fait plusieurs fois dans ce projet — ajout des snapshots, de la config).

Aucune des deux n'est "meilleure" dans l'absolu : ce sont deux outils
choisis pour deux usages différents au sein de la même application.

---

## 3. Concepts financiers et statistiques utilisés

Cette section explique le *pourquoi* derrière le code, pas seulement le
*comment*. Comprendre ces notions est nécessaire pour interpréter
correctement ce qu'affiche le dashboard.

### 3.1 Le pair trading (arbitrage statistique)

Idée de base : au lieu de parier sur la direction du marché (BTC va monter
ou descendre), on parie sur la **relation** entre deux actifs corrélés.
Si BTC et ETH évoluent historiquement ensemble, et que leur écart de prix
("spread") s'éloigne anormalement de sa moyenne habituelle, on parie que
cet écart va se resserrer — sans avoir besoin de savoir si le marché
global monte ou descend. C'est ce qui rend la stratégie théoriquement
"neutre au marché" (*market neutral*).

### 3.2 Cointégration

Deux séries de prix sont dites **cointégrées** si, bien que chacune
évolue de façon aléatoire et imprévisible individuellement, une
combinaison linéaire des deux (leur "spread", une fois ajusté par le
hedge ratio — voir 3.3) reste stable dans le temps (elle revient toujours
vers une moyenne). C'est l'hypothèse statistique fondamentale sur
laquelle repose toute la stratégie : **sans cointégration, il n'y a
aucune raison statistique de penser que l'écart va se résorber**, et
trader dans ce cas reviendrait à parier à l'aveugle.

Le bot teste cette hypothèse avec deux méthodes complémentaires :
- **Test ADF** (Augmented Dickey-Fuller) : teste si le spread est
  *stationnaire* (revient à une moyenne) plutôt que de dériver sans
  limite.
- **Test d'Engle-Granger** : teste directement la cointégration entre les
  deux séries de prix brutes.

Chaque test produit une **p-value** : plus elle est basse (typiquement
< 0.05), plus on a de raisons de rejeter l'hypothèse "pas de
cointégration" — donc plus la relation semble statistiquement valide. À
l'inverse, une p-value proche de 1 (comme on l'a vu se produire dans ce
projet, à 0.97 et 0.99) signifie que rien ne permet de dire que la
relation est stable en ce moment.

### 3.3 Hedge ratio (β, beta)

Le hedge ratio est le coefficient qui répond à la question : "combien
d'ETH dois-je détenir pour neutraliser le risque directionnel d'une unité
de BTC ?" Il est estimé par régression linéaire (moindres carrés
ordinaires, OLS) : `prix_BTC = intercept + β × prix_ETH + résidu`. Ce
résidu, une fois la relation linéaire retirée, **est** le spread que la
stratégie surveille.

### 3.4 Spread et Z-score

- **Spread** : l'écart entre le prix réel de BTC et le prix "prédit" par
  le hedge ratio à partir du prix d'ETH.
- **Z-score** : le spread exprimé en nombre d'écarts-types par rapport à
  sa moyenne récente. Un Z-score de +2 signifie "le spread est
  actuellement 2 écarts-types au-dessus de sa moyenne habituelle" — un
  signal que quelque chose d'anormal se produit, et donc une occasion
  potentielle d'entrée en position.

Seuils utilisés par la stratégie (configurables, voir section 8) :
- **Seuil d'entrée** (`ZSCORE_ENTRY`, défaut 2.0) : au-delà, on ouvre une
  position.
- **Seuil de sortie** (`ZSCORE_EXIT`, défaut 0.5) : en dessous, on
  referme la position (le spread est revenu près de sa moyenne).
- **Seuil de stop-loss** (`ZSCORE_STOPLOSS`, défaut 4.0) : si le spread
  continue de s'éloigner au lieu de revenir, on coupe la perte plutôt que
  d'attendre indéfiniment un retour qui pourrait ne jamais survenir.

### 3.5 Half-life (demi-vie de retour à la moyenne)

Mesure, en nombre de périodes, le temps que met statistiquement le
spread à revenir à mi-chemin de sa moyenne après un écart. Une half-life
trop élevée (le retour est trop lent) rend la stratégie peu exploitable
en pratique, même si la cointégration est techniquement valide — c'est
pourquoi c'est un second garde-fou de désactivation automatique,
indépendant du test de cointégration.

### 3.6 Recalibrage périodique

Les relations statistiques entre actifs évoluent avec le temps (nouvelles
conditions de marché, événements spécifiques à une des deux cryptos...).
Le bot recalcule donc périodiquement (`RECALIBRATION_INTERVAL_HOURS`,
défaut 7 jours) le hedge ratio et revalide la cointégration sur les
données récentes, plutôt que de se fier indéfiniment à une estimation
faite une seule fois au démarrage.

### 3.7 Backtesting et ses métriques

Avant de risquer le moindre capital, la stratégie peut être testée sur
des données passées (`scripts/run_backtest.py`). Métriques produites :

| Métrique | Signification |
|---|---|
| **Sharpe ratio (annualisé)** | Rendement obtenu par unité de risque pris. Plus il est élevé, mieux c'est ; négatif signifie que la stratégie a perdu de l'argent ajusté du risque. |
| **Max drawdown** | La pire perte cumulée observée depuis un sommet, en pourcentage. Indique le pire scénario traversé pendant la période testée. |
| **Win rate** | Pourcentage de trades clôturés avec un gain. **Attention** : un win rate élevé ne garantit pas un rendement positif si les pertes, quand elles arrivent, sont plus grosses que les gains (ou si les frais de transaction rongent des gains individuellement petits — un cas réel rencontré lors des tests de ce projet, voir section 10.3). |
| **In-sample / out-of-sample** | La stratégie est calibrée sur une portion des données ("in-sample") puis testée sur la portion suivante, jamais vue pendant le calibrage ("out-of-sample") — pour éviter de sur-ajuster les paramètres aux données passées d'une façon qui ne se généraliserait pas. |

---

## 4. Simulation vs mode réel — comment la sécurité est construite

C'est la distinction la plus importante à comprendre avant toute mise en
production.

### 4.1 Le principe

Le bot peut fonctionner en **simulation** (aucun ordre envoyé à
l'exchange, tout est calculé "pour de faux") ou en **réel** (`live`,
ordres véritablement envoyés, argent réel engagé). Par défaut et sans
action explicite, le bot est **toujours** en simulation.

### 4.2 Le double interrupteur

Passer en réel nécessite de positionner **deux** variables
d'environnement distinctes dans `trading-bot/.env`, volontairement
séparées l'une de l'autre :

```
TRADING_MODE=live
LIVE_TRADING_CONFIRMED=true
```

**Pourquoi deux et pas une seule ?** Pour qu'une erreur de manipulation
(mauvais fichier `.env` copié, copier-coller malheureux, valeur laissée
par erreur d'un test précédent) ne puisse jamais, à elle seule, activer
le trading réel. Il faut deux erreurs indépendantes pour que ça arrive
par accident — un principe de sécurité classique ("defense in depth").

### 4.3 L'avertissement au démarrage

Quand le mode réel est effectivement actif, le bot affiche un
avertissement bloquant de 10 secondes dans sa console avant de démarrer,
rappelant le capital exposé et les actifs concernés — une dernière
occasion d'interrompre (Ctrl+C) avant que quoi que ce soit ne parte.

### 4.4 Le garde-fou automatique de cointégration

Indépendamment du mode simulation/réel, le bot **refuse de générer des
signaux de trading** si le test de cointégration échoue (voir section
3.2) ou si la half-life est trop élevée. Dans ce cas :
- Les prix continuent d'être suivis et affichés (pour que vous puissiez
  observer ce qui se passe).
- Aucun signal, aucune position, aucun ordre n'est généré.
- Le bot retente automatiquement à chaque cycle, et réactive le trading
  dès que les conditions redeviennent valides.

Ce garde-fou s'applique **également en mode réel** — il n'existe aucune
façon de le contourner depuis la configuration normale du bot.

### 4.5 Le coupe-circuit manuel (page Réglages)

En complément du garde-fou automatique, un interrupteur manuel est
disponible depuis l'interface web (page **Réglages**) : "Mettre le
trading en pause" / "Réactiver le trading". Utile pour interrompre
volontairement le trading (maintenance, doute, actualité de marché...)
sans avoir à toucher au serveur. Le bot vérifie cet état à chaque cycle.
Les deux mécanismes (automatique et manuel) sont indépendants : si l'un
des deux dit "pause", le trading est en pause.

### 4.6 Permissions des clés API exchange

Recommandation opérationnelle systématiquement rappelée dans ce projet :
les clés API générées sur l'exchange doivent avoir **uniquement** la
permission "trading spot" — jamais la permission "retrait" (withdraw).
Ainsi, même en cas de compromission des clés, un attaquant ne peut pas
vider le compte, seulement passer des ordres.

---

## 5. Détail des composants

### 5.1 Le bot Python (`trading-bot/`)

| Fichier | Rôle |
|---|---|
| `config.py` | Centralise toute la configuration (lue depuis `.env`) — une seule source de vérité pour tous les autres modules. |
| `data_collector.py` | Récupère l'historique de prix (OHLCV) via CCXT, avec pagination automatique. |
| `stats.py` | Calcule hedge ratio, spread, tests de cointégration (ADF, Engle-Granger), Z-score glissant, half-life. |
| `signal_generator.py` | Transforme un Z-score en décision (`long` / `short` / `close` / `hold`) selon les seuils configurés et la position actuelle. |
| `backtester.py` | Simule l'application de la stratégie sur un historique, avec frais de transaction réalistes, pour produire les métriques de la section 3.7. |
| `recalibrator.py` | Recalcule périodiquement les paramètres de la stratégie et revalide la cointégration ; détermine si le trading doit être mis en pause. |
| `executor.py` | Exécute réellement l'ordre (via CCXT) en mode réel, ou simule le résultat en mode simulation. |
| `api_client.py` | Transmet logs, trades, statut, snapshots et configuration au backend ; interroge le coupe-circuit manuel. Toujours "best-effort" : une panne du backend ne doit jamais faire planter le bot. |
| `main.py` | Orchestrateur : la boucle principale qui enchaîne toutes les étapes à chaque cycle (voir section 6). |
| `db.py` | Connexion et schéma PostgreSQL pour l'historique de recherche. |
| `monitor.py` | Logging, alertes Telegram optionnelles, détection de drawdown excessif. |

### 5.2 Le backend (`backend/`)

Une API REST en Express.js. Deux catégories de routes, avec deux
mécanismes d'authentification différents et volontairement séparés :

- **Routes utilisateur** (`/api/auth/*`, lectures sous `/api/bot/*`) :
  protégées par un cookie JWT HttpOnly, obtenu via connexion
  email/mot de passe. C'est ce que le frontend utilise.
- **Routes bot-to-bot** (écritures sous `/api/bot/*` : logs, trades,
  status, snapshots, config) : protégées par un token statique partagé
  (`BOT_API_TOKEN`), envoyé en en-tête `Authorization: Bearer ...`. Le
  bot Python n'est pas un "utilisateur" au sens propre, donc il n'utilise
  pas le même mécanisme.

Modèles de données (MongoDB) :

| Modèle | Contenu |
|---|---|
| `User` | Comptes utilisateurs (email, mot de passe haché). |
| `Trade` | Chaque position ouverte/fermée par le bot. |
| `BotLog` | Journal d'exécution du bot. |
| `BotStatus` | État courant "vivant" du bot (isRunning, dernier Z-score, raison de pause éventuelle). |
| `MarketSnapshot` | Un point par cycle (prix, spread, Z-score, beta) — alimente les graphiques continus, indépendamment des trades. |
| `BotConfig` | Configuration active rapportée par le bot (lecture seule côté interface) + coupe-circuit manuel (écrit depuis l'interface). |

### 5.3 Le frontend (`frontend/`)

| Page | Contenu |
|---|---|
| **Dashboard** | Vue d'ensemble : cartes de synthèse (PnL, nombre de trades, win rate, drawdown, dernier Z-score, statut), graphique des prix BTC/ETH en continu, PnL cumulé, Z-score avec seuils, derniers trades. Rafraîchi automatiquement toutes les 15 secondes. |
| **Historique des trades** | Liste complète des trades passés. |
| **Logs** | Journal d'exécution du bot, consultable depuis le navigateur. |
| **Réglages** | Contrôle du process (démarrer/arrêter le bot), coupe-circuit manuel, configuration active du bot (lecture seule). |

---

## 6. Le cycle d'exécution du bot, étape par étape

À chaque intervalle (`CYCLE_INTERVAL_SECONDS`, défaut 5 minutes), le bot
exécute dans l'ordre :

1. **Récupère** les derniers prix de BTC et ETH (via l'exchange).
2. **Met à jour** son historique en mémoire (fenêtre glissante).
3. **Recalibre** si l'intervalle de recalibrage est écoulé (ou si c'est
   le tout premier cycle) : recalcule hedge ratio, revalide la
   cointégration.
4. **Vérifie le coupe-circuit manuel** (interface web) en plus du
   résultat de la recalibration.
5. **Si le trading est en pause** (cointégration invalide ou pause
   manuelle) : transmet uniquement les prix pour affichage, ne génère
   aucun signal, s'arrête là pour ce cycle.
6. **Sinon** : calcule le spread et le Z-score courants, génère un
   signal, l'exécute (réellement ou en simulation), transmet trade/
   snapshot/statut au backend.
7. **Attend** l'intervalle configuré, puis recommence.

---

## 7. Sécurité de l'authentification

- Mots de passe : jamais stockés en clair, toujours hachés.
- Session : cookie **HttpOnly** (inaccessible en JavaScript côté
  navigateur, ce qui limite l'impact d'une éventuelle faille XSS) +
  **JWT** signé côté serveur, expirant après 7 jours.
- `SameSite` du cookie : `lax` par défaut (adapté à un usage
  local/réseau local), `none` + HTTPS obligatoire si frontend et backend
  sont déployés en ligne sur deux domaines différents.
- CORS : liste blanche explicite d'origines autorisées
  (`FRONTEND_ORIGIN`), qui accepte plusieurs valeurs séparées par des
  virgules pour combiner local + réseau local + déploiement public.

---

## 8. Configuration — où et comment

Toute la configuration se fait via des fichiers `.env` (jamais commités
dans le dépôt Git — ce sont des secrets/réglages propres à chaque
installation), à partir des fichiers `.env.example` fournis :

| Fichier | Contrôle |
|---|---|
| `trading-bot/.env` | Exchange, paire tradée, seuils de stratégie, mode simulation/réel, bases de données, fenêtre d'historique. |
| `backend/.env` | Connexion MongoDB, secret JWT, origine(s) frontend autorisée(s), token partagé avec le bot, chemins pour le contrôle du process (section 9). |
| `frontend/.env` | URL de l'API backend (uniquement nécessaire si frontend et backend sont sur des domaines différents). |

La page **Réglages** de l'interface affiche la configuration active du
bot en lecture seule (rapportée automatiquement au démarrage) — pour
modifier une valeur, il faut éditer le `.env` correspondant puis
redémarrer le bot ; ce n'est pas un choix technique arbitraire mais une
conséquence du fait que le process Python ne relit pas son
environnement en cours d'exécution.

---

## 9. Démarrer / arrêter le bot depuis l'interface

Une fois `TRADING_BOT_DIR` et `TRADING_BOT_PYTHON` renseignés dans
`backend/.env` (chemins absolus, voir `.env.example` pour l'exemple
Windows), la page **Réglages** permet de démarrer et arrêter le bot d'un
clic, sans terminal.

**Comment ça fonctionne techniquement :** le backend Node.js lance le
bot comme un process enfant (`python -m src.main`) et garde une
référence à ce process. "Démarrer" le lance, "Arrêter" y met fin
(proprement si possible, en forçant l'arrêt après un court délai sinon).

**Prérequis et limites à connaître :**
- Le backend et le bot doivent tourner **sur la même machine** (ce qui
  est le cas ici avec des bases de données natives).
- L'état "en cours d'exécution" affiché n'est fiable que tant que **ce**
  process backend n'a pas redémarré depuis le dernier démarrage du bot —
  la référence est gardée en mémoire, pas persistée sur disque. Si le
  backend redémarre (ex. `nodemon` qui recharge sur un changement de
  fichier), il perd la trace du bot même si celui-ci continue de
  tourner en arrière-plan. En cas de doute, vérifiez le Gestionnaire des
  tâches Windows (recherchez `python.exe`).
- Arrêter le bot depuis l'interface est un arrêt **de process** : si le
  bot était en train d'exécuter un ordre au moment précis de l'arrêt,
  ce n'est pas annulé — seul le prochain cycle n'aura pas lieu.

---

## 10. Guide de lecture du dashboard

| Élément affiché | Comment l'interpréter |
|---|---|
| **Statut du bot** (Actif/Arrêté) | Reflète si le bot a rapporté un battement de vie récent. "Arrêté" après un arrêt manuel ou un crash. |
| **Bandeau "Trading en pause"** | Le bot tourne et suit les prix, mais ne génère aucun signal — cointégration invalide et/ou pause manuelle active (page Réglages indique la raison exacte). |
| **Dernier Z-score** | Voir section 3.4. Proche de 0 = spread normal. Au-delà des seuils = signal potentiel. |
| **Prix BTC/ETH** | Alimenté à chaque cycle, même hors trading — c'est la vue "marché", indépendante de la stratégie. |
| **PnL cumulé** | Ne bouge qu'aux trades clôturés — reste plat tant qu'aucune position n'a été fermée, y compris en cours de position ouverte. |
| **Win rate élevé mais PnL négatif** | Signal d'alerte connu du pair trading à haute fréquence : les frais de transaction peuvent dépasser des gains individuellement petits même avec un bon taux de réussite (observé lors des tests de simulation de ce projet). |

### 10.3 Rappel sur le test de simulation réalisé pendant le développement

Une simulation de bout en bout sur données synthétiques (mais
statistiquement fidèles à une vraie paire cointégrée) a validé que toute
la chaîne fonctionne correctement — hedge ratio et cointégration
correctement détectés — mais a produit un rendement légèrement négatif
malgré un win rate élevé (73 %/69 %), à cause des frais de transaction
sur un spread qui revenait à la moyenne trop rapidement. Ce n'est ni un
bug ni une prédiction sur les vraies données de marché : c'est la preuve
que le pipeline détecte correctement une configuration de paramètres
perdante, exactement le rôle attendu du backtesting avant toute mise en
production réelle.

---

## 11. Glossaire

| Terme | Définition courte |
|---|---|
| **ADF (test)** | Test statistique vérifiant si une série revient à une moyenne plutôt que de dériver indéfiniment. |
| **Backtest** | Simulation d'une stratégie sur des données passées. |
| **Cointégration** | Relation stable dans le temps entre deux séries de prix, condition nécessaire à la stratégie. |
| **CORS** | Mécanisme du navigateur limitant quels sites peuvent appeler une API. |
| **Coupe-circuit manuel** | Interrupteur dans l'interface pour mettre le trading en pause sans toucher au serveur. |
| **Cointégration invalidée** | Message indiquant que le test statistique a échoué — le trading se met alors en pause automatiquement. |
| **CCXT** | Bibliothèque logicielle permettant de dialoguer avec de nombreux exchanges de cryptomonnaies via une interface commune. |
| **Drawdown** | Baisse depuis un sommet précédent, exprimée en pourcentage. |
| **Engle-Granger** | Test statistique de cointégration entre deux séries de prix. |
| **Half-life** | Temps estimé pour qu'un écart revienne à mi-chemin de sa moyenne. |
| **Hedge ratio (β)** | Coefficient de la relation linéaire entre les deux actifs de la paire. |
| **JWT** | Jeton signé numériquement utilisé pour authentifier une session utilisateur. |
| **Live trading** | Mode où des ordres réels sont envoyés à l'exchange, avec de l'argent réel. |
| **OHLCV** | Open/High/Low/Close/Volume — format standard de bougie de prix. |
| **Pair trading** | Stratégie pariant sur la relation entre deux actifs plutôt que sur leur direction individuelle. |
| **PnL** | Profit and Loss — le résultat financier, réalisé (trades clôturés) ou latent (positions ouvertes). |
| **Sharpe ratio** | Rendement ajusté du risque pris. |
| **Simulation (paper trading)** | Mode où la stratégie tourne "pour de faux", sans engager d'argent réel. |
| **Snapshot** | Un point de données (prix/spread/Z-score) capturé à un instant donné, pour l'affichage continu. |
| **Spread** | Écart entre le prix réel d'un actif et sa valeur "prédite" par le hedge ratio. |
| **Win rate** | Proportion de trades clôturés en gain. |
| **Z-score** | Le spread exprimé en nombre d'écarts-types par rapport à sa moyenne récente. |

---

## 12. Limites connues et pistes d'amélioration

- **Contrôle du process bot** : fonctionne uniquement en local (backend
  et bot sur la même machine), et son état n'est pas persisté si le
  backend redémarre (voir section 9).
- **Configuration éditable** : la page Réglages est en lecture seule
  pour les paramètres de stratégie ; les modifier nécessite d'éditer un
  `.env` et de redémarrer le bot.
- **Backtesting** : les résultats sur données synthétiques valident le
  pipeline logiciel, pas une garantie de rentabilité sur de vraies
  données de marché.
- **Aucune fonctionnalité de cette application ne constitue un conseil
  financier.** Toute décision de risquer du capital réel reste sous la
  seule responsabilité de la personne qui exploite le bot.

---

*Fin du document. Pour toute question sur une section précise, se
référer au code source correspondant (chemins indiqués tout au long de
ce document) ou au `README.md` à la racine du projet pour les
instructions d'installation pas à pas.*
