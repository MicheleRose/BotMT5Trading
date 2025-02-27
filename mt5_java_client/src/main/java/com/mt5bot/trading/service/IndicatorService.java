package main.java.com.mt5bot.trading.service;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
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
 * Servizio per il calcolo degli indicatori tecnici.
 * Implementa il calcolo real-time degli indicatori tecnici e i segnali di ingresso.
 */
public class IndicatorService {
    
    private static final Logger LOGGER = Logger.getLogger(IndicatorService.class.getName());
    
    // Istanza singleton
    private static IndicatorService instance;
    
    // Servizio per i dati di mercato
    private final MarketDataService marketDataService;
    
    // Configurazione
    private final Properties config;
    
    // Cache degli indicatori
    private final Map<String, Map<String, Object>> indicatorsCache = new ConcurrentHashMap<>();
    
    // Scheduler per l'aggiornamento periodico
    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(1);
    
    // Stato del servizio
    private final AtomicBoolean running = new AtomicBoolean(false);
    
    /**
     * Costruttore privato per il pattern singleton.
     * 
     * @param marketDataService Il servizio per i dati di mercato
     * @param config La configurazione
     */
    private IndicatorService(MarketDataService marketDataService, Properties config) {
        this.marketDataService = marketDataService;
        this.config = config;
    }
    
    /**
     * Ottiene l'istanza singleton del servizio.
     * 
     * @param marketDataService Il servizio per i dati di mercato
     * @param config La configurazione
     * @return L'istanza singleton del servizio
     */
    public static synchronized IndicatorService getInstance(MarketDataService marketDataService, Properties config) {
        if (instance == null) {
            instance = new IndicatorService(marketDataService, config);
        }
        return instance;
    }
    
    /**
     * Avvia il servizio.
     */
    public void start() {
        if (running.compareAndSet(false, true)) {
            LOGGER.info("Avvio del servizio IndicatorService...");
            
            // Avvia lo scheduler per l'aggiornamento periodico degli indicatori
            long indicatorsUpdateIntervalMs = Long.parseLong(
                    config.getProperty("indicators.updateIntervalMs", "1000"));
            
            scheduler.scheduleAtFixedRate(
                    this::updateIndicators,
                    0,
                    indicatorsUpdateIntervalMs,
                    TimeUnit.MILLISECONDS);
            
            LOGGER.info("Servizio IndicatorService avviato con successo.");
        } else {
            LOGGER.warning("Il servizio IndicatorService è già in esecuzione.");
        }
    }
    
    /**
     * Ferma il servizio.
     */
    public void stop() {
        if (running.compareAndSet(true, false)) {
            LOGGER.info("Arresto del servizio IndicatorService...");
            
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
            
            // Pulisci la cache
            indicatorsCache.clear();
            
            LOGGER.info("Servizio IndicatorService arrestato con successo.");
        } else {
            LOGGER.warning("Il servizio IndicatorService non è in esecuzione.");
        }
    }
    
    /**
     * Aggiorna gli indicatori per tutti i simboli configurati.
     */
    private void updateIndicators() {
        if (!running.get()) {
            return;
        }
        
        try {
            // Ottieni i simboli configurati
            String[] symbols = config.getProperty("indicators.symbols", "EURUSD,GBPUSD,USDJPY").split(",");
            
            for (String symbol : symbols) {
                try {
                    // Aggiorna gli indicatori per il simbolo
                    updateIndicatorsForSymbol(symbol.trim());
                } catch (Exception e) {
                    LOGGER.log(Level.WARNING, "Errore durante l'aggiornamento degli indicatori per il simbolo: " + symbol, e);
                }
            }
        } catch (Exception e) {
            LOGGER.log(Level.SEVERE, "Errore durante l'aggiornamento degli indicatori", e);
        }
    }
    
    /**
     * Aggiorna gli indicatori per un simbolo specifico.
     * 
     * @param symbol Il simbolo
     */
    private void updateIndicatorsForSymbol(String symbol) {
        // Ottieni i dati OHLC
        String timeframe = config.getProperty("indicators.timeframe", "M5");
        Map<String, Object> ohlcData = marketDataService.getOHLCData(symbol, timeframe);
        
        if (ohlcData.isEmpty()) {
            LOGGER.warning("Dati OHLC non disponibili per il simbolo: " + symbol);
            return;
        }
        
        try {
            // Calcola gli indicatori
            Map<String, Object> indicators = calculateIndicatorsFromOHLC(ohlcData);
            
            // Aggiorna la cache
            indicatorsCache.put(symbol, indicators);
            
            LOGGER.fine("Indicatori aggiornati per il simbolo: " + symbol);
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Errore durante il calcolo degli indicatori per il simbolo: " + symbol, e);
        }
    }
    
    /**
     * Calcola gli indicatori dai dati OHLC.
     * 
     * @param ohlcData I dati OHLC
     * @return Gli indicatori calcolati
     */
    private Map<String, Object> calculateIndicatorsFromOHLC(Map<String, Object> ohlcData) {
        Map<String, Object> indicators = new HashMap<>();
        
        try {
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> ohlc = (List<Map<String, Object>>) ohlcData.get("ohlc");
            
            if (ohlc == null || ohlc.isEmpty()) {
                return Collections.emptyMap();
            }
            
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
            
            // Calcola gli indicatori
            
            // Prezzo corrente
            double currentPrice = close[size - 1];
            indicators.put("PRICE", currentPrice);
            
            // RSI(2)
            double rsi = calculateRSI(close, 2);
            indicators.put("RSI", rsi);
            
            // MACD(2,4,2)
            double[] macd = calculateMACD(close, 2, 4, 2);
            indicators.put("MACD", macd[0]);
            indicators.put("MACD_SIGNAL", macd[1]);
            indicators.put("MACD_HISTOGRAM", macd[2]);
            
            // Bollinger(3,2)
            double[] bollinger = calculateBollinger(close, 3, 2);
            indicators.put("BOLL_UPPER", bollinger[0]);
            indicators.put("BOLL_MIDDLE", bollinger[1]);
            indicators.put("BOLL_LOWER", bollinger[2]);
            
            // ADX(2)
            double adx = calculateADX(high, low, close, 2);
            indicators.put("ADX", adx);
            
            // Stocastico(2,2,2)
            double[] stochastic = calculateStochastic(high, low, close, 2, 2, 2);
            indicators.put("STOCH_K", stochastic[0]);
            indicators.put("STOCH_D", stochastic[1]);
            
            return indicators;
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Errore durante il calcolo degli indicatori", e);
            return Collections.emptyMap();
        }
    }
    
    /**
     * Calcola l'indicatore RSI.
     * 
     * @param close I prezzi di chiusura
     * @param period Il periodo
     * @return Il valore dell'RSI
     */
    private double calculateRSI(double[] close, int period) {
        if (close.length <= period) {
            return 50.0;
        }
        
        double[] changes = new double[close.length - 1];
        for (int i = 0; i < changes.length; i++) {
            changes[i] = close[i + 1] - close[i];
        }
        
        double sumGain = 0;
        double sumLoss = 0;
        
        for (int i = changes.length - period; i < changes.length; i++) {
            if (changes[i] > 0) {
                sumGain += changes[i];
            } else {
                sumLoss -= changes[i];
            }
        }
        
        if (sumLoss == 0) {
            return 100.0;
        }
        
        double rs = sumGain / sumLoss;
        return 100.0 - (100.0 / (1.0 + rs));
    }
    
    /**
     * Calcola l'indicatore MACD.
     * 
     * @param close I prezzi di chiusura
     * @param fastPeriod Il periodo veloce
     * @param slowPeriod Il periodo lento
     * @param signalPeriod Il periodo del segnale
     * @return I valori del MACD [macd, signal, histogram]
     */
    private double[] calculateMACD(double[] close, int fastPeriod, int slowPeriod, int signalPeriod) {
        if (close.length <= slowPeriod) {
            return new double[] { 0.0, 0.0, 0.0 };
        }
        
        double[] fastEMA = calculateEMA(close, fastPeriod);
        double[] slowEMA = calculateEMA(close, slowPeriod);
        
        double[] macdLine = new double[close.length];
        for (int i = 0; i < close.length; i++) {
            macdLine[i] = fastEMA[i] - slowEMA[i];
        }
        
        double[] signalLine = calculateEMA(macdLine, signalPeriod);
        
        double macd = macdLine[macdLine.length - 1];
        double signal = signalLine[signalLine.length - 1];
        double histogram = macd - signal;
        
        return new double[] { macd, signal, histogram };
    }
    
    /**
     * Calcola l'EMA (Exponential Moving Average).
     * 
     * @param data I dati
     * @param period Il periodo
     * @return I valori dell'EMA
     */
    private double[] calculateEMA(double[] data, int period) {
        double[] ema = new double[data.length];
        double multiplier = 2.0 / (period + 1.0);
        
        // Inizializza l'EMA con la media semplice
        double sum = 0;
        for (int i = 0; i < period; i++) {
            sum += data[i];
        }
        ema[period - 1] = sum / period;
        
        // Calcola l'EMA
        for (int i = period; i < data.length; i++) {
            ema[i] = (data[i] - ema[i - 1]) * multiplier + ema[i - 1];
        }
        
        return ema;
    }
    
    /**
     * Calcola l'indicatore Bollinger Bands.
     * 
     * @param close I prezzi di chiusura
     * @param period Il periodo
     * @param deviations Il numero di deviazioni standard
     * @return I valori delle Bollinger Bands [upper, middle, lower]
     */
    private double[] calculateBollinger(double[] close, int period, double deviations) {
        if (close.length <= period) {
            return new double[] { close[close.length - 1], close[close.length - 1], close[close.length - 1] };
        }
        
        // Calcola la media mobile semplice
        double sum = 0;
        for (int i = close.length - period; i < close.length; i++) {
            sum += close[i];
        }
        double sma = sum / period;
        
        // Calcola la deviazione standard
        double sumSquaredDeviations = 0;
        for (int i = close.length - period; i < close.length; i++) {
            double deviation = close[i] - sma;
            sumSquaredDeviations += deviation * deviation;
        }
        double standardDeviation = Math.sqrt(sumSquaredDeviations / period);
        
        // Calcola le bande
        double upper = sma + (standardDeviation * deviations);
        double lower = sma - (standardDeviation * deviations);
        
        return new double[] { upper, sma, lower };
    }
    
    /**
     * Calcola l'indicatore ADX (Average Directional Index).
     * 
     * @param high I prezzi massimi
     * @param low I prezzi minimi
     * @param close I prezzi di chiusura
     * @param period Il periodo
     * @return Il valore dell'ADX
     */
    private double calculateADX(double[] high, double[] low, double[] close, int period) {
        if (high.length <= period + 1 || low.length <= period + 1 || close.length <= period + 1) {
            return 0.0;
        }
        
        // Calcola il True Range (TR)
        double[] tr = new double[close.length - 1];
        for (int i = 1; i < close.length; i++) {
            double hl = high[i] - low[i];
            double hc = Math.abs(high[i] - close[i - 1]);
            double lc = Math.abs(low[i] - close[i - 1]);
            tr[i - 1] = Math.max(hl, Math.max(hc, lc));
        }
        
        // Calcola il Directional Movement (DM)
        double[] plusDM = new double[close.length - 1];
        double[] minusDM = new double[close.length - 1];
        for (int i = 1; i < close.length; i++) {
            double upMove = high[i] - high[i - 1];
            double downMove = low[i - 1] - low[i];
            
            if (upMove > downMove && upMove > 0) {
                plusDM[i - 1] = upMove;
            } else {
                plusDM[i - 1] = 0;
            }
            
            if (downMove > upMove && downMove > 0) {
                minusDM[i - 1] = downMove;
            } else {
                minusDM[i - 1] = 0;
            }
        }
        
        // Calcola l'Average True Range (ATR)
        double atr = 0;
        for (int i = tr.length - period; i < tr.length; i++) {
            atr += tr[i];
        }
        atr /= period;
        
        // Calcola il Directional Index (DI)
        double plusDI = 0;
        double minusDI = 0;
        for (int i = plusDM.length - period; i < plusDM.length; i++) {
            plusDI += plusDM[i];
            minusDI += minusDM[i];
        }
        plusDI = (plusDI / atr) * 100.0 / period;
        minusDI = (minusDI / atr) * 100.0 / period;
        
        // Calcola il Directional Movement Index (DX)
        double dx = 0;
        if (plusDI + minusDI > 0) {
            dx = (Math.abs(plusDI - minusDI) / (plusDI + minusDI)) * 100.0;
        }
        
        // Calcola l'Average Directional Index (ADX)
        // Nota: Normalmente l'ADX è una media mobile del DX, ma per semplicità
        // restituiamo direttamente il DX
        return dx;
    }
    
    /**
     * Calcola l'indicatore Stocastico.
     * 
     * @param high I prezzi massimi
     * @param low I prezzi minimi
     * @param close I prezzi di chiusura
     * @param kPeriod Il periodo K
     * @param dPeriod Il periodo D
     * @param slowing Il periodo di rallentamento
     * @return I valori dello Stocastico [%K, %D]
     */
    private double[] calculateStochastic(double[] high, double[] low, double[] close, int kPeriod, int dPeriod, int slowing) {
        if (high.length <= kPeriod || low.length <= kPeriod || close.length <= kPeriod) {
            return new double[] { 50.0, 50.0 };
        }
        
        // Calcola %K
        double[] k = new double[close.length - kPeriod + 1];
        for (int i = 0; i < k.length; i++) {
            double highestHigh = Double.MIN_VALUE;
            double lowestLow = Double.MAX_VALUE;
            
            for (int j = i; j < i + kPeriod; j++) {
                highestHigh = Math.max(highestHigh, high[j]);
                lowestLow = Math.min(lowestLow, low[j]);
            }
            
            if (highestHigh - lowestLow > 0) {
                k[i] = ((close[i + kPeriod - 1] - lowestLow) / (highestHigh - lowestLow)) * 100.0;
            } else {
                k[i] = 50.0;
            }
        }
        
        // Calcola %K rallentato
        double[] kSlowed = new double[k.length - slowing + 1];
        for (int i = 0; i < kSlowed.length; i++) {
            double sum = 0;
            for (int j = i; j < i + slowing; j++) {
                sum += k[j];
            }
            kSlowed[i] = sum / slowing;
        }
        
        // Calcola %D
        double[] d = new double[kSlowed.length - dPeriod + 1];
        for (int i = 0; i < d.length; i++) {
            double sum = 0;
            for (int j = i; j < i + dPeriod; j++) {
                sum += kSlowed[j];
            }
            d[i] = sum / dPeriod;
        }
        
        double kValue = kSlowed[kSlowed.length - 1];
        double dValue = d[d.length - 1];
        
        return new double[] { kValue, dValue };
    }
    
    /**
     * Ottiene gli indicatori per un simbolo specifico.
     * 
     * @param symbol Il simbolo
     * @return Gli indicatori
     */
    public Map<String, Object> calculateIndicators(String symbol) {
        // Verifica se gli indicatori sono presenti nella cache
        if (indicatorsCache.containsKey(symbol)) {
            return indicatorsCache.get(symbol);
        }
        
        // Gli indicatori non sono presenti nella cache
        try {
            // Aggiorna gli indicatori
            updateIndicatorsForSymbol(symbol);
            
            // Restituisci gli indicatori aggiornati
            return indicatorsCache.getOrDefault(symbol, Collections.emptyMap());
        } catch (Exception e) {
            LOGGER.log(Level.WARNING, "Errore durante il calcolo degli indicatori per il simbolo: " + symbol, e);
            return Collections.emptyMap();
        }
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
