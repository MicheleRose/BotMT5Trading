package main.java.com.mt5bot.trading.risk;

import com.mt5bot.client.CommandExecutionException;
import com.mt5bot.client.MT5Commands;
import com.mt5bot.trading.event.StrategyEvent;
import com.mt5bot.trading.event.TradingEvent.EventType;
import com.mt5bot.trading.event.TradingEventManager;
import com.mt5bot.trading.model.Position;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Implementazione predefinita del gestore di risk management.
 * Gestisce tutti gli handler di risk management e implementa le regole di risk management.
 */
public class DefaultRiskManager implements RiskManager {
    
    private static final Logger LOGGER = Logger.getLogger(DefaultRiskManager.class.getName());
    
    private final MT5Commands mt5Commands;
    private final TradingEventManager eventManager;
    
    // Lista degli handler di risk management
    private final List<RiskHandler> handlers = new CopyOnWriteArrayList<>();
    
    // Parametri di configurazione
    private double minFreeMargin = 50.0; // Margine libero minimo in valuta
    private int maxSpreadPoints = 20; // Spread massimo in punti
    private long monitoringIntervalSeconds = 30; // Intervallo di monitoraggio in secondi
    
    // Scheduler per il monitoraggio periodico
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
    private boolean monitoring = false;
    
    /**
     * Costruttore per il gestore di risk management.
     * 
     * @param mt5Commands Il client MT5 per l'esecuzione dei comandi
     * @param eventManager Il gestore degli eventi di trading
     */
    public DefaultRiskManager(MT5Commands mt5Commands, TradingEventManager eventManager) {
        this.mt5Commands = mt5Commands;
        this.eventManager = eventManager;
    }
    
    @Override
    public boolean canOpenPosition(String symbol, double volume, double stopLoss, double takeProfit) throws CommandExecutionException {
        // Ottieni le informazioni sull'account
        Map<String, Object> accountInfo = getAccountInfo();
        
        // Ottieni le posizioni aperte
        List<Position> positions = getPositions();
        
        // Verifica se lo spread è accettabile
        if (!isSpreadAcceptable(symbol)) {
            LOGGER.log(Level.WARNING, "Apertura posizione non permessa: spread non accettabile per {0}", symbol);
            return false;
        }
        
        // Verifica se il margine libero è sufficiente
        if (!isFreeMarginSufficient()) {
            LOGGER.log(Level.WARNING, "Apertura posizione non permessa: margine libero insufficiente");
            return false;
        }
        
        // Verifica se gli handler permettono l'apertura della posizione
        for (RiskHandler handler : getSortedHandlers()) {
            try {
                if (!handler.canOpenPosition(accountInfo, positions, symbol, volume, stopLoss, takeProfit)) {
                    LOGGER.log(Level.WARNING, "Apertura posizione non permessa dall'handler: {0}", handler.getName());
                    return false;
                }
            } catch (Exception e) {
                LOGGER.log(Level.SEVERE, "Errore durante la validazione della nuova posizione nell'handler " + handler.getName(), e);
            }
        }
        
        return true;
    }
    
    @Override
    public boolean shouldClosePositions() throws CommandExecutionException {
        // Ottieni le informazioni sull'account
        Map<String, Object> accountInfo = getAccountInfo();
        
        // Ottieni le posizioni aperte
        List<Position> positions = getPositions();
        
        // Verifica se gli handler richiedono la chiusura delle posizioni
        for (RiskHandler handler : getSortedHandlers()) {
            try {
                if (handler.shouldExecute(accountInfo, positions)) {
                    LOGGER.log(Level.INFO, "Chiusura posizioni richiesta dall'handler: {0}", handler.getName());
                    return true;
                }
            } catch (Exception e) {
                LOGGER.log(Level.SEVERE, "Errore durante la verifica delle condizioni dell'handler " + handler.getName(), e);
            }
        }
        
        return false;
    }
    
    @Override
    public void executeRiskManagement() throws CommandExecutionException {
        // Ottieni le informazioni sull'account
        Map<String, Object> accountInfo = getAccountInfo();
        
        // Ottieni le posizioni aperte
        List<Position> positions = getPositions();
        
        // Esegui gli handler che richiedono l'esecuzione
        for (RiskHandler handler : getSortedHandlers()) {
            try {
                if (handler.shouldExecute(accountInfo, positions)) {
                    LOGGER.log(Level.INFO, "Esecuzione dell'handler: {0}", handler.getName());
                    handler.execute(accountInfo, positions);
                }
            } catch (Exception e) {
                LOGGER.log(Level.SEVERE, "Errore durante l'esecuzione dell'handler " + handler.getName(), e);
            }
        }
    }
    
    @Override
    public boolean isSpreadAcceptable(String symbol) throws CommandExecutionException {
        try {
            Map<String, Object> result = mt5Commands.checkSpread(symbol);
            
            if (result.containsKey("spread")) {
                int spread = ((Number) result.get("spread")).intValue();
                
                if (spread > maxSpreadPoints) {
                    LOGGER.log(Level.WARNING, "Spread non accettabile per {0}: {1} > {2}", 
                            new Object[]{symbol, spread, maxSpreadPoints});
                    return false;
                }
                
                return true;
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante la verifica dello spread", e);
        }
        
        return false;
    }
    
    @Override
    public boolean isFreeMarginSufficient() throws CommandExecutionException {
        try {
            Map<String, Object> accountInfo = getAccountInfo();
            
            if (accountInfo.containsKey("account_info")) {
                @SuppressWarnings("unchecked")
                Map<String, Object> accountInfoData = (Map<String, Object>) accountInfo.get("account_info");
                
                if (accountInfoData.containsKey("margin_free")) {
                    double freeMargin = ((Number) accountInfoData.get("margin_free")).doubleValue();
                    
                    if (freeMargin < minFreeMargin) {
                        LOGGER.log(Level.WARNING, "Margine libero insufficiente: {0} < {1}", 
                                new Object[]{freeMargin, minFreeMargin});
                        return false;
                    }
                    
                    return true;
                }
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante la verifica del margine libero", e);
        }
        
        return false;
    }
    
    @Override
    public Map<String, Object> getAccountInfo() throws CommandExecutionException {
        return mt5Commands.getAccountInfo();
    }
    
    @Override
    public void addRiskHandler(RiskHandler handler) {
        if (handler != null && !handlers.contains(handler)) {
            handlers.add(handler);
            LOGGER.log(Level.INFO, "Handler aggiunto: {0}", handler.getName());
            
            // Avvia il monitoraggio dell'handler se il monitoraggio è attivo
            if (isMonitoring()) {
                handler.startMonitoring();
            }
        }
    }
    
    @Override
    public void removeRiskHandler(RiskHandler handler) {
        if (handler != null) {
            // Ferma il monitoraggio dell'handler
            handler.stopMonitoring();
            
            handlers.remove(handler);
            LOGGER.log(Level.INFO, "Handler rimosso: {0}", handler.getName());
        }
    }
    
    @Override
    public void startMonitoring() {
        if (!monitoring) {
            monitoring = true;
            
            // Avvia il monitoraggio degli handler
            for (RiskHandler handler : handlers) {
                handler.startMonitoring();
            }
            
            // Avvia lo scheduler per il monitoraggio periodico
            scheduler.scheduleAtFixedRate(this::monitorRisk, 0, monitoringIntervalSeconds, TimeUnit.SECONDS);
            
            LOGGER.info("Monitoraggio del risk management avviato");
            
            // Notifica l'evento di avvio del monitoraggio
            eventManager.notifyEvent(new StrategyEvent(
                EventType.RISK_MONITORING_STARTED,
                "ALL",
                "DefaultRiskManager",
                "Monitoraggio del risk management avviato"
            ));
        }
    }
    
    @Override
    public void stopMonitoring() {
        if (monitoring) {
            monitoring = false;
            
            // Ferma il monitoraggio degli handler
            for (RiskHandler handler : handlers) {
                handler.stopMonitoring();
            }
            
            // Ferma lo scheduler
            scheduler.shutdown();
            try {
                if (!scheduler.awaitTermination(5, TimeUnit.SECONDS)) {
                    scheduler.shutdownNow();
                }
            } catch (InterruptedException e) {
                scheduler.shutdownNow();
                Thread.currentThread().interrupt();
            }
            
            LOGGER.info("Monitoraggio del risk management fermato");
            
            // Notifica l'evento di arresto del monitoraggio
            eventManager.notifyEvent(new StrategyEvent(
                EventType.RISK_MONITORING_STOPPED,
                "ALL",
                "DefaultRiskManager",
                "Monitoraggio del risk management fermato"
            ));
        }
    }
    
    @Override
    public boolean isMonitoring() {
        return monitoring;
    }
    
    /**
     * Monitora il risk management.
     */
    private void monitorRisk() {
        try {
            // Esegui il risk management
            executeRiskManagement();
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante il monitoraggio del risk management", e);
        }
    }
    
    /**
     * Ottiene le posizioni aperte.
     * 
     * @return Le posizioni aperte
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    private List<Position> getPositions() throws CommandExecutionException {
        try {
            Map<String, Object> result = mt5Commands.getPositions(null);
            
            if (result.containsKey("positions")) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> positionsList = (List<Map<String, Object>>) result.get("positions");
                
                // Converti le posizioni in oggetti Position
                List<Position> positions = new ArrayList<>();
                for (Map<String, Object> positionData : positionsList) {
                    // Crea la posizione (implementazione semplificata)
                    Position position = Position.fromMap(positionData);
                    positions.add(position);
                }
                
                return positions;
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante l'ottenimento delle posizioni", e);
            throw e;
        }
        
        return Collections.emptyList();
    }
    
    /**
     * Ottiene gli handler ordinati per priorità.
     * 
     * @return Gli handler ordinati per priorità
     */
    private List<RiskHandler> getSortedHandlers() {
        List<RiskHandler> sortedHandlers = new ArrayList<>(handlers);
        sortedHandlers.sort(Comparator.comparing(RiskHandler::getPriority).reversed());
        return sortedHandlers;
    }
    
    /**
     * Imposta il margine libero minimo.
     * 
     * @param minFreeMargin Il margine libero minimo in valuta
     */
    public void setMinFreeMargin(double minFreeMargin) {
        this.minFreeMargin = minFreeMargin;
    }
    
    /**
     * Imposta lo spread massimo in punti.
     * 
     * @param maxSpreadPoints Lo spread massimo in punti
     */
    public void setMaxSpreadPoints(int maxSpreadPoints) {
        this.maxSpreadPoints = maxSpreadPoints;
    }
    
    /**
     * Imposta l'intervallo di monitoraggio.
     * 
     * @param monitoringIntervalSeconds L'intervallo di monitoraggio in secondi
     */
    public void setMonitoringIntervalSeconds(long monitoringIntervalSeconds) {
        this.monitoringIntervalSeconds = monitoringIntervalSeconds;
    }
    
    /**
     * Restituisce il margine libero minimo.
     * 
     * @return Il margine libero minimo in valuta
     */
    public double getMinFreeMargin() {
        return minFreeMargin;
    }
    
    /**
     * Restituisce lo spread massimo in punti.
     * 
     * @return Lo spread massimo in punti
     */
    public int getMaxSpreadPoints() {
        return maxSpreadPoints;
    }
    
    /**
     * Restituisce l'intervallo di monitoraggio.
     * 
     * @return L'intervallo di monitoraggio in secondi
     */
    public long getMonitoringIntervalSeconds() {
        return monitoringIntervalSeconds;
    }
    
    /**
     * Restituisce gli handler di risk management.
     * 
     * @return Gli handler di risk management
     */
    public List<RiskHandler> getHandlers() {
        return new ArrayList<>(handlers);
    }
}
