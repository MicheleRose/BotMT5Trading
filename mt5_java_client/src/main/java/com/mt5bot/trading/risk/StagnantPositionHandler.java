package main.java.com.mt5bot.trading.risk;

import main.java.com.mt5bot.client.CommandExecutionException;
import main.java.com.mt5bot.client.MT5Commands;
import main.java.com.mt5bot.trading.event.PositionEvent;
import main.java.com.mt5bot.trading.event.TradingEvent.EventType;
import main.java.com.mt5bot.trading.event.TradingEventManager;
import main.java.com.mt5bot.trading.model.Position;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.stream.Collectors;

/**
 * Handler per il monitoraggio e la chiusura automatica delle posizioni stagnanti.
 * Implementa il monitoraggio della durata delle posizioni aperte e la chiusura automatica
 * dopo un periodo di inattività.
 */
public class StagnantPositionHandler extends AbstractRiskHandler {
    
    private static final Logger LOGGER = Logger.getLogger(StagnantPositionHandler.class.getName());
    
    private final MT5Commands mt5Commands;
    
    // Parametri di configurazione
    private long maxInactiveMinutes = 50; // Durata massima di inattività in minuti
    private double minProfitPips = 5.0; // Profitto minimo in pips per considerare una posizione attiva
    private long checkIntervalSeconds = 60; // Intervallo di verifica in secondi
    
    // Scheduler per la verifica periodica
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
    
    /**
     * Costruttore per l'handler delle posizioni stagnanti.
     * 
     * @param mt5Commands Il client MT5 per l'esecuzione dei comandi
     * @param eventManager Il gestore degli eventi di trading
     */
    public StagnantPositionHandler(MT5Commands mt5Commands, TradingEventManager eventManager) {
        super(eventManager, "StagnantPositionHandler", Priority.MEDIUM);
        this.mt5Commands = mt5Commands;
    }
    
    @Override
    public void startMonitoring() {
        super.startMonitoring();
        
        // Avvia lo scheduler per la verifica periodica
        scheduler.scheduleAtFixedRate(this::checkStagnantPositions, 0, checkIntervalSeconds, TimeUnit.SECONDS);
        
        LOGGER.info("Monitoraggio delle posizioni stagnanti avviato");
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
        
        LOGGER.info("Monitoraggio delle posizioni stagnanti fermato");
    }
    
    /**
     * Verifica le posizioni stagnanti.
     */
    private void checkStagnantPositions() {
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
                        ticket, symbol, type, volume, openPrice, LocalDateTime.now().minusMinutes(
                            // Simula il tempo di apertura (in un'implementazione reale, questo verrebbe dal server MT5)
                            positionData.containsKey("time_open") ? 
                                ((Number) positionData.get("time_open")).longValue() : 
                                (long) (Math.random() * 120) // Tempo casuale tra 0 e 120 minuti
                        ),
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
            LOGGER.log(Level.SEVERE, "Errore durante la verifica delle posizioni stagnanti", e);
        }
    }
    
    @Override
    protected boolean checkConditions(Map<String, Object> accountInfo, List<Position> positions) throws CommandExecutionException {
        // Verifica se ci sono posizioni stagnanti
        return !getStagnantPositions(positions).isEmpty();
    }
    
    @Override
    protected boolean executeAction(Map<String, Object> accountInfo, List<Position> positions) throws CommandExecutionException {
        // Ottieni le posizioni stagnanti
        List<Position> stagnantPositions = getStagnantPositions(positions);
        
        if (stagnantPositions.isEmpty()) {
            return false;
        }
        
        LOGGER.log(Level.INFO, "Chiusura di {0} posizioni stagnanti", stagnantPositions.size());
        
        // Chiudi le posizioni stagnanti
        for (Position position : stagnantPositions) {
            try {
                Map<String, Object> result = mt5Commands.closePosition(position.getTicket(), null);
                
                if (result.containsKey("success") && (Boolean) result.get("success")) {
                    LOGGER.log(Level.INFO, "Posizione stagnante chiusa: {0}", position.getTicket());
                    
                    // Notifica l'evento di chiusura della posizione
                    eventManager.notifyEvent(new PositionEvent(
                        EventType.POSITION_CLOSED,
                        position,
                        "Posizione stagnante chiusa dopo " + getPositionAgeMinutes(position) + " minuti"
                    ));
                } else {
                    LOGGER.log(Level.WARNING, "Errore durante la chiusura della posizione stagnante: {0}", position.getTicket());
                }
            } catch (Exception e) {
                LOGGER.log(Level.SEVERE, "Errore durante la chiusura della posizione stagnante: " + position.getTicket(), e);
            }
        }
        
        return true;
    }
    
    @Override
    protected boolean validateNewPosition(Map<String, Object> accountInfo, List<Position> positions, 
                                        String symbol, double volume, double stopLoss, double takeProfit) throws CommandExecutionException {
        // Non ci sono restrizioni per l'apertura di nuove posizioni
        return true;
    }
    
    /**
     * Ottiene le posizioni stagnanti.
     * 
     * @param positions Le posizioni aperte
     * @return Le posizioni stagnanti
     */
    private List<Position> getStagnantPositions(List<Position> positions) {
        return positions.stream()
                .filter(this::isStagnant)
                .collect(Collectors.toList());
    }
    
    /**
     * Verifica se una posizione è stagnante.
     * 
     * @param position La posizione
     * @return true se la posizione è stagnante, false altrimenti
     */
    private boolean isStagnant(Position position) {
        // Verifica se la posizione è aperta da troppo tempo
        long ageMinutes = getPositionAgeMinutes(position);
        
        // Verifica se la posizione ha un profitto minimo
        boolean hasMinProfit = position.hasProfitPips(minProfitPips);
        
        // Una posizione è stagnante se è aperta da troppo tempo e non ha un profitto minimo
        return ageMinutes >= maxInactiveMinutes && !hasMinProfit;
    }
    
    /**
     * Calcola l'età di una posizione in minuti.
     * 
     * @param position La posizione
     * @return L'età della posizione in minuti
     */
    private long getPositionAgeMinutes(Position position) {
        return Duration.between(position.getOpenTime(), LocalDateTime.now()).toMinutes();
    }
    
    /**
     * Imposta la durata massima di inattività.
     * 
     * @param maxInactiveMinutes La durata massima di inattività in minuti
     */
    public void setMaxInactiveMinutes(long maxInactiveMinutes) {
        this.maxInactiveMinutes = maxInactiveMinutes;
    }
    
    /**
     * Imposta il profitto minimo in pips per considerare una posizione attiva.
     * 
     * @param minProfitPips Il profitto minimo in pips
     */
    public void setMinProfitPips(double minProfitPips) {
        this.minProfitPips = minProfitPips;
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
     * Restituisce la durata massima di inattività.
     * 
     * @return La durata massima di inattività in minuti
     */
    public long getMaxInactiveMinutes() {
        return maxInactiveMinutes;
    }
    
    /**
     * Restituisce il profitto minimo in pips per considerare una posizione attiva.
     * 
     * @return Il profitto minimo in pips
     */
    public double getMinProfitPips() {
        return minProfitPips;
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
