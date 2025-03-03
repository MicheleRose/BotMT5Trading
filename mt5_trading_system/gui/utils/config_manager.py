#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config Manager - Classe per la gestione della configurazione del trading bot.

Questa classe si occupa di caricare e salvare la configurazione del trading bot
da file JSON.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Union

# Configurazione logging
logger = logging.getLogger("ConfigManager")

class ConfigManager:
    """
    Gestore della configurazione del trading bot.
    """
    
    def __init__(self, config_path: str):
        """
        Inizializza il gestore della configurazione.
        
        Args:
            config_path: Percorso al file di configurazione JSON
        """
        self.config_path = config_path
        self.config = {}
        self.default_config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Restituisce la configurazione predefinita.
        
        Returns:
            Configurazione predefinita
        """
        return {
            "trading": {
                "broker": "Demo",
                "symbol": "EURUSD",
                "timeframe": "M5",
                "lot_size": 0.01,
                "trade_frequency_seconds": 5,
                "max_trades_open": 10,
                "spread_limit_points": 20,
                "adaptive_risk": False,
                "profit_trailing": False,
                "strict_mode": False,
                "lot_increment_every": 5,
                "position_management": {
                    "min_pips_between_orders": 10,
                    "floating_profit_close_percentage": 1.0,
                    "hedge_protection": False
                }
            },
            "risk_management": {
                "max_drawdown_percentage": 10,
                "capital_protection_thresholds": {
                    "1000": 0.20,
                    "5000": 0.15,
                    "10000": 0.10
                },
                "minimum_free_margin": 100
            },
            "execution": {
                "order_type": "market",
                "deviation": 5,
                "magic_number": 123456,
                "order_comment": "MT5 Trading Bot",
                "type_filling": "IOC",
                "type_time": "GTC"
            },
            "stop_loss_take_profit": {
                "use_atr": True,
                "atr_multiplier_sl": 1.5,
                "atr_multiplier_tp": 2.0,
                "default_sl_pips": 30,
                "default_tp_pips": 50,
                "increase_sl_if_trend_confident": True
            },
            "indicators": {
                "ema": {
                    "fast_period": 9,
                    "slow_period": 21
                },
                "rsi": {
                    "period": 14,
                    "oversold": 30,
                    "overbought": 70
                },
                "macd": {
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                },
                "bollinger": {
                    "period": 20,
                    "std_dev": 2
                },
                "adx": {
                    "period": 14,
                    "threshold": 25
                },
                "atr": {
                    "period": 14
                }
            },
            "logging": {
                "log_file": "logs/trading.log",
                "error_file": "logs/error.log",
                "log_level": "INFO"
            }
        }
    
    def load(self) -> Dict[str, Any]:
        """
        Carica la configurazione dal file.
        
        Returns:
            Configurazione caricata
        """
        try:
            # Verifica se il file esiste
            if not os.path.exists(self.config_path):
                logger.warning(f"File di configurazione non trovato: {self.config_path}")
                logger.info("Utilizzo configurazione predefinita")
                self.config = self.default_config
                return self.config
            
            # Carica configurazione da file
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            
            logger.info(f"Configurazione caricata da {self.config_path}")
            
            # Verifica e completa configurazione
            self._validate_and_complete_config()
            
            return self.config
            
        except Exception as e:
            logger.error(f"Errore nel caricamento della configurazione: {e}")
            logger.info("Utilizzo configurazione predefinita")
            self.config = self.default_config
            return self.config
    
    def save(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Salva la configurazione su file.
        
        Args:
            config: Configurazione da salvare (opzionale, se non specificata usa self.config)
            
        Returns:
            True se il salvataggio è riuscito, False altrimenti
        """
        try:
            # Usa configurazione specificata o quella corrente
            config_to_save = config if config is not None else self.config
            
            # Crea directory se non esiste
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Salva configurazione su file
            with open(self.config_path, 'w') as f:
                json.dump(config_to_save, f, indent=2)
            
            logger.info(f"Configurazione salvata su {self.config_path}")
            
            # Aggiorna configurazione corrente
            if config is not None:
                self.config = config
            
            return True
            
        except Exception as e:
            logger.error(f"Errore nel salvataggio della configurazione: {e}")
            return False
    
    def _validate_and_complete_config(self) -> None:
        """
        Verifica e completa la configurazione con valori predefiniti per campi mancanti.
        """
        # Funzione ricorsiva per completare configurazione
        def complete_config(default: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
            result = current.copy()
            
            for key, value in default.items():
                if key not in result:
                    # Aggiungi campo mancante
                    result[key] = value
                elif isinstance(value, dict) and isinstance(result[key], dict):
                    # Completa sottodizionario
                    result[key] = complete_config(value, result[key])
            
            return result
        
        # Completa configurazione
        self.config = complete_config(self.default_config, self.config)
    
    def get_value(self, path: str, default: Any = None) -> Any:
        """
        Ottiene un valore dalla configurazione.
        
        Args:
            path: Percorso del valore (es. "trading.symbol")
            default: Valore predefinito da restituire se il percorso non esiste
            
        Returns:
            Valore trovato o valore predefinito
        """
        try:
            # Dividi percorso in parti
            parts = path.split('.')
            
            # Naviga nella configurazione
            value = self.config
            for part in parts:
                value = value[part]
            
            return value
            
        except (KeyError, TypeError):
            return default
    
    def set_value(self, path: str, value: Any) -> bool:
        """
        Imposta un valore nella configurazione.
        
        Args:
            path: Percorso del valore (es. "trading.symbol")
            value: Valore da impostare
            
        Returns:
            True se l'operazione è riuscita, False altrimenti
        """
        try:
            # Dividi percorso in parti
            parts = path.split('.')
            
            # Naviga nella configurazione
            config = self.config
            for part in parts[:-1]:
                if part not in config:
                    config[part] = {}
                config = config[part]
            
            # Imposta valore
            config[parts[-1]] = value
            
            return True
            
        except Exception as e:
            logger.error(f"Errore nell'impostazione del valore {path}: {e}")
            return False
    
    def get_symbols(self) -> List[str]:
        """
        Ottiene la lista dei simboli disponibili.
        
        Returns:
            Lista dei simboli
        """
        # In una versione più avanzata, questa funzione potrebbe ottenere
        # la lista dei simboli da MT5 Keeper
        return [
            "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD",
            "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "XAUUSD", "XAGUSD"
        ]
    
    def get_timeframes(self) -> List[str]:
        """
        Ottiene la lista dei timeframe disponibili.
        
        Returns:
            Lista dei timeframe
        """
        return [
            "M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"
        ]
