#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per calcolare la volatilità di un simbolo tramite MT5 Keeper.

Questo script calcola l'ATR (Average True Range) per un simbolo e timeframe specificati,
categorizza la volatilità (bassa/media/alta) e suggerisce valori per stop loss e take profit.
"""

import sys
import json
import argparse
import datetime
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
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

class MT5CalculateVolatility(MT5CommandBase):
    """
    Classe per calcolare la volatilità di un simbolo.
    """
    
    # Cache per i dati di volatilità
    _cache = {}
    
    @staticmethod
    def parse_args() -> argparse.Namespace:
        """
        Analizza gli argomenti della linea di comando.
        
        Returns:
            Namespace con gli argomenti
        """
        parser = argparse.ArgumentParser(
            description="Calcola la volatilità di un simbolo tramite MT5 Keeper",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument("symbol", help="Simbolo da analizzare (es. EURUSD)")
        parser.add_argument("timeframe", help=f"Timeframe ({', '.join(TIMEFRAME_MAP.keys())})")
        parser.add_argument("-c", "--config", help="Percorso al file di configurazione JSON")
        parser.add_argument("-d", "--debug", action="store_true", help="Attiva modalità debug")
        parser.add_argument("--cache", action="store_true", help="Utilizza la cache per i dati")
        parser.add_argument("--period", type=int, default=14, help="Periodo per il calcolo dell'ATR")
        parser.add_argument("--num-candles", type=int, default=100, help="Numero di candele da ottenere")
        parser.add_argument("--risk-factor", type=float, default=1.5, help="Fattore di rischio per SL/TP (1.0-3.0)")
        
        return parser.parse_args()
    
    @classmethod
    def get_cache_key(cls, symbol: str, timeframe: str, period: int) -> str:
        """
        Genera una chiave per la cache.
        
        Args:
            symbol: Simbolo
            timeframe: Timeframe
            period: Periodo ATR
            
        Returns:
            Chiave per la cache
        """
        return f"{symbol}_{timeframe}_ATR{period}"
    
    @classmethod
    def get_from_cache(cls, key: str) -> Optional[Dict[str, Any]]:
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
    def add_to_cache(cls, key: str, data: Dict[str, Any]) -> None:
        """
        Aggiunge dati alla cache.
        
        Args:
            key: Chiave per la cache
            data: Dati da aggiungere
        """
        cls._cache[key] = (datetime.datetime.now(), data)
    
    @staticmethod
    def calculate_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Calcola l'indicatore ATR (Average True Range).
        
        Formula:
        TR = max(High - Low, |High - Close_prev|, |Low - Close_prev|)
        ATR = EMA(TR, period)
        
        Args:
            high: Array di prezzi massimi
            low: Array di prezzi minimi
            close: Array di prezzi di chiusura
            period: Periodo per il calcolo
            
        Returns:
            Array con i valori dell'ATR
        """
        if len(high) <= period:
            return np.array([])
        
        # Calcola True Range
        tr = np.zeros(len(high))
        
        for i in range(1, len(high)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr[i] = max(hl, hc, lc)
        
        # Calcola ATR
        atr = np.zeros(len(high))
        
        # Inizializza il primo ATR con SMA
        atr[period] = np.mean(tr[1:period+1])
        
        # Calcola i valori successivi con EMA
        for i in range(period+1, len(high)):
            atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
        
        return atr
    
    @staticmethod
    def categorize_volatility(atr_value: float, avg_price: float) -> str:
        """
        Categorizza la volatilità in base al valore ATR.
        
        Args:
            atr_value: Valore ATR
            avg_price: Prezzo medio
            
        Returns:
            Categoria di volatilità (bassa, media, alta)
        """
        # Calcola la percentuale di ATR rispetto al prezzo medio
        atr_percent = (atr_value / avg_price) * 100
        
        if atr_percent < 0.1:
            return "bassa"
        elif atr_percent < 0.3:
            return "media"
        else:
            return "alta"
    
    @staticmethod
    def suggest_sl_tp(atr_value: float, category: str, risk_factor: float, is_forex: bool) -> Tuple[float, float]:
        """
        Suggerisce valori per stop loss e take profit in base alla volatilità.
        
        Args:
            atr_value: Valore ATR
            category: Categoria di volatilità
            risk_factor: Fattore di rischio
            is_forex: True se il simbolo è una coppia forex
            
        Returns:
            Tuple con stop loss e take profit suggeriti
        """
        # Moltiplica ATR per un fattore basato sulla categoria di volatilità
        if category == "bassa":
            sl_multiplier = 1.5 * risk_factor
            tp_multiplier = 2.0 * risk_factor
        elif category == "media":
            sl_multiplier = 2.0 * risk_factor
            tp_multiplier = 3.0 * risk_factor
        else:  # alta
            sl_multiplier = 2.5 * risk_factor
            tp_multiplier = 4.0 * risk_factor
        
        # Calcola SL e TP
        sl = atr_value * sl_multiplier
        tp = atr_value * tp_multiplier
        
        # Arrotonda i valori in base al tipo di simbolo
        if is_forex:
            # Per forex, arrotonda a 5 decimali
            sl = round(sl, 5)
            tp = round(tp, 5)
        else:
            # Per altri simboli, arrotonda a 2 decimali
            sl = round(sl, 2)
            tp = round(tp, 2)
        
        return sl, tp
    
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
    
    @classmethod
    def run(cls) -> None:
        """
        Esegue il calcolo della volatilità.
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
        
        # Validazione risk_factor
        if args.risk_factor < 0.5 or args.risk_factor > 3.0:
            print(json.dumps({
                "success": False,
                "error": "Fattore di rischio deve essere compreso tra 0.5 e 3.0"
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
            cache_key = cls.get_cache_key(args.symbol, args.timeframe, args.period)
            cached_data = cls.get_from_cache(cache_key)
            if cached_data:
                print(json.dumps({
                    "success": True,
                    "symbol": args.symbol,
                    "timeframe": args.timeframe,
                    "from_cache": True,
                    "data": cached_data
                }, indent=2))
                return
        
        try:
            # Creazione istanza
            cmd = cls(args.config)
            
            # Ottieni dati storici
            num_candles = max(args.num_candles, args.period + 50)
            
            # Invia comando per ottenere dati storici
            rates = cmd.send_command("copy_rates_from", {
                "symbol": args.symbol,
                "timeframe": timeframe,
                "count": num_candles
            })
            
            if not rates:
                raise ValueError(f"Nessun dato storico disponibile per {args.symbol}")
            
            # Estrai array di prezzi
            high = np.array([rate[2] for rate in rates])  # HIGH_IDX = 2
            low = np.array([rate[3] for rate in rates])   # LOW_IDX = 3
            close = np.array([rate[4] for rate in rates]) # CLOSE_IDX = 4
            
            # Calcola prezzo medio
            avg_price = np.mean(close[-20:])  # Media degli ultimi 20 prezzi di chiusura
            
            # Calcola ATR
            atr_values = cls.calculate_atr(high, low, close, args.period)
            
            # Ottieni l'ultimo valore ATR
            current_atr = float(atr_values[-1])
            
            # Categorizza volatilità
            volatility_category = cls.categorize_volatility(current_atr, avg_price)
            
            # Verifica se il simbolo è forex
            is_forex_symbol = cls.is_forex(args.symbol)
            
            # Suggerisci SL e TP
            sl, tp = cls.suggest_sl_tp(current_atr, volatility_category, args.risk_factor, is_forex_symbol)
            
            # Prepara risultato
            result_data = {
                "symbol": args.symbol,
                "timeframe": args.timeframe,
                "atr_period": args.period,
                "atr_value": round(current_atr, 5),
                "volatility_category": volatility_category,
                "avg_price": round(avg_price, 5),
                "suggested_sl_points": round(sl / (10**-5 if is_forex_symbol else 10**-2)),
                "suggested_tp_points": round(tp / (10**-5 if is_forex_symbol else 10**-2)),
                "suggested_sl_price": round(sl, 5),
                "suggested_tp_price": round(tp, 5),
                "risk_factor": args.risk_factor,
                "is_forex": is_forex_symbol,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            # Aggiungi alla cache se richiesto
            if args.cache and cache_key:
                cls.add_to_cache(cache_key, result_data)
            
            # Formatta e stampa risultato
            output = {
                "success": True,
                "symbol": args.symbol,
                "timeframe": args.timeframe,
                "from_cache": False,
                "data": result_data
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
    MT5CalculateVolatility.run()
