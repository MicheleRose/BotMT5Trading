package main.java.com.mt5bot.trading.event;

import java.time.LocalDateTime;

/**
 * Classe base per tutti gli eventi di trading.
 */
public abstract class TradingEvent {
    
    /**
     * Tipo di evento di trading.
     */
    public enum EventType {
        POSITION_OPENED,
        POSITION_CLOSED,
        POSITION_MODIFIED,
        POSITION_GROUPED,
        POSITION_PROFIT_REACHED,
        POSITION_LOSS_REACHED,
        TRAILING_STOP_UPDATED,
        VOLATILITY_CHANGED,
        SCALING_TRIGGERED,
        SCALING_COMPLETED,
        ERROR
    }
    
    private final EventType type;
    private final LocalDateTime timestamp;
    private final String symbol;
    
    /**
     * Costruttore per un evento di trading.
     * 
     * @param type Il tipo di evento
     * @param symbol Il simbolo associato all'evento
     */
    protected TradingEvent(EventType type, String symbol) {
        this.type = type;
        this.timestamp = LocalDateTime.now();
        this.symbol = symbol;
    }
    
    /**
     * Restituisce il tipo di evento.
     * 
     * @return Il tipo di evento
     */
    public EventType getType() {
        return type;
    }
    
    /**
     * Restituisce il timestamp dell'evento.
     * 
     * @return Il timestamp dell'evento
     */
    public LocalDateTime getTimestamp() {
        return timestamp;
    }
    
    /**
     * Restituisce il simbolo associato all'evento.
     * 
     * @return Il simbolo associato all'evento
     */
    public String getSymbol() {
        return symbol;
    }
    
    /**
     * Restituisce una descrizione dell'evento.
     * 
     * @return Una descrizione dell'evento
     */
    public abstract String getDescription();
    
    @Override
    public String toString() {
        return String.format("[%s] %s - %s: %s", 
                timestamp, type, symbol, getDescription());
    }
}
