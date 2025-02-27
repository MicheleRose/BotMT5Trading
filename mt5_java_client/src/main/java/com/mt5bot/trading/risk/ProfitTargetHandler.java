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
 * Handler per il monitoraggio del profitto flottante totale.
 * Implementa il monitoraggio del profitto flottante totale e la chiusura globale
 * al raggiungimento di un target di profitto.
 */
public class ProfitTargetHandler extends AbstractRiskHandler {
    
    private static final Logger LOGGER = Logger.getLogger(ProfitTargetHandler.class.getName());
    
    private final MT5Commands mt5Commands;
    
    // Parametri di configurazione
    private double profitTargetPercent = 2.0; // Target di profitto in percentuale del saldo iniziale
    private long checkIntervalSeconds = 30; // Intervallo di verifica in secondi
    
    // Scheduler per la verifica periodica
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
    
    /**
     * Costruttore per l'handler del target di profitto.
     * 
     * @param mt5Commands Il client MT5 per l'esecuzione dei comandi
     * @param eventManager Il gestore degli eventi di trading
     */
    public ProfitTargetHandler(MT5Commands mt5Commands, TradingEventManager eventManager) {
        super(eventManager, "ProfitTargetHandler", Priority.HIGH);
        this.mt5Commands = mt5Commands;
    }
    
    @Override
    public void startMonitoring() {
        super.startMonitoring();
        
        // Avvia lo scheduler per la verifica periodica
        scheduler.scheduleAtFixedRate(this::checkProfitTarget, 0, checkIntervalSeconds, TimeUnit.SECONDS);
        
        LOGGER.info("Monitoraggio del target di profitto avviato");
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
        
        LOGGER.info("Monitoraggio del target di profitto fermato");
    }
    
    /**
     * Verifica il target di profitto.
     */
    private void checkProfitTarget() {
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
                    double profit = ((Number) positionData.get("profit")).doubleValue();
                    
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
                }
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante la verifica del target di profitto", e);
        }
    }
    
    @Override
    protected boolean checkConditions(Map<String, Object> accountInfo, List<Position> positions) throws CommandExecutionException {
        // Verifica se il profitto totale ha raggiunto il target
        double totalProfit = getTotalProfit(positions);
        double balance = getBalance(accountInfo);
        double profitTarget = balance * profitTargetPercent / 100.0;
        
        return totalProfit >= profitTarget;
    }
    
    @Override
    protected boolean executeAction(Map<String, Object> accountInfo, List<Position> positions) throws CommandExecutionException {
        if (positions.isEmpty()) {
            return false;
        }
        
        double totalProfit = getTotalProfit(positions);
        double balance = getBalance(accountInfo);
        double profitTarget = balance * profitTargetPercent / 100.0;
        
        LOGGER.log(Level.INFO, "Target di profitto raggiunto: {0} >= {1}", new Object[]{totalProfit, profitTarget});
        
        // Notifica l'evento di raggiungimento del target di profitto
        eventManager.notifyEvent(new StrategyEvent(
            EventType.SCALING_COMPLETED,
            "ALL",
            "ProfitTargetHandler",
            "Target di profitto raggiunto: " + totalProfit + " >= " + profitTarget
        ));
        
        // Ordina le posizioni per profitto (dalla più profittevole alla meno profittevole)
        List<Position> sortedPositions = positions.stream()
                .sorted(Comparator.comparing(Position::getProfit).reversed())
                .collect(Collectors.toList());
        
        // Chiudi tutte le posizioni
        for (Position position : sortedPositions) {
            try {
                Map<String, Object> result = mt5Commands.closePosition(position.getTicket(), null);
                
                if (result.containsKey("success") && (Boolean) result.get("success")) {
                    LOGGER.log(Level.INFO, "Posizione chiusa per target di profitto: {0}", position.getTicket());
                    
                    // Notifica l'evento di chiusura della posizione
                    eventManager.notifyEvent(new PositionEvent(
                        EventType.POSITION_CLOSED,
                        position,
                        "Posizione chiusa per target di profitto"
                    ));
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
        // Verifica se il profitto totale ha raggiunto il target
        double totalProfit = getTotalProfit(positions);
        double balance = getBalance(accountInfo);
        double profitTarget = balance * profitTargetPercent / 100.0;
        
        // Se il profitto totale ha raggiunto il target, non permettere l'apertura di nuove posizioni
        if (totalProfit >= profitTarget) {
            LOGGER.log(Level.WARNING, "Apertura posizione non permessa: target di profitto raggiunto");
            return false;
        }
        
        return true;
    }
    
    /**
     * Calcola il profitto totale delle posizioni aperte.
     * 
     * @param positions Le posizioni aperte
     * @return Il profitto totale
     */
    private double getTotalProfit(List<Position> positions) {
        return positions.stream()
                .mapToDouble(Position::getProfit)
                .sum();
    }
    
    /**
     * Ottiene il saldo dell'account.
     * 
     * @param accountInfo Le informazioni sull'account
     * @return Il saldo dell'account
     */
    private double getBalance(Map<String, Object> accountInfo) {
        if (accountInfo.containsKey("account_info")) {
            @SuppressWarnings("unchecked")
            Map<String, Object> accountInfoData = (Map<String, Object>) accountInfo.get("account_info");
            
            if (accountInfoData.containsKey("balance")) {
                return ((Number) accountInfoData.get("balance")).doubleValue();
            }
        }
        
        return 0.0;
    }
    
    /**
     * Imposta il target di profitto in percentuale del saldo iniziale.
     * 
     * @param profitTargetPercent Il target di profitto in percentuale
     */
    public void setProfitTargetPercent(double profitTargetPercent) {
        this.profitTargetPercent = profitTargetPercent;
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
     * Restituisce il target di profitto in percentuale del saldo iniziale.
     * 
     * @return Il target di profitto in percentuale
     */
    public double getProfitTargetPercent() {
        return profitTargetPercent;
    }
    
    /**
     * Restituisce l'intervallo di verifica.
     * 
     * @return L'intervallo di verifica in secondi
     */
    public long getCheckIntervalSeconds() {
        return checkIntervalSeconds;
    }
}
