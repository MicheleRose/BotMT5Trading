#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script di test per verificare l'installazione di MetaTrader 5.
"""

import sys
import platform

print(f"Python version: {sys.version}")
print(f"Platform: {platform.system()} {platform.release()}")

try:
    import MetaTrader5 as mt5
    print(f"MetaTrader5 package version: {mt5.__version__}")
    
    print("\nTentativo di inizializzazione MT5...")
    init_result = mt5.initialize()
    
    if init_result:
        print("Inizializzazione riuscita!")
        
        # Ottieni informazioni sul terminale
        terminal_info = mt5.terminal_info()
        if terminal_info is not None:
            print(f"Terminale: {terminal_info.name} (build {terminal_info.build})")
            print(f"Path: {terminal_info.path}")
            print(f"Connected: {terminal_info.connected}")
            
        # Chiudi la connessione
        mt5.shutdown()
        print("Connessione chiusa correttamente")
    else:
        print(f"Inizializzazione fallita: {mt5.last_error()}")
        
except ImportError:
    print("MetaTrader5 package non installato. Installalo con 'pip install MetaTrader5'")
except Exception as e:
    print(f"Errore: {e}")
