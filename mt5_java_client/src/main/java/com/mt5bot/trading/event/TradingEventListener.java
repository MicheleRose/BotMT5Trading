package main.java.com.mt5bot.trading.event;

/**
 * Interfaccia per il pattern Observer che definisce i metodi per ricevere notifiche
 * sugli eventi di trading.
 */
public interface TradingEventListener {
    
    /**
     * Metodo chiamato quando si verifica un evento di trading.
     * 
     * @param event L'evento di trading
     */
    void onTradingEvent(TradingEvent event);
}
