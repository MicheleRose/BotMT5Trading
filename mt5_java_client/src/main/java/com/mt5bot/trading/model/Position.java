package main.java.com.mt5bot.trading.model;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * Rappresenta una posizione di trading aperta nel sistema MT5.
 */
public class Position {
    
    /**
     * Crea una posizione da una mappa di dati.
     * 
     * @param positionData La mappa di dati della posizione
     * @return La posizione creata
     */
    public static Position fromMap(Map<String, Object> positionData) {
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
        
        // Crea la posizione
        Position position = new Position(
            ticket, symbol, type, volume, openPrice, LocalDateTime.now(),
            stopLoss, takeProfit, comment, magicNumber
        );
        position.updatePrice(currentPrice);
        
        return position;
    }
    
    /**
     * Tipo di posizione (Buy o Sell).
     */
    public enum PositionType {
        BUY, SELL
    }
    
    private final long ticket;
    private final String symbol;
    private final PositionType type;
    private final double volume;
    private final double openPrice;
    private final LocalDateTime openTime;
    private double stopLoss;
    private double takeProfit;
    private final String comment;
    private final int magicNumber;
    private double currentPrice;
    private double profit;
    private String groupId;
    
    /**
     * Costruttore per una posizione.
     * 
     * @param ticket Il numero di ticket della posizione
     * @param symbol Il simbolo della posizione
     * @param type Il tipo di posizione (BUY o SELL)
     * @param volume Il volume della posizione
     * @param openPrice Il prezzo di apertura della posizione
     * @param openTime L'orario di apertura della posizione
     * @param stopLoss Il livello di stop loss della posizione
     * @param takeProfit Il livello di take profit della posizione
     * @param comment Il commento della posizione
     * @param magicNumber Il magic number della posizione
     */
    public Position(long ticket, String symbol, PositionType type, double volume, 
                   double openPrice, LocalDateTime openTime, double stopLoss, 
                   double takeProfit, String comment, int magicNumber) {
        this.ticket = ticket;
        this.symbol = symbol;
        this.type = type;
        this.volume = volume;
        this.openPrice = openPrice;
        this.openTime = openTime;
        this.stopLoss = stopLoss;
        this.takeProfit = takeProfit;
        this.comment = comment;
        this.magicNumber = magicNumber;
        this.currentPrice = openPrice;
        this.profit = 0.0;
        this.groupId = null;
    }
    
    /**
     * Costruttore per una posizione con gruppo predefinito.
     * 
     * @param ticket Il numero di ticket della posizione
     * @param symbol Il simbolo della posizione
     * @param type Il tipo di posizione (BUY o SELL)
     * @param volume Il volume della posizione
     * @param openPrice Il prezzo di apertura della posizione
     * @param openTime L'orario di apertura della posizione
     * @param stopLoss Il livello di stop loss della posizione
     * @param takeProfit Il livello di take profit della posizione
     * @param comment Il commento della posizione
     * @param magicNumber Il magic number della posizione
     * @param groupId L'ID del gruppo a cui appartiene la posizione
     */
    public Position(long ticket, String symbol, PositionType type, double volume, 
                   double openPrice, LocalDateTime openTime, double stopLoss, 
                   double takeProfit, String comment, int magicNumber, String groupId) {
        this(ticket, symbol, type, volume, openPrice, openTime, stopLoss, takeProfit, comment, magicNumber);
        this.groupId = groupId;
    }
    
    /**
     * Aggiorna il prezzo corrente e il profitto della posizione.
     * 
     * @param currentPrice Il prezzo corrente
     * @return Il profitto aggiornato
     */
    public double updatePrice(double currentPrice) {
        this.currentPrice = currentPrice;
        calculateProfit();
        return this.profit;
    }
    
    /**
     * Calcola il profitto della posizione in base al prezzo corrente.
     */
    private void calculateProfit() {
        double priceDifference = 0.0;
        
        if (type == PositionType.BUY) {
            priceDifference = currentPrice - openPrice;
        } else if (type == PositionType.SELL) {
            priceDifference = openPrice - currentPrice;
        }
        
        // Calcolo semplificato del profitto (in realtà dipende dal simbolo e dal broker)
        this.profit = priceDifference * volume * 100000;
    }
    
    /**
     * Aggiorna i livelli di stop loss e take profit della posizione.
     * 
     * @param stopLoss Il nuovo livello di stop loss
     * @param takeProfit Il nuovo livello di take profit
     */
    public void updateLevels(double stopLoss, double takeProfit) {
        this.stopLoss = stopLoss;
        this.takeProfit = takeProfit;
    }
    
    /**
     * Aggiorna solo il livello di stop loss della posizione.
     * 
     * @param stopLoss Il nuovo livello di stop loss
     */
    public void updateStopLoss(double stopLoss) {
        this.stopLoss = stopLoss;
    }
    
    /**
     * Aggiorna solo il livello di take profit della posizione.
     * 
     * @param takeProfit Il nuovo livello di take profit
     */
    public void updateTakeProfit(double takeProfit) {
        this.takeProfit = takeProfit;
    }
    
    /**
     * Imposta l'ID del gruppo a cui appartiene la posizione.
     * 
     * @param groupId L'ID del gruppo
     */
    public void setGroupId(String groupId) {
        this.groupId = groupId;
    }
    
    /**
     * Calcola la distanza in pips tra il prezzo corrente e il prezzo di apertura.
     * 
     * @return La distanza in pips
     */
    public double getDistanceInPips() {
        double priceDifference = 0.0;
        
        if (type == PositionType.BUY) {
            priceDifference = currentPrice - openPrice;
        } else if (type == PositionType.SELL) {
            priceDifference = openPrice - currentPrice;
        }
        
        // Conversione in pips (assumendo 4 decimali per le coppie forex)
        return priceDifference * 10000;
    }
    
    /**
     * Verifica se la posizione è in profitto.
     * 
     * @return true se la posizione è in profitto, false altrimenti
     */
    public boolean isInProfit() {
        return profit > 0;
    }
    
    /**
     * Verifica se la posizione ha raggiunto un determinato livello di profitto in pips.
     * 
     * @param pips Il livello di profitto in pips
     * @return true se la posizione ha raggiunto il livello di profitto, false altrimenti
     */
    public boolean hasProfitPips(double pips) {
        return getDistanceInPips() >= pips;
    }
    
    // Getters
    
    public long getTicket() {
        return ticket;
    }
    
    public String getSymbol() {
        return symbol;
    }
    
    public PositionType getType() {
        return type;
    }
    
    public double getVolume() {
        return volume;
    }
    
    public double getOpenPrice() {
        return openPrice;
    }
    
    public LocalDateTime getOpenTime() {
        return openTime;
    }
    
    public double getStopLoss() {
        return stopLoss;
    }
    
    public double getTakeProfit() {
        return takeProfit;
    }
    
    public String getComment() {
        return comment;
    }
    
    public int getMagicNumber() {
        return magicNumber;
    }
    
    public double getCurrentPrice() {
        return currentPrice;
    }
    
    public double getProfit() {
        return profit;
    }
    
    public String getGroupId() {
        return groupId;
    }
    
    @Override
    public String toString() {
        return "Position{" +
                "ticket=" + ticket +
                ", symbol='" + symbol + '\'' +
                ", type=" + type +
                ", volume=" + volume +
                ", openPrice=" + openPrice +
                ", currentPrice=" + currentPrice +
                ", profit=" + profit +
                ", stopLoss=" + stopLoss +
                ", takeProfit=" + takeProfit +
                ", groupId='" + groupId + '\'' +
                '}';
    }
}
