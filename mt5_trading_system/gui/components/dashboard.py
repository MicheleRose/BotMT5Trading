#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard - Componente per il monitoraggio dell'account.

Questo modulo fornisce un componente per visualizzare le informazioni sull'account
e lo stato del trading bot.
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import time
import datetime
from typing import Dict, Any, Optional, List, Callable, Union

class Dashboard(tb.Frame):
    """
    Componente per il monitoraggio dell'account.
    """
    
    def __init__(self, parent, mt5_client, logger, **kwargs):
        """
        Inizializza il componente Dashboard.
        
        Args:
            parent: Widget genitore
            mt5_client: Client MT5
            logger: Logger
            **kwargs: Parametri aggiuntivi per Frame
        """
        super().__init__(parent, **kwargs)
        
        self.mt5_client = mt5_client
        self.logger = logger
        
        # Stato connessione
        self.connection_status = False
        
        # Dati account
        self.account_info = {}
        
        # Crea interfaccia
        self._create_widgets()
        
        # Registra callback per aggiornamenti
        self.mt5_client.on_connection_change = self._on_connection_change
        self.mt5_client.on_account_update = self._on_account_update
    
    def _create_widgets(self):
        """
        Crea i widget dell'interfaccia.
        """
        # Frame principale con padding
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # Titolo
        title_frame = tb.Frame(main_frame)
        title_frame.pack(fill=X, pady=(0, 10))
        
        title_label = tb.Label(
            title_frame,
            text="Dashboard",
            font=("TkDefaultFont", 16, "bold"),
            bootstyle="primary"
        )
        title_label.pack(side=LEFT)
        
        # Indicatore connessione
        self.connection_frame = tb.Frame(title_frame)
        self.connection_frame.pack(side=RIGHT)
        
        self.connection_indicator = tb.Label(
            self.connection_frame,
            text="●",
            font=("TkDefaultFont", 16),
            bootstyle="danger"
        )
        self.connection_indicator.pack(side=LEFT, padx=(0, 5))
        
        self.connection_label = tb.Label(
            self.connection_frame,
            text="Disconnesso",
            bootstyle="danger"
        )
        self.connection_label.pack(side=LEFT)
        
        # Informazioni account
        account_frame = tb.LabelFrame(main_frame, text="Informazioni Account", padding=10)
        account_frame.pack(fill=X, pady=10)
        
        # Griglia per informazioni account
        account_grid = tb.Frame(account_frame)
        account_grid.pack(fill=X)
        
        # Riga 1: Login e Server
        tb.Label(account_grid, text="Login:").grid(row=0, column=0, sticky=W, padx=5, pady=2)
        self.login_label = tb.Label(account_grid, text="---")
        self.login_label.grid(row=0, column=1, sticky=W, padx=5, pady=2)
        
        tb.Label(account_grid, text="Server:").grid(row=0, column=2, sticky=W, padx=5, pady=2)
        self.server_label = tb.Label(account_grid, text="---")
        self.server_label.grid(row=0, column=3, sticky=W, padx=5, pady=2)
        
        # Riga 2: Valuta e Leva
        tb.Label(account_grid, text="Valuta:").grid(row=1, column=0, sticky=W, padx=5, pady=2)
        self.currency_label = tb.Label(account_grid, text="---")
        self.currency_label.grid(row=1, column=1, sticky=W, padx=5, pady=2)
        
        tb.Label(account_grid, text="Leva:").grid(row=1, column=2, sticky=W, padx=5, pady=2)
        self.leverage_label = tb.Label(account_grid, text="---")
        self.leverage_label.grid(row=1, column=3, sticky=W, padx=5, pady=2)
        
        # Riga 3: Bilancio e Equity
        tb.Label(account_grid, text="Bilancio:").grid(row=2, column=0, sticky=W, padx=5, pady=2)
        self.balance_label = tb.Label(account_grid, text="---")
        self.balance_label.grid(row=2, column=1, sticky=W, padx=5, pady=2)
        
        tb.Label(account_grid, text="Equity:").grid(row=2, column=2, sticky=W, padx=5, pady=2)
        self.equity_label = tb.Label(account_grid, text="---")
        self.equity_label.grid(row=2, column=3, sticky=W, padx=5, pady=2)
        
        # Riga 4: Margine e Margine Libero
        tb.Label(account_grid, text="Margine:").grid(row=3, column=0, sticky=W, padx=5, pady=2)
        self.margin_label = tb.Label(account_grid, text="---")
        self.margin_label.grid(row=3, column=1, sticky=W, padx=5, pady=2)
        
        tb.Label(account_grid, text="Margine Libero:").grid(row=3, column=2, sticky=W, padx=5, pady=2)
        self.free_margin_label = tb.Label(account_grid, text="---")
        self.free_margin_label.grid(row=3, column=3, sticky=W, padx=5, pady=2)
        
        # Riga 5: Livello Margine e Profitto
        tb.Label(account_grid, text="Livello Margine:").grid(row=4, column=0, sticky=W, padx=5, pady=2)
        self.margin_level_label = tb.Label(account_grid, text="---")
        self.margin_level_label.grid(row=4, column=1, sticky=W, padx=5, pady=2)
        
        tb.Label(account_grid, text="Profitto:").grid(row=4, column=2, sticky=W, padx=5, pady=2)
        self.profit_label = tb.Label(account_grid, text="---")
        self.profit_label.grid(row=4, column=3, sticky=W, padx=5, pady=2)
        
        # Stato Trading Bot
        bot_frame = tb.LabelFrame(main_frame, text="Stato Trading Bot", padding=10)
        bot_frame.pack(fill=X, pady=10)
        
        # Griglia per stato bot
        bot_grid = tb.Frame(bot_frame)
        bot_grid.pack(fill=X)
        
        # Riga 1: Stato e Simbolo
        tb.Label(bot_grid, text="Stato:").grid(row=0, column=0, sticky=W, padx=5, pady=2)
        self.bot_status_label = tb.Label(bot_grid, text="Inattivo", bootstyle="danger")
        self.bot_status_label.grid(row=0, column=1, sticky=W, padx=5, pady=2)
        
        tb.Label(bot_grid, text="Simbolo:").grid(row=0, column=2, sticky=W, padx=5, pady=2)
        self.symbol_label = tb.Label(bot_grid, text="---")
        self.symbol_label.grid(row=0, column=3, sticky=W, padx=5, pady=2)
        
        # Riga 2: Timeframe e Dimensione Lotto
        tb.Label(bot_grid, text="Timeframe:").grid(row=1, column=0, sticky=W, padx=5, pady=2)
        self.timeframe_label = tb.Label(bot_grid, text="---")
        self.timeframe_label.grid(row=1, column=1, sticky=W, padx=5, pady=2)
        
        tb.Label(bot_grid, text="Dimensione Lotto:").grid(row=1, column=2, sticky=W, padx=5, pady=2)
        self.lot_size_label = tb.Label(bot_grid, text="---")
        self.lot_size_label.grid(row=1, column=3, sticky=W, padx=5, pady=2)
        
        # Riga 3: Posizioni Aperte e Ultimo Segnale
        tb.Label(bot_grid, text="Posizioni Aperte:").grid(row=2, column=0, sticky=W, padx=5, pady=2)
        self.open_positions_label = tb.Label(bot_grid, text="0")
        self.open_positions_label.grid(row=2, column=1, sticky=W, padx=5, pady=2)
        
        tb.Label(bot_grid, text="Ultimo Segnale:").grid(row=2, column=2, sticky=W, padx=5, pady=2)
        self.last_signal_label = tb.Label(bot_grid, text="---")
        self.last_signal_label.grid(row=2, column=3, sticky=W, padx=5, pady=2)
        
        # Riga 4: Ultimo Aggiornamento
        tb.Label(bot_grid, text="Ultimo Aggiornamento:").grid(row=3, column=0, sticky=W, padx=5, pady=2)
        self.last_update_label = tb.Label(bot_grid, text="---")
        self.last_update_label.grid(row=3, column=1, columnspan=3, sticky=W, padx=5, pady=2)
        
        # Pulsanti di controllo
        control_frame = tb.Frame(main_frame)
        control_frame.pack(fill=X, pady=10)
        
        # Pulsante Connetti
        self.connect_button = tb.Button(
            control_frame,
            text="Connetti a MT5",
            bootstyle="primary",
            command=self._on_connect
        )
        self.connect_button.pack(side=LEFT, padx=5)
        
        # Pulsante Disconnetti
        self.disconnect_button = tb.Button(
            control_frame,
            text="Disconnetti",
            bootstyle="secondary",
            state=DISABLED,
            command=self._on_disconnect
        )
        self.disconnect_button.pack(side=LEFT, padx=5)
        
        # Separatore
        tb.Separator(control_frame, orient="vertical").pack(side=LEFT, padx=10, fill=Y)
        
        # Pulsanti Bot
        self.start_button = tb.Button(
            control_frame,
            text="Avvia Bot",
            bootstyle="success",
            state=DISABLED,  # Disabilitato finché non siamo connessi
            command=self._on_start_bot
        )
        self.start_button.pack(side=LEFT, padx=5)
        
        self.stop_button = tb.Button(
            control_frame,
            text="Ferma Bot",
            bootstyle="danger",
            state=DISABLED,
            command=self._on_stop_bot
        )
        self.stop_button.pack(side=LEFT, padx=5)
        
        # Separatore
        tb.Separator(control_frame, orient="vertical").pack(side=LEFT, padx=10, fill=Y)
        
        # Pulsante Aggiorna
        self.refresh_button = tb.Button(
            control_frame,
            text="Aggiorna",
            bootstyle="info",
            command=self._on_refresh
        )
        self.refresh_button.pack(side=LEFT, padx=5)
    
    def _on_connect(self) -> None:
        """
        Callback per connessione manuale a MT5 Keeper.
        """
        # Mostra messaggio di attesa
        self.connect_button.configure(text="Connessione...", state=DISABLED)
        
        # Avvia thread per connessione
        threading.Thread(target=self._connect_thread, daemon=True).start()
    
    def _connect_thread(self) -> None:
        """
        Thread per connessione a MT5 Keeper.
        """
        try:
            # Verifica connessione
            connected = self.mt5_client.check_connection()
            
            # Aggiorna UI nel thread principale
            if connected:
                self.after(0, self._on_connect_success)
            else:
                self.after(0, self._on_connect_failure)
                
        except Exception as e:
            self.logger.error(f"Errore nella connessione a MT5 Keeper: {e}")
            self.after(0, self._on_connect_failure)
    
    def _on_connect_success(self) -> None:
        """
        Callback per connessione riuscita.
        """
        # Aggiorna pulsanti
        self.connect_button.configure(text="Connetti a MT5", state=DISABLED)
        self.disconnect_button.configure(state=NORMAL)
        self.start_button.configure(state=NORMAL)
        
        # Aggiorna informazioni account
        account_info = self.mt5_client.get_account_info()
        self._on_account_update(account_info)
        
        # Log
        self.logger.info("Connessione manuale a MT5 Keeper riuscita")
    
    def _on_connect_failure(self) -> None:
        """
        Callback per connessione fallita.
        """
        # Aggiorna pulsanti
        self.connect_button.configure(text="Connetti a MT5", state=NORMAL)
        
        # Log
        self.logger.error("Connessione manuale a MT5 Keeper fallita")
    
    def _on_disconnect(self) -> None:
        """
        Callback per disconnessione manuale da MT5 Keeper.
        """
        # Aggiorna pulsanti
        self.connect_button.configure(state=NORMAL)
        self.disconnect_button.configure(state=DISABLED)
        self.start_button.configure(state=DISABLED)
        self.stop_button.configure(state=DISABLED)
        
        # Aggiorna stato connessione
        self.connection_status = False
        self.connection_indicator.configure(bootstyle="danger")
        self.connection_label.configure(text="Disconnesso", bootstyle="danger")
        
        # Log
        self.logger.info("Disconnessione manuale da MT5 Keeper")
    
    def _on_connection_change(self, connected: bool) -> None:
        """
        Callback per cambiamento stato connessione.
        
        Args:
            connected: True se connesso, False altrimenti
        """
        self.connection_status = connected
        
        # Aggiorna interfaccia
        if connected:
            self.connection_indicator.configure(bootstyle="success")
            self.connection_label.configure(text="Connesso", bootstyle="success")
            self.connect_button.configure(state=DISABLED)
            self.disconnect_button.configure(state=NORMAL)
            self.start_button.configure(state=NORMAL)
            self.logger.info("Connesso a MT5 Keeper")
        else:
            self.connection_indicator.configure(bootstyle="danger")
            self.connection_label.configure(text="Disconnesso", bootstyle="danger")
            self.connect_button.configure(state=NORMAL)
            self.disconnect_button.configure(state=DISABLED)
            self.start_button.configure(state=DISABLED)
            self.stop_button.configure(state=DISABLED)
            self.logger.warning("Disconnesso da MT5 Keeper")
    
    def _on_account_update(self, account_info: Dict[str, Any]) -> None:
        """
        Callback per aggiornamento informazioni account.
        
        Args:
            account_info: Informazioni account
        """
        self.account_info = account_info
        
        # Aggiorna interfaccia
        self.login_label.configure(text=str(account_info.get("login", "---")))
        self.server_label.configure(text=account_info.get("server", "---"))
        self.currency_label.configure(text=account_info.get("currency", "---"))
        self.leverage_label.configure(text=f"1:{account_info.get('leverage', '---')}")
        
        # Formatta valori numerici
        balance = account_info.get("balance", 0.0)
        equity = account_info.get("equity", 0.0)
        margin = account_info.get("margin", 0.0)
        free_margin = account_info.get("free_margin", 0.0)
        margin_level = account_info.get("margin_level", 0.0)
        profit = account_info.get("profit", 0.0)
        
        self.balance_label.configure(text=f"{balance:.2f}")
        self.equity_label.configure(text=f"{equity:.2f}")
        self.margin_label.configure(text=f"{margin:.2f}")
        self.free_margin_label.configure(text=f"{free_margin:.2f}")
        self.margin_level_label.configure(text=f"{margin_level:.2f}%")
        
        # Imposta colore per profitto
        if profit > 0:
            self.profit_label.configure(text=f"+{profit:.2f}", bootstyle="success")
        elif profit < 0:
            self.profit_label.configure(text=f"{profit:.2f}", bootstyle="danger")
        else:
            self.profit_label.configure(text=f"{profit:.2f}", bootstyle="default")
        
        # Aggiorna timestamp
        self.last_update_label.configure(
            text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def update_bot_status(self, active: bool, config: Optional[Dict[str, Any]] = None, positions_count: int = 0) -> None:
        """
        Aggiorna lo stato del trading bot.
        
        Args:
            active: True se il bot è attivo, False altrimenti
            config: Configurazione del bot (opzionale)
            positions_count: Numero di posizioni aperte
        """
        # Aggiorna stato
        if active:
            self.bot_status_label.configure(text="Attivo", bootstyle="success")
            self.start_button.configure(state=DISABLED)
            self.stop_button.configure(state=NORMAL)
        else:
            self.bot_status_label.configure(text="Inattivo", bootstyle="danger")
            self.start_button.configure(state=NORMAL)
            self.stop_button.configure(state=DISABLED)
        
        # Aggiorna configurazione
        if config:
            self.symbol_label.configure(text=config.get("trading", {}).get("symbol", "---"))
            self.timeframe_label.configure(text=config.get("trading", {}).get("timeframe", "---"))
            self.lot_size_label.configure(text=str(config.get("trading", {}).get("lot_size", "---")))
        
        # Aggiorna posizioni
        self.open_positions_label.configure(text=str(positions_count))
        
        # Aggiorna timestamp
        self.last_update_label.configure(
            text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def update_last_signal(self, signal: Union[str, Dict[str, Any]]) -> None:
        """
        Aggiorna l'ultimo segnale di trading.
        
        Args:
            signal: Segnale di trading (stringa o dizionario)
        """
        try:
            # Se il segnale è un dizionario, estrai l'azione
            if isinstance(signal, dict):
                action = signal.get("action", "")
                symbol = signal.get("symbol", "")
                price = signal.get("price", 0.0)
                
                if action.upper() == "BUY":
                    self.last_signal_label.configure(text=f"BUY {symbol} @ {price:.5f}", bootstyle="success")
                elif action.upper() == "SELL":
                    self.last_signal_label.configure(text=f"SELL {symbol} @ {price:.5f}", bootstyle="danger")
                else:
                    self.last_signal_label.configure(text=str(signal), bootstyle="default")
            
            # Se il segnale è una stringa
            elif isinstance(signal, str):
                if signal.upper() == "BUY":
                    self.last_signal_label.configure(text="BUY", bootstyle="success")
                elif signal.upper() == "SELL":
                    self.last_signal_label.configure(text="SELL", bootstyle="danger")
                else:
                    self.last_signal_label.configure(text=signal, bootstyle="default")
            
            # Altro tipo di segnale
            else:
                self.last_signal_label.configure(text=str(signal), bootstyle="default")
                
        except Exception as e:
            self.logger.error(f"Errore nell'aggiornamento del segnale: {e}")
            self.last_signal_label.configure(text="Errore", bootstyle="danger")
    
    def _on_start_bot(self) -> None:
        """
        Callback per avvio del trading bot.
        """
        # Questo metodo sarà implementato nella classe principale
        # Qui emettiamo solo un evento che sarà catturato dalla classe principale
        self.event_generate("<<StartBot>>")
    
    def _on_stop_bot(self) -> None:
        """
        Callback per arresto del trading bot.
        """
        # Questo metodo sarà implementato nella classe principale
        # Qui emettiamo solo un evento che sarà catturato dalla classe principale
        self.event_generate("<<StopBot>>")
    
    def _on_refresh(self) -> None:
        """
        Callback per aggiornamento manuale.
        """
        # Verifica connessione
        self.mt5_client.check_connection()
        
        # Se connesso, aggiorna informazioni account
        if self.connection_status:
            account_info = self.mt5_client.get_account_info()
            self._on_account_update(account_info)
            
            # Log
            self.logger.info("Aggiornamento manuale completato")
        else:
            self.logger.warning("Impossibile aggiornare: non connesso a MT5 Keeper")
