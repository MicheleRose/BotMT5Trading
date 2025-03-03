# MT5 Trading Bot GUI

Interfaccia grafica per il sistema MT5 Trading Bot, sviluppata con TTKBootstrap.

## Descrizione

MT5 Trading Bot GUI è un'applicazione desktop che fornisce un'interfaccia grafica per il sistema MT5 Trading Bot. L'applicazione consente di monitorare e gestire il trading automatico su MetaTrader 5 attraverso MT5 Keeper.

## Funzionalità

- **Dashboard**: Visualizzazione dello stato dell'account e del trading bot
- **Posizioni**: Gestione delle posizioni aperte
- **Configurazione**: Configurazione del trading bot tramite file JSON
- **Grafici**: Visualizzazione dei grafici di mercato e delle performance
- **Log**: Visualizzazione dei log delle operazioni

## Requisiti

- Python 3.7+
- MetaTrader 5
- MT5 Keeper (per la comunicazione con MetaTrader 5)
- Librerie Python:
  - ttkbootstrap
  - matplotlib
  - numpy

## Installazione

1. Clona il repository:
   ```
   git clone https://github.com/tuorepository/mt5_trading_system.git
   cd mt5_trading_system
   ```

2. Installa le dipendenze:
   ```
   pip install ttkbootstrap matplotlib numpy
   ```

3. Configura MT5 Keeper e assicurati che sia in esecuzione.

4. Configura il file `config/mt5_config.json` con i parametri di connessione a MT5 Keeper.

5. Configura il file `config/trading_config.json` con i parametri di trading.

## Utilizzo

Esegui lo script di avvio:

```
python run_gui.py
```

### Dashboard

La dashboard mostra le informazioni principali sull'account e sullo stato del trading bot. Da qui è possibile avviare e fermare il bot.

### Posizioni

La scheda Posizioni mostra le posizioni aperte e consente di chiuderle o modificarle.

### Configurazione

La scheda Configurazione consente di modificare i parametri del trading bot. Le modifiche possono essere salvate su file.

### Grafici

La scheda Grafici mostra i grafici di mercato e le performance del trading bot.

### Log

La scheda Log mostra i log delle operazioni del trading bot.

## Struttura del Progetto

```
gui/
├── __init__.py
├── main.py
├── components/
│   ├── __init__.py
│   ├── dashboard.py
│   ├── positions.py
│   ├── config.py
│   ├── charts.py
│   └── logs.py
└── utils/
    ├── __init__.py
    ├── mt5_client.py
    ├── config_manager.py
    └── logger.py
```

## Licenza

Questo progetto è distribuito con licenza MIT.
