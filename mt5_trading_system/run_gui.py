#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script di avvio per MT5 Trading Bot GUI.

Questo script avvia MT5 Keeper e poi l'interfaccia grafica.
"""

import os
import sys
import time
import logging
import subprocess
import threading
import signal
import atexit

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Variabili globali
mt5_keeper_process = None

def start_mt5_keeper():
    """
    Avvia MT5 Keeper come processo separato.
    
    Returns:
        Processo MT5 Keeper
    """
    try:
        # Percorso al file di configurazione MT5
        config_path = os.path.abspath("config/mt5_config.json")
        
        # Comando per avviare MT5 Keeper
        cmd = [
            sys.executable,  # Python interpreter
            os.path.abspath("core/mt5_keeper.py"),
            "-c", config_path
        ]
        
        # Avvia processo con console separata su Windows
        # Questo permette di vedere l'output di MT5 Keeper
        if os.name == 'nt':
            process = subprocess.Popen(
                cmd,
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Su altri sistemi operativi
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
        
        logging.info(f"MT5 Keeper avviato (PID: {process.pid})")
        
        # Attendi un po' per dare tempo a MT5 Keeper di avviarsi
        time.sleep(3)  # Aumentato da 2 a 3 secondi
        
        # Verifica che MT5 Keeper sia in esecuzione
        if process.poll() is not None:
            # Il processo è terminato
            stdout, stderr = process.communicate()
            logging.error(f"MT5 Keeper terminato prematuramente: {stderr}")
            return None
        
        # Non verifichiamo più la connessione qui, sarà l'utente a connettersi manualmente
        # tramite il pulsante nell'interfaccia grafica
        logging.info("MT5 Keeper avviato, connessione manuale richiesta")
        
        return process
        
    except Exception as e:
        logging.error(f"Errore nell'avvio di MT5 Keeper: {e}")
        return None

def stop_mt5_keeper():
    """
    Ferma MT5 Keeper.
    """
    global mt5_keeper_process
    
    if mt5_keeper_process:
        try:
            # Invia segnale di terminazione
            if os.name == 'nt':
                # Windows
                mt5_keeper_process.terminate()
            else:
                # Unix
                os.kill(mt5_keeper_process.pid, signal.SIGTERM)
            
            # Attendi terminazione
            mt5_keeper_process.wait(timeout=5)
            
            logging.info("MT5 Keeper fermato")
            
        except Exception as e:
            logging.error(f"Errore nell'arresto di MT5 Keeper: {e}")
            
            # Forza terminazione
            try:
                mt5_keeper_process.kill()
            except:
                pass

def main():
    """
    Funzione principale.
    """
    global mt5_keeper_process
    
    try:
        # Avvia MT5 Keeper
        mt5_keeper_process = start_mt5_keeper()
        
        # Registra funzione di pulizia
        atexit.register(stop_mt5_keeper)
        
        # Importa modulo principale
        from gui.main import main as run_app
        
        # Esegui applicazione
        run_app()
        
    except ImportError as e:
        logging.error(f"Errore nell'importazione dei moduli: {e}")
        print(f"Errore nell'importazione dei moduli: {e}")
        print("Assicurati di aver installato tutte le dipendenze necessarie.")
        print("Esegui: pip install ttkbootstrap matplotlib numpy")
        sys.exit(1)
        
    except Exception as e:
        logging.error(f"Errore nell'avvio dell'applicazione: {e}")
        print(f"Errore nell'avvio dell'applicazione: {e}")
        sys.exit(1)
        
    finally:
        # Ferma MT5 Keeper
        stop_mt5_keeper()

if __name__ == "__main__":
    main()
