#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per generare previsioni sulla direzione dei prezzi utilizzando un modello LSTM.

Questo script carica un modello LSTM esistente, ottiene dati correnti da MT5,
calcola indicatori tecnici e genera una previsione sulla direzione dei prezzi.
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional

# Importa le classi di utilità
from mt5_trading_system.ml.utils import DataProcessor, ModelManager

def parse_args() -> argparse.Namespace:
    """
    Analizza gli argomenti della linea di comando.
    
    Returns:
        Namespace con gli argomenti
    """
    parser = argparse.ArgumentParser(
        description="Genera previsioni sulla direzione dei prezzi utilizzando un modello LSTM",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("symbol", help="Simbolo da analizzare (es. EURUSD)")
    parser.add_argument("model_path", help="Percorso al modello salvato")
    parser.add_argument("-c", "--config", help="Percorso al file di configurazione JSON")
    parser.add_argument("-s", "--scalers-path", help="Percorso agli scalers salvati")
    parser.add_argument("-n", "--num-candles", type=int, default=100, help="Numero di candele da ottenere")
    parser.add_argument("-t", "--timeframe", default="H1", help="Timeframe (es. H1)")
    parser.add_argument("-o", "--output", help="Percorso dove salvare la previsione (opzionale)")
    parser.add_argument("-d", "--debug", action="store_true", help="Attiva modalità debug")
    
    return parser.parse_args()

def predict_direction(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Genera una previsione sulla direzione dei prezzi.
    
    Args:
        args: Argomenti della linea di comando
        
    Returns:
        Dizionario con la previsione
    """
    # Crea processore di dati
    data_processor = DataProcessor(args.config)
    
    # Carica scalers se specificati
    if args.scalers_path and os.path.exists(args.scalers_path):
        print(f"Carico scalers da {args.scalers_path}...")
        data_processor.load_scalers(args.scalers_path)
    
    # Ottieni dati correnti
    print(f"Ottengo dati correnti per {args.symbol} su timeframe {args.timeframe}...")
    df = data_processor.get_market_data(args.symbol, args.timeframe, args.num_candles)
    print(f"Ottenute {len(df)} candele.")
    
    # Aggiungi indicatori tecnici
    print("Calcolo indicatori tecnici...")
    df_with_indicators = data_processor.add_technical_indicators(df)
    print(f"Calcolati indicatori tecnici. Righe rimanenti: {len(df_with_indicators)}")
    
    # Prepara dati per la previsione
    print("Preparo i dati per la previsione...")
    X = data_processor.prepare_data_for_prediction(df_with_indicators)
    print(f"Dati preparati. X shape: {X.shape}")
    
    # Crea gestore del modello
    model_manager = ModelManager()
    
    # Carica modello
    print(f"Carico il modello da {args.model_path}...")
    model_manager.load_model(args.model_path)
    
    # Genera previsione
    print("Genero previsione...")
    prediction = model_manager.predict(X)
    
    # Aggiungi informazioni aggiuntive
    prediction["symbol"] = args.symbol
    prediction["timeframe"] = args.timeframe
    prediction["timestamp"] = datetime.now().isoformat()
    prediction["last_price"] = float(df_with_indicators["close"].iloc[-1])
    
    # Aggiungi valori degli indicatori tecnici
    indicators = {}
    for indicator in ["rsi", "macd", "adx", "atr"]:
        if indicator in df_with_indicators.columns:
            indicators[indicator] = float(df_with_indicators[indicator].iloc[-1])
    
    prediction["indicators"] = indicators
    
    # Salva previsione se richiesto
    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w') as f:
            json.dump(prediction, f, indent=2)
    
    return prediction

def main() -> None:
    """
    Funzione principale.
    """
    # Parsing argomenti
    args = parse_args()
    
    # Imposta debug se richiesto
    if args.debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
        logging.debug("Modalità debug attivata")
    
    try:
        # Genera previsione
        prediction = predict_direction(args)
        
        # Stampa previsione
        print(json.dumps(prediction, indent=2))
        
    except Exception as e:
        # Gestione errori
        print(json.dumps({
            "success": False,
            "error": str(e)
        }, indent=2))
        
        if args.debug:
            import traceback
            traceback.print_exc()
        
        sys.exit(1)

if __name__ == "__main__":
    main()
