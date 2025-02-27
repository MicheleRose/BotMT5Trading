package main.java.com.mt5bot.trading;

import com.mt5bot.client.CommandExecutor;
import com.mt5bot.client.MT5Commands;
import com.mt5bot.client.MT5Configuration;
import com.mt5bot.client.ProcessBuilderCommandExecutor;
import com.mt5bot.trading.event.TradingEventManager;
import com.mt5bot.trading.manager.PositionManager;
import com.mt5bot.trading.risk.DefaultRiskManager;
import com.mt5bot.trading.risk.MarginProtector;
import com.mt5bot.trading.risk.ProfitTargetHandler;
import com.mt5bot.trading.risk.RiskManager;
import com.mt5bot.trading.risk.StagnantPositionHandler;
import com.mt5bot.trading.service.IndicatorService;
import com.mt5bot.trading.service.MarketDataService;
import com.mt5bot.trading.service.SchedulerService;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;
import java.util.Properties;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.logging.Level;
import java.util.logging.LogManager;
import java.util.logging.Logger;

/**
 * Classe principale del trading bot.
 * Gestisce l'inizializzazione dei componenti e il ciclo principale di trading.
 */
public class TradingBot {
    
    private static final Logger LOGGER = Logger.getLogger(TradingBot.class.getName());
    
    // Componenti principali
    private final MT5Commands mt5Commands;
    private final TradingEventManager eventManager;
    private final RiskManager riskManager;
    private final PositionManager positionManager;
    private final MarketDataService marketDataService;
    private final IndicatorService indicatorService;
    private final SchedulerService schedulerService;
    
    // Configurazione
    private final Properties config;
    
    // Stato del bot
    private final AtomicBoolean running = new AtomicBoolean(false);
    private final CountDownLatch shutdownLatch = new CountDownLatch(1);
    
    /**
     * Costruttore privato per il pattern singleton.
     * 
     * @param configPath Il percorso del file di configurazione
     * @throws IOException Se si verifica un errore durante la lettura del file di configurazione
     */
    private TradingBot(String configPath) throws IOException {
        // Carica la configurazione
        this.config = loadConfiguration(configPath);
        
        // Inizializza i componenti
        CommandExecutor executor = new ProcessBuilderCommandExecutor();
        this.mt5Commands = new MT5Commands(executor);
        this.eventManager = new TradingEventManager();
        
        // Inizializza i servizi
        this.marketDataService = MarketDataService.getInstance(mt5Commands, config);
        this.indicatorService = IndicatorService.getInstance(marketDataService, config);
        this.schedulerService = SchedulerService.getInstance(config);
        
        // Inizializza i manager
        this.riskManager = initializeRiskManager();
        this.positionManager = new PositionManager(mt5Commands, eventManager, riskManager);
        
        // Registra gli shutdown hook
        registerShutdownHook();
    }
    
    /**
     * Istanza singleton del trading bot.
     */
    private static TradingBot instance;
    
    /**
     * Ottiene l'istanza singleton del trading bot.
     * 
     * @param configPath Il percorso del file di configurazione
     * @return L'istanza singleton del trading bot
     * @throws IOException Se si verifica un errore durante la lettura del file di configurazione
     */
    public static synchronized TradingBot getInstance(String configPath) throws IOException {
        if (instance == null) {
            instance = new TradingBot(configPath);
        }
        return instance;
    }
    
    /**
     * Carica la configurazione dal file.
     * 
     * @param configPath Il percorso del file di configurazione
     * @return Le proprietà di configurazione
     * @throws IOException Se si verifica un errore durante la lettura del file di configurazione
     */
    private Properties loadConfiguration(String configPath) throws IOException {
        Properties config = new Properties();
        Path path = Paths.get(configPath);
        
        if (Files.exists(path)) {
            config.load(Files.newInputStream(path));
            LOGGER.info("Configurazione caricata da: " + configPath);
        } else {
            LOGGER.warning("File di configurazione non trovato: " + configPath + ". Utilizzo configurazione predefinita.");
            // Carica la configurazione predefinita
            config.load(TradingBot.class.getResourceAsStream("/trading_bot.properties"));
        }
        
        return config;
    }
    
    /**
     * Inizializza il gestore del risk management.
     * 
     * @return Il gestore del risk management
     */
    private RiskManager initializeRiskManager() {
        DefaultRiskManager riskManager = new DefaultRiskManager(mt5Commands, eventManager);
        
        // Crea gli handler per il risk management
        StagnantPositionHandler stagnantPositionHandler = new StagnantPositionHandler(mt5Commands, eventManager);
        ProfitTargetHandler profitTargetHandler = new ProfitTargetHandler(mt5Commands, eventManager);
        MarginProtector marginProtector = new MarginProtector(mt5Commands, eventManager);
        
        // Configura gli handler
        stagnantPositionHandler.setMaxInactiveMinutes(
                Long.parseLong(config.getProperty("risk.stagnant.maxInactiveMinutes", "50")));
        stagnantPositionHandler.setMinProfitPips(
                Double.parseDouble(config.getProperty("risk.stagnant.minProfitPips", "5.0")));
        stagnantPositionHandler.setCheckIntervalSeconds(
                Long.parseLong(config.getProperty("risk.stagnant.checkIntervalSeconds", "60")));
        
        profitTargetHandler.setProfitTargetPercent(
                Double.parseDouble(config.getProperty("risk.profitTarget.profitTargetPercent", "2.0")));
        profitTargetHandler.setCheckIntervalSeconds(
                Long.parseLong(config.getProperty("risk.profitTarget.checkIntervalSeconds", "30")));
        
        marginProtector.setMinFreeMargin(
                Double.parseDouble(config.getProperty("risk.margin.minFreeMargin", "50.0")));
        marginProtector.setCriticalMarginLevel(
                Double.parseDouble(config.getProperty("risk.margin.criticalMarginLevel", "150.0")));
        marginProtector.setWarningMarginLevel(
                Double.parseDouble(config.getProperty("risk.margin.warningMarginLevel", "200.0")));
        marginProtector.setCheckIntervalSeconds(
                Long.parseLong(config.getProperty("risk.margin.checkIntervalSeconds", "10")));
        
        // Aggiungi gli handler al gestore del risk management
        riskManager.addRiskHandler(stagnantPositionHandler);
        riskManager.addRiskHandler(profitTargetHandler);
        riskManager.addRiskHandler(marginProtector);
        
        return riskManager;
    }
    
    /**
     * Registra gli shutdown hook per la chiusura graceful.
     */
    private void registerShutdownHook() {
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            LOGGER.info("Shutdown hook attivato. Arresto del trading bot...");
            stop();
            try {
                // Attendi che il bot si fermi
                shutdownLatch.await();
                LOGGER.info("Trading bot arrestato con successo.");
            } catch (InterruptedException e) {
                LOGGER.log(Level.SEVERE, "Errore durante l'attesa dell'arresto del trading bot", e);
                Thread.currentThread().interrupt();
            }
        }));
    }
    
    /**
     * Avvia il trading bot.
     */
    public void start() {
        if (running.compareAndSet(false, true)) {
            LOGGER.info("Avvio del trading bot...");
            
            try {
                // Verifica la connessione a MT5
                Map<String, Object> accountInfo = mt5Commands.getAccountInfo();
                LOGGER.info("Connessione a MT5 stabilita. Account: " + accountInfo);
                
                // Avvia i servizi
                marketDataService.start();
                indicatorService.start();
                schedulerService.start();
                
                // Avvia il monitoraggio del risk management
                riskManager.startMonitoring();
                
                // Avvia il ciclo principale di trading
                startTradingLoop();
                
                LOGGER.info("Trading bot avviato con successo.");
            } catch (Exception e) {
                LOGGER.log(Level.SEVERE, "Errore durante l'avvio del trading bot", e);
                stop();
            }
        } else {
            LOGGER.warning("Il trading bot è già in esecuzione.");
        }
    }
    
    /**
     * Avvia il ciclo principale di trading.
     */
    private void startTradingLoop() {
        // Avvia il ciclo principale di trading in un thread separato
        Thread tradingThread = new Thread(() -> {
            LOGGER.info("Ciclo principale di trading avviato.");
            
            while (running.get()) {
                try {
                    // Esegui la strategia di trading
                    executeStrategy();
                    
                    // Attendi il prossimo ciclo
                    Thread.sleep(Long.parseLong(config.getProperty("trading.loopIntervalMs", "1000")));
                } catch (InterruptedException e) {
                    LOGGER.log(Level.WARNING, "Ciclo principale di trading interrotto", e);
                    Thread.currentThread().interrupt();
                    break;
                } catch (Exception e) {
                    LOGGER.log(Level.SEVERE, "Errore durante l'esecuzione della strategia di trading", e);
                }
            }
            
            LOGGER.info("Ciclo principale di trading terminato.");
        });
        
        tradingThread.setName("TradingLoop");
        tradingThread.setDaemon(true);
        tradingThread.start();
    }
    
    /**
     * Esegue la strategia di trading.
     */
    private void executeStrategy() {
        try {
            // Ottieni i dati di mercato aggiornati
            Map<String, Object> marketData = marketDataService.getMarketData(
                    config.getProperty("trading.symbol", "EURUSD"));
            
            // Calcola gli indicatori
            Map<String, Object> indicators = indicatorService.calculateIndicators(
                    config.getProperty("trading.symbol", "EURUSD"));
            
            // Verifica le condizioni di ingresso
            if (checkEntryConditions(indicators)) {
                // Apri una posizione
                openPosition();
            }
            
            // Verifica le condizioni di uscita
            if (checkExitConditions(indicators)) {
                // Chiudi le posizioni
                closePositions();
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante l'esecuzione della strategia di trading", e);
        }
    }
    
    /**
     * Verifica le condizioni di ingresso.
     * 
     * @param indicators Gli indicatori tecnici
     * @return true se le condizioni di ingresso sono soddisfatte, false altrimenti
     */
    private boolean checkEntryConditions(Map<String, Object> indicators) {
        // Implementazione delle condizioni di ingresso
        // RSI(2): 15/85
        double rsi = (double) indicators.get("RSI");
        if (rsi < 15 || rsi > 85) {
            LOGGER.info("Condizione di ingresso RSI soddisfatta: " + rsi);
            return true;
        }
        
        // MACD(2,4,2)
        double macd = (double) indicators.get("MACD");
        double signal = (double) indicators.get("MACD_SIGNAL");
        if (macd > signal) {
            LOGGER.info("Condizione di ingresso MACD soddisfatta: " + macd + " > " + signal);
            return true;
        }
        
        // Bollinger(3,2)
        double price = (double) indicators.get("PRICE");
        double upperBand = (double) indicators.get("BOLL_UPPER");
        double lowerBand = (double) indicators.get("BOLL_LOWER");
        if (price > upperBand || price < lowerBand) {
            LOGGER.info("Condizione di ingresso Bollinger soddisfatta: " + price + " fuori dalle bande " + lowerBand + " - " + upperBand);
            return true;
        }
        
        // ADX(2): 20
        double adx = (double) indicators.get("ADX");
        if (adx > 20) {
            LOGGER.info("Condizione di ingresso ADX soddisfatta: " + adx);
            return true;
        }
        
        // Stocastico(2,2,2)
        double k = (double) indicators.get("STOCH_K");
        double d = (double) indicators.get("STOCH_D");
        if (k > d) {
            LOGGER.info("Condizione di ingresso Stocastico soddisfatta: " + k + " > " + d);
            return true;
        }
        
        return false;
    }
    
    /**
     * Verifica le condizioni di uscita.
     * 
     * @param indicators Gli indicatori tecnici
     * @return true se le condizioni di uscita sono soddisfatte, false altrimenti
     */
    private boolean checkExitConditions(Map<String, Object> indicators) {
        // Implementazione delle condizioni di uscita
        // RSI(2): 50
        double rsi = (double) indicators.get("RSI");
        if (rsi > 45 && rsi < 55) {
            LOGGER.info("Condizione di uscita RSI soddisfatta: " + rsi);
            return true;
        }
        
        // MACD(2,4,2)
        double macd = (double) indicators.get("MACD");
        double signal = (double) indicators.get("MACD_SIGNAL");
        if (macd < signal) {
            LOGGER.info("Condizione di uscita MACD soddisfatta: " + macd + " < " + signal);
            return true;
        }
        
        // Bollinger(3,2)
        double price = (double) indicators.get("PRICE");
        double middleBand = (double) indicators.get("BOLL_MIDDLE");
        if (Math.abs(price - middleBand) < 0.0010) {
            LOGGER.info("Condizione di uscita Bollinger soddisfatta: " + price + " vicino alla banda media " + middleBand);
            return true;
        }
        
        // ADX(2): 15
        double adx = (double) indicators.get("ADX");
        if (adx < 15) {
            LOGGER.info("Condizione di uscita ADX soddisfatta: " + adx);
            return true;
        }
        
        // Stocastico(2,2,2)
        double k = (double) indicators.get("STOCH_K");
        double d = (double) indicators.get("STOCH_D");
        if (k < d) {
            LOGGER.info("Condizione di uscita Stocastico soddisfatta: " + k + " < " + d);
            return true;
        }
        
        return false;
    }
    
    /**
     * Apre una posizione.
     */
    private void openPosition() {
        try {
            String symbol = config.getProperty("trading.symbol", "EURUSD");
            double volume = Double.parseDouble(config.getProperty("trading.volume", "0.1"));
            double stopLoss = Double.parseDouble(config.getProperty("trading.stopLoss", "0.0"));
            double takeProfit = Double.parseDouble(config.getProperty("trading.takeProfit", "0.0"));
            
            // Verifica se è possibile aprire una posizione
            if (riskManager.canOpenPosition(symbol, volume, stopLoss, takeProfit)) {
                // Apri una posizione
                Map<String, Object> result = mt5Commands.marketBuy(symbol, volume, stopLoss, takeProfit, "TradingBot", 12345);
                
                if (result.containsKey("success") && (Boolean) result.get("success")) {
                    LOGGER.info("Posizione aperta: " + result);
                } else {
                    LOGGER.warning("Errore durante l'apertura della posizione: " + result);
                }
            } else {
                LOGGER.warning("Apertura posizione non permessa dal risk manager");
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante l'apertura della posizione", e);
        }
    }
    
    /**
     * Chiude le posizioni.
     */
    private void closePositions() {
        try {
            // Ottieni le posizioni aperte
            Map<String, Object> result = mt5Commands.getPositions(null);
            
            if (result.containsKey("positions")) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> positions = (List<Map<String, Object>>) result.get("positions");
                
                for (Map<String, Object> position : positions) {
                    long ticket = ((Number) position.get("ticket")).longValue();
                    
                    // Chiudi la posizione
                    Map<String, Object> closeResult = mt5Commands.closePosition(ticket, null);
                    
                    if (closeResult.containsKey("success") && (Boolean) closeResult.get("success")) {
                        LOGGER.info("Posizione chiusa: " + ticket);
                    } else {
                        LOGGER.warning("Errore durante la chiusura della posizione: " + ticket);
                    }
                }
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante la chiusura delle posizioni", e);
        }
    }
    
    /**
     * Ferma il trading bot.
     */
    public void stop() {
        if (running.compareAndSet(true, false)) {
            LOGGER.info("Arresto del trading bot...");
            
            try {
                // Ferma i servizi
                schedulerService.stop();
                indicatorService.stop();
                marketDataService.stop();
                
                // Ferma il monitoraggio del risk management
                riskManager.stopMonitoring();
                
                LOGGER.info("Trading bot arrestato con successo.");
            } catch (Exception e) {
                LOGGER.log(Level.SEVERE, "Errore durante l'arresto del trading bot", e);
            } finally {
                // Segnala che il bot è stato arrestato
                shutdownLatch.countDown();
            }
        } else {
            LOGGER.warning("Il trading bot non è in esecuzione.");
        }
    }
    
    /**
     * Metodo principale.
     * 
     * @param args Gli argomenti della linea di comando
     */
    public static void main(String[] args) {
        try {
            // Configura il logging
            LogManager.getLogManager().readConfiguration(
                    TradingBot.class.getResourceAsStream("/logging.properties"));
            
            // Ottieni il percorso del file di configurazione
            String configPath = args.length > 0 ? args[0] : "config/trading_bot.properties";
            
            // Crea e avvia il trading bot
            TradingBot bot = TradingBot.getInstance(configPath);
            bot.start();
            
            // Attendi l'arresto del bot
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                LOGGER.info("Arresto del trading bot...");
                bot.stop();
            }));
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante l'avvio del trading bot", e);
        }
    }
}
