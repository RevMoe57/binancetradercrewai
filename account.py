#!/usr/bin/env python3
import os
from binance.client import Client
from dotenv import load_dotenv
from datetime import datetime

def log(message):
    """Affiche un log avec timestamp."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

def list_shitcoins(client):
    """
    Récupère les actifs de votre compte Binance et retourne une liste
    des crypto-monnaies considérées comme 'shitcoins' (c'est-à-dire
    excluant les grandes cryptos majeures).
    """
    # Récupération des informations du compte
    account_info = client.get_account()
    balances = account_info.get("balances", [])
    
    # Liste des grandes cryptos à exclure
    major_coins = {"BTC", "ETH", "BNB", "USDT", "BUSD", "USDC", "TUSD", "PAX"}
    
    shitcoins = []
    for asset in balances:
        asset_name = asset["asset"]
        free = float(asset["free"])
        locked = float(asset["locked"])
        total = free + locked
        # Considérer uniquement les actifs avec un solde non nul et hors major coins
        if total > 0 and asset_name not in major_coins:
            shitcoins.append((asset_name, total))
    
    return shitcoins

def main():
    # Chargement des variables d'environnement
    load_dotenv("creds.env")
    BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY")
    BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET")
    if not BINANCE_API_KEY or not BINANCE_API_SECRET:
        raise Exception("Merci de définir BINANCE_API_KEY et BINANCE_API_SECRET dans creds.env")
    
    # Initialisation du client Binance (testnet peut être désactivé si besoin)
    client = Client(BINANCE_API_KEY, BINANCE_API_SECRET, testnet=True)
    
    log("Récupération des actifs de votre compte...")
    shitcoins = list_shitcoins(client)
    
    if shitcoins:
        log("Voici la liste des crypto 'shitcoins' que vous possédez :")
        for coin, amount in shitcoins:
            print(f" - {coin}: {amount}")
    else:
        log("Aucun actif considéré comme 'shitcoin' n'a été trouvé dans votre compte.")

if __name__ == "__main__":
    main()
