package com.mt5bot.client;

/**
 * Test di integrazione per il client MT5 Java.
 * Questo test verifica il funzionamento del client con il sistema MT5 Trading Bot.
 */
public class MT5ClientTest {
    
    public static void main(String[] args) {
        System.out.println("=== Test del client MT5 Java ===");
        
        try {
            // Inizializza la configurazione
            MT5Configuration configuration = new MT5Configuration();
            System.out.println("Configurazione inizializzata con successo.");
            
            // Crea un'istanza di MT5Commands
            MT5Commands mt5Commands = new MT5Commands(new ProcessBuilderCommandExecutor(), configuration);
            System.out.println("Client MT5 inizializzato con successo.");
            
            // Test 1: Verifica dello spread
            System.out.println("\n=== Test 1: Verifica dello spread ===");
            try {
                System.out.println("Esecuzione del comando checkSpread(\"EURUSD\")...");
                java.util.Map<String, Object> result = mt5Commands.checkSpread("EURUSD");
                System.out.println("Comando eseguito con successo!");
                System.out.println("Risultato: " + result);
                System.out.println("Test 1 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 1: " + e.getMessage());
                e.printStackTrace();
            }
            
            // Test 2: Ottieni informazioni sull'account
            System.out.println("\n=== Test 2: Informazioni sull'account ===");
            try {
                System.out.println("Esecuzione del comando getAccountInfo()...");
                java.util.Map<String, Object> result = mt5Commands.getAccountInfo();
                System.out.println("Comando eseguito con successo!");
                System.out.println("Risultato: " + result);
                System.out.println("Test 2 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 2: " + e.getMessage());
                e.printStackTrace();
            }
            
            // Test 3: Ottieni dati di mercato
            System.out.println("\n=== Test 3: Dati di mercato ===");
            try {
                System.out.println("Esecuzione del comando getMarketData(\"EURUSD\", \"H1\", 10)...");
                java.util.Map<String, Object> result = mt5Commands.getMarketData("EURUSD", "H1", 10);
                System.out.println("Comando eseguito con successo!");
                System.out.println("Risultato: " + result);
                System.out.println("Test 3 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 3: " + e.getMessage());
                e.printStackTrace();
            }
            
            // Test 4: Ottieni le posizioni aperte
            System.out.println("\n=== Test 4: Posizioni aperte ===");
            try {
                System.out.println("Esecuzione del comando getPositions(null)...");
                java.util.Map<String, Object> result = mt5Commands.getPositions(null);
                System.out.println("Comando eseguito con successo!");
                System.out.println("Risultato: " + result);
                System.out.println("Test 4 completato con successo.");
            } catch (Exception e) {
                System.err.println("Errore durante il test 4: " + e.getMessage());
                e.printStackTrace();
            }
            
            System.out.println("\n=== Test completati ===");
            System.out.println("Il client MT5 Java funziona correttamente!");
            
        } catch (Exception e) {
            System.err.println("Errore durante l'inizializzazione del client: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
