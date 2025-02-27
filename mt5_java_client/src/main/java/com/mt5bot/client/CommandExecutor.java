package com.mt5bot.client;

import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * Interfaccia astratta per l'esecuzione di comandi esterni.
 * Definisce i metodi per eseguire comandi di sistema e gestire i risultati.
 */
public interface CommandExecutor {
    
    /**
     * Esegue un comando e restituisce il risultato come stringa.
     * 
     * @param command Il comando da eseguire
     * @return Il risultato dell'esecuzione del comando
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    String execute(String command) throws CommandExecutionException;
    
    /**
     * Esegue un comando con un timeout specificato.
     * 
     * @param command Il comando da eseguire
     * @param timeout Il timeout per l'esecuzione
     * @param unit L'unità di tempo per il timeout
     * @return Il risultato dell'esecuzione del comando
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     * @throws CommandTimeoutException Se l'esecuzione supera il timeout
     */
    String execute(String command, long timeout, TimeUnit unit) 
            throws CommandExecutionException, CommandTimeoutException;
    
    /**
     * Esegue un comando con variabili d'ambiente aggiuntive.
     * 
     * @param command Il comando da eseguire
     * @param environmentVars Variabili d'ambiente aggiuntive
     * @return Il risultato dell'esecuzione del comando
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    String execute(String command, Map<String, String> environmentVars) 
            throws CommandExecutionException;
    
    /**
     * Esegue un comando con variabili d'ambiente aggiuntive e timeout.
     * 
     * @param command Il comando da eseguire
     * @param environmentVars Variabili d'ambiente aggiuntive
     * @param timeout Il timeout per l'esecuzione
     * @param unit L'unità di tempo per il timeout
     * @return Il risultato dell'esecuzione del comando
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     * @throws CommandTimeoutException Se l'esecuzione supera il timeout
     */
    String execute(String command, Map<String, String> environmentVars, long timeout, TimeUnit unit) 
            throws CommandExecutionException, CommandTimeoutException;
    
    /**
     * Interrompe l'esecuzione di un comando in corso.
     * 
     * @return true se il comando è stato interrotto con successo, false altrimenti
     */
    boolean interrupt();
}
