#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5 Trading Bot GUI - Applicazione principale.

Questo modulo fornisce l'applicazione principale per il sistema MT5 Trading Bot.
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import time
import datetime
import json
import logging
from typing import Dict, Any, Optional, List, Callable

# Aggiungi directory principale al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa moduli
from gui.utils.mt5_client import MT5Client
from gui.utils.config_manager import ConfigManager
from gui.utils.logger import BotLogger
from gui.components.dashboard import Dashboard
from gui.components.positions import Positions
from gui.components.config import Config
from gui.components.logs import Logs
from gui.components.charts import Charts

# Importa moduli per il trading bot
from bot import TradingBot

class MT5TradingBotGUI(tb.Window):
    """
    Applicazione principale per il sistema MT5 Trading Bot.
    """
    
    def __init__(self, config_path: str = "config/trading_config.json"):
        """
        Inizializza l'applicazione.
        
        Args:
            config_path: Percorso al file di configurazione JSON
        """
        # Inizializza finestra
        super().__init__(
            title="MT5 Trading Bot",
            themename="darkly",
            size=(1200, 800),
            position=(100, 100),
            minsize=(800, 600),
            iconphoto=""
        )
        
        # Inizializza logger
        self.logger = BotLogger(log_dir="logs", log_level="INFO")
        self.logger.info("Applicazione avviata", "GUI")
        
        # Inizializza config manager
        self.config_manager = ConfigManager(config_path)
        
        # Inizializza MT5 client
        self.mt5_client = MT5Client(config_path="config/mt5_config.json")
        
        # Trading bot
        self.trading_bot = None
        self.bot_thread = None
        self.bot_active = False
        
        # Dati per grafici
        self.equity_history = []
        self.balance_history = []
        self.profit_history = []
        
        # Crea interfaccia
        self._create_widgets()
        
        # Avvia monitoraggio
        self._start_monitoring()
        
        # Verifica connessione
        self._check_connection()
    
    def _create_widgets(self):
        """
        Crea i widget dell'interfaccia.
        """
        # Frame principale
        main_frame = tb.Frame(self)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # Notebook principale
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=BOTH, expand=YES, padx=10, pady=10)
        
        # Tab Dashboard
        self.dashboard_frame = tb.Frame(self.notebook)
        self.notebook.add(self.dashboard_frame, text="Dashboard")
        
        # Tab Posizioni
        self.positions_frame = tb.Frame(self.notebook)
        self.notebook.add(self.positions_frame, text="Posizioni")
        
        # Tab Configurazione
        self.config_frame = tb.Frame(self.notebook)
        self.notebook.add(self.config_frame, text="Configurazione")
        
        # Tab Grafici
        self.charts_frame = tb.Frame(self.notebook)
        self.notebook.add(self.charts_frame, text="Grafici")
        
        # Tab Log
        self.logs_frame = tb.Frame(self.notebook)
        self.notebook.add(self.logs_frame, text="Log")
        
        # Crea componenti
        self.dashboard = Dashboard(self.dashboard_frame, self.mt5_client, self.logger)
        self.dashboard.pack(fill=BOTH, expand=YES)
        
        self.positions = Positions(self.positions_frame, self.mt5_client, self.logger)
        self.positions.pack(fill=BOTH, expand=YES)
        
        self.config_component = Config(self.config_frame, self.config_manager, self.logger)
        self.config_component.pack(fill=BOTH, expand=YES)
        
        self.charts = Charts(self.charts_frame, self.mt5_client, self.logger)
        self.charts.pack(fill=BOTH, expand=YES)
        
        self.logs = Logs(self.logs_frame, self.logger)
        self.logs.pack(fill=BOTH, expand=YES)
        
        # Barra di stato
        self.status_bar = tb.Frame(self, bootstyle="secondary")
        self.status_bar.pack(side=BOTTOM, fill=X)
        
        # Stato connessione
        self.connection_frame = tb.Frame(self.status_bar)
        self.connection_frame.pack(side=LEFT, padx=10, pady=2)
        
        self.connection_indicator = tb.Label(
            self.connection_frame,
            text="●",
            font=("TkDefaultFont", 12),
            bootstyle="danger"
        )
        self.connection_indicator.pack(side=LEFT, padx=(0, 5))
        
        self.connection_label = tb.Label(
            self.connection_frame,
            text="Disconnesso",
            bootstyle="danger"
        )
        self.connection_label.pack(side=LEFT)
        
        # Stato bot
        self.bot_frame = tb.Frame(self.status_bar)
        self.bot_frame.pack(side=LEFT, padx=10, pady=2)
        
        self.bot_indicator = tb.Label(
            self.bot_frame,
            text="●",
            font=("TkDefaultFont", 12),
            bootstyle="danger"
        )
        self.bot_indicator.pack(side=LEFT, padx=(0, 5))
        
        self.bot_label = tb.Label(
            self.bot_frame,
            text="Bot Inattivo",
            bootstyle="danger"
        )
        self.bot_label.pack(side=LEFT)
        
        # Timestamp
        self.timestamp_label = tb.Label(
            self.status_bar,
            text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            bootstyle="secondary"
        )
        self.timestamp_label.pack(side=RIGHT, padx=10, pady=2)
        
        # Bind eventi
        self.dashboard.bind("<<StartBot>>", self._on_start_bot)
        self.dashboard.bind("<<StopBot>>", self._on_stop_bot)
        
        # Non avviamo più il monitoraggio automaticamente
        # self._start_monitoring()
        
        # Non verifichiamo più la connessione automaticamente
        # self._check_connection()
        
        # Aggiorna timestamp periodicamente
        self._update_timestamp()
    
    def _check_connection(self):
        """
        Verifica la connessione a MT5 Keeper.
        """
        try:
            # Esegui verifica connessione in thread separato
            threading.Thread(
                target=self._check_connection_thread,
                daemon=True
            ).start()
            
            # Pianifica prossima verifica
            self.after(5000, self._check_connection)
            
        except Exception as e:
            self.logger.error(f"Errore nella verifica della connessione: {e}", "GUI")
            # Pianifica prossima verifica anche in caso di errore
            self.after(5000, self._check_connection)
    
    def _check_connection_thread(self):
        """
        Thread per verifica connessione.
        """
        try:
            connected = self.mt5_client.check_connection()
            
            # Aggiorna UI nel thread principale
            self.after(0, lambda: self._update_connection_ui(connected))
            
        except Exception as e:
            self.logger.error(f"Errore nel thread di verifica connessione: {e}", "GUI")
            # Aggiorna UI nel thread principale
            self.after(0, lambda: self._update_connection_ui(False))
    
    def _update_connection_ui(self, connected: bool):
        """
        Aggiorna UI in base allo stato della connessione.
        
        Args:
            connected: True se connesso, False altrimenti
        """
        if connected:
            self.connection_indicator.configure(bootstyle="success")
            self.connection_label.configure(text="Connesso", bootstyle="success")
            self.logger.info("Connesso a MT5 Keeper", "GUI")
            
            # Avvia thread per aggiornamento dati
            threading.Thread(
                target=self._update_data_thread,
                daemon=True
            ).start()
        else:
            self.connection_indicator.configure(bootstyle="danger")
            self.connection_label.configure(text="Disconnesso", bootstyle="danger")
            self.logger.warning("Disconnesso da MT5 Keeper", "GUI")
    
    def _update_data_thread(self):
        """
        Thread per aggiornamento dati.
        """
        try:
            # Aggiorna account info
            account_info = self.mt5_client.get_account_info()
            if account_info:
                # Aggiorna UI nel thread principale
                self.after(0, lambda: self.dashboard._on_account_update(account_info))
            
            # Aggiorna posizioni
            positions = self.mt5_client.get_positions()
            if positions is not None:
                # Aggiorna UI nel thread principale
                self.after(0, lambda: self.positions._on_positions_update(positions))
                
        except Exception as e:
            self.logger.error(f"Errore nell'aggiornamento dei dati: {e}", "GUI")
    
    def _update_timestamp(self):
        """
        Aggiorna il timestamp nella barra di stato.
        """
        self.timestamp_label.configure(
            text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Pianifica prossimo aggiornamento
        self.after(1000, self._update_timestamp)
    
    def _start_monitoring(self):
        """
        Avvia il monitoraggio dell'account e delle posizioni.
        """
        self.mt5_client.start_monitoring()
    
    def _on_start_bot(self, event=None):
        """
        Callback per avvio del trading bot.
        """
        if self.bot_active:
            self.logger.warning("Trading bot già attivo", "GUI")
            return
        
        # Avvia in thread separato per evitare blocchi dell'interfaccia
        threading.Thread(
            target=self._start_bot_thread,
            daemon=True
        ).start()
    
    def _start_bot_thread(self):
        """
        Thread per avvio del trading bot.
        """
        try:
            # Verifica connessione a MT5 Keeper
            if not self.mt5_client.connected:
                self.logger.warning("Impossibile avviare il bot: MT5 Keeper non connesso", "GUI")
                # Mostra errore nel thread principale
                self.after(0, lambda: messagebox.showwarning(
                    "Attenzione", 
                    "Impossibile avviare il bot: MT5 Keeper non connesso.\n" +
                    "Assicurarsi che MT5 Keeper sia in esecuzione e riprovare."
                ))
                return
            
            # Ottieni configurazione
            config = self.config_manager.config
            
            # Crea trading bot
            self.trading_bot = TradingBot(config)
            
            # Aggiorna UI nel thread principale
            self.after(0, lambda: self._update_bot_ui(True, config))
            
            # Breve pausa per evitare problemi di connessione
            time.sleep(0.5)
            
            # Avvia thread del bot
            self.bot_active = True
            self._bot_thread_exit_flag = False  # Reset flag di terminazione
            self.bot_thread = threading.Thread(
                target=self._bot_thread_func,
                daemon=True
            )
            self.bot_thread.start()
            
            # Log
            self.logger.info("Trading bot avviato", "GUI")
            
        except Exception as e:
            self.logger.error(f"Errore nell'avvio del trading bot: {e}", "GUI")
            # Mostra errore nel thread principale
            self.after(0, lambda: messagebox.showerror("Errore", f"Errore nell'avvio del trading bot: {e}"))
    
    def _update_bot_ui(self, active: bool, config=None):
        """
        Aggiorna UI in base allo stato del bot.
        
        Args:
            active: True se bot attivo, False altrimenti
            config: Configurazione del bot (opzionale)
        """
        try:
            if active:
                # Aggiorna stato
                self.bot_indicator.configure(bootstyle="success")
                self.bot_label.configure(text="Bot Attivo", bootstyle="success")
                
                # Aggiorna dashboard
                positions_count = len(self.mt5_client.get_positions())
                self.dashboard.update_bot_status(True, config, positions_count)
            else:
                # Aggiorna stato
                self.bot_indicator.configure(bootstyle="danger")
                self.bot_label.configure(text="Bot Inattivo", bootstyle="danger")
                
                # Aggiorna dashboard
                positions_count = len(self.mt5_client.get_positions())
                self.dashboard.update_bot_status(False, None, positions_count)
        except Exception as e:
            self.logger.error(f"Errore nell'aggiornamento dell'interfaccia: {e}", "GUI")
    
    def _on_stop_bot(self, event=None):
        """
        Callback per arresto del trading bot.
        """
        if not self.bot_active:
            self.logger.warning("Trading bot non attivo", "GUI")
            return
        
        # Avvia in thread separato per evitare blocchi dell'interfaccia
        threading.Thread(
            target=self._stop_bot_thread,
            daemon=True
        ).start()
    
    def _stop_bot_thread(self):
        """
        Thread per arresto del trading bot.
        """
        try:
            # Imposta flag di terminazione
            self.bot_active = False
            self._bot_thread_exit_flag = True
            
            # Aggiorna UI nel thread principale immediatamente
            self.after(0, lambda: self._update_bot_ui(False))
            
            # Attendi thread bot con timeout
            if self.bot_thread and self.bot_thread.is_alive():
                self.logger.info("Attesa terminazione thread bot...", "GUI")
                
                # Attendi con timeout più lungo
                self.bot_thread.join(timeout=3.0)
                
                # Verifica se il thread è ancora vivo
                if self.bot_thread.is_alive():
                    self.logger.warning("Thread bot non terminato entro il timeout", "GUI")
                    # Non possiamo forzare la terminazione del thread in Python
                    # ma possiamo avvisare l'utente
                    self.after(0, lambda: messagebox.showwarning(
                        "Attenzione", 
                        "Il thread del bot non si è fermato correttamente. " +
                        "L'applicazione continuerà a funzionare, ma potrebbe essere necessario riavviarla."
                    ))
                    
                    # Imposta thread a None per evitare problemi
                    self.bot_thread = None
            
            # Log
            self.logger.info("Trading bot fermato", "GUI")
            
        except Exception as e:
            self.logger.error(f"Errore nell'arresto del trading bot: {e}", "GUI")
            # Mostra errore nel thread principale
            self.after(0, lambda: messagebox.showerror("Errore", f"Errore nell'arresto del trading bot: {e}"))
    
    def _bot_thread_func(self):
        """
        Funzione per il thread del trading bot.
        """
        # Flag per controllo terminazione
        self._bot_thread_exit_flag = False
        
        # Contatore per tentativi di riconnessione
        reconnect_attempts = 0
        max_reconnect_attempts = 10
        reconnect_interval = 5.0  # secondi
        last_reconnect_time = datetime.datetime.now() - datetime.timedelta(seconds=reconnect_interval)
        
        # Flag per stato connessione precedente
        was_connected = False
        
        while self.bot_active and not self._bot_thread_exit_flag:
            try:
                # Verifica se è richiesta la terminazione
                if not self.bot_active or self._bot_thread_exit_flag:
                    break
                
                # Verifica connessione a MT5 Keeper
                current_time = datetime.datetime.now()
                
                # Verifica connessione solo se:
                # 1. Non siamo connessi e è passato abbastanza tempo dall'ultimo tentativo
                # 2. Vogliamo verificare periodicamente la connessione anche se siamo connessi
                if (not self.mt5_client.connected and 
                    (current_time - last_reconnect_time).total_seconds() >= reconnect_interval):
                    
                    # Verifica connessione
                    connected = self.mt5_client.check_connection()
                    last_reconnect_time = current_time
                    
                    if connected:
                        # Reset contatore tentativi
                        reconnect_attempts = 0
                        
                        # Log solo se prima non eravamo connessi
                        if not was_connected:
                            self.logger.info("Trading bot: Connessione a MT5 Keeper ristabilita", "TradingBot")
                    else:
                        # Incrementa contatore tentativi
                        reconnect_attempts += 1
                        
                        # Log
                        self.logger.warning(f"Trading bot: MT5 Keeper non connesso, tentativo {reconnect_attempts}/{max_reconnect_attempts}", "TradingBot")
                        
                        # Se troppi tentativi, aumenta intervallo
                        if reconnect_attempts > max_reconnect_attempts:
                            reconnect_interval = min(60.0, reconnect_interval * 1.5)
                            self.logger.warning(f"Trading bot: Troppi tentativi falliti, aumento intervallo a {reconnect_interval}s", "TradingBot")
                            reconnect_attempts = 0  # Reset contatore
                    
                    # Aggiorna stato connessione precedente
                    was_connected = connected
                
                # Se non connesso, attendi e riprova
                if not self.mt5_client.connected:
                    # Attendi e riprova, ma controlla se è richiesta la terminazione
                    for _ in range(5):  # 5 secondi, ma con controllo ogni secondo
                        if not self.bot_active or self._bot_thread_exit_flag:
                            break
                        time.sleep(1.0)
                    continue
                
                # Siamo connessi, reset variabili riconnessione
                reconnect_attempts = 0
                reconnect_interval = 5.0
                was_connected = True
                
                # Esegui ciclo del bot
                if self.trading_bot:
                    signal = self.trading_bot.run_cycle()
                    
                    # Aggiorna segnale nel thread principale
                    if signal and self.bot_active:  # Verifica ancora che il bot sia attivo
                        try:
                            # Estrai informazioni dal segnale
                            if isinstance(signal, str):
                                # Formato: "buy XAUUSD @ 1.1652074405677213"
                                parts = signal.split(" ")
                                if len(parts) >= 4 and parts[2] == "@":
                                    signal_text = {
                                        "action": parts[0],
                                        "symbol": parts[1],
                                        "price": float(parts[3])
                                    }
                                else:
                                    signal_text = signal
                            else:
                                # Il segnale è già un dizionario o altro tipo
                                signal_text = signal
                            
                            # Aggiorna UI nel thread principale
                            if self.bot_active:  # Verifica ancora che il bot sia attivo
                                self.after(0, lambda s=signal_text: self.dashboard.update_last_signal(s))
                        except Exception as e:
                            self.logger.error(f"Errore nell'elaborazione del segnale: {e}", "TradingBot")
                
                # Aggiorna dati per grafici solo se il bot è ancora attivo
                if self.bot_active and not self._bot_thread_exit_flag:
                    try:
                        # Aggiorna dati direttamente invece di creare un nuovo thread
                        self._update_chart_data()
                    except Exception as e:
                        self.logger.error(f"Errore nell'aggiornamento dei dati per i grafici: {e}", "GUI")
                
            except Exception as e:
                self.logger.error(f"Errore nel ciclo del trading bot: {e}", "TradingBot")
                # Breve pausa in caso di errore per evitare loop troppo rapidi
                time.sleep(1.0)
                continue
            
            # Attendi, ma controlla se è richiesta la terminazione
            for _ in range(10):  # 1 secondo, ma con controllo ogni 0.1 secondi
                if not self.bot_active or self._bot_thread_exit_flag:
                    break
                time.sleep(0.1)
        
        self.logger.info("Thread del trading bot terminato", "TradingBot")
    
    def _update_chart_data_thread(self):
        """
        Thread per aggiornamento dati grafici.
        """
        try:
            # Ottieni dati account
            account_info = self.mt5_client.get_account_info()
            
            if account_info:
                # Prepara dati
                equity_data = {
                    "time": datetime.datetime.now(),
                    "equity": account_info.get("equity", 0.0)
                }
                
                balance_data = {
                    "time": datetime.datetime.now(),
                    "balance": account_info.get("balance", 0.0)
                }
                
                # Aggiorna dati nel thread principale
                self.after(0, lambda e=equity_data, b=balance_data: self._update_chart_data_ui(e, b))
        
        except Exception as e:
            self.logger.error(f"Errore nell'aggiornamento dei dati per i grafici: {e}", "GUI")
    
    def _update_chart_data_ui(self, equity_data, balance_data):
        """
        Aggiorna UI con dati per grafici.
        
        Args:
            equity_data: Dati equity
            balance_data: Dati balance
        """
        try:
            # Aggiungi dati
            self.equity_history.append(equity_data)
            self.balance_history.append(balance_data)
            
            # Limita dimensione
            max_history = 1000
            if len(self.equity_history) > max_history:
                self.equity_history = self.equity_history[-max_history:]
            
            if len(self.balance_history) > max_history:
                self.balance_history = self.balance_history[-max_history:]
            
            # Aggiorna grafici
            self.charts.update_equity_data(self.equity_history, self.balance_history)
            
        except Exception as e:
            self.logger.error(f"Errore nell'aggiornamento dell'interfaccia dei grafici: {e}", "GUI")
    
    def _update_chart_data(self):
        """
        Aggiorna i dati per i grafici.
        """
        try:
            # Ottieni dati account
            account_info = self.mt5_client.get_account_info()
            
            if account_info:
                # Aggiungi dati equity
                self.equity_history.append({
                    "time": datetime.datetime.now(),
                    "equity": account_info.get("equity", 0.0)
                })
                
                # Aggiungi dati balance
                self.balance_history.append({
                    "time": datetime.datetime.now(),
                    "balance": account_info.get("balance", 0.0)
                })
                
                # Limita dimensione
                max_history = 1000
                if len(self.equity_history) > max_history:
                    self.equity_history = self.equity_history[-max_history:]
                
                if len(self.balance_history) > max_history:
                    self.balance_history = self.balance_history[-max_history:]
                
                # Aggiorna grafici
                self.charts.update_equity_data(self.equity_history, self.balance_history)
        
        except Exception as e:
            self.logger.error(f"Errore nell'aggiornamento dei dati per i grafici: {e}", "GUI")

def main():
    """
    Funzione principale.
    """
    app = MT5TradingBotGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
