package test.java.com.mt5bot.backtest;

import static org.junit.Assert.*;

import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;

import org.junit.Before;
import org.junit.Test;

import main.java.com.mt5bot.trading.service.IndicatorService;
import main.java.com.mt5bot.trading.service.MarketDataService;
import test.java.com.mt5bot.mock.MT5Simulator;

/**
 * Test di validazione delle performance su serie storiche.
 * Verifica le performance del sistema di trading su dati storici.
 */
public class HistoricalPerformanceTest {
    
    private MT5Simulator mt5Simulator;
    private Properties config;
    
    @Before
    public void setUp() throws Exception {
        // Ottieni l'istanza del simulatore MT5
        mt5Simulator = MT5Simulator.getInstance();
        
        // Carica la configurazione
        config = new Properties();
        config.load(new FileReader(new File("src/main/resources/trading_bot.properties")));
    }
    
    @Test
    public void testStrategyPerformanceOnHistoricalData() throws IOException {
        // Carica i dati storici
        List<Map<String, Object>> historicalData = loadHistoricalData("EURUSD", "M5", 1000);
        
        // Esegui il backtest
        Map<String, Object> result = runBacktest(historicalData);
        
        // Verifica i risultati
        assertNotNull("Il risultato del backtest non dovrebbe essere null", result);
        assertTrue("Il risultato del backtest dovrebbe contenere il campo 'profit'", result.containsKey("profit"));
        assertTrue("Il risultato del backtest dovrebbe contenere il campo 'trades'", result.containsKey("trades"));
        assertTrue("Il risultato del backtest dovrebbe contenere il campo 'win_rate'", result.containsKey("win_rate"));
        assertTrue("Il risultato del backtest dovrebbe contenere il campo 'profit_factor'", result.containsKey("profit_factor"));
        assertTrue("Il risultato del backtest dovrebbe contenere il campo 'max_drawdown'", result.containsKey("max_drawdown"));
        
        // Verifica che le performance siano accettabili
        double profit = ((Number) result.get("profit")).doubleValue();
        double winRate = ((Number) result.get("win_rate")).doubleValue();
        double profitFactor = ((Number) result.get("profit_factor")).doubleValue();
        double maxDrawdown = ((Number) result.get("max_drawdown")).doubleValue();
        
        assertTrue("Il profitto dovrebbe essere positivo", profit > 0);
        assertTrue("Il win rate dovrebbe essere almeno del 50%", winRate >= 50.0);
        assertTrue("Il profit factor dovrebbe essere almeno 1.5", profitFactor >= 1.5);
        assertTrue("Il max drawdown non dovrebbe superare il 20%", maxDrawdown <= 20.0);
        
        // Stampa i risultati
        System.out.println("Risultati del backtest:");
        System.out.println("Profitto: " + profit);
        System.out.println("Numero di trade: " + result.get("trades"));
        System.out.println("Win rate: " + winRate + "%");
        System.out.println("Profit factor: " + profitFactor);
        System.out.println("Max drawdown: " + maxDrawdown + "%");
    }
    
    /**
     * Carica i dati storici.
     * 
     * @param symbol Il simbolo
     * @param timeframe Il timeframe
     * @param count Il numero di candele
     * @return I dati storici
     */
    private List<Map<String, Object>> loadHistoricalData(String symbol, String timeframe, int count) {
        // In un'implementazione reale, questi dati verrebbero caricati da un file CSV o da un database
        // Per questo esempio, utilizziamo i dati simulati
        Map<String, Object> ohlcData = mt5Simulator.getOHLCData(symbol, timeframe, count);
        
        @SuppressWarnings("unchecked")
        List<Map<String, Object>> ohlc = (List<Map<String, Object>>) ohlcData.get("ohlc");
        
        return ohlc;
    }
    
    /**
     * Esegue il backtest.
     * 
     * @param historicalData I dati storici
     * @return I risultati del backtest
     */
    private Map<String, Object> runBacktest(List<Map<String, Object>> historicalData) {
        // Inizializza i risultati
        Map<String, Object> result = new HashMap<>();
        double initialBalance = 10000.0;
        double balance = initialBalance;
        double maxBalance = initialBalance;
        double maxDrawdown = 0.0;
        int trades = 0;
        int winTrades = 0;
        double grossProfit = 0.0;
        double grossLoss = 0.0;
        
        // Posizione corrente
        Map<String, Object> currentPosition = null;
        
        // Esegui il backtest
        for (int i = 30; i < historicalData.size(); i++) { // Inizia da 30 per avere abbastanza dati per gli indicatori
            // Ottieni i dati OHLC
            List<Map<String, Object>> ohlcWindow = historicalData.subList(i - 30, i + 1);
            
            // Calcola gli indicatori
            Map<String, Object> indicators = calculateIndicators(ohlcWindow);
            
            // Ottieni il prezzo corrente
            Map<String, Object> currentCandle = historicalData.get(i);
            double currentPrice = ((Number) currentCandle.get("close")).doubleValue();
            
            // Verifica le condizioni di ingresso
            if (currentPosition == null && checkEntryConditions(indicators)) {
                // Apri una posizione
                currentPosition = new HashMap<>();
                currentPosition.put("type", "buy");
                currentPosition.put("open_price", currentPrice);
                currentPosition.put("volume", 0.1);
                currentPosition.put("open_time", currentCandle.get("time"));
            }
            
            // Verifica le condizioni di uscita
            if (currentPosition != null && checkExitConditions(indicators)) {
                // Chiudi la posizione
                String type = (String) currentPosition.get("type");
                double openPrice = ((Number) currentPosition.get("open_price")).doubleValue();
                double volume = ((Number) currentPosition.get("volume")).doubleValue();
                double profit = type.equals("buy") ? (currentPrice - openPrice) * volume * 100000 : (openPrice - currentPrice) * volume * 100000;
                
                // Aggiorna il bilancio
                balance += profit;
                
                // Aggiorna le statistiche
                trades++;
                if (profit > 0) {
                    winTrades++;
                    grossProfit += profit;
                } else {
                    grossLoss -= profit;
                }
                
                // Aggiorna il max drawdown
                if (balance > maxBalance) {
                    maxBalance = balance;
                } else {
                    double drawdown = (maxBalance - balance) / maxBalance * 100.0;
                    if (drawdown > maxDrawdown) {
                        maxDrawdown = drawdown;
                    }
                }
                
                // Resetta la posizione corrente
                currentPosition = null;
            }
        }
        
        // Calcola le statistiche finali
        double profit = balance - initialBalance;
        double winRate = trades > 0 ? (double) winTrades / trades * 100.0 : 0.0;
        double profitFactor = grossLoss > 0 ? grossProfit / grossLoss : 0.0;
        
        // Imposta i risultati
        result.put("profit", profit);
        result.put("trades", trades);
        result.put("win_rate", winRate);
        result.put("profit_factor", profitFactor);
        result.put("max_drawdown", maxDrawdown);
        
        return result;
    }
    
    /**
     * Calcola gli indicatori.
     * 
     * @param ohlcWindow La finestra di dati OHLC
     * @return Gli indicatori calcolati
     */
    private Map<String, Object> calculateIndicators(List<Map<String, Object>> ohlcWindow) {
        Map<String, Object> indicators = new HashMap<>();
        
        // Estrai i prezzi di chiusura
        double[] close = new double[ohlcWindow.size()];
        double[] high = new double[ohlcWindow.size()];
        double[] low = new double[ohlcWindow.size()];
        
        for (int i = 0; i < ohlcWindow.size(); i++) {
            Map<String, Object> candle = ohlcWindow.get(i);
            close[i] = ((Number) candle.get("close")).doubleValue();
            high[i] = ((Number) candle.get("high")).doubleValue();
            low[i] = ((Number) candle.get("low")).doubleValue();
        }
        
        // Prezzo corrente
        double currentPrice = close[close.length - 1];
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
    }
    
    /**
     * Verifica le condizioni di ingresso.
     * 
     * @param indicators Gli indicatori
     * @return true se le condizioni di ingresso sono soddisfatte, false altrimenti
     */
    private boolean checkEntryConditions(Map<String, Object> indicators) {
        // RSI(2): 15/85
        double rsi = (double) indicators.get("RSI");
        if (rsi < 15 || rsi > 85) {
            return true;
        }
        
        // MACD(2,4,2)
        double macd = (double) indicators.get("MACD");
        double signal = (double) indicators.get("MACD_SIGNAL");
        if (macd > signal) {
            return true;
        }
        
        // Bollinger(3,2)
        double price = (double) indicators.get("PRICE");
        double upperBand = (double) indicators.get("BOLL_UPPER");
        double lowerBand = (double) indicators.get("BOLL_LOWER");
        if (price > upperBand || price < lowerBand) {
            return true;
        }
        
        // ADX(2): 20
        double adx = (double) indicators.get("ADX");
        if (adx > 20) {
            return true;
        }
        
        // Stocastico(2,2,2)
        double k = (double) indicators.get("STOCH_K");
        double d = (double) indicators.get("STOCH_D");
        if (k > d) {
            return true;
        }
        
        return false;
    }
    
    /**
     * Verifica le condizioni di uscita.
     * 
     * @param indicators Gli indicatori
     * @return true se le condizioni di uscita sono soddisfatte, false altrimenti
     */
    private boolean checkExitConditions(Map<String, Object> indicators) {
        // RSI(2): 50
        double rsi = (double) indicators.get("RSI");
        if (rsi > 45 && rsi < 55) {
            return true;
        }
        
        // MACD(2,4,2)
        double macd = (double) indicators.get("MACD");
        double signal = (double) indicators.get("MACD_SIGNAL");
        if (macd < signal) {
            return true;
        }
        
        // Bollinger(3,2)
        double price = (double) indicators.get("PRICE");
        double middleBand = (double) indicators.get("BOLL_MIDDLE");
        if (Math.abs(price - middleBand) < 0.0010) {
            return true;
        }
        
        // ADX(2): 15
        double adx = (double) indicators.get("ADX");
        if (adx < 15) {
            return true;
        }
        
        // Stocastico(2,2,2)
        double k = (double) indicators.get("STOCH_K");
        double d = (double) indicators.get("STOCH_D");
        if (k < d) {
            return true;
        }
        
        return false;
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
}
