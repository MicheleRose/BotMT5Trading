#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5 Trading Bot - Sistema di trading automatico per MetaTrader 5.

Questo modulo fornisce la classe principale per il trading automatico.
"""

import os
import sys
import time
import datetime
import json
import logging
from typing import Dict, Any, Optional, List

class TradingBot:
    """
    Trading bot per MetaTrader 5.
    
    Versione semplificata per l'interfaccia grafica.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inizializza il trading bot.
        
        Args:
            config: Configurazione del bot
        """
        self.config = config
        self.last_check_time = datetime.datetime.now()
        self.logger = logging.getLogger("TradingBot")
        
        # Configura logger
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
        
        # Log
        self.logger.info("Trading bot inizializzato")
    
    def run_cycle(self) -> Optional[Dict[str, Any]]:
        """
        Esegue un ciclo del trading bot.
        
        Returns:
            Segnale di trading generato, se presente
        """
        try:
            # Verifica tempo trascorso
            now = datetime.datetime.now()
            seconds_elapsed = (now - self.last_check_time).total_seconds()
            
            # Verifica se è il momento di controllare
            trade_frequency = self.config.get("trading", {}).get("trade_frequency_seconds", 5)
            if seconds_elapsed < trade_frequency:
                return None
            
            # Aggiorna tempo ultimo controllo
            self.last_check_time = now
            
            # Genera segnale di esempio (solo per demo)
            # In un sistema reale, qui ci sarebbe una logica più complessa
            symbol = self.config.get("trading", {}).get("symbol", "EURUSD")
            lot_size = self.config.get("trading", {}).get("lot_size", 0.01)
            
            # Genera casualmente un segnale (solo per demo)
            # Importa random solo quando necessario per evitare blocchi
            import random
            
            # Riduce la probabilità di generare un segnale per evitare troppi log
            if random.random() < 0.05:  # 5% di probabilità di generare un segnale
                action = random.choice(["buy", "sell"])
                price = 1.1000 + random.random() * 0.1  # Prezzo casuale tra 1.1000 e 1.2000
                
                # Formatta il segnale come stringa per evitare problemi di serializzazione
                signal_str = f"{action} {symbol} @ {price}"
                
                self.logger.info(f"Segnale generato: {signal_str}")
                
                # Esegui operazione di trading
                try:
                    # Importa MT5Client solo quando necessario
                    from gui.utils.mt5_client import MT5Client
                    
                    # Crea client MT5
                    mt5_client = MT5Client(config_path="config/mt5_config.json")
                    
                    # Verifica connessione
                    if not mt5_client.check_connection():
                        self.logger.error("Impossibile eseguire operazione: MT5 Keeper non connesso")
                        return signal_str
                    
                    # Calcola stop loss e take profit
                    sl = 0.0  # In un sistema reale, calcolare in base alla volatilità
                    tp = 0.0  # In un sistema reale, calcolare in base alla volatilità
                    
                    # Esegui operazione
                    if action.lower() == "buy":
                        result = mt5_client.market_buy(
                            symbol=symbol,
                            volume=lot_size,
                            sl=sl,
                            tp=tp,
                            comment="MT5 Trading Bot"
                        )
                        self.logger.info(f"Operazione BUY eseguita: {result}")
                    else:  # sell
                        result = mt5_client.market_sell(
                            symbol=symbol,
                            volume=lot_size,
                            sl=sl,
                            tp=tp,
                            comment="MT5 Trading Bot"
                        )
                        self.logger.info(f"Operazione SELL eseguita: {result}")
                    
                except Exception as e:
                    self.logger.error(f"Errore nell'esecuzione dell'operazione: {e}")
                
                return signal_str
            
            return None
            
        except Exception as e:
            self.logger.error(f"Errore nel ciclo del trading bot: {e}")
            return None
