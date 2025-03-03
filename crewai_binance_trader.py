import os
import pandas as pd
import requests
from dotenv import load_dotenv
from binance.client import Client
from crewai import Crew, Agent, Task, Process
from binance.enums import ORDER_TYPE_MARKET, SIDE_BUY, SIDE_SELL
from langchain_ollama import OllamaLLM  # Utilisation correcte d'Ollama

# Charger les variables d'environnement
load_dotenv()
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_SECRET_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Initialiser le client Binance
client = Client(API_KEY, API_SECRET)

# 🔥 Initialiser Ollama sans LiteLLM
ollama_llm = OllamaLLM(
    model="deepseek-r1:14b",  # Assure-toi que c'est bien le modèle disponible
    base_url="http://localhost:11434"
)

# ✅ Fonction d'envoi d'alerte Telegram
def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)

# ✅ Récupérer toutes les paires de trading USDT
def get_all_usdt_pairs():
    exchange_info = client.get_exchange_info()
    usdt_pairs = [s['symbol'] for s in exchange_info['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
    return usdt_pairs

# ✅ Fonction pour récupérer les prix
def fetch_crypto_data(symbol, interval='1h', limit=50):
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'volume', 
                                       'close_time', 'quote_volume', 'trades', 
                                       'taker_base', 'taker_quote', 'ignore'])
    df['close'] = df['close'].astype(float)
    return df[['time', 'close']]

# ✅ Fonction pour analyser RSI et MACD
def analyze_crypto(symbol):
    df = fetch_crypto_data(symbol)
    df['rsi'] = df['close'].rolling(window=14).mean()
    df['macd'] = df['close'].ewm(span=12, adjust=False).mean() - df['close'].ewm(span=26, adjust=False).mean()
    
    last_rsi = df['rsi'].iloc[-1]
    last_macd = df['macd'].iloc[-1]
    
    if last_rsi < 30 and last_macd > 0:
        return "BUY"
    elif last_rsi > 70 and last_macd < 0:
        return "SELL"
    else:
        return "HOLD"

# ✅ Fonction pour valider avec l'IA via Ollama
def ai_manager(symbol, action):
    prompt = f"""
    Symbol: {symbol}
    Action suggérée: {action}
    
    Ton rôle est d'analyser cette action et de donner une réponse finale.
    ⚠️ Réponds uniquement par BUY, SELL ou HOLD.
    - Si la tendance est haussière et RSI < 30 → BUY.
    - Si la tendance est baissière et RSI > 70 → SELL.
    - Sinon → HOLD.
    
    Donne uniquement la réponse finale sans explication.
    """
    decision = ollama_llm.invoke(prompt).strip().upper()
    
    # Vérifier et filtrer la réponse
    valid_responses = ["BUY", "SELL", "HOLD"]
    if decision not in valid_responses:
        decision = action  # Sécuriser si l'IA renvoie autre chose
    
    # Debug: Envoyer la décision AI sur Telegram
    debug_message = f"🔍 AI Decision Debug:\nSymbol: {symbol}\nAction Suggérée: {action}\nRéponse AI: {decision}"
    print(debug_message)
    send_telegram_alert(debug_message)
    
    return decision

# ✅ Fonction pour exécuter les trades
def trade_crypto(symbol, action):
    final_action = ai_manager(symbol, action)
    if final_action == "BUY":
        client.create_order(symbol=symbol, side=SIDE_BUY, type=ORDER_TYPE_MARKET, quantity=0.001)
        send_telegram_alert(f"✅ Achat de {symbol} exécuté après validation AI !")
    elif final_action == "SELL":
        client.create_order(symbol=symbol, side=SIDE_SELL, type=ORDER_TYPE_MARKET, quantity=0.001)
        send_telegram_alert(f"❌ Vente de {symbol} exécutée après validation AI !")
    else:
        send_telegram_alert(f"⏸️ AI a annulé le trade pour {symbol}")

# ✅ Création des agents CrewAI avec Ollama uniquement
fetcher = Agent(name="DataFetcher", role="Récupérateur de données", goal="Récupérer les prix des cryptos", backstory="Expert en extraction de données", llm=ollama_llm)
analyst = Agent(name="Analyst", role="Analyste de marché", goal="Analyser les tendances", backstory="Spécialiste en trading algorithmique", llm=ollama_llm)
manager = Agent(name="AI Manager", role="Validateur de trades", goal="Vérifier les décisions de trading avec l'IA", backstory="IA avancée utilisant DeepSeek", llm=ollama_llm)
trader = Agent(name="Trader", role="Exécuteur d'ordres", goal="Acheter et vendre les cryptos", backstory="Stratège financier", llm=ollama_llm)

# ✅ Lancer CrewAI avec Ollama uniquement
def run_trading():
    symbols = get_all_usdt_pairs()
    for symbol in symbols[:5]:  # Limiter à 5 pour éviter un trop grand nombre d'appels
        print(f"🚀 Trading en cours pour {symbol}")
        crew = Crew(agents=[fetcher, analyst, manager, trader], tasks=[
            Task(description=f"Analyser et trader {symbol}", agent=manager, expected_output="BUY/SELL/HOLD"),
        ], process=Process.sequential)
        crew.kickoff()
    return "✅ Trading terminé sur toutes les cryptos."

if __name__ == "__main__":
    result = run_trading()
    print(result)
