package test.java.com.mt5bot.mock;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Simulatore MT5 per i test offline.
 * Simula il comportamento di MetaTrader 5 per i test senza una connessione reale.
 */
public class MT5Simulator {
    
    // Singleton
    private static MT5Simulator instance;
    
    // Dati di mercato simulati
    private final Map<String, Map<String, Object>> marketData = new ConcurrentHashMap<>();
    
    // Dati OHLC simulati
    private final Map<String, Map<String, Object>> ohlcData = new ConcurrentHashMap<>();
    
    // Posizioni aperte
    private final Map<Long, Map<String, Object>> positions = new ConcurrentHashMap<>();
    
    // Generatore di ticket
    private final AtomicLong ticketGenerator = new AtomicLong(1);
    
    // Generatore di numeri casuali
    private final Random random = new Random();
    
    /**
     * Costruttore privato per il pattern singleton.
     */
    private MT5Simulator() {
        // Inizializza i dati di mercato simulati
        initializeMarketData();
        
        // Inizializza i dati OHLC simulati
        initializeOHLCData();
    }
    
    /**
     * Ottiene l'istanza singleton del simulatore.
     * 
     * @return L'istanza singleton del simulatore
     */
    public static synchronized MT5Simulator getInstance() {
        if (instance == null) {
            instance = new MT5Simulator();
        }
        return instance;
    }
    
    /**
     * Inizializza i dati di mercato simulati.
     */
    private void initializeMarketData() {
        // EURUSD
        Map<String, Object> eurusd = new HashMap<>();
        eurusd.put("symbol", "EURUSD");
        eurusd.put("bid", 1.1234);
        eurusd.put("ask", 1.1236);
        eurusd.put("spread", 2);
        eurusd.put("time", System.currentTimeMillis());
        marketData.put("EURUSD", eurusd);
        
        // GBPUSD
        Map<String, Object> gbpusd = new HashMap<>();
        gbpusd.put("symbol", "GBPUSD");
        gbpusd.put("bid", 1.3456);
        gbpusd.put("ask", 1.3458);
        gbpusd.put("spread", 2);
        gbpusd.put("time", System.currentTimeMillis());
        marketData.put("GBPUSD", gbpusd);
        
        // USDJPY
        Map<String, Object> usdjpy = new HashMap<>();
        usdjpy.put("symbol", "USDJPY");
        usdjpy.put("bid", 110.45);
        usdjpy.put("ask", 110.47);
        usdjpy.put("spread", 2);
        usdjpy.put("time", System.currentTimeMillis());
        marketData.put("USDJPY", usdjpy);
    }
    
    /**
     * Inizializza i dati OHLC simulati.
     */
    private void initializeOHLCData() {
        // EURUSD M5
        Map<String, Object> eurusdM5 = new HashMap<>();
        eurusdM5.put("symbol", "EURUSD");
        eurusdM5.put("timeframe", "M5");
        eurusdM5.put("ohlc", createOHLCData("EURUSD", 100));
        ohlcData.put("EURUSD_M5", eurusdM5);
        
        // EURUSD M15
        Map<String, Object> eurusdM15 = new HashMap<>();
        eurusdM15.put("symbol", "EURUSD");
        eurusdM15.put("timeframe", "M15");
        eurusdM15.put("ohlc", createOHLCData("EURUSD", 100));
        ohlcData.put("EURUSD_M15", eurusdM15);
        
        // GBPUSD M5
        Map<String, Object> gbpusdM5 = new HashMap<>();
        gbpusdM5.put("symbol", "GBPUSD");
        gbpusdM5.put("timeframe", "M5");
        gbpusdM5.put("ohlc", createOHLCData("GBPUSD", 100));
        ohlcData.put("GBPUSD_M5", gbpusdM5);
    }
    
    /**
     * Crea dati OHLC simulati.
     * 
     * @param symbol Il simbolo
     * @param count Il numero di candele
     * @return I dati OHLC simulati
     */
    private List<Map<String, Object>> createOHLCData(String symbol, int count) {
        List<Map<String, Object>> ohlc = new ArrayList<>();
        
        // Ottieni il prezzo corrente
        Map<String, Object> marketDataForSymbol = marketData.get(symbol);
        double currentPrice = ((Number) marketDataForSymbol.get("bid")).doubleValue();
        
        // Crea le candele
        for (int i = 0; i < count; i++) {
            Map<String, Object> candle = new HashMap<>();
            
            // Calcola il tempo
            long time = System.currentTimeMillis() - (i * 300000); // 5 minuti per candela
            
            // Calcola i prezzi
            double open = currentPrice + (random.nextDouble() * 0.01 - 0.005);
            double high = open + (random.nextDouble() * 0.005);
            double low = open - (random.nextDouble() * 0.005);
            double close = low + (random.nextDouble() * (high - low));
            
            // Calcola il volume
            int volume = 100 + random.nextInt(100);
            
            // Imposta i valori
            candle.put("time", time);
            candle.put("open", open);
            candle.put("high", high);
            candle.put("low", low);
            candle.put("close", close);
            candle.put("volume", volume);
            
            // Aggiungi la candela
            ohlc.add(candle);
            
            // Aggiorna il prezzo corrente
            currentPrice = close;
        }
        
        return ohlc;
    }
    
    /**
     * Ottiene le informazioni sull'account.
     * 
     * @return Le informazioni sull'account
     */
    public Map<String, Object> getAccountInfo() {
        Map<String, Object> accountInfo = new HashMap<>();
        accountInfo.put("success", true);
        accountInfo.put("balance", 10000.0);
        accountInfo.put("equity", 10000.0 + getTotalProfit());
        accountInfo.put("margin", getTotalMargin());
        accountInfo.put("free_margin", 10000.0 + getTotalProfit() - getTotalMargin());
        accountInfo.put("margin_level", getTotalMargin() > 0 ? (10000.0 + getTotalProfit()) / getTotalMargin() * 100.0 : 0.0);
        return accountInfo;
    }
    
    /**
     * Ottiene i dati di mercato per un simbolo.
     * 
     * @param symbol Il simbolo
     * @return I dati di mercato
     */
    public Map<String, Object> getMarketData(String symbol) {
        Map<String, Object> data = marketData.get(symbol);
        if (data == null) {
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("error", "Symbol not found: " + symbol);
            return error;
        }
        
        // Aggiorna i dati di mercato con piccole variazioni casuali
        double bid = ((Number) data.get("bid")).doubleValue();
        double ask = ((Number) data.get("ask")).doubleValue();
        
        bid += (random.nextDouble() * 0.0002 - 0.0001);
        ask = bid + ((Number) data.get("spread")).doubleValue() * 0.0001;
        
        data.put("bid", bid);
        data.put("ask", ask);
        data.put("time", System.currentTimeMillis());
        
        // Aggiungi il flag di successo
        data.put("success", true);
        
        return new HashMap<>(data);
    }
    
    /**
     * Ottiene i dati OHLC per un simbolo e un timeframe.
     * 
     * @param symbol Il simbolo
     * @param timeframe Il timeframe
     * @param count Il numero di candele
     * @return I dati OHLC
     */
    public Map<String, Object> getOHLCData(String symbol, String timeframe, int count) {
        String key = symbol + "_" + timeframe;
        Map<String, Object> data = ohlcData.get(key);
        if (data == null) {
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("error", "OHLC data not found for symbol: " + symbol + ", timeframe: " + timeframe);
            return error;
        }
        
        // Limita il numero di candele
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> ohlc = (List<Map<String, Object>>) data.get("ohlc");
        if (count > 0 && count < ohlc.size()) {
            ohlc = ohlc.subList(0, count);
        }
        
        // Crea una copia dei dati
        Map<String, Object> result = new HashMap<>(data);
        result.put("ohlc", ohlc);
        result.put("success", true);
        
        return result;
    }
    
    /**
     * Apre una posizione di acquisto.
     * 
     * @param symbol Il simbolo
     * @param volume Il volume
     * @param stopLoss Il livello di stop loss
     * @param takeProfit Il livello di take profit
     * @param comment Il commento
     * @param magicNumber Il magic number
     * @return Il risultato dell'operazione
     */
    public Map<String, Object> marketBuy(String symbol, double volume, double stopLoss, double takeProfit, String comment, int magicNumber) {
        // Verifica che il simbolo esista
        Map<String, Object> data = marketData.get(symbol);
        if (data == null) {
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("error", "Symbol not found: " + symbol);
            return error;
        }
        
        // Ottieni il prezzo di apertura
        double openPrice = ((Number) data.get("ask")).doubleValue();
        
        // Genera un nuovo ticket
        long ticket = ticketGenerator.getAndIncrement();
        
        // Crea la posizione
        Map<String, Object> position = new HashMap<>();
        position.put("ticket", ticket);
        position.put("symbol", symbol);
        position.put("type", "buy");
        position.put("volume", volume);
        position.put("open_price", openPrice);
        position.put("open_time", System.currentTimeMillis());
        position.put("sl", stopLoss);
        position.put("tp", takeProfit);
        position.put("comment", comment);
        position.put("magic", magicNumber);
        position.put("profit", 0.0);
        
        // Aggiungi la posizione
        positions.put(ticket, position);
        
        // Crea il risultato
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("ticket", ticket);
        result.put("symbol", symbol);
        result.put("volume", volume);
        result.put("open_price", openPrice);
        
        return result;
    }
    
    /**
     * Apre una posizione di vendita.
     * 
     * @param symbol Il simbolo
     * @param volume Il volume
     * @param stopLoss Il livello di stop loss
     * @param takeProfit Il livello di take profit
     * @param comment Il commento
     * @param magicNumber Il magic number
     * @return Il risultato dell'operazione
     */
    public Map<String, Object> marketSell(String symbol, double volume, double stopLoss, double takeProfit, String comment, int magicNumber) {
        // Verifica che il simbolo esista
        Map<String, Object> data = marketData.get(symbol);
        if (data == null) {
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("error", "Symbol not found: " + symbol);
            return error;
        }
        
        // Ottieni il prezzo di apertura
        double openPrice = ((Number) data.get("bid")).doubleValue();
        
        // Genera un nuovo ticket
        long ticket = ticketGenerator.getAndIncrement();
        
        // Crea la posizione
        Map<String, Object> position = new HashMap<>();
        position.put("ticket", ticket);
        position.put("symbol", symbol);
        position.put("type", "sell");
        position.put("volume", volume);
        position.put("open_price", openPrice);
        position.put("open_time", System.currentTimeMillis());
        position.put("sl", stopLoss);
        position.put("tp", takeProfit);
        position.put("comment", comment);
        position.put("magic", magicNumber);
        position.put("profit", 0.0);
        
        // Aggiungi la posizione
        positions.put(ticket, position);
        
        // Crea il risultato
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("ticket", ticket);
        result.put("symbol", symbol);
        result.put("volume", volume);
        result.put("open_price", openPrice);
        
        return result;
    }
    
    /**
     * Modifica una posizione.
     * 
     * @param ticket Il ticket della posizione
     * @param stopLoss Il nuovo livello di stop loss
     * @param takeProfit Il nuovo livello di take profit
     * @return Il risultato dell'operazione
     */
    public Map<String, Object> modifyPosition(long ticket, double stopLoss, double takeProfit) {
        // Verifica che la posizione esista
        Map<String, Object> position = positions.get(ticket);
        if (position == null) {
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("error", "Position not found: " + ticket);
            return error;
        }
        
        // Modifica la posizione
        position.put("sl", stopLoss);
        position.put("tp", takeProfit);
        
        // Crea il risultato
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("ticket", ticket);
        result.put("sl", stopLoss);
        result.put("tp", takeProfit);
        
        return result;
    }
    
    /**
     * Chiude una posizione.
     * 
     * @param ticket Il ticket della posizione
     * @return Il risultato dell'operazione
     */
    public Map<String, Object> closePosition(long ticket) {
        // Verifica che la posizione esista
        Map<String, Object> position = positions.get(ticket);
        if (position == null) {
            Map<String, Object> error = new HashMap<>();
            error.put("success", false);
            error.put("error", "Position not found: " + ticket);
            return error;
        }
        
        // Ottieni il simbolo e il tipo
        String symbol = (String) position.get("symbol");
        String type = (String) position.get("type");
        
        // Ottieni il prezzo di chiusura
        Map<String, Object> data = marketData.get(symbol);
        double closePrice = type.equals("buy") ? ((Number) data.get("bid")).doubleValue() : ((Number) data.get("ask")).doubleValue();
        
        // Calcola il profitto
        double openPrice = ((Number) position.get("open_price")).doubleValue();
        double volume = ((Number) position.get("volume")).doubleValue();
        double profit = type.equals("buy") ? (closePrice - openPrice) * volume * 100000 : (openPrice - closePrice) * volume * 100000;
        
        // Rimuovi la posizione
        positions.remove(ticket);
        
        // Crea il risultato
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("ticket", ticket);
        result.put("close_price", closePrice);
        result.put("profit", profit);
        
        return result;
    }
    
    /**
     * Chiude tutte le posizioni.
     * 
     * @return Il risultato dell'operazione
     */
    public Map<String, Object> closeAllPositions() {
        // Crea il risultato
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("closed", new ArrayList<>());
        
        // Chiudi tutte le posizioni
        for (Long ticket : new ArrayList<>(positions.keySet())) {
            Map<String, Object> closeResult = closePosition(ticket);
            if ((Boolean) closeResult.get("success")) {
                ((List<Map<String, Object>>) result.get("closed")).add(closeResult);
            }
        }
        
        return result;
    }
    
    /**
     * Ottiene le posizioni aperte.
     * 
     * @return Le posizioni aperte
     */
    public Map<String, Object> getPositions() {
        // Aggiorna i profitti
        updateProfits();
        
        // Crea il risultato
        Map<String, Object> result = new HashMap<>();
        result.put("success", true);
        result.put("positions", new ArrayList<>(positions.values()));
        
        return result;
    }
    
    /**
     * Aggiorna i profitti delle posizioni aperte.
     */
    private void updateProfits() {
        for (Map<String, Object> position : positions.values()) {
            // Ottieni il simbolo e il tipo
            String symbol = (String) position.get("symbol");
            String type = (String) position.get("type");
            
            // Ottieni il prezzo corrente
            Map<String, Object> data = marketData.get(symbol);
            double currentPrice = type.equals("buy") ? ((Number) data.get("bid")).doubleValue() : ((Number) data.get("ask")).doubleValue();
            
            // Calcola il profitto
            double openPrice = ((Number) position.get("open_price")).doubleValue();
            double volume = ((Number) position.get("volume")).doubleValue();
            double profit = type.equals("buy") ? (currentPrice - openPrice) * volume * 100000 : (openPrice - currentPrice) * volume * 100000;
            
            // Aggiorna il profitto
            position.put("profit", profit);
            position.put("current_price", currentPrice);
        }
    }
    
    /**
     * Ottiene il profitto totale.
     * 
     * @return Il profitto totale
     */
    private double getTotalProfit() {
        updateProfits();
        
        double totalProfit = 0.0;
        for (Map<String, Object> position : positions.values()) {
            totalProfit += ((Number) position.get("profit")).doubleValue();
        }
        
        return totalProfit;
    }
    
    /**
     * Ottiene il margine totale.
     * 
     * @return Il margine totale
     */
    private double getTotalMargin() {
        double totalMargin = 0.0;
        for (Map<String, Object> position : positions.values()) {
            double volume = ((Number) position.get("volume")).doubleValue();
            totalMargin += volume * 1000.0; // Margine semplificato
        }
        
        return totalMargin;
    }
}
