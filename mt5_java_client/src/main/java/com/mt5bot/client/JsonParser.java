package main.java.com.mt5bot.client;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Classe di utilità per il parsing JSON.
 * Implementazione semplice senza dipendenze esterne.
 */
public class JsonParser {
    
    /**
     * Converte una stringa JSON in un oggetto Map.
     * 
     * @param jsonString La stringa JSON da convertire
     * @return Una Map che rappresenta l'oggetto JSON
     * @throws IllegalArgumentException Se la stringa JSON non è valida
     */
    public static Map<String, Object> parseJson(String jsonString) {
        try {
            return (Map<String, Object>) parseValue(jsonString.trim());
        } catch (Exception e) {
            throw new IllegalArgumentException("Invalid JSON string: " + jsonString, e);
        }
    }
    
    /**
     * Analizza un valore JSON.
     * 
     * @param json La stringa JSON da analizzare
     * @return L'oggetto Java corrispondente
     */
    private static Object parseValue(String json) {
        json = json.trim();
        
        if (json.isEmpty()) {
            return null;
        }
        
        if (json.startsWith("{")) {
            return parseObject(json);
        } else if (json.startsWith("[")) {
            return parseArray(json);
        } else if (json.startsWith("\"")) {
            return parseString(json);
        } else if (json.equals("true")) {
            return Boolean.TRUE;
        } else if (json.equals("false")) {
            return Boolean.FALSE;
        } else if (json.equals("null")) {
            return null;
        } else {
            return parseNumber(json);
        }
    }
    
    /**
     * Analizza un oggetto JSON.
     * 
     * @param json La stringa JSON da analizzare
     * @return Una Map che rappresenta l'oggetto JSON
     */
    private static Map<String, Object> parseObject(String json) {
        Map<String, Object> map = new HashMap<>();
        
        // Rimuovi le parentesi graffe
        json = json.substring(1, json.length() - 1).trim();
        
        if (json.isEmpty()) {
            return map;
        }
        
        // Analizza le coppie chiave-valore
        int i = 0;
        while (i < json.length()) {
            // Trova la chiave
            if (json.charAt(i) != '\"') {
                throw new IllegalArgumentException("Expected '\"' at position " + i);
            }
            
            int keyStart = i + 1;
            int keyEnd = findEndOfString(json, keyStart);
            String key = json.substring(keyStart, keyEnd);
            
            i = keyEnd + 1;
            
            // Trova il separatore
            while (i < json.length() && Character.isWhitespace(json.charAt(i))) {
                i++;
            }
            
            if (i >= json.length() || json.charAt(i) != ':') {
                throw new IllegalArgumentException("Expected ':' at position " + i);
            }
            
            i++;
            
            // Trova il valore
            while (i < json.length() && Character.isWhitespace(json.charAt(i))) {
                i++;
            }
            
            // Trova la fine del valore
            int valueEnd = findEndOfValue(json, i);
            String valueStr = json.substring(i, valueEnd);
            Object value = parseValue(valueStr);
            
            map.put(key, value);
            
            i = valueEnd;
            
            // Trova la virgola o la fine dell'oggetto
            while (i < json.length() && Character.isWhitespace(json.charAt(i))) {
                i++;
            }
            
            if (i >= json.length()) {
                break;
            }
            
            if (json.charAt(i) == ',') {
                i++;
                while (i < json.length() && Character.isWhitespace(json.charAt(i))) {
                    i++;
                }
            } else if (json.charAt(i) != '}') {
                throw new IllegalArgumentException("Expected ',' or '}' at position " + i);
            }
        }
        
        return map;
    }
    
    /**
     * Analizza un array JSON.
     * 
     * @param json La stringa JSON da analizzare
     * @return Una List che rappresenta l'array JSON
     */
    private static List<Object> parseArray(String json) {
        List<Object> list = new ArrayList<>();
        
        // Rimuovi le parentesi quadre
        json = json.substring(1, json.length() - 1).trim();
        
        if (json.isEmpty()) {
            return list;
        }
        
        // Analizza i valori
        int i = 0;
        while (i < json.length()) {
            // Trova il valore
            int valueEnd = findEndOfValue(json, i);
            String valueStr = json.substring(i, valueEnd);
            Object value = parseValue(valueStr);
            
            list.add(value);
            
            i = valueEnd;
            
            // Trova la virgola o la fine dell'array
            while (i < json.length() && Character.isWhitespace(json.charAt(i))) {
                i++;
            }
            
            if (i >= json.length()) {
                break;
            }
            
            if (json.charAt(i) == ',') {
                i++;
                while (i < json.length() && Character.isWhitespace(json.charAt(i))) {
                    i++;
                }
            } else if (json.charAt(i) != ']') {
                throw new IllegalArgumentException("Expected ',' or ']' at position " + i);
            }
        }
        
        return list;
    }
    
    /**
     * Analizza una stringa JSON.
     * 
     * @param json La stringa JSON da analizzare
     * @return La stringa Java corrispondente
     */
    private static String parseString(String json) {
        // Rimuovi le virgolette
        return json.substring(1, json.length() - 1);
    }
    
    /**
     * Analizza un numero JSON.
     * 
     * @param json La stringa JSON da analizzare
     * @return Il numero Java corrispondente
     */
    private static Number parseNumber(String json) {
        try {
            if (json.contains(".") || json.contains("e") || json.contains("E")) {
                return Double.parseDouble(json);
            } else {
                return Long.parseLong(json);
            }
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Invalid number: " + json, e);
        }
    }
    
    /**
     * Trova la fine di una stringa JSON.
     * 
     * @param json La stringa JSON da analizzare
     * @param start La posizione di inizio
     * @return La posizione di fine
     */
    private static int findEndOfString(String json, int start) {
        int i = start;
        boolean escaped = false;
        
        while (i < json.length()) {
            char c = json.charAt(i);
            
            if (escaped) {
                escaped = false;
            } else if (c == '\\') {
                escaped = true;
            } else if (c == '\"') {
                return i;
            }
            
            i++;
        }
        
        throw new IllegalArgumentException("Unterminated string");
    }
    
    /**
     * Trova la fine di un valore JSON.
     * 
     * @param json La stringa JSON da analizzare
     * @param start La posizione di inizio
     * @return La posizione di fine
     */
    private static int findEndOfValue(String json, int start) {
        int i = start;
        
        if (i >= json.length()) {
            return i;
        }
        
        char c = json.charAt(i);
        
        if (c == '{') {
            return findEndOfObject(json, i);
        } else if (c == '[') {
            return findEndOfArray(json, i);
        } else if (c == '\"') {
            return findEndOfString(json, i + 1) + 1;
        } else if (c == 't' && json.startsWith("true", i)) {
            return i + 4;
        } else if (c == 'f' && json.startsWith("false", i)) {
            return i + 5;
        } else if (c == 'n' && json.startsWith("null", i)) {
            return i + 4;
        } else {
            // Numero
            while (i < json.length() && !isEndOfValue(json.charAt(i))) {
                i++;
            }
            return i;
        }
    }
    
    /**
     * Trova la fine di un oggetto JSON.
     * 
     * @param json La stringa JSON da analizzare
     * @param start La posizione di inizio
     * @return La posizione di fine
     */
    private static int findEndOfObject(String json, int start) {
        int i = start + 1;
        int depth = 1;
        boolean inString = false;
        boolean escaped = false;
        
        while (i < json.length() && depth > 0) {
            char c = json.charAt(i);
            
            if (inString) {
                if (escaped) {
                    escaped = false;
                } else if (c == '\\') {
                    escaped = true;
                } else if (c == '\"') {
                    inString = false;
                }
            } else if (c == '\"') {
                inString = true;
            } else if (c == '{') {
                depth++;
            } else if (c == '}') {
                depth--;
            }
            
            i++;
        }
        
        if (depth > 0) {
            throw new IllegalArgumentException("Unterminated object");
        }
        
        return i;
    }
    
    /**
     * Trova la fine di un array JSON.
     * 
     * @param json La stringa JSON da analizzare
     * @param start La posizione di inizio
     * @return La posizione di fine
     */
    private static int findEndOfArray(String json, int start) {
        int i = start + 1;
        int depth = 1;
        boolean inString = false;
        boolean escaped = false;
        
        while (i < json.length() && depth > 0) {
            char c = json.charAt(i);
            
            if (inString) {
                if (escaped) {
                    escaped = false;
                } else if (c == '\\') {
                    escaped = true;
                } else if (c == '\"') {
                    inString = false;
                }
            } else if (c == '\"') {
                inString = true;
            } else if (c == '[') {
                depth++;
            } else if (c == ']') {
                depth--;
            }
            
            i++;
        }
        
        if (depth > 0) {
            throw new IllegalArgumentException("Unterminated array");
        }
        
        return i;
    }
    
    /**
     * Verifica se un carattere indica la fine di un valore JSON.
     * 
     * @param c Il carattere da verificare
     * @return true se il carattere indica la fine di un valore JSON, false altrimenti
     */
    private static boolean isEndOfValue(char c) {
        return c == ',' || c == '}' || c == ']' || Character.isWhitespace(c);
    }
    
    /**
     * Estrae un valore da una Map utilizzando un percorso di chiavi.
     * 
     * @param <T> Il tipo del valore da estrarre
     * @param map La Map da cui estrarre il valore
     * @param path Il percorso di chiavi separato da punti
     * @param defaultValue Il valore predefinito da restituire se il percorso non esiste
     * @return Il valore estratto o il valore predefinito
     */
    @SuppressWarnings("unchecked")
    public static <T> T getValueFromPath(Map<String, Object> map, String path, T defaultValue) {
        String[] keys = path.split("\\.");
        Map<String, Object> currentMap = map;
        
        for (int i = 0; i < keys.length - 1; i++) {
            Object value = currentMap.get(keys[i]);
            if (value instanceof Map) {
                currentMap = (Map<String, Object>) value;
            } else {
                return defaultValue;
            }
        }
        
        Object value = currentMap.get(keys[keys.length - 1]);
        if (value == null) {
            return defaultValue;
        }
        
        try {
            return (T) value;
        } catch (ClassCastException e) {
            return defaultValue;
        }
    }
    
    /**
     * Estrae un valore booleano da una Map utilizzando un percorso di chiavi.
     * 
     * @param map La Map da cui estrarre il valore
     * @param path Il percorso di chiavi separato da punti
     * @param defaultValue Il valore predefinito da restituire se il percorso non esiste
     * @return Il valore booleano estratto o il valore predefinito
     */
    public static boolean getBooleanFromPath(Map<String, Object> map, String path, boolean defaultValue) {
        Object value = getValueFromPath(map, path, null);
        if (value instanceof Boolean) {
            return (Boolean) value;
        } else if (value instanceof String) {
            return Boolean.parseBoolean((String) value);
        } else if (value instanceof Number) {
            return ((Number) value).intValue() != 0;
        } else {
            return defaultValue;
        }
    }
    
    /**
     * Estrae un valore intero da una Map utilizzando un percorso di chiavi.
     * 
     * @param map La Map da cui estrarre il valore
     * @param path Il percorso di chiavi separato da punti
     * @param defaultValue Il valore predefinito da restituire se il percorso non esiste
     * @return Il valore intero estratto o il valore predefinito
     */
    public static int getIntFromPath(Map<String, Object> map, String path, int defaultValue) {
        Object value = getValueFromPath(map, path, null);
        if (value instanceof Number) {
            return ((Number) value).intValue();
        } else if (value instanceof String) {
            try {
                return Integer.parseInt((String) value);
            } catch (NumberFormatException e) {
                return defaultValue;
            }
        } else {
            return defaultValue;
        }
    }
    
    /**
     * Estrae un valore double da una Map utilizzando un percorso di chiavi.
     * 
     * @param map La Map da cui estrarre il valore
     * @param path Il percorso di chiavi separato da punti
     * @param defaultValue Il valore predefinito da restituire se il percorso non esiste
     * @return Il valore double estratto o il valore predefinito
     */
    public static double getDoubleFromPath(Map<String, Object> map, String path, double defaultValue) {
        Object value = getValueFromPath(map, path, null);
        if (value instanceof Number) {
            return ((Number) value).doubleValue();
        } else if (value instanceof String) {
            try {
                return Double.parseDouble((String) value);
            } catch (NumberFormatException e) {
                return defaultValue;
            }
        } else {
            return defaultValue;
        }
    }
    
    /**
     * Estrae un valore stringa da una Map utilizzando un percorso di chiavi.
     * 
     * @param map La Map da cui estrarre il valore
     * @param path Il percorso di chiavi separato da punti
     * @param defaultValue Il valore predefinito da restituire se il percorso non esiste
     * @return Il valore stringa estratto o il valore predefinito
     */
    public static String getStringFromPath(Map<String, Object> map, String path, String defaultValue) {
        Object value = getValueFromPath(map, path, null);
        if (value != null) {
            return value.toString();
        } else {
            return defaultValue;
        }
    }
}
