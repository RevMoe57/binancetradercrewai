#!/usr/bin/env python3
import os
import json
import yaml
import re
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from binance.client import Client

# Charge les variables d'environnement depuis creds.env
load_dotenv('creds.env')

# Supprime toute clé OpenAI pour forcer l'utilisation d'Ollama
os.environ.pop("OPENAI_API_KEY", None)
os.environ["CREWAI_LLM_PROVIDER"] = "ollama"
os.environ["CREWAI_EMBEDDINGS_PROVIDER"] = "ollama"

# Initialisation du LLM via Ollama avec DeepSeek-R1 14b
llm = LLM(
    model="ollama/deepseek-r1:14b",
    base_url="http://localhost:11434",
    api_key="ollama",  # Indique que c'est en local
    temperature=0.3
)

# Initialisation du client Binance avec timeout augmenté
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET")
if not BINANCE_API_KEY or not BINANCE_API_SECRET:
    raise Exception("Merci de définir BINANCE_API_KEY et BINANCE_API_SECRET dans creds.env")
client = Client(
    BINANCE_API_KEY,
    BINANCE_API_SECRET,
    requests_params={'timeout': 30}  # Timeout de 30 secondes
)

def get_usdt_tickers():
    """Récupère la liste des symboles se terminant par 'USDT'."""
    exchange_info = client.get_exchange_info()
    return [s['symbol'] for s in exchange_info['symbols'] if s['symbol'].endswith('USDT')]

def get_market_data(symbols):
    """Récupère les données de marché pour chaque symbole."""
    tickers = client.get_ticker()
    market_data = {}
    for ticker in tickers:
        sym = ticker['symbol']
        if sym in symbols:
            market_data[sym] = {
                "price": float(ticker['lastPrice']),
                "volume": float(ticker['volume'])
            }
    return market_data

@CrewBase
class TradingCrew:
    """
    Crew pour trader automatiquement sur Binance en sélectionnant le meilleur shitcoin.
    Le manager orchestre plusieurs agents.
    """
    def __init__(self):
        self.llm = llm
        self.client = client
        self.usdt_symbols = get_usdt_tickers()
        self.market_data = get_market_data(self.usdt_symbols)
        # Charger la configuration des agents et des tâches depuis les fichiers YAML
        with open("config/agents.yaml", "r") as f:
            self.agents_config = yaml.safe_load(f)
        with open("config/tasks.yaml", "r") as f:
            self.tasks_config = yaml.safe_load(f)
        # Variable pour stocker le prompt final de l'agent de sélection
        self.selection_agent_prompt = None

    @agent
    def selection_agent(self) -> Agent:
        """
        Agent qui analyse les données de marché et choisit le meilleur shitcoin à trader.
        """
        config = self.agents_config.get("selection_agent")
        prompt_template = config.get("prompt")
        # Construit une chaîne contenant les données de marché (limité à 10 entrées)
        market_data_str = ""
        count = 0
        for symbol, data in self.market_data.items():
            if count >= 10:
                break
            market_data_str += f"{symbol}: Prix = {data['price']}, Volume = {data['volume']}\n"
            count += 1
        # Remplace le placeholder {market_data} dans le prompt
        prompt = prompt_template.replace("{market_data}", market_data_str)
        # On recrée une config pour l'agent
        agent_config = {
            "role": config.get("role"),
            "goal": config.get("goal"),
            "backstory": config.get("backstory"),
            "prompt": prompt,
            "stop": config.get("stop")
        }
        # Stocke le prompt pour utilisation dans la tâche
        self.selection_agent_prompt = prompt
        return Agent(
            config=agent_config,
            verbose=True,
            llm=self.llm
        )

    @agent
    def order_agent(self) -> Agent:
        """
        Agent simulé pour l'exécution de l'ordre.
        """
        config = self.agents_config.get("order_agent")
        return Agent(
            config=config,
            verbose=True,
            llm=self.llm
        )

    @crew
    def crew(self) -> Crew:
        """
        Le manager (Crew) orchestre les agents.
        Ici, nous utilisons uniquement l'agent de sélection.
        """
        return Crew(
            agents=[self.selection_agent()],
            process=Process.sequential,
            verbose=True
        )

    @task
    def execute_trade_task(self) -> Task:
        """
        Tâche qui combine la sélection et l'exécution du trade.
        Elle utilise l'agent de sélection pour obtenir le symbole,
        puis exécute l'ordre via l'API Binance.
        """
        # Si le prompt n'est pas encore défini, on force la création de l'agent de sélection.
        if not self.selection_agent_prompt:
            self.selection_agent()
        agent_prompt = self.selection_agent_prompt

        # Appelle directement l'LLM avec le prompt construit
        response = self.llm.call(messages=[{"role": "user", "content": agent_prompt}])
        # Extraction du symbole en prenant la dernière ligne de la réponse
        if isinstance(response, dict):
            full_text = response.get("message", {}).get("content", "").strip()
        else:
            full_text = response.strip()
        lines = full_text.splitlines()
        chosen_symbol = lines[-1].strip().upper()

        print("Le LLM a choisi :", chosen_symbol)

        # Vérification du symbole pour respecter le format Binance
        if not re.fullmatch(r"^[A-Z0-9\-_.]{1,20}$", chosen_symbol):
            raise Exception(f"Symbole invalide extrait : {chosen_symbol}")

        # Exemple : achat d'une quantité fixe (à adapter selon ta stratégie)
        quantity = 10
        try:
            order = self.client.create_order(
                symbol=chosen_symbol,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_MARKET,
                quantity=quantity
            )
        except Exception as e:
            print("Erreur lors de la création de l'ordre :", e)
            return

        print("Commande passée :", json.dumps(order, indent=2))
        task_config = self.tasks_config.get("execute_trade_task", {})
        return Task(
            config=task_config,
            output_file="trade_order.json"
        )

def main():
    crew_instance = TradingCrew()
    crew_instance.execute_trade_task()
    print("Trading effectué avec succès.")

if __name__ == '__main__':
    main()
