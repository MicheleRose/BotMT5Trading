#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logs - Componente per la visualizzazione dei log.

Questo modulo fornisce un componente per visualizzare i log del trading bot.
"""

import tkinter as tk
from tkinter import ttk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import time
import datetime
from typing import Dict, Any, Optional, List, Callable

class Logs(tb.Frame):
    """
    Componente per la visualizzazione dei log.
    """
    
    def __init__(self, parent, logger, **kwargs):
        """
        Inizializza il componente Logs.
        
        Args:
            parent: Widget genitore
            logger: Logger
            **kwargs: Parametri aggiuntivi per Frame
        """
        super().__init__(parent, **kwargs)
        
        self.logger = logger
        
        # Filtri
        self.level_filter = None
        self.module_filter = None
        self.search_text = ""
        
        # Aggiornamento automatico
        self.auto_update = True
        self.update_interval = 1.0  # secondi
        self.update_thread = None
        self.update_active = False
        
        # Crea interfaccia
        self._create_widgets()
        
        # Avvia aggiornamento automatico
        self._start_auto_update()
    
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
            text="Log Operazioni",
            font=("TkDefaultFont", 16, "bold"),
            bootstyle="primary"
        )
        title_label.pack(side=LEFT)
        
        # Filtri
        filter_frame = tb.Frame(title_frame)
        filter_frame.pack(side=RIGHT)
        
        # Filtro livello
        tb.Label(filter_frame, text="Livello:").pack(side=LEFT, padx=(0, 5))
        self.level_var = tk.StringVar(value="Tutti")
        level_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.level_var,
            values=["Tutti", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            width=10
        )
        level_combo.pack(side=LEFT, padx=5)
        level_combo.bind("<<ComboboxSelected>>", self._on_filter_change)
        
        # Filtro modulo
        tb.Label(filter_frame, text="Modulo:").pack(side=LEFT, padx=(10, 5))
        self.module_var = tk.StringVar(value="Tutti")
        module_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.module_var,
            values=["Tutti", "GUI", "TradingBot", "MT5Client"],
            width=12
        )
        module_combo.pack(side=LEFT, padx=5)
        module_combo.bind("<<ComboboxSelected>>", self._on_filter_change)
        
        # Ricerca
        search_frame = tb.Frame(main_frame)
        search_frame.pack(fill=X, pady=(0, 10))
        
        tb.Label(search_frame, text="Cerca:").pack(side=LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        search_entry = tb.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=LEFT, fill=X, expand=YES, padx=5)
        search_entry.bind("<Return>", self._on_search)
        
        search_button = tb.Button(
            search_frame,
            text="Cerca",
            bootstyle="info",
            command=self._on_search
        )
        search_button.pack(side=LEFT, padx=5)
        
        clear_button = tb.Button(
            search_frame,
            text="Pulisci",
            bootstyle="secondary",
            command=self._on_clear_search
        )
        clear_button.pack(side=LEFT, padx=5)
        
        # Auto-aggiornamento
        self.auto_update_var = tk.BooleanVar(value=True)
        auto_update_check = tb.Checkbutton(
            search_frame,
            text="Auto-aggiornamento",
            variable=self.auto_update_var,
            command=self._on_auto_update_change
        )
        auto_update_check.pack(side=RIGHT, padx=5)
        
        # Tabella log
        log_frame = tb.Frame(main_frame)
        log_frame.pack(fill=BOTH, expand=YES)
        
        # Colonne
        columns = ("timestamp", "level", "module", "message")
        
        # Treeview
        self.log_tree = ttk.Treeview(
            log_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Configura colonne
        self.log_tree.heading("timestamp", text="Timestamp")
        self.log_tree.heading("level", text="Livello")
        self.log_tree.heading("module", text="Modulo")
        self.log_tree.heading("message", text="Messaggio")
        
        # Imposta larghezza colonne
        self.log_tree.column("timestamp", width=150)
        self.log_tree.column("level", width=80)
        self.log_tree.column("module", width=100)
        self.log_tree.column("message", width=500)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(log_frame, orient=VERTICAL, command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.log_tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Pulsanti
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X, pady=(10, 0))
        
        refresh_button = tb.Button(
            button_frame,
            text="Aggiorna",
            bootstyle="info",
            command=self._on_refresh
        )
        refresh_button.pack(side=LEFT, padx=5)
        
        clear_logs_button = tb.Button(
            button_frame,
            text="Cancella Log",
            bootstyle="danger",
            command=self._on_clear_logs
        )
        clear_logs_button.pack(side=LEFT, padx=5)
        
        export_button = tb.Button(
            button_frame,
            text="Esporta",
            bootstyle="secondary",
            command=self._on_export
        )
        export_button.pack(side=RIGHT, padx=5)
    
    def _update_log_tree(self):
        """
        Aggiorna la tabella dei log.
        """
        # Cancella log esistenti
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        
        # Ottieni messaggi filtrati
        messages = self._get_filtered_messages()
        
        # Aggiungi messaggi
        for message in messages:
            # Formatta timestamp
            timestamp = datetime.datetime.fromisoformat(message["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            
            # Aggiungi alla tabella
            item_id = self.log_tree.insert(
                "",
                "end",
                values=(
                    timestamp,
                    message["level"],
                    message["module"],
                    message["message"]
                )
            )
            
            # Imposta colore in base al livello
            if message["level"] == "ERROR" or message["level"] == "CRITICAL":
                self.log_tree.item(item_id, tags=("error",))
            elif message["level"] == "WARNING":
                self.log_tree.item(item_id, tags=("warning",))
            elif message["level"] == "DEBUG":
                self.log_tree.item(item_id, tags=("debug",))
        
        # Configura tag per colori
        self.log_tree.tag_configure("error", foreground="red")
        self.log_tree.tag_configure("warning", foreground="orange")
        self.log_tree.tag_configure("debug", foreground="gray")
        
        # Scorri alla fine
        if self.log_tree.get_children():
            self.log_tree.see(self.log_tree.get_children()[-1])
    
    def _get_filtered_messages(self) -> List[Dict[str, Any]]:
        """
        Ottiene i messaggi filtrati.
        
        Returns:
            Lista di messaggi filtrati
        """
        # Ottieni messaggi
        messages = self.logger.get_gui_messages()
        
        # Filtra per livello
        if self.level_filter and self.level_filter != "Tutti":
            messages = [m for m in messages if m["level"] == self.level_filter]
        
        # Filtra per modulo
        if self.module_filter and self.module_filter != "Tutti":
            messages = [m for m in messages if m["module"] == self.module_filter]
        
        # Filtra per testo
        if self.search_text:
            messages = [m for m in messages if self.search_text.lower() in m["message"].lower()]
        
        return messages
    
    def _on_filter_change(self, event=None):
        """
        Callback per cambio filtro.
        """
        self.level_filter = self.level_var.get()
        self.module_filter = self.module_var.get()
        self._update_log_tree()
    
    def _on_search(self, event=None):
        """
        Callback per ricerca.
        """
        self.search_text = self.search_var.get()
        self._update_log_tree()
    
    def _on_clear_search(self):
        """
        Callback per pulizia ricerca.
        """
        self.search_var.set("")
        self.search_text = ""
        self._update_log_tree()
    
    def _on_refresh(self):
        """
        Callback per aggiornamento manuale.
        """
        self._update_log_tree()
    
    def _on_clear_logs(self):
        """
        Callback per pulizia log.
        """
        self.logger.clear_gui_messages()
        self._update_log_tree()
    
    def _on_export(self):
        """
        Callback per esportazione log.
        """
        # Implementazione futura
        pass
    
    def _on_auto_update_change(self):
        """
        Callback per cambio auto-aggiornamento.
        """
        self.auto_update = self.auto_update_var.get()
        
        if self.auto_update:
            self._start_auto_update()
        else:
            self._stop_auto_update()
    
    def _start_auto_update(self):
        """
        Avvia l'aggiornamento automatico.
        """
        if self.update_thread and self.update_thread.is_alive():
            return
        
        self.update_active = True
        self.update_thread = threading.Thread(
            target=self._auto_update_loop,
            daemon=True
        )
        self.update_thread.start()
    
    def _stop_auto_update(self):
        """
        Ferma l'aggiornamento automatico.
        """
        self.update_active = False
        if self.update_thread:
            self.update_thread.join(timeout=1.0)
    
    def _auto_update_loop(self):
        """
        Loop di aggiornamento automatico.
        """
        while self.update_active:
            # Aggiorna log
            try:
                self.after(0, self._update_log_tree)
            except Exception:
                pass
            
            # Attendi
            time.sleep(self.update_interval)
