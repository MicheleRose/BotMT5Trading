package com.mt5bot.client;

import static org.junit.Assert.*;
import org.junit.Before;
import org.junit.Test;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import static org.mockito.Mockito.*;

import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * Test unitari per la classe MT5Commands.
 */
public class MT5CommandsTest {
    
    @Mock
    private CommandExecutor mockExecutor;
    
    private MT5Configuration configuration;
    private MT5Commands mt5Commands;
    
    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        configuration = new MT5Configuration();
        mt5Commands = new MT5Commands(mockExecutor, configuration);
    }
    
    @Test
    public void testCheckSpread() throws Exception {
        // Prepara il mock per restituire un risultato JSON valido
        String jsonResult = "{\"success\": true, \"symbol\": \"EURUSD\", \"data\": {\"spread_points\": 1, \"category\": \"basso\"}}";
        when(mockExecutor.execute(anyString(), anyLong(), any(TimeUnit.class))).thenReturn(jsonResult);
        
        // Esegui il metodo da testare
        Map<String, Object> result = mt5Commands.checkSpread("EURUSD");
        
        // Verifica che il comando sia stato eseguito correttamente
        verify(mockExecutor).execute(contains("analysis.check_spread"), anyLong(), any(TimeUnit.class));
        
        // Verifica il risultato
        assertTrue((Boolean) result.get("success"));
        assertEquals("EURUSD", result.get("symbol"));
        
        @SuppressWarnings("unchecked")
        Map<String, Object> data = (Map<String, Object>) result.get("data");
        assertEquals(1L, data.get("spread_points"));
        assertEquals("basso", data.get("category"));
    }
    
    @Test
    public void testGetMarketData() throws Exception {
        // Prepara il mock per restituire un risultato JSON valido
        String jsonResult = "{\"success\": true, \"symbol\": \"EURUSD\", \"timeframe\": \"H1\", \"data\": [{\"time\": 1614556800, \"open\": 1.2076, \"high\": 1.2091, \"low\": 1.2075, \"close\": 1.2088, \"volume\": 12345}]}";
        when(mockExecutor.execute(anyString(), anyLong(), any(TimeUnit.class))).thenReturn(jsonResult);
        
        // Esegui il metodo da testare
        Map<String, Object> result = mt5Commands.getMarketData("EURUSD", "H1", 100);
        
        // Verifica che il comando sia stato eseguito correttamente
        verify(mockExecutor).execute(contains("analysis.get_market_data"), anyLong(), any(TimeUnit.class));
        
        // Verifica il risultato
        assertTrue((Boolean) result.get("success"));
        assertEquals("EURUSD", result.get("symbol"));
        assertEquals("H1", result.get("timeframe"));
    }
    
    @Test
    public void testMarketBuy() throws Exception {
        // Prepara il mock per restituire un risultato JSON valido
        String jsonResult = "{\"success\": true, \"ticket\": 12345, \"symbol\": \"EURUSD\", \"volume\": 0.1, \"type\": \"buy\", \"price\": 1.2088, \"sl\": 1.2050, \"tp\": 1.2150}";
        when(mockExecutor.execute(anyString(), anyLong(), any(TimeUnit.class))).thenReturn(jsonResult);
        
        // Esegui il metodo da testare
        Map<String, Object> result = mt5Commands.marketBuy("EURUSD", 0.1, 1.2050, 1.2150, "Test", 12345);
        
        // Verifica che il comando sia stato eseguito correttamente
        verify(mockExecutor).execute(contains("commands.market_buy"), anyLong(), any(TimeUnit.class));
        
        // Verifica il risultato
        assertTrue((Boolean) result.get("success"));
        assertEquals(12345L, result.get("ticket"));
        assertEquals("EURUSD", result.get("symbol"));
        assertEquals(0.1, ((Number) result.get("volume")).doubleValue(), 0.001);
        assertEquals("buy", result.get("type"));
    }
    
    @Test
    public void testMarketSell() throws Exception {
        // Prepara il mock per restituire un risultato JSON valido
        String jsonResult = "{\"success\": true, \"ticket\": 12346, \"symbol\": \"EURUSD\", \"volume\": 0.1, \"type\": \"sell\", \"price\": 1.2088, \"sl\": 1.2150, \"tp\": 1.2050}";
        when(mockExecutor.execute(anyString(), anyLong(), any(TimeUnit.class))).thenReturn(jsonResult);
        
        // Esegui il metodo da testare
        Map<String, Object> result = mt5Commands.marketSell("EURUSD", 0.1, 1.2150, 1.2050, "Test", 12345);
        
        // Verifica che il comando sia stato eseguito correttamente
        verify(mockExecutor).execute(contains("commands.market_sell"), anyLong(), any(TimeUnit.class));
        
        // Verifica il risultato
        assertTrue((Boolean) result.get("success"));
        assertEquals(12346L, result.get("ticket"));
        assertEquals("EURUSD", result.get("symbol"));
        assertEquals(0.1, ((Number) result.get("volume")).doubleValue(), 0.001);
        assertEquals("sell", result.get("type"));
    }
    
    @Test
    public void testClosePosition() throws Exception {
        // Prepara il mock per restituire un risultato JSON valido
        String jsonResult = "{\"success\": true, \"ticket\": 12345, \"symbol\": \"EURUSD\", \"volume\": 0.1, \"profit\": 10.5}";
        when(mockExecutor.execute(anyString(), anyLong(), any(TimeUnit.class))).thenReturn(jsonResult);
        
        // Esegui il metodo da testare
        Map<String, Object> result = mt5Commands.closePosition(12345, null);
        
        // Verifica che il comando sia stato eseguito correttamente
        verify(mockExecutor).execute(contains("commands.close_position"), anyLong(), any(TimeUnit.class));
        
        // Verifica il risultato
        assertTrue((Boolean) result.get("success"));
        assertEquals(12345L, result.get("ticket"));
        assertEquals("EURUSD", result.get("symbol"));
        assertEquals(0.1, ((Number) result.get("volume")).doubleValue(), 0.001);
        assertEquals(10.5, ((Number) result.get("profit")).doubleValue(), 0.001);
    }
    
    @Test
    public void testCloseAllPositions() throws Exception {
        // Prepara il mock per restituire un risultato JSON valido
        String jsonResult = "{\"success\": true, \"closed_positions\": 2, \"total_profit\": 15.75}";
        when(mockExecutor.execute(anyString(), anyLong(), any(TimeUnit.class))).thenReturn(jsonResult);
        
        // Esegui il metodo da testare
        Map<String, Object> result = mt5Commands.closeAllPositions("EURUSD", 12345);
        
        // Verifica che il comando sia stato eseguito correttamente
        verify(mockExecutor).execute(contains("commands.close_all_positions"), anyLong(), any(TimeUnit.class));
        
        // Verifica il risultato
        assertTrue((Boolean) result.get("success"));
        assertEquals(2L, result.get("closed_positions"));
        assertEquals(15.75, ((Number) result.get("total_profit")).doubleValue(), 0.001);
    }
    
    @Test
    public void testGetAccountInfo() throws Exception {
        // Prepara il mock per restituire un risultato JSON valido
        String jsonResult = "{\"success\": true, \"account_info\": {\"login\": 12345678, \"balance\": 10000.0, \"equity\": 10050.0, \"margin\": 500.0, \"free_margin\": 9550.0, \"margin_level\": 2010.0}}";
        when(mockExecutor.execute(anyString(), anyLong(), any(TimeUnit.class))).thenReturn(jsonResult);
        
        // Esegui il metodo da testare
        Map<String, Object> result = mt5Commands.getAccountInfo();
        
        // Verifica che il comando sia stato eseguito correttamente
        verify(mockExecutor).execute(contains("commands.get_account_info"), anyLong(), any(TimeUnit.class));
        
        // Verifica il risultato
        assertTrue((Boolean) result.get("success"));
        
        @SuppressWarnings("unchecked")
        Map<String, Object> accountInfo = (Map<String, Object>) result.get("account_info");
        assertEquals(12345678L, accountInfo.get("login"));
        assertEquals(10000.0, ((Number) accountInfo.get("balance")).doubleValue(), 0.001);
        assertEquals(10050.0, ((Number) accountInfo.get("equity")).doubleValue(), 0.001);
    }
    
    @Test
    public void testTrainModel() throws Exception {
        // Prepara il mock per restituire un risultato JSON valido
        String jsonResult = "{\"symbol\": \"EURUSD\", \"timeframe\": \"H1\", \"training_period\": 1000, \"epochs\": 10, \"batch_size\": 32, \"metrics\": {\"accuracy\": 0.75, \"precision\": 0.78, \"recall\": 0.72, \"f1_score\": 0.75}}";
        when(mockExecutor.execute(anyString(), anyLong(), any(TimeUnit.class))).thenReturn(jsonResult);
        
        // Esegui il metodo da testare
        Map<String, Object> result = mt5Commands.trainModel("EURUSD", "H1", 1000, "./models/lstm", 10, 32, true);
        
        // Verifica che il comando sia stato eseguito correttamente
        verify(mockExecutor).execute(contains("ml.train_model"), anyLong(), any(TimeUnit.class));
        
        // Verifica il risultato
        assertEquals("EURUSD", result.get("symbol"));
        assertEquals("H1", result.get("timeframe"));
        assertEquals(1000L, result.get("training_period"));
        assertEquals(10L, result.get("epochs"));
        assertEquals(32L, result.get("batch_size"));
        
        @SuppressWarnings("unchecked")
        Map<String, Object> metrics = (Map<String, Object>) result.get("metrics");
        assertEquals(0.75, ((Number) metrics.get("accuracy")).doubleValue(), 0.001);
        assertEquals(0.78, ((Number) metrics.get("precision")).doubleValue(), 0.001);
    }
    
    @Test
    public void testPredictDirection() throws Exception {
        // Prepara il mock per restituire un risultato JSON valido
        String jsonResult = "{\"probability\": 0.65, \"direction\": \"up\", \"confidence\": 0.3, \"symbol\": \"EURUSD\", \"timeframe\": \"H1\", \"last_price\": 1.2088}";
        when(mockExecutor.execute(anyString(), anyLong(), any(TimeUnit.class))).thenReturn(jsonResult);
        
        // Esegui il metodo da testare
        Map<String, Object> result = mt5Commands.predictDirection("EURUSD", "./models/lstm/model.keras", "./models/lstm/scalers.pkl", 100, "H1", null, false);
        
        // Verifica che il comando sia stato eseguito correttamente
        verify(mockExecutor).execute(contains("ml.predict_direction"), anyLong(), any(TimeUnit.class));
        
        // Verifica il risultato
        assertEquals(0.65, ((Number) result.get("probability")).doubleValue(), 0.001);
        assertEquals("up", result.get("direction"));
        assertEquals(0.3, ((Number) result.get("confidence")).doubleValue(), 0.001);
        assertEquals("EURUSD", result.get("symbol"));
        assertEquals("H1", result.get("timeframe"));
        assertEquals(1.2088, ((Number) result.get("last_price")).doubleValue(), 0.001);
    }
    
    @Test(expected = CommandExecutionException.class)
    public void testCommandFailure() throws Exception {
        // Prepara il mock per restituire un risultato JSON con errore
        String jsonResult = "{\"success\": false, \"error\": \"Symbol not found\"}";
        when(mockExecutor.execute(anyString(), anyLong(), any(TimeUnit.class))).thenReturn(jsonResult);
        
        // Esegui il metodo da testare, dovrebbe lanciare un'eccezione
        mt5Commands.checkSpread("INVALID");
    }
    
    @Test(expected = CommandExecutionException.class)
    public void testCommandExecutionError() throws Exception {
        // Prepara il mock per lanciare un'eccezione
        when(mockExecutor.execute(anyString(), anyLong(), any(TimeUnit.class)))
            .thenThrow(new CommandExecutionException("Command execution failed"));
        
        // Esegui il metodo da testare, dovrebbe lanciare un'eccezione
        mt5Commands.checkSpread("EURUSD");
    }
    
    @Test(expected = CommandExecutionException.class)
    public void testCommandTimeoutError() throws Exception {
        // Prepara il mock per lanciare un'eccezione di timeout
        when(mockExecutor.execute(anyString(), anyLong(), any(TimeUnit.class)))
            .thenThrow(new CommandTimeoutException("Command execution timed out"));
        
        // Esegui il metodo da testare, dovrebbe lanciare un'eccezione
        mt5Commands.checkSpread("EURUSD");
    }
}
