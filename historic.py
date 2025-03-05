#!/usr/bin/env python3
import os
from binance.client import Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

def log(message):
    """Affiche un log avec timestamp."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def list_trade_history_last_hour(client, symbol, limit=10):
    """
    Récupère l'historique des transactions depuis la dernière heure pour un symbole donné.
    
    :param client: Instance du client Binance
    :param symbol: Symbole de la crypto-monnaie (ex: 'BTCUSDT')
    :param limit: Nombre maximum d'ordres à récupérer
    :return: Liste des transactions passées dans la dernière heure
    """
    log(f"Récupération de l'historique des transactions pour {symbol} depuis la dernière heure...")
    
    try:
        # Calcul de la limite de temps (1 heure en arrière)
        one_hour_ago = datetime.now() - timedelta(hours=1)
        one_hour_timestamp = int(one_hour_ago.timestamp() * 1000)  # Convertir en millisecondes
        
        # Récupération de l'historique des ordres
        trades = client.get_my_trades(symbol=symbol, limit=limit)
        
        if not trades:
            log(f"Aucune transaction trouvée pour {symbol}.")
            return []
        
        recent_trades = []
        
        # Filtrer les transactions pour n'inclure que celles qui ont eu lieu dans la dernière heure
        for trade in trades:
            trade_time = datetime.fromtimestamp(trade['time'] / 1000)  # Convertir timestamp en datetime
            if trade_time >= one_hour_ago:
                recent_trades.append(trade)
        
        if not recent_trades:
            log(f"Aucune transaction trouvée dans la dernière heure pour {symbol}.")
            return []

        # Affichage de l'historique des transactions récentes
        for trade in recent_trades:
            print(f"Date: {datetime.fromtimestamp(trade['time'] / 1000)}")
            print(f"Type: {trade['side']}")  # 'BUY' ou 'SELL'
            print(f"Quantité: {trade['qty']} {symbol}")
            print(f"Prix: {trade['price']} {symbol}")
            print(f"Total: {float(trade['qty']) * float(trade['price'])} USDT")
            print("-" * 50)
        
        return recent_trades
    except Exception as e:
        log(f"Erreur lors de la récupération de l'historique des transactions pour {symbol}: {e}")
        return []

def get_all_pairs(client):
    """
    Récupère toutes les paires de trading disponibles sur Binance.
    
    :param client: Instance du client Binance
    :return: Liste des paires de trading
    """
    try:
        exchange_info = client.get_exchange_info()
        symbols = exchange_info['symbols']
        pairs = [symbol['symbol'] for symbol in symbols if symbol['status'] == 'TRADING']
        return pairs
    except Exception as e:
        log(f"Erreur lors de la récupération des paires de trading: {e}")
        return []

def main():
    # Chargement des variables d'environnement
    load_dotenv("creds.env")
    BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
    BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET")
    
    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        raise Exception("Merci de définir BINANCE_API_KEY et BINANCE_API_SECRET dans creds.env")
    
    # Initialisation du client Binance (testnet peut être désactivé si besoin)
    client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=True)
    
    log("Récupération de toutes les paires de crypto-monnaies disponibles...")
    pairs = get_all_pairs(client)
    
    if not pairs:
        log("Aucune paire de trading trouvée.")
        return
    
    # Boucle sur toutes les paires de trading
    for pair in pairs:
        log(f"Récupération de l'historique des transactions pour {pair}...")
        list_trade_history_last_hour(client, pair)

if __name__ == "__main__":
    main()
