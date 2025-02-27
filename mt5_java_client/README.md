# MT5 Java Client

Client Java per il sistema MT5 Trading Bot. Questo client fornisce un'interfaccia Java per interagire con il sistema MT5 Trading Bot.

## Struttura del progetto

```
mt5_java_client/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/
│   │   │       └── mt5bot/
│   │   │           ├── client/           # Client MT5 per l'esecuzione dei comandi
│   │   │           └── trading/          # Componenti di trading
│   │   │               ├── event/        # Sistema di eventi
│   │   │               ├── manager/      # Manager per le posizioni e altri aspetti
│   │   │               ├── model/        # Modelli di dati
│   │   │               ├── risk/         # Componenti di risk management
│   │   │               └── strategy/     # Strategie di trading
│   │   └── resources/                    # Risorse (configurazioni, ecc.)
│   └── test/
│       └── java/
│           └── com/
│               └── mt5bot/
│                   ├── client/           # Test per il client MT5
│                   └── trading/          # Test per i componenti di trading
│                       └── risk/         # Test per i componenti di risk management
└── pom.xml                               # Configurazione Maven
```

## Componenti principali

### Client MT5

Il client MT5 fornisce un'interfaccia per interagire con il sistema MT5 Trading Bot. I componenti principali sono:

- `MT5Commands`: Interfaccia per l'esecuzione dei comandi MT5
- `CommandExecutor`: Esecutore di comandi
- `ProcessBuilderCommandExecutor`: Implementazione dell'esecutore di comandi basata su ProcessBuilder

### Sistema di eventi

Il sistema di eventi fornisce un meccanismo per la notifica degli eventi di trading. I componenti principali sono:

- `TradingEvent`: Evento di trading
- `TradingEventListener`: Listener per gli eventi di trading
- `TradingEventManager`: Gestore degli eventi di trading

### Componenti di trading

I componenti di trading forniscono funzionalità per il trading. I componenti principali sono:

- `Position`: Modello di una posizione di trading
- `PositionManager`: Gestore delle posizioni
- `TrailingManager`: Gestore del trailing stop
- `VolatilityManager`: Gestore della volatilità

### Componenti di risk management

I componenti di risk management forniscono funzionalità per il risk management. I componenti principali sono:

- `RiskManager`: Gestore del risk management
- `RiskHandler`: Handler per il risk management
- `StagnantPositionHandler`: Handler per le posizioni stagnanti
- `ProfitTargetHandler`: Handler per il target di profitto
- `MarginProtector`: Protettore del margine

## Utilizzo

### Compilazione

```bash
mvn clean compile
```

### Esecuzione dei test

```bash
mvn test
```

### Creazione del JAR

```bash
mvn package
```

### Esecuzione del JAR

```bash
java -jar target/mt5-java-client-1.0-SNAPSHOT-jar-with-dependencies.jar
```

## Esempi

### Utilizzo del client MT5

```java
// Crea un esecutore di comandi
CommandExecutor executor = new ProcessBuilderCommandExecutor();

// Crea un client MT5
MT5Commands mt5Commands = new MT5Commands(executor);

// Ottieni le informazioni sull'account
Map<String, Object> accountInfo = mt5Commands.getAccountInfo();

// Ottieni le posizioni aperte
Map<String, Object> positions = mt5Commands.getPositions(null);

// Apri una posizione
Map<String, Object> result = mt5Commands.marketBuy("EURUSD", 0.1, 1.1950, 1.2050, "Test", 12345);
```

### Utilizzo del sistema di risk management

```java
// Crea un gestore degli eventi di trading
TradingEventManager eventManager = new TradingEventManager();

// Crea un client MT5
MT5Commands mt5Commands = new MT5Commands(executor);

// Crea un gestore del risk management
RiskManager riskManager = new DefaultRiskManager(mt5Commands, eventManager);

// Crea gli handler per il risk management
StagnantPositionHandler stagnantPositionHandler = new StagnantPositionHandler(mt5Commands, eventManager);
ProfitTargetHandler profitTargetHandler = new ProfitTargetHandler(mt5Commands, eventManager);
MarginProtector marginProtector = new MarginProtector(mt5Commands, eventManager);

// Configura gli handler
stagnantPositionHandler.setMaxInactiveMinutes(50);
stagnantPositionHandler.setMinProfitPips(5.0);
stagnantPositionHandler.setCheckIntervalSeconds(60);

profitTargetHandler.setProfitTargetPercent(2.0);
profitTargetHandler.setCheckIntervalSeconds(30);

marginProtector.setMinFreeMargin(50.0);
marginProtector.setCriticalMarginLevel(150.0);
marginProtector.setWarningMarginLevel(200.0);
marginProtector.setCheckIntervalSeconds(10);

// Aggiungi gli handler al gestore del risk management
riskManager.addRiskHandler(stagnantPositionHandler);
riskManager.addRiskHandler(profitTargetHandler);
riskManager.addRiskHandler(marginProtector);

// Avvia il monitoraggio del risk management
riskManager.startMonitoring();

// Verifica se è possibile aprire una posizione
boolean canOpen = riskManager.canOpenPosition("EURUSD", 0.1, 1.1950, 1.2050);

// Esegui il risk management
riskManager.executeRiskManagement();

// Ferma il monitoraggio del risk management
riskManager.stopMonitoring();
```

## Licenza

Questo progetto è rilasciato sotto licenza MIT.
