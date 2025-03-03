#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config - Componente per la gestione della configurazione del trading bot.

Questo modulo fornisce un componente per visualizzare e modificare la configurazione
del trading bot.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import json
import os
from typing import Dict, Any, Optional, List, Callable

class Config(tb.Frame):
    """
    Componente per la gestione della configurazione del trading bot.
    """
    
    def __init__(self, parent, config_manager, logger, **kwargs):
        """
        Inizializza il componente Config.
        
        Args:
            parent: Widget genitore
            config_manager: Gestore configurazione
            logger: Logger
            **kwargs: Parametri aggiuntivi per Frame
        """
        super().__init__(parent, **kwargs)
        
        self.config_manager = config_manager
        self.logger = logger
        
        # Crea interfaccia
        self._create_widgets()
        
        # Carica configurazione
        self._load_config()
    
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
            text="Configurazione Trading Bot",
            font=("TkDefaultFont", 16, "bold"),
            bootstyle="primary"
        )
        title_label.pack(side=LEFT)
        
        # Pulsanti di controllo
        control_frame = tb.Frame(title_frame)
        control_frame.pack(side=RIGHT)
        
        self.load_button = tb.Button(
            control_frame,
            text="Carica",
            bootstyle="info",
            command=self._on_load
        )
        self.load_button.pack(side=LEFT, padx=5)
        
        self.save_button = tb.Button(
            control_frame,
            text="Salva",
            bootstyle="success",
            command=self._on_save
        )
        self.save_button.pack(side=LEFT, padx=5)
        
        self.reset_button = tb.Button(
            control_frame,
            text="Reset",
            bootstyle="danger",
            command=self._on_reset
        )
        self.reset_button.pack(side=LEFT, padx=5)
        
        # Notebook per categorie
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=BOTH, expand=YES, pady=10)
        
        # Tab Trading
        self.trading_frame = self._create_trading_tab()
        self.notebook.add(self.trading_frame, text="Trading")
        
        # Tab Risk Management
        self.risk_frame = self._create_risk_tab()
        self.notebook.add(self.risk_frame, text="Risk Management")
        
        # Tab Execution
        self.execution_frame = self._create_execution_tab()
        self.notebook.add(self.execution_frame, text="Execution")
        
        # Tab Stop Loss/Take Profit
        self.sltp_frame = self._create_sltp_tab()
        self.notebook.add(self.sltp_frame, text="Stop Loss/Take Profit")
        
        # Tab Indicators
        self.indicators_frame = self._create_indicators_tab()
        self.notebook.add(self.indicators_frame, text="Indicators")
        
        # Tab Logging
        self.logging_frame = self._create_logging_tab()
        self.notebook.add(self.logging_frame, text="Logging")
    
    def _create_trading_tab(self) -> tb.Frame:
        """
        Crea il tab per la configurazione del trading.
        
        Returns:
            Frame per il tab
        """
        frame = tb.Frame(self.notebook, padding=10)
        
        # Griglia per form
        form_grid = tb.Frame(frame)
        form_grid.pack(fill=BOTH, expand=YES)
        
        # Broker
        row = 0
        tb.Label(form_grid, text="Broker:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.broker_var = tk.StringVar()
        broker_entry = tb.Entry(form_grid, textvariable=self.broker_var)
        broker_entry.grid(row=row, column=1, sticky=(W, E), padx=5, pady=5)
        
        # Symbol
        row += 1
        tb.Label(form_grid, text="Simbolo:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.symbol_var = tk.StringVar()
        symbol_combo = ttk.Combobox(form_grid, textvariable=self.symbol_var, values=self.config_manager.get_symbols())
        symbol_combo.grid(row=row, column=1, sticky=(W, E), padx=5, pady=5)
        
        # Timeframe
        row += 1
        tb.Label(form_grid, text="Timeframe:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.timeframe_var = tk.StringVar()
        timeframe_combo = ttk.Combobox(form_grid, textvariable=self.timeframe_var, values=self.config_manager.get_timeframes())
        timeframe_combo.grid(row=row, column=1, sticky=(W, E), padx=5, pady=5)
        
        # Lot Size
        row += 1
        tb.Label(form_grid, text="Dimensione Lotto:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.lot_size_var = tk.DoubleVar()
        lot_size_entry = tb.Spinbox(
            form_grid,
            textvariable=self.lot_size_var,
            from_=0.01,
            to=100.0,
            increment=0.01,
            width=10
        )
        lot_size_entry.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        
        # Trade Frequency
        row += 1
        tb.Label(form_grid, text="Frequenza Trading (sec):").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.trade_frequency_var = tk.IntVar()
        trade_frequency_entry = tb.Spinbox(
            form_grid,
            textvariable=self.trade_frequency_var,
            from_=1,
            to=3600,
            increment=1,
            width=10
        )
        trade_frequency_entry.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        
        # Max Trades Open
        row += 1
        tb.Label(form_grid, text="Max Posizioni Aperte:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.max_trades_var = tk.IntVar()
        max_trades_entry = tb.Spinbox(
            form_grid,
            textvariable=self.max_trades_var,
            from_=1,
            to=100,
            increment=1,
            width=10
        )
        max_trades_entry.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        
        # Spread Limit
        row += 1
        tb.Label(form_grid, text="Limite Spread (punti):").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.spread_limit_var = tk.IntVar()
        spread_limit_entry = tb.Spinbox(
            form_grid,
            textvariable=self.spread_limit_var,
            from_=0,
            to=1000,
            increment=1,
            width=10
        )
        spread_limit_entry.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        
        # Adaptive Risk
        row += 1
        self.adaptive_risk_var = tk.BooleanVar()
        adaptive_risk_check = tb.Checkbutton(
            form_grid,
            text="Rischio Adattivo",
            variable=self.adaptive_risk_var
        )
        adaptive_risk_check.grid(row=row, column=0, columnspan=2, sticky=W, padx=5, pady=5)
        
        # Profit Trailing
        row += 1
        self.profit_trailing_var = tk.BooleanVar()
        profit_trailing_check = tb.Checkbutton(
            form_grid,
            text="Trailing Profit",
            variable=self.profit_trailing_var
        )
        profit_trailing_check.grid(row=row, column=0, columnspan=2, sticky=W, padx=5, pady=5)
        
        # Strict Mode
        row += 1
        self.strict_mode_var = tk.BooleanVar()
        strict_mode_check = tb.Checkbutton(
            form_grid,
            text="Modalità Strict",
            variable=self.strict_mode_var
        )
        strict_mode_check.grid(row=row, column=0, columnspan=2, sticky=W, padx=5, pady=5)
        
        # Lot Increment Every
        row += 1
        tb.Label(form_grid, text="Incremento Lotto Ogni:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.lot_increment_var = tk.IntVar()
        lot_increment_entry = tb.Spinbox(
            form_grid,
            textvariable=self.lot_increment_var,
            from_=0,
            to=100,
            increment=1,
            width=10
        )
        lot_increment_entry.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        
        # Position Management
        row += 1
        position_frame = tb.LabelFrame(form_grid, text="Gestione Posizioni", padding=10)
        position_frame.grid(row=row, column=0, columnspan=2, sticky=(W, E), padx=5, pady=10)
        
        # Min Pips Between Orders
        tb.Label(position_frame, text="Min Pips Tra Ordini:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.min_pips_var = tk.IntVar()
        min_pips_entry = tb.Spinbox(
            position_frame,
            textvariable=self.min_pips_var,
            from_=0,
            to=1000,
            increment=1,
            width=10
        )
        min_pips_entry.grid(row=0, column=1, sticky=W, padx=5, pady=5)
        
        # Floating Profit Close Percentage
        tb.Label(position_frame, text="% Chiusura Profit:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.floating_profit_var = tk.DoubleVar()
        floating_profit_entry = tb.Spinbox(
            position_frame,
            textvariable=self.floating_profit_var,
            from_=0.0,
            to=100.0,
            increment=0.1,
            width=10
        )
        floating_profit_entry.grid(row=1, column=1, sticky=W, padx=5, pady=5)
        
        # Hedge Protection
        self.hedge_protection_var = tk.BooleanVar()
        hedge_protection_check = tb.Checkbutton(
            position_frame,
            text="Protezione Hedge",
            variable=self.hedge_protection_var
        )
        hedge_protection_check.grid(row=2, column=0, columnspan=2, sticky=W, padx=5, pady=5)
        
        return frame
    
    def _load_config(self) -> None:
        """
        Carica la configurazione dal file e aggiorna l'interfaccia.
        """
        # Carica configurazione
        config = self.config_manager.load()
        
        # Trading
        self.broker_var.set(config.get("trading", {}).get("broker", ""))
        self.symbol_var.set(config.get("trading", {}).get("symbol", ""))
        self.timeframe_var.set(config.get("trading", {}).get("timeframe", ""))
        self.lot_size_var.set(config.get("trading", {}).get("lot_size", 0.01))
        self.trade_frequency_var.set(config.get("trading", {}).get("trade_frequency_seconds", 5))
        self.max_trades_var.set(config.get("trading", {}).get("max_trades_open", 10))
        self.spread_limit_var.set(config.get("trading", {}).get("spread_limit_points", 20))
        self.adaptive_risk_var.set(config.get("trading", {}).get("adaptive_risk", False))
        self.profit_trailing_var.set(config.get("trading", {}).get("profit_trailing", False))
        self.strict_mode_var.set(config.get("trading", {}).get("strict_mode", False))
        self.lot_increment_var.set(config.get("trading", {}).get("lot_increment_every", 5))
        
        # Position Management
        position_management = config.get("trading", {}).get("position_management", {})
        self.min_pips_var.set(position_management.get("min_pips_between_orders", 10))
        self.floating_profit_var.set(position_management.get("floating_profit_close_percentage", 1.0))
        self.hedge_protection_var.set(position_management.get("hedge_protection", False))
        
        # Risk Management
        risk_management = config.get("risk_management", {})
        self.max_drawdown_var.set(risk_management.get("max_drawdown_percentage", 10))
        self.min_free_margin_var.set(risk_management.get("minimum_free_margin", 100))
        
        # Capital Protection Thresholds
        thresholds = risk_management.get("capital_protection_thresholds", {})
        self.threshold_5000_var.set(thresholds.get("5000", 0.15))
        self.threshold_10000_var.set(thresholds.get("10000", 0.10))
        self.threshold_50000_var.set(thresholds.get("50000", 0.05))
        
        # Execution
        execution = config.get("execution", {})
        self.order_type_var.set(execution.get("order_type", "market"))
        self.deviation_var.set(execution.get("deviation", 5))
        self.magic_number_var.set(execution.get("magic_number", 123456))
        self.order_comment_var.set(execution.get("order_comment", "MT5 Trading Bot"))
        self.type_filling_var.set(execution.get("type_filling", "IOC"))
        self.type_time_var.set(execution.get("type_time", "GTC"))
        
        # Stop Loss/Take Profit
        sltp = config.get("stop_loss_take_profit", {})
        self.use_atr_var.set(sltp.get("use_atr", True))
        self.atr_multiplier_sl_var.set(sltp.get("atr_multiplier_sl", 1.5))
        self.atr_multiplier_tp_var.set(sltp.get("atr_multiplier_tp", 2.0))
        self.default_sl_pips_var.set(sltp.get("default_sl_pips", 30))
        self.default_tp_pips_var.set(sltp.get("default_tp_pips", 50))
        self.increase_sl_var.set(sltp.get("increase_sl_if_trend_confident", True))
        
        # Indicators
        indicators = config.get("indicators", {})
        
        # EMA
        ema = indicators.get("ema", {})
        self.ema_fast_var.set(ema.get("fast_period", 9))
        self.ema_slow_var.set(ema.get("slow_period", 21))
        
        # RSI
        rsi = indicators.get("rsi", {})
        self.rsi_period_var.set(rsi.get("period", 14))
        self.rsi_oversold_var.set(rsi.get("oversold", 30))
        self.rsi_overbought_var.set(rsi.get("overbought", 70))
        
        # MACD
        macd = indicators.get("macd", {})
        self.macd_fast_var.set(macd.get("fast_period", 12))
        self.macd_slow_var.set(macd.get("slow_period", 26))
        self.macd_signal_var.set(macd.get("signal_period", 9))
        
        # Bollinger
        bollinger = indicators.get("bollinger", {})
        self.bollinger_period_var.set(bollinger.get("period", 20))
        self.bollinger_std_dev_var.set(bollinger.get("std_dev", 2))
        
        # ADX
        adx = indicators.get("adx", {})
        self.adx_period_var.set(adx.get("period", 14))
        self.adx_threshold_var.set(adx.get("threshold", 25))
        
        # ATR
        atr = indicators.get("atr", {})
        self.atr_period_var.set(atr.get("period", 14))
        
        # Logging
        logging_config = config.get("logging", {})
        self.log_file_var.set(logging_config.get("log_file", "logs/trading.log"))
        self.error_file_var.set(logging_config.get("error_file", "logs/error.log"))
        self.log_level_var.set(logging_config.get("log_level", "INFO"))
        
        # Log
        self.logger.info("Configurazione caricata")
    
    def _get_config_from_ui(self) -> Dict[str, Any]:
        """
        Ottiene la configurazione dall'interfaccia utente.
        
        Returns:
            Configurazione
        """
        config = {}
        
        # Trading
        config["trading"] = {
            "broker": self.broker_var.get(),
            "symbol": self.symbol_var.get(),
            "timeframe": self.timeframe_var.get(),
            "lot_size": self.lot_size_var.get(),
            "trade_frequency_seconds": self.trade_frequency_var.get(),
            "max_trades_open": self.max_trades_var.get(),
            "spread_limit_points": self.spread_limit_var.get(),
            "adaptive_risk": self.adaptive_risk_var.get(),
            "profit_trailing": self.profit_trailing_var.get(),
            "strict_mode": self.strict_mode_var.get(),
            "lot_increment_every": self.lot_increment_var.get(),
            "position_management": {
                "min_pips_between_orders": self.min_pips_var.get(),
                "floating_profit_close_percentage": self.floating_profit_var.get(),
                "hedge_protection": self.hedge_protection_var.get()
            }
        }
        
        # Risk Management
        config["risk_management"] = {
            "max_drawdown_percentage": self.max_drawdown_var.get(),
            "minimum_free_margin": self.min_free_margin_var.get(),
            "capital_protection_thresholds": {
                "5000": self.threshold_5000_var.get(),
                "10000": self.threshold_10000_var.get(),
                "50000": self.threshold_50000_var.get()
            }
        }
        
        # Execution
        config["execution"] = {
            "order_type": self.order_type_var.get(),
            "deviation": self.deviation_var.get(),
            "magic_number": self.magic_number_var.get(),
            "order_comment": self.order_comment_var.get(),
            "type_filling": self.type_filling_var.get(),
            "type_time": self.type_time_var.get()
        }
        
        # Stop Loss/Take Profit
        config["stop_loss_take_profit"] = {
            "use_atr": self.use_atr_var.get(),
            "atr_multiplier_sl": self.atr_multiplier_sl_var.get(),
            "atr_multiplier_tp": self.atr_multiplier_tp_var.get(),
            "default_sl_pips": self.default_sl_pips_var.get(),
            "default_tp_pips": self.default_tp_pips_var.get(),
            "increase_sl_if_trend_confident": self.increase_sl_var.get()
        }
        
        # Indicators
        config["indicators"] = {
            "ema": {
                "fast_period": self.ema_fast_var.get(),
                "slow_period": self.ema_slow_var.get()
            },
            "rsi": {
                "period": self.rsi_period_var.get(),
                "oversold": self.rsi_oversold_var.get(),
                "overbought": self.rsi_overbought_var.get()
            },
            "macd": {
                "fast_period": self.macd_fast_var.get(),
                "slow_period": self.macd_slow_var.get(),
                "signal_period": self.macd_signal_var.get()
            },
            "bollinger": {
                "period": self.bollinger_period_var.get(),
                "std_dev": self.bollinger_std_dev_var.get()
            },
            "adx": {
                "period": self.adx_period_var.get(),
                "threshold": self.adx_threshold_var.get()
            },
            "atr": {
                "period": self.atr_period_var.get()
            }
        }
        
        # Logging
        config["logging"] = {
            "log_file": self.log_file_var.get(),
            "error_file": self.error_file_var.get(),
            "log_level": self.log_level_var.get()
        }
        
        return config
    
    def _on_load(self) -> None:
        """
        Callback per caricamento configurazione da file.
        """
        # Chiedi file
        file_path = filedialog.askopenfilename(
            title="Carica Configurazione",
            filetypes=[("JSON", "*.json"), ("Tutti i file", "*.*")],
            initialdir=os.path.dirname(self.config_manager.config_path)
        )
        
        if not file_path:
            return
        
        # Imposta nuovo percorso
        self.config_manager.config_path = file_path
        
        # Carica configurazione
        self._load_config()
        
        # Log
        self.logger.info(f"Configurazione caricata da {file_path}")
        messagebox.showinfo("Caricamento Completato", f"Configurazione caricata da {file_path}")
    
    def _on_save(self) -> None:
        """
        Callback per salvataggio configurazione su file.
        """
        # Chiedi file
        file_path = filedialog.asksaveasfilename(
            title="Salva Configurazione",
            filetypes=[("JSON", "*.json"), ("Tutti i file", "*.*")],
            initialdir=os.path.dirname(self.config_manager.config_path),
            defaultextension=".json"
        )
        
        if not file_path:
            return
        
        # Ottieni configurazione
        config = self._get_config_from_ui()
        
        # Imposta nuovo percorso
        old_path = self.config_manager.config_path
        self.config_manager.config_path = file_path
        
        # Salva configurazione
        if self.config_manager.save(config):
            # Log
            self.logger.info(f"Configurazione salvata su {file_path}")
            messagebox.showinfo("Salvataggio Completato", f"Configurazione salvata su {file_path}")
        else:
            # Ripristina percorso
            self.config_manager.config_path = old_path
            
            # Log
            self.logger.error(f"Errore nel salvataggio della configurazione su {file_path}")
            messagebox.showerror("Errore", f"Errore nel salvataggio della configurazione su {file_path}")
    
    def _on_reset(self) -> None:
        """
        Callback per reset configurazione.
        """
        # Chiedi conferma
        if not messagebox.askyesno("Conferma", "Sei sicuro di voler ripristinare la configurazione predefinita?"):
            return
        
        # Imposta configurazione predefinita
        self.config_manager.config = self.config_manager.default_config
        
        # Carica configurazione
        self._load_config()
        
        # Log
        self.logger.info("Configurazione ripristinata ai valori predefiniti")
        messagebox.showinfo("Reset Completato", "Configurazione ripristinata ai valori predefiniti")
    def _create_risk_tab(self) -> tb.Frame:
        """
        Crea il tab per la configurazione del risk management.
        
        Returns:
            Frame per il tab
        """
        frame = tb.Frame(self.notebook, padding=10)
        
        # Griglia per form
        form_grid = tb.Frame(frame)
        form_grid.pack(fill=BOTH, expand=YES)
        
        # Max Drawdown Percentage
        row = 0
        tb.Label(form_grid, text="Max Drawdown (%):").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.max_drawdown_var = tk.DoubleVar()
        max_drawdown_entry = tb.Spinbox(
            form_grid,
            textvariable=self.max_drawdown_var,
            from_=0.0,
            to=100.0,
            increment=0.1,
            width=10
        )
        max_drawdown_entry.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        
        # Minimum Free Margin
        row += 1
        tb.Label(form_grid, text="Margine Libero Minimo:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.min_free_margin_var = tk.DoubleVar()
        min_free_margin_entry = tb.Spinbox(
            form_grid,
            textvariable=self.min_free_margin_var,
            from_=0.0,
            to=10000.0,
            increment=10.0,
            width=10
        )
        min_free_margin_entry.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        
        # Capital Protection Thresholds
        row += 1
        thresholds_frame = tb.LabelFrame(form_grid, text="Soglie Protezione Capitale", padding=10)
        thresholds_frame.grid(row=row, column=0, columnspan=2, sticky=(W, E), padx=5, pady=10)
        
        # Threshold 5000
        tb.Label(thresholds_frame, text="Soglia 5000:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.threshold_5000_var = tk.DoubleVar()
        threshold_5000_entry = tb.Spinbox(
            thresholds_frame,
            textvariable=self.threshold_5000_var,
            from_=0.0,
            to=1.0,
            increment=0.01,
            width=10
        )
        threshold_5000_entry.grid(row=0, column=1, sticky=W, padx=5, pady=5)
        
        # Threshold 10000
        tb.Label(thresholds_frame, text="Soglia 10000:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.threshold_10000_var = tk.DoubleVar()
        threshold_10000_entry = tb.Spinbox(
            thresholds_frame,
            textvariable=self.threshold_10000_var,
            from_=0.0,
            to=1.0,
            increment=0.01,
            width=10
        )
        threshold_10000_entry.grid(row=1, column=1, sticky=W, padx=5, pady=5)
        
        # Threshold 50000
        tb.Label(thresholds_frame, text="Soglia 50000:").grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.threshold_50000_var = tk.DoubleVar()
        threshold_50000_entry = tb.Spinbox(
            thresholds_frame,
            textvariable=self.threshold_50000_var,
            from_=0.0,
            to=1.0,
            increment=0.01,
            width=10
        )
        threshold_50000_entry.grid(row=2, column=1, sticky=W, padx=5, pady=5)
        
        return frame
    
    def _create_execution_tab(self) -> tb.Frame:
        """
        Crea il tab per la configurazione dell'esecuzione.
        
        Returns:
            Frame per il tab
        """
        frame = tb.Frame(self.notebook, padding=10)
        
        # Griglia per form
        form_grid = tb.Frame(frame)
        form_grid.pack(fill=BOTH, expand=YES)
        
        # Order Type
        row = 0
        tb.Label(form_grid, text="Tipo Ordine:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.order_type_var = tk.StringVar()
        order_type_combo = ttk.Combobox(
            form_grid,
            textvariable=self.order_type_var,
            values=["market", "limit", "stop"]
        )
        order_type_combo.grid(row=row, column=1, sticky=(W, E), padx=5, pady=5)
        
        # Deviation
        row += 1
        tb.Label(form_grid, text="Deviazione:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.deviation_var = tk.IntVar()
        deviation_entry = tb.Spinbox(
            form_grid,
            textvariable=self.deviation_var,
            from_=0,
            to=100,
            increment=1,
            width=10
        )
        deviation_entry.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        
        # Magic Number
        row += 1
        tb.Label(form_grid, text="Magic Number:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.magic_number_var = tk.IntVar()
        magic_number_entry = tb.Entry(form_grid, textvariable=self.magic_number_var)
        magic_number_entry.grid(row=row, column=1, sticky=(W, E), padx=5, pady=5)
        
        # Order Comment
        row += 1
        tb.Label(form_grid, text="Commento Ordine:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.order_comment_var = tk.StringVar()
        order_comment_entry = tb.Entry(form_grid, textvariable=self.order_comment_var)
        order_comment_entry.grid(row=row, column=1, sticky=(W, E), padx=5, pady=5)
        
        # Type Filling
        row += 1
        tb.Label(form_grid, text="Tipo Filling:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.type_filling_var = tk.StringVar()
        type_filling_combo = ttk.Combobox(
            form_grid,
            textvariable=self.type_filling_var,
            values=["IOC", "FOK", "Return"]
        )
        type_filling_combo.grid(row=row, column=1, sticky=(W, E), padx=5, pady=5)
        
        # Type Time
        row += 1
        tb.Label(form_grid, text="Tipo Time:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.type_time_var = tk.StringVar()
        type_time_combo = ttk.Combobox(
            form_grid,
            textvariable=self.type_time_var,
            values=["GTC", "DAY", "Specified"]
        )
        type_time_combo.grid(row=row, column=1, sticky=(W, E), padx=5, pady=5)
        
        return frame
    
    def _create_sltp_tab(self) -> tb.Frame:
        """
        Crea il tab per la configurazione di stop loss e take profit.
        
        Returns:
            Frame per il tab
        """
        frame = tb.Frame(self.notebook, padding=10)
        
        # Griglia per form
        form_grid = tb.Frame(frame)
        form_grid.pack(fill=BOTH, expand=YES)
        
        # Use ATR
        row = 0
        self.use_atr_var = tk.BooleanVar()
        use_atr_check = tb.Checkbutton(
            form_grid,
            text="Usa ATR",
            variable=self.use_atr_var
        )
        use_atr_check.grid(row=row, column=0, columnspan=2, sticky=W, padx=5, pady=5)
        
        # ATR Multiplier SL
        row += 1
        tb.Label(form_grid, text="Moltiplicatore ATR SL:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.atr_multiplier_sl_var = tk.DoubleVar()
        atr_multiplier_sl_entry = tb.Spinbox(
            form_grid,
            textvariable=self.atr_multiplier_sl_var,
            from_=0.1,
            to=10.0,
            increment=0.1,
            width=10
        )
        atr_multiplier_sl_entry.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        
        # ATR Multiplier TP
        row += 1
        tb.Label(form_grid, text="Moltiplicatore ATR TP:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.atr_multiplier_tp_var = tk.DoubleVar()
        atr_multiplier_tp_entry = tb.Spinbox(
            form_grid,
            textvariable=self.atr_multiplier_tp_var,
            from_=0.1,
            to=10.0,
            increment=0.1,
            width=10
        )
        atr_multiplier_tp_entry.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        
        # Default SL Pips
        row += 1
        tb.Label(form_grid, text="SL Default (pips):").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.default_sl_pips_var = tk.IntVar()
        default_sl_pips_entry = tb.Spinbox(
            form_grid,
            textvariable=self.default_sl_pips_var,
            from_=1,
            to=1000,
            increment=1,
            width=10
        )
        default_sl_pips_entry.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        
        # Default TP Pips
        row += 1
        tb.Label(form_grid, text="TP Default (pips):").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.default_tp_pips_var = tk.IntVar()
        default_tp_pips_entry = tb.Spinbox(
            form_grid,
            textvariable=self.default_tp_pips_var,
            from_=1,
            to=1000,
            increment=1,
            width=10
        )
        default_tp_pips_entry.grid(row=row, column=1, sticky=W, padx=5, pady=5)
        
        # Increase SL if Trend Confident
        row += 1
        self.increase_sl_var = tk.BooleanVar()
        increase_sl_check = tb.Checkbutton(
            form_grid,
            text="Aumenta SL se Trend Confidente",
            variable=self.increase_sl_var
        )
        increase_sl_check.grid(row=row, column=0, columnspan=2, sticky=W, padx=5, pady=5)
        
        return frame
    
    def _create_indicators_tab(self) -> tb.Frame:
        """
        Crea il tab per la configurazione degli indicatori.
        
        Returns:
            Frame per il tab
        """
        frame = tb.Frame(self.notebook, padding=10)
        
        # Notebook per indicatori
        indicators_notebook = ttk.Notebook(frame)
        indicators_notebook.pack(fill=BOTH, expand=YES)
        
        # EMA
        ema_frame = tb.Frame(indicators_notebook, padding=10)
        indicators_notebook.add(ema_frame, text="EMA")
        
        tb.Label(ema_frame, text="Periodo Fast:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.ema_fast_var = tk.IntVar()
        ema_fast_entry = tb.Spinbox(
            ema_frame,
            textvariable=self.ema_fast_var,
            from_=1,
            to=200,
            increment=1,
            width=10
        )
        ema_fast_entry.grid(row=0, column=1, sticky=W, padx=5, pady=5)
        
        tb.Label(ema_frame, text="Periodo Slow:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.ema_slow_var = tk.IntVar()
        ema_slow_entry = tb.Spinbox(
            ema_frame,
            textvariable=self.ema_slow_var,
            from_=1,
            to=200,
            increment=1,
            width=10
        )
        ema_slow_entry.grid(row=1, column=1, sticky=W, padx=5, pady=5)
        
        # RSI
        rsi_frame = tb.Frame(indicators_notebook, padding=10)
        indicators_notebook.add(rsi_frame, text="RSI")
        
        tb.Label(rsi_frame, text="Periodo:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.rsi_period_var = tk.IntVar()
        rsi_period_entry = tb.Spinbox(
            rsi_frame,
            textvariable=self.rsi_period_var,
            from_=1,
            to=100,
            increment=1,
            width=10
        )
        rsi_period_entry.grid(row=0, column=1, sticky=W, padx=5, pady=5)
        
        tb.Label(rsi_frame, text="Oversold:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.rsi_oversold_var = tk.IntVar()
        rsi_oversold_entry = tb.Spinbox(
            rsi_frame,
            textvariable=self.rsi_oversold_var,
            from_=0,
            to=100,
            increment=1,
            width=10
        )
        rsi_oversold_entry.grid(row=1, column=1, sticky=W, padx=5, pady=5)
        
        tb.Label(rsi_frame, text="Overbought:").grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.rsi_overbought_var = tk.IntVar()
        rsi_overbought_entry = tb.Spinbox(
            rsi_frame,
            textvariable=self.rsi_overbought_var,
            from_=0,
            to=100,
            increment=1,
            width=10
        )
        rsi_overbought_entry.grid(row=2, column=1, sticky=W, padx=5, pady=5)
        
        # MACD
        macd_frame = tb.Frame(indicators_notebook, padding=10)
        indicators_notebook.add(macd_frame, text="MACD")
        
        tb.Label(macd_frame, text="Periodo Fast:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.macd_fast_var = tk.IntVar()
        macd_fast_entry = tb.Spinbox(
            macd_frame,
            textvariable=self.macd_fast_var,
            from_=1,
            to=100,
            increment=1,
            width=10
        )
        macd_fast_entry.grid(row=0, column=1, sticky=W, padx=5, pady=5)
        
        tb.Label(macd_frame, text="Periodo Slow:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.macd_slow_var = tk.IntVar()
        macd_slow_entry = tb.Spinbox(
            macd_frame,
            textvariable=self.macd_slow_var,
            from_=1,
            to=100,
            increment=1,
            width=10
        )
        macd_slow_entry.grid(row=1, column=1, sticky=W, padx=5, pady=5)
        
        tb.Label(macd_frame, text="Periodo Signal:").grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.macd_signal_var = tk.IntVar()
        macd_signal_entry = tb.Spinbox(
            macd_frame,
            textvariable=self.macd_signal_var,
            from_=1,
            to=100,
            increment=1,
            width=10
        )
        macd_signal_entry.grid(row=2, column=1, sticky=W, padx=5, pady=5)
        
        # Bollinger
        bollinger_frame = tb.Frame(indicators_notebook, padding=10)
        indicators_notebook.add(bollinger_frame, text="Bollinger")
        
        tb.Label(bollinger_frame, text="Periodo:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.bollinger_period_var = tk.IntVar()
        bollinger_period_entry = tb.Spinbox(
            bollinger_frame,
            textvariable=self.bollinger_period_var,
            from_=1,
            to=100,
            increment=1,
            width=10
        )
        bollinger_period_entry.grid(row=0, column=1, sticky=W, padx=5, pady=5)
        
        tb.Label(bollinger_frame, text="Deviazione Standard:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.bollinger_std_dev_var = tk.DoubleVar()
        bollinger_std_dev_entry = tb.Spinbox(
            bollinger_frame,
            textvariable=self.bollinger_std_dev_var,
            from_=0.1,
            to=5.0,
            increment=0.1,
            width=10
        )
        bollinger_std_dev_entry.grid(row=1, column=1, sticky=W, padx=5, pady=5)
        
        # ADX
        adx_frame = tb.Frame(indicators_notebook, padding=10)
        indicators_notebook.add(adx_frame, text="ADX")
        
        tb.Label(adx_frame, text="Periodo:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.adx_period_var = tk.IntVar()
        adx_period_entry = tb.Spinbox(
            adx_frame,
            textvariable=self.adx_period_var,
            from_=1,
            to=100,
            increment=1,
            width=10
        )
        adx_period_entry.grid(row=0, column=1, sticky=W, padx=5, pady=5)
        
        tb.Label(adx_frame, text="Soglia:").grid(row=1, column=0, sticky=W, padx=5, pady=5)
        self.adx_threshold_var = tk.IntVar()
        adx_threshold_entry = tb.Spinbox(
            adx_frame,
            textvariable=self.adx_threshold_var,
            from_=0,
            to=100,
            increment=1,
            width=10
        )
        adx_threshold_entry.grid(row=1, column=1, sticky=W, padx=5, pady=5)
        
        # ATR
        atr_frame = tb.Frame(indicators_notebook, padding=10)
        indicators_notebook.add(atr_frame, text="ATR")
        
        tb.Label(atr_frame, text="Periodo:").grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.atr_period_var = tk.IntVar()
        atr_period_entry = tb.Spinbox(
            atr_frame,
            textvariable=self.atr_period_var,
            from_=1,
            to=100,
            increment=1,
            width=10
        )
        atr_period_entry.grid(row=0, column=1, sticky=W, padx=5, pady=5)
        
        return frame
    
    def _create_logging_tab(self) -> tb.Frame:
        """
        Crea il tab per la configurazione del logging.
        
        Returns:
            Frame per il tab
        """
        frame = tb.Frame(self.notebook, padding=10)
        
        # Griglia per form
        form_grid = tb.Frame(frame)
        form_grid.pack(fill=BOTH, expand=YES)
        
        # Log File
        row = 0
        tb.Label(form_grid, text="File di Log:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.log_file_var = tk.StringVar()
        log_file_entry = tb.Entry(form_grid, textvariable=self.log_file_var)
        log_file_entry.grid(row=row, column=1, sticky=(W, E), padx=5, pady=5)
        
        # Error File
        row += 1
        tb.Label(form_grid, text="File di Errore:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.error_file_var = tk.StringVar()
        error_file_entry = tb.Entry(form_grid, textvariable=self.error_file_var)
        error_file_entry.grid(row=row, column=1, sticky=(W, E), padx=5, pady=5)
        
        # Log Level
        row += 1
        tb.Label(form_grid, text="Livello di Log:").grid(row=row, column=0, sticky=W, padx=5, pady=5)
        self.log_level_var = tk.StringVar()
        log_level_combo = ttk.Combobox(
            form_grid,
            textvariable=self.log_level_var,
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        )
        log_level_combo.grid(row=row, column=1, sticky=(W, E), padx=5, pady=5)
        
        return frame
