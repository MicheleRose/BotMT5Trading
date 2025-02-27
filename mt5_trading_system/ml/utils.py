#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilità per i modelli di machine learning.

Questo modulo contiene funzioni di utilità per il preprocessing dei dati,
l'estrazione di features, la normalizzazione e la gestione dei modelli.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional, Union
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model, save_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Aggiungi la directory principale al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from mt5_trading_system.core.mt5_command_base import MT5CommandBase

# Costanti
SEQUENCE_LENGTH = 20  # Numero di candele per sequenza
FEATURE_COLUMNS = [
    'open', 'high', 'low', 'close', 'volume',
    'rsi', 'macd', 'macd_signal', 'macd_hist',
    'atr', 'adx', 'plus_di', 'minus_di',
    'bb_upper', 'bb_middle', 'bb_lower'
]

# Classe per la gestione dei dati
class DataProcessor:
    """
    Classe per il preprocessing dei dati e l'estrazione di features.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inizializza il processore di dati.
        
        Args:
            config_path: Percorso al file di configurazione JSON
        """
        self.mt5_cmd = MT5CommandBase(config_path)
        self.scalers = {}  # Dizionario di scalers per ogni feature
    
    def get_market_data(self, symbol: str, timeframe: str, num_candles: int) -> pd.DataFrame:
        """
        Ottiene dati storici di mercato da MT5.
        
        Args:
            symbol: Simbolo (es. EURUSD)
            timeframe: Timeframe (es. H1)
            num_candles: Numero di candele da ottenere
            
        Returns:
            DataFrame con i dati di mercato
        """
        # Mappa timeframe a formato MT5
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
            raise ValueError(f"Timeframe non valido. Valori consentiti: {', '.join(timeframe_map.keys())}")
        
        # Ottieni dati
        rates = self.mt5_cmd.send_command("copy_rates_from", {
            "symbol": symbol,
            "timeframe": timeframe_map[timeframe],
            "count": num_candles
        })
        
        if not rates:
            raise ValueError(f"Nessun dato disponibile per {symbol} su timeframe {timeframe}")
        
        # Converti in DataFrame
        df = pd.DataFrame(rates, columns=['time', 'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume'])
        
        # Converti timestamp in datetime
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Rinomina colonne
        df.rename(columns={'tick_volume': 'volume'}, inplace=True)
        
        # Ordina per tempo
        df.sort_values('time', inplace=True)
        df.reset_index(drop=True, inplace=True)
        
        return df
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aggiunge indicatori tecnici al DataFrame.
        
        Args:
            df: DataFrame con dati OHLCV
            
        Returns:
            DataFrame con indicatori tecnici aggiunti
        """
        # Copia DataFrame
        df_with_indicators = df.copy()
        
        # RSI
        df_with_indicators['rsi'] = self._calculate_rsi(df_with_indicators['close'])
        
        # MACD
        macd, signal, hist = self._calculate_macd(df_with_indicators['close'])
        df_with_indicators['macd'] = macd
        df_with_indicators['macd_signal'] = signal
        df_with_indicators['macd_hist'] = hist
        
        # ATR
        df_with_indicators['atr'] = self._calculate_atr(
            df_with_indicators['high'], 
            df_with_indicators['low'], 
            df_with_indicators['close']
        )
        
        # ADX
        adx, plus_di, minus_di = self._calculate_adx(
            df_with_indicators['high'], 
            df_with_indicators['low'], 
            df_with_indicators['close']
        )
        df_with_indicators['adx'] = adx
        df_with_indicators['plus_di'] = plus_di
        df_with_indicators['minus_di'] = minus_di
        
        # Bollinger Bands
        upper, middle, lower = self._calculate_bollinger_bands(df_with_indicators['close'])
        df_with_indicators['bb_upper'] = upper
        df_with_indicators['bb_middle'] = middle
        df_with_indicators['bb_lower'] = lower
        
        # Rimuovi righe con NaN (dovute al calcolo degli indicatori)
        df_with_indicators.dropna(inplace=True)
        df_with_indicators.reset_index(drop=True, inplace=True)
        
        return df_with_indicators
    
    def prepare_data_for_training(self, df: pd.DataFrame, target_column: str = 'close') -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepara i dati per l'addestramento del modello.
        
        Args:
            df: DataFrame con dati e indicatori
            target_column: Colonna target per la previsione
            
        Returns:
            Tuple con X (features) e y (target)
        """
        # Crea target: 1 se il prezzo sale, 0 se scende
        df['target'] = (df[target_column].shift(-1) > df[target_column]).astype(int)
        
        # Rimuovi l'ultima riga (NaN nel target)
        df = df[:-1]
        
        # Seleziona colonne per features
        feature_columns = [col for col in FEATURE_COLUMNS if col in df.columns]
        
        # Normalizza features
        X_scaled = self._normalize_features(df[feature_columns])
        
        # Crea sequenze
        X, y = self._create_sequences(X_scaled, df['target'].values)
        
        return X, y
    
    def prepare_data_for_prediction(self, df: pd.DataFrame) -> np.ndarray:
        """
        Prepara i dati per la previsione.
        
        Args:
            df: DataFrame con dati e indicatori
            
        Returns:
            Array con features normalizzate
        """
        # Seleziona colonne per features
        feature_columns = [col for col in FEATURE_COLUMNS if col in df.columns]
        
        # Normalizza features
        X_scaled = self._normalize_features(df[feature_columns], training=False)
        
        # Crea sequenza
        X = X_scaled[-SEQUENCE_LENGTH:].reshape(1, SEQUENCE_LENGTH, len(feature_columns))
        
        return X
    
    def _normalize_features(self, features: pd.DataFrame, training: bool = True) -> np.ndarray:
        """
        Normalizza le features.
        
        Args:
            features: DataFrame con features
            training: True se in fase di training, False per predizione
            
        Returns:
            Array con features normalizzate
        """
        # Crea array per dati normalizzati
        normalized_data = np.zeros((len(features), len(features.columns)))
        
        # Normalizza ogni colonna
        for i, column in enumerate(features.columns):
            if training:
                # In fase di training, crea un nuovo scaler
                scaler = MinMaxScaler(feature_range=(0, 1))
                normalized_data[:, i] = scaler.fit_transform(features[column].values.reshape(-1, 1)).flatten()
                self.scalers[column] = scaler
            else:
                # In fase di predizione, usa lo scaler esistente
                if column in self.scalers:
                    normalized_data[:, i] = self.scalers[column].transform(features[column].values.reshape(-1, 1)).flatten()
                else:
                    # Se lo scaler non esiste, crea uno nuovo (non ideale, ma evita errori)
                    scaler = MinMaxScaler(feature_range=(0, 1))
                    normalized_data[:, i] = scaler.fit_transform(features[column].values.reshape(-1, 1)).flatten()
                    self.scalers[column] = scaler
        
        return normalized_data
    
    def _create_sequences(self, data: np.ndarray, target: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Crea sequenze per l'addestramento LSTM.
        
        Args:
            data: Array con features normalizzate
            target: Array con target
            
        Returns:
            Tuple con X (sequenze) e y (target)
        """
        X, y = [], []
        
        for i in range(len(data) - SEQUENCE_LENGTH):
            X.append(data[i:i + SEQUENCE_LENGTH])
            y.append(target[i + SEQUENCE_LENGTH])
        
        return np.array(X), np.array(y)
    
    def save_scalers(self, path: str) -> None:
        """
        Salva gli scalers su file.
        
        Args:
            path: Percorso dove salvare gli scalers
        """
        # Crea directory se non esiste
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Salva scalers
        with open(path, 'wb') as f:
            import pickle
            pickle.dump(self.scalers, f)
    
    def load_scalers(self, path: str) -> None:
        """
        Carica gli scalers da file.
        
        Args:
            path: Percorso da cui caricare gli scalers
        """
        if os.path.exists(path):
            with open(path, 'rb') as f:
                import pickle
                self.scalers = pickle.load(f)
    
    # Implementazione degli indicatori tecnici
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calcola l'indicatore RSI (Relative Strength Index).
        
        Args:
            prices: Serie di prezzi
            period: Periodo per il calcolo
            
        Returns:
            Serie con i valori dell'RSI
        """
        # Calcola le differenze tra i prezzi
        delta = prices.diff()
        
        # Separa guadagni e perdite
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # Calcola le medie mobili di guadagni e perdite
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        # Calcola RS e RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calcola l'indicatore MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Serie di prezzi
            fast_period: Periodo veloce
            slow_period: Periodo lento
            signal_period: Periodo segnale
            
        Returns:
            Tuple con MACD Line, Signal Line e Histogram
        """
        # Calcola le medie mobili esponenziali
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
        
        # Calcola MACD Line
        macd_line = ema_fast - ema_slow
        
        # Calcola Signal Line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        
        # Calcola Histogram
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, deviation: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calcola l'indicatore Bollinger Bands.
        
        Args:
            prices: Serie di prezzi
            period: Periodo per il calcolo
            deviation: Deviazione standard
            
        Returns:
            Tuple con Upper Band, Middle Band e Lower Band
        """
        # Calcola la media mobile semplice (Middle Band)
        middle_band = prices.rolling(window=period).mean()
        
        # Calcola la deviazione standard
        std_dev = prices.rolling(window=period).std()
        
        # Calcola Upper e Lower Band
        upper_band = middle_band + (deviation * std_dev)
        lower_band = middle_band - (deviation * std_dev)
        
        return upper_band, middle_band, lower_band
    
    def _calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Calcola l'indicatore ATR (Average True Range).
        
        Args:
            high: Serie di prezzi massimi
            low: Serie di prezzi minimi
            close: Serie di prezzi di chiusura
            period: Periodo per il calcolo
            
        Returns:
            Serie con i valori dell'ATR
        """
        # Calcola True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calcola ATR
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    def _calculate_adx(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calcola l'indicatore ADX (Average Directional Index).
        
        Args:
            high: Serie di prezzi massimi
            low: Serie di prezzi minimi
            close: Serie di prezzi di chiusura
            period: Periodo per il calcolo
            
        Returns:
            Tuple con ADX, +DI e -DI
        """
        # Calcola True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calcola Directional Movement
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        plus_dm = pd.Series(plus_dm, index=high.index)
        minus_dm = pd.Series(minus_dm, index=high.index)
        
        # Calcola ATR
        atr = tr.rolling(window=period).mean()
        
        # Calcola +DI e -DI
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        # Calcola DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        
        # Calcola ADX
        adx = dx.rolling(window=period).mean()
        
        return adx, plus_di, minus_di

# Classe per la gestione del modello
class ModelManager:
    """
    Classe per la gestione del modello LSTM.
    """
    
    def __init__(self):
        """
        Inizializza il gestore del modello.
        """
        self.model = None
    
    def build_model(self, input_shape: Tuple[int, int]) -> None:
        """
        Costruisce il modello LSTM.
        
        Args:
            input_shape: Forma dell'input (sequence_length, num_features)
        """
        self.model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50),
            Dropout(0.2),
            Dense(25, activation='relu'),
            Dense(1, activation='sigmoid')
        ])
        
        # Compila il modello
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
    
    def train_model(self, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray, 
                   epochs: int = 10, batch_size: int = 32, checkpoint_path: Optional[str] = None) -> Dict[str, List[float]]:
        """
        Addestra il modello LSTM.
        
        Args:
            X_train: Features di training
            y_train: Target di training
            X_val: Features di validazione
            y_val: Target di validazione
            epochs: Numero di epoche
            batch_size: Dimensione del batch
            checkpoint_path: Percorso per salvare i checkpoint
            
        Returns:
            Dizionario con la storia dell'addestramento
        """
        if self.model is None:
            raise ValueError("Il modello non è stato costruito. Chiamare build_model() prima di train_model().")
        
        # Callbacks
        callbacks = []
        
        # Early stopping
        early_stopping = EarlyStopping(
            monitor='val_loss',
            patience=5,
            restore_best_weights=True
        )
        callbacks.append(early_stopping)
        
        # Model checkpoint
        if checkpoint_path:
            os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
            # Assicurati che il percorso del file termini con .keras
            if not checkpoint_path.endswith('.keras'):
                checkpoint_path = f"{checkpoint_path}.keras"
            
            model_checkpoint = ModelCheckpoint(
                filepath=checkpoint_path,
                save_best_only=True,
                monitor='val_loss'
            )
            callbacks.append(model_checkpoint)
        
        # Addestra il modello
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        # Converti history in dizionario
        history_dict = {
            'loss': history.history['loss'],
            'accuracy': history.history['accuracy'],
            'val_loss': history.history['val_loss'],
            'val_accuracy': history.history['val_accuracy']
        }
        
        return history_dict
    
    def evaluate_model(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Valuta il modello.
        
        Args:
            X_test: Features di test
            y_test: Target di test
            
        Returns:
            Dizionario con le metriche di valutazione
        """
        if self.model is None:
            raise ValueError("Il modello non è stato costruito. Chiamare build_model() prima di evaluate_model().")
        
        # Predizioni
        y_pred_prob = self.model.predict(X_test)
        y_pred = (y_pred_prob > 0.5).astype(int).flatten()
        
        # Calcola metriche
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred)),
            'recall': float(recall_score(y_test, y_pred)),
            'f1_score': float(f1_score(y_test, y_pred))
        }
        
        return metrics
    
    def predict(self, X: np.ndarray) -> Dict[str, float]:
        """
        Genera una previsione.
        
        Args:
            X: Features
            
        Returns:
            Dizionario con la previsione
        """
        if self.model is None:
            raise ValueError("Il modello non è stato costruito o caricato.")
        
        # Predizione
        prediction = float(self.model.predict(X)[0, 0])
        
        # Calcola confidence score
        confidence = abs(prediction - 0.5) * 2  # 0.5 -> 0.0, 0.0/1.0 -> 1.0
        
        # Direzione
        direction = "up" if prediction > 0.5 else "down"
        
        return {
            'probability': prediction,
            'direction': direction,
            'confidence': float(confidence)
        }
    
    def save_model(self, model_path: str, history_path: Optional[str] = None, metrics_path: Optional[str] = None,
                  history: Optional[Dict[str, List[float]]] = None, metrics: Optional[Dict[str, float]] = None) -> None:
        """
        Salva il modello e le metriche.
        
        Args:
            model_path: Percorso dove salvare il modello
            history_path: Percorso dove salvare la storia dell'addestramento
            metrics_path: Percorso dove salvare le metriche
            history: Storia dell'addestramento
            metrics: Metriche di valutazione
        """
        if self.model is None:
            raise ValueError("Il modello non è stato costruito o caricato.")
        
        # Crea directory se non esiste
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Assicurati che il percorso del file termini con .keras
        if not model_path.endswith('.keras'):
            model_path = f"{model_path}.keras"
            
        # Salva il modello
        self.model.save(model_path)
        
        # Salva la storia dell'addestramento
        if history_path and history:
            with open(history_path, 'w') as f:
                json.dump(history, f, indent=2)
        
        # Salva le metriche
        if metrics_path and metrics:
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)
    
    def load_model(self, model_path: str) -> None:
        """
        Carica il modello.
        
        Args:
            model_path: Percorso da cui caricare il modello
        """
        # Assicurati che il percorso del file termini con .keras
        if not model_path.endswith('.keras'):
            model_path_keras = f"{model_path}.keras"
            # Verifica se esiste il file con estensione .keras
            if os.path.exists(model_path_keras):
                model_path = model_path_keras
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Il file del modello non esiste: {model_path}")
        
        # Carica il modello
        self.model = load_model(model_path)
