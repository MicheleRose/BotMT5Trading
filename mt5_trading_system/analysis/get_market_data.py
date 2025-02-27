#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per ottenere dati storici di mercato tramite MT5 Keeper.

Questo script invia un comando al MT5 Keeper per ottenere dati storici OHLCV
(Open, High, Low, Close, Volume) per un simbolo e timeframe specificati.
"""

import sys
import json
import argparse
import datetime
from typing import Dict, Any, Optional, List
import sys
import os

# Importa direttamente il modulo mt5_command_base.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from mt5_trading_system.core.mt5_command_base import MT5CommandBase

# Dizionario per la conversione dei timeframe da stringa a costante MT5
TIMEFRAME_MAP = {
    "M1": "TIMEFRAME_M1",     # 1 minuto
    "M2": "TIMEFRAME_M2",     # 2 minuti
    "M3": "TIMEFRAME_M3",     # 3 minuti
    "M4": "TIMEFRAME_M4",     # 4 minuti
    "M5": "TIMEFRAME_M5",     # 5 minuti
    "M6": "TIMEFRAME_M6",     # 6 minuti
    "M10": "TIMEFRAME_M10",   # 10 minuti
    "M12": "TIMEFRAME_M12",   # 12 minuti
    "M15": "TIMEFRAME_M15",   # 15 minuti
    "M20": "TIMEFRAME_M20",   # 20 minuti
    "M30": "TIMEFRAME_M30",   # 30 minuti
    "H1": "TIMEFRAME_H1",     # 1 ora
    "H2": "TIMEFRAME_H2",     # 2 ore
    "H3": "TIMEFRAME_H3",     # 3 ore
    "H4": "TIMEFRAME_H4",     # 4 ore
    "H6": "TIMEFRAME_H6",     # 6 ore
    "H8": "TIMEFRAME_H8",     # 8 ore
    "H12": "TIMEFRAME_H12",   # 12 ore
    "D1": "TIMEFRAME_D1",     # 1 giorno
    "W1": "TIMEFRAME_W1",     # 1 settimana
    "MN1": "TIMEFRAME_MN1"    # 1 mese
}

class MT5GetMarketData(MT5CommandBase):
    """
    Classe per ottenere dati storici di mercato.
    """
    
    # Cache per i dati di mercato
    _cache = {}
    
    @staticmethod
    def parse_args() -> argparse.Namespace:
        """
        Analizza gli argomenti della linea di comando.
        
        Returns:
            Namespace con gli argomenti
        """
        parser = argparse.ArgumentParser(
            description="Ottiene dati storici di mercato tramite MT5 Keeper",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument("symbol", help="Simbolo da analizzare (es. EURUSD)")
        parser.add_argument("timeframe", help=f"Timeframe ({', '.join(TIMEFRAME_MAP.keys())})")
        parser.add_argument("num_candles", type=int, help="Numero di candele da ottenere")
        parser.add_argument("-c", "--config", help="Percorso al file di configurazione JSON")
        parser.add_argument("-d", "--debug", action="store_true", help="Attiva modalità debug")
        parser.add_argument("--cache", action="store_true", help="Utilizza la cache per i dati")
        parser.add_argument("--from-date", help="Data di inizio (formato ISO: YYYY-MM-DD)")
        
        return parser.parse_args()
    
    @classmethod
    def get_cache_key(cls, symbol: str, timeframe: str, num_candles: int, from_date: Optional[str] = None) -> str:
        """
        Genera una chiave per la cache.
        
        Args:
            symbol: Simbolo
            timeframe: Timeframe
            num_candles: Numero di candele
            from_date: Data di inizio (opzionale)
            
        Returns:
            Chiave per la cache
        """
        return f"{symbol}_{timeframe}_{num_candles}_{from_date}"
    
    @classmethod
    def get_from_cache(cls, key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Ottiene dati dalla cache.
        
        Args:
            key: Chiave per la cache
            
        Returns:
            Dati dalla cache o None se non presenti
        """
        # Verifica se i dati sono nella cache e se sono ancora validi (max 5 minuti)
        if key in cls._cache:
            cache_time, data = cls._cache[key]
            if (datetime.datetime.now() - cache_time).total_seconds() < 300:  # 5 minuti
                return data
        return None
    
    @classmethod
    def add_to_cache(cls, key: str, data: List[Dict[str, Any]]) -> None:
        """
        Aggiunge dati alla cache.
        
        Args:
            key: Chiave per la cache
            data: Dati da aggiungere
        """
        cls._cache[key] = (datetime.datetime.now(), data)
    
    @classmethod
    def run(cls) -> None:
        """
        Esegue la richiesta di dati storici di mercato.
        """
        # Parsing argomenti
        args = cls.parse_args()
        
        # Validazione timeframe
        if args.timeframe not in TIMEFRAME_MAP:
            print(json.dumps({
                "success": False,
                "error": f"Timeframe non valido. Valori consentiti: {', '.join(TIMEFRAME_MAP.keys())}"
            }, indent=2))
            sys.exit(1)
        
        # Conversione timeframe
        timeframe = TIMEFRAME_MAP[args.timeframe]
        
        # Validazione num_candles
        if args.num_candles <= 0:
            print(json.dumps({
                "success": False,
                "error": "Il numero di candele deve essere maggiore di zero"
            }, indent=2))
            sys.exit(1)
        
        # Conversione from_date
        from_date = None
        if args.from_date:
            try:
                from_date = datetime.datetime.fromisoformat(args.from_date)
            except ValueError:
                print(json.dumps({
                    "success": False,
                    "error": "Formato data non valido. Utilizzare il formato ISO: YYYY-MM-DD"
                }, indent=2))
                sys.exit(1)
        
        # Imposta debug se richiesto
        if args.debug:
            import logging
            logging.getLogger("MT5Command").setLevel(logging.DEBUG)
            logging.getLogger("MT5Command").debug("Modalità debug attivata")
        
        # Verifica cache
        cache_key = None
        if args.cache:
            cache_key = cls.get_cache_key(args.symbol, args.timeframe, args.num_candles, args.from_date)
            cached_data = cls.get_from_cache(cache_key)
            if cached_data:
                print(json.dumps({
                    "success": True,
                    "symbol": args.symbol,
                    "timeframe": args.timeframe,
                    "num_candles": args.num_candles,
                    "from_cache": True,
                    "data": cached_data
                }, indent=2))
                return
        
        try:
            # Creazione istanza
            cmd = cls(args.config)
            
            # Prepara parametri
            params = {
                "symbol": args.symbol,
                "timeframe": timeframe,
                "count": args.num_candles
            }
            
            # Aggiungi from_date se specificato
            if from_date:
                params["date_from"] = from_date.isoformat()
            
            # Invia comando
            result = cmd.send_command("copy_rates_from", params)
            
            # Formatta i dati
            formatted_data = []
            for rate in result:
                # Converti timestamp in data leggibile
                time_str = datetime.datetime.fromtimestamp(rate[0]).isoformat()
                
                # Formatta candela
                candle = {
                    "time": time_str,
                    "open": rate[1],
                    "high": rate[2],
                    "low": rate[3],
                    "close": rate[4],
                    "tick_volume": rate[5],
                    "spread": rate[6],
                    "real_volume": rate[7]
                }
                formatted_data.append(candle)
            
            # Aggiungi alla cache se richiesto
            if args.cache and cache_key:
                cls.add_to_cache(cache_key, formatted_data)
            
            # Formatta e stampa risultato
            output = {
                "success": True,
                "symbol": args.symbol,
                "timeframe": args.timeframe,
                "num_candles": args.num_candles,
                "from_cache": False,
                "data": formatted_data
            }
            
            print(json.dumps(output, indent=2))
            
        except Exception as e:
            # Gestione errori
            output = {
                "success": False,
                "error": str(e),
                "symbol": args.symbol,
                "timeframe": args.timeframe
            }
            
            print(json.dumps(output, indent=2))
            sys.exit(1)


if __name__ == "__main__":
    MT5GetMarketData.run()
