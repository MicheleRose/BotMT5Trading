package main.java.com.mt5bot.trading.manager;

import com.mt5bot.client.CommandExecutionException;
import com.mt5bot.client.MT5Commands;
import com.mt5bot.trading.event.PositionEvent;
import com.mt5bot.trading.event.TradingEvent.EventType;
import com.mt5bot.trading.event.TradingEventManager;
import com.mt5bot.trading.model.Position;
import com.mt5bot.trading.model.Position.PositionType;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.locks.ReadWriteLock;
import java.util.concurrent.locks.ReentrantReadWriteLock;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.stream.Collectors;

/**
 * Gestore delle posizioni di trading.
 * Implementa il tracking delle posizioni aperte, il raggruppamento delle posizioni correlate,
 * il calcolo del profitto aggregato e la verifica dei limiti di operazioni concorrenti.
 */
public class PositionManager {
    
    private static final Logger LOGGER = Logger.getLogger(PositionManager.class.getName());
    
    private final MT5Commands mt5Commands;
    private final TradingEventManager eventManager;
    
    // Mappa delle posizioni aperte (ticket -> Position)
    private final Map<Long, Position> positions = new ConcurrentHashMap<>();
    
    // Mappa dei gruppi di posizioni (groupId -> List<Position>)
    private final Map<String, List<Long>> positionGroups = new ConcurrentHashMap<>();
    
    // Lock per le operazioni di lettura/scrittura
    private final ReadWriteLock lock = new ReentrantReadWriteLock();
    
    // Limiti di operazioni concorrenti
    private int maxConcurrentPositions = 20;
    private int maxConcurrentPositionsPerSymbol = 10;
    private int maxConcurrentPositionsPerGroup = 20;
    
    /**
     * Costruttore per il gestore delle posizioni.
     * 
     * @param mt5Commands Il client MT5 per l'esecuzione dei comandi
     * @param eventManager Il gestore degli eventi di trading
     */
    public PositionManager(MT5Commands mt5Commands, TradingEventManager eventManager) {
        this.mt5Commands = mt5Commands;
        this.eventManager = eventManager;
    }
    
    /**
     * Aggiorna le posizioni aperte dal sistema MT5.
     * 
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    public void updatePositions() throws CommandExecutionException {
        try {
            Map<String, Object> result = mt5Commands.getPositions(null);
            
            if (result.containsKey("positions")) {
                @SuppressWarnings("unchecked")
                List<Map<String, Object>> positionsList = (List<Map<String, Object>>) result.get("positions");
                
                // Aggiorna le posizioni
                lock.writeLock().lock();
                try {
                    // Crea una copia delle posizioni correnti per verificare quali sono state chiuse
                    Map<Long, Position> currentPositions = new HashMap<>(positions);
                    
                    for (Map<String, Object> positionData : positionsList) {
                        long ticket = ((Number) positionData.get("ticket")).longValue();
                        String symbol = (String) positionData.get("symbol");
                        String typeStr = (String) positionData.get("type");
                        PositionType type = typeStr.equalsIgnoreCase("buy") ? PositionType.BUY : PositionType.SELL;
                        double volume = ((Number) positionData.get("volume")).doubleValue();
                        double openPrice = ((Number) positionData.get("open_price")).doubleValue();
                        double stopLoss = positionData.containsKey("sl") ? ((Number) positionData.get("sl")).doubleValue() : 0.0;
                        double takeProfit = positionData.containsKey("tp") ? ((Number) positionData.get("tp")).doubleValue() : 0.0;
                        String comment = positionData.containsKey("comment") ? (String) positionData.get("comment") : "";
                        int magicNumber = positionData.containsKey("magic") ? ((Number) positionData.get("magic")).intValue() : 0;
                        double currentPrice = ((Number) positionData.get("current_price")).doubleValue();
                        double profit = ((Number) positionData.get("profit")).doubleValue();
                        
                        // Verifica se la posizione esiste già
                        if (positions.containsKey(ticket)) {
                            // Aggiorna la posizione esistente
                            Position position = positions.get(ticket);
                            position.updatePrice(currentPrice);
                            position.updateLevels(stopLoss, takeProfit);
                            
                            // Rimuovi dalla mappa delle posizioni correnti
                            currentPositions.remove(ticket);
                        } else {
                            // Crea una nuova posizione
                            Position position = new Position(
                                ticket, symbol, type, volume, openPrice, LocalDateTime.now(),
                                stopLoss, takeProfit, comment, magicNumber
                            );
                            position.updatePrice(currentPrice);
                            
                            // Aggiungi la posizione alla mappa
                            positions.put(ticket, position);
                            
                            // Notifica l'evento di apertura della posizione
                            eventManager.notifyEvent(new PositionEvent(EventType.POSITION_OPENED, position));
                        }
                    }
                    
                    // Verifica le posizioni chiuse
                    for (Position closedPosition : currentPositions.values()) {
                        // Rimuovi la posizione dalla mappa
                        positions.remove(closedPosition.getTicket());
                        
                        // Rimuovi la posizione dai gruppi
                        if (closedPosition.getGroupId() != null) {
                            removePositionFromGroup(closedPosition.getTicket(), closedPosition.getGroupId());
                        }
                        
                        // Notifica l'evento di chiusura della posizione
                        eventManager.notifyEvent(new PositionEvent(EventType.POSITION_CLOSED, closedPosition));
                    }
                } finally {
                    lock.writeLock().unlock();
                }
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante l'aggiornamento delle posizioni", e);
            eventManager.notifyError(null, "Errore durante l'aggiornamento delle posizioni", "PositionManager", e);
            throw e;
        }
    }
    
    /**
     * Restituisce tutte le posizioni aperte.
     * 
     * @return La lista delle posizioni aperte
     */
    public List<Position> getAllPositions() {
        lock.readLock().lock();
        try {
            return new ArrayList<>(positions.values());
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Restituisce le posizioni aperte per un simbolo.
     * 
     * @param symbol Il simbolo
     * @return La lista delle posizioni aperte per il simbolo
     */
    public List<Position> getPositionsBySymbol(String symbol) {
        if (symbol == null) {
            return Collections.emptyList();
        }
        
        lock.readLock().lock();
        try {
            return positions.values().stream()
                    .filter(p -> symbol.equals(p.getSymbol()))
                    .collect(Collectors.toList());
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Restituisce le posizioni aperte per un gruppo.
     * 
     * @param groupId L'ID del gruppo
     * @return La lista delle posizioni aperte per il gruppo
     */
    public List<Position> getPositionsByGroup(String groupId) {
        if (groupId == null) {
            return Collections.emptyList();
        }
        
        lock.readLock().lock();
        try {
            List<Long> tickets = positionGroups.getOrDefault(groupId, Collections.emptyList());
            return tickets.stream()
                    .map(positions::get)
                    .filter(p -> p != null)
                    .collect(Collectors.toList());
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Restituisce una posizione per ticket.
     * 
     * @param ticket Il ticket della posizione
     * @return La posizione o null se non esiste
     */
    public Position getPosition(long ticket) {
        lock.readLock().lock();
        try {
            return positions.get(ticket);
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Crea un nuovo gruppo di posizioni.
     * 
     * @param symbol Il simbolo del gruppo
     * @return L'ID del gruppo creato
     */
    public String createGroup(String symbol) {
        String groupId = symbol + "_" + UUID.randomUUID().toString().substring(0, 8);
        
        lock.writeLock().lock();
        try {
            positionGroups.put(groupId, new ArrayList<>());
        } finally {
            lock.writeLock().unlock();
        }
        
        LOGGER.log(Level.INFO, "Creato nuovo gruppo: {0}", groupId);
        return groupId;
    }
    
    /**
     * Aggiunge una posizione a un gruppo.
     * 
     * @param ticket Il ticket della posizione
     * @param groupId L'ID del gruppo
     * @return true se la posizione è stata aggiunta, false altrimenti
     */
    public boolean addPositionToGroup(long ticket, String groupId) {
        if (groupId == null) {
            return false;
        }
        
        lock.writeLock().lock();
        try {
            Position position = positions.get(ticket);
            if (position == null) {
                return false;
            }
            
            // Verifica se il gruppo esiste
            if (!positionGroups.containsKey(groupId)) {
                positionGroups.put(groupId, new ArrayList<>());
            }
            
            // Aggiungi la posizione al gruppo
            List<Long> groupPositions = positionGroups.get(groupId);
            if (!groupPositions.contains(ticket)) {
                groupPositions.add(ticket);
                position.setGroupId(groupId);
                
                // Notifica l'evento di raggruppamento della posizione
                eventManager.notifyEvent(new PositionEvent(EventType.POSITION_GROUPED, position));
                
                return true;
            }
            
            return false;
        } finally {
            lock.writeLock().unlock();
        }
    }
    
    /**
     * Rimuove una posizione da un gruppo.
     * 
     * @param ticket Il ticket della posizione
     * @param groupId L'ID del gruppo
     * @return true se la posizione è stata rimossa, false altrimenti
     */
    public boolean removePositionFromGroup(long ticket, String groupId) {
        if (groupId == null) {
            return false;
        }
        
        lock.writeLock().lock();
        try {
            // Verifica se il gruppo esiste
            if (!positionGroups.containsKey(groupId)) {
                return false;
            }
            
            // Rimuovi la posizione dal gruppo
            List<Long> groupPositions = positionGroups.get(groupId);
            boolean removed = groupPositions.remove(ticket);
            
            // Se il gruppo è vuoto, rimuovilo
            if (groupPositions.isEmpty()) {
                positionGroups.remove(groupId);
            }
            
            // Aggiorna la posizione
            Position position = positions.get(ticket);
            if (position != null && groupId.equals(position.getGroupId())) {
                position.setGroupId(null);
            }
            
            return removed;
        } finally {
            lock.writeLock().unlock();
        }
    }
    
    /**
     * Calcola il profitto totale di tutte le posizioni aperte.
     * 
     * @return Il profitto totale
     */
    public double getTotalProfit() {
        lock.readLock().lock();
        try {
            return positions.values().stream()
                    .mapToDouble(Position::getProfit)
                    .sum();
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Calcola il profitto totale delle posizioni aperte per un simbolo.
     * 
     * @param symbol Il simbolo
     * @return Il profitto totale per il simbolo
     */
    public double getTotalProfitBySymbol(String symbol) {
        if (symbol == null) {
            return 0.0;
        }
        
        lock.readLock().lock();
        try {
            return positions.values().stream()
                    .filter(p -> symbol.equals(p.getSymbol()))
                    .mapToDouble(Position::getProfit)
                    .sum();
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Calcola il profitto totale delle posizioni aperte per un gruppo.
     * 
     * @param groupId L'ID del gruppo
     * @return Il profitto totale per il gruppo
     */
    public double getTotalProfitByGroup(String groupId) {
        if (groupId == null) {
            return 0.0;
        }
        
        lock.readLock().lock();
        try {
            List<Long> tickets = positionGroups.getOrDefault(groupId, Collections.emptyList());
            return tickets.stream()
                    .map(positions::get)
                    .filter(p -> p != null)
                    .mapToDouble(Position::getProfit)
                    .sum();
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Verifica se è possibile aprire una nuova posizione in base ai limiti configurati.
     * 
     * @param symbol Il simbolo della nuova posizione
     * @param groupId L'ID del gruppo della nuova posizione (può essere null)
     * @return true se è possibile aprire la posizione, false altrimenti
     */
    public boolean canOpenPosition(String symbol, String groupId) {
        lock.readLock().lock();
        try {
            // Verifica il limite totale di posizioni
            if (positions.size() >= maxConcurrentPositions) {
                LOGGER.warning("Limite di posizioni concorrenti raggiunto: " + positions.size() + "/" + maxConcurrentPositions);
                return false;
            }
            
            // Verifica il limite di posizioni per simbolo
            if (symbol != null) {
                long symbolPositions = positions.values().stream()
                        .filter(p -> symbol.equals(p.getSymbol()))
                        .count();
                
                if (symbolPositions >= maxConcurrentPositionsPerSymbol) {
                    LOGGER.warning("Limite di posizioni concorrenti per simbolo raggiunto: " + symbolPositions + "/" + maxConcurrentPositionsPerSymbol);
                    return false;
                }
            }
            
            // Verifica il limite di posizioni per gruppo
            if (groupId != null) {
                List<Long> groupTickets = positionGroups.getOrDefault(groupId, Collections.emptyList());
                
                if (groupTickets.size() >= maxConcurrentPositionsPerGroup) {
                    LOGGER.warning("Limite di posizioni concorrenti per gruppo raggiunto: " + groupTickets.size() + "/" + maxConcurrentPositionsPerGroup);
                    return false;
                }
            }
            
            return true;
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Imposta il limite massimo di posizioni concorrenti.
     * 
     * @param maxConcurrentPositions Il limite massimo di posizioni concorrenti
     */
    public void setMaxConcurrentPositions(int maxConcurrentPositions) {
        this.maxConcurrentPositions = maxConcurrentPositions;
    }
    
    /**
     * Imposta il limite massimo di posizioni concorrenti per simbolo.
     * 
     * @param maxConcurrentPositionsPerSymbol Il limite massimo di posizioni concorrenti per simbolo
     */
    public void setMaxConcurrentPositionsPerSymbol(int maxConcurrentPositionsPerSymbol) {
        this.maxConcurrentPositionsPerSymbol = maxConcurrentPositionsPerSymbol;
    }
    
    /**
     * Imposta il limite massimo di posizioni concorrenti per gruppo.
     * 
     * @param maxConcurrentPositionsPerGroup Il limite massimo di posizioni concorrenti per gruppo
     */
    public void setMaxConcurrentPositionsPerGroup(int maxConcurrentPositionsPerGroup) {
        this.maxConcurrentPositionsPerGroup = maxConcurrentPositionsPerGroup;
    }
    
    /**
     * Restituisce il numero totale di posizioni aperte.
     * 
     * @return Il numero totale di posizioni aperte
     */
    public int getPositionCount() {
        lock.readLock().lock();
        try {
            return positions.size();
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Restituisce il numero di posizioni aperte per un simbolo.
     * 
     * @param symbol Il simbolo
     * @return Il numero di posizioni aperte per il simbolo
     */
    public int getPositionCountBySymbol(String symbol) {
        if (symbol == null) {
            return 0;
        }
        
        lock.readLock().lock();
        try {
            return (int) positions.values().stream()
                    .filter(p -> symbol.equals(p.getSymbol()))
                    .count();
        } finally {
            lock.readLock().unlock();
        }
    }
    
    /**
     * Restituisce il numero di posizioni aperte per un gruppo.
     * 
     * @param groupId L'ID del gruppo
     * @return Il numero di posizioni aperte per il gruppo
     */
    public int getPositionCountByGroup(String groupId) {
        if (groupId == null) {
            return 0;
        }
        
        lock.readLock().lock();
        try {
            List<Long> tickets = positionGroups.getOrDefault(groupId, Collections.emptyList());
            return tickets.size();
        } finally {
            lock.readLock().unlock();
        }
    }
}
