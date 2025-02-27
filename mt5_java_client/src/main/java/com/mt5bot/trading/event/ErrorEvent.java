package main.java.com.mt5bot.trading.event;

/**
 * Evento di errore nel sistema di trading.
 */
public class ErrorEvent extends TradingEvent {
    
    private final String errorMessage;
    private final Throwable exception;
    private final String source;
    
    /**
     * Costruttore per un evento di errore.
     * 
     * @param symbol Il simbolo associato all'errore (può essere null)
     * @param errorMessage Il messaggio di errore
     * @param source La sorgente dell'errore
     */
    public ErrorEvent(String symbol, String errorMessage, String source) {
        this(symbol, errorMessage, source, null);
    }
    
    /**
     * Costruttore per un evento di errore con eccezione.
     * 
     * @param symbol Il simbolo associato all'errore (può essere null)
     * @param errorMessage Il messaggio di errore
     * @param source La sorgente dell'errore
     * @param exception L'eccezione che ha causato l'errore
     */
    public ErrorEvent(String symbol, String errorMessage, String source, Throwable exception) {
        super(EventType.ERROR, symbol != null ? symbol : "SYSTEM");
        this.errorMessage = errorMessage;
        this.source = source;
        this.exception = exception;
    }
    
    /**
     * Restituisce il messaggio di errore.
     * 
     * @return Il messaggio di errore
     */
    public String getErrorMessage() {
        return errorMessage;
    }
    
    /**
     * Restituisce l'eccezione che ha causato l'errore.
     * 
     * @return L'eccezione che ha causato l'errore
     */
    public Throwable getException() {
        return exception;
    }
    
    /**
     * Restituisce la sorgente dell'errore.
     * 
     * @return La sorgente dell'errore
     */
    public String getSource() {
        return source;
    }
    
    @Override
    public String getDescription() {
        StringBuilder description = new StringBuilder();
        
        description.append("Error in '")
                  .append(source)
                  .append("': ")
                  .append(errorMessage);
        
        if (exception != null) {
            description.append(" - Exception: ")
                      .append(exception.getClass().getSimpleName())
                      .append(": ")
                      .append(exception.getMessage());
        }
        
        return description.toString();
    }
}
