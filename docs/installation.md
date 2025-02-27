# Guida all'Installazione del MT5 Trading Bot

Questa guida fornisce istruzioni dettagliate per l'installazione e la configurazione del MT5 Trading Bot.

## Requisiti Software

Prima di iniziare l'installazione, assicurati di avere i seguenti requisiti software:

### Requisiti Obbligatori

- **MetaTrader 5** (versione 5.0.0 o superiore)
- **Python** (versione 3.8 o superiore)
- **Java Development Kit (JDK)** (versione 11 o superiore)
- **Maven** (versione 3.6 o superiore)

### Requisiti Opzionali

- **Git** (per il controllo versione)
- **Visual Studio Code** o altro IDE (per lo sviluppo)

## Procedura di Setup Iniziale

Segui questi passaggi per configurare il MT5 Trading Bot:

### 1. Installazione di MetaTrader 5

1. Scarica MetaTrader 5 dal [sito ufficiale](https://www.metatrader5.com/en/download).
2. Esegui il file di installazione e segui le istruzioni a schermo.
3. Avvia MetaTrader 5 e accedi al tuo account di trading.

### 2. Installazione di Python e Dipendenze

1. Scarica Python dal [sito ufficiale](https://www.python.org/downloads/).
2. Durante l'installazione, assicurati di selezionare l'opzione "Add Python to PATH".
3. Apri un terminale e installa le dipendenze necessarie:

```bash
pip install MetaTrader5 pandas numpy matplotlib
```

### 3. Installazione di Java e Maven

1. Scarica JDK dal [sito ufficiale di Oracle](https://www.oracle.com/java/technologies/javase-jdk11-downloads.html) o usa OpenJDK.
2. Installa JDK seguendo le istruzioni a schermo.
3. Scarica Maven dal [sito ufficiale](https://maven.apache.org/download.cgi).
4. Estrai l'archivio Maven in una directory a tua scelta.
5. Aggiungi la directory `bin` di Maven al PATH di sistema.

### 4. Configurazione delle Variabili di Ambiente

#### Windows

1. Apri il Pannello di Controllo > Sistema > Impostazioni di sistema avanzate > Variabili d'ambiente.
2. Nella sezione "Variabili di sistema", trova la variabile PATH e seleziona "Modifica".
3. Aggiungi i seguenti percorsi (sostituisci con i percorsi effettivi):
   - `C:\Program Files\Java\jdk-11\bin`
   - `C:\path\to\maven\bin`
4. Crea una nuova variabile di sistema chiamata `JAVA_HOME` con il valore `C:\Program Files\Java\jdk-11`.
5. Fai clic su "OK" per salvare le modifiche.

#### macOS/Linux

Aggiungi le seguenti righe al file `~/.bash_profile` o `~/.zshrc`:

```bash
export JAVA_HOME=/path/to/jdk
export PATH=$JAVA_HOME/bin:/path/to/maven/bin:$PATH
```

Riavvia il terminale o esegui `source ~/.bash_profile` (o `source ~/.zshrc`).

### 5. Clonazione del Repository

1. Apri un terminale e naviga nella directory in cui desideri installare il bot.
2. Clona il repository:

```bash
git clone https://github.com/yourusername/mt5-trading-bot.git
cd mt5-trading-bot
```

### 6. Compilazione del Progetto

1. Naviga nella directory del progetto Java:

```bash
cd mt5_java_client
```

2. Compila il progetto con Maven:

```bash
mvn clean package
```

## Configurazione del Bot

### 1. Configurazione di MetaTrader 5

1. Avvia MetaTrader 5.
2. Vai su File > Apri cartella dati.
3. Naviga nella cartella `MQL5\Scripts`.
4. Copia tutti i file Python dalla directory `mt5_trading_system/scripts` del repository nella cartella `Scripts`.

### 2. Configurazione del MT5 Keeper

1. Crea una directory per il MT5 Keeper:

```bash
mkdir -p ~/.mt5bot/commands ~/.mt5bot/results
```

2. Copia il file `mt5_keeper.py` nella directory principale:

```bash
cp mt5_keeper.py ~/.mt5bot/
```

### 3. Configurazione del Trading Bot

1. Copia il file di configurazione di esempio:

```bash
cp mt5_java_client/src/main/resources/trading_bot.properties.example mt5_java_client/src/main/resources/trading_bot.properties
```

2. Modifica il file `trading_bot.properties` con le tue impostazioni:

```properties
# Configurazione generale
trading.symbol=EURUSD
trading.volume=0.1
trading.stopLoss=0.0
trading.takeProfit=0.0
trading.loopIntervalMs=1000

# Configurazione dei dati di mercato
marketData.symbols=EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD
marketData.timeframes=M1,M5,M15,H1
marketData.updateIntervalMs=1000
marketData.ohlcUpdateIntervalMs=60000
marketData.ohlcCount=100
marketData.maxAgeMs=5000

# Configurazione degli indicatori
indicators.symbols=EURUSD,GBPUSD,USDJPY,AUDUSD,USDCAD
indicators.timeframe=M5
indicators.updateIntervalMs=1000

# Configurazione dello scheduler
scheduler.positionMonitoring.intervalMs=5000
scheduler.marketConditionsCheck.intervalMs=10000
scheduler.trailingStopUpdate.intervalMs=2000

# Configurazione del risk management
risk.stagnant.maxInactiveMinutes=50
risk.stagnant.minProfitPips=5.0
risk.stagnant.checkIntervalSeconds=60

risk.profitTarget.profitTargetPercent=2.0
risk.profitTarget.checkIntervalSeconds=30

risk.margin.minFreeMargin=50.0
risk.margin.criticalMarginLevel=150.0
risk.margin.warningMarginLevel=200.0
risk.margin.checkIntervalSeconds=10

# Configurazione delle strategie di trading
strategy.rsi.enabled=true
strategy.rsi.oversold=15
strategy.rsi.overbought=85
strategy.rsi.period=2

strategy.macd.enabled=true
strategy.macd.fastPeriod=2
strategy.macd.slowPeriod=4
strategy.macd.signalPeriod=2

strategy.bollinger.enabled=true
strategy.bollinger.period=3
strategy.bollinger.deviations=2.0

strategy.adx.enabled=true
strategy.adx.period=2
strategy.adx.threshold=20

strategy.stochastic.enabled=true
strategy.stochastic.kPeriod=2
strategy.stochastic.dPeriod=2
strategy.stochastic.slowing=2

# Configurazione del logging
logging.level=INFO
logging.file=logs/trading_bot.log
logging.pattern=%d{yyyy-MM-dd HH:mm:ss} %-5p %c{1}:%L - %m%n
```

## Avvio del Bot

### 1. Avvio del MT5 Keeper

1. Apri un terminale e naviga nella directory del MT5 Keeper:

```bash
cd ~/.mt5bot
```

2. Avvia il MT5 Keeper:

```bash
python mt5_keeper.py
```

### 2. Avvio del Trading Bot

1. Apri un nuovo terminale e naviga nella directory del progetto Java:

```bash
cd mt5_java_client
```

2. Avvia il Trading Bot:

```bash
# Windows
run_trading_bot.bat

# macOS/Linux
./run_trading_bot.sh
```

## Verifica dell'Installazione

Per verificare che l'installazione sia avvenuta con successo:

1. Controlla che il MT5 Keeper sia in esecuzione senza errori.
2. Controlla che il Trading Bot sia in esecuzione senza errori.
3. Esegui i test:

```bash
# Windows
run_tests.bat

# macOS/Linux
./run_tests.sh
```

## Troubleshooting

### Problemi Comuni

#### Il MT5 Keeper non si avvia

- Verifica che Python sia installato correttamente.
- Verifica che la libreria MetaTrader5 sia installata.
- Verifica che MetaTrader 5 sia in esecuzione.
- Verifica che la directory `~/.mt5bot` esista e abbia i permessi corretti.

#### Il Trading Bot non si avvia

- Verifica che Java sia installato correttamente.
- Verifica che Maven sia installato correttamente.
- Verifica che il progetto sia stato compilato con successo.
- Verifica che il file `trading_bot.properties` sia configurato correttamente.

#### Errori di Connessione

- Verifica che MetaTrader 5 sia in esecuzione.
- Verifica che il MT5 Keeper sia in esecuzione.
- Verifica che le porte utilizzate per la comunicazione non siano bloccate dal firewall.

#### Errori di Trading

- Verifica che l'account di trading sia attivo e abbia fondi sufficienti.
- Verifica che i simboli configurati siano disponibili nel tuo account di trading.
- Verifica che le impostazioni di risk management siano appropriate per il tuo account.

## Screenshot di Configurazione

![MetaTrader 5 Setup](images/mt5_setup.png)

*Figura 1: Configurazione di MetaTrader 5*

![Trading Bot Setup](images/trading_bot_setup.png)

*Figura 2: Configurazione del Trading Bot*

## Supporto

Per ulteriori informazioni o supporto, contatta il team di sviluppo all'indirizzo support@mt5tradingbot.com o apri un issue sul repository GitHub.
