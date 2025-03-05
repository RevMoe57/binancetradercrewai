#!/usr/bin/env python3
import os
import json
import yaml
import re
import math
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from binance.client import Client
import ollama  # Module pour gérer Ollama

# 🚀 Assurer que Ollama est lancé
ollama.start_ollama()

# 🛠️ Chargement des variables d'environnement
load_dotenv('creds.env')

# 🌐 Configuration de CrewAI pour Ollama
os.environ.pop("OPENAI_API_KEY", None)
os.environ["CREWAI_LLM_PROVIDER"] = "ollama"
os.environ["CREWAI_EMBEDDINGS_PROVIDER"] = "ollama"

# 🎯 Initialisation du modèle LLM
llm = LLM(
    model="ollama/deepseek-r1:1.5b",
    base_url="http://localhost:11434",
    api_key="ollama",
    temperature=0.3
)

# 🔑 Vérification des clés API Binance
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET")
if not BINANCE_API_KEY or not BINANCE_API_SECRET:
    raise Exception("\033[91m[ERREUR]\033[0m Merci de définir BINANCE_API_KEY et BINANCE_API_SECRET dans creds.env")

# 📡 Initialisation du client Binance
client = Client(
    BINANCE_API_KEY,
    BINANCE_API_SECRET,
    testnet=True,
    tld='com',
    requests_params={'timeout': 30}
)

def log_step(message):
    """Affiche un log avec timestamp."""
    print(f"\033[94m[{datetime.now().strftime('%H:%M:%S')}]\033[0m {message}")

def get_usdt_tickers():
    """Récupère les symboles USDT depuis Binance."""
    log_step("Récupération des symboles USDT...")
    exchange_info = client.get_exchange_info()
    tickers = [s['symbol'] for s in exchange_info['symbols'] if s['symbol'].endswith('USDT')]
    log_step("\033[92m✔ Symboles USDT récupérés\033[0m")
    return tickers

def get_market_data(symbols):
    """Récupère les données de marché pour les symboles donnés."""
    log_step("Récupération des données de marché...")
    tickers = client.get_ticker()
    market_data = {
        t['symbol']: {"price": float(t['lastPrice']), "volume": float(t['volume'])}
        for t in tickers if t['symbol'] in symbols
    }
    log_step("\033[92m✔ Données de marché récupérées\033[0m")
    return market_data

@CrewBase
class TradingCrew:
    def __init__(self):
        log_step("📦 Initialisation de TradingCrew...")
        self.llm = llm
        self.client = client
        self.usdt_symbols = get_usdt_tickers()
        self.market_data = get_market_data(self.usdt_symbols)

        with open("config/agents.yaml", "r") as f:
            self.agents_config = yaml.safe_load(f)
        with open("config/tasks.yaml", "r") as f:
            self.tasks_config = yaml.safe_load(f)

        self.selection_agent_prompt = None
        log_step("\033[92m✔ TradingCrew initialisé\033[0m")

    @agent
    def selection_agent(self) -> Agent:
        log_step("🤖 Création de l'agent de sélection...")
        config = self.agents_config.get("selection_agent")
        prompt_template = config.get("prompt")
        market_data_str = "\n".join(
            f"{sym}: Prix={data['price']}, Volume={data['volume']}"
            for sym, data in list(self.market_data.items())[:10]
        )
        prompt = prompt_template.replace("{market_data}", market_data_str)
        self.selection_agent_prompt = prompt
        log_step("\033[92m✔ Agent de sélection prêt\033[0m")
        return Agent(
            config={
                "role": config.get("role"),
                "goal": config.get("goal"),
                "backstory": config.get("backstory"),
                "prompt": prompt,
                "stop": config.get("stop"),
            },
            verbose=True,
            llm=self.llm
        )

    @crew
    def crew(self) -> Crew:
        log_step("🚀 Création du Crew...")
        return Crew(
            agents=[self.selection_agent()],
            process=Process.sequential,
            verbose=True
        )

    @task
    def execute_trade_task(self) -> Task:
        log_step("📡 Sélection du symbole via LLM...")
        if not self.selection_agent_prompt:
            self.selection_agent()
        if self.selection_agent_prompt is None:
            raise Exception("\033[91m[ERREUR]\033[0m L'agent de sélection n'a pas pu être créé.")

        response = self.llm.call(messages=[{"role": "user", "content": self.selection_agent_prompt}])
        chosen_symbol = response.strip().splitlines()[-1].strip().upper()
        log_step(f"🎯 Symbole sélectionné : \033[93m{chosen_symbol}\033[0m")

        if "USDT" not in chosen_symbol:
            chosen_symbol += "USDT"
            log_step(f"🔧 Correction du symbole : {chosen_symbol}")

        if not re.fullmatch(r"^[A-Z0-9\-_.]{1,20}$", chosen_symbol):
            raise Exception(f"\033[91m[ERREUR]\033[0m Symbole invalide : {chosen_symbol}")

        log_step(f"🔍 Vérification des restrictions pour {chosen_symbol}...")
        try:
            symbol_info = self.client.get_symbol_info(chosen_symbol)
            if not symbol_info:
                raise ValueError(f"\033[91m[ERREUR]\033[0m Impossible de récupérer les informations pour {chosen_symbol}.")
        except Exception as e:
            log_step(f"\033[91m[ERREUR]\033[0m Échec de la récupération des informations pour {chosen_symbol} : {e}")
            raise e

        min_notional, min_qty, max_qty, step_size = None, None, None, None
        for filter in symbol_info.get('filters', []):
            if filter['filterType'] == 'NOTIONAL':
                min_notional = float(filter['minNotional'])
            if filter['filterType'] == 'LOT_SIZE':
                min_qty = float(filter['minQty'])
                max_qty = float(filter['maxQty'])
                step_size = float(filter['stepSize'])

        price = float(self.client.get_symbol_ticker(symbol=chosen_symbol)['price'])
        min_quantity = max(min_qty, round(min_notional / price, 2))
        total_value = min_quantity * price

        if total_value < min_notional:
            min_quantity = math.ceil(min_notional / price)
            total_value = min_quantity * price
            log_step(f"🔧 Ajustement de la quantité : {min_quantity} {chosen_symbol} pour respecter la contrainte NOTIONAL.")

        if min_quantity > max_qty:
            min_quantity = max_qty

        if step_size:
            min_quantity = math.floor(min_quantity / step_size) * step_size

        log_step(f"💰 Quantité ajustée : {min_quantity} {chosen_symbol} (valeur totale : {total_value} USDT)")

        # Log ajouté avant de passer la commande
        log_step("📤 Envoi de la commande à Binance...")

        try:
            order = self.client.create_order(
                symbol=chosen_symbol,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_MARKET,
                quantity=min_quantity
            )
            log_step("\033[92m✔ Commande passée avec succès\033[0m")
            print(json.dumps(order, indent=2))
        except Exception as e:
            log_step(f"\033[91m[ERREUR]\033[0m Échec de la commande : {e}")
            return Task(
                config=self.tasks_config.get("execute_trade_task", {}),
                output_file="trade_order.json",
                description="Commande d'achat échouée",
                expected_output=str(e)
            )

        print("Commande passée :", json.dumps(order, indent=2))
        task_config = self.tasks_config.get("execute_trade_task", {})
        order_str = json.dumps(order)
        return Task(
            config=task_config,
            output_file="trade_order.json",
            description="Commande d'achat exécutée",
            expected_output=order_str
        )

def main():
    log_step("🎬 Démarrage du trading...")
    crew_instance = TradingCrew()
    crew_instance.execute_trade_task()
    log_step("✅ Trading terminé avec succès.")

if __name__ == '__main__':
    main()
