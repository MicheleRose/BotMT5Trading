#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per avviare MT5 Keeper in background e poi eseguire il test.

Questo script avvia MT5 Keeper in un processo separato, attende che sia
pronto, e poi esegue lo script di test.
"""

import os
import sys
import time
import signal
import subprocess
import argparse
import platform
import json
import uuid
import datetime
from pathlib import Path

def is_keeper_running() -> bool:
    """
    Verifica se MT5 Keeper è in esecuzione.
    
    Returns:
        True se MT5 Keeper è in esecuzione, False altrimenti
    """
    # Metodo 1: Verifica se ci sono processi Python in esecuzione con "mt5_keeper.py" nel nome
    if platform.system() == "Windows":
        try:
            # Su Windows, usa tasklist e findstr
            output = subprocess.check_output("tasklist /FI \"IMAGENAME eq python.exe\" /FO CSV", shell=True).decode()
            for line in output.splitlines():
                if "python.exe" in line and "mt5_keeper" in line:
                    print("Processo MT5 Keeper trovato tramite tasklist")
                    return True
        except Exception as e:
            print(f"Errore nella verifica dei processi: {e}")
    else:
        try:
            # Su Unix-like, usa ps e grep
            output = subprocess.check_output("ps aux | grep python | grep mt5_keeper", shell=True).decode()
            if "mt5_keeper.py" in output:
                print("Processo MT5 Keeper trovato tramite ps")
                return True
        except Exception as e:
            print(f"Errore nella verifica dei processi: {e}")
    
    # Metodo 2: Verifica se il file di lock esiste
    lock_file = Path.home() / ".mt5bot" / "mt5keeper.lock"
    if lock_file.exists():
        print(f"File di lock trovato: {lock_file}")
        # Non proviamo a leggere il file per evitare errori di permesso
        # Assumiamo che se il file esiste, MT5 Keeper potrebbe essere in esecuzione
    else:
        print("File di lock non trovato")
    
    # Metodo 3: Verifica se la directory commands esiste e possiamo scriverci
    commands_dir = Path.home() / ".mt5bot" / "commands"
    if commands_dir.exists() and os.access(commands_dir, os.W_OK):
        print(f"Directory commands trovata e accessibile: {commands_dir}")
        
        # Crea un file di comando di test
        test_command_id = f"test_{uuid.uuid4()}"
        test_command_file = commands_dir / f"{test_command_id}.json"
        
        try:
            # Scrivi un comando di test (ping)
            with open(test_command_file, 'w') as f:
                json.dump({
                    "command": "ping",
                    "params": {},
                    "timestamp": datetime.datetime.now().isoformat()
                }, f)
            
            print(f"File di comando di test creato: {test_command_file}")
            
            # Attendi che MT5 Keeper processi il comando
            results_dir = Path.home() / ".mt5bot" / "results"
            result_file = results_dir / f"{test_command_id}.json"
            
            # Attendi fino a 5 secondi per il risultato
            for _ in range(10):
                if result_file.exists():
                    print(f"File di risultato trovato: {result_file}")
                    try:
                        with open(result_file, 'r') as f:
                            result_data = json.load(f)
                        
                        if result_data.get("status") == "success":
                            print("MT5 Keeper ha risposto con successo al comando di test")
                            return True
                    except Exception as e:
                        print(f"Errore nella lettura del file di risultato: {e}")
                    
                    break
                
                time.sleep(0.5)
            
            print("Nessun risultato ricevuto dal comando di test")
        except Exception as e:
            print(f"Errore nella creazione del file di comando di test: {e}")
        finally:
            # Rimuovi il file di comando se esiste ancora
            if test_command_file.exists():
                try:
                    os.remove(test_command_file)
                except:
                    pass
    else:
        print(f"Directory commands non trovata o non accessibile: {commands_dir}")
    
    # Metodo 4: Prova a eseguire get_account_info.py
    try:
        print("Tentativo di esecuzione di get_account_info.py...")
        result = subprocess.run(
            [sys.executable, "get_account_info.py", "-c", "mt5_config.json"],
            capture_output=True,
            text=True
        )
        
        print(f"Codice di ritorno: {result.returncode}")
        if result.returncode == 0:
            try:
                json_result = json.loads(result.stdout)
                success = json_result.get("success", False)
                print(f"get_account_info.py ha restituito success={success}")
                return success
            except json.JSONDecodeError:
                print("Errore nella decodifica JSON dell'output di get_account_info.py")
                print(f"Output: {result.stdout}")
        else:
            print(f"Errore nell'esecuzione di get_account_info.py: {result.stderr}")
    except Exception as e:
        print(f"Eccezione durante l'esecuzione di get_account_info.py: {e}")
    
    return False

def is_process_running(pid: int) -> bool:
    """
    Verifica se un processo con il PID specificato è in esecuzione.
    
    Args:
        pid: Process ID da verificare
        
    Returns:
        True se il processo è in esecuzione, False altrimenti
    """
    if platform.system() == "Windows":
        # Su Windows, usa tasklist
        try:
            output = subprocess.check_output(f"tasklist /FI \"PID eq {pid}\"", shell=True).decode()
            return str(pid) in output
        except subprocess.CalledProcessError:
            return False
    else:
        # Su Unix-like, usa kill -0
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

def main():
    """
    Funzione principale.
    """
    parser = argparse.ArgumentParser(description="Avvia MT5 Keeper e esegui il test")
    parser.add_argument("-c", "--config", default="mt5_config.json", help="Percorso al file di configurazione JSON")
    parser.add_argument("-s", "--symbol", default="EURUSD", help="Simbolo da utilizzare per i test")
    parser.add_argument("-v", "--volume", type=float, default=0.01, help="Volume da utilizzare per i test")
    parser.add_argument("-f", "--force", action="store_true", help="Forza l'esecuzione del test anche se MT5 Keeper non è pronto")
    parser.add_argument("-t", "--timeout", type=int, default=10, help="Timeout in secondi per l'attesa di MT5 Keeper")
    args = parser.parse_args()
    
    print("\n\n" + "=" * 60)
    print("AVVIO MT5 KEEPER E ESECUZIONE TEST")
    print("=" * 60)
    
    # Variabile per tenere traccia se MT5 Keeper è stato avviato da noi
    keeper_started_by_us = False
    keeper_process = None
    
    # Verifica se MT5 Keeper è già in esecuzione
    if is_keeper_running():
        print("\nMT5 Keeper è già in esecuzione.")
    else:
        print("\nAvvio MT5 Keeper in background...")
        
        # Avvia MT5 Keeper in un processo separato
        if platform.system() == "Windows":
            # Su Windows, usa subprocess.Popen con creationflags=subprocess.CREATE_NEW_CONSOLE
            keeper_process = subprocess.Popen(
                [sys.executable, "mt5_keeper.py", "-c", args.config],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            # Su Unix-like, usa subprocess.Popen con stdout e stderr redirectati
            keeper_process = subprocess.Popen(
                [sys.executable, "mt5_keeper.py", "-c", args.config],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        print(f"MT5 Keeper avviato (PID: {keeper_process.pid})")
        keeper_started_by_us = True
        
        # Attendi che MT5 Keeper sia pronto
        print("\nAttesa che MT5 Keeper sia pronto...")
        max_attempts = args.timeout
        keeper_ready = False
        
        for attempt in range(max_attempts):
            if is_keeper_running():
                print(f"MT5 Keeper è pronto dopo {attempt + 1} tentativi.")
                keeper_ready = True
                break
            
            if attempt < max_attempts - 1:
                print(f"Tentativo {attempt + 1}/{max_attempts}... attendere...")
                time.sleep(1)
        
        if not keeper_ready:
            print("\nATTENZIONE: MT5 Keeper potrebbe non essere pronto.")
            if not args.force:
                print("Usa l'opzione --force per eseguire il test comunque.")
                print("Verifica che MT5 sia installato e configurato correttamente.")
                return
            else:
                print("Esecuzione forzata del test...")
    
    # Esegui il test
    print("\n\nEsecuzione del test...")
    test_cmd = [
        sys.executable, "test_trading_system.py",
        "-c", args.config,
        "-s", args.symbol,
        "-v", str(args.volume)
    ]
    
    subprocess.run(test_cmd)
    
    print("\n\n" + "=" * 60)
    print("TEST COMPLETATO")
    print("=" * 60)
    
    # Chiedi all'utente se vuole terminare MT5 Keeper solo se l'abbiamo avviato noi
    if keeper_started_by_us and keeper_process is not None:
        try:
            choice = input("\nVuoi terminare MT5 Keeper? (s/n): ").strip().lower()
            if choice in ["s", "si", "sì", "y", "yes"]:
                print("\nTerminazione di MT5 Keeper...")
                
                # Su Windows, non possiamo terminare direttamente il processo
                # perché è stato avviato in una nuova console
                if platform.system() == "Windows":
                    print("Su Windows, devi chiudere manualmente la finestra di MT5 Keeper.")
                else:
                    # Su Unix-like, possiamo terminare il processo
                    try:
                        os.kill(keeper_process.pid, signal.SIGTERM)
                        print(f"MT5 Keeper (PID: {keeper_process.pid}) terminato.")
                    except Exception as e:
                        print(f"Errore nella terminazione di MT5 Keeper: {e}")
        except KeyboardInterrupt:
            print("\nOperazione annullata.")


if __name__ == "__main__":
    main()
