package com.mt5bot.client;

/**
 * Eccezione lanciata quando l'esecuzione di un comando supera il timeout specificato.
 */
public class CommandTimeoutException extends Exception {
    
    private static final long serialVersionUID = 1L;
    
    /**
     * Costruttore con messaggio di errore.
     * 
     * @param message Il messaggio di errore
     */
    public CommandTimeoutException(String message) {
        super(message);
    }
    
    /**
     * Costruttore con messaggio di errore e causa.
     * 
     * @param message Il messaggio di errore
     * @param cause La causa dell'eccezione
     */
    public CommandTimeoutException(String message, Throwable cause) {
        super(message, cause);
    }
}
