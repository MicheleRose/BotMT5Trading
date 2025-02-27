package main.java.com.mt5bot.trading.manager;

import com.mt5bot.client.CommandExecutionException;
import com.mt5bot.client.MT5Commands;
import com.mt5bot.trading.event.PositionEvent;
import com.mt5bot.trading.event.TradingEvent.EventType;
import com.mt5bot.trading.event.TradingEventManager;
import com.mt5bot.trading.model.Position;
import com.mt5bot.trading.model.Position.PositionType;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Gestore del trailing stop.
 * Implementa il trailing stop a 30 pips, il monitoraggio delle posizioni in profitto
 * e l'aggiornamento periodico dello stop loss.
 */
public class TrailingManager {
    
    private static final Logger LOGGER = Logger.getLogger(TrailingManager.class.getName());
    
    private final MT5Commands mt5Commands;
    private final PositionManager positionManager;
    private final TradingEventManager eventManager;
    
    // Parametri di configurazione
    private double trailingDistance = 30.0; // Distanza del trailing stop in pips
    private double activationDistance = 15.0; // Distanza di attivazione del trailing stop in pips
    private long updateInterval = 5; // Intervallo di aggiornamento in secondi
    
    // Mappa dei livelli di trailing stop per posizione (ticket -> livello)
    private final Map<Long, Double> trailingLevels = new ConcurrentHashMap<>();
    
    // Scheduler per l'aggiornamento periodico
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
    private boolean isRunning = false;
    
    /**
     * Costruttore per il gestore del trailing stop.
     * 
     * @param mt5Commands Il client MT5 per l'esecuzione dei comandi
     * @param positionManager Il gestore delle posizioni
     * @param eventManager Il gestore degli eventi di trading
     */
    public TrailingManager(MT5Commands mt5Commands, PositionManager positionManager, TradingEventManager eventManager) {
        this.mt5Commands = mt5Commands;
        this.positionManager = positionManager;
        this.eventManager = eventManager;
    }
    
    /**
     * Avvia il monitoraggio del trailing stop.
     */
    public void start() {
        if (!isRunning) {
            isRunning = true;
            
            // Avvia lo scheduler per l'aggiornamento periodico
            scheduler.scheduleAtFixedRate(this::updateTrailingStops, 0, updateInterval, TimeUnit.SECONDS);
            
            LOGGER.info("Monitoraggio del trailing stop avviato");
        }
    }
    
    /**
     * Ferma il monitoraggio del trailing stop.
     */
    public void stop() {
        if (isRunning) {
            isRunning = false;
            
            // Ferma lo scheduler
            scheduler.shutdown();
            try {
                if (!scheduler.awaitTermination(5, TimeUnit.SECONDS)) {
                    scheduler.shutdownNow();
                }
            } catch (InterruptedException e) {
                scheduler.shutdownNow();
                Thread.currentThread().interrupt();
            }
            
            LOGGER.info("Monitoraggio del trailing stop fermato");
        }
    }
    
    /**
     * Aggiorna i trailing stop per tutte le posizioni.
     */
    private void updateTrailingStops() {
        try {
            // Aggiorna le posizioni
            positionManager.updatePositions();
            
            // Ottieni tutte le posizioni
            List<Position> positions = positionManager.getAllPositions();
            
            // Aggiorna i trailing stop per ogni posizione
            for (Position position : positions) {
                try {
                    updateTrailingStop(position);
                } catch (Exception e) {
                    LOGGER.log(Level.WARNING, "Errore durante l'aggiornamento del trailing stop per la posizione " + position.getTicket(), e);
                }
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante l'aggiornamento dei trailing stop", e);
            eventManager.notifyError(null, "Errore durante l'aggiornamento dei trailing stop", "TrailingManager", e);
        }
    }
    
    /**
     * Aggiorna il trailing stop per una posizione.
     * 
     * @param position La posizione
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    private void updateTrailingStop(Position position) throws CommandExecutionException {
        // Verifica se la posizione è in profitto
        if (!position.isInProfit()) {
            return;
        }
        
        // Verifica se la posizione ha raggiunto la distanza di attivazione
        if (!position.hasProfitPips(activationDistance)) {
            return;
        }
        
        // Calcola il nuovo livello di stop loss
        double currentPrice = position.getCurrentPrice();
        double newStopLoss;
        
        if (position.getType() == PositionType.BUY) {
            // Per le posizioni di acquisto, il trailing stop è sotto il prezzo corrente
            newStopLoss = currentPrice - (trailingDistance / 10000.0);
            
            // Verifica se il nuovo stop loss è superiore allo stop loss corrente
            if (newStopLoss <= position.getStopLoss()) {
                return;
            }
        } else {
            // Per le posizioni di vendita, il trailing stop è sopra il prezzo corrente
            newStopLoss = currentPrice + (trailingDistance / 10000.0);
            
            // Verifica se il nuovo stop loss è inferiore allo stop loss corrente
            if (newStopLoss >= position.getStopLoss()) {
                return;
            }
        }
        
        // Verifica se il livello di trailing stop è cambiato
        Double previousLevel = trailingLevels.get(position.getTicket());
        if (previousLevel != null && Math.abs(previousLevel - newStopLoss) < 0.0001) {
            return;
        }
        
        // Aggiorna lo stop loss
        try {
            Map<String, Object> result = mt5Commands.modifyPosition(
                position.getTicket(),
                newStopLoss,
                position.getTakeProfit()
            );
            
            if (result.containsKey("success") && (Boolean) result.get("success")) {
                // Aggiorna il livello di trailing stop
                trailingLevels.put(position.getTicket(), newStopLoss);
                
                // Aggiorna la posizione
                position.updateStopLoss(newStopLoss);
                
                // Notifica l'evento di aggiornamento del trailing stop
                eventManager.notifyEvent(new PositionEvent(
                    EventType.TRAILING_STOP_UPDATED,
                    position,
                    "Trailing stop aggiornato a " + newStopLoss
                ));
                
                LOGGER.log(Level.INFO, "Trailing stop aggiornato per la posizione {0}: {1}",
                        new Object[]{position.getTicket(), newStopLoss});
            } else {
                LOGGER.warning("Errore durante l'aggiornamento del trailing stop: " + result);
            }
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Errore durante l'aggiornamento del trailing stop", e);
            eventManager.notifyError(position.getSymbol(), "Errore durante l'aggiornamento del trailing stop", "TrailingManager", e);
            throw e;
        }
    }
    
    /**
     * Imposta la distanza del trailing stop.
     * 
     * @param trailingDistance La distanza del trailing stop in pips
     */
    public void setTrailingDistance(double trailingDistance) {
        this.trailingDistance = trailingDistance;
    }
    
    /**
     * Imposta la distanza di attivazione del trailing stop.
     * 
     * @param activationDistance La distanza di attivazione del trailing stop in pips
     */
    public void setActivationDistance(double activationDistance) {
        this.activationDistance = activationDistance;
    }
    
    /**
     * Imposta l'intervallo di aggiornamento.
     * 
     * @param updateInterval L'intervallo di aggiornamento in secondi
     */
    public void setUpdateInterval(long updateInterval) {
        this.updateInterval = updateInterval;
    }
    
    /**
     * Restituisce la distanza del trailing stop.
     * 
     * @return La distanza del trailing stop in pips
     */
    public double getTrailingDistance() {
        return trailingDistance;
    }
    
    /**
     * Restituisce la distanza di attivazione del trailing stop.
     * 
     * @return La distanza di attivazione del trailing stop in pips
     */
    public double getActivationDistance() {
        return activationDistance;
    }
    
    /**
     * Restituisce l'intervallo di aggiornamento.
     * 
     * @return L'intervallo di aggiornamento in secondi
     */
    public long getUpdateInterval() {
        return updateInterval;
    }
    
    /**
     * Verifica se il monitoraggio del trailing stop è attivo.
     * 
     * @return true se il monitoraggio è attivo, false altrimenti
     */
    public boolean isRunning() {
        return isRunning;
    }
}
