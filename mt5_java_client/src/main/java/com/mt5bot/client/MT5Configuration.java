package com.mt5bot.client;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Properties;
import java.util.concurrent.TimeUnit;

/**
 * Classe di configurazione per il client MT5.
 * Gestisce il caricamento dei parametri da file properties e fornisce valori di default.
 */
public class MT5Configuration {
    
    // Chiavi di configurazione
    private static final String PYTHON_PATH = "python.path";
    private static final String SCRIPTS_BASE_PATH = "scripts.base.path";
    private static final String COMMAND_TIMEOUT = "command.timeout.seconds";
    private static final String RETRY_COUNT = "command.retry.count";
    private static final String RETRY_DELAY = "command.retry.delay.seconds";
    private static final String DEFAULT_MAGIC_NUMBER = "trading.default.magic";
    private static final String CONFIG_FILE_PATH = "mt5.config.file.path";
    
    // Valori di default
    private static final String DEFAULT_PYTHON_PATH = "python";
    private static final String DEFAULT_SCRIPTS_BASE_PATH = "mt5_trading_system";
    private static final int DEFAULT_COMMAND_TIMEOUT = 60;
    private static final int DEFAULT_RETRY_COUNT = 3;
    private static final int DEFAULT_RETRY_DELAY = 2;
    private static final int DEFAULT_MAGIC_NUMBER_VALUE = 123456;
    private static final String DEFAULT_CONFIG_FILE_PATH = "mt5_config.json";
    
    private final Properties properties = new Properties();
    private boolean loaded = false;
    
    /**
     * Costruttore predefinito.
     * Inizializza la configurazione con i valori di default.
     */
    public MT5Configuration() {
        setDefaults();
    }
    
    /**
     * Costruttore che carica la configurazione da un file.
     * 
     * @param configFilePath Il percorso del file di configurazione
     * @throws IOException Se si verifica un errore durante la lettura del file
     */
    public MT5Configuration(String configFilePath) throws IOException {
        setDefaults();
        loadFromFile(configFilePath);
    }
    
    /**
     * Imposta i valori di default per la configurazione.
     */
    private void setDefaults() {
        properties.setProperty(PYTHON_PATH, DEFAULT_PYTHON_PATH);
        properties.setProperty(SCRIPTS_BASE_PATH, DEFAULT_SCRIPTS_BASE_PATH);
        properties.setProperty(COMMAND_TIMEOUT, String.valueOf(DEFAULT_COMMAND_TIMEOUT));
        properties.setProperty(RETRY_COUNT, String.valueOf(DEFAULT_RETRY_COUNT));
        properties.setProperty(RETRY_DELAY, String.valueOf(DEFAULT_RETRY_DELAY));
        properties.setProperty(DEFAULT_MAGIC_NUMBER, String.valueOf(DEFAULT_MAGIC_NUMBER_VALUE));
        properties.setProperty(CONFIG_FILE_PATH, DEFAULT_CONFIG_FILE_PATH);
    }
    
    /**
     * Carica la configurazione da un file.
     * 
     * @param configFilePath Il percorso del file di configurazione
     * @throws IOException Se si verifica un errore durante la lettura del file
     */
    public void loadFromFile(String configFilePath) throws IOException {
        Path path = Paths.get(configFilePath);
        if (!Files.exists(path)) {
            throw new IOException("Configuration file not found: " + configFilePath);
        }
        
        try (InputStream input = new FileInputStream(path.toFile())) {
            properties.load(input);
            loaded = true;
        }
    }
    
    /**
     * Restituisce il percorso dell'eseguibile Python.
     * 
     * @return Il percorso dell'eseguibile Python
     */
    public String getPythonPath() {
        return properties.getProperty(PYTHON_PATH);
    }
    
    /**
     * Imposta il percorso dell'eseguibile Python.
     * 
     * @param pythonPath Il percorso dell'eseguibile Python
     */
    public void setPythonPath(String pythonPath) {
        properties.setProperty(PYTHON_PATH, pythonPath);
    }
    
    /**
     * Restituisce il percorso base degli script Python.
     * 
     * @return Il percorso base degli script Python
     */
    public String getScriptsBasePath() {
        return properties.getProperty(SCRIPTS_BASE_PATH);
    }
    
    /**
     * Imposta il percorso base degli script Python.
     * 
     * @param scriptsBasePath Il percorso base degli script Python
     */
    public void setScriptsBasePath(String scriptsBasePath) {
        properties.setProperty(SCRIPTS_BASE_PATH, scriptsBasePath);
    }
    
    /**
     * Restituisce il timeout per l'esecuzione dei comandi in secondi.
     * 
     * @return Il timeout per l'esecuzione dei comandi in secondi
     */
    public int getCommandTimeoutSeconds() {
        return Integer.parseInt(properties.getProperty(COMMAND_TIMEOUT));
    }
    
    /**
     * Imposta il timeout per l'esecuzione dei comandi in secondi.
     * 
     * @param timeoutSeconds Il timeout per l'esecuzione dei comandi in secondi
     */
    public void setCommandTimeoutSeconds(int timeoutSeconds) {
        properties.setProperty(COMMAND_TIMEOUT, String.valueOf(timeoutSeconds));
    }
    
    /**
     * Restituisce il numero di tentativi per l'esecuzione dei comandi.
     * 
     * @return Il numero di tentativi per l'esecuzione dei comandi
     */
    public int getRetryCount() {
        return Integer.parseInt(properties.getProperty(RETRY_COUNT));
    }
    
    /**
     * Imposta il numero di tentativi per l'esecuzione dei comandi.
     * 
     * @param retryCount Il numero di tentativi per l'esecuzione dei comandi
     */
    public void setRetryCount(int retryCount) {
        properties.setProperty(RETRY_COUNT, String.valueOf(retryCount));
    }
    
    /**
     * Restituisce il ritardo tra i tentativi di esecuzione dei comandi in secondi.
     * 
     * @return Il ritardo tra i tentativi di esecuzione dei comandi in secondi
     */
    public int getRetryDelaySeconds() {
        return Integer.parseInt(properties.getProperty(RETRY_DELAY));
    }
    
    /**
     * Imposta il ritardo tra i tentativi di esecuzione dei comandi in secondi.
     * 
     * @param retryDelaySeconds Il ritardo tra i tentativi di esecuzione dei comandi in secondi
     */
    public void setRetryDelaySeconds(int retryDelaySeconds) {
        properties.setProperty(RETRY_DELAY, String.valueOf(retryDelaySeconds));
    }
    
    /**
     * Restituisce il magic number predefinito per le operazioni di trading.
     * 
     * @return Il magic number predefinito per le operazioni di trading
     */
    public int getDefaultMagicNumber() {
        return Integer.parseInt(properties.getProperty(DEFAULT_MAGIC_NUMBER));
    }
    
    /**
     * Imposta il magic number predefinito per le operazioni di trading.
     * 
     * @param magicNumber Il magic number predefinito per le operazioni di trading
     */
    public void setDefaultMagicNumber(int magicNumber) {
        properties.setProperty(DEFAULT_MAGIC_NUMBER, String.valueOf(magicNumber));
    }
    
    /**
     * Restituisce il percorso del file di configurazione MT5.
     * 
     * @return Il percorso del file di configurazione MT5
     */
    public String getMT5ConfigFilePath() {
        return properties.getProperty(CONFIG_FILE_PATH);
    }
    
    /**
     * Imposta il percorso del file di configurazione MT5.
     * 
     * @param configFilePath Il percorso del file di configurazione MT5
     */
    public void setMT5ConfigFilePath(String configFilePath) {
        properties.setProperty(CONFIG_FILE_PATH, configFilePath);
    }
    
    /**
     * Verifica se la configurazione è stata caricata da un file.
     * 
     * @return true se la configurazione è stata caricata da un file, false altrimenti
     */
    public boolean isLoaded() {
        return loaded;
    }
    
    /**
     * Costruisce il percorso completo di uno script Python.
     * 
     * @param scriptPath Il percorso relativo dello script
     * @return Il percorso completo dello script
     */
    public String buildScriptPath(String scriptPath) {
        // Sostituisci eventuali "/" con "." per il formato corretto del modulo Python
        return getScriptsBasePath() + "." + scriptPath.replace('/', '.');
    }
    
    /**
     * Costruisce il comando Python completo per eseguire uno script.
     * 
     * @param scriptPath Il percorso relativo dello script
     * @param args Gli argomenti da passare allo script
     * @return Il comando Python completo
     */
    public String buildPythonCommand(String scriptPath, String... args) {
        StringBuilder command = new StringBuilder();
        command.append(getPythonPath())
               .append(" -m ")
               .append(buildScriptPath(scriptPath));
        
        // Aggiungi il percorso del file di configurazione MT5 se non è già incluso negli argomenti
        boolean hasConfigArg = false;
        for (String arg : args) {
            if (arg.startsWith("-c ") || arg.startsWith("--config ")) {
                hasConfigArg = true;
                break;
            }
        }
        
        if (!hasConfigArg && !getMT5ConfigFilePath().isEmpty()) {
            command.append(" -c ").append(getMT5ConfigFilePath());
        }
        
        // Aggiungi gli altri argomenti
        for (String arg : args) {
            command.append(" ").append(arg);
        }
        
        return command.toString();
    }
}
