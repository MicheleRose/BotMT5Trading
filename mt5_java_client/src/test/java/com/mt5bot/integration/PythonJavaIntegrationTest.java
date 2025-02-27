package test.java.com.mt5bot.integration;

import static org.junit.Assert.*;

import java.io.File;
import java.io.IOException;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import org.junit.After;
import org.junit.Before;
import org.junit.Test;

import com.mt5bot.client.CommandExecutionException;
import com.mt5bot.client.CommandExecutor;
import com.mt5bot.client.MT5Commands;
import com.mt5bot.client.ProcessBuilderCommandExecutor;

/**
 * Test di integrazione tra Python e Java.
 * Verifica la comunicazione tra i componenti Java e Python.
 */
public class PythonJavaIntegrationTest {
    
    private Process mt5KeeperProcess;
    private MT5Commands mt5Commands;
    
    @Before
    public void setUp() throws Exception {
        // Avvia il processo MT5 Keeper
        startMT5Keeper();
        
        // Attendi che il processo sia avviato
        TimeUnit.SECONDS.sleep(2);
        
        // Crea l'istanza di MT5Commands
        CommandExecutor executor = new ProcessBuilderCommandExecutor();
        mt5Commands = new MT5Commands(executor);
    }
    
    @After
    public void tearDown() throws Exception {
        // Termina il processo MT5 Keeper
        if (mt5KeeperProcess != null && mt5KeeperProcess.isAlive()) {
            mt5KeeperProcess.destroy();
            mt5KeeperProcess.waitFor(5, TimeUnit.SECONDS);
            if (mt5KeeperProcess.isAlive()) {
                mt5KeeperProcess.destroyForcibly();
            }
        }
    }
    
    /**
     * Avvia il processo MT5 Keeper.
     * 
     * @throws IOException Se si verifica un errore durante l'avvio del processo
     */
    private void startMT5Keeper() throws IOException {
        // Determina il percorso del file Python
        String pythonPath = System.getProperty("python.path", "python");
        
        // Determina il percorso del file MT5 Keeper
        String mt5KeeperPath = new File("../mt5_keeper.py").getAbsolutePath();
        
        // Avvia il processo
        ProcessBuilder processBuilder = new ProcessBuilder(pythonPath, mt5KeeperPath);
        processBuilder.redirectErrorStream(true);
        mt5KeeperProcess = processBuilder.start();
    }
    
    @Test
    public void testGetAccountInfo() throws CommandExecutionException {
        // Ottieni le informazioni sull'account
        Map<String, Object> accountInfo = mt5Commands.getAccountInfo();
        
        // Verifica che le informazioni siano corrette
        assertNotNull("Le informazioni sull'account non dovrebbero essere null", accountInfo);
        assertTrue("Le informazioni sull'account dovrebbero contenere il campo 'success'", accountInfo.containsKey("success"));
        assertTrue("Le informazioni sull'account dovrebbero contenere il campo 'balance'", accountInfo.containsKey("balance"));
        assertTrue("Le informazioni sull'account dovrebbero contenere il campo 'equity'", accountInfo.containsKey("equity"));
        assertTrue("Le informazioni sull'account dovrebbero contenere il campo 'margin'", accountInfo.containsKey("margin"));
        assertTrue("Le informazioni sull'account dovrebbero contenere il campo 'free_margin'", accountInfo.containsKey("free_margin"));
        assertTrue("Le informazioni sull'account dovrebbero contenere il campo 'margin_level'", accountInfo.containsKey("margin_level"));
    }
    
    @Test
    public void testGetMarketData() throws CommandExecutionException {
        // Ottieni i dati di mercato
        Map<String, Object> marketData = mt5Commands.getMarketData("EURUSD");
        
        // Verifica che i dati siano corretti
        assertNotNull("I dati di mercato non dovrebbero essere null", marketData);
        assertTrue("I dati di mercato dovrebbero contenere il campo 'success'", marketData.containsKey("success"));
        assertTrue("I dati di mercato dovrebbero contenere il campo 'symbol'", marketData.containsKey("symbol"));
        assertTrue("I dati di mercato dovrebbero contenere il campo 'bid'", marketData.containsKey("bid"));
        assertTrue("I dati di mercato dovrebbero contenere il campo 'ask'", marketData.containsKey("ask"));
        assertTrue("I dati di mercato dovrebbero contenere il campo 'spread'", marketData.containsKey("spread"));
    }
    
    @Test
    public void testGetOHLCData() throws CommandExecutionException {
        // Parametri per i dati OHLC
        Map<String, Object> params = new java.util.HashMap<>();
        params.put("timeframe", "M5");
        params.put("count", 10);
        
        // Ottieni i dati OHLC
        Map<String, Object> ohlcData = mt5Commands.getOHLCData("EURUSD", params);
        
        // Verifica che i dati siano corretti
        assertNotNull("I dati OHLC non dovrebbero essere null", ohlcData);
        assertTrue("I dati OHLC dovrebbero contenere il campo 'success'", ohlcData.containsKey("success"));
        assertTrue("I dati OHLC dovrebbero contenere il campo 'symbol'", ohlcData.containsKey("symbol"));
        assertTrue("I dati OHLC dovrebbero contenere il campo 'timeframe'", ohlcData.containsKey("timeframe"));
        assertTrue("I dati OHLC dovrebbero contenere il campo 'ohlc'", ohlcData.containsKey("ohlc"));
        
        // Verifica che i dati OHLC siano corretti
        @SuppressWarnings("unchecked")
        java.util.List<Map<String, Object>> ohlc = (java.util.List<Map<String, Object>>) ohlcData.get("ohlc");
        assertNotNull("I dati OHLC non dovrebbero essere null", ohlc);
        assertFalse("I dati OHLC non dovrebbero essere vuoti", ohlc.isEmpty());
        
        // Verifica che ogni candela contenga i campi corretti
        Map<String, Object> candle = ohlc.get(0);
        assertTrue("La candela dovrebbe contenere il campo 'time'", candle.containsKey("time"));
        assertTrue("La candela dovrebbe contenere il campo 'open'", candle.containsKey("open"));
        assertTrue("La candela dovrebbe contenere il campo 'high'", candle.containsKey("high"));
        assertTrue("La candela dovrebbe contenere il campo 'low'", candle.containsKey("low"));
        assertTrue("La candela dovrebbe contenere il campo 'close'", candle.containsKey("close"));
        assertTrue("La candela dovrebbe contenere il campo 'volume'", candle.containsKey("volume"));
    }
    
    @Test
    public void testMarketBuySell() throws CommandExecutionException {
        // Ottieni i dati di mercato
        Map<String, Object> marketData = mt5Commands.getMarketData("EURUSD");
        double ask = ((Number) marketData.get("ask")).doubleValue();
        
        // Calcola lo stop loss e il take profit
        double stopLoss = ask - 0.0050;
        double takeProfit = ask + 0.0050;
        
        // Apri una posizione
        Map<String, Object> buyResult = mt5Commands.marketBuy("EURUSD", 0.01, stopLoss, takeProfit, "Test", 12345);
        
        // Verifica che la posizione sia stata aperta
        assertNotNull("Il risultato dell'apertura della posizione non dovrebbe essere null", buyResult);
        assertTrue("Il risultato dell'apertura della posizione dovrebbe contenere il campo 'success'", buyResult.containsKey("success"));
        assertTrue("L'apertura della posizione dovrebbe essere avvenuta con successo", (Boolean) buyResult.get("success"));
        assertTrue("Il risultato dell'apertura della posizione dovrebbe contenere il campo 'ticket'", buyResult.containsKey("ticket"));
        
        // Ottieni il ticket della posizione
        long ticket = ((Number) buyResult.get("ticket")).longValue();
        
        // Chiudi la posizione
        Map<String, Object> closeResult = mt5Commands.closePosition(ticket, null);
        
        // Verifica che la posizione sia stata chiusa
        assertNotNull("Il risultato della chiusura della posizione non dovrebbe essere null", closeResult);
        assertTrue("Il risultato della chiusura della posizione dovrebbe contenere il campo 'success'", closeResult.containsKey("success"));
        assertTrue("La chiusura della posizione dovrebbe essere avvenuta con successo", (Boolean) closeResult.get("success"));
    }
}
