package com.mt5bot.client.examples;

import com.mt5bot.client.CommandExecutionException;
import com.mt5bot.client.MT5Commands;
import com.mt5bot.client.MT5Configuration;
import com.mt5bot.client.ProcessBuilderCommandExecutor;

import java.io.IOException;
import java.util.Map;

/**
 * Esempio di utilizzo del client MT5 Java.
 */
public class MT5ClientExample {
    
    public static void main(String[] args) {
        try {
            // Carica la configurazione da file
            MT5Configuration configuration = loadConfiguration();
            
            // Crea un'istanza di MT5Commands
            MT5Commands mt5Commands = new MT5Commands(new ProcessBuilderCommandExecutor(), configuration);
            
            // Esegui alcuni comandi di esempio
            runExamples(mt5Commands);
            
        } catch (Exception e) {
            System.err.println("Errore: " + e.getMessage());
            e.printStackTrace();
        }
    }
    
    /**
     * Carica la configurazione da file.
     * 
     * @return La configurazione caricata
     */
    private static MT5Configuration loadConfiguration() {
        MT5Configuration configuration = new MT5Configuration();
        
        try {
            // Carica la configurazione dal file di properties
            configuration.loadFromFile("mt5_java_client/src/main/resources/mt5_client.properties");
            System.out.println("Configurazione caricata con successo.");
        } catch (IOException e) {
            System.out.println("Impossibile caricare la configurazione da file, utilizzo valori di default.");
        }
        
        return configuration;
    }
    
    /**
     * Esegue alcuni comandi di esempio.
     * 
     * @param mt5Commands L'istanza di MT5Commands da utilizzare
     */
    private static void runExamples(MT5Commands mt5Commands) {
        try {
            // Esempio 1: Verifica lo spread di EURUSD
            System.out.println("\n=== Esempio 1: Verifica dello spread ===");
            Map<String, Object> spreadResult = mt5Commands.checkSpread("EURUSD");
            printResult("Spread", spreadResult);
            
            // Esempio 2: Ottieni informazioni sull'account
            System.out.println("\n=== Esempio 2: Informazioni sull'account ===");
            Map<String, Object> accountInfo = mt5Commands.getAccountInfo();
            printResult("Account Info", accountInfo);
            
            // Esempio 3: Ottieni dati di mercato
            System.out.println("\n=== Esempio 3: Dati di mercato ===");
            Map<String, Object> marketData = mt5Commands.getMarketData("EURUSD", "H1", 10);
            printResult("Market Data", marketData);
            
            // Esempio 4: Calcola la volatilità
            System.out.println("\n=== Esempio 4: Calcolo della volatilità ===");
            Map<String, Object> volatility = mt5Commands.calculateVolatility("EURUSD", "H1", 14);
            printResult("Volatility", volatility);
            
            // Esempio 5: Ottieni dati di un indicatore
            System.out.println("\n=== Esempio 5: Dati di un indicatore ===");
            Map<String, Object> indicatorData = mt5Commands.getIndicatorData("EURUSD", "H1", "RSI", 14);
            printResult("Indicator Data", indicatorData);
            
            // Esempio 6: Ottieni le posizioni aperte
            System.out.println("\n=== Esempio 6: Posizioni aperte ===");
            Map<String, Object> positions = mt5Commands.getPositions(null);
            printResult("Positions", positions);
            
            // Esempio 7: Previsione della direzione dei prezzi
            // Nota: questo esempio richiede un modello addestrato
            /*
            System.out.println("\n=== Esempio 7: Previsione della direzione dei prezzi ===");
            Map<String, Object> prediction = mt5Commands.predictDirection(
                "EURUSD", 
                "./models/lstm/models/EURUSD_H1_model.keras", 
                "./models/lstm/scalers/EURUSD_H1_scalers.pkl", 
                100, 
                "H1", 
                null, 
                false
            );
            printResult("Prediction", prediction);
            */
            
        } catch (CommandExecutionException e) {
            System.err.println("Errore durante l'esecuzione dei comandi: " + e.getMessage());
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
