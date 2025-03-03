#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Charts - Componente per la visualizzazione dei grafici.

Questo modulo fornisce un componente per visualizzare i grafici di mercato
e le performance del trading bot.
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import time
import datetime
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.dates as mdates
import numpy as np
from typing import Dict, Any, Optional, List, Callable, Tuple

class Charts(tb.Frame):
    """
    Componente per la visualizzazione dei grafici.
    """
    
    def __init__(self, parent, mt5_client, logger, **kwargs):
        """
        Inizializza il componente Charts.
        
        Args:
            parent: Widget genitore
            mt5_client: Client MT5
            logger: Logger
            **kwargs: Parametri aggiuntivi per Frame
        """
        super().__init__(parent, **kwargs)
        
        self.mt5_client = mt5_client
        self.logger = logger
        
        # Dati
        self.market_data = []
        self.equity_data = []
        self.balance_data = []
        self.profit_data = []
        
        # Simbolo e timeframe correnti
        self.current_symbol = "EURUSD"
        self.current_timeframe = "M5"
        
        # Crea interfaccia
        self._create_widgets()
    
    def _create_widgets(self):
        """
        Crea i widget dell'interfaccia.
        """
        # Frame principale con padding
        main_frame = tb.Frame(self, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # Titolo e controlli
        title_frame = tb.Frame(main_frame)
        title_frame.pack(fill=X, pady=(0, 10))
        
        title_label = tb.Label(
            title_frame,
            text="Grafici",
            font=("TkDefaultFont", 16, "bold"),
            bootstyle="primary"
        )
        title_label.pack(side=LEFT)
        
        # Controlli
        control_frame = tb.Frame(title_frame)
        control_frame.pack(side=RIGHT)
        
        # Simbolo
        tb.Label(control_frame, text="Simbolo:").pack(side=LEFT, padx=(0, 5))
        self.symbol_var = tk.StringVar(value=self.current_symbol)
        symbol_combo = ttk.Combobox(
            control_frame,
            textvariable=self.symbol_var,
            values=["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD"],
            width=10
        )
        symbol_combo.pack(side=LEFT, padx=5)
        symbol_combo.bind("<<ComboboxSelected>>", self._on_symbol_change)
        
        # Timeframe
        tb.Label(control_frame, text="Timeframe:").pack(side=LEFT, padx=(10, 5))
        self.timeframe_var = tk.StringVar(value=self.current_timeframe)
        timeframe_combo = ttk.Combobox(
            control_frame,
            textvariable=self.timeframe_var,
            values=["M1", "M5", "M15", "M30", "H1", "H4", "D1"],
            width=5
        )
        timeframe_combo.pack(side=LEFT, padx=5)
        timeframe_combo.bind("<<ComboboxSelected>>", self._on_timeframe_change)
        
        # Aggiorna
        refresh_button = tb.Button(
            control_frame,
            text="Aggiorna",
            bootstyle="info",
            command=self._on_refresh
        )
        refresh_button.pack(side=LEFT, padx=5)
        
        # Notebook per grafici
        self.chart_notebook = ttk.Notebook(main_frame)
        self.chart_notebook.pack(fill=BOTH, expand=YES)
        
        # Tab Grafico Mercato
        self.market_frame = tb.Frame(self.chart_notebook)
        self.chart_notebook.add(self.market_frame, text="Grafico Mercato")
        
        # Tab Equity
        self.equity_frame = tb.Frame(self.chart_notebook)
        self.chart_notebook.add(self.equity_frame, text="Equity")
        
        # Tab Profitto
        self.profit_frame = tb.Frame(self.chart_notebook)
        self.chart_notebook.add(self.profit_frame, text="Profitto")
        
        # Crea grafici
        self._create_market_chart()
        self._create_equity_chart()
        self._create_profit_chart()
        
        # Non caricare dati iniziali, aspetta che l'utente prema il pulsante Aggiorna
        # o che il bot sia avviato
        # self._load_market_data()
    
    def _create_market_chart(self):
        """
        Crea il grafico di mercato.
        """
        # Crea figura
        self.market_figure = Figure(figsize=(10, 6), dpi=100)
        self.market_ax = self.market_figure.add_subplot(111)
        
        # Canvas
        self.market_canvas = FigureCanvasTkAgg(self.market_figure, master=self.market_frame)
        self.market_canvas.draw()
        self.market_canvas.get_tk_widget().pack(fill=BOTH, expand=YES)
        
        # Toolbar
        toolbar_frame = tb.Frame(self.market_frame)
        toolbar_frame.pack(fill=X)
        toolbar = NavigationToolbar2Tk(self.market_canvas, toolbar_frame)
        toolbar.update()
    
    def _create_equity_chart(self):
        """
        Crea il grafico dell'equity.
        """
        # Crea figura
        self.equity_figure = Figure(figsize=(10, 6), dpi=100)
        self.equity_ax = self.equity_figure.add_subplot(111)
        
        # Canvas
        self.equity_canvas = FigureCanvasTkAgg(self.equity_figure, master=self.equity_frame)
        self.equity_canvas.draw()
        self.equity_canvas.get_tk_widget().pack(fill=BOTH, expand=YES)
        
        # Toolbar
        toolbar_frame = tb.Frame(self.equity_frame)
        toolbar_frame.pack(fill=X)
        toolbar = NavigationToolbar2Tk(self.equity_canvas, toolbar_frame)
        toolbar.update()
    
    def _create_profit_chart(self):
        """
        Crea il grafico del profitto.
        """
        # Crea figura
        self.profit_figure = Figure(figsize=(10, 6), dpi=100)
        self.profit_ax = self.profit_figure.add_subplot(111)
        
        # Canvas
        self.profit_canvas = FigureCanvasTkAgg(self.profit_figure, master=self.profit_frame)
        self.profit_canvas.draw()
        self.profit_canvas.get_tk_widget().pack(fill=BOTH, expand=YES)
        
        # Toolbar
        toolbar_frame = tb.Frame(self.profit_frame)
        toolbar_frame.pack(fill=X)
        toolbar = NavigationToolbar2Tk(self.profit_canvas, toolbar_frame)
        toolbar.update()
    
    def _load_market_data(self):
        """
        Carica i dati di mercato.
        """
        try:
            # Ottieni dati
            self.market_data = self.mt5_client.get_market_data(
                self.current_symbol,
                self.current_timeframe,
                count=100
            )
            
            # Aggiorna grafico
            self._update_market_chart()
            
            # Log
            self.logger.info(f"Dati di mercato caricati per {self.current_symbol} {self.current_timeframe}")
            
        except Exception as e:
            self.logger.error(f"Errore nel caricamento dei dati di mercato: {e}")
    
    def _update_market_chart(self):
        """
        Aggiorna il grafico di mercato.
        """
        if not self.market_data:
            return
        
        # Pulisci grafico
        self.market_ax.clear()
        
        # Estrai dati
        dates = [datetime.datetime.fromisoformat(candle["time"]) for candle in self.market_data]
        opens = [candle["open"] for candle in self.market_data]
        highs = [candle["high"] for candle in self.market_data]
        lows = [candle["low"] for candle in self.market_data]
        closes = [candle["close"] for candle in self.market_data]
        
        # Calcola colori
        colors = ["green" if closes[i] >= opens[i] else "red" for i in range(len(closes))]
        
        # Disegna candele
        width = 0.6
        width2 = 0.1
        
        # Disegna candele
        for i in range(len(dates)):
            # Corpo candela
            self.market_ax.bar(
                dates[i],
                closes[i] - opens[i],
                width,
                bottom=opens[i],
                color=colors[i],
                alpha=0.7
            )
            
            # Ombra
            self.market_ax.plot(
                [dates[i], dates[i]],
                [lows[i], highs[i]],
                color=colors[i],
                linewidth=1
            )
        
        # Formatta asse x
        self.market_ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
        self.market_ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Titolo e etichette
        self.market_ax.set_title(f"{self.current_symbol} - {self.current_timeframe}")
        self.market_ax.set_xlabel("Data/Ora")
        self.market_ax.set_ylabel("Prezzo")
        
        # Griglia
        self.market_ax.grid(True, alpha=0.3)
        
        # Ruota etichette
        plt = self.market_figure.canvas
        self.market_figure.autofmt_xdate()
        
        # Aggiorna canvas
        self.market_canvas.draw()
    
    def _update_equity_chart(self):
        """
        Aggiorna il grafico dell'equity.
        """
        if not self.equity_data or not self.balance_data:
            return
        
        # Pulisci grafico
        self.equity_ax.clear()
        
        # Estrai dati
        dates = [item["time"] for item in self.equity_data]
        equity = [item["equity"] for item in self.equity_data]
        balance = [item["balance"] for item in self.balance_data]
        
        # Disegna linee
        self.equity_ax.plot(dates, equity, label="Equity", color="blue", linewidth=2)
        self.equity_ax.plot(dates, balance, label="Bilancio", color="green", linewidth=2)
        
        # Formatta asse x
        self.equity_ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
        self.equity_ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Titolo e etichette
        self.equity_ax.set_title("Equity e Bilancio")
        self.equity_ax.set_xlabel("Data/Ora")
        self.equity_ax.set_ylabel("Valore")
        
        # Griglia
        self.equity_ax.grid(True, alpha=0.3)
        
        # Legenda
        self.equity_ax.legend()
        
        # Ruota etichette
        plt = self.equity_figure.canvas
        self.equity_figure.autofmt_xdate()
        
        # Aggiorna canvas
        self.equity_canvas.draw()
    
    def _update_profit_chart(self):
        """
        Aggiorna il grafico del profitto.
        """
        if not self.profit_data:
            return
        
        # Pulisci grafico
        self.profit_ax.clear()
        
        # Estrai dati
        dates = [item["time"] for item in self.profit_data]
        profits = [item["profit"] for item in self.profit_data]
        
        # Calcola colori
        colors = ["green" if profit >= 0 else "red" for profit in profits]
        
        # Disegna barre
        self.profit_ax.bar(dates, profits, color=colors, alpha=0.7)
        
        # Formatta asse x
        self.profit_ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
        self.profit_ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Titolo e etichette
        self.profit_ax.set_title("Profitto Operazioni")
        self.profit_ax.set_xlabel("Data/Ora")
        self.profit_ax.set_ylabel("Profitto")
        
        # Griglia
        self.profit_ax.grid(True, alpha=0.3)
        
        # Ruota etichette
        plt = self.profit_figure.canvas
        self.profit_figure.autofmt_xdate()
        
        # Aggiorna canvas
        self.profit_canvas.draw()
    
    def _on_symbol_change(self, event=None):
        """
        Callback per cambio simbolo.
        """
        self.current_symbol = self.symbol_var.get()
        self._load_market_data()
    
    def _on_timeframe_change(self, event=None):
        """
        Callback per cambio timeframe.
        """
        self.current_timeframe = self.timeframe_var.get()
        self._load_market_data()
    
    def _on_refresh(self):
        """
        Callback per aggiornamento manuale.
        """
        self._load_market_data()
    
    def update_equity_data(self, equity_data: List[Dict[str, Any]], balance_data: List[Dict[str, Any]]):
        """
        Aggiorna i dati dell'equity.
        
        Args:
            equity_data: Dati equity
            balance_data: Dati bilancio
        """
        self.equity_data = equity_data
        self.balance_data = balance_data
        self._update_equity_chart()
    
    def update_profit_data(self, profit_data: List[Dict[str, Any]]):
        """
        Aggiorna i dati del profitto.
        
        Args:
            profit_data: Dati profitto
        """
        self.profit_data = profit_data
        self._update_profit_chart()
