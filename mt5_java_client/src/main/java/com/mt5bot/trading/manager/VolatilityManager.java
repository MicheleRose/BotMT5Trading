package main.java.com.mt5bot.trading.manager;

import com.mt5bot.client.CommandExecutionException;
import com.mt5bot.client.MT5Commands;
import com.mt5bot.trading.event.StrategyEvent;
import com.mt5bot.trading.event.TradingEvent.EventType;
import com.mt5bot.trading.event.TradingEventManager;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Gestore della volatilità.
 * Implementa l'analisi ATR per la categorizzazione della volatilità,
 * il calcolo dinamico di SL/TP e il mapping delle categorie di volatilità a valori pip.
 */
public class VolatilityManager {
    
    private static final Logger LOGGER = Logger.getLogger(VolatilityManager.class.getName());
    
    /**
     * Categoria di volatilità.
     */
    public enum VolatilityCategory {
        LOW, MEDIUM, HIGH
    }
    
    private final MT5Commands mt5Commands;
    private final TradingEventManager eventManager;
    
    // Mappa dei valori ATR per simbolo
    private final Map<String, Double> atrValues = new ConcurrentHashMap<>();
    
    // Mappa delle categorie di volatilità per simbolo
    private final Map<String, VolatilityCategory> volatilityCategories = new ConcurrentHashMap<>();
    
    // Parametri di configurazione
    private int atrPeriod = 14;
    private String atrTimeframe = "H1";
    
    // Soglie per la categorizzazione della volatilità (in pips)
    private double lowVolatilityThreshold = 30.0;
    private double highVolatilityThreshold = 60.0;
    
    // Moltiplicatori ATR per SL/TP
    private double slAtrMultiplier = 1.5;
    private double tpAtrMultiplier = 2.0;
    
    // Valori pip per categoria di volatilità
    private final Map<VolatilityCategory, Integer> slPipValues = new HashMap<>();
    private final Map<VolatilityCategory, Integer> tpPipValues = new HashMap<>();
    
    /**
     * Costruttore per il gestore della volatilità.
     * 
     * @param mt5Commands Il client MT5 per l'esecuzione dei comandi
     * @param eventManager Il gestore degli eventi di trading
     */
    public VolatilityManager(MT5Commands mt5Commands, TradingEventManager eventManager) {
        this.mt5Commands = mt5Commands;
        this.eventManager = eventManager;
        
        // Inizializza i valori pip per categoria di volatilità
        slPipValues.put(VolatilityCategory.LOW, 30);
        slPipValues.put(VolatilityCategory.MEDIUM, 45);
        slPipValues.put(VolatilityCategory.HIGH, 75);
        
        tpPipValues.put(VolatilityCategory.LOW, 40);
        tpPipValues.put(VolatilityCategory.MEDIUM, 60);
        tpPipValues.put(VolatilityCategory.HIGH, 100);
    }
    
    /**
     * Aggiorna il valore ATR per un simbolo.
     * 
     * @param symbol Il simbolo
     * @return Il valore ATR aggiornato
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    public double updateAtr(String symbol) throws CommandExecutionException {
        try {
            Map<String, Object> result = mt5Commands.calculateVolatility(symbol, atrTimeframe, atrPeriod);
            
            if (result.containsKey("volatility")) {
                double atr = ((Number) result.get("volatility")).doubleValue();
                double atrPips = atr * 10000; // Converti in pips (assumendo 4 decimali per le coppie forex)
                
                // Aggiorna il valore ATR
                atrValues.put(symbol, atrPips);
                
                // Aggiorna la categoria di volatilità
                VolatilityCategory oldCategory = volatilityCategories.get(symbol);
                VolatilityCategory newCategory = categorizeVolatility(atrPips);
                
                if (oldCategory != newCategory) {
                    volatilityCategories.put(symbol, newCategory);
                    
                    // Notifica l'evento di cambio categoria di volatilità
                    eventManager.notifyEvent(new StrategyEvent(
                        EventType.VOLATILITY_CHANGED,
                        symbol,
                        "VolatilityManager",
                        "Categoria di volatilità cambiata da " + oldCategory + " a " + newCategory + " (ATR: " + atrPips + " pips)"
                    ));
                }
                
                LOGGER.log(Level.INFO, "ATR aggiornato per {0}: {1} pips (categoria: {2})",
                        new Object[]{symbol, atrPips, newCategory});
                
                return atrPips;
            } else {
                LOGGER.warning("Errore durante il calcolo dell'ATR: " + result);
                return 0.0;
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante l'aggiornamento dell'ATR", e);
            eventManager.notifyError(symbol, "Errore durante l'aggiornamento dell'ATR", "VolatilityManager", e);
            throw e;
        }
    }
    
    /**
     * Categorizza la volatilità in base al valore ATR.
     * 
     * @param atrPips Il valore ATR in pips
     * @return La categoria di volatilità
     */
    private VolatilityCategory categorizeVolatility(double atrPips) {
        if (atrPips < lowVolatilityThreshold) {
            return VolatilityCategory.LOW;
        } else if (atrPips < highVolatilityThreshold) {
            return VolatilityCategory.MEDIUM;
        } else {
            return VolatilityCategory.HIGH;
        }
    }
    
    /**
     * Restituisce la categoria di volatilità per un simbolo.
     * 
     * @param symbol Il simbolo
     * @return La categoria di volatilità
     */
    public VolatilityCategory getVolatilityCategory(String symbol) {
        return volatilityCategories.getOrDefault(symbol, VolatilityCategory.MEDIUM);
    }
    
    /**
     * Restituisce il valore ATR per un simbolo.
     * 
     * @param symbol Il simbolo
     * @return Il valore ATR in pips
     */
    public double getAtrPips(String symbol) {
        return atrValues.getOrDefault(symbol, 0.0);
    }
    
    /**
     * Calcola il livello di stop loss in base alla volatilità.
     * 
     * @param symbol Il simbolo
     * @param entryPrice Il prezzo di entrata
     * @param isBuy true se è una posizione di acquisto, false se è una posizione di vendita
     * @return Il livello di stop loss
     */
    public double calculateStopLoss(String symbol, double entryPrice, boolean isBuy) {
        double atrPips = getAtrPips(symbol);
        VolatilityCategory category = getVolatilityCategory(symbol);
        
        // Usa il valore ATR se disponibile, altrimenti usa il valore predefinito per la categoria
        double slPips = (atrPips > 0) ? (atrPips * slAtrMultiplier) : slPipValues.get(category);
        
        // Converti pips in prezzo (assumendo 4 decimali per le coppie forex)
        double slDistance = slPips / 10000.0;
        
        // Calcola il livello di stop loss
        return isBuy ? (entryPrice - slDistance) : (entryPrice + slDistance);
    }
    
    /**
     * Calcola il livello di take profit in base alla volatilità.
     * 
     * @param symbol Il simbolo
     * @param entryPrice Il prezzo di entrata
     * @param isBuy true se è una posizione di acquisto, false se è una posizione di vendita
     * @return Il livello di take profit
     */
    public double calculateTakeProfit(String symbol, double entryPrice, boolean isBuy) {
        double atrPips = getAtrPips(symbol);
        VolatilityCategory category = getVolatilityCategory(symbol);
        
        // Usa il valore ATR se disponibile, altrimenti usa il valore predefinito per la categoria
        double tpPips = (atrPips > 0) ? (atrPips * tpAtrMultiplier) : tpPipValues.get(category);
        
        // Converti pips in prezzo (assumendo 4 decimali per le coppie forex)
        double tpDistance = tpPips / 10000.0;
        
        // Calcola il livello di take profit
        return isBuy ? (entryPrice + tpDistance) : (entryPrice - tpDistance);
    }
    
    /**
     * Restituisce il valore di stop loss in pips per una categoria di volatilità.
     * 
     * @param category La categoria di volatilità
     * @return Il valore di stop loss in pips
     */
    public int getSlPips(VolatilityCategory category) {
        return slPipValues.get(category);
    }
    
    /**
     * Restituisce il valore di take profit in pips per una categoria di volatilità.
     * 
     * @param category La categoria di volatilità
     * @return Il valore di take profit in pips
     */
    public int getTpPips(VolatilityCategory category) {
        return tpPipValues.get(category);
    }
    
    /**
     * Imposta il periodo ATR.
     * 
     * @param atrPeriod Il periodo ATR
     */
    public void setAtrPeriod(int atrPeriod) {
        this.atrPeriod = atrPeriod;
    }
    
    /**
     * Imposta il timeframe ATR.
     * 
     * @param atrTimeframe Il timeframe ATR
     */
    public void setAtrTimeframe(String atrTimeframe) {
        this.atrTimeframe = atrTimeframe;
    }
    
    /**
     * Imposta la soglia di volatilità bassa.
     * 
     * @param lowVolatilityThreshold La soglia di volatilità bassa in pips
     */
    public void setLowVolatilityThreshold(double lowVolatilityThreshold) {
        this.lowVolatilityThreshold = lowVolatilityThreshold;
    }
    
    /**
     * Imposta la soglia di volatilità alta.
     * 
     * @param highVolatilityThreshold La soglia di volatilità alta in pips
     */
    public void setHighVolatilityThreshold(double highVolatilityThreshold) {
        this.highVolatilityThreshold = highVolatilityThreshold;
    }
    
    /**
     * Imposta il moltiplicatore ATR per lo stop loss.
     * 
     * @param slAtrMultiplier Il moltiplicatore ATR per lo stop loss
     */
    public void setSlAtrMultiplier(double slAtrMultiplier) {
        this.slAtrMultiplier = slAtrMultiplier;
    }
    
    /**
     * Imposta il moltiplicatore ATR per il take profit.
     * 
     * @param tpAtrMultiplier Il moltiplicatore ATR per il take profit
     */
    public void setTpAtrMultiplier(double tpAtrMultiplier) {
        this.tpAtrMultiplier = tpAtrMultiplier;
    }
    
    /**
     * Imposta il valore di stop loss in pips per una categoria di volatilità.
     * 
     * @param category La categoria di volatilità
     * @param pips Il valore di stop loss in pips
     */
    public void setSlPips(VolatilityCategory category, int pips) {
        slPipValues.put(category, pips);
    }
    
    /**
     * Imposta il valore di take profit in pips per una categoria di volatilità.
     * 
     * @param category La categoria di volatilità
     * @param pips Il valore di take profit in pips
     */
    public void setTpPips(VolatilityCategory category, int pips) {
        tpPipValues.put(category, pips);
    }
}
