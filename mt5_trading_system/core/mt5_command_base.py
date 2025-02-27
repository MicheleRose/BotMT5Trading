#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5 Command Base - Classe base per tutti gli script client che comunicano con MT5 Keeper.

Questa classe fornisce le funzionalità di base per inviare comandi al MT5 Keeper
e ricevere i risultati.
"""

import os
import sys
import json
import time
import uuid
import logging
import argparse
import datetime
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MT5Command")

class MT5CommandBase:
    """
    Classe base per tutti i comandi MT5.
    Fornisce funzionalità per comunicare con MT5 Keeper tramite file.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inizializza la classe base per i comandi MT5.
        
        Args:
            config_path: Percorso al file di configurazione JSON (opzionale)
        """
        # Carica configurazione
        self.config = self._load_config(config_path)
        
        # Imposta directory di lavoro
        self.work_dir = self._get_work_dir()
        self.commands_dir = self.work_dir / "commands"
        self.results_dir = self.work_dir / "results"
        
        # Imposta timeout
        self.timeout = self.config.get("timeout", 10.0)  # secondi (ridotto da 60.0 a 10.0)
        self.poll_interval = self.config.get("poll_interval", 0.5)  # secondi
        
        # Configura logging
        if self.config.get("debug", False):
            logger.setLevel(logging.DEBUG)
            logger.debug("Modalità debug attivata")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Carica la configurazione da file JSON.
        
        Args:
            config_path: Percorso al file di configurazione
            
        Returns:
            Dizionario con la configurazione
        """
        default_config = {
            "timeout": 60.0,       # Timeout per attesa risultati (s)
            "poll_interval": 0.5,  # Intervallo polling risultati (s)
            "debug": False,        # Modalità debug
        }
        
        config = default_config.copy()
        
        # Prima cerca nella directory di lavoro
        work_dir_config = self._get_work_dir() / "config.json"
        if work_dir_config.exists():
            try:
                with open(work_dir_config, 'r') as f:
                    work_config = json.load(f)
                    config.update(work_config)
                    logger.debug(f"Configurazione caricata da {work_dir_config}")
            except Exception as e:
                logger.warning(f"Errore nel caricamento della configurazione da {work_dir_config}: {e}")
        
        # Poi carica configurazione specifica se fornita
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                    config.update(user_config)
                    logger.debug(f"Configurazione caricata da {config_path}")
            except Exception as e:
                logger.error(f"Errore nel caricamento della configurazione da {config_path}: {e}")
        
        return config
    
    def _get_work_dir(self) -> Path:
        """
        Determina la directory di lavoro cross-platform.
        
        Returns:
            Path alla directory di lavoro
        """
        home = Path.home()
        return home / ".mt5bot"
    
    def _check_keeper_running(self) -> bool:
        """
        Verifica se MT5 Keeper è in esecuzione.
        
        Returns:
            True se MT5 Keeper è in esecuzione, False altrimenti
        """
        # Metodo 1: Verifica se il file di lock esiste
        lock_file = self.work_dir / "mt5keeper.lock"
        if not lock_file.exists():
            logger.error("MT5 Keeper non in esecuzione: file di lock non trovato")
            return False
        
        # Metodo 2: Verifica se la directory commands esiste e possiamo scriverci
        if not self.commands_dir.exists():
            logger.error("MT5 Keeper non in esecuzione: directory commands non trovata")
            return False
        
        if not os.access(self.commands_dir, os.W_OK):
            logger.error("MT5 Keeper non in esecuzione: directory commands non accessibile in scrittura")
            return False
        
        # Metodo 3: Verifica se la directory results esiste
        if not self.results_dir.exists():
            logger.error("MT5 Keeper non in esecuzione: directory results non trovata")
            return False
        
        # Se tutte le verifiche sono passate, assumiamo che MT5 Keeper sia in esecuzione
        logger.debug("MT5 Keeper sembra essere in esecuzione")
        return True
    
    def _create_directories(self) -> None:
        """
        Crea le directory necessarie se non esistono.
        """
        for directory in [self.work_dir, self.commands_dir, self.results_dir]:
            directory.mkdir(exist_ok=True, parents=True)
            logger.debug(f"Directory creata/verificata: {directory}")
    
    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Invia un comando al MT5 Keeper e attende il risultato.
        
        Args:
            command_type: Tipo di comando da inviare
            params: Parametri del comando (opzionale)
            
        Returns:
            Risultato del comando
            
        Raises:
            TimeoutError: Se il timeout viene raggiunto
            RuntimeError: Se si verifica un errore durante l'esecuzione del comando
        """
        if params is None:
            params = {}
        
        # Verifica che MT5 Keeper sia in esecuzione
        if not self._check_keeper_running():
            raise RuntimeError("MT5 Keeper non in esecuzione")
        
        # Crea directory se non esistono
        self._create_directories()
        
        # Genera ID comando univoco
        command_id = str(uuid.uuid4())
        command_file = self.commands_dir / f"{command_id}.json"
        result_file = self.results_dir / f"{command_id}.json"
        
        # Prepara comando
        command_data = {
            "command": command_type,
            "params": params,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Scrivi file comando
        try:
            with open(command_file, 'w') as f:
                json.dump(command_data, f, indent=4)
            
            logger.debug(f"Comando inviato: {command_id} ({command_type})")
            
        except Exception as e:
            raise RuntimeError(f"Errore nell'invio del comando: {e}")
        
        # Attendi risultato
        start_time = time.time()
        while not result_file.exists():
            # Verifica timeout
            if time.time() - start_time > self.timeout:
                # Rimuovi file comando se esiste ancora
                if command_file.exists():
                    try:
                        os.remove(command_file)
                    except:
                        pass
                
                raise TimeoutError(f"Timeout raggiunto ({self.timeout}s) per comando {command_id}")
            
            # Verifica che MT5 Keeper sia ancora in esecuzione
            if not self._check_keeper_running():
                # Rimuovi file comando se esiste ancora
                if command_file.exists():
                    try:
                        os.remove(command_file)
                    except:
                        pass
                
                raise RuntimeError("MT5 Keeper non più in esecuzione durante l'attesa del risultato")
            
            # Attendi
            time.sleep(self.poll_interval)
        
        # Leggi risultato
        try:
            with open(result_file, 'r') as f:
                result_data = json.load(f)
            
            logger.debug(f"Risultato ricevuto: {command_id}")
            
            # Rimuovi file risultato
            try:
                os.remove(result_file)
            except:
                pass
            
            # Verifica stato
            if result_data.get("status") == "error":
                error_msg = result_data.get("error", "Errore sconosciuto")
                traceback_info = result_data.get("traceback")
                
                if traceback_info and self.config.get("debug", False):
                    logger.debug(f"Traceback: {traceback_info}")
                
                raise RuntimeError(f"Errore nell'esecuzione del comando: {error_msg}")
            
            return result_data.get("result", {})
            
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Errore nella decodifica del risultato: {e}")
        
        except Exception as e:
            if not isinstance(e, RuntimeError):
                raise RuntimeError(f"Errore nella lettura del risultato: {e}")
            raise
    
    @staticmethod
    def parse_args() -> argparse.Namespace:
        """
        Analizza gli argomenti della linea di comando.
        
        Returns:
            Namespace con gli argomenti
        """
        parser = argparse.ArgumentParser(description="MT5 Command - Client per MT5 Keeper")
        parser.add_argument("-c", "--config", help="Percorso al file di configurazione JSON")
        parser.add_argument("-d", "--debug", action="store_true", help="Attiva modalità debug")
        
        # Aggiungi qui altri argomenti specifici per il comando
        
        return parser.parse_args()
    
    @classmethod
    def run(cls) -> None:
        """
        Metodo principale da sovrascrivere nelle classi derivate.
        """
        raise NotImplementedError("Il metodo run() deve essere implementato nelle classi derivate")


class MT5CommandExample(MT5CommandBase):
    """
    Esempio di classe derivata da MT5CommandBase.
    """
    
    @classmethod
    def run(cls) -> None:
        """
        Implementazione del metodo run() per l'esempio.
        """
        # Parsing argomenti
        args = cls.parse_args()
        
        # Creazione istanza
        cmd = cls(args.config)
        
        # Imposta debug se richiesto
        if args.debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("Modalità debug attivata")
        
        try:
            # Esempio: invia comando ping
            result = cmd.send_command("ping")
            print(f"Risultato ping: {result}")
            
            # Esempio: ottieni informazioni terminale
            result = cmd.send_command("terminal_info")
            print(f"Informazioni terminale: {json.dumps(result, indent=2)}")
            
        except Exception as e:
            logger.error(f"Errore: {e}")
            sys.exit(1)


if __name__ == "__main__":
    # Questo è solo un esempio, non verrà eseguito quando il modulo viene importato
    MT5CommandExample.run()
