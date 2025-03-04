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
            
            # Importa MT5Client solo quando necessario
            from gui.utils.mt5_client import MT5Client
            
            # Crea client MT5
            mt5_client = MT5Client(config_path="config/mt5_config.json")
            
            # Verifica connessione
            if not mt5_client.check_connection():
                self.logger.error("Impossibile eseguire operazione: MT5 Keeper non connesso")
                return None
            
            # Ottieni informazioni sul simbolo per avere il prezzo attuale
            symbol_info = mt5_client.get_symbol_info_tick(symbol)
            
            if "error" in symbol_info:
                self.logger.error(f"Errore nell'ottenere informazioni sul simbolo: {symbol_info.get('error', 'Errore sconosciuto')}")
                return None
            
            # Ottieni prezzi bid/ask attuali
            bid_price = symbol_info.get("bid", 0.0)
            ask_price = symbol_info.get("ask", 0.0)
            
            if bid_price <= 0 or ask_price <= 0:
                self.logger.error(f"Prezzi non validi: bid={bid_price}, ask={ask_price}")
                return None
            
            # Log dei prezzi attuali
            self.logger.info(f"Prezzi attuali per {symbol}: bid={bid_price}, ask={ask_price}")
            
            # Verifica se ci sono posizioni aperte da chiudere
            positions = mt5_client.get_positions(symbol=symbol)
            
            # Gestione chiusura posizioni
            if positions:
                # Ottieni configurazione per la gestione delle posizioni
                position_management = self.config.get("trading", {}).get("position_management", {})
                floating_profit_close_percentage = position_management.get("floating_profit_close_percentage", 2.0)
                
                for position in positions:
                    try:
                        # Verifica se la posizione ha un profitto sufficiente per essere chiusa
                        profit = position.get("profit", 0.0)
                        volume = position.get("volume", 0.0)
                        ticket = position.get("ticket", 0)
                        position_type = position.get("type", "")
                        
                        # Calcola la percentuale di profitto
                        # Questo è un calcolo approssimativo, in un sistema reale sarebbe più preciso
                        profit_percentage = (profit / (volume * 100)) * 100  # Approssimativo
                        
                        # Chiudi la posizione se il profitto è sufficiente
                        if profit_percentage >= floating_profit_close_percentage:
                            self.logger.info(f"Chiusura posizione {ticket} con profitto {profit} ({profit_percentage:.2f}%)")
                            result = mt5_client.close_position(ticket)
                            self.logger.info(f"Risultato chiusura: {result}")
                    except Exception as e:
                        self.logger.error(f"Errore nella gestione della posizione {position.get('ticket', 'unknown')}: {e}")
            
            # Genera casualmente un segnale (solo per demo)
            # Importa random solo quando necessario per evitare blocchi
            import random
            
            # Riduce la probabilità di generare un segnale per evitare troppi log
            if random.random() < 0.05:  # 5% di probabilità di generare un segnale
                action = random.choice(["buy", "sell"])
                
                # Usa il prezzo attuale invece di un prezzo casuale
                if action.lower() == "buy":
                    price = ask_price  # Per acquisto, usa il prezzo ask
                else:
                    price = bid_price  # Per vendita, usa il prezzo bid
                
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
                    
                    # Calcola stop loss e take profit in base alla configurazione
                    sl_tp_config = self.config.get("stop_loss_take_profit", {})
                    
                    # Ottieni i valori di default
                    default_sl_pips = sl_tp_config.get("default_sl_pips", 30)
                    default_tp_pips = sl_tp_config.get("default_tp_pips", 50)
                    
                    # Converti pips in prezzo (approssimativo, in un sistema reale sarebbe più preciso)
                    pip_value = 0.0001  # Per la maggior parte delle coppie di valute
                    
                    # Gestione speciale per XAUUSD (oro)
                    if symbol == "XAUUSD":
                        # Per l'oro, usiamo valori più grandi per SL e TP
                        # Ottieni il prezzo attuale dal mercato
                        try:
                            # Ottieni informazioni sul simbolo
                            symbol_info = mt5_client.get_symbol_info_tick(symbol)
                            
                            if "error" in symbol_info:
                                self.logger.error(f"Errore nell'ottenere informazioni sul simbolo: {symbol_info['error']}")
                                return signal_str
                            
                            # Usa il prezzo bid/ask attuale
                            if action.lower() == "buy":
                                current_price = symbol_info.get("ask", 0.0)
                            else:  # sell
                                current_price = symbol_info.get("bid", 0.0)
                            
                            if current_price <= 0:
                                self.logger.error(f"Prezzo non valido: {current_price}")
                                return signal_str
                            
                            # Per l'oro, usiamo valori assoluti per SL e TP
                            if action.lower() == "buy":
                                sl = current_price - 3.0  # 3 USD sotto il prezzo attuale
                                tp = current_price + 5.0  # 5 USD sopra il prezzo attuale
                            else:  # sell
                                sl = current_price + 3.0  # 3 USD sopra il prezzo attuale
                                tp = current_price - 5.0  # 5 USD sotto il prezzo attuale
                            
                            # Log
                            self.logger.info(f"XAUUSD - Prezzo attuale: {current_price}, SL calcolato: {sl}, TP calcolato: {tp}")
                            
                        except Exception as e:
                            self.logger.error(f"Errore nel calcolo di SL/TP per XAUUSD: {e}")
                            # In caso di errore, usa valori di default
                            sl = 0.0
                            tp = 0.0
                    else:
                        # Per altri simboli, usa il calcolo originale
                        if symbol == "XAGUSD":
                            pip_value = 0.01  # Per argento
                        
                        # Calcola SL e TP
                        if action.lower() == "buy":
                            sl = price - (default_sl_pips * pip_value)
                            tp = price + (default_tp_pips * pip_value)
                        else:  # sell
                            sl = price + (default_sl_pips * pip_value)
                            tp = price - (default_tp_pips * pip_value)
                        
                        # Log
                        self.logger.info(f"SL calcolato: {sl}, TP calcolato: {tp}")
                    
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
