# BinanceTraderCrewAI

![Banner](https://via.placeholder.com/1200x300?text=BinanceTraderCrewAI)

**BinanceTraderCrewAI** est un projet expérimental qui combine le pouvoir des grands modèles de langage (LLM) en local via Ollama (DeepSeek-R1) avec la flexibilité de CrewAI pour automatiser le trading sur Binance. L'idée est de sélectionner automatiquement le "meilleur shitcoin" à trader en analysant les données de marché, puis de passer un ordre d'achat via l'API Binance.

> **Attention :**  
> Ce projet est **expérimental** et ne constitue en aucun cas un conseil financier. Teste-le sur un compte de simulation avant toute utilisation réelle et utilise-le avec précaution !

---

## Table des matières

- [Caractéristiques](#caractéristiques)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Utilisation](#utilisation)
- [Avertissements](#avertissements)
- [Contribuer](#contribuer)
- [Licence](#licence)
- [Contact](#contact)

---

## Caractéristiques

- **Automatisation complète** : Un manager de CrewAI orchestre plusieurs agents pour analyser les données de marché et décider automatiquement du meilleur actif à trader.
- **LLM Local** : Utilisation de DeepSeek-R1 via Ollama pour traiter et analyser les informations en local.
- **Intégration Binance** : Passage automatique d'ordres via l'API Binance avec gestion des erreurs et timeout personnalisé.
- **Configuration flexible** : Les prompts et la logique des agents sont paramétrables via des fichiers YAML.

---

## Prérequis

- **Python 3.12** ou version compatible.
- Compte Binance et accès à l'API Binance.
- [Ollama](https://ollama.com/) installé et configuré pour lancer le modèle DeepSeek-R1 (14b recommandé).

---

## Installation

1. **Cloner le dépôt :**

   ```bash
   git clone https://github.com/RevMoe57/binancetradercrewai.git
   cd binancetradercrewai

    Installer les dépendances :

pip install crewai python-binance pyyaml python-dotenv

Lancer le modèle LLM localement via Ollama :

    ollama run deepseek-r1:14b

Configuration
Fichier creds.env

Crée un fichier nommé creds.env à la racine du projet avec le contenu suivant :

BINANCE_API_KEY=ta_cle_api_binance
BINANCE_API_SECRET=ton_secret_binance

Fichiers YAML de configuration

Dans le dossier config/, crée les fichiers suivants :
config/agents.yaml

selection_agent:
  role: "Sélecteur de crypto"
  goal: "Analyser les données de marché et choisir le meilleur shitcoin à trader"
  backstory: "Expert en trading crypto avec une connaissance approfondie des tendances du marché."
  prompt: >
    Voici quelques données de marché de crypto-monnaies USDT :
    {market_data}
    Parmi ces crypto-monnaies, quel est le meilleur shitcoin à trader aujourd'hui ? Réponds uniquement avec le symbole.
  stop: "\n"

order_agent:
  role: "Exécuteur d'ordre"
  goal: "Confirmer l'exécution d'une commande d'achat sur Binance"
  backstory: "Agent de trading automatique, spécialisé dans l'exécution rapide des ordres."
  prompt: "Confirme l'exécution de l'ordre d'achat sur Binance."
  stop: "\n"

config/tasks.yaml

execute_trade_task:
  action: "execute_trade"
  output_file: "trade_order.json"

Utilisation

Pour lancer le projet, exécute :

python3 main.py

Le script va :

    Récupérer les tickers se terminant par USDT sur Binance.
    Extraire et analyser les données de marché pour une sélection automatique.
    Construire un prompt personnalisé à partir des données et de la configuration des agents.
    Utiliser le LLM local pour choisir le meilleur actif (shitcoin) à trader.
    Passer un ordre d'achat via l'API Binance et enregistrer les détails de l'ordre dans trade_order.json.

Avertissements

    Projet Expérimental :
    Ce code est développé pour tester et expérimenter l'automatisation du trading. Il n'est pas optimisé pour une utilisation en production.

    Risques Financiers :
    Le trading de cryptomonnaies comporte des risques importants. N'utilise ce projet que pour des expérimentations sur des comptes de simulation et n'investis que ce que tu es prêt à perdre.

    Validation :
    Le choix effectué par le LLM est basé sur une analyse textuelle des données et ne garantit en aucun cas la rentabilité.

Contribuer

Les contributions sont les bienvenues !
Si tu souhaites apporter des améliorations, corriger des bugs ou ajouter de nouvelles fonctionnalités, n'hésite pas à :

    Forker ce dépôt.
    Créer une branche avec tes modifications.
    Soumettre une Pull Request.

