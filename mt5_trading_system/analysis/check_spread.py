#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per verificare lo spread di un simbolo tramite MT5 Keeper.

Questo script ottiene informazioni sul simbolo tramite MT5 Keeper e verifica
lo spread attuale, fornendo una valutazione (basso/medio/alto).
"""

import sys
import json
import argparse
import datetime
from typing import Dict, Any, Optional, List
import os

# Importa direttamente il modulo mt5_command_base.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from mt5_trading_system.core.mt5_command_base import MT5CommandBase

class MT5CheckSpread(MT5CommandBase):
    """
    Classe per verificare lo spread di un simbolo.
    """
    
    # Cache per i dati di spread
    _cache = {}
    
    # Categorie di spread per diversi tipi di simboli
    SPREAD_CATEGORIES = {
        "forex_major": {
            "low": 1.0,    # Spread <= 1.0 pips è considerato basso
            "medium": 2.0  # Spread <= 2.0 pips è considerato medio, altrimenti alto
        },
        "forex_minor": {
            "low": 1.5,    # Spread <= 1.5 pips è considerato basso
            "medium": 3.0  # Spread <= 3.0 pips è considerato medio, altrimenti alto
        },
        "forex_exotic": {
            "low": 3.0,    # Spread <= 3.0 pips è considerato basso
            "medium": 6.0  # Spread <= 6.0 pips è considerato medio, altrimenti alto
        },
        "indices": {
            "low": 0.5,    # Spread <= 0.5 punti è considerato basso
            "medium": 1.0  # Spread <= 1.0 punti è considerato medio, altrimenti alto
        },
        "commodities": {
            "low": 0.03,   # Spread <= 0.03% è considerato basso
            "medium": 0.06 # Spread <= 0.06% è considerato medio, altrimenti alto
        },
        "crypto": {
            "low": 0.1,    # Spread <= 0.1% è considerato basso
            "medium": 0.3  # Spread <= 0.3% è considerato medio, altrimenti alto
        },
        "stocks": {
            "low": 0.05,   # Spread <= 0.05% è considerato basso
            "medium": 0.1  # Spread <= 0.1% è considerato medio, altrimenti alto
        },
        "default": {
            "low": 0.05,   # Spread <= 0.05% è considerato basso
            "medium": 0.1  # Spread <= 0.1% è considerato medio, altrimenti alto
        }
    }
    
    # Mappatura delle valute principali
    MAJOR_CURRENCIES = ["EUR", "USD", "JPY", "GBP", "AUD", "CAD", "CHF", "NZD"]
    
    # Mappatura delle coppie forex principali
    MAJOR_PAIRS = [
        "EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "USDCHF", "USDCAD", "NZDUSD",
        "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURCAD", "GBPJPY"
    ]
    
    @staticmethod
    def parse_args() -> argparse.Namespace:
        """
        Analizza gli argomenti della linea di comando.
        
        Returns:
            Namespace con gli argomenti
        """
        parser = argparse.ArgumentParser(
            description="Verifica lo spread di un simbolo tramite MT5 Keeper",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument("symbol", help="Simbolo da analizzare (es. EURUSD)")
        parser.add_argument("-c", "--config", help="Percorso al file di configurazione JSON")
        parser.add_argument("-d", "--debug", action="store_true", help="Attiva modalità debug")
        parser.add_argument("--cache", action="store_true", help="Utilizza la cache per i dati")
        parser.add_argument("--type", choices=["forex_major", "forex_minor", "forex_exotic", "indices", "commodities", "crypto", "stocks"],
                           help="Tipo di simbolo (se non specificato, viene rilevato automaticamente)")
        
        return parser.parse_args()
    
    @classmethod
    def get_cache_key(cls, symbol: str) -> str:
        """
        Genera una chiave per la cache.
        
        Args:
            symbol: Simbolo
            
        Returns:
            Chiave per la cache
        """
        return f"{symbol}_spread"
    
    @classmethod
    def get_from_cache(cls, key: str) -> Optional[Dict[str, Any]]:
        """
        Ottiene dati dalla cache.
        
        Args:
            key: Chiave per la cache
            
        Returns:
            Dati dalla cache o None se non presenti
        """
        # Verifica se i dati sono nella cache e se sono ancora validi (max 30 secondi per lo spread)
        if key in cls._cache:
            cache_time, data = cls._cache[key]
            if (datetime.datetime.now() - cache_time).total_seconds() < 30:  # 30 secondi
                return data
        return None
    
    @classmethod
    def add_to_cache(cls, key: str, data: Dict[str, Any]) -> None:
        """
        Aggiunge dati alla cache.
        
        Args:
            key: Chiave per la cache
            data: Dati da aggiungere
        """
        cls._cache[key] = (datetime.datetime.now(), data)
    
    @classmethod
    def detect_symbol_type(cls, symbol: str, symbol_info: Dict[str, Any]) -> str:
        """
        Rileva il tipo di simbolo.
        
        Args:
            symbol: Simbolo
            symbol_info: Informazioni sul simbolo
            
        Returns:
            Tipo di simbolo
        """
        # Verifica se è una coppia forex
        if cls.is_forex(symbol):
            # Verifica se è una coppia principale
            if symbol in cls.MAJOR_PAIRS:
                return "forex_major"
            
            # Verifica se è una coppia minore (entrambe le valute sono principali)
            currencies = cls.extract_currencies(symbol)
            if currencies and all(curr in cls.MAJOR_CURRENCIES for curr in currencies):
                return "forex_minor"
            
            # Altrimenti è una coppia esotica
            return "forex_exotic"
        
        # Verifica se è un indice
        if "index" in symbol.lower() or symbol.startswith("^") or symbol in ["US30", "US500", "NAS100", "GER30", "UK100", "FRA40", "JPN225"]:
            return "indices"
        
        # Verifica se è una commodity
        if symbol in ["XAUUSD", "XAGUSD", "XPDUSD", "XPTUSD"] or symbol.startswith("OIL") or symbol in ["NATGAS", "COPPER"]:
            return "commodities"
        
        # Verifica se è una crypto
        if symbol.endswith("USD") and symbol[:-3] in ["BTC", "ETH", "LTC", "XRP", "BCH", "EOS", "XLM", "ADA", "TRX", "DASH"]:
            return "crypto"
        
        # Verifica se è un'azione
        if "." in symbol or symbol_info.get("path", "").startswith("Stocks"):
            return "stocks"
        
        # Default
        return "default"
    
    @staticmethod
    def is_forex(symbol: str) -> bool:
        """
        Verifica se un simbolo è una coppia forex.
        
        Args:
            symbol: Simbolo da verificare
            
        Returns:
            True se il simbolo è una coppia forex
        """
        # Simboli forex tipici hanno 6-8 caratteri e contengono solo lettere
        if len(symbol) >= 6 and len(symbol) <= 8 and symbol.isalpha():
            # Verifica se contiene valute comuni
            common_currencies = ["USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"]
            for curr in common_currencies:
                if curr in symbol:
                    return True
        return False
    
    @staticmethod
    def extract_currencies(symbol: str) -> Optional[List[str]]:
        """
        Estrae le valute da una coppia forex.
        
        Args:
            symbol: Simbolo da analizzare
            
        Returns:
            Lista di valute o None se non è una coppia forex
        """
        if len(symbol) == 6:
            return [symbol[:3], symbol[3:]]
        return None
    
    @classmethod
    def categorize_spread(cls, spread_points: float, symbol_type: str, point_value: float) -> str:
        """
        Categorizza lo spread in base al tipo di simbolo.
        
        Args:
            spread_points: Spread in punti
            symbol_type: Tipo di simbolo
            point_value: Valore di un punto
            
        Returns:
            Categoria di spread (basso, medio, alto)
        """
        # Ottieni le soglie per il tipo di simbolo
        thresholds = cls.SPREAD_CATEGORIES.get(symbol_type, cls.SPREAD_CATEGORIES["default"])
        
        # Converti spread in pips per forex
        if symbol_type.startswith("forex"):
            spread_pips = spread_points * point_value * 10
            
            if spread_pips <= thresholds["low"]:
                return "basso"
            elif spread_pips <= thresholds["medium"]:
                return "medio"
            else:
                return "alto"
        
        # Per altri simboli, usa lo spread in punti o percentuale
        if symbol_type in ["indices", "commodities"]:
            spread_value = spread_points * point_value
        else:
            # Per crypto e stocks, usa percentuale
            spread_value = (spread_points * point_value) * 100  # Converti in percentuale
        
        if spread_value <= thresholds["low"]:
            return "basso"
        elif spread_value <= thresholds["medium"]:
            return "medio"
        else:
            return "alto"
    
    @staticmethod
    def get_spread_evaluation(category: str) -> str:
        """
        Fornisce una valutazione dello spread.
        
        Args:
            category: Categoria di spread
            
        Returns:
            Valutazione dello spread
        """
        if category == "basso":
            return "Ottimo spread, ideale per trading ad alta frequenza e scalping."
        elif category == "medio":
            return "Spread accettabile, adatto per swing trading e posizioni intraday."
        else:
            return "Spread elevato, consigliato per trading a lungo termine o in condizioni di mercato normali."
    
    @classmethod
    def run(cls) -> None:
        """
        Esegue la verifica dello spread.
        """
        # Parsing argomenti
        args = cls.parse_args()
        
        # Imposta debug se richiesto
        if args.debug:
            import logging
            logging.getLogger("MT5Command").setLevel(logging.DEBUG)
            logging.getLogger("MT5Command").debug("Modalità debug attivata")
        
        # Verifica cache
        cache_key = None
        if args.cache:
            cache_key = cls.get_cache_key(args.symbol)
            cached_data = cls.get_from_cache(cache_key)
            if cached_data:
                print(json.dumps({
                    "success": True,
                    "symbol": args.symbol,
                    "from_cache": True,
                    "data": cached_data
                }, indent=2))
                return
        
        try:
            # Creazione istanza
            cmd = cls(args.config)
            
            # Ottieni informazioni sul simbolo
            symbol_info = cmd.send_command("symbol_info", {
                "symbol": args.symbol
            })
            
            if not symbol_info:
                raise ValueError(f"Simbolo non trovato: {args.symbol}")
            
            # Ottieni tick corrente
            tick_info = cmd.send_command("symbol_info_tick", {
                "symbol": args.symbol
            })
            
            if not tick_info:
                raise ValueError(f"Impossibile ottenere tick per: {args.symbol}")
            
            # Estrai informazioni rilevanti
            point = symbol_info.get("point", 0.00001)  # Valore di un punto
            digits = symbol_info.get("digits", 5)      # Numero di decimali
            spread_points = symbol_info.get("spread", 0)  # Spread in punti
            
            # Se lo spread è 0, calcolalo dalla differenza tra ask e bid
            if spread_points == 0 and "ask" in tick_info and "bid" in tick_info:
                ask = tick_info["ask"]
                bid = tick_info["bid"]
                spread_points = round((ask - bid) / point)
            
            # Determina il tipo di simbolo
            symbol_type = args.type or cls.detect_symbol_type(args.symbol, symbol_info)
            
            # Categorizza lo spread
            spread_category = cls.categorize_spread(spread_points, symbol_type, point)
            
            # Ottieni valutazione
            evaluation = cls.get_spread_evaluation(spread_category)
            
            # Calcola spread in pips per forex
            spread_pips = None
            if symbol_type.startswith("forex"):
                spread_pips = spread_points * (10 ** (digits - 4))
            
            # Calcola spread in percentuale
            spread_percent = (spread_points * point) * 100
            
            # Prepara risultato
            result_data = {
                "symbol": args.symbol,
                "symbol_type": symbol_type,
                "spread_points": spread_points,
                "spread_pips": spread_pips if spread_pips is not None else None,
                "spread_percent": round(spread_percent, 6),
                "point_value": point,
                "digits": digits,
                "ask": tick_info.get("ask", 0),
                "bid": tick_info.get("bid", 0),
                "category": spread_category,
                "evaluation": evaluation,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Aggiungi alla cache se richiesto
            if args.cache and cache_key:
                cls.add_to_cache(cache_key, result_data)
            
            # Formatta e stampa risultato
            output = {
                "success": True,
                "symbol": args.symbol,
                "from_cache": False,
                "data": result_data
            }
            
            print(json.dumps(output, indent=2))
            
        except Exception as e:
            # Gestione errori
            output = {
                "success": False,
                "error": str(e),
                "symbol": args.symbol
            }
            
            print(json.dumps(output, indent=2))
            sys.exit(1)


if __name__ == "__main__":
    MT5CheckSpread.run()
