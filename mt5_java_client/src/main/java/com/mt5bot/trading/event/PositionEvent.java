package main.java.com.mt5bot.trading.event;

import com.mt5bot.trading.model.Position;

/**
 * Evento relativo a una posizione di trading.
 */
public class PositionEvent extends TradingEvent {
    
    private final Position position;
    private final String additionalInfo;
    
    /**
     * Costruttore per un evento di posizione.
     * 
     * @param type Il tipo di evento
     * @param position La posizione associata all'evento
     */
    public PositionEvent(EventType type, Position position) {
        this(type, position, null);
    }
    
    /**
     * Costruttore per un evento di posizione con informazioni aggiuntive.
     * 
     * @param type Il tipo di evento
     * @param position La posizione associata all'evento
     * @param additionalInfo Informazioni aggiuntive sull'evento
     */
    public PositionEvent(EventType type, Position position, String additionalInfo) {
        super(type, position.getSymbol());
        this.position = position;
        this.additionalInfo = additionalInfo;
    }
    
    /**
     * Restituisce la posizione associata all'evento.
     * 
     * @return La posizione associata all'evento
     */
    public Position getPosition() {
        return position;
    }
    
    /**
     * Restituisce le informazioni aggiuntive sull'evento.
     * 
     * @return Le informazioni aggiuntive sull'evento
     */
    public String getAdditionalInfo() {
        return additionalInfo;
    }
    
    @Override
    public String getDescription() {
        StringBuilder description = new StringBuilder();
        
        switch (getType()) {
            case POSITION_OPENED:
                description.append("Posizione aperta: ")
                          .append(position.getType())
                          .append(" ")
                          .append(position.getVolume())
                          .append(" lotti a ")
                          .append(position.getOpenPrice());
                break;
                
            case POSITION_CLOSED:
                description.append("Posizione chiusa: ")
                          .append(position.getType())
                          .append(" ")
                          .append(position.getVolume())
                          .append(" lotti, profitto: ")
                          .append(position.getProfit());
                break;
                
            case POSITION_MODIFIED:
                description.append("Posizione modificata: ")
                          .append("SL=")
                          .append(position.getStopLoss())
                          .append(", TP=")
                          .append(position.getTakeProfit());
                break;
                
            case POSITION_GROUPED:
                description.append("Posizione aggiunta al gruppo: ")
                          .append(position.getGroupId());
                break;
                
            case POSITION_PROFIT_REACHED:
                description.append("Profitto raggiunto: ")
                          .append(position.getProfit())
                          .append(" (")
                          .append(position.getDistanceInPips())
                          .append(" pips)");
                break;
                
            case POSITION_LOSS_REACHED:
                description.append("Perdita raggiunta: ")
                          .append(position.getProfit())
                          .append(" (")
                          .append(position.getDistanceInPips())
                          .append(" pips)");
                break;
                
            case TRAILING_STOP_UPDATED:
                description.append("Trailing stop aggiornato: ")
                          .append("SL=")
                          .append(position.getStopLoss());
                break;
                
            default:
                description.append("Evento posizione: ")
                          .append(position.getTicket());
                break;
        }
        
        if (additionalInfo != null && !additionalInfo.isEmpty()) {
            description.append(" - ").append(additionalInfo);
        }
        
        return description.toString();
    }
}
