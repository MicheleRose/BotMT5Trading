#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logger - Sistema di logging per MT5 Trading Bot GUI.

Questo modulo fornisce funzionalità di logging per l'applicazione.
"""

import os
import sys
import logging
import datetime
from typing import Optional, Dict, Any, List
from logging.handlers import RotatingFileHandler

class BotLogger:
    """
    Sistema di logging per MT5 Trading Bot GUI.
    """
    
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        """
        Inizializza il sistema di logging.
        
        Args:
            log_dir: Directory per i file di log
            log_level: Livello di logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.log_dir = log_dir
        self.log_level = self._get_log_level(log_level)
        
        # Crea directory per i log se non esiste
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Configura logger root
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(self.log_level)
        
        # Rimuovi handler esistenti
        for handler in self.root_logger.handlers[:]:
            self.root_logger.removeHandler(handler)
        
        # Aggiungi handler per console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.root_logger.addHandler(console_handler)
        
        # Crea file di log
        self.log_file = os.path.join(self.log_dir, f"trading_bot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        self.error_file = os.path.join(self.log_dir, f"error_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        # Aggiungi handler per file di log
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.root_logger.addHandler(file_handler)
        
        # Aggiungi handler per file di errori
        error_handler = RotatingFileHandler(
            self.error_file,
            maxBytes=10*1024*1024,  # 10 MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(pathname)s:%(lineno)d\n%(message)s\n'
        ))
        self.root_logger.addHandler(error_handler)
        
        # Crea logger per trading bot
        self.bot_logger = logging.getLogger("TradingBot")
        
        # Lista di messaggi per GUI
        self.gui_messages: List[Dict[str, Any]] = []
        self.max_gui_messages = 1000
    
    def _get_log_level(self, level_name: str) -> int:
        """
        Converte il nome del livello di logging in valore numerico.
        
        Args:
            level_name: Nome del livello di logging
            
        Returns:
            Valore numerico del livello di logging
        """
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        return levels.get(level_name.upper(), logging.INFO)
    
    def set_log_level(self, level: str) -> None:
        """
        Imposta il livello di logging.
        
        Args:
            level: Livello di logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_level = self._get_log_level(level)
        
        # Imposta livello per logger root
        self.root_logger.setLevel(log_level)
        
        # Imposta livello per handler console
        for handler in self.root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                handler.setLevel(log_level)
            elif isinstance(handler, RotatingFileHandler) and handler.baseFilename == self.log_file:
                handler.setLevel(log_level)
    
    def log(self, level: str, message: str, module: str = "GUI") -> None:
        """
        Registra un messaggio di log.
        
        Args:
            level: Livello di logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Messaggio da registrare
            module: Nome del modulo
        """
        logger = logging.getLogger(module)
        
        # Registra messaggio
        log_level = self._get_log_level(level)
        logger.log(log_level, message)
        
        # Aggiungi messaggio per GUI
        self.add_gui_message(level, message, module)
    
    def debug(self, message: str, module: str = "GUI") -> None:
        """
        Registra un messaggio di debug.
        
        Args:
            message: Messaggio da registrare
            module: Nome del modulo
        """
        self.log("DEBUG", message, module)
    
    def info(self, message: str, module: str = "GUI") -> None:
        """
        Registra un messaggio informativo.
        
        Args:
            message: Messaggio da registrare
            module: Nome del modulo
        """
        self.log("INFO", message, module)
    
    def warning(self, message: str, module: str = "GUI") -> None:
        """
        Registra un messaggio di avviso.
        
        Args:
            message: Messaggio da registrare
            module: Nome del modulo
        """
        self.log("WARNING", message, module)
    
    def error(self, message: str, module: str = "GUI") -> None:
        """
        Registra un messaggio di errore.
        
        Args:
            message: Messaggio da registrare
            module: Nome del modulo
        """
        self.log("ERROR", message, module)
    
    def critical(self, message: str, module: str = "GUI") -> None:
        """
        Registra un messaggio critico.
        
        Args:
            message: Messaggio da registrare
            module: Nome del modulo
        """
        self.log("CRITICAL", message, module)
    
    def add_gui_message(self, level: str, message: str, module: str = "GUI") -> None:
        """
        Aggiunge un messaggio alla lista per la GUI.
        
        Args:
            level: Livello di logging
            message: Messaggio
            module: Nome del modulo
        """
        # Crea messaggio
        gui_message = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": level,
            "module": module,
            "message": message
        }
        
        # Aggiungi messaggio
        self.gui_messages.append(gui_message)
        
        # Limita numero di messaggi
        if len(self.gui_messages) > self.max_gui_messages:
            self.gui_messages = self.gui_messages[-self.max_gui_messages:]
    
    def get_gui_messages(self, level: Optional[str] = None, module: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Ottiene i messaggi per la GUI.
        
        Args:
            level: Filtra per livello (opzionale)
            module: Filtra per modulo (opzionale)
            limit: Numero massimo di messaggi da restituire
            
        Returns:
            Lista di messaggi
        """
        # Filtra messaggi
        filtered_messages = self.gui_messages
        
        if level:
            filtered_messages = [m for m in filtered_messages if m["level"] == level]
        
        if module:
            filtered_messages = [m for m in filtered_messages if m["module"] == module]
        
        # Restituisci ultimi messaggi
        return filtered_messages[-limit:]
    
    def clear_gui_messages(self) -> None:
        """
        Cancella i messaggi per la GUI.
        """
        self.gui_messages = []
