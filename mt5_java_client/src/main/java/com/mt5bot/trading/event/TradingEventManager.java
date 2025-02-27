package main.java.com.mt5bot.trading.event;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Gestore degli eventi di trading.
 * Implementa il pattern Observer per notificare gli eventi ai listener registrati.
 */
public class TradingEventManager {
    
    private static final Logger LOGGER = Logger.getLogger(TradingEventManager.class.getName());
    
    private final List<TradingEventListener> listeners = new CopyOnWriteArrayList<>();
    
    /**
     * Registra un listener per gli eventi di trading.
     * 
     * @param listener Il listener da registrare
     */
    public void addListener(TradingEventListener listener) {
        if (listener != null && !listeners.contains(listener)) {
            listeners.add(listener);
            LOGGER.fine("Listener registrato: " + listener.getClass().getName());
        }
    }
    
    /**
     * Rimuove un listener per gli eventi di trading.
     * 
     * @param listener Il listener da rimuovere
     */
    public void removeListener(TradingEventListener listener) {
        if (listener != null) {
            listeners.remove(listener);
            LOGGER.fine("Listener rimosso: " + listener.getClass().getName());
        }
    }
    
    /**
     * Rimuove tutti i listener registrati.
     */
    public void removeAllListeners() {
        listeners.clear();
        LOGGER.fine("Tutti i listener sono stati rimossi");
    }
    
    /**
     * Notifica un evento a tutti i listener registrati.
     * 
     * @param event L'evento da notificare
     */
    public void notifyEvent(TradingEvent event) {
        if (event != null) {
            LOGGER.log(Level.INFO, "Evento: {0}", event);
            
            for (TradingEventListener listener : listeners) {
                try {
                    listener.onTradingEvent(event);
                } catch (Exception e) {
                    LOGGER.log(Level.WARNING, "Errore durante la notifica dell'evento al listener: " + listener.getClass().getName(), e);
                }
            }
        }
    }
    
    /**
     * Crea e notifica un evento di errore.
     * 
     * @param symbol Il simbolo associato all'errore (può essere null)
     * @param errorMessage Il messaggio di errore
     * @param source La sorgente dell'errore
     */
    public void notifyError(String symbol, String errorMessage, String source) {
        notifyEvent(new ErrorEvent(symbol, errorMessage, source));
    }
    
    /**
     * Crea e notifica un evento di errore con eccezione.
     * 
     * @param symbol Il simbolo associato all'errore (può essere null)
     * @param errorMessage Il messaggio di errore
     * @param source La sorgente dell'errore
     * @param exception L'eccezione che ha causato l'errore
     */
    public void notifyError(String symbol, String errorMessage, String source, Throwable exception) {
        notifyEvent(new ErrorEvent(symbol, errorMessage, source, exception));
    }
}
