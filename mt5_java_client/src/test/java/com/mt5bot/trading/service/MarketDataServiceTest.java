package test.java.com.mt5bot.trading.service;

import static org.junit.Assert.*;
import static org.mockito.Mockito.*;

import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

import org.junit.Before;
import org.junit.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import com.mt5bot.client.CommandExecutionException;
import com.mt5bot.client.MT5Commands;

/**
 * Test unitari per il servizio MarketDataService.
 */
public class MarketDataServiceTest {
    
    @Mock
    private MT5Commands mt5Commands;
    
    private Properties config;
    private MarketDataService marketDataService;
    
    @Before
    public void setUp() throws Exception {
        MockitoAnnotations.initMocks(this);
        
        // Configura le proprietà di test
        config = new Properties();
        config.setProperty("marketData.symbols", "EURUSD,GBPUSD");
        config.setProperty("marketData.timeframes", "M1,M5");
        config.setProperty("marketData.updateIntervalMs", "1000");
        config.setProperty("marketData.ohlcUpdateIntervalMs", "5000");
        config.setProperty("marketData.ohlcCount", "10");
        config.setProperty("marketData.maxAgeMs", "2000");
        
        // Configura il mock di MT5Commands
        Map<String, Object> marketData = new HashMap<>();
        marketData.put("success", true);
        marketData.put("symbol", "EURUSD");
        marketData.put("bid", 1.1234);
        marketData.put("ask", 1.1236);
        marketData.put("spread", 2);
        when(mt5Commands.getMarketData("EURUSD")).thenReturn(marketData);
        
        Map<String, Object> ohlcData = new HashMap<>();
        ohlcData.put("success", true);
        ohlcData.put("symbol", "EURUSD");
        ohlcData.put("timeframe", "M5");
        ohlcData.put("ohlc", createMockOHLCData());
        when(mt5Commands.getOHLCData(eq("EURUSD"), any(Map.class))).thenReturn(ohlcData);
        
        // Crea l'istanza di MarketDataService con il mock
        marketDataService = MarketDataService.getInstance(mt5Commands, config);
    }
    
    /**
     * Crea dati OHLC di esempio per i test.
     * 
     * @return I dati OHLC di esempio
     */
    private Object createMockOHLCData() {
        // Crea 10 candele di esempio
        java.util.List<Map<String, Object>> ohlc = new java.util.ArrayList<>();
        
        for (int i = 0; i < 10; i++) {
            Map<String, Object> candle = new HashMap<>();
            candle.put("time", System.currentTimeMillis() - (i * 300000)); // 5 minuti per candela
            candle.put("open", 1.1230 + (i * 0.0001));
            candle.put("high", 1.1240 + (i * 0.0001));
            candle.put("low", 1.1220 + (i * 0.0001));
            candle.put("close", 1.1235 + (i * 0.0001));
            candle.put("volume", 100 + i);
            ohlc.add(candle);
        }
        
        return ohlc;
    }
    
    @Test
    public void testGetMarketData() throws CommandExecutionException {
        // Avvia il servizio
        marketDataService.start();
        
        try {
            // Ottieni i dati di mercato
            Map<String, Object> marketData = marketDataService.getMarketData("EURUSD");
            
            // Verifica che i dati siano corretti
            assertNotNull("I dati di mercato non dovrebbero essere null", marketData);
            assertTrue("I dati di mercato dovrebbero contenere il campo 'success'", marketData.containsKey("success"));
            assertEquals("Il simbolo dovrebbe essere EURUSD", "EURUSD", marketData.get("symbol"));
            assertEquals("Il bid dovrebbe essere 1.1234", 1.1234, marketData.get("bid"));
            assertEquals("L'ask dovrebbe essere 1.1236", 1.1236, marketData.get("ask"));
            assertEquals("Lo spread dovrebbe essere 2", 2, marketData.get("spread"));
            
            // Verifica che il metodo getMarketData sia stato chiamato
            verify(mt5Commands, times(1)).getMarketData("EURUSD");
        } finally {
            // Ferma il servizio
            marketDataService.stop();
        }
    }
    
    @Test
    public void testGetOHLCData() throws CommandExecutionException {
        // Avvia il servizio
        marketDataService.start();
        
        try {
            // Ottieni i dati OHLC
            Map<String, Object> ohlcData = marketDataService.getOHLCData("EURUSD", "M5");
            
            // Verifica che i dati siano corretti
            assertNotNull("I dati OHLC non dovrebbero essere null", ohlcData);
            assertTrue("I dati OHLC dovrebbero contenere il campo 'success'", ohlcData.containsKey("success"));
            assertEquals("Il simbolo dovrebbe essere EURUSD", "EURUSD", ohlcData.get("symbol"));
            assertEquals("Il timeframe dovrebbe essere M5", "M5", ohlcData.get("timeframe"));
            
            // Verifica che il metodo getOHLCData sia stato chiamato
            verify(mt5Commands, times(1)).getOHLCData(eq("EURUSD"), any(Map.class));
        } finally {
            // Ferma il servizio
            marketDataService.stop();
        }
    }
    
    @Test
    public void testGetPreprocessedData() throws CommandExecutionException {
        // Avvia il servizio
        marketDataService.start();
        
        try {
            // Ottieni i dati preprocessati
            Map<String, Object> preprocessedData = marketDataService.getPreprocessedData("EURUSD", "M5");
            
            // Verifica che i dati siano corretti
            assertNotNull("I dati preprocessati non dovrebbero essere null", preprocessedData);
            assertTrue("I dati preprocessati dovrebbero contenere il campo 'open'", preprocessedData.containsKey("open"));
            assertTrue("I dati preprocessati dovrebbero contenere il campo 'high'", preprocessedData.containsKey("high"));
            assertTrue("I dati preprocessati dovrebbero contenere il campo 'low'", preprocessedData.containsKey("low"));
            assertTrue("I dati preprocessati dovrebbero contenere il campo 'close'", preprocessedData.containsKey("close"));
            assertTrue("I dati preprocessati dovrebbero contenere il campo 'volume'", preprocessedData.containsKey("volume"));
            
            // Verifica che il metodo getOHLCData sia stato chiamato
            verify(mt5Commands, times(1)).getOHLCData(eq("EURUSD"), any(Map.class));
        } finally {
            // Ferma il servizio
            marketDataService.stop();
        }
    }
    
    @Test
    public void testStartStop() {
        // Verifica che il servizio non sia in esecuzione all'inizio
        assertFalse("Il servizio non dovrebbe essere in esecuzione all'inizio", marketDataService.isRunning());
        
        // Avvia il servizio
        marketDataService.start();
        
        // Verifica che il servizio sia in esecuzione
        assertTrue("Il servizio dovrebbe essere in esecuzione dopo l'avvio", marketDataService.isRunning());
        
        // Ferma il servizio
        marketDataService.stop();
        
        // Verifica che il servizio non sia più in esecuzione
        assertFalse("Il servizio non dovrebbe essere in esecuzione dopo l'arresto", marketDataService.isRunning());
    }
}
