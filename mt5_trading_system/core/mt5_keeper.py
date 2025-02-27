#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5 Keeper - Processo singleton per gestione connessione persistente a MetaTrader 5.

Questo script mantiene una connessione persistente a MetaTrader 5 e gestisce
le richieste inviate tramite file nella directory commands/.
"""

import os
import sys
import json
import time
import signal
import logging
import platform
import datetime
import traceback
import threading
import MetaTrader5 as mt5
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple
import shutil
import uuid

# Importa moduli specifici per sistema operativo
if platform.system() == "Windows":
    import msvcrt  # Per Windows
else:
    import fcntl  # Per sistemi Unix-like

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MT5Keeper")

class MT5Keeper:
    """
    Classe principale per il MT5 Keeper.
    Gestisce una connessione persistente a MetaTrader 5 e processa i comandi ricevuti.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inizializza il MT5 Keeper.
        
        Args:
            config_path: Percorso al file di configurazione JSON (opzionale)
        """
        self.running = False
        self.connected = False
        self.lock_file = None
        self.lock_file_handle = None
        
        # Carica configurazione
        self.config = self._load_config(config_path)
        
        # Imposta directory di lavoro
        self.work_dir = self._get_work_dir()
        self.commands_dir = self.work_dir / "commands"
        self.results_dir = self.work_dir / "results"
        self.logs_dir = self.work_dir / "logs"
        
        # Crea directory se non esistono
        self._create_directories()
        
        # Configura file di log
        self._setup_file_logging()
        
        # Imposta file di lock
        self.lock_file = self.work_dir / "mt5keeper.lock"
        
        # Inizializza variabili per il controllo del ciclo principale
        self.last_heartbeat = datetime.datetime.now()
        self.last_reconnect_attempt = datetime.datetime.now()
        self.command_check_interval = self.config.get("command_check_interval", 1.0)  # secondi
        self.heartbeat_interval = self.config.get("heartbeat_interval", 30.0)  # secondi
        self.reconnect_interval = self.config.get("reconnect_interval", 60.0)  # secondi
        
        # Gestione segnali per chiusura pulita
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Carica la configurazione da file JSON.
        
        Args:
            config_path: Percorso al file di configurazione
            
        Returns:
            Dizionario con la configurazione
        """
        default_config = {
            "mt5_path": "",  # Percorso all'eseguibile di MT5 (vuoto = auto-detect)
            "account": 0,    # Numero account (0 = nessun login)
            "password": "",  # Password (vuoto = nessun login)
            "server": "",    # Server (vuoto = default)
            "timeout": 60000,  # Timeout per operazioni MT5 (ms)
            "command_check_interval": 1.0,  # Intervallo controllo comandi (s)
            "heartbeat_interval": 30.0,     # Intervallo heartbeat (s)
            "reconnect_interval": 60.0,     # Intervallo tentativi riconnessione (s)
            "debug": False,  # Modalità debug
        }
        
        config = default_config.copy()
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    config.update(user_config)
                    logger.info(f"Configurazione caricata da {config_path}")
            except Exception as e:
                logger.error(f"Errore nel caricamento della configurazione: {e}")
        
        # Salva configurazione nella directory di lavoro
        try:
            work_dir = self._get_work_dir()
            os.makedirs(work_dir, exist_ok=True)
            with open(work_dir / "config.json", 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logger.warning(f"Impossibile salvare la configurazione: {e}")
        
        return config
    
    def _get_work_dir(self) -> Path:
        """
        Determina la directory di lavoro cross-platform.
        
        Returns:
            Path alla directory di lavoro
        """
        home = Path.home()
        return home / ".mt5bot"
    
    def _create_directories(self) -> None:
        """
        Crea le directory necessarie se non esistono.
        """
        for directory in [self.work_dir, self.commands_dir, self.results_dir, self.logs_dir]:
            directory.mkdir(exist_ok=True, parents=True)
            logger.debug(f"Directory creata/verificata: {directory}")
    
    def _setup_file_logging(self) -> None:
        """
        Configura il logging su file.
        """
        log_file = self.logs_dir / f"mt5keeper_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        if self.config.get("debug", False):
            logger.setLevel(logging.DEBUG)
            logger.debug("Modalità debug attivata")
    
    def _acquire_lock(self) -> bool:
        """
        Acquisisce il lock file per garantire che ci sia una sola istanza in esecuzione.
        
        Returns:
            True se il lock è stato acquisito, False altrimenti
        """
        try:
            self.lock_file_handle = open(self.lock_file, 'w')
            
            # Implementazione cross-platform del file locking
            if platform.system() == "Windows":
                # Windows file locking
                msvcrt.locking(self.lock_file_handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                # Unix file locking
                fcntl.flock(self.lock_file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # Scrivi PID nel file di lock
            self.lock_file_handle.write(str(os.getpid()))
            self.lock_file_handle.flush()
            logger.info(f"Lock acquisito: {self.lock_file}")
            return True
            
        except (IOError, OSError) as e:
            if self.lock_file_handle:
                self.lock_file_handle.close()
                self.lock_file_handle = None
            logger.error(f"Impossibile acquisire il lock. Un'altra istanza potrebbe essere in esecuzione: {e}")
            return False
    
    def _release_lock(self) -> None:
        """
        Rilascia il lock file.
        """
        if self.lock_file_handle:
            try:
                if platform.system() == "Windows":
                    try:
                        # Windows file unlocking
                        msvcrt.locking(self.lock_file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                    except Exception as e:
                        logger.debug(f"Errore nello sblocco del file (ignorato): {e}")
                else:
                    try:
                        # Unix file unlocking
                        fcntl.flock(self.lock_file_handle.fileno(), fcntl.LOCK_UN)
                    except Exception as e:
                        logger.debug(f"Errore nello sblocco del file (ignorato): {e}")
                
                # Chiudi il file handle in ogni caso
                try:
                    self.lock_file_handle.close()
                except Exception as e:
                    logger.debug(f"Errore nella chiusura del file handle (ignorato): {e}")
                
                self.lock_file_handle = None
                logger.info(f"Lock rilasciato: {self.lock_file}")
            except Exception as e:
                logger.error(f"Errore nel rilascio del lock: {e}")
                # Assicurati che il file handle sia None anche in caso di errore
                self.lock_file_handle = None
    
    def _connect_mt5(self) -> bool:
        """
        Inizializza la connessione a MetaTrader 5.
        
        Returns:
            True se la connessione è stata stabilita, False altrimenti
        """
        try:
            # Chiudi eventuali connessioni precedenti
            try:
                if mt5.terminal_info() is not None:
                    mt5.shutdown()
            except:
                pass
            
            # Inizializza MT5 senza parametri (auto-rilevamento)
            logger.info("Inizializzazione MT5 con auto-rilevamento")
            init_result = mt5.initialize()
            
            if not init_result:
                logger.error(f"Inizializzazione MT5 fallita: {mt5.last_error()}")
                return False
            
            # Effettua login se specificato
            account = self.config.get("account", 0)
            if account > 0:
                login_result = mt5.login(
                    account,
                    self.config.get("password", ""),
                    self.config.get("server", "")
                )
                
                if not login_result:
                    logger.error(f"Login MT5 fallito: {mt5.last_error()}")
                    mt5.shutdown()
                    return False
                
                logger.info(f"Login effettuato con account: {account}")
            
            # Verifica connessione
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                logger.error("Impossibile ottenere informazioni sul terminale MT5")
                mt5.shutdown()
                return False
            
            logger.info(f"Connesso a MT5: {terminal_info.name} (build {terminal_info.build})")
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Errore durante la connessione a MT5: {e}")
            logger.debug(traceback.format_exc())
            self.connected = False
            return False
    
    def _disconnect_mt5(self) -> None:
        """
        Chiude la connessione a MetaTrader 5.
        """
        try:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnesso da MT5")
        except Exception as e:
            logger.error(f"Errore durante la disconnessione da MT5: {e}")
    
    def _heartbeat(self) -> bool:
        """
        Esegue un heartbeat per verificare che la connessione a MT5 sia ancora attiva.
        
        Returns:
            True se la connessione è attiva, False altrimenti
        """
        try:
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                logger.warning("Heartbeat fallito: connessione MT5 persa")
                self.connected = False
                return False
            
            # Aggiorna timestamp ultimo heartbeat
            self.last_heartbeat = datetime.datetime.now()
            logger.debug(f"Heartbeat OK: {terminal_info.name} (build {terminal_info.build})")
            return True
            
        except Exception as e:
            logger.error(f"Errore durante heartbeat: {e}")
            self.connected = False
            return False
    
    def _process_command_file(self, command_file: Path) -> None:
        """
        Processa un file di comando.
        
        Args:
            command_file: Path al file di comando
        """
        command_id = command_file.stem
        result_file = self.results_dir / f"{command_id}.json"
        
        logger.info(f"Elaborazione comando: {command_id}")
        
        try:
            # Leggi comando
            with open(command_file, 'r') as f:
                command_data = json.load(f)
            
            # Estrai informazioni comando
            command_type = command_data.get("command", "")
            params = command_data.get("params", {})
            
            # Esegui comando
            result = self._execute_command(command_type, params)
            
            # Prepara risposta
            response = {
                "command_id": command_id,
                "status": "success",
                "timestamp": datetime.datetime.now().isoformat(),
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Errore nell'elaborazione del comando {command_id}: {e}")
            logger.debug(traceback.format_exc())
            
            # Prepara risposta di errore
            response = {
                "command_id": command_id,
                "status": "error",
                "timestamp": datetime.datetime.now().isoformat(),
                "error": str(e),
                "traceback": traceback.format_exc() if self.config.get("debug", False) else None
            }
        
        # Scrivi risultato
        try:
            with open(result_file, 'w') as f:
                json.dump(response, f, indent=4, default=self._json_serializer)
            
            logger.info(f"Risultato scritto: {result_file}")
            
            # Rimuovi file comando
            os.remove(command_file)
            logger.debug(f"File comando rimosso: {command_file}")
            
        except Exception as e:
            logger.error(f"Errore nella scrittura del risultato per {command_id}: {e}")
    
    def _json_serializer(self, obj: Any) -> Any:
        """
        Serializzatore JSON personalizzato per gestire tipi non serializzabili.
        
        Args:
            obj: Oggetto da serializzare
            
        Returns:
            Versione serializzabile dell'oggetto
        """
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)
    
    def _execute_command(self, command_type: str, params: Dict[str, Any]) -> Any:
        """
        Esegue un comando MT5.
        
        Args:
            command_type: Tipo di comando
            params: Parametri del comando
            
        Returns:
            Risultato del comando
            
        Raises:
            ValueError: Se il comando non è supportato
        """
        if not self.connected:
            raise ValueError("MT5 non connesso")
        
        # Nota: La funzione set_timeout non è disponibile in questa versione di MetaTrader5
        # Utilizziamo il timeout predefinito
        
        # Esegui comando in base al tipo
        if command_type == "ping":
            return {"status": "pong", "timestamp": datetime.datetime.now().isoformat()}
        
        elif command_type == "terminal_info":
            terminal_info = mt5.terminal_info()
            return {k: getattr(terminal_info, k) for k in dir(terminal_info) if not k.startswith('_')}
        
        elif command_type == "account_info":
            account_info = mt5.account_info()
            return {k: getattr(account_info, k) for k in dir(account_info) if not k.startswith('_')}
        
        elif command_type == "symbols_get":
            symbols = params.get("symbols", [])
            if symbols:
                result = mt5.symbols_get(symbols)
            else:
                result = mt5.symbols_get()
            
            return [
                {k: getattr(symbol, k) for k in dir(symbol) if not k.startswith('_')}
                for symbol in result
            ] if result else []
        
        elif command_type == "symbol_info":
            symbol = params.get("symbol", "")
            if not symbol:
                raise ValueError("Parametro 'symbol' mancante")
            
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                raise ValueError(f"Simbolo non trovato: {symbol}")
            
            return {k: getattr(symbol_info, k) for k in dir(symbol_info) if not k.startswith('_')}
        
        elif command_type == "symbol_info_tick":
            symbol = params.get("symbol", "")
            if not symbol:
                raise ValueError("Parametro 'symbol' mancante")
            
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                raise ValueError(f"Impossibile ottenere tick per: {symbol}")
            
            return {k: getattr(tick, k) for k in dir(tick) if not k.startswith('_')}
        
        elif command_type == "copy_rates_from":
            symbol = params.get("symbol", "")
            timeframe = params.get("timeframe", "TIMEFRAME_M1")
            date_from = params.get("date_from", "")
            count = params.get("count", 100)
            
            if not symbol:
                raise ValueError("Parametro 'symbol' mancante")
            
            # Converti timeframe da stringa a costante MT5
            tf_value = getattr(mt5, timeframe, mt5.TIMEFRAME_M1)
            
            # Converti date_from da stringa a datetime
            if isinstance(date_from, str) and date_from:
                date_from = datetime.datetime.fromisoformat(date_from)
            elif not date_from:
                date_from = datetime.datetime.now() - datetime.timedelta(days=1)
            
            rates = mt5.copy_rates_from(symbol, tf_value, date_from, count)
            if rates is None:
                raise ValueError(f"Impossibile ottenere rates per: {symbol}")
            
            return rates.tolist() if hasattr(rates, 'tolist') else rates
        
        # Nuovi comandi per gli script di trading
        
        elif command_type == "market_buy":
            # Parametri obbligatori
            symbol = params.get("symbol", "")
            volume = params.get("volume", 0.0)
            
            if not symbol:
                raise ValueError("Parametro 'symbol' mancante")
            
            if volume <= 0:
                raise ValueError("Volume deve essere maggiore di zero")
            
            # Parametri opzionali
            sl = params.get("sl", 0.0)
            tp = params.get("tp", 0.0)
            magic = params.get("magic", 0)
            comment = params.get("comment", "")
            
            # Prepara richiesta
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(volume),
                "type": mt5.ORDER_TYPE_BUY,
                "price": mt5.symbol_info_tick(symbol).ask,
                "sl": sl,
                "tp": tp,
                "deviation": 10,
                "magic": magic,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Invia ordine
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                raise ValueError(f"Errore nell'invio dell'ordine: {result.retcode} - {result.comment}")
            
            return {
                "order_id": result.order,
                "price": result.price,
                "timestamp": datetime.datetime.now().isoformat(),
                "request": request,
                "result": {k: getattr(result, k) for k in dir(result) if not k.startswith('_')}
            }
        
        elif command_type == "market_sell":
            # Parametri obbligatori
            symbol = params.get("symbol", "")
            volume = params.get("volume", 0.0)
            
            if not symbol:
                raise ValueError("Parametro 'symbol' mancante")
            
            if volume <= 0:
                raise ValueError("Volume deve essere maggiore di zero")
            
            # Parametri opzionali
            sl = params.get("sl", 0.0)
            tp = params.get("tp", 0.0)
            magic = params.get("magic", 0)
            comment = params.get("comment", "")
            
            # Prepara richiesta
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": float(volume),
                "type": mt5.ORDER_TYPE_SELL,
                "price": mt5.symbol_info_tick(symbol).bid,
                "sl": sl,
                "tp": tp,
                "deviation": 10,
                "magic": magic,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Invia ordine
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                raise ValueError(f"Errore nell'invio dell'ordine: {result.retcode} - {result.comment}")
            
            return {
                "order_id": result.order,
                "price": result.price,
                "timestamp": datetime.datetime.now().isoformat(),
                "request": request,
                "result": {k: getattr(result, k) for k in dir(result) if not k.startswith('_')}
            }
        
        elif command_type == "modify_position":
            # Parametri obbligatori
            ticket = params.get("ticket", 0)
            
            if ticket <= 0:
                raise ValueError("Ticket non valido")
            
            # Ottieni posizione
            position = mt5.positions_get(ticket=ticket)
            if not position:
                raise ValueError(f"Posizione con ticket {ticket} non trovata")
            
            position = position[0]
            
            # Parametri opzionali
            sl = params.get("sl", None)
            tp = params.get("tp", None)
            
            # Se né sl né tp sono specificati, non fare nulla
            if sl is None and tp is None:
                return {
                    "modified": False,
                    "message": "Nessun parametro da modificare specificato"
                }
            
            # Usa i valori attuali se non specificati
            if sl is None:
                sl = position.sl
            
            if tp is None:
                tp = position.tp
            
            # Prepara richiesta
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": ticket,
                "sl": sl,
                "tp": tp
            }
            
            # Invia richiesta
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                raise ValueError(f"Errore nella modifica della posizione: {result.retcode} - {result.comment}")
            
            return {
                "modified": True,
                "message": "Posizione modificata con successo",
                "sl": sl,
                "tp": tp,
                "request": request,
                "result": {k: getattr(result, k) for k in dir(result) if not k.startswith('_')}
            }
        
        elif command_type == "close_position":
            # Parametri obbligatori
            ticket = params.get("ticket", 0)
            
            if ticket <= 0:
                raise ValueError("Ticket non valido")
            
            # Ottieni posizione
            position = mt5.positions_get(ticket=ticket)
            if not position:
                raise ValueError(f"Posizione con ticket {ticket} non trovata")
            
            position = position[0]
            
            # Parametri opzionali
            volume = params.get("volume", None)
            
            # Se volume non è specificato, chiudi tutta la posizione
            if volume is None:
                volume = position.volume
            else:
                # Assicurati che il volume non sia maggiore del volume della posizione
                volume = min(volume, position.volume)
            
            # Prepara richiesta
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": float(volume),
                "type": mt5.ORDER_TYPE_BUY if position.type == 1 else mt5.ORDER_TYPE_SELL,  # Tipo opposto
                "position": ticket,
                "price": mt5.symbol_info_tick(position.symbol).ask if position.type == 1 else mt5.symbol_info_tick(position.symbol).bid,
                "deviation": 10,
                "magic": position.magic,
                "comment": "close_position.py",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Invia richiesta
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                raise ValueError(f"Errore nella chiusura della posizione: {result.retcode} - {result.comment}")
            
            return {
                "closed": True,
                "price": result.price,
                "volume_closed": volume,
                "message": "Posizione chiusa con successo",
                "request": request,
                "result": {k: getattr(result, k) for k in dir(result) if not k.startswith('_')}
            }
        
        elif command_type == "close_all_positions":
            # Parametri opzionali
            symbol = params.get("symbol", None)
            magic = params.get("magic", None)
            
            # Ottieni tutte le posizioni
            if symbol and magic is not None:
                positions = mt5.positions_get(symbol=symbol, magic=magic)
            elif symbol:
                positions = mt5.positions_get(symbol=symbol)
            elif magic is not None:
                positions = mt5.positions_get(magic=magic)
            else:
                positions = mt5.positions_get()
            
            if not positions:
                return {
                    "positions_closed": 0,
                    "total_profit": 0.0,
                    "details": [],
                    "message": "Nessuna posizione trovata"
                }
            
            # Chiudi ogni posizione
            closed_positions = []
            total_profit = 0.0
            
            for position in positions:
                # Prepara richiesta
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": position.symbol,
                    "volume": float(position.volume),
                    "type": mt5.ORDER_TYPE_BUY if position.type == 1 else mt5.ORDER_TYPE_SELL,  # Tipo opposto
                    "position": position.ticket,
                    "price": mt5.symbol_info_tick(position.symbol).ask if position.type == 1 else mt5.symbol_info_tick(position.symbol).bid,
                    "deviation": 10,
                    "magic": position.magic,
                    "comment": "close_all_positions.py",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                # Invia richiesta
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    closed_positions.append({
                        "ticket": position.ticket,
                        "symbol": position.symbol,
                        "volume": position.volume,
                        "price": result.price
                    })
                    # Nota: result non ha l'attributo profit
                    # Utilizziamo il profitto della posizione
                    total_profit += position.profit
                else:
                    logger.warning(f"Errore nella chiusura della posizione {position.ticket}: {result.retcode} - {result.comment}")
            
            return {
                "positions_closed": len(closed_positions),
                "total_profit": total_profit,
                "details": closed_positions,
                "message": f"Chiuse {len(closed_positions)} posizioni con profitto totale {total_profit}"
            }
        
        elif command_type == "get_positions":
            # Parametri opzionali
            symbol = params.get("symbol", None)
            magic = params.get("magic", None)
            
            # Ottieni tutte le posizioni
            if symbol and magic is not None:
                positions = mt5.positions_get(symbol=symbol, magic=magic)
            elif symbol:
                positions = mt5.positions_get(symbol=symbol)
            elif magic is not None:
                positions = mt5.positions_get(magic=magic)
            else:
                positions = mt5.positions_get()
            
            if not positions:
                return {
                    "positions": [],
                    "timestamp": datetime.datetime.now().isoformat()
                }
            
            # Formatta le posizioni
            formatted_positions = []
            for position in positions:
                formatted_positions.append({
                    "ticket": position.ticket,
                    "time": position.time,
                    "type": "BUY" if position.type == 0 else "SELL",
                    "symbol": position.symbol,
                    "volume": position.volume,
                    "open_price": position.price_open,
                    "current_price": position.price_current,
                    "sl": position.sl,
                    "tp": position.tp,
                    "profit": position.profit,
                    "swap": position.swap,
                    "magic": position.magic,
                    "comment": position.comment
                })
            
            return {
                "positions": formatted_positions,
                "timestamp": datetime.datetime.now().isoformat()
            }
        
        else:
            raise ValueError(f"Comando non supportato: {command_type}")
    
    def _check_commands(self) -> None:
        """
        Controlla e processa i file di comando nella directory commands/.
        """
        try:
            command_files = list(self.commands_dir.glob("*.json"))
            if command_files:
                logger.debug(f"Trovati {len(command_files)} file di comando")
                
                for command_file in command_files:
                    self._process_command_file(command_file)
                    
        except Exception as e:
            logger.error(f"Errore nel controllo dei comandi: {e}")
    
    def _signal_handler(self, sig, frame) -> None:
        """
        Gestisce i segnali di terminazione.
        
        Args:
            sig: Segnale ricevuto
            frame: Frame corrente
        """
        logger.info(f"Ricevuto segnale {sig}, arresto in corso...")
        self.stop()
    
    def start(self) -> None:
        """
        Avvia il MT5 Keeper.
        """
        # Verifica che non ci siano altre istanze in esecuzione
        if not self._acquire_lock():
            logger.error("Impossibile avviare MT5 Keeper: un'altra istanza è già in esecuzione")
            return
        
        logger.info("Avvio MT5 Keeper...")
        
        # Connetti a MT5
        if not self._connect_mt5():
            logger.error("Impossibile connettersi a MT5, arresto in corso...")
            self._release_lock()
            return
        
        self.running = True
        
        try:
            logger.info("MT5 Keeper avviato e in attesa di comandi")
            
            # Ciclo principale
            while self.running:
                # Verifica connessione e riconnetti se necessario
                if not self.connected:
                    current_time = datetime.datetime.now()
                    if (current_time - self.last_reconnect_attempt).total_seconds() >= self.reconnect_interval:
                        logger.info("Tentativo di riconnessione a MT5...")
                        self._connect_mt5()
                        self.last_reconnect_attempt = current_time
                
                # Se connesso, processa comandi e fai heartbeat
                if self.connected:
                    # Controlla comandi
                    self._check_commands()
                    
                    # Heartbeat periodico
                    current_time = datetime.datetime.now()
                    if (current_time - self.last_heartbeat).total_seconds() >= self.heartbeat_interval:
                        self._heartbeat()
                
                # Pausa per evitare utilizzo eccessivo CPU
                time.sleep(self.command_check_interval)
                
        except Exception as e:
            logger.error(f"Errore nel ciclo principale: {e}")
            logger.debug(traceback.format_exc())
        
        finally:
            self.stop()
    
    def stop(self) -> None:
        """
        Arresta il MT5 Keeper.
        """
        if not self.running:
            return
        
        logger.info("Arresto MT5 Keeper...")
        self.running = False
        
        # Disconnetti da MT5
        if self.connected:
            self._disconnect_mt5()
        
        # Rilascia lock
        self._release_lock()
        
        logger.info("MT5 Keeper arrestato")


def main():
    """
    Funzione principale.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="MT5 Keeper - Processo singleton per gestione connessione persistente a MetaTrader 5")
    parser.add_argument("-c", "--config", help="Percorso al file di configurazione JSON")
    args = parser.parse_args()
    
    keeper = MT5Keeper(args.config)
    keeper.start()


if __name__ == "__main__":
    main()
