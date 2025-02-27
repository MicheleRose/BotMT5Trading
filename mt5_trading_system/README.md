# MT5 Trading Bot

Un sistema di comunicazione Python per MetaTrader 5 (MT5) che consente di automatizzare operazioni di trading tramite un'architettura client-server.

## Caratteristiche Principali

### MT5 Keeper (Processo Server)

- **Processo singleton** per la gestione della connessione persistente a MetaTrader 5
- **Inizializzazione unica** della connessione MT5
- **Directory di lavoro cross-platform** (`~/.mt5bot/`)
- **Meccanismo file lock** per verifica istanza singola
- **Comunicazione file-based** tramite directory `commands/` e `results/`
- **Heartbeat** per mantenimento sessione
- **Riconnessione automatica** in caso di disconnessione

### MT5CommandBase (Classe Base Client)

- **Classe base** per tutti gli script client
- **Verifica esistenza keeper** prima dell'invio dei comandi
- **Gestione timeout e errori** per comunicazione robusta
- **Parsing argomenti command-line** per facile utilizzo
- **Protocollo comunicazione file-based** con MT5 Keeper

### Moduli Funzionali

#### Analisi di Mercato

- **Check Spread**: Verifica e categorizza lo spread di un simbolo
- **Get Market Data**: Ottiene dati storici OHLCV per un simbolo e timeframe
- **Get Indicator Data**: Calcola indicatori tecnici (RSI, MACD, Bollinger Bands, ADX, Stochastic, ATR)
- **Calculate Volatility**: Calcola la volatilità e suggerisce valori per stop loss e take profit

#### Comandi di Trading

- **Market Buy/Sell**: Apertura posizioni a mercato
- **Modify Position**: Modifica stop loss e take profit di posizioni aperte
- **Close Position**: Chiusura totale o parziale di posizioni
- **Close All Positions**: Chiusura di tutte le posizioni (con filtri opzionali)
- **Get Positions**: Informazioni sulle posizioni aperte
- **Get Account Info**: Informazioni sull'account (balance, equity, margin, ecc.)

## Requisiti

- Python 3.6+
- MetaTrader 5 installato
- Libreria Python MetaTrader5 (`pip install MetaTrader5`)

## Struttura del Progetto

```
mt5_trading_system/
├── analysis/                # Script per analisi di mercato
│   ├── calculate_volatility.py
│   ├── check_spread.py
│   ├── get_indicator_data.py
│   └── get_market_data.py
├── commands/                # Script per operazioni di trading
│   ├── close_all_positions.py
│   ├── close_position.py
│   ├── get_account_info.py
│   ├── get_positions.py
│   ├── market_buy.py
│   ├── market_sell.py
│   └── modify_position.py
├── config/                  # File di configurazione
│   └── mt5_config.json
├── core/                    # Componenti core del sistema
│   ├── mt5_command_base.py  # Classe base per tutti i client
│   └── mt5_keeper.py        # Server per connessione persistente
├── ml/                      # Modelli di machine learning
│   ├── __init__.py
│   ├── train_model.py       # Script per addestramento modello LSTM
│   ├── predict_direction.py # Script per previsione direzione prezzi
│   └── utils.py             # Utilità per preprocessing e gestione modelli
└── tests/                   # Script di test
    ├── run_test_with_keeper.py
    ├── test_mt5.py
    └── test_trading_system.py
```

## Configurazione

Il sistema utilizza un file di configurazione JSON per impostare i parametri di connessione a MetaTrader 5:

```json
{
  "account": 650586,
  "password": "_4XeVtQj",
  "server": "TenTrade-Server",
  "timeout": 60000,
  "command_check_interval": 1.0,
  "heartbeat_interval": 30.0,
  "reconnect_interval": 60.0,
  "debug": false,
  "mt5_account": {
    "nome": "GG Allin",
    "server": "TenTrade-Server",
    "tipo": "MTQ leads",
    "login": 650586,
    "password": "_4XeVtQj",
    "investitore": "7hJm!iQu"
  }
}
```

## Esempi di Utilizzo

### Avvio di MT5 Keeper

```bash
python -m mt5_trading_system.core.mt5_keeper -c mt5_trading_system/config/mt5_config.json
```

### Verifica dello Spread

```bash
python -m mt5_trading_system.analysis.check_spread EURUSD
```

Output:
```json
{
  "success": true,
  "symbol": "EURUSD",
  "from_cache": false,
  "data": {
    "symbol": "EURUSD",
    "symbol_type": "forex_major",
    "spread_points": 1,
    "spread_pips": 10,
    "spread_percent": 0.001,
    "point_value": 1e-05,
    "digits": 5,
    "ask": 1.04752,
    "bid": 1.04751,
    "category": "basso",
    "evaluation": "Ottimo spread, ideale per trading ad alta frequenza e scalping.",
    "timestamp": "2025-02-27T11:44:35.360034"
  }
}
```

### Calcolo di Indicatori Tecnici

```bash
python -m mt5_trading_system.analysis.get_indicator_data EURUSD H4 RSI --period 14
```

### Apertura di una Posizione

```bash
python -m mt5_trading_system.commands.market_buy EURUSD 0.1 --sl 1.0450 --tp 1.0500
```

### Ottenere Informazioni sull'Account

```bash
python -m mt5_trading_system.commands.get_account_info
```

Output:
```json
{
  "success": true,
  "account_info": {
    "login": 12345678,
    "server": "Demo Server",
    "currency": "USD",
    "leverage": 100,
    "balance": 1038.98,
    "equity": 7108.89,
    "margin": 437.43,
    "free_margin": 3451.61,
    "margin_level": 344.29,
    "profit": 47.17
  },
  "timestamp": "2025-02-27T12:08:17.696138"
}
```

## Test del Sistema

Il sistema include script di test per verificare il corretto funzionamento:

### Test di Connessione a MT5

```bash
python -m mt5_trading_system.tests.test_mt5
```

### Test Completo del Sistema di Trading

```bash
python -m mt5_trading_system.tests.test_trading_system -c mt5_trading_system/config/mt5_config.json
```

### Test con Avvio Automatico di MT5 Keeper

```bash
python -m mt5_trading_system.tests.run_test_with_keeper -c mt5_trading_system/config/mt5_config.json
```

### Test del Modulo di Machine Learning

#### Addestramento di un Modello LSTM

```bash
# Addestramento con 1000 candele, 10 epoche e batch size 32
python -m mt5_trading_system.ml.train_model EURUSD H1 1000 ./models/lstm -e 10 -b 32

# Addestramento rapido per test (100 candele, 2 epoche)
python -m mt5_trading_system.ml.train_model EURUSD H1 100 ./models/lstm -e 2 -b 16 -d
```

#### Generazione di Previsioni

```bash
# Previsione utilizzando un modello esistente
python -m mt5_trading_system.ml.predict_direction EURUSD ./models/lstm/models/EURUSD_H1_model.keras -s ./models/lstm/scalers/EURUSD_H1_scalers.pkl

# Output di esempio:
# {
#   "probability": 0.7234,
#   "direction": "up",
#   "confidence": 0.4468,
#   "symbol": "EURUSD",
#   "timeframe": "H1",
#   "timestamp": "2025-02-27T12:30:45.123456",
#   "last_price": 1.04756,
#   "indicators": {
#     "rsi": 58.42,
#     "macd": 0.00023,
#     "adx": 24.56,
#     "atr": 0.00042
#   }
# }
```

## Caratteristiche Avanzate

- **Cache dei dati**: Riduzione delle richieste a MT5 per dati frequentemente utilizzati
- **Modalità debug**: Logging dettagliato per troubleshooting
- **Modalità test**: Generazione di dati finti per test senza connessione a MT5
- **Gestione errori robusta**: Rilevamento e gestione di errori di connessione e timeout
- **Cross-platform**: Funzionamento su Windows e macOS

## Estensibilità

Il sistema è progettato per essere facilmente estensibile:

1. Nuovi comandi possono essere aggiunti creando nuovi script che ereditano da `MT5CommandBase`
2. Nuovi indicatori tecnici possono essere implementati in `get_indicator_data.py`
3. Nuove strategie di trading possono essere costruite combinando i comandi esistenti

## Sicurezza

- **Nessun trading reale di default**: La configurazione predefinita disabilita il trading reale
- **File lock**: Impedisce l'esecuzione di più istanze di MT5 Keeper
- **Validazione input**: Tutti gli input vengono validati prima dell'invio a MT5
- **Gestione delle credenziali**: Le credenziali sono memorizzate solo nel file di configurazione
