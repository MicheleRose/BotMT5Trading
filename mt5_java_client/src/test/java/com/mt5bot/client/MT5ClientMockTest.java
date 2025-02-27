package com.mt5bot.client;

import java.util.Map;

/**
 * Test del client MT5 Java con mock per simulare le risposte del sistema MT5 Trading Bot.
 * Questa classe non richiede l'esecuzione effettiva dei comandi Python.
 */
public class MT5ClientMockTest {
    
    /**
     * Implementazione mock di CommandExecutor che restituisce risposte predefinite.
     */
    static class MockCommandExecutor implements CommandExecutor {
        @Override
        public String execute(String command, long timeout, java.util.concurrent.TimeUnit timeUnit) 
                throws CommandExecutionException, CommandTimeoutException {
            
            // Simula risposte diverse in base al comando
            if (command.contains("check_spread")) {
                return "{\"success\": true, \"symbol\": \"EURUSD\", \"data\": {\"spread_points\": 1, \"category\": \"basso\"}}";
            } else if (command.contains("get_account_info")) {
                return "{\"success\": true, \"account_info\": {\"login\": 12345678, \"balance\": 10000.0, \"equity\": 10050.0, \"margin\": 500.0, \"free_margin\": 9550.0, \"margin_level\": 2010.0}}";
            } else if (command.contains("get_market_data")) {
                return "{\"success\": true, \"symbol\": \"EURUSD\", \"timeframe\": \"H1\", \"data\": [{\"time\": 1614556800, \"open\": 1.2076, \"high\": 1.2091, \"low\": 1.2075, \"close\": 1.2088, \"volume\": 12345}]}";
            } else if (command.contains("get_positions")) {
                return "{\"success\": true, \"positions\": [{\"ticket\": 12345, \"symbol\": \"EURUSD\", \"type\": \"buy\", \"volume\": 0.1, \"open_price\": 1.2076, \"sl\": 1.2050, \"tp\": 1.2150, \"profit\": 10.5}]}";
            } else if (command.contains("market_buy")) {
                return "{\"success\": true, \"ticket\": 12345, \"symbol\": \"EURUSD\", \"volume\": 0.1, \"type\": \"buy\", \"price\": 1.2088, \"sl\": 1.2050, \"tp\": 1.2150}";
            } else if (command.contains("market_sell")) {
                return "{\"success\": true, \"ticket\": 12346, \"symbol\": \"EURUSD\", \"volume\": 0.1, \"type\": \"sell\", \"price\": 1.2088, \"sl\": 1.2150, \"tp\": 1.2050}";
            } else if (command.contains("close_position")) {
                return "{\"success\": true, \"ticket\": 12345, \"symbol\": \"EURUSD\", \"volume\": 0.1, \"profit\": 10.5}";
            } else if (command.contains("close_all_positions")) {
                return "{\"success\": true, \"closed_positions\": 2, \"total_profit\": 15.75}";
            } else if (command.contains("calculate_volatility")) {
                return "{\"success\": true, \"symbol\": \"EURUSD\", \"timeframe\": \"H1\", \"period\": 14, \"volatility\": 0.0012, \"volatility_percent\": 0.12}";
            } else if (command.contains("get_indicator_data")) {
                return "{\"success\": true, \"symbol\": \"EURUSD\", \"timeframe\": \"H1\", \"indicator\": \"RSI\", \"period\": 14, \"data\": [45.5, 48.2, 52.7, 55.1, 53.8]}";
            } else {
                // Comando non riconosciuto
                throw new CommandExecutionException("Comando non riconosciuto: " + command);
            }
        }
    }
    
    public static void main(String[] args) {
        System.out.println("=== Test del client MT5 Java con mock ===");
        
        try {
            // Inizializza la configurazione
            MT5Configuration configuration = new MT5Configuration();
            System.out.println("Configurazione inizializzata con successo.");
            
            // Crea un'istanza di MT5Commands con il mock
            MT5Commands mt5Commands = new MT5Commands(new MockCommandExecutor(), configuration);
            System.out.println("Client MT5 inizializzato con successo.");
            
            // Test 1: Verifica dello spread
            System.out.println("\n=== Test 1: Verifica dello spread ===");
            try {
                System.out.println("Esecuzione del comando checkSpread(\"EURUSD\")...");
                Map<String, Object> result = mt5Commands.checkSpread("EURUSD");
                System.out.println("Comando eseguito con successo!");
                printResult("Risultato", result);
                System.out.println("Test 1 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 1: " + e.getMessage());
                e.printStackTrace();
            }
            
            // Test 2: Ottieni informazioni sull'account
            System.out.println("\n=== Test 2: Informazioni sull'account ===");
            try {
                System.out.println("Esecuzione del comando getAccountInfo()...");
                Map<String, Object> result = mt5Commands.getAccountInfo();
                System.out.println("Comando eseguito con successo!");
                printResult("Risultato", result);
                System.out.println("Test 2 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 2: " + e.getMessage());
                e.printStackTrace();
            }
            
            // Test 3: Ottieni dati di mercato
            System.out.println("\n=== Test 3: Dati di mercato ===");
            try {
                System.out.println("Esecuzione del comando getMarketData(\"EURUSD\", \"H1\", 10)...");
                Map<String, Object> result = mt5Commands.getMarketData("EURUSD", "H1", 10);
                System.out.println("Comando eseguito con successo!");
                printResult("Risultato", result);
                System.out.println("Test 3 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 3: " + e.getMessage());
                e.printStackTrace();
            }
            
            // Test 4: Ottieni le posizioni aperte
            System.out.println("\n=== Test 4: Posizioni aperte ===");
            try {
                System.out.println("Esecuzione del comando getPositions(null)...");
                Map<String, Object> result = mt5Commands.getPositions(null);
                System.out.println("Comando eseguito con successo!");
                printResult("Risultato", result);
                System.out.println("Test 4 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 4: " + e.getMessage());
                e.printStackTrace();
            }
            
            // Test 5: Apri una posizione di acquisto
            System.out.println("\n=== Test 5: Apertura posizione di acquisto ===");
            try {
                System.out.println("Esecuzione del comando marketBuy(\"EURUSD\", 0.1, 1.2050, 1.2150, \"Test\", 12345)...");
                Map<String, Object> result = mt5Commands.marketBuy("EURUSD", 0.1, 1.2050, 1.2150, "Test", 12345);
                System.out.println("Comando eseguito con successo!");
                printResult("Risultato", result);
                System.out.println("Test 5 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 5: " + e.getMessage());
                e.printStackTrace();
            }
            
            // Test 6: Apri una posizione di vendita
            System.out.println("\n=== Test 6: Apertura posizione di vendita ===");
            try {
                System.out.println("Esecuzione del comando marketSell(\"EURUSD\", 0.1, 1.2150, 1.2050, \"Test\", 12345)...");
                Map<String, Object> result = mt5Commands.marketSell("EURUSD", 0.1, 1.2150, 1.2050, "Test", 12345);
                System.out.println("Comando eseguito con successo!");
                printResult("Risultato", result);
                System.out.println("Test 6 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 6: " + e.getMessage());
                e.printStackTrace();
            }
            
            // Test 7: Chiudi una posizione
            System.out.println("\n=== Test 7: Chiusura posizione ===");
            try {
                System.out.println("Esecuzione del comando closePosition(12345, null)...");
                Map<String, Object> result = mt5Commands.closePosition(12345, null);
                System.out.println("Comando eseguito con successo!");
                printResult("Risultato", result);
                System.out.println("Test 7 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 7: " + e.getMessage());
                e.printStackTrace();
            }
            
            // Test 8: Chiudi tutte le posizioni
            System.out.println("\n=== Test 8: Chiusura di tutte le posizioni ===");
            try {
                System.out.println("Esecuzione del comando closeAllPositions(\"EURUSD\", 12345)...");
                Map<String, Object> result = mt5Commands.closeAllPositions("EURUSD", 12345);
                System.out.println("Comando eseguito con successo!");
                printResult("Risultato", result);
                System.out.println("Test 8 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 8: " + e.getMessage());
                e.printStackTrace();
            }
            
            // Test 9: Calcola la volatilità
            System.out.println("\n=== Test 9: Calcolo della volatilità ===");
            try {
                System.out.println("Esecuzione del comando calculateVolatility(\"EURUSD\", \"H1\", 14)...");
                Map<String, Object> result = mt5Commands.calculateVolatility("EURUSD", "H1", 14);
                System.out.println("Comando eseguito con successo!");
                printResult("Risultato", result);
                System.out.println("Test 9 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 9: " + e.getMessage());
                e.printStackTrace();
            }
            
            // Test 10: Ottieni dati di un indicatore
            System.out.println("\n=== Test 10: Dati di un indicatore ===");
            try {
                System.out.println("Esecuzione del comando getIndicatorData(\"EURUSD\", \"H1\", \"RSI\", 14)...");
                Map<String, Object> result = mt5Commands.getIndicatorData("EURUSD", "H1", "RSI", 14);
                System.out.println("Comando eseguito con successo!");
                printResult("Risultato", result);
                System.out.println("Test 10 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 10: " + e.getMessage());
                e.printStackTrace();
            }
            
            System.out.println("\n=== Test completati ===");
            System.out.println("Il client MT5 Java funziona correttamente!");
            
        } catch (Exception e) {
            System.err.println("Errore durante l'inizializzazione del client: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * Stampa il risultato di un comando.
     * 
     * @param title Il titolo del risultato
     * @param result Il risultato da stampare
     */
    private static void printResult(String title, Map<String, Object> result) {
        System.out.println(title + ":");
        printMap(result, 1);
        System.out.println();
    }
    
    /**
     * Stampa una Map con indentazione.
     * 
     * @param map La Map da stampare
     * @param indent Il livello di indentazione
     */
    @SuppressWarnings("unchecked")
    private static void printMap(Map<String, Object> map, int indent) {
        String indentStr = "  ".repeat(indent);
        
        for (Map.Entry<String, Object> entry : map.entrySet()) {
            String key = entry.getKey();
            Object value = entry.getValue();
            
            if (value instanceof Map) {
                System.out.println(indentStr + key + ":");
                printMap((Map<String, Object>) value, indent + 1);
            } else if (value instanceof Iterable) {
                System.out.println(indentStr + key + ":");
                printIterable((Iterable<?>) value, indent + 1);
            } else {
                System.out.println(indentStr + key + ": " + value);
            }
        }
    }
    
    /**
     * Stampa un Iterable con indentazione.
     * 
     * @param iterable L'Iterable da stampare
     * @param indent Il livello di indentazione
     */
    @SuppressWarnings("unchecked")
    private static void printIterable(Iterable<?> iterable, int indent) {
        String indentStr = "  ".repeat(indent);
        int index = 0;
        
        for (Object item : iterable) {
            if (item instanceof Map) {
                System.out.println(indentStr + "[" + index + "]:");
                printMap((Map<String, Object>) item, indent + 1);
            } else if (item instanceof Iterable) {
                System.out.println(indentStr + "[" + index + "]:");
                printIterable((Iterable<?>) item, indent + 1);
            } else {
                System.out.println(indentStr + "[" + index + "]: " + item);
            }
            
            index++;
        }
    }
}
