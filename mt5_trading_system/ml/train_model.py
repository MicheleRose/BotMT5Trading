#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script per addestrare un modello LSTM per la previsione della direzione dei prezzi.

Questo script ottiene dati storici da MT5, calcola indicatori tecnici,
prepara i dati per l'addestramento e addestra un modello LSTM.
"""

import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from sklearn.model_selection import train_test_split

# Importa le classi di utilità
from mt5_trading_system.ml.utils import DataProcessor, ModelManager

def parse_args() -> argparse.Namespace:
    """
    Analizza gli argomenti della linea di comando.
    
    Returns:
        Namespace con gli argomenti
    """
    parser = argparse.ArgumentParser(
        description="Addestra un modello LSTM per la previsione della direzione dei prezzi",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("symbol", help="Simbolo da analizzare (es. EURUSD)")
    parser.add_argument("timeframe", help="Timeframe (es. H1)")
    parser.add_argument("training_period", type=int, help="Numero di candele per l'addestramento")
    parser.add_argument("output_path", help="Percorso dove salvare il modello e le metriche")
    parser.add_argument("-c", "--config", help="Percorso al file di configurazione JSON")
    parser.add_argument("-e", "--epochs", type=int, default=10, help="Numero di epoche per l'addestramento")
    parser.add_argument("-b", "--batch-size", type=int, default=32, help="Dimensione del batch per l'addestramento")
    parser.add_argument("-v", "--validation-split", type=float, default=0.2, help="Frazione dei dati da usare per la validazione")
    parser.add_argument("-t", "--test-split", type=float, default=0.1, help="Frazione dei dati da usare per il test")
    parser.add_argument("-s", "--seed", type=int, default=42, help="Seed per la riproducibilità")
    parser.add_argument("-d", "--debug", action="store_true", help="Attiva modalità debug")
    
    return parser.parse_args()

def setup_output_paths(output_path: str, symbol: str, timeframe: str) -> Dict[str, str]:
    """
    Configura i percorsi di output per il modello e le metriche.
    
    Args:
        output_path: Percorso base per l'output
        symbol: Simbolo
        timeframe: Timeframe
        
    Returns:
        Dizionario con i percorsi di output
    """
    # Crea timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Crea nome base per i file
    base_name = f"{symbol}_{timeframe}_{timestamp}"
    
    # Crea percorsi
    model_dir = os.path.join(output_path, "models")
    os.makedirs(model_dir, exist_ok=True)
    
    metrics_dir = os.path.join(output_path, "metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    
    scalers_dir = os.path.join(output_path, "scalers")
    os.makedirs(scalers_dir, exist_ok=True)
    
    # Crea dizionario con percorsi
    paths = {
        "model": os.path.join(model_dir, f"{base_name}_model"),
        "history": os.path.join(metrics_dir, f"{base_name}_history.json"),
        "metrics": os.path.join(metrics_dir, f"{base_name}_metrics.json"),
        "scalers": os.path.join(scalers_dir, f"{base_name}_scalers.pkl"),
        "summary": os.path.join(output_path, f"{base_name}_summary.json")
    }
    
    return paths

def train_model(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Addestra un modello LSTM per la previsione della direzione dei prezzi.
    
    Args:
        args: Argomenti della linea di comando
        
    Returns:
        Dizionario con i risultati dell'addestramento
    """
    # Imposta seed per riproducibilità
    np.random.seed(args.seed)
    
    # Crea processore di dati
    data_processor = DataProcessor(args.config)
    
    # Ottieni dati storici
    print(f"Ottengo dati storici per {args.symbol} su timeframe {args.timeframe}...")
    df = data_processor.get_market_data(args.symbol, args.timeframe, args.training_period)
    print(f"Ottenute {len(df)} candele.")
    
    # Aggiungi indicatori tecnici
    print("Calcolo indicatori tecnici...")
    df_with_indicators = data_processor.add_technical_indicators(df)
    print(f"Calcolati indicatori tecnici. Righe rimanenti: {len(df_with_indicators)}")
    
    # Prepara dati per l'addestramento
    print("Preparo i dati per l'addestramento...")
    X, y = data_processor.prepare_data_for_training(df_with_indicators)
    print(f"Dati preparati. X shape: {X.shape}, y shape: {y.shape}")
    
    # Dividi i dati in training, validation e test
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=args.test_split, shuffle=False
    )
    
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=args.validation_split, shuffle=False
    )
    
    print(f"Dati divisi. Training: {X_train.shape[0]}, Validation: {X_val.shape[0]}, Test: {X_test.shape[0]}")
    
    # Crea gestore del modello
    model_manager = ModelManager()
    
    # Costruisci modello
    print("Costruisco il modello LSTM...")
    model_manager.build_model((X_train.shape[1], X_train.shape[2]))
    
    # Configura percorsi di output
    output_paths = setup_output_paths(args.output_path, args.symbol, args.timeframe)
    
    # Addestra modello
    print(f"Addestro il modello per {args.epochs} epoche con batch size {args.batch_size}...")
    history = model_manager.train_model(
        X_train, y_train,
        X_val, y_val,
        epochs=args.epochs,
        batch_size=args.batch_size,
        checkpoint_path=output_paths["model"] + "_checkpoint"
    )
    
    # Valuta modello
    print("Valuto il modello sul test set...")
    metrics = model_manager.evaluate_model(X_test, y_test)
    print(f"Metriche: {metrics}")
    
    # Salva modello e metriche
    print("Salvo il modello e le metriche...")
    model_manager.save_model(
        output_paths["model"],
        output_paths["history"],
        output_paths["metrics"],
        history,
        metrics
    )
    
    # Salva scalers
    data_processor.save_scalers(output_paths["scalers"])
    
    # Crea sommario
    summary = {
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "training_period": args.training_period,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "validation_split": args.validation_split,
        "test_split": args.test_split,
        "seed": args.seed,
        "data_shape": {
            "total_samples": len(df_with_indicators),
            "sequence_length": X.shape[1],
            "num_features": X.shape[2],
            "training_samples": X_train.shape[0],
            "validation_samples": X_val.shape[0],
            "test_samples": X_test.shape[0]
        },
        "metrics": metrics,
        "paths": {
            "model": os.path.relpath(output_paths["model"], args.output_path),
            "history": os.path.relpath(output_paths["history"], args.output_path),
            "metrics": os.path.relpath(output_paths["metrics"], args.output_path),
            "scalers": os.path.relpath(output_paths["scalers"], args.output_path)
        },
        "timestamp": datetime.now().isoformat()
    }
    
    # Salva sommario
    with open(output_paths["summary"], 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Addestramento completato. Modello salvato in {output_paths['model']}")
    
    return summary

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
        # Addestra modello
        summary = train_model(args)
        
        # Stampa sommario
        print(json.dumps(summary, indent=2))
        
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
