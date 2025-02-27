package main.java.com.mt5bot.trading.strategy;

import com.mt5bot.client.CommandExecutionException;
import com.mt5bot.client.MT5Commands;
import com.mt5bot.trading.event.StrategyEvent;
import com.mt5bot.trading.event.TradingEvent.EventType;
import com.mt5bot.trading.event.TradingEventManager;
import com.mt5bot.trading.manager.PositionManager;
import com.mt5bot.trading.model.Position;
import com.mt5bot.trading.model.Position.PositionType;

import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Strategia di scaling per l'apertura di posizioni.
 * Implementa la logica di entrata scalare con 3 operazioni iniziali,
 * trigger a 15 pips per 4 nuove operazioni, tracking del massimo 20 operazioni
 * e gestione incremento lotti (+0.01 ogni 4 operazioni).
 */
public class ScalingStrategy {
    
    private static final Logger LOGGER = Logger.getLogger(ScalingStrategy.class.getName());
    
    private final MT5Commands mt5Commands;
    private final PositionManager positionManager;
    private final TradingEventManager eventManager;
    
    // Parametri di configurazione
    private int initialPositions = 3;
    private int additionalPositions = 4;
    private double triggerPips = 15.0;
    private double lotIncrement = 0.01;
    private int lotIncrementStep = 4;
    private int maxPositions = 20;
    
    // Stato della strategia
    private final AtomicInteger scalingLevel = new AtomicInteger(0);
    
    /**
     * Costruttore per la strategia di scaling.
     * 
     * @param mt5Commands Il client MT5 per l'esecuzione dei comandi
     * @param positionManager Il gestore delle posizioni
     * @param eventManager Il gestore degli eventi di trading
     */
    public ScalingStrategy(MT5Commands mt5Commands, PositionManager positionManager, TradingEventManager eventManager) {
        this.mt5Commands = mt5Commands;
        this.positionManager = positionManager;
        this.eventManager = eventManager;
    }
    
    /**
     * Inizia una nuova strategia di scaling.
     * 
     * @param symbol Il simbolo
     * @param type Il tipo di posizione (BUY o SELL)
     * @param baseLot Il lotto base
     * @param stopLoss Il livello di stop loss
     * @param takeProfit Il livello di take profit
     * @param comment Il commento
     * @param magicNumber Il magic number
     * @return L'ID del gruppo creato
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    public String startScaling(String symbol, PositionType type, double baseLot, 
                              double stopLoss, double takeProfit, String comment, 
                              int magicNumber) throws CommandExecutionException {
        // Crea un nuovo gruppo per le posizioni
        String groupId = positionManager.createGroup(symbol);
        
        // Resetta il livello di scaling
        scalingLevel.set(0);
        
        // Apri le posizioni iniziali
        for (int i = 0; i < initialPositions; i++) {
            if (positionManager.canOpenPosition(symbol, groupId)) {
                openPosition(symbol, type, baseLot, stopLoss, takeProfit, comment, magicNumber, groupId);
            } else {
                LOGGER.warning("Impossibile aprire tutte le posizioni iniziali. Limite raggiunto.");
                break;
            }
        }
        
        // Notifica l'evento di inizio scaling
        eventManager.notifyEvent(new StrategyEvent(
            EventType.SCALING_TRIGGERED,
            symbol,
            "ScalingStrategy",
            "Iniziata strategia di scaling con " + initialPositions + " posizioni iniziali"
        ));
        
        return groupId;
    }
    
    /**
     * Verifica se è necessario eseguire lo scaling per un gruppo.
     * 
     * @param groupId L'ID del gruppo
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    public void checkScaling(String groupId) throws CommandExecutionException {
        List<Position> groupPositions = positionManager.getPositionsByGroup(groupId);
        
        if (groupPositions.isEmpty()) {
            return;
        }
        
        // Ottieni il simbolo e il tipo dalla prima posizione
        String symbol = groupPositions.get(0).getSymbol();
        PositionType type = groupPositions.get(0).getType();
        
        // Verifica se è stato raggiunto il livello di profitto per lo scaling
        boolean triggerReached = groupPositions.stream()
                .anyMatch(p -> p.hasProfitPips(triggerPips * (scalingLevel.get() + 1)));
        
        if (triggerReached && positionManager.getPositionCountByGroup(groupId) < maxPositions) {
            // Incrementa il livello di scaling
            int level = scalingLevel.incrementAndGet();
            
            // Calcola il lotto per le nuove posizioni
            double baseLot = groupPositions.get(0).getVolume();
            double lot = baseLot + (lotIncrement * (level / lotIncrementStep));
            
            // Ottieni i livelli di stop loss e take profit dalla prima posizione
            double stopLoss = groupPositions.get(0).getStopLoss();
            double takeProfit = groupPositions.get(0).getTakeProfit();
            
            // Ottieni il commento e il magic number dalla prima posizione
            String comment = groupPositions.get(0).getComment();
            int magicNumber = groupPositions.get(0).getMagicNumber();
            
            // Apri le posizioni aggiuntive
            int positionsOpened = 0;
            for (int i = 0; i < additionalPositions; i++) {
                if (positionManager.canOpenPosition(symbol, groupId)) {
                    openPosition(symbol, type, lot, stopLoss, takeProfit, comment, magicNumber, groupId);
                    positionsOpened++;
                } else {
                    LOGGER.warning("Impossibile aprire tutte le posizioni aggiuntive. Limite raggiunto.");
                    break;
                }
            }
            
            // Notifica l'evento di scaling
            eventManager.notifyEvent(new StrategyEvent(
                EventType.SCALING_TRIGGERED,
                symbol,
                "ScalingStrategy",
                "Eseguito scaling di livello " + level + " con " + positionsOpened + " nuove posizioni"
            ));
        }
    }
    
    /**
     * Apre una nuova posizione e la aggiunge al gruppo.
     * 
     * @param symbol Il simbolo
     * @param type Il tipo di posizione (BUY o SELL)
     * @param lot Il lotto
     * @param stopLoss Il livello di stop loss
     * @param takeProfit Il livello di take profit
     * @param comment Il commento
     * @param magicNumber Il magic number
     * @param groupId L'ID del gruppo
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    private void openPosition(String symbol, PositionType type, double lot, 
                             double stopLoss, double takeProfit, String comment, 
                             int magicNumber, String groupId) throws CommandExecutionException {
        try {
            Map<String, Object> result;
            
            if (type == PositionType.BUY) {
                result = mt5Commands.marketBuy(symbol, lot, stopLoss, takeProfit, comment, magicNumber);
            } else {
                result = mt5Commands.marketSell(symbol, lot, stopLoss, takeProfit, comment, magicNumber);
            }
            
            if (result.containsKey("ticket")) {
                long ticket = ((Number) result.get("ticket")).longValue();
                
                // Aggiorna le posizioni
                positionManager.updatePositions();
                
                // Aggiungi la posizione al gruppo
                positionManager.addPositionToGroup(ticket, groupId);
                
                LOGGER.log(Level.INFO, "Aperta posizione {0} {1} {2} lotti, ticket: {3}, gruppo: {4}",
                        new Object[]{type, symbol, lot, ticket, groupId});
            } else {
                LOGGER.warning("Errore durante l'apertura della posizione: " + result);
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante l'apertura della posizione", e);
            eventManager.notifyError(symbol, "Errore durante l'apertura della posizione", "ScalingStrategy", e);
            throw e;
        }
    }
    
    /**
     * Verifica se una strategia di scaling è completata.
     * 
     * @param groupId L'ID del gruppo
     * @return true se la strategia è completata, false altrimenti
     */
    public boolean isScalingCompleted(String groupId) {
        int positionCount = positionManager.getPositionCountByGroup(groupId);
        return positionCount >= maxPositions || scalingLevel.get() >= 5;
    }
    
    /**
     * Imposta il numero di posizioni iniziali.
     * 
     * @param initialPositions Il numero di posizioni iniziali
     */
    public void setInitialPositions(int initialPositions) {
        this.initialPositions = initialPositions;
    }
    
    /**
     * Imposta il numero di posizioni aggiuntive per ogni livello di scaling.
     * 
     * @param additionalPositions Il numero di posizioni aggiuntive
     */
    public void setAdditionalPositions(int additionalPositions) {
        this.additionalPositions = additionalPositions;
    }
    
    /**
     * Imposta il livello di profitto in pips per attivare lo scaling.
     * 
     * @param triggerPips Il livello di profitto in pips
     */
    public void setTriggerPips(double triggerPips) {
        this.triggerPips = triggerPips;
    }
    
    /**
     * Imposta l'incremento del lotto per ogni step.
     * 
     * @param lotIncrement L'incremento del lotto
     */
    public void setLotIncrement(double lotIncrement) {
        this.lotIncrement = lotIncrement;
    }
    
    /**
     * Imposta il numero di livelli di scaling per incrementare il lotto.
     * 
     * @param lotIncrementStep Il numero di livelli di scaling
     */
    public void setLotIncrementStep(int lotIncrementStep) {
        this.lotIncrementStep = lotIncrementStep;
    }
    
    /**
     * Imposta il numero massimo di posizioni per una strategia di scaling.
     * 
     * @param maxPositions Il numero massimo di posizioni
     */
    public void setMaxPositions(int maxPositions) {
        this.maxPositions = maxPositions;
    }
    
    /**
     * Restituisce il livello di scaling corrente.
     * 
     * @return Il livello di scaling corrente
     */
    public int getScalingLevel() {
        return scalingLevel.get();
    }
}
