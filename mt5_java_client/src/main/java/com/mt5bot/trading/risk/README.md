# MT5 Risk Management Components

Questo pacchetto contiene i componenti Java per il risk management del sistema MT5 Trading Bot. I componenti sono progettati per lavorare insieme al sistema MT5 Trading Bot e forniscono funzionalità avanzate per il risk management.

## Componenti principali

### 1. RiskManager

Interfaccia principale per il risk management che definisce le regole di risk management e i metodi per la validazione degli ordini:
- Verifica margine libero (minimo $50)
- Controllo spread (massimo 20 punti)
- Validazione nuovi ordini contro policy
- Gestione degli handler di risk management

```java
// Esempio di utilizzo
RiskManager riskManager = new DefaultRiskManager(mt5Commands, eventManager);
riskManager.addRiskHandler(stagnantPositionHandler);
riskManager.addRiskHandler(profitTargetHandler);
riskManager.addRiskHandler(marginProtector);
riskManager.startMonitoring();

// Verifica se è possibile aprire una nuova posizione
boolean canOpen = riskManager.canOpenPosition("EURUSD", 0.1, 1.1950, 1.2050);
```

### 2. StagnantPositionHandler

Handler per il monitoraggio e la chiusura automatica delle posizioni stagnanti:
- Monitoraggio durata posizioni aperte
- Chiusura automatica dopo 50 minuti inattivi
- Criteri per identificare posizioni stagnanti
- Scheduler per verifica periodica

```java
// Esempio di utilizzo
StagnantPositionHandler stagnantPositionHandler = new StagnantPositionHandler(mt5Commands, eventManager);
stagnantPositionHandler.setMaxInactiveMinutes(50);
stagnantPositionHandler.setMinProfitPips(5.0);
stagnantPositionHandler.setCheckIntervalSeconds(60);
stagnantPositionHandler.startMonitoring();
```

### 3. ProfitTargetHandler

Handler per il monitoraggio del profitto flottante totale:
- Monitoraggio profitto flottante totale
- Trigger chiusura globale al 2% del saldo iniziale
- Prioritizzazione chiusura posizioni
- Gestione esecuzione chiusura completa

```java
// Esempio di utilizzo
ProfitTargetHandler profitTargetHandler = new ProfitTargetHandler(mt5Commands, eventManager);
profitTargetHandler.setProfitTargetPercent(2.0);
profitTargetHandler.setCheckIntervalSeconds(30);
profitTargetHandler.startMonitoring();
```

### 4. MarginProtector

Handler per il monitoraggio del livello di margine:
- Monitoraggio continuo livello margine
- Trigger protezione con chiusura parziale
- Politica di selezione posizioni da chiudere
- System safe-state management

```java
// Esempio di utilizzo
MarginProtector marginProtector = new MarginProtector(mt5Commands, eventManager);
marginProtector.setMinFreeMargin(50.0);
marginProtector.setCriticalMarginLevel(150.0);
marginProtector.setWarningMarginLevel(200.0);
marginProtector.setCheckIntervalSeconds(10);
marginProtector.startMonitoring();
```

## Sistema di priorità per regole conflittuali

Il sistema di risk management utilizza un sistema di priorità per gestire le regole conflittuali. Gli handler con priorità più alta vengono eseguiti prima:

```java
public enum Priority {
    HIGHEST(100),
    HIGH(75),
    MEDIUM(50),
    LOW(25),
    LOWEST(0);
}
```

## Meccanismo thread-safe notification

Il sistema di risk management utilizza un meccanismo thread-safe per la notifica degli eventi:

```java
// Implementazione di un listener
public class MyListener implements TradingEventListener {
    @Override
    public void onTradingEvent(TradingEvent event) {
        System.out.println("Evento ricevuto: " + event);
    }
}

// Registrazione del listener
TradingEventManager eventManager = new TradingEventManager();
eventManager.addListener(new MyListener());
```

## Configurabilità completa soglie

Tutti i componenti sono altamente configurabili tramite metodi setter:

```java
// Esempio di configurazione
stagnantPositionHandler.setMaxInactiveMinutes(50);
stagnantPositionHandler.setMinProfitPips(5.0);
stagnantPositionHandler.setCheckIntervalSeconds(60);

profitTargetHandler.setProfitTargetPercent(2.0);
profitTargetHandler.setCheckIntervalSeconds(30);

marginProtector.setMinFreeMargin(50.0);
marginProtector.setCriticalMarginLevel(150.0);
marginProtector.setWarningMarginLevel(200.0);
marginProtector.setCheckIntervalSeconds(10);

riskManager.setMinFreeMargin(50.0);
riskManager.setMaxSpreadPoints(20);
riskManager.setMonitoringIntervalSeconds(30);
```

## Logging dettagliato decisioni

Il sistema di risk management utilizza un sistema di logging dettagliato per tracciare le decisioni:

```java
LOGGER.log(Level.INFO, "Esecuzione dell'handler {0}", getName());
LOGGER.log(Level.WARNING, "Apertura posizione non permessa: margine libero insufficiente {0} < {1}", 
        new Object[]{freeMargin, minFreeMargin});
LOGGER.log(Level.SEVERE, "Errore durante l'esecuzione dell'handler " + handler.getName(), e);
```

## Pattern Strategy per policy selezionabili

Il sistema di risk management utilizza il pattern Strategy per le policy selezionabili:

```java
// Aggiunta di un handler al risk manager
riskManager.addRiskHandler(stagnantPositionHandler);
riskManager.addRiskHandler(profitTargetHandler);
riskManager.addRiskHandler(marginProtector);

// Rimozione di un handler dal risk manager
riskManager.removeRiskHandler(stagnantPositionHandler);
```

## Test

La classe `RiskManagementTest` fornisce un esempio completo di utilizzo dei componenti con un'implementazione mock di MT5Commands per i test.

Per eseguire il test:

```bash
cd mt5_java_client
.\run_risk_test.bat
```

## Thread-safety

Tutti i componenti sono thread-safe e possono essere utilizzati in ambienti multi-thread. In particolare:
- `DefaultRiskManager` utilizza `CopyOnWriteArrayList` per la gestione degli handler
- `StagnantPositionHandler`, `ProfitTargetHandler` e `MarginProtector` utilizzano `ScheduledExecutorService` per l'aggiornamento periodico
- `TradingEventManager` utilizza `CopyOnWriteArrayList` per la gestione dei listener
