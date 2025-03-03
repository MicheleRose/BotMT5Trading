#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Positions - Componente per la visualizzazione delle posizioni aperte.

Questo modulo fornisce un componente per visualizzare le posizioni aperte
e gestirle (chiusura, modifica).
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import threading
import time
import datetime
from typing import Dict, Any, Optional, List, Callable

class Positions(tb.Frame):
    """
    Componente per la visualizzazione delle posizioni aperte.
    """
    
    def __init__(self, parent, mt5_client, logger, **kwargs):
        """
        Inizializza il componente Positions.
        
        Args:
            parent: Widget genitore
            mt5_client: Client MT5
            logger: Logger
            **kwargs: Parametri aggiuntivi per Frame
        """
        super().__init__(parent, **kwargs)
        
        self.mt5_client = mt5_client
        self.logger = logger
        
        # Posizioni
        self.positions = []
        
        # Crea interfaccia
        self._create_widgets()
        
        # Registra callback per aggiornamenti
        self.mt5_client.on_positions_update = self._on_positions_update
    
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
            text="Posizioni Aperte",
            font=("TkDefaultFont", 16, "bold"),
            bootstyle="primary"
        )
        title_label.pack(side=LEFT)
        
        # Pulsanti di controllo
        control_frame = tb.Frame(title_frame)
        control_frame.pack(side=RIGHT)
        
        self.refresh_button = tb.Button(
            control_frame,
            text="Aggiorna",
            bootstyle="info",
            command=self._on_refresh
        )
        self.refresh_button.pack(side=LEFT, padx=5)
        
        self.close_all_button = tb.Button(
            control_frame,
            text="Chiudi Tutte",
            bootstyle="danger",
            command=self._on_close_all
        )
        self.close_all_button.pack(side=LEFT, padx=5)
        
        # Treeview per posizioni
        columns = (
            "ticket", "time", "type", "symbol", "volume",
            "open_price", "current_price", "sl", "tp", "profit"
        )
        
        self.positions_tree = ttk.Treeview(
            main_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Configura colonne
        self.positions_tree.heading("ticket", text="Ticket")
        self.positions_tree.heading("time", text="Orario")
        self.positions_tree.heading("type", text="Tipo")
        self.positions_tree.heading("symbol", text="Simbolo")
        self.positions_tree.heading("volume", text="Volume")
        self.positions_tree.heading("open_price", text="Prezzo Apertura")
        self.positions_tree.heading("current_price", text="Prezzo Attuale")
        self.positions_tree.heading("sl", text="Stop Loss")
        self.positions_tree.heading("tp", text="Take Profit")
        self.positions_tree.heading("profit", text="Profitto")
        
        # Imposta larghezza colonne
        self.positions_tree.column("ticket", width=80)
        self.positions_tree.column("time", width=150)
        self.positions_tree.column("type", width=80)
        self.positions_tree.column("symbol", width=100)
        self.positions_tree.column("volume", width=80)
        self.positions_tree.column("open_price", width=120)
        self.positions_tree.column("current_price", width=120)
        self.positions_tree.column("sl", width=100)
        self.positions_tree.column("tp", width=100)
        self.positions_tree.column("profit", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient=VERTICAL, command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.positions_tree.pack(side=LEFT, fill=BOTH, expand=YES)
        scrollbar.pack(side=RIGHT, fill=Y)
        
        # Menu contestuale
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Chiudi Posizione", command=self._on_close_position)
        self.context_menu.add_command(label="Modifica Stop Loss/Take Profit", command=self._on_modify_position)
        
        # Bind eventi
        self.positions_tree.bind("<Button-3>", self._on_right_click)
        self.positions_tree.bind("<Double-1>", self._on_double_click)
    
    def _on_positions_update(self, positions: List[Dict[str, Any]]) -> None:
        """
        Callback per aggiornamento posizioni.
        
        Args:
            positions: Lista di posizioni
        """
        self.positions = positions
        self._update_positions_tree()
    
    def _update_positions_tree(self) -> None:
        """
        Aggiorna il treeview con le posizioni.
        """
        # Cancella posizioni esistenti
        for item in self.positions_tree.get_children():
            self.positions_tree.delete(item)
        
        # Aggiungi posizioni
        for position in self.positions:
            # Converti timestamp in data leggibile
            time_str = datetime.datetime.fromtimestamp(position["time"]).strftime("%Y-%m-%d %H:%M:%S")
            
            # Formatta valori
            ticket = position["ticket"]
            type_str = position["type"]
            symbol = position["symbol"]
            volume = position["volume"]
            open_price = position["open_price"]
            current_price = position["current_price"]
            sl = position["sl"] if position["sl"] > 0 else "-"
            tp = position["tp"] if position["tp"] > 0 else "-"
            profit = position["profit"]
            
            # Aggiungi alla tabella
            item_id = self.positions_tree.insert(
                "",
                "end",
                values=(
                    ticket, time_str, type_str, symbol, volume,
                    open_price, current_price, sl, tp, profit
                )
            )
            
            # Imposta colore in base al profitto
            if profit > 0:
                self.positions_tree.item(item_id, tags=("profit_positive",))
            elif profit < 0:
                self.positions_tree.item(item_id, tags=("profit_negative",))
        
        # Configura tag per colori
        self.positions_tree.tag_configure("profit_positive", foreground="green")
        self.positions_tree.tag_configure("profit_negative", foreground="red")
    
    def _on_refresh(self) -> None:
        """
        Callback per aggiornamento manuale.
        """
        try:
            positions = self.mt5_client.get_positions()
            self._on_positions_update(positions)
            self.logger.info("Posizioni aggiornate manualmente")
        except Exception as e:
            self.logger.error(f"Errore nell'aggiornamento delle posizioni: {e}")
            messagebox.showerror("Errore", f"Errore nell'aggiornamento delle posizioni: {e}")
    
    def _on_close_all(self) -> None:
        """
        Callback per chiusura di tutte le posizioni.
        """
        if not self.positions:
            messagebox.showinfo("Informazione", "Non ci sono posizioni aperte da chiudere")
            return
        
        # Chiedi conferma
        if not messagebox.askyesno("Conferma", "Sei sicuro di voler chiudere tutte le posizioni aperte?"):
            return
        
        try:
            result = self.mt5_client.close_all_positions()
            
            if result.get("positions_closed", 0) > 0:
                self.logger.info(f"Chiuse {result['positions_closed']} posizioni con profitto totale {result['total_profit']}")
                messagebox.showinfo("Successo", f"Chiuse {result['positions_closed']} posizioni con profitto totale {result['total_profit']}")
                
                # Aggiorna posizioni
                self._on_refresh()
            else:
                self.logger.warning("Nessuna posizione chiusa")
                messagebox.showinfo("Informazione", "Nessuna posizione chiusa")
                
        except Exception as e:
            self.logger.error(f"Errore nella chiusura delle posizioni: {e}")
            messagebox.showerror("Errore", f"Errore nella chiusura delle posizioni: {e}")
    
    def _on_right_click(self, event) -> None:
        """
        Callback per click destro su posizione.
        
        Args:
            event: Evento click
        """
        # Seleziona item sotto il cursore
        item = self.positions_tree.identify_row(event.y)
        if item:
            self.positions_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _on_double_click(self, event) -> None:
        """
        Callback per doppio click su posizione.
        
        Args:
            event: Evento click
        """
        # Seleziona item sotto il cursore
        item = self.positions_tree.identify_row(event.y)
        if item:
            self.positions_tree.selection_set(item)
            self._on_modify_position()
    
    def _on_close_position(self) -> None:
        """
        Callback per chiusura posizione selezionata.
        """
        # Ottieni posizione selezionata
        selection = self.positions_tree.selection()
        if not selection:
            return
        
        # Ottieni ticket
        item = selection[0]
        ticket = int(self.positions_tree.item(item, "values")[0])
        
        # Chiedi conferma
        if not messagebox.askyesno("Conferma", f"Sei sicuro di voler chiudere la posizione {ticket}?"):
            return
        
        try:
            result = self.mt5_client.close_position(ticket)
            
            if result.get("closed", False):
                self.logger.info(f"Posizione {ticket} chiusa con successo")
                messagebox.showinfo("Successo", f"Posizione {ticket} chiusa con successo")
                
                # Aggiorna posizioni
                self._on_refresh()
            else:
                self.logger.warning(f"Impossibile chiudere la posizione {ticket}")
                messagebox.showwarning("Attenzione", f"Impossibile chiudere la posizione {ticket}")
                
        except Exception as e:
            self.logger.error(f"Errore nella chiusura della posizione {ticket}: {e}")
            messagebox.showerror("Errore", f"Errore nella chiusura della posizione {ticket}: {e}")
    
    def _on_modify_position(self) -> None:
        """
        Callback per modifica posizione selezionata.
        """
        # Ottieni posizione selezionata
        selection = self.positions_tree.selection()
        if not selection:
            return
        
        # Ottieni ticket e valori attuali
        item = selection[0]
        values = self.positions_tree.item(item, "values")
        ticket = int(values[0])
        symbol = values[3]
        current_sl = values[7]
        current_tp = values[8]
        
        # Converti "-" in 0
        if current_sl == "-":
            current_sl = "0"
        
        if current_tp == "-":
            current_tp = "0"
        
        # Crea dialog per modifica
        dialog = tb.Toplevel(self)
        dialog.title(f"Modifica Posizione {ticket}")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        
        # Frame principale
        main_frame = tb.Frame(dialog, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)
        
        # Titolo
        title_label = tb.Label(
            main_frame,
            text=f"Modifica Posizione {ticket} ({symbol})",
            font=("TkDefaultFont", 12, "bold"),
            bootstyle="primary"
        )
        title_label.pack(pady=(0, 10))
        
        # Form
        form_frame = tb.Frame(main_frame)
        form_frame.pack(fill=X, pady=10)
        
        # Stop Loss
        sl_frame = tb.Frame(form_frame)
        sl_frame.pack(fill=X, pady=5)
        
        sl_label = tb.Label(sl_frame, text="Stop Loss:", width=15, anchor=E)
        sl_label.pack(side=LEFT, padx=5)
        
        sl_var = tk.StringVar(value=current_sl)
        sl_entry = tb.Entry(sl_frame, textvariable=sl_var)
        sl_entry.pack(side=LEFT, fill=X, expand=YES, padx=5)
        
        # Take Profit
        tp_frame = tb.Frame(form_frame)
        tp_frame.pack(fill=X, pady=5)
        
        tp_label = tb.Label(tp_frame, text="Take Profit:", width=15, anchor=E)
        tp_label.pack(side=LEFT, padx=5)
        
        tp_var = tk.StringVar(value=current_tp)
        tp_entry = tb.Entry(tp_frame, textvariable=tp_var)
        tp_entry.pack(side=LEFT, fill=X, expand=YES, padx=5)
        
        # Pulsanti
        button_frame = tb.Frame(main_frame)
        button_frame.pack(fill=X, pady=10)
        
        cancel_button = tb.Button(
            button_frame,
            text="Annulla",
            bootstyle="secondary",
            command=dialog.destroy
        )
        cancel_button.pack(side=RIGHT, padx=5)
        
        save_button = tb.Button(
            button_frame,
            text="Salva",
            bootstyle="primary",
            command=lambda: self._save_position_changes(dialog, ticket, sl_var.get(), tp_var.get())
        )
        save_button.pack(side=RIGHT, padx=5)
    
    def _save_position_changes(self, dialog, ticket: int, sl_str: str, tp_str: str) -> None:
        """
        Salva le modifiche alla posizione.
        
        Args:
            dialog: Dialog da chiudere
            ticket: Ticket della posizione
            sl_str: Stop Loss (stringa)
            tp_str: Take Profit (stringa)
        """
        try:
            # Converti valori
            sl = float(sl_str) if sl_str and sl_str != "-" else 0.0
            tp = float(tp_str) if tp_str and tp_str != "-" else 0.0
            
            # Modifica posizione
            result = self.mt5_client.modify_position(ticket, sl, tp)
            
            if result.get("modified", False):
                self.logger.info(f"Posizione {ticket} modificata con successo")
                messagebox.showinfo("Successo", f"Posizione {ticket} modificata con successo")
                
                # Aggiorna posizioni
                self._on_refresh()
                
                # Chiudi dialog
                dialog.destroy()
            else:
                self.logger.warning(f"Impossibile modificare la posizione {ticket}: {result.get('message', 'Errore sconosciuto')}")
                messagebox.showwarning("Attenzione", f"Impossibile modificare la posizione {ticket}: {result.get('message', 'Errore sconosciuto')}")
                
        except ValueError:
            messagebox.showerror("Errore", "Valori non validi. Inserisci numeri validi per Stop Loss e Take Profit.")
        except Exception as e:
            self.logger.error(f"Errore nella modifica della posizione {ticket}: {e}")
            messagebox.showerror("Errore", f"Errore nella modifica della posizione {ticket}: {e}")
