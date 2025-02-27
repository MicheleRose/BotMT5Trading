package com.mt5bot.client;

/**
 * Eccezione lanciata quando si verifica un errore durante l'esecuzione di un comando.
 */
public class CommandExecutionException extends Exception {
    
    private static final long serialVersionUID = 1L;
    
    /**
     * Costruttore con messaggio di errore.
     * 
     * @param message Il messaggio di errore
     */
    public CommandExecutionException(String message) {
        super(message);
    }
    
    /**
     * Costruttore con messaggio di errore e causa.
     * 
     * @param message Il messaggio di errore
     * @param cause La causa dell'eccezione
     */
    public CommandExecutionException(String message, Throwable cause) {
        super(message, cause);
    }
}
