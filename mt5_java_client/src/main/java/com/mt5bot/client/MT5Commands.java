package main.java.com.mt5bot.client;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 * Classe che fornisce metodi per eseguire i comandi Python del sistema MT5 Trading Bot.
 * Implementa wrapper per tutti gli script Python disponibili.
 */
public class MT5Commands {
    
    private static final Logger LOGGER = Logger.getLogger(MT5Commands.class.getName());
    
    private final CommandExecutor commandExecutor;
    private final MT5Configuration configuration;
    
    /**
     * Costruttore con CommandExecutor e configurazione personalizzati.
     * 
     * @param commandExecutor L'esecutore di comandi da utilizzare
     * @param configuration La configurazione da utilizzare
     */
    public MT5Commands(CommandExecutor commandExecutor, MT5Configuration configuration) {
        this.commandExecutor = commandExecutor;
        this.configuration = configuration;
    }
    
    /**
     * Costruttore con configurazione personalizzata.
     * Utilizza ProcessBuilderCommandExecutor come esecutore di comandi.
     * 
     * @param configuration La configurazione da utilizzare
     */
    public MT5Commands(MT5Configuration configuration) {
        this(new ProcessBuilderCommandExecutor(), configuration);
    }
    
    /**
     * Costruttore predefinito.
     * Utilizza ProcessBuilderCommandExecutor come esecutore di comandi e la configurazione predefinita.
     */
    public MT5Commands() {
        this(new ProcessBuilderCommandExecutor(), new MT5Configuration());
    }
    
    /**
     * Esegue un comando Python e restituisce il risultato come Map.
     * 
     * @param scriptPath Il percorso relativo dello script Python
     * @param args Gli argomenti da passare allo script
     * @return Una Map che rappresenta il risultato JSON del comando
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> executeCommand(String scriptPath, String... args) throws CommandExecutionException {
        return executeCommandWithRetry(scriptPath, args);
    }
    
    /**
     * Esegue un comando Python con tentativi multipli e restituisce il risultato come Map.
     * 
     * @param scriptPath Il percorso relativo dello script Python
     * @param args Gli argomenti da passare allo script
     * @return Una Map che rappresenta il risultato JSON del comando
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    private Map<String, Object> executeCommandWithRetry(String scriptPath, String... args) throws CommandExecutionException {
        int retryCount = configuration.getRetryCount();
        int retryDelay = configuration.getRetryDelaySeconds();
        
        CommandExecutionException lastException = null;
        
        for (int attempt = 0; attempt <= retryCount; attempt++) {
            try {
                String command = configuration.buildPythonCommand(scriptPath, args);
                LOGGER.log(Level.INFO, "Executing command: {0}", command);
                
                String result = commandExecutor.execute(command, configuration.getCommandTimeoutSeconds(), TimeUnit.SECONDS);
                LOGGER.log(Level.FINE, "Command result: {0}", result);
                
                return JsonParser.parseJson(result);
            } catch (CommandExecutionException | CommandTimeoutException e) {
                lastException = new CommandExecutionException("Error executing command: " + scriptPath, e);
                LOGGER.log(Level.WARNING, "Command execution failed (attempt {0}/{1}): {2}", 
                        new Object[]{attempt + 1, retryCount + 1, e.getMessage()});
                
                if (attempt < retryCount) {
                    try {
                        Thread.sleep(retryDelay * 1000L);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new CommandExecutionException("Command execution interrupted", ie);
                    }
                }
            } catch (IllegalArgumentException e) {
                throw new CommandExecutionException("Error parsing JSON result: " + e.getMessage(), e);
            }
        }
        
        throw lastException;
    }
    
    /**
     * Verifica se un comando è stato eseguito con successo.
     * 
     * @param result Il risultato del comando
     * @return true se il comando è stato eseguito con successo, false altrimenti
     */
    private boolean isSuccess(Map<String, Object> result) {
        return JsonParser.getBooleanFromPath(result, "success", false);
    }
    
    /**
     * Ottiene il messaggio di errore da un risultato di comando.
     * 
     * @param result Il risultato del comando
     * @return Il messaggio di errore o null se non presente
     */
    private String getErrorMessage(Map<String, Object> result) {
        return JsonParser.getStringFromPath(result, "error", null);
    }
    
    /**
     * Verifica lo spread di un simbolo.
     * 
     * @param symbol Il simbolo da verificare
     * @return Una Map con le informazioni sullo spread
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> checkSpread(String symbol) throws CommandExecutionException {
        Map<String, Object> result = executeCommand("analysis.check_spread", symbol);
        
        if (!isSuccess(result)) {
            throw new CommandExecutionException("Check spread failed: " + getErrorMessage(result));
        }
        
        return result;
    }
    
    /**
     * Ottiene dati di mercato per un simbolo e timeframe.
     * 
     * @param symbol Il simbolo
     * @param timeframe Il timeframe
     * @param count Il numero di candele da ottenere
     * @return Una Map con i dati di mercato
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> getMarketData(String symbol, String timeframe, int count) throws CommandExecutionException {
        Map<String, Object> result = executeCommand("analysis.get_market_data", 
                symbol, timeframe, String.valueOf(count));
        
        if (!isSuccess(result)) {
            throw new CommandExecutionException("Get market data failed: " + getErrorMessage(result));
        }
        
        return result;
    }
    
    /**
     * Calcola la volatilità di un simbolo.
     * 
     * @param symbol Il simbolo
     * @param timeframe Il timeframe
     * @param period Il periodo per il calcolo
     * @return Una Map con le informazioni sulla volatilità
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> calculateVolatility(String symbol, String timeframe, int period) throws CommandExecutionException {
        Map<String, Object> result = executeCommand("analysis.calculate_volatility", 
                symbol, timeframe, "--period", String.valueOf(period));
        
        if (!isSuccess(result)) {
            throw new CommandExecutionException("Calculate volatility failed: " + getErrorMessage(result));
        }
        
        return result;
    }
    
    /**
     * Ottiene dati di un indicatore tecnico.
     * 
     * @param symbol Il simbolo
     * @param timeframe Il timeframe
     * @param indicator L'indicatore da calcolare
     * @param period Il periodo per il calcolo
     * @return Una Map con i dati dell'indicatore
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> getIndicatorData(String symbol, String timeframe, String indicator, int period) throws CommandExecutionException {
        Map<String, Object> result = executeCommand("analysis.get_indicator_data", 
                symbol, timeframe, indicator, "--period", String.valueOf(period));
        
        if (!isSuccess(result)) {
            throw new CommandExecutionException("Get indicator data failed: " + getErrorMessage(result));
        }
        
        return result;
    }
    
    /**
     * Ottiene informazioni sull'account.
     * 
     * @return Una Map con le informazioni sull'account
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> getAccountInfo() throws CommandExecutionException {
        Map<String, Object> result = executeCommand("commands.get_account_info");
        
        if (!isSuccess(result)) {
            throw new CommandExecutionException("Get account info failed: " + getErrorMessage(result));
        }
        
        return result;
    }
    
    /**
     * Ottiene le posizioni aperte.
     * 
     * @param symbol Il simbolo (opzionale)
     * @return Una Map con le posizioni aperte
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> getPositions(String symbol) throws CommandExecutionException {
        String[] args = symbol != null && !symbol.isEmpty() ? new String[]{symbol} : new String[0];
        Map<String, Object> result = executeCommand("commands.get_positions", args);
        
        if (!isSuccess(result)) {
            throw new CommandExecutionException("Get positions failed: " + getErrorMessage(result));
        }
        
        return result;
    }
    
    /**
     * Apre una posizione di acquisto a mercato.
     * 
     * @param symbol Il simbolo
     * @param volume Il volume
     * @param stopLoss Il livello di stop loss (opzionale)
     * @param takeProfit Il livello di take profit (opzionale)
     * @param comment Il commento (opzionale)
     * @param magicNumber Il magic number (opzionale)
     * @return Una Map con le informazioni sulla posizione aperta
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> marketBuy(String symbol, double volume, Double stopLoss, Double takeProfit, 
            String comment, Integer magicNumber) throws CommandExecutionException {
        
        Map<String, String> args = new HashMap<>();
        args.put("symbol", symbol);
        args.put("volume", String.valueOf(volume));
        
        if (stopLoss != null) {
            args.put("sl", String.valueOf(stopLoss));
        }
        
        if (takeProfit != null) {
            args.put("tp", String.valueOf(takeProfit));
        }
        
        if (comment != null && !comment.isEmpty()) {
            args.put("comment", comment);
        }
        
        if (magicNumber != null) {
            args.put("magic", String.valueOf(magicNumber));
        } else if (configuration.getDefaultMagicNumber() > 0) {
            args.put("magic", String.valueOf(configuration.getDefaultMagicNumber()));
        }
        
        String[] commandArgs = buildCommandArgs(args);
        Map<String, Object> result = executeCommand("commands.market_buy", commandArgs);
        
        if (!isSuccess(result)) {
            throw new CommandExecutionException("Market buy failed: " + getErrorMessage(result));
        }
        
        return result;
    }
    
    /**
     * Apre una posizione di vendita a mercato.
     * 
     * @param symbol Il simbolo
     * @param volume Il volume
     * @param stopLoss Il livello di stop loss (opzionale)
     * @param takeProfit Il livello di take profit (opzionale)
     * @param comment Il commento (opzionale)
     * @param magicNumber Il magic number (opzionale)
     * @return Una Map con le informazioni sulla posizione aperta
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> marketSell(String symbol, double volume, Double stopLoss, Double takeProfit, 
            String comment, Integer magicNumber) throws CommandExecutionException {
        
        Map<String, String> args = new HashMap<>();
        args.put("symbol", symbol);
        args.put("volume", String.valueOf(volume));
        
        if (stopLoss != null) {
            args.put("sl", String.valueOf(stopLoss));
        }
        
        if (takeProfit != null) {
            args.put("tp", String.valueOf(takeProfit));
        }
        
        if (comment != null && !comment.isEmpty()) {
            args.put("comment", comment);
        }
        
        if (magicNumber != null) {
            args.put("magic", String.valueOf(magicNumber));
        } else if (configuration.getDefaultMagicNumber() > 0) {
            args.put("magic", String.valueOf(configuration.getDefaultMagicNumber()));
        }
        
        String[] commandArgs = buildCommandArgs(args);
        Map<String, Object> result = executeCommand("commands.market_sell", commandArgs);
        
        if (!isSuccess(result)) {
            throw new CommandExecutionException("Market sell failed: " + getErrorMessage(result));
        }
        
        return result;
    }
    
    /**
     * Modifica una posizione.
     * 
     * @param ticket Il ticket della posizione
     * @param stopLoss Il nuovo livello di stop loss (opzionale)
     * @param takeProfit Il nuovo livello di take profit (opzionale)
     * @return Una Map con le informazioni sulla posizione modificata
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> modifyPosition(long ticket, Double stopLoss, Double takeProfit) throws CommandExecutionException {
        Map<String, String> args = new HashMap<>();
        args.put("ticket", String.valueOf(ticket));
        
        if (stopLoss != null) {
            args.put("sl", String.valueOf(stopLoss));
        }
        
        if (takeProfit != null) {
            args.put("tp", String.valueOf(takeProfit));
        }
        
        String[] commandArgs = buildCommandArgs(args);
        Map<String, Object> result = executeCommand("commands.modify_position", commandArgs);
        
        if (!isSuccess(result)) {
            throw new CommandExecutionException("Modify position failed: " + getErrorMessage(result));
        }
        
        return result;
    }
    
    /**
     * Chiude una posizione.
     * 
     * @param ticket Il ticket della posizione
     * @param volume Il volume da chiudere (opzionale, se non specificato chiude tutta la posizione)
     * @return Una Map con le informazioni sulla posizione chiusa
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> closePosition(long ticket, Double volume) throws CommandExecutionException {
        Map<String, String> args = new HashMap<>();
        args.put("ticket", String.valueOf(ticket));
        
        if (volume != null) {
            args.put("volume", String.valueOf(volume));
        }
        
        String[] commandArgs = buildCommandArgs(args);
        Map<String, Object> result = executeCommand("commands.close_position", commandArgs);
        
        if (!isSuccess(result)) {
            throw new CommandExecutionException("Close position failed: " + getErrorMessage(result));
        }
        
        return result;
    }
    
    /**
     * Chiude tutte le posizioni.
     * 
     * @param symbol Il simbolo (opzionale, se non specificato chiude tutte le posizioni)
     * @param magicNumber Il magic number (opzionale, se non specificato chiude tutte le posizioni)
     * @return Una Map con le informazioni sulle posizioni chiuse
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> closeAllPositions(String symbol, Integer magicNumber) throws CommandExecutionException {
        Map<String, String> args = new HashMap<>();
        
        if (symbol != null && !symbol.isEmpty()) {
            args.put("symbol", symbol);
        }
        
        if (magicNumber != null) {
            args.put("magic", String.valueOf(magicNumber));
        }
        
        String[] commandArgs = buildCommandArgs(args);
        Map<String, Object> result = executeCommand("commands.close_all_positions", commandArgs);
        
        if (!isSuccess(result)) {
            throw new CommandExecutionException("Close all positions failed: " + getErrorMessage(result));
        }
        
        return result;
    }
    
    /**
     * Addestra un modello LSTM per la previsione della direzione dei prezzi.
     * 
     * @param symbol Il simbolo
     * @param timeframe Il timeframe
     * @param trainingPeriod Il numero di candele per l'addestramento
     * @param outputPath Il percorso dove salvare il modello
     * @param epochs Il numero di epoche per l'addestramento (opzionale)
     * @param batchSize La dimensione del batch per l'addestramento (opzionale)
     * @param debug Attiva la modalità debug (opzionale)
     * @return Una Map con le informazioni sull'addestramento
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> trainModel(String symbol, String timeframe, int trainingPeriod, String outputPath,
            Integer epochs, Integer batchSize, boolean debug) throws CommandExecutionException {
        
        Map<String, String> args = new HashMap<>();
        args.put("symbol", symbol);
        args.put("timeframe", timeframe);
        args.put("training_period", String.valueOf(trainingPeriod));
        args.put("output_path", outputPath);
        
        if (epochs != null) {
            args.put("-e", String.valueOf(epochs));
        }
        
        if (batchSize != null) {
            args.put("-b", String.valueOf(batchSize));
        }
        
        if (debug) {
            args.put("-d", "");
        }
        
        String[] commandArgs = buildCommandArgs(args);
        Map<String, Object> result = executeCommand("ml.train_model", commandArgs);
        
        return result;
    }
    
    /**
     * Genera una previsione sulla direzione dei prezzi utilizzando un modello LSTM.
     * 
     * @param symbol Il simbolo
     * @param modelPath Il percorso al modello salvato
     * @param scalersPath Il percorso agli scalers salvati (opzionale)
     * @param numCandles Il numero di candele da ottenere (opzionale)
     * @param timeframe Il timeframe (opzionale)
     * @param outputPath Il percorso dove salvare la previsione (opzionale)
     * @param debug Attiva la modalità debug (opzionale)
     * @return Una Map con la previsione
     * @throws CommandExecutionException Se si verifica un errore durante l'esecuzione
     */
    public Map<String, Object> predictDirection(String symbol, String modelPath, String scalersPath,
            Integer numCandles, String timeframe, String outputPath, boolean debug) throws CommandExecutionException {
        
        Map<String, String> args = new HashMap<>();
        args.put("symbol", symbol);
        args.put("model_path", modelPath);
        
        if (scalersPath != null && !scalersPath.isEmpty()) {
            args.put("-s", scalersPath);
        }
        
        if (numCandles != null) {
            args.put("-n", String.valueOf(numCandles));
        }
        
        if (timeframe != null && !timeframe.isEmpty()) {
            args.put("-t", timeframe);
        }
        
        if (outputPath != null && !outputPath.isEmpty()) {
            args.put("-o", outputPath);
        }
        
        if (debug) {
            args.put("-d", "");
        }
        
        String[] commandArgs = buildCommandArgs(args);
        Map<String, Object> result = executeCommand("ml.predict_direction", commandArgs);
        
        return result;
    }
    
    /**
     * Costruisce un array di argomenti per un comando a partire da una Map.
     * 
     * @param args La Map di argomenti
     * @return Un array di stringhe con gli argomenti
     */
    private String[] buildCommandArgs(Map<String, String> args) {
        return args.entrySet().stream()
                .flatMap(entry -> {
                    if (entry.getValue().isEmpty()) {
                        return java.util.stream.Stream.of(entry.getKey());
                    } else {
                        return java.util.stream.Stream.of(entry.getKey(), entry.getValue());
                    }
                })
                .toArray(String[]::new);
    }
}
