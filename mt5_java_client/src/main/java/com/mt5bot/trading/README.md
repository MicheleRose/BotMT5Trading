# MT5 Trading Bot - Modulo di Trading

Questo modulo implementa il sistema di trading automatico per MetaTrader 5. Il sistema è progettato per essere modulare, configurabile e robusto, con una gestione avanzata del rischio e un'architettura orientata ai servizi.

## Architettura

Il sistema è composto dai seguenti componenti principali:

### TradingBot

La classe principale che funge da entry point per l'applicazione. Si occupa di:

- Inizializzare tutti i componenti del sistema
- Gestire il ciclo principale di trading
- Coordinare i vari servizi
- Gestire lo shutdown graceful

### MarketDataService

Servizio per la gestione dei dati di mercato. Si occupa di:

- Mantenere una cache dei dati di mercato
- Aggiornare periodicamente i dati
- Ottimizzare le chiamate al server MT5
- Preprocessare i dati per il modello LSTM

### IndicatorService

Servizio per il calcolo degli indicatori tecnici. Implementa:

- Calcolo real-time degli indicatori
- Implementazione dei segnali di ingresso
- Supporto per RSI, MACD, Bollinger Bands, ADX, Stocastico
- Configurazione personalizzabile degli indicatori

### SchedulerService

Servizio per la gestione dei task periodici. Si occupa di:

- Monitorare le posizioni aperte
- Verificare le condizioni di mercato
- Aggiornare i trailing stop
- Gestire task personalizzati

### Risk Management

Sistema di gestione del rischio. Implementa:

- Protezione del capitale
- Gestione delle posizioni stagnanti
- Target di profitto globale
- Protezione del margine

## Configurazione

Il sistema è completamente configurabile tramite file di proprietà:

- `trading_bot.properties`: Configurazione generale del trading bot
- `logging.properties`: Configurazione del logging

## Utilizzo

### Avvio del Trading Bot

```bash
# Avvio con configurazione predefinita
./run_trading_bot.bat

# Avvio con configurazione personalizzata
java -cp target/mt5-java-client-1.0-SNAPSHOT-jar-with-dependencies.jar main.java.com.mt5bot.trading.TradingBot path/to/config.properties
```

### Implementazione di una Strategia Personalizzata

Per implementare una strategia personalizzata, è possibile estendere il sistema in diversi modi:

1. **Modifica della configurazione**: Personalizzare i parametri degli indicatori e delle strategie esistenti
2. **Implementazione di nuovi indicatori**: Aggiungere nuovi indicatori tecnici al servizio IndicatorService
3. **Implementazione di nuove regole di ingresso/uscita**: Modificare i metodi `checkEntryConditions` e `checkExitConditions` nella classe TradingBot
4. **Implementazione di nuovi handler di risk management**: Creare nuove classi che estendono AbstractRiskHandler

## Caratteristiche Principali

- **Pattern Singleton**: Tutti i servizi sono implementati come singleton per garantire un'unica istanza
- **Thread-safety**: Tutti i componenti sono thread-safe e utilizzano meccanismi di sincronizzazione appropriati
- **Lazy Initialization**: I servizi vengono inizializzati solo quando necessario
- **Configurazione Completa**: Tutti i parametri sono configurabili tramite file di proprietà
- **Logging Strutturato**: Sistema di logging completo e configurabile
- **Gestione Errori Robusta**: Gestione degli errori a tutti i livelli
- **Recovery Automatico**: Riconnessione automatica in caso di disconnessione

## Diagramma delle Classi

```
TradingBot
├── MarketDataService
├── IndicatorService
├── SchedulerService
├── RiskManager
│   ├── StagnantPositionHandler
│   ├── ProfitTargetHandler
│   └── MarginProtector
└── PositionManager
```

## Diagramma di Sequenza

```
TradingBot                MarketDataService       IndicatorService        RiskManager
    │                           │                       │                     │
    │ start()                   │                       │                     │
    │ ─────────────────────────>│                       │                     │
    │                           │ start()               │                     │
    │ ─────────────────────────────────────────────────>│                     │
    │                           │                       │ start()             │
    │ ─────────────────────────────────────────────────────────────────────> │
    │                           │                       │                     │
    │ startTradingLoop()        │                       │                     │
    │ ───┐                      │                       │                     │
    │    │                      │                       │                     │
    │ <──┘                      │                       │                     │
    │                           │                       │                     │
    │ executeStrategy()         │                       │                     │
    │ ───┐                      │                       │                     │
    │    │ getMarketData()      │                       │                     │
    │    │ ─────────────────────>                       │                     │
    │    │ <─────────────────────                       │                     │
    │    │                      │                       │                     │
    │    │ calculateIndicators()│                       │                     │
    │    │ ─────────────────────────────────────────────>                     │
    │    │ <─────────────────────────────────────────────                     │
    │    │                      │                       │                     │
    │    │ checkEntryConditions()                       │                     │
    │    │ ───┐                 │                       │                     │
    │    │    │                 │                       │                     │
    │    │ <──┘                 │                       │                     │
    │    │                      │                       │                     │
    │    │ openPosition()       │                       │                     │
    │    │ ───┐                 │                       │                     │
    │    │    │ canOpenPosition()                       │                     │
    │    │    │ ───────────────────────────────────────────────────────────> │
    │    │    │ <─────────────────────────────────────────────────────────── │
    │    │    │                 │                       │                     │
    │    │    │ marketBuy()     │                       │                     │
    │    │    │ ───┐            │                       │                     │
    │    │    │    │            │                       │                     │
    │    │    │ <──┘            │                       │                     │
    │    │ <──┘                 │                       │                     │
    │ <──┘                      │                       │                     │
```

## Requisiti di Sistema

- Java 11 o superiore
- MetaTrader 5
- Maven 3.6 o superiore

## Licenza

Questo progetto è rilasciato sotto licenza MIT.
