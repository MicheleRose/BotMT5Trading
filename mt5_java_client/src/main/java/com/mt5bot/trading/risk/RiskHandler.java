package main.java.com.mt5bot.trading.risk;

import main.java.com.mt5bot.client.CommandExecutionException;
import main.java.com.mt5bot.trading.model.Position;

import java.util.List;
import java.util.Map;

/**
 * Interfaccia per gli handler di risk management.
 * Definisce i metodi che devono essere implementati da ogni handler di risk management.
 */
public interface RiskHandler {
    
    /**
     * Priorità dell'handler.
     * Gli handler con priorità più alta vengono eseguiti prima.
     */
    enum Priority {
        HIGHEST(100),
        HIGH(75),
        MEDIUM(50),
        LOW(25),
        LOWEST(0);
        
        private final int value;
        
        Priority(int value) {
            this.value = value;
        }
        
        public int getValue() {
            return value;
        }
    }
    
    /**
     * Verifica se è necessario eseguire l'handler.
     * 
     * @param accountInfo Le informazioni sull'account
     * @param positions Le posizioni aperte
     * @return true se è necessario eseguire l'handler, false altrimenti
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    boolean shouldExecute(Map<String, Object> accountInfo, List<Position> positions) throws CommandExecutionException;
    
    /**
     * Esegue l'handler.
     * 
     * @param accountInfo Le informazioni sull'account
     * @param positions Le posizioni aperte
     * @return true se l'handler è stato eseguito con successo, false altrimenti
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    boolean execute(Map<String, Object> accountInfo, List<Position> positions) throws CommandExecutionException;
    
    /**
     * Verifica se è possibile aprire una nuova posizione.
     * 
     * @param accountInfo Le informazioni sull'account
     * @param positions Le posizioni aperte
     * @param symbol Il simbolo della nuova posizione
     * @param volume Il volume della nuova posizione
     * @param stopLoss Il livello di stop loss della nuova posizione
     * @param takeProfit Il livello di take profit della nuova posizione
     * @return true se è possibile aprire la posizione, false altrimenti
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    boolean canOpenPosition(Map<String, Object> accountInfo, List<Position> positions, 
                           String symbol, double volume, double stopLoss, double takeProfit) throws CommandExecutionException;
    
    /**
     * Restituisce la priorità dell'handler.
     * 
     * @return La priorità dell'handler
     */
    Priority getPriority();
    
    /**
     * Restituisce il nome dell'handler.
     * 
     * @return Il nome dell'handler
     */
    String getName();
    
    /**
     * Avvia il monitoraggio dell'handler.
     */
    void startMonitoring();
    
    /**
     * Ferma il monitoraggio dell'handler.
     */
    void stopMonitoring();
    
    /**
     * Verifica se l'handler è attivo.
     * 
     * @return true se l'handler è attivo, false altrimenti
     */
    boolean isActive();
}
