# AI Scalping Ultra v3.0

Bot di trading automatico avanzato che utilizza indicatori tecnici multipli, gestione adattiva del rischio e entrata scalare intelligente per operare sui mercati finanziari attraverso MetaTrader 5.

## Caratteristiche Principali

- Entrata scalare intelligente con gestione automatica delle posizioni
- Stop Loss e Take Profit adattivi basati sulla volatilità (ATR)
- Trailing Stop automatico per protezione dei profitti
- Analisi multi-indicatore (RSI, MACD, Bollinger Bands, ADX, Stocastico, ATR)
- Gestione adattiva del rischio con protezione del margine
- Verifica dello spread prima delle operazioni
- Chiusura automatica delle posizioni stagnanti
- Interfaccia utente colorata in tempo reale
- Sistema di logging completo

## Requisiti

- Python 3.8+
- MetaTrader 5
- Librerie Python richieste (vedi requirements.txt)

## Struttura del Progetto

```
GiovanniPython/
├── src/              # Codice sorgente
│   ├── main.py           # Entry point
│   ├── mt5_connector.py  # Connettore MetaTrader 5
│   ├── trading_logic.py  # Logica di trading
│   ├── display_manager.py # Interfaccia utente
│   └── config_validator.py # Validazione configurazione
│
├── config/           # File di configurazione
│   ├── config.json       # Configurazione trading
│   ├── access.json      # Credenziali MT5
│   └── requirements.txt # Dipendenze Python
│
├── logs/            # File di log
│   ├── journal.log     # Log operazioni
│   └── error.log      # Log errori
│
├── README.md        # Documentazione
└── run_bot.bat      # Script di avvio
```

## Installazione

1. Clonare il repository
2. Installare le dipendenze: `pip install -r config/requirements.txt`
3. Configurare MetaTrader 5 con le credenziali appropriate
4. Modificare il file `config/access.json` con le proprie credenziali MT5
5. Personalizzare `config/config.json` secondo le proprie esigenze

## Configurazione

Il bot utilizza due file di configurazione principali che vengono validati automaticamente all'avvio:

### access.json
Contiene le credenziali di accesso a MetaTrader 5:
```json
{
    "mt5_account": {
        "login": 123456,        // Numero account MT5
        "password": "password", // Password account
        "server": "Server"      // Nome server MT5
    }
}
```

### config.json
Contiene tutte le impostazioni di trading e degli indicatori:

#### Trading Base
```json
{
    "symbol": "XAUUSD",          // Simbolo da tradare
    "timeframe": "M1",           // Timeframe (M1, M5, M15, M30, H1, H4, D1)
    "initial_trades": 3,         // Numero operazioni iniziali
    "max_concurrent_trades": 20, // Massimo operazioni contemporanee
    "pip_step_for_new_trades": 15, // Pips per nuove operazioni
    "trades_per_step": 4,        // Operazioni per ogni step
    "max_loss": 100,            // Massima perdita consentita
    
    "lot_size": {
        "initial": 0.01,         // Lotto iniziale
        "increment": 0.01,       // Incremento lotto
        "increment_every": 4     // Ogni quante operazioni
    }
}
```

#### Controlli e Protezioni
```json
{
    "spread_check": {
        "max_spread_points": 20, // Spread massimo consentito
        "enabled": true         // Attiva verifica spread
    },
    
    "trailing_stop": {
        "enabled": true,        // Attiva trailing stop
        "pips": 30             // Distanza trailing stop
    },
    
    "stagnant_trade": {
        "max_minutes": 50,      // Minuti per chiusura
        "enabled": true        // Attiva controllo
    }
}
```

#### Gestione Posizioni
```json
{
    "position_management": {
        "min_pips_between_orders": 15, // Distanza minima ordini
        "floating_profit_close": 2.0,  // % profitto per chiusura
        "hedge_protection": false      // Protezione hedge
    }
}
```

#### Gestione Rischio
```json
{
    "margin_protection": {
        "min_free_margin": 50,  // Margine minimo
        "enabled": true        // Attiva protezione
    },
    "max_drawdown_percentage": 15, // Massimo drawdown
    "max_risk_per_trade": 1.0    // Rischio per trade
}
```

#### Stop Loss e Take Profit Adattivi
```json
{
    "adaptive_sl_tp": {
        "atr_periods": 2,        // Periodi ATR
        "sl_multiplier": 1.5,    // Moltiplicatore SL
        "tp_multiplier": 2.0,    // Moltiplicatore TP
        "market_conditions": {
            "calm": {
                "sl_pips": 30,    // SL mercato calmo
                "tp_pips": 40     // TP mercato calmo
            },
            "normal": {
                "sl_pips": 45,    // SL mercato normale
                "tp_pips": 60     // TP mercato normale
            },
            "volatile": {
                "sl_pips": 75,    // SL mercato volatile
                "tp_pips": 100    // TP mercato volatile
            }
        }
    }
}
```

#### Indicatori
```json
{
    "rsi": {
        "period": 2,
        "oversold": 15,
        "overbought": 85
    },
    "macd": {
        "fast_period": 2,
        "slow_period": 4,
        "signal_period": 2
    },
    "bollinger": {
        "period": 3,
        "std_dev": 2
    },
    "adx": {
        "period": 2,
        "threshold": 20
    },
    "stochastic": {
        "k_period": 2,
        "d_period": 2,
        "slow_d_period": 2
    },
    "atr": {
        "period": 2
    }
}
```

## Funzionalità Avanzate

### Entrata Scalare Intelligente
- Apertura iniziale di 3 operazioni
- Aggiunta di 4 nuove operazioni quando il prezzo si muove di 15 pips
- Gestione fino a 20 operazioni contemporanee
- Incremento automatico del lotto ogni 4 operazioni

### Stop Loss e Take Profit Adattivi
- Basati sull'Average True Range (ATR)
- Adattamento automatico alla volatilità del mercato
- Tre modalità: calma, normale, volatile
- Moltiplicatori configurabili per SL e TP

### Trailing Stop
- Attivazione automatica a 30 pips di profitto
- Protezione dei guadagni in tempo reale
- Aggiornamento dinamico dello stop loss
- Gestione separata per posizioni long e short

### Verifica Spread
- Controllo dello spread prima di ogni operazione
- Limite massimo configurabile
- Attesa automatica per spread elevati
- Protezione da costi di transazione eccessivi

### Gestione del Rischio
- Protezione del margine libero
- Chiusura al raggiungimento del target di profitto
- Gestione del drawdown massimo
- Limite di rischio per operazione

### Gestione Posizioni Stagnanti
- Chiusura automatica dopo 50 minuti
- Monitoraggio del tempo di apertura
- Prevenzione blocco capitale
- Log dettagliato delle chiusure

### Sistema di Logging
- journal.log: registra tutte le operazioni di trading
- error.log: registra tutti gli errori del sistema
- Rotazione automatica dei file di log
- Visualizzazione ultimo log nell'interfaccia

### Interfaccia Utente
- Display in tempo reale senza scrolling
- Sezioni dedicate per ogni tipo di informazione
- Indicatori colorati per stato sistema
- Visualizzazione errori in-place

## Avvio

1. Assicurarsi che MetaTrader 5 sia in esecuzione
2. Eseguire `run_bot.bat`
3. Il sistema verificherà automaticamente la configurazione
4. Monitorare l'interfaccia per stato e operazioni

## Note
- Il bot utilizza un'interfaccia colorata per una migliore visualizzazione
- Gli errori vengono mostrati in rosso con pausa di sistema
- Il sistema si riprende automaticamente da errori non critici
- Tutti i parametri sono validati all'avvio
- I log vengono salvati nella cartella logs/
- Le operazioni vengono aperte solo con spread accettabile
- Il trailing stop protegge automaticamente i profitti
- Le posizioni stagnanti vengono chiuse automaticamente
- Il sistema adatta SL e TP alla volatilità del mercato

## Guida Dettagliata ai Parametri

### Trading Base
- **symbol**: Strumento finanziario da tradare (es. XAUUSD per oro)
- **timeframe**: Intervallo temporale per l'analisi (M1 = 1 minuto)
- **initial_trades**: Numero di operazioni aperte all'inizio (3 operazioni)
- **max_concurrent_trades**: Limite massimo di operazioni contemporanee (20)
- **pip_step_for_new_trades**: Distanza in pips per aprire nuove operazioni (15)
- **trades_per_step**: Numero di nuove operazioni per ogni step di prezzo (4)
- **max_loss**: Perdita massima consentita in dollari (100)

### Gestione Lotti
- **initial**: Dimensione del lotto iniziale (0.01)
- **increment**: Quanto aumenta il lotto (0.01)
- **increment_every**: Frequenza di incremento del lotto (ogni 4 operazioni)

### Controllo Spread
- **max_spread_points**: Spread massimo accettabile in punti (20)
- **enabled**: Attiva/disattiva il controllo dello spread

### Trailing Stop
- **enabled**: Attiva/disattiva il trailing stop
- **pips**: Distanza del trailing stop dal prezzo (30 pips)

### Gestione Operazioni Stagnanti
- **max_minutes**: Tempo massimo di vita di un'operazione (50 minuti)
- **enabled**: Attiva/disattiva la chiusura automatica

### Gestione Posizioni
- **min_pips_between_orders**: Distanza minima tra ordini successivi (15 pips)
- **floating_profit_close**: Chiusura al raggiungimento del profitto target (2%)
- **hedge_protection**: Protezione da operazioni opposte

### Gestione Rischio
- **min_free_margin**: Margine libero minimo richiesto (50$)
- **max_drawdown_percentage**: Massima perdita accettabile sul capitale (15%)
- **max_risk_per_trade**: Rischio massimo per singola operazione (1%)

### Stop Loss e Take Profit Adattivi
- **atr_periods**: Periodi per il calcolo dell'ATR (2)
- **sl_multiplier**: Moltiplicatore ATR per Stop Loss (1.5)
- **tp_multiplier**: Moltiplicatore ATR per Take Profit (2.0)

#### Condizioni di Mercato
- Calmo: SL=30 pips, TP=40 pips
- Normale: SL=45 pips, TP=60 pips
- Volatile: SL=75 pips, TP=100 pips

### Indicatori Tecnici
- **RSI**: Periodo=2, Ipervenduto=15, Ipercomprato=85
- **MACD**: Veloce=2, Lento=4, Segnale=2
- **Bollinger**: Periodo=3, Deviazioni Standard=2
- **ADX**: Periodo=2, Soglia=20
- **Stocastico**: K=2, D=2, Slow D=2
- **ATR**: Periodo=2

### Impostazioni Strumenti
#### XAUUSD (Oro)
- **pip_value**: 0.1 (1 pip = 0.1)
- **pip_multiplier**: 10
- **profit_multiplier**: 100 (1 punto = $1 con lotto 0.01)

#### EURUSD
- **pip_value**: 0.0001 (1 pip = 0.0001)
- **pip_multiplier**: 10000
- **profit_multiplier**: 100000 (1 pip = $10 con lotto 0.1)

### Note sui Parametri
1. I periodi degli indicatori sono molto corti per lo scalping
2. Il sistema usa una strategia di entrata scalare aggressiva
3. La gestione del rischio è conservativa (max 1% per trade)
4. Gli SL/TP si adattano automaticamente alla volatilità
5. Il trailing stop protegge i profitti dopo 30 pips
6. Le operazioni vengono chiuse dopo 50 minuti se stagnanti
7. Il sistema è ottimizzato per trading su oro (XAUUSD)
