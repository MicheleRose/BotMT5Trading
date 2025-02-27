package main.java.com.mt5bot.trading.event;

/**
 * Evento relativo a una strategia di trading.
 */
public class StrategyEvent extends TradingEvent {
    
    private final String strategyName;
    private final String details;
    
    /**
     * Costruttore per un evento di strategia.
     * 
     * @param type Il tipo di evento
     * @param symbol Il simbolo associato all'evento
     * @param strategyName Il nome della strategia
     * @param details I dettagli dell'evento
     */
    public StrategyEvent(EventType type, String symbol, String strategyName, String details) {
        super(type, symbol);
        this.strategyName = strategyName;
        this.details = details;
    }
    
    /**
     * Restituisce il nome della strategia.
     * 
     * @return Il nome della strategia
     */
    public String getStrategyName() {
        return strategyName;
    }
    
    /**
     * Restituisce i dettagli dell'evento.
     * 
     * @return I dettagli dell'evento
     */
    public String getDetails() {
        return details;
    }
    
    @Override
    public String getDescription() {
        StringBuilder description = new StringBuilder();
        
        description.append("Strategia '")
                  .append(strategyName)
                  .append("': ");
        
        switch (getType()) {
            case SCALING_TRIGGERED:
                description.append("Scaling triggered");
                break;
                
            case SCALING_COMPLETED:
                description.append("Scaling completed");
                break;
                
            case VOLATILITY_CHANGED:
                description.append("Volatility changed");
                break;
                
            default:
                description.append("Strategy event");
                break;
        }
        
        if (details != null && !details.isEmpty()) {
            description.append(" - ").append(details);
        }
        
        return description.toString();
    }
}
