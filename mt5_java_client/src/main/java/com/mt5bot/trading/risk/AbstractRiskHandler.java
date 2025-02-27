package main.java.com.mt5bot.trading.risk;

import main.java.com.mt5bot.client.CommandExecutionException;
import main.java.com.mt5bot.trading.event.TradingEventManager;
import main.java.com.mt5bot.trading.model.Position;

import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Classe base per gli handler di risk management.
 * Fornisce l'implementazione comune per tutti gli handler di risk management.
 */
public abstract class AbstractRiskHandler implements RiskHandler {
    
    private static final Logger LOGGER = Logger.getLogger(AbstractRiskHandler.class.getName());
    
    protected final TradingEventManager eventManager;
    protected final String name;
    protected final Priority priority;
    
    private final AtomicBoolean active = new AtomicBoolean(false);
    
    /**
     * Costruttore per l'handler di risk management.
     * 
     * @param eventManager Il gestore degli eventi di trading
     * @param name Il nome dell'handler
     * @param priority La priorità dell'handler
     */
    protected AbstractRiskHandler(TradingEventManager eventManager, String name, Priority priority) {
        this.eventManager = eventManager;
        this.name = name;
        this.priority = priority;
    }
    
    @Override
    public boolean shouldExecute(Map<String, Object> accountInfo, List<Position> positions) throws CommandExecutionException {
        if (!isActive()) {
            return false;
        }
        
        try {
            return checkConditions(accountInfo, positions);
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Errore durante la verifica delle condizioni dell'handler " + getName(), e);
            return false;
        }
    }
    
    @Override
    public boolean execute(Map<String, Object> accountInfo, List<Position> positions) throws CommandExecutionException {
        if (!isActive()) {
            return false;
        }
        
        try {
            LOGGER.log(Level.INFO, "Esecuzione dell'handler {0}", getName());
            return executeAction(accountInfo, positions);
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante l'esecuzione dell'handler " + getName(), e);
            return false;
        }
    }
    
    @Override
    public boolean canOpenPosition(Map<String, Object> accountInfo, List<Position> positions, 
                                  String symbol, double volume, double stopLoss, double takeProfit) throws CommandExecutionException {
        if (!isActive()) {
            return true;
        }
        
        try {
            return validateNewPosition(accountInfo, positions, symbol, volume, stopLoss, takeProfit);
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Errore durante la validazione della nuova posizione nell'handler " + getName(), e);
            return false;
        }
    }
    
    @Override
    public Priority getPriority() {
        return priority;
    }
    
    @Override
    public String getName() {
        return name;
    }
    
    @Override
    public void startMonitoring() {
        active.set(true);
        LOGGER.log(Level.INFO, "Handler {0} avviato", getName());
    }
    
    @Override
    public void stopMonitoring() {
        active.set(false);
        LOGGER.log(Level.INFO, "Handler {0} fermato", getName());
    }
    
    @Override
    public boolean isActive() {
        return active.get();
    }
    
    /**
     * Verifica le condizioni per l'esecuzione dell'handler.
     * 
     * @param accountInfo Le informazioni sull'account
     * @param positions Le posizioni aperte
     * @return true se le condizioni sono soddisfatte, false altrimenti
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    protected abstract boolean checkConditions(Map<String, Object> accountInfo, List<Position> positions) throws CommandExecutionException;
    
    /**
     * Esegue l'azione dell'handler.
     * 
     * @param accountInfo Le informazioni sull'account
     * @param positions Le posizioni aperte
     * @return true se l'azione è stata eseguita con successo, false altrimenti
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    protected abstract boolean executeAction(Map<String, Object> accountInfo, List<Position> positions) throws CommandExecutionException;
    
    /**
     * Valida una nuova posizione.
     * 
     * @param accountInfo Le informazioni sull'account
     * @param positions Le posizioni aperte
     * @param symbol Il simbolo della nuova posizione
     * @param volume Il volume della nuova posizione
     * @param stopLoss Il livello di stop loss della nuova posizione
     * @param takeProfit Il livello di take profit della nuova posizione
     * @return true se la posizione è valida, false altrimenti
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    protected abstract boolean validateNewPosition(Map<String, Object> accountInfo, List<Position> positions, 
                                                 String symbol, double volume, double stopLoss, double takeProfit) throws CommandExecutionException;
}
