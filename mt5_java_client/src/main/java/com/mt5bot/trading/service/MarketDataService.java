package main.java.com.mt5bot.trading.service;

import com.mt5bot.client.CommandExecutionException;
import com.mt5bot.client.MT5Commands;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Servizio per la gestione dei dati di mercato.
 * Implementa la cache dei dati di mercato e l'aggiornamento periodico degli indicatori.
 */
public class MarketDataService {
    
    private static final Logger LOGGER = Logger.getLogger(MarketDataService.class.getName());
    
    // Istanza singleton
    private static MarketDataService instance;
    
    // Client MT5
    private final MT5Commands mt5Commands;
    
    // Configurazione
    private final Properties config;
    
    // Cache dei dati di mercato
    private final Map<String, Map<String, Object>> marketDataCache = new ConcurrentHashMap<>();
    
    // Cache dei dati OHLC
    private final Map<String, Map<String, Object>> ohlcDataCache = new ConcurrentHashMap<>();
    
    // Timestamp dell'ultimo aggiornamento
    private final Map<String, LocalDateTime> lastUpdateTime = new ConcurrentHashMap<>();
    
    // Scheduler per l'aggiornamento periodico
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(2);
    
    // Stato del servizio
    private final AtomicBoolean running = new AtomicBoolean(false);
    
    /**
     * Costruttore privato per il pattern singleton.
     * 
     * @param mt5Commands Il client MT5
     * @param config La configurazione
     */
    private MarketDataService(MT5Commands mt5Commands, Properties config) {
        this.mt5Commands = mt5Commands;
        this.config = config;
    }
    
    /**
     * Ottiene l'istanza singleton del servizio.
     * 
     * @param mt5Commands Il client MT5
     * @param config La configurazione
     * @return L'istanza singleton del servizio
     */
    public static synchronized MarketDataService getInstance(MT5Commands mt5Commands, Properties config) {
        if (instance == null) {
            instance = new MarketDataService(mt5Commands, config);
        }
        return instance;
    }
    
    /**
     * Avvia il servizio.
     */
    public void start() {
        if (running.compareAndSet(false, true)) {
            LOGGER.info("Avvio del servizio MarketDataService...");
            
            // Avvia lo scheduler per l'aggiornamento periodico dei dati di mercato
            long marketDataUpdateIntervalMs = Long.parseLong(
                    config.getProperty("marketData.updateIntervalMs", "1000"));
            
            scheduler.scheduleAtFixedRate(
                    this::updateMarketData,
                    0,
                    marketDataUpdateIntervalMs,
                    TimeUnit.MILLISECONDS);
            
            // Avvia lo scheduler per l'aggiornamento periodico dei dati OHLC
            long ohlcDataUpdateIntervalMs = Long.parseLong(
                    config.getProperty("marketData.ohlcUpdateIntervalMs", "60000"));
            
            scheduler.scheduleAtFixedRate(
                    this::updateOHLCData,
                    0,
                    ohlcDataUpdateIntervalMs,
                    TimeUnit.MILLISECONDS);
            
            LOGGER.info("Servizio MarketDataService avviato con successo.");
        } else {
            LOGGER.warning("Il servizio MarketDataService è già in esecuzione.");
        }
    }
    
    /**
     * Ferma il servizio.
     */
    public void stop() {
        if (running.compareAndSet(true, false)) {
            LOGGER.info("Arresto del servizio MarketDataService...");
            
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
            
            // Pulisci le cache
            marketDataCache.clear();
            ohlcDataCache.clear();
            lastUpdateTime.clear();
            
            LOGGER.info("Servizio MarketDataService arrestato con successo.");
        } else {
            LOGGER.warning("Il servizio MarketDataService non è in esecuzione.");
        }
    }
    
    /**
     * Aggiorna i dati di mercato per tutti i simboli configurati.
     */
    private void updateMarketData() {
        if (!running.get()) {
            return;
        }
        
        try {
            // Ottieni i simboli configurati
            String[] symbols = config.getProperty("marketData.symbols", "EURUSD,GBPUSD,USDJPY").split(",");
            
            for (String symbol : symbols) {
                try {
                    // Aggiorna i dati di mercato per il simbolo
                    updateMarketDataForSymbol(symbol.trim());
                } catch (Exception e) {
                    LOGGER.log(Level.WARNING, "Errore durante l'aggiornamento dei dati di mercato per il simbolo: " + symbol, e);
                }
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante l'aggiornamento dei dati di mercato", e);
        }
    }
    
    /**
     * Aggiorna i dati di mercato per un simbolo specifico.
     * 
     * @param symbol Il simbolo
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    private void updateMarketDataForSymbol(String symbol) throws CommandExecutionException {
        // Ottieni i dati di mercato dal client MT5
        Map<String, Object> marketData = mt5Commands.getMarketData(symbol);
        
        if (marketData.containsKey("success") && (Boolean) marketData.get("success")) {
            // Aggiorna la cache
            marketDataCache.put(symbol, marketData);
            lastUpdateTime.put(symbol, LocalDateTime.now());
            
            LOGGER.fine("Dati di mercato aggiornati per il simbolo: " + symbol);
        } else {
            LOGGER.warning("Errore durante l'ottenimento dei dati di mercato per il simbolo: " + symbol);
        }
    }
    
    /**
     * Aggiorna i dati OHLC per tutti i simboli configurati.
     */
    private void updateOHLCData() {
        if (!running.get()) {
            return;
        }
        
        try {
            // Ottieni i simboli configurati
            String[] symbols = config.getProperty("marketData.symbols", "EURUSD,GBPUSD,USDJPY").split(",");
            
            for (String symbol : symbols) {
                try {
                    // Aggiorna i dati OHLC per il simbolo
                    updateOHLCDataForSymbol(symbol.trim());
                } catch (Exception e) {
                    LOGGER.log(Level.WARNING, "Errore durante l'aggiornamento dei dati OHLC per il simbolo: " + symbol, e);
                }
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante l'aggiornamento dei dati OHLC", e);
        }
    }
    
    /**
     * Aggiorna i dati OHLC per un simbolo specifico.
     * 
     * @param symbol Il simbolo
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione del comando
     */
    private void updateOHLCDataForSymbol(String symbol) throws CommandExecutionException {
        // Ottieni i timeframe configurati
        String[] timeframes = config.getProperty("marketData.timeframes", "M1,M5,M15,H1").split(",");
        
        for (String timeframe : timeframes) {
            // Ottieni i dati OHLC dal client MT5
            Map<String, Object> params = new HashMap<>();
            params.put("timeframe", timeframe.trim());
            params.put("count", Integer.parseInt(config.getProperty("marketData.ohlcCount", "100")));
            
            Map<String, Object> ohlcData = mt5Commands.getOHLCData(symbol, params);
            
            if (ohlcData.containsKey("success") && (Boolean) ohlcData.get("success")) {
                // Aggiorna la cache
                String key = symbol + "_" + timeframe.trim();
                ohlcDataCache.put(key, ohlcData);
                
                LOGGER.fine("Dati OHLC aggiornati per il simbolo: " + symbol + ", timeframe: " + timeframe);
            } else {
                LOGGER.warning("Errore durante l'ottenimento dei dati OHLC per il simbolo: " + symbol + ", timeframe: " + timeframe);
            }
        }
    }
    
    /**
     * Ottiene i dati di mercato per un simbolo specifico.
     * 
     * @param symbol Il simbolo
     * @return I dati di mercato
     */
    public Map<String, Object> getMarketData(String symbol) {
        // Verifica se i dati sono presenti nella cache
        if (marketDataCache.containsKey(symbol)) {
            // Verifica se i dati sono aggiornati
            LocalDateTime lastUpdate = lastUpdateTime.getOrDefault(symbol, LocalDateTime.MIN);
            Duration age = Duration.between(lastUpdate, LocalDateTime.now());
            
            long maxAgeMs = Long.parseLong(config.getProperty("marketData.maxAgeMs", "5000"));
            
            if (age.toMillis() <= maxAgeMs) {
                // I dati sono aggiornati, restituisci dalla cache
                return marketDataCache.get(symbol);
            }
        }
        
        // I dati non sono presenti nella cache o non sono aggiornati
        try {
            // Aggiorna i dati
            updateMarketDataForSymbol(symbol);
            
            // Restituisci i dati aggiornati
            return marketDataCache.getOrDefault(symbol, Collections.emptyMap());
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Errore durante l'ottenimento dei dati di mercato per il simbolo: " + symbol, e);
            return Collections.emptyMap();
        }
    }
    
    /**
     * Ottiene i dati OHLC per un simbolo e un timeframe specifici.
     * 
     * @param symbol Il simbolo
     * @param timeframe Il timeframe
     * @return I dati OHLC
     */
    public Map<String, Object> getOHLCData(String symbol, String timeframe) {
        String key = symbol + "_" + timeframe;
        
        // Verifica se i dati sono presenti nella cache
        if (ohlcDataCache.containsKey(key)) {
            return ohlcDataCache.get(key);
        }
        
        // I dati non sono presenti nella cache
        try {
            // Aggiorna i dati
            Map<String, Object> params = new HashMap<>();
            params.put("timeframe", timeframe);
            params.put("count", Integer.parseInt(config.getProperty("marketData.ohlcCount", "100")));
            
            Map<String, Object> ohlcData = mt5Commands.getOHLCData(symbol, params);
            
            if (ohlcData.containsKey("success") && (Boolean) ohlcData.get("success")) {
                // Aggiorna la cache
                ohlcDataCache.put(key, ohlcData);
                
                // Restituisci i dati aggiornati
                return ohlcData;
            } else {
                LOGGER.warning("Errore durante l'ottenimento dei dati OHLC per il simbolo: " + symbol + ", timeframe: " + timeframe);
                return Collections.emptyMap();
            }
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Errore durante l'ottenimento dei dati OHLC per il simbolo: " + symbol + ", timeframe: " + timeframe, e);
            return Collections.emptyMap();
        }
    }
    
    /**
     * Ottiene i dati preprocessati per il modello LSTM.
     * 
     * @param symbol Il simbolo
     * @param timeframe Il timeframe
     * @return I dati preprocessati
     */
    public Map<String, Object> getPreprocessedData(String symbol, String timeframe) {
        // Ottieni i dati OHLC
        Map<String, Object> ohlcData = getOHLCData(symbol, timeframe);
        
        if (ohlcData.isEmpty()) {
            return Collections.emptyMap();
        }
        
        try {
            // Preprocessa i dati per il modello LSTM
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> ohlc = (List<Map<String, Object>>) ohlcData.get("ohlc");
            
            // Estrai i dati OHLC
            int size = ohlc.size();
            double[] open = new double[size];
            double[] high = new double[size];
            double[] low = new double[size];
            double[] close = new double[size];
            double[] volume = new double[size];
            
            for (int i = 0; i < size; i++) {
                Map<String, Object> candle = ohlc.get(i);
                open[i] = ((Number) candle.get("open")).doubleValue();
                high[i] = ((Number) candle.get("high")).doubleValue();
                low[i] = ((Number) candle.get("low")).doubleValue();
                close[i] = ((Number) candle.get("close")).doubleValue();
                volume[i] = ((Number) candle.get("volume")).doubleValue();
            }
            
            // Normalizza i dati
            double[] normalizedOpen = normalize(open);
            double[] normalizedHigh = normalize(high);
            double[] normalizedLow = normalize(low);
            double[] normalizedClose = normalize(close);
            double[] normalizedVolume = normalize(volume);
            
            // Crea il risultato
            Map<String, Object> result = new HashMap<>();
            result.put("open", normalizedOpen);
            result.put("high", normalizedHigh);
            result.put("low", normalizedLow);
            result.put("close", normalizedClose);
            result.put("volume", normalizedVolume);
            
            return result;
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Errore durante il preprocessamento dei dati per il simbolo: " + symbol + ", timeframe: " + timeframe, e);
            return Collections.emptyMap();
        }
    }
    
    /**
     * Normalizza un array di valori.
     * 
     * @param values I valori da normalizzare
     * @return I valori normalizzati
     */
    private double[] normalize(double[] values) {
        // Trova il minimo e il massimo
        double min = Double.MAX_VALUE;
        double max = Double.MIN_VALUE;
        
        for (double value : values) {
            min = Math.min(min, value);
            max = Math.max(max, value);
        }
        
        // Normalizza i valori
        double[] normalized = new double[values.length];
        double range = max - min;
        
        for (int i = 0; i < values.length; i++) {
            normalized[i] = (values[i] - min) / range;
        }
        
        return normalized;
    }
    
    /**
     * Verifica se il servizio è in esecuzione.
     * 
     * @return true se il servizio è in esecuzione, false altrimenti
     */
    public boolean isRunning() {
        return running.get();
    }
}
