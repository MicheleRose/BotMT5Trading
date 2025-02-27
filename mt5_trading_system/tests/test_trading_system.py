#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script di test per il sistema MT5 Trading Bot.

Questo script esegue una sequenza di operazioni di trading per testare
le funzionalità del sistema MT5 Trading Bot.
"""

import os
import sys
import json
import time
import subprocess
import argparse
from typing import Dict, Any, List, Optional

def run_command(script: str, *args: str) -> Dict[str, Any]:
    """
    Esegue uno script Python con gli argomenti specificati.
    
    Args:
        script: Nome dello script da eseguire
        args: Argomenti da passare allo script
        
    Returns:
        Risultato dell'esecuzione dello script in formato JSON
    """
    cmd = [sys.executable, script]
    cmd.extend(args)
    
    print(f"\n{'=' * 80}")
    print(f"Esecuzione: {' '.join(cmd)}")
    print(f"{'=' * 80}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"ERRORE (codice {result.returncode}):")
        print(result.stderr)
        return {"success": False, "error": result.stderr}
    
    try:
        json_result = json.loads(result.stdout)
        print("RISULTATO:")
        print(json.dumps(json_result, indent=2, ensure_ascii=False))
        return json_result
    except json.JSONDecodeError:
        print("RISULTATO (non JSON):")
        print(result.stdout)
        return {"success": False, "error": "Output non in formato JSON", "output": result.stdout}

def main():
    """
    Funzione principale.
    """
    parser = argparse.ArgumentParser(description="Test del sistema MT5 Trading Bot")
    parser.add_argument("-c", "--config", default="mt5_config.json", help="Percorso al file di configurazione JSON")
    parser.add_argument("-s", "--symbol", default="EURUSD", help="Simbolo da utilizzare per i test")
    parser.add_argument("-v", "--volume", type=float, default=0.01, help="Volume da utilizzare per i test")
    args = parser.parse_args()
    
    config_arg = f"-c {args.config}" if args.config else ""
    
    print("\n\n" + "=" * 40)
    print("TEST DEL SISTEMA MT5 TRADING BOT")
    print("=" * 40)
    
    # Step 1: Verifica che MT5 Keeper sia in esecuzione
    print("\n\n[STEP 1] Verifica che MT5 Keeper sia in esecuzione...")
    
    # Ottieni informazioni sull'account
    account_info = run_command("get_account_info.py", config_arg)
    
    if not account_info.get("success", False):
        print("\nERRORE: MT5 Keeper non sembra essere in esecuzione.")
        print("Avvialo con: python mt5_keeper.py -c mt5_config.json")
        return
    
    print(f"\nMT5 Keeper è in esecuzione e connesso all'account {account_info.get('account_info', {}).get('login', 'N/A')}")
    
    # Step 2: Ottieni posizioni aperte
    print("\n\n[STEP 2] Ottieni posizioni aperte...")
    positions = run_command("get_positions.py", config_arg)
    
    initial_positions_count = len(positions.get("positions", []))
    print(f"\nPosizioni aperte: {initial_positions_count}")
    
    # Step 3: Apri una posizione di acquisto
    print("\n\n[STEP 3] Apri una posizione di acquisto...")
    buy_result = run_command("market_buy.py", config_arg, args.symbol, str(args.volume))
    
    if not buy_result.get("success", False):
        print("\nERRORE: Impossibile aprire la posizione di acquisto.")
        return
    
    order_id = buy_result.get("order_id", 0)
    print(f"\nPosizione aperta con ID: {order_id}")
    
    # Attendi un momento per assicurarsi che la posizione sia registrata
    time.sleep(2)
    
    # Step 4: Ottieni posizioni aperte aggiornate
    print("\n\n[STEP 4] Ottieni posizioni aperte aggiornate...")
    positions = run_command("get_positions.py", config_arg)
    
    # Trova la posizione appena aperta
    current_position = None
    for position in positions.get("positions", []):
        if position.get("ticket") == order_id:
            current_position = position
            break
    
    if not current_position:
        print("\nERRORE: Impossibile trovare la posizione appena aperta.")
        return
    
    print(f"\nPosizione trovata: {current_position}")
    
    # Step 5: Modifica lo stop loss e il take profit
    print("\n\n[STEP 5] Modifica lo stop loss e il take profit...")
    
    # Calcola nuovi valori di SL e TP
    current_price = current_position.get("current_price", 0.0)
    
    if current_position.get("type") == "BUY":
        new_sl = current_price - 0.0050  # 50 pips sotto
        new_tp = current_price + 0.0100  # 100 pips sopra
    else:
        new_sl = current_price + 0.0050  # 50 pips sopra
        new_tp = current_price - 0.0100  # 100 pips sotto
    
    # Arrotonda a 5 decimali
    new_sl = round(new_sl, 5)
    new_tp = round(new_tp, 5)
    
    modify_result = run_command("modify_position.py", config_arg, str(order_id), f"--sl={new_sl}", f"--tp={new_tp}")
    
    if not modify_result.get("success", False):
        print("\nERRORE: Impossibile modificare la posizione.")
    else:
        print(f"\nPosizione modificata con SL={new_sl} e TP={new_tp}")
    
    # Step 6: Chiudi la posizione
    print("\n\n[STEP 6] Chiudi la posizione...")
    close_result = run_command("close_position.py", config_arg, str(order_id))
    
    if not close_result.get("success", False):
        print("\nERRORE: Impossibile chiudere la posizione.")
    else:
        print(f"\nPosizione chiusa con profitto: {close_result.get('profit', 0.0)}")
    
    # Step 7: Verifica che la posizione sia stata chiusa
    print("\n\n[STEP 7] Verifica che la posizione sia stata chiusa...")
    positions = run_command("get_positions.py", config_arg)
    
    final_positions_count = len(positions.get("positions", []))
    print(f"\nPosizioni aperte: {final_positions_count}")
    
    # Verifica che il numero di posizioni sia tornato al valore iniziale
    if final_positions_count == initial_positions_count:
        print("\nTest completato con successo!")
    else:
        print("\nERRORE: Il numero di posizioni aperte non corrisponde al valore iniziale.")
    
    print("\n\n" + "=" * 40)
    print("FINE DEL TEST")
    print("=" * 40)


if __name__ == "__main__":
    main()
