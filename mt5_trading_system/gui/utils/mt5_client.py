#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5 Client - Classe per la comunicazione con MT5 Keeper.

Questa classe estende MT5CommandBase per fornire funzionalità specifiche
per l'interfaccia grafica.
"""

import sys
import os
import json
import time
import logging
import threading
import datetime
from typing import Dict, Any, Optional, List, Callable, Tuple

# Importa la classe base MT5CommandBase
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from core.mt5_command_base import MT5CommandBase

# Configurazione logging
logger = logging.getLogger("MT5Client")

class MT5Client(MT5CommandBase):
    """
    Client per la comunicazione con MT5 Keeper.
    Estende MT5CommandBase con funzionalità specifiche per l'interfaccia grafica.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inizializza il client MT5.
        
        Args:
            config_path: Percorso al file di configurazione JSON (opzionale)
        """
        super().__init__(config_path)
        
        # Stato connessione
        self.connected = False
        self.last_check_time = datetime.datetime.now()
        self.check_interval = 5.0  # secondi
        
        # Callback per aggiornamenti
        self.on_connection_change: Optional[Callable[[bool], None]] = None
        self.on_account_update: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_positions_update: Optional[Callable[[List[Dict[str, Any]]], None]] = None
        
        # Thread per monitoraggio
        self.monitoring_thread = None
        self.monitoring_active = False
    
    def check_connection(self) -> bool:
        """
        Verifica la connessione a MT5 Keeper.
        
        Returns:
            True se connesso, False altrimenti
        """
        try:
            # Invia comando ping con timeout ridotto per evitare blocchi
            # Tenta più volte in caso di errore
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # Usa un timeout ancora più breve per il ping
                    result = self.send_command("ping", timeout=0.5)
                    
                    # Aggiorna stato connessione
                    was_connected = self.connected
                    self.connected = True
                    
                    # Notifica cambiamento stato connessione
                    if not was_connected and self.on_connection_change:
                        self.on_connection_change(True)
                        logger.info("Connessione a MT5 Keeper stabilita")
                    
                    # Aggiorna timestamp ultimo controllo
                    self.last_check_time = datetime.datetime.now()
                    
                    return True
                except TimeoutError:
                    # Timeout specifico, potrebbe essere un problema temporaneo
                    logger.debug(f"Timeout nella verifica della connessione (tentativo {attempt+1}/{max_attempts})")
                    
                    # Attendi un po' prima di riprovare, ma meno del precedente
                    if attempt < max_attempts - 1:
                        time.sleep(0.2)  # Ridotto da 0.5 a 0.2
                except Exception as e:
                    # Altri errori
                    logger.debug(f"Errore nella verifica della connessione (tentativo {attempt+1}/{max_attempts}): {e}")
                    
                    # Attendi un po' prima di riprovare, ma meno del precedente
                    if attempt < max_attempts - 1:
                        time.sleep(0.2)  # Ridotto da 0.5 a 0.2
            
            # Se arriviamo qui, tutti i tentativi sono falliti
            # Aggiorna stato connessione
            was_connected = self.connected
            self.connected = False
            
            # Notifica cambiamento stato connessione solo se prima eravamo connessi
            if was_connected and self.on_connection_change:
                self.on_connection_change(False)
                logger.warning("Connessione a MT5 Keeper persa")
            
            return False
            
        except Exception as e:
            # Errore non previsto
            logger.error(f"Errore non previsto nella verifica della connessione: {e}")
            
            # Aggiorna stato connessione
            was_connected = self.connected
            self.connected = False
            
            # Notifica cambiamento stato connessione solo se prima eravamo connessi
            if was_connected and self.on_connection_change:
                self.on_connection_change(False)
                logger.warning("Connessione a MT5 Keeper persa")
            
            return False
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Ottiene informazioni sull'account.
        
        Returns:
            Dizionario con informazioni sull'account
        """
        try:
            result = self.send_command("account_info")
            
            # Estrai informazioni principali
            account_info = {
                "login": result.get("login", 0),
                "server": result.get("server", ""),
                "currency": result.get("currency", ""),
                "leverage": result.get("leverage", 0),
                "balance": result.get("balance", 0.0),
                "equity": result.get("equity", 0.0),
                "margin": result.get("margin", 0.0),
                "free_margin": result.get("margin_free", 0.0),
                "margin_level": result.get("margin_level", 0.0),
                "profit": result.get("profit", 0.0)
            }
            
            return account_info
            
        except Exception as e:
            logger.error(f"Errore nell'ottenere informazioni sull'account: {e}")
            return {}
    
    def get_positions(self, symbol: Optional[str] = None, magic: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Ottiene le posizioni aperte.
        
        Args:
            symbol: Simbolo per filtrare le posizioni (opzionale)
            magic: Magic number per filtrare le posizioni (opzionale)
            
        Returns:
            Lista di posizioni aperte
        """
        try:
            # Prepara parametri
            params = {}
            
            # Aggiungi filtri solo se specificati
            if symbol:
                params["symbol"] = symbol.upper()
            
            if magic is not None:
                params["magic"] = magic
            
            # Invia comando
            result = self.send_command("get_positions", params)
            
            return result.get("positions", [])
            
        except Exception as e:
            logger.error(f"Errore nell'ottenere le posizioni: {e}")
            return []
    
    def market_buy(self, symbol: str, volume: float, sl: float = 0.0, tp: float = 0.0, 
                  magic: int = 0, comment: str = "") -> Dict[str, Any]:
        """
        Apre una posizione di acquisto a mercato.
        
        Args:
            symbol: Simbolo
            volume: Volume
            sl: Stop Loss (opzionale)
            tp: Take Profit (opzionale)
            magic: Magic number (opzionale)
            comment: Commento (opzionale)
            
        Returns:
            Risultato dell'operazione
        """
        try:
            # Prepara parametri
            params = {
                "symbol": symbol.upper(),
                "volume": volume
            }
            
            # Aggiungi parametri opzionali solo se specificati
            if sl > 0:
                params["sl"] = sl
            
            if tp > 0:
                params["tp"] = tp
            
            if magic > 0:
                params["magic"] = magic
            
            if comment:
                params["comment"] = comment
            
            # Invia comando
            result = self.send_command("market_buy", params)
            
            return result
            
        except Exception as e:
            logger.error(f"Errore nell'apertura della posizione di acquisto: {e}")
            return {"error": str(e)}
    
    def market_sell(self, symbol: str, volume: float, sl: float = 0.0, tp: float = 0.0, 
                   magic: int = 0, comment: str = "") -> Dict[str, Any]:
        """
        Apre una posizione di vendita a mercato.
        
        Args:
            symbol: Simbolo
            volume: Volume
            sl: Stop Loss (opzionale)
            tp: Take Profit (opzionale)
            magic: Magic number (opzionale)
            comment: Commento (opzionale)
            
        Returns:
            Risultato dell'operazione
        """
        try:
            # Prepara parametri
            params = {
                "symbol": symbol.upper(),
                "volume": volume
            }
            
            # Aggiungi parametri opzionali solo se specificati
            if sl > 0:
                params["sl"] = sl
            
            if tp > 0:
                params["tp"] = tp
            
            if magic > 0:
                params["magic"] = magic
            
            if comment:
                params["comment"] = comment
            
            # Invia comando
            result = self.send_command("market_sell", params)
            
            return result
            
        except Exception as e:
            logger.error(f"Errore nell'apertura della posizione di vendita: {e}")
            return {"error": str(e)}
    
    def close_position(self, ticket: int, volume: Optional[float] = None) -> Dict[str, Any]:
        """
        Chiude una posizione.
        
        Args:
            ticket: Ticket della posizione
            volume: Volume da chiudere (opzionale, se non specificato chiude tutta la posizione)
            
        Returns:
            Risultato dell'operazione
        """
        try:
            # Prepara parametri
            params = {
                "ticket": ticket
            }
            
            # Aggiungi volume solo se specificato
            if volume is not None:
                params["volume"] = volume
            
            # Invia comando
            result = self.send_command("close_position", params)
            
            return result
            
        except Exception as e:
            logger.error(f"Errore nella chiusura della posizione: {e}")
            return {"error": str(e)}
    
    def close_all_positions(self, symbol: Optional[str] = None, magic: Optional[int] = None) -> Dict[str, Any]:
        """
        Chiude tutte le posizioni.
        
        Args:
            symbol: Simbolo per filtrare le posizioni (opzionale)
            magic: Magic number per filtrare le posizioni (opzionale)
            
        Returns:
            Risultato dell'operazione
        """
        try:
            # Prepara parametri
            params = {}
            
            # Aggiungi filtri solo se specificati
            if symbol:
                params["symbol"] = symbol.upper()
            
            if magic is not None:
                params["magic"] = magic
            
            # Invia comando
            result = self.send_command("close_all_positions", params)
            
            return result
            
        except Exception as e:
            logger.error(f"Errore nella chiusura di tutte le posizioni: {e}")
            return {"error": str(e)}
    
    def modify_position(self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None) -> Dict[str, Any]:
        """
        Modifica una posizione.
        
        Args:
            ticket: Ticket della posizione
            sl: Nuovo Stop Loss (opzionale)
            tp: Nuovo Take Profit (opzionale)
            
        Returns:
            Risultato dell'operazione
        """
        try:
            # Prepara parametri
            params = {
                "ticket": ticket
            }
            
            # Aggiungi parametri opzionali solo se specificati
            if sl is not None:
                params["sl"] = sl
            
            if tp is not None:
                params["tp"] = tp
            
            # Invia comando
            result = self.send_command("modify_position", params)
            
            return result
            
        except Exception as e:
            logger.error(f"Errore nella modifica della posizione: {e}")
            return {"error": str(e)}
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Ottiene informazioni su un simbolo.
        
        Args:
            symbol: Simbolo
            
        Returns:
            Informazioni sul simbolo
        """
        try:
            # Prepara parametri
            params = {
                "symbol": symbol.upper()
            }
            
            # Invia comando
            result = self.send_command("symbol_info", params)
            
            return result
            
        except Exception as e:
            logger.error(f"Errore nell'ottenere informazioni sul simbolo: {e}")
            return {"error": str(e)}
    
    def get_symbol_info_tick(self, symbol: str) -> Dict[str, Any]:
        """
        Ottiene informazioni sul tick corrente di un simbolo.
        
        Args:
            symbol: Simbolo
            
        Returns:
            Informazioni sul tick
        """
        try:
            # Prepara parametri
            params = {
                "symbol": symbol.upper()
            }
            
            # Invia comando
            result = self.send_command("symbol_info_tick", params)
            
            return result
            
        except Exception as e:
            logger.error(f"Errore nell'ottenere informazioni sul tick: {e}")
            return {"error": str(e)}
    
    def get_market_data(self, symbol: str, timeframe: str, count: int = 100) -> List[Dict[str, Any]]:
        """
        Ottiene dati storici di mercato.
        
        Args:
            symbol: Simbolo
            timeframe: Timeframe (es. "M1", "H1", "D1")
            count: Numero di candele da ottenere
            
        Returns:
            Lista di candele
        """
        try:
            # Mappa timeframe
            timeframe_map = {
                "M1": "TIMEFRAME_M1",
                "M5": "TIMEFRAME_M5",
                "M15": "TIMEFRAME_M15",
                "M30": "TIMEFRAME_M30",
                "H1": "TIMEFRAME_H1",
                "H4": "TIMEFRAME_H4",
                "D1": "TIMEFRAME_D1",
                "W1": "TIMEFRAME_W1",
                "MN1": "TIMEFRAME_MN1"
            }
            
            # Verifica timeframe
            if timeframe not in timeframe_map:
                raise ValueError(f"Timeframe non valido: {timeframe}")
            
            # Prepara parametri
            params = {
                "symbol": symbol.upper(),
                "timeframe": timeframe_map[timeframe],
                "count": count
            }
            
            # Invia comando
            result = self.send_command("copy_rates_from", params)
            
            # Formatta i dati
            formatted_data = []
            for rate in result:
                # Converti timestamp in data leggibile
                time_str = datetime.datetime.fromtimestamp(rate[0]).isoformat()
                
                # Formatta candela
                candle = {
                    "time": time_str,
                    "open": rate[1],
                    "high": rate[2],
                    "low": rate[3],
                    "close": rate[4],
                    "tick_volume": rate[5],
                    "spread": rate[6],
                    "real_volume": rate[7]
                }
                formatted_data.append(candle)
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Errore nell'ottenere dati di mercato: {e}")
            return []
    
    def start_monitoring(self, account_interval: float = 5.0, positions_interval: float = 2.0) -> None:
        """
        Avvia il monitoraggio dell'account e delle posizioni.
        
        Args:
            account_interval: Intervallo di aggiornamento dell'account (secondi)
            positions_interval: Intervallo di aggiornamento delle posizioni (secondi)
        """
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Monitoraggio già attivo")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(account_interval, positions_interval),
            daemon=True
        )
        self.monitoring_thread.start()
        logger.info("Monitoraggio avviato")
    
    def stop_monitoring(self) -> None:
        """
        Ferma il monitoraggio dell'account e delle posizioni.
        """
        if not self.monitoring_thread or not self.monitoring_thread.is_alive():
            logger.warning("Monitoraggio non attivo")
            return
        
        self.monitoring_active = False
        self.monitoring_thread.join(timeout=2.0)
        logger.info("Monitoraggio fermato")
    
    def _monitoring_loop(self, account_interval: float, positions_interval: float) -> None:
        """
        Loop di monitoraggio dell'account e delle posizioni.
        
        Args:
            account_interval: Intervallo di aggiornamento dell'account (secondi)
            positions_interval: Intervallo di aggiornamento delle posizioni (secondi)
        """
        last_account_update = 0.0
        last_positions_update = 0.0
        connection_failures = 0
        max_failures = 3
        
        # Inizializza check_interval
        self.check_interval = 5.0  # Reset all'avvio
        
        while self.monitoring_active:
            try:
                current_time = time.time()
                
                # Verifica connessione
                if current_time - self.last_check_time.timestamp() >= self.check_interval:
                    try:
                        connected = self.check_connection()
                        self.last_check_time = datetime.datetime.now()
                        
                        # Gestione errori di connessione
                        if connected:
                            connection_failures = 0
                            # Reset check_interval dopo una connessione riuscita
                            if self.check_interval > 5.0:
                                self.check_interval = 5.0
                                logger.info("Connessione ripristinata, reset intervallo di verifica")
                        else:
                            connection_failures += 1
                            
                            # Se troppe connessioni fallite consecutive, aumenta intervallo di verifica
                            if connection_failures > max_failures:
                                logger.warning(f"Troppe connessioni fallite ({connection_failures}), aumento intervallo di verifica")
                                self.check_interval = min(30.0, self.check_interval * 1.5)  # Max 30 secondi
                            
                            # Attendi più a lungo in caso di errore
                            time.sleep(1.0)
                            continue
                    except Exception as e:
                        logger.error(f"Errore nella verifica della connessione: {e}")
                        connection_failures += 1
                        time.sleep(1.0)
                        continue
                
                # Se non connesso, attendi e riprova
                if not self.connected:
                    time.sleep(1.0)
                    continue
                
                # Aggiorna account
                if current_time - last_account_update >= account_interval:
                    try:
                        account_info = self.get_account_info()
                        if account_info and self.on_account_update:
                            self.on_account_update(account_info)
                        last_account_update = current_time
                    except Exception as e:
                        logger.error(f"Errore nell'aggiornamento dell'account: {e}")
                        # In caso di errore, verifica subito la connessione
                        self.last_check_time = datetime.datetime.now() - datetime.timedelta(seconds=self.check_interval)
                
                # Aggiorna posizioni
                if current_time - last_positions_update >= positions_interval:
                    try:
                        positions = self.get_positions()
                        if self.on_positions_update:
                            self.on_positions_update(positions)
                        last_positions_update = current_time
                    except Exception as e:
                        logger.error(f"Errore nell'aggiornamento delle posizioni: {e}")
                        # In caso di errore, verifica subito la connessione
                        self.last_check_time = datetime.datetime.now() - datetime.timedelta(seconds=self.check_interval)
                
                # Pausa per evitare utilizzo eccessivo CPU
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Errore nel loop di monitoraggio: {e}")
                time.sleep(1.0)  # Pausa in caso di errore
