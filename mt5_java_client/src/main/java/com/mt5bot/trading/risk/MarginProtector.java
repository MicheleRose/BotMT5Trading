package main.java.com.mt5bot.trading.risk;

import main.java.com.mt5bot.client.CommandExecutionException;
import main.java.com.mt5bot.client.MT5Commands;
import main.java.com.mt5bot.trading.event.PositionEvent;
import main.java.com.mt5bot.trading.event.StrategyEvent;
import main.java.com.mt5bot.trading.event.TradingEvent.EventType;
import main.java.com.mt5bot.trading.event.TradingEventManager;
import main.java.com.mt5bot.trading.model.Position;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.stream.Collectors;

/**
 * Handler per il monitoraggio del livello di margine.
 * Implementa il monitoraggio continuo del livello di margine e la protezione
 * con chiusura parziale delle posizioni in caso di livello critico.
 */
public class MarginProtector extends AbstractRiskHandler {
    
    private static final Logger LOGGER = Logger.getLogger(MarginProtector.class.getName());
    
    private final MT5Commands mt5Commands;
    
    // Parametri di configurazione
    private double minFreeMargin = 50.0; // Margine libero minimo in valuta
    private double criticalMarginLevel = 150.0; // Livello di margine critico in percentuale
    private double warningMarginLevel = 200.0; // Livello di margine di avviso in percentuale
    private long checkIntervalSeconds = 10; // Intervallo di verifica in secondi
    
    // Stato del protettore
    private boolean safeStateActive = false;
    
    // Scheduler per la verifica periodica
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
    
    /**
     * Costruttore per il protettore del margine.
     * 
     * @param mt5Commands Il client MT5 per l'esecuzione dei comandi
     * @param eventManager Il gestore degli eventi di trading
     */
    public MarginProtector(MT5Commands mt5Commands, TradingEventManager eventManager) {
        super(eventManager, "MarginProtector", Priority.HIGHEST);
        this.mt5Commands = mt5Commands;
    }
    
    @Override
    public void startMonitoring() {
        super.startMonitoring();
        
        // Avvia lo scheduler per la verifica periodica
        scheduler.scheduleAtFixedRate(this::checkMarginLevel, 0, checkIntervalSeconds, TimeUnit.SECONDS);
        
        LOGGER.info("Monitoraggio del livello di margine avviato");
    }
    
    @Override
    public void stopMonitoring() {
        super.stopMonitoring();
        
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
        
        LOGGER.info("Monitoraggio del livello di margine fermato");
    }
    
    /**
     * Verifica il livello di margine.
     */
    private void checkMarginLevel() {
        try {
            // Ottieni le informazioni sull'account
            Map<String, Object> accountInfo = mt5Commands.getAccountInfo();
            
            // Ottieni le posizioni aperte
            Map<String, Object> result = mt5Commands.getPositions(null);
            
            if (result.containsKey("positions")) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> positionsList = (List<Map<String, Object>>) result.get("positions");
                
                // Converti le posizioni in oggetti Position
                List<Position> positions = new ArrayList<>();
                for (Map<String, Object> positionData : positionsList) {
                    long ticket = ((Number) positionData.get("ticket")).longValue();
                    String symbol = (String) positionData.get("symbol");
                    String typeStr = (String) positionData.get("type");
                    Position.PositionType type = typeStr.equalsIgnoreCase("buy") ? Position.PositionType.BUY : Position.PositionType.SELL;
                    double volume = ((Number) positionData.get("volume")).doubleValue();
                    double openPrice = ((Number) positionData.get("open_price")).doubleValue();
                    double stopLoss = positionData.containsKey("sl") ? ((Number) positionData.get("sl")).doubleValue() : 0.0;
                    double takeProfit = positionData.containsKey("tp") ? ((Number) positionData.get("tp")).doubleValue() : 0.0;
                    String comment = positionData.containsKey("comment") ? (String) positionData.get("comment") : "";
                    int magicNumber = positionData.containsKey("magic") ? ((Number) positionData.get("magic")).intValue() : 0;
                    double currentPrice = ((Number) positionData.get("current_price")).doubleValue();
                    
                    // Crea la posizione
                    Position position = new Position(
                        ticket, symbol, type, volume, openPrice, LocalDateTime.now(),
                        stopLoss, takeProfit, comment, magicNumber
                    );
                    position.updatePrice(currentPrice);
                    
                    positions.add(position);
                }
                
                // Esegui l'handler
                if (shouldExecute(accountInfo, positions)) {
                    execute(accountInfo, positions);
                } else {
                    // Verifica se è necessario disattivare lo stato di sicurezza
                    if (safeStateActive) {
                        double marginLevel = getMarginLevel(accountInfo);
                        
                        if (marginLevel > warningMarginLevel) {
                            safeStateActive = false;
                            
                            LOGGER.log(Level.INFO, "Stato di sicurezza disattivato: livello di margine {0}% > {1}%", 
                                    new Object[]{marginLevel, warningMarginLevel});
                            
                            // Notifica l'evento di disattivazione dello stato di sicurezza
                            eventManager.notifyEvent(new StrategyEvent(
                                EventType.MARGIN_SAFE,
                                "ALL",
                                "MarginProtector",
                                "Stato di sicurezza disattivato: livello di margine " + marginLevel + "% > " + warningMarginLevel + "%"
                            ));
                        }
                    }
                }
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante la verifica del livello di margine", e);
        }
    }
    
    @Override
    protected boolean checkConditions(Map<String, Object> accountInfo, List<Position> positions) throws CommandExecutionException {
        // Verifica se il margine libero è inferiore al minimo
        double freeMargin = getFreeMargin(accountInfo);
        if (freeMargin < minFreeMargin) {
            LOGGER.log(Level.WARNING, "Margine libero critico: {0} < {1}", new Object[]{freeMargin, minFreeMargin});
            return true;
        }
        
        // Verifica se il livello di margine è inferiore al livello critico
        double marginLevel = getMarginLevel(accountInfo);
        if (marginLevel < criticalMarginLevel) {
            LOGGER.log(Level.WARNING, "Livello di margine critico: {0}% < {1}%", new Object[]{marginLevel, criticalMarginLevel});
            return true;
        }
        
        return false;
    }
    
    @Override
    protected boolean executeAction(Map<String, Object> accountInfo, List<Position> positions) throws CommandExecutionException {
        if (positions.isEmpty()) {
            return false;
        }
        
        // Attiva lo stato di sicurezza
        safeStateActive = true;
        
        double freeMargin = getFreeMargin(accountInfo);
        double marginLevel = getMarginLevel(accountInfo);
        
        LOGGER.log(Level.WARNING, "Protezione margine attivata: margine libero {0}, livello di margine {1}%", 
                new Object[]{freeMargin, marginLevel});
        
        // Notifica l'evento di protezione del margine
        eventManager.notifyEvent(new StrategyEvent(
            EventType.MARGIN_CALL,
            "ALL",
            "MarginProtector",
            "Protezione margine attivata: margine libero " + freeMargin + ", livello di margine " + marginLevel + "%"
        ));
        
        // Ordina le posizioni per perdita (dalla più in perdita alla meno in perdita)
        List<Position> sortedPositions = positions.stream()
                .sorted(Comparator.comparing(Position::getProfit))
                .collect(Collectors.toList());
        
        // Chiudi le posizioni in perdita fino a raggiungere un livello di margine sicuro
        for (Position position : sortedPositions) {
            try {
                // Chiudi la posizione
                Map<String, Object> result = mt5Commands.closePosition(position.getTicket(), null);
                
                if (result.containsKey("success") && (Boolean) result.get("success")) {
                    LOGGER.log(Level.INFO, "Posizione chiusa per protezione margine: {0}", position.getTicket());
                    
                    // Notifica l'evento di chiusura della posizione
                    eventManager.notifyEvent(new PositionEvent(
                        EventType.POSITION_CLOSED,
                        position,
                        "Posizione chiusa per protezione margine"
                    ));
                    
                    // Aggiorna le informazioni sull'account
                    accountInfo = mt5Commands.getAccountInfo();
                    
                    // Verifica se il livello di margine è tornato a un livello sicuro
                    marginLevel = getMarginLevel(accountInfo);
                    if (marginLevel > warningMarginLevel) {
                        LOGGER.log(Level.INFO, "Livello di margine tornato a un livello sicuro: {0}% > {1}%", 
                                new Object[]{marginLevel, warningMarginLevel});
                        break;
                    }
                } else {
                    LOGGER.log(Level.WARNING, "Errore durante la chiusura della posizione: {0}", position.getTicket());
                }
            } catch (Exception e) {
                LOGGER.log(Level.SEVERE, "Errore durante la chiusura della posizione: " + position.getTicket(), e);
            }
        }
        
        return true;
    }
    
    @Override
    protected boolean validateNewPosition(Map<String, Object> accountInfo, List<Position> positions, 
                                        String symbol, double volume, double stopLoss, double takeProfit) throws CommandExecutionException {
        // Se lo stato di sicurezza è attivo, non permettere l'apertura di nuove posizioni
        if (safeStateActive) {
            LOGGER.log(Level.WARNING, "Apertura posizione non permessa: stato di sicurezza attivo");
            return false;
        }
        
        // Verifica se il margine libero è sufficiente
        double freeMargin = getFreeMargin(accountInfo);
        if (freeMargin < minFreeMargin) {
            LOGGER.log(Level.WARNING, "Apertura posizione non permessa: margine libero insufficiente {0} < {1}", 
                    new Object[]{freeMargin, minFreeMargin});
            return false;
        }
        
        // Verifica se il livello di margine è sufficiente
        double marginLevel = getMarginLevel(accountInfo);
        if (marginLevel < warningMarginLevel) {
            LOGGER.log(Level.WARNING, "Apertura posizione non permessa: livello di margine insufficiente {0}% < {1}%", 
                    new Object[]{marginLevel, warningMarginLevel});
            return false;
        }
        
        return true;
    }
    
    /**
     * Ottiene il margine libero.
     * 
     * @param accountInfo Le informazioni sull'account
     * @return Il margine libero
     */
    private double getFreeMargin(Map<String, Object> accountInfo) {
        if (accountInfo.containsKey("account_info")) {
            @SuppressWarnings("unchecked")
            Map<String, Object> accountInfoData = (Map<String, Object>) accountInfo.get("account_info");
            
            if (accountInfoData.containsKey("margin_free")) {
                return ((Number) accountInfoData.get("margin_free")).doubleValue();
            }
        }
        
        return 0.0;
    }
    
    /**
     * Ottiene il livello di margine.
     * 
     * @param accountInfo Le informazioni sull'account
     * @return Il livello di margine in percentuale
     */
    private double getMarginLevel(Map<String, Object> accountInfo) {
        if (accountInfo.containsKey("account_info")) {
            @SuppressWarnings("unchecked")
            Map<String, Object> accountInfoData = (Map<String, Object>) accountInfo.get("account_info");
            
            if (accountInfoData.containsKey("margin_level")) {
                return ((Number) accountInfoData.get("margin_level")).doubleValue();
            }
        }
        
        return 0.0;
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
     * Imposta il livello di margine critico.
     * 
     * @param criticalMarginLevel Il livello di margine critico in percentuale
     */
    public void setCriticalMarginLevel(double criticalMarginLevel) {
        this.criticalMarginLevel = criticalMarginLevel;
    }
    
    /**
     * Imposta il livello di margine di avviso.
     * 
     * @param warningMarginLevel Il livello di margine di avviso in percentuale
     */
    public void setWarningMarginLevel(double warningMarginLevel) {
        this.warningMarginLevel = warningMarginLevel;
    }
    
    /**
     * Imposta l'intervallo di verifica.
     * 
     * @param checkIntervalSeconds L'intervallo di verifica in secondi
     */
    public void setCheckIntervalSeconds(long checkIntervalSeconds) {
        this.checkIntervalSeconds = checkIntervalSeconds;
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
     * Restituisce il livello di margine critico.
     * 
     * @return Il livello di margine critico in percentuale
     */
    public double getCriticalMarginLevel() {
        return criticalMarginLevel;
    }
    
    /**
     * Restituisce il livello di margine di avviso.
     * 
     * @return Il livello di margine di avviso in percentuale
     */
    public double getWarningMarginLevel() {
        return warningMarginLevel;
    }
    
    /**
     * Restituisce l'intervallo di verifica.
     * 
     * @return L'intervallo di verifica in secondi
     */
    public long getCheckIntervalSeconds() {
        return checkIntervalSeconds;
    }
    
    /**
     * Verifica se lo stato di sicurezza è attivo.
     * 
     * @return true se lo stato di sicurezza è attivo, false altrimenti
     */
    public boolean isSafeStateActive() {
        return safeStateActive;
    }
}
