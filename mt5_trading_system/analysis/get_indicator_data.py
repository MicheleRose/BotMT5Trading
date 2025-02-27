#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per calcolare indicatori tecnici tramite MT5 Keeper.

Questo script ottiene dati storici tramite MT5 Keeper e calcola vari indicatori tecnici
come RSI, MACD, Bollinger Bands, ADX, Stochastic e ATR.
"""

import sys
import json
import argparse
import datetime
import numpy as np
from typing import Dict, Any, Optional, List, Tuple, Callable
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

# Indicatori supportati
SUPPORTED_INDICATORS = ["RSI", "MACD", "BOLLINGER", "ADX", "STOCHASTIC", "ATR"]

class MT5GetIndicatorData(MT5CommandBase):
    """
    Classe per calcolare indicatori tecnici.
    """
    
    # Cache per i dati degli indicatori
    _cache = {}
    
    @staticmethod
    def parse_args() -> argparse.Namespace:
        """
        Analizza gli argomenti della linea di comando.
        
        Returns:
            Namespace con gli argomenti
        """
        parser = argparse.ArgumentParser(
            description="Calcola indicatori tecnici tramite MT5 Keeper",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument("symbol", help="Simbolo da analizzare (es. EURUSD)")
        parser.add_argument("timeframe", help=f"Timeframe ({', '.join(TIMEFRAME_MAP.keys())})")
        parser.add_argument("indicator", help=f"Indicatore ({', '.join(SUPPORTED_INDICATORS)})")
        parser.add_argument("-c", "--config", help="Percorso al file di configurazione JSON")
        parser.add_argument("-d", "--debug", action="store_true", help="Attiva modalità debug")
        parser.add_argument("--cache", action="store_true", help="Utilizza la cache per i dati")
        parser.add_argument("--period", type=int, help="Periodo per l'indicatore (es. 14 per RSI)")
        parser.add_argument("--fast-period", type=int, help="Periodo veloce per MACD (es. 12)")
        parser.add_argument("--slow-period", type=int, help="Periodo lento per MACD (es. 26)")
        parser.add_argument("--signal-period", type=int, help="Periodo segnale per MACD (es. 9)")
        parser.add_argument("--deviation", type=float, help="Deviazione per Bollinger Bands (es. 2.0)")
        parser.add_argument("--k-period", type=int, help="Periodo %K per Stochastic (es. 14)")
        parser.add_argument("--d-period", type=int, help="Periodo %D per Stochastic (es. 3)")
        parser.add_argument("--slowing", type=int, help="Rallentamento per Stochastic (es. 3)")
        parser.add_argument("--price-type", choices=["CLOSE", "OPEN", "HIGH", "LOW", "HL2", "HLC3", "OHLC4"], 
                           help="Tipo di prezzo da utilizzare (default: CLOSE)")
        parser.add_argument("--num-candles", type=int, default=200, 
                           help="Numero di candele da ottenere per il calcolo")
        
        return parser.parse_args()
    
    @classmethod
    def get_cache_key(cls, symbol: str, timeframe: str, indicator: str, params: Dict[str, Any]) -> str:
        """
        Genera una chiave per la cache.
        
        Args:
            symbol: Simbolo
            timeframe: Timeframe
            indicator: Indicatore
            params: Parametri dell'indicatore
            
        Returns:
            Chiave per la cache
        """
        params_str = "_".join(f"{k}={v}" for k, v in sorted(params.items()))
        return f"{symbol}_{timeframe}_{indicator}_{params_str}"
    
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
    def get_price_array(rates: List[List[float]], price_type: str) -> np.ndarray:
        """
        Estrae un array di prezzi dai dati delle candele.
        
        Args:
            rates: Dati delle candele
            price_type: Tipo di prezzo da utilizzare
            
        Returns:
            Array di prezzi
        """
        if not rates:
            return np.array([])
        
        # Indici per i vari tipi di prezzo
        OPEN_IDX, HIGH_IDX, LOW_IDX, CLOSE_IDX = 1, 2, 3, 4
        
        if price_type == "OPEN":
            return np.array([rate[OPEN_IDX] for rate in rates])
        elif price_type == "HIGH":
            return np.array([rate[HIGH_IDX] for rate in rates])
        elif price_type == "LOW":
            return np.array([rate[LOW_IDX] for rate in rates])
        elif price_type == "CLOSE":
            return np.array([rate[CLOSE_IDX] for rate in rates])
        elif price_type == "HL2":  # (High + Low) / 2
            return np.array([(rate[HIGH_IDX] + rate[LOW_IDX]) / 2 for rate in rates])
        elif price_type == "HLC3":  # (High + Low + Close) / 3
            return np.array([(rate[HIGH_IDX] + rate[LOW_IDX] + rate[CLOSE_IDX]) / 3 for rate in rates])
        elif price_type == "OHLC4":  # (Open + High + Low + Close) / 4
            return np.array([(rate[OPEN_IDX] + rate[HIGH_IDX] + rate[LOW_IDX] + rate[CLOSE_IDX]) / 4 for rate in rates])
        else:
            # Default: CLOSE
            return np.array([rate[CLOSE_IDX] for rate in rates])
    
    @staticmethod
    def calculate_rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Calcola l'indicatore RSI (Relative Strength Index).
        
        Formula:
        RSI = 100 - (100 / (1 + RS))
        dove RS = Media dei guadagni / Media delle perdite
        
        Args:
            prices: Array di prezzi
            period: Periodo per il calcolo
            
        Returns:
            Array con i valori dell'RSI
        """
        if len(prices) <= period:
            return np.array([])
        
        # Calcola le differenze tra i prezzi
        deltas = np.diff(prices)
        
        # Separa guadagni e perdite
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calcola le medie mobili di guadagni e perdite
        avg_gain = np.zeros_like(prices)
        avg_loss = np.zeros_like(prices)
        
        # Inizializza le prime medie
        avg_gain[period] = np.mean(gains[:period])
        avg_loss[period] = np.mean(losses[:period])
        
        # Calcola le medie successive
        for i in range(period + 1, len(prices)):
            avg_gain[i] = (avg_gain[i-1] * (period - 1) + gains[i-1]) / period
            avg_loss[i] = (avg_loss[i-1] * (period - 1) + losses[i-1]) / period
        
        # Calcola RS e RSI
        rs = np.zeros_like(prices)
        rsi = np.zeros_like(prices)
        
        for i in range(period, len(prices)):
            if avg_loss[i] == 0:
                rs[i] = 100.0
            else:
                rs[i] = avg_gain[i] / avg_loss[i]
            
            rsi[i] = 100 - (100 / (1 + rs[i]))
        
        return rsi
    
    @staticmethod
    def calculate_macd(prices: np.ndarray, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calcola l'indicatore MACD (Moving Average Convergence Divergence).
        
        Formula:
        MACD Line = EMA(fast_period) - EMA(slow_period)
        Signal Line = EMA(MACD Line, signal_period)
        Histogram = MACD Line - Signal Line
        
        Args:
            prices: Array di prezzi
            fast_period: Periodo veloce
            slow_period: Periodo lento
            signal_period: Periodo segnale
            
        Returns:
            Tuple con MACD Line, Signal Line e Histogram
        """
        if len(prices) <= slow_period + signal_period:
            return np.array([]), np.array([]), np.array([])
        
        # Calcola le medie mobili esponenziali
        ema_fast = np.zeros_like(prices)
        ema_slow = np.zeros_like(prices)
        
        # Inizializza le prime EMA con SMA
        ema_fast[fast_period-1] = np.mean(prices[:fast_period])
        ema_slow[slow_period-1] = np.mean(prices[:slow_period])
        
        # Calcola le EMA successive
        alpha_fast = 2 / (fast_period + 1)
        alpha_slow = 2 / (slow_period + 1)
        
        for i in range(fast_period, len(prices)):
            ema_fast[i] = prices[i] * alpha_fast + ema_fast[i-1] * (1 - alpha_fast)
        
        for i in range(slow_period, len(prices)):
            ema_slow[i] = prices[i] * alpha_slow + ema_slow[i-1] * (1 - alpha_slow)
        
        # Calcola MACD Line
        macd_line = ema_fast - ema_slow
        
        # Calcola Signal Line
        signal_line = np.zeros_like(prices)
        
        # Inizializza la prima Signal Line con SMA
        signal_line[slow_period+signal_period-1] = np.mean(macd_line[slow_period:slow_period+signal_period])
        
        # Calcola le Signal Line successive
        alpha_signal = 2 / (signal_period + 1)
        
        for i in range(slow_period+signal_period, len(prices)):
            signal_line[i] = macd_line[i] * alpha_signal + signal_line[i-1] * (1 - alpha_signal)
        
        # Calcola Histogram
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(prices: np.ndarray, period: int = 20, deviation: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calcola l'indicatore Bollinger Bands.
        
        Formula:
        Middle Band = SMA(period)
        Upper Band = Middle Band + (deviation * Standard Deviation)
        Lower Band = Middle Band - (deviation * Standard Deviation)
        
        Args:
            prices: Array di prezzi
            period: Periodo per il calcolo
            deviation: Deviazione standard
            
        Returns:
            Tuple con Upper Band, Middle Band e Lower Band
        """
        if len(prices) <= period:
            return np.array([]), np.array([]), np.array([])
        
        # Calcola la media mobile semplice (Middle Band)
        middle_band = np.zeros_like(prices)
        
        for i in range(period-1, len(prices)):
            middle_band[i] = np.mean(prices[i-period+1:i+1])
        
        # Calcola la deviazione standard
        std_dev = np.zeros_like(prices)
        
        for i in range(period-1, len(prices)):
            std_dev[i] = np.std(prices[i-period+1:i+1])
        
        # Calcola Upper e Lower Band
        upper_band = middle_band + (deviation * std_dev)
        lower_band = middle_band - (deviation * std_dev)
        
        return upper_band, middle_band, lower_band
    
    @staticmethod
    def calculate_adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calcola l'indicatore ADX (Average Directional Index).
        
        Formula:
        +DI = 100 * EMA(+DM) / ATR
        -DI = 100 * EMA(-DM) / ATR
        DX = 100 * |+DI - -DI| / (|+DI| + |-DI|)
        ADX = EMA(DX, period)
        
        Args:
            high: Array di prezzi massimi
            low: Array di prezzi minimi
            close: Array di prezzi di chiusura
            period: Periodo per il calcolo
            
        Returns:
            Tuple con ADX, +DI e -DI
        """
        if len(high) <= 2 * period:
            return np.array([]), np.array([]), np.array([])
        
        # Calcola True Range
        tr = np.zeros(len(high))
        
        for i in range(1, len(high)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr[i] = max(hl, hc, lc)
        
        # Calcola Directional Movement
        plus_dm = np.zeros(len(high))
        minus_dm = np.zeros(len(high))
        
        for i in range(1, len(high)):
            up_move = high[i] - high[i-1]
            down_move = low[i-1] - low[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            else:
                plus_dm[i] = 0
            
            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move
            else:
                minus_dm[i] = 0
        
        # Calcola ATR, +DI e -DI
        atr = np.zeros(len(high))
        plus_di = np.zeros(len(high))
        minus_di = np.zeros(len(high))
        
        # Inizializza i primi valori con SMA
        atr[period] = np.mean(tr[1:period+1])
        plus_di[period] = np.mean(plus_dm[1:period+1])
        minus_di[period] = np.mean(minus_dm[1:period+1])
        
        # Calcola i valori successivi con EMA
        for i in range(period+1, len(high)):
            atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
            plus_di[i] = (plus_di[i-1] * (period - 1) + plus_dm[i]) / period
            minus_di[i] = (minus_di[i-1] * (period - 1) + minus_dm[i]) / period
        
        # Normalizza +DI e -DI
        for i in range(period, len(high)):
            if atr[i] != 0:
                plus_di[i] = 100 * plus_di[i] / atr[i]
                minus_di[i] = 100 * minus_di[i] / atr[i]
        
        # Calcola DX e ADX
        dx = np.zeros(len(high))
        adx = np.zeros(len(high))
        
        for i in range(period, len(high)):
            if plus_di[i] + minus_di[i] != 0:
                dx[i] = 100 * abs(plus_di[i] - minus_di[i]) / (plus_di[i] + minus_di[i])
        
        # Inizializza il primo ADX con SMA
        adx[2*period-1] = np.mean(dx[period:2*period])
        
        # Calcola i valori successivi con EMA
        for i in range(2*period, len(high)):
            adx[i] = (adx[i-1] * (period - 1) + dx[i]) / period
        
        return adx, plus_di, minus_di
    
    @staticmethod
    def calculate_stochastic(high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int = 14, d_period: int = 3, slowing: int = 3) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcola l'indicatore Stochastic Oscillator.
        
        Formula:
        %K = 100 * (Close - Lowest Low(k_period)) / (Highest High(k_period) - Lowest Low(k_period))
        %D = SMA(%K, d_period)
        
        Args:
            high: Array di prezzi massimi
            low: Array di prezzi minimi
            close: Array di prezzi di chiusura
            k_period: Periodo per %K
            d_period: Periodo per %D
            slowing: Periodo di rallentamento
            
        Returns:
            Tuple con %K e %D
        """
        if len(high) <= k_period + d_period:
            return np.array([]), np.array([])
        
        # Calcola %K
        k = np.zeros(len(high))
        
        for i in range(k_period-1, len(high)):
            lowest_low = np.min(low[i-k_period+1:i+1])
            highest_high = np.max(high[i-k_period+1:i+1])
            
            if highest_high - lowest_low != 0:
                k[i] = 100 * (close[i] - lowest_low) / (highest_high - lowest_low)
        
        # Applica rallentamento a %K
        if slowing > 1:
            k_slowed = np.zeros(len(high))
            
            for i in range(k_period+slowing-2, len(high)):
                k_slowed[i] = np.mean(k[i-slowing+1:i+1])
        else:
            k_slowed = k
        
        # Calcola %D
        d = np.zeros(len(high))
        
        for i in range(k_period+d_period+slowing-3, len(high)):
            d[i] = np.mean(k_slowed[i-d_period+1:i+1])
        
        return k_slowed, d
    
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
    
    @classmethod
    def run(cls) -> None:
        """
        Esegue il calcolo dell'indicatore tecnico.
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
        
        # Validazione indicatore
        indicator = args.indicator.upper()
        if indicator not in SUPPORTED_INDICATORS:
            print(json.dumps({
                "success": False,
                "error": f"Indicatore non valido. Valori consentiti: {', '.join(SUPPORTED_INDICATORS)}"
            }, indent=2))
            sys.exit(1)
        
        # Imposta debug se richiesto
        if args.debug:
            import logging
            logging.getLogger("MT5Command").setLevel(logging.DEBUG)
            logging.getLogger("MT5Command").debug("Modalità debug attivata")
        
        # Prepara parametri dell'indicatore
        indicator_params = {}
        
        if indicator == "RSI":
            indicator_params["period"] = args.period or 14
        elif indicator == "MACD":
            indicator_params["fast_period"] = args.fast_period or 12
            indicator_params["slow_period"] = args.slow_period or 26
            indicator_params["signal_period"] = args.signal_period or 9
        elif indicator == "BOLLINGER":
            indicator_params["period"] = args.period or 20
            indicator_params["deviation"] = args.deviation or 2.0
        elif indicator == "ADX":
            indicator_params["period"] = args.period or 14
        elif indicator == "STOCHASTIC":
            indicator_params["k_period"] = args.k_period or 14
            indicator_params["d_period"] = args.d_period or 3
            indicator_params["slowing"] = args.slowing or 3
        elif indicator == "ATR":
            indicator_params["period"] = args.period or 14
        
        # Tipo di prezzo da utilizzare
        price_type = args.price_type or "CLOSE"
        
        # Verifica cache
        cache_key = None
        if args.cache:
            cache_key = cls.get_cache_key(args.symbol, args.timeframe, indicator, indicator_params)
            cached_data = cls.get_from_cache(cache_key)
            if cached_data:
                print(json.dumps({
                    "success": True,
                    "symbol": args.symbol,
                    "timeframe": args.timeframe,
                    "indicator": indicator,
                    "parameters": indicator_params,
                    "from_cache": True,
                    "data": cached_data
                }, indent=2))
                return
        
        try:
            # Creazione istanza
            cmd = cls(args.config)
            
            # Ottieni dati storici
            num_candles = args.num_candles
            
            # Per alcuni indicatori, aumenta il numero di candele per avere dati sufficienti
            if indicator == "MACD":
                num_candles = max(num_candles, indicator_params["slow_period"] + indicator_params["signal_period"] + 50)
            elif indicator == "ADX":
                num_candles = max(num_candles, 2 * indicator_params["period"] + 50)
            elif indicator == "STOCHASTIC":
                num_candles = max(num_candles, indicator_params["k_period"] + indicator_params["d_period"] + 50)
            else:
                num_candles = max(num_candles, indicator_params.get("period", 14) + 50)
            
            # Invia comando per ottenere dati storici
            rates = cmd.send_command("copy_rates_from", {
                "symbol": args.symbol,
                "timeframe": timeframe,
                "count": num_candles
            })
            
            if not rates:
                raise ValueError(f"Nessun dato storico disponibile per {args.symbol}")
            
            # Estrai array di prezzi
            if indicator in ["ADX", "STOCHASTIC", "ATR"]:
                # Questi indicatori richiedono high, low e close
                high = np.array([rate[2] for rate in rates])  # HIGH_IDX = 2
                low = np.array([rate[3] for rate in rates])   # LOW_IDX = 3
                close = np.array([rate[4] for rate in rates]) # CLOSE_IDX = 4
            else:
                # Gli altri indicatori utilizzano un solo tipo di prezzo
                prices = cls.get_price_array(rates, price_type)
            
            # Calcola l'indicatore
            result_data = {}
            
            if indicator == "RSI":
                rsi_values = cls.calculate_rsi(prices, indicator_params["period"])
                
                # Formatta i risultati
                result_data = {
                    "description": f"RSI({indicator_params['period']})",
                    "formula": "RSI = 100 - (100 / (1 + RS)), dove RS = Media dei guadagni / Media delle perdite",
                    "values": [float(v) if not np.isnan(v) else None for v in rsi_values[-100:]]
                }
            
            elif indicator == "MACD":
                macd_line, signal_line, histogram = cls.calculate_macd(
                    prices, 
                    indicator_params["fast_period"],
                    indicator_params["slow_period"],
                    indicator_params["signal_period"]
                )
                
                # Formatta i risultati
                result_data = {
                    "description": f"MACD({indicator_params['fast_period']},{indicator_params['slow_period']},{indicator_params['signal_period']})",
                    "formula": "MACD Line = EMA(fast_period) - EMA(slow_period), Signal Line = EMA(MACD Line, signal_period), Histogram = MACD Line - Signal Line",
                    "macd_line": [float(v) if not np.isnan(v) else None for v in macd_line[-100:]],
                    "signal_line": [float(v) if not np.isnan(v) else None for v in signal_line[-100:]],
                    "histogram": [float(v) if not np.isnan(v) else None for v in histogram[-100:]]
                }
            
            elif indicator == "BOLLINGER":
                upper_band, middle_band, lower_band = cls.calculate_bollinger_bands(
                    prices,
                    indicator_params["period"],
                    indicator_params["deviation"]
                )
                
                # Formatta i risultati
                result_data = {
                    "description": f"Bollinger Bands({indicator_params['period']},{indicator_params['deviation']})",
                    "formula": "Middle Band = SMA(period), Upper Band = Middle Band + (deviation * Standard Deviation), Lower Band = Middle Band - (deviation * Standard Deviation)",
                    "upper_band": [float(v) if not np.isnan(v) else None for v in upper_band[-100:]],
                    "middle_band": [float(v) if not np.isnan(v) else None for v in middle_band[-100:]],
                    "lower_band": [float(v) if not np.isnan(v) else None for v in lower_band[-100:]]
                }
            
            elif indicator == "ADX":
                adx, plus_di, minus_di = cls.calculate_adx(
                    high, low, close,
                    indicator_params["period"]
                )
                
                # Formatta i risultati
                result_data = {
                    "description": f"ADX({indicator_params['period']})",
                    "formula": "+DI = 100 * EMA(+DM) / ATR, -DI = 100 * EMA(-DM) / ATR, DX = 100 * |+DI - -DI| / (|+DI| + |-DI|), ADX = EMA(DX, period)",
                    "adx": [float(v) if not np.isnan(v) else None for v in adx[-100:]],
                    "plus_di": [float(v) if not np.isnan(v) else None for v in plus_di[-100:]],
                    "minus_di": [float(v) if not np.isnan(v) else None for v in minus_di[-100:]]
                }
            
            elif indicator == "STOCHASTIC":
                k, d = cls.calculate_stochastic(
                    high, low, close,
                    indicator_params["k_period"],
                    indicator_params["d_period"],
                    indicator_params["slowing"]
                )
                
                # Formatta i risultati
                result_data = {
                    "description": f"Stochastic({indicator_params['k_period']},{indicator_params['d_period']},{indicator_params['slowing']})",
                    "formula": "%K = 100 * (Close - Lowest Low(k_period)) / (Highest High(k_period) - Lowest Low(k_period)), %D = SMA(%K, d_period)",
                    "k": [float(v) if not np.isnan(v) else None for v in k[-100:]],
                    "d": [float(v) if not np.isnan(v) else None for v in d[-100:]]
                }
            
            elif indicator == "ATR":
                atr_values = cls.calculate_atr(
                    high, low, close,
                    indicator_params["period"]
                )
                
                # Formatta i risultati
                result_data = {
                    "description": f"ATR({indicator_params['period']})",
                    "formula": "TR = max(High - Low, |High - Close_prev|, |Low - Close_prev|), ATR = EMA(TR, period)",
                    "values": [float(v) if not np.isnan(v) else None for v in atr_values[-100:]]
                }
            
            # Aggiungi alla cache se richiesto
            if args.cache and cache_key:
                cls.add_to_cache(cache_key, result_data)
            
            # Formatta e stampa risultato
            output = {
                "success": True,
                "symbol": args.symbol,
                "timeframe": args.timeframe,
                "indicator": indicator,
                "parameters": indicator_params,
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
                "timeframe": args.timeframe,
                "indicator": indicator
            }
            
            print(json.dumps(output, indent=2))
            sys.exit(1)


if __name__ == "__main__":
    MT5GetIndicatorData.run()
