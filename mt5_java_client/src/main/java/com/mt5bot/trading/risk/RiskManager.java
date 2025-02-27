package main.java.com.mt5bot.trading.risk;

import com.mt5bot.client.CommandExecutionException;
import com.mt5bot.trading.model.Position;

import java.util.Map;

/**
 * Interfaccia principale per il risk management.
 * Definisce le regole di risk management e i metodi per la validazione degli ordini.
 */
public interface RiskManager {
    
    /**
     * Verifica se è possibile aprire una nuova posizione in base alle regole di risk management.
     * 
     * @param symbol Il simbolo della nuova posizione
     * @param volume Il volume della nuova posizione
     * @param stopLoss Il livello di stop loss della nuova posizione
     * @param takeProfit Il livello di take profit della nuova posizione
     * @return true se è possibile aprire la posizione, false altrimenti
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    boolean canOpenPosition(String symbol, double volume, double stopLoss, double takeProfit) throws CommandExecutionException;
    
    /**
     * Verifica se è necessario chiudere alcune posizioni in base alle regole di risk management.
     * 
     * @return true se è necessario chiudere alcune posizioni, false altrimenti
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    boolean shouldClosePositions() throws CommandExecutionException;
    
    /**
     * Esegue le azioni di risk management.
     * 
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    void executeRiskManagement() throws CommandExecutionException;
    
    /**
     * Verifica se lo spread è accettabile per un simbolo.
     * 
     * @param symbol Il simbolo
     * @return true se lo spread è accettabile, false altrimenti
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    boolean isSpreadAcceptable(String symbol) throws CommandExecutionException;
    
    /**
     * Verifica se il margine libero è sufficiente.
     * 
     * @return true se il margine libero è sufficiente, false altrimenti
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    boolean isFreeMarginSufficient() throws CommandExecutionException;
    
    /**
     * Ottiene le informazioni sull'account.
     * 
     * @return Le informazioni sull'account
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    Map<String, Object> getAccountInfo() throws CommandExecutionException;
    
    /**
     * Aggiunge un handler di risk management.
     * 
     * @param handler L'handler da aggiungere
     */
    void addRiskHandler(RiskHandler handler);
    
    /**
     * Rimuove un handler di risk management.
     * 
     * @param handler L'handler da rimuovere
     */
    void removeRiskHandler(RiskHandler handler);
    
    /**
     * Avvia il monitoraggio del risk management.
     */
    void startMonitoring();
    
    /**
     * Ferma il monitoraggio del risk management.
     */
    void stopMonitoring();
    
    /**
     * Verifica se il monitoraggio del risk management è attivo.
     * 
     * @return true se il monitoraggio è attivo, false altrimenti
     */
    boolean isMonitoring();
}
