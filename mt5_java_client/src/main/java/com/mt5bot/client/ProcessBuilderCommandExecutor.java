package com.mt5bot.client;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Implementazione di CommandExecutor che utilizza ProcessBuilder per eseguire comandi.
 * Questa classe è thread-safe e supporta timeout e interruzioni.
 */
public class ProcessBuilderCommandExecutor implements CommandExecutor {
    
    private final AtomicReference<Process> currentProcess = new AtomicReference<>();
    private final ExecutorService executor = Executors.newCachedThreadPool();
    
    /**
     * {@inheritDoc}
     */
    @Override
    public String execute(String command) throws CommandExecutionException {
        return execute(command, new HashMap<>());
    }
    
    /**
     * {@inheritDoc}
     */
    @Override
    public String execute(String command, long timeout, TimeUnit unit) 
            throws CommandExecutionException, CommandTimeoutException {
        return execute(command, new HashMap<>(), timeout, unit);
    }
    
    /**
     * {@inheritDoc}
     */
    @Override
    public String execute(String command, Map<String, String> environmentVars) 
            throws CommandExecutionException {
        try {
            ProcessBuilder processBuilder = createProcessBuilder(command, environmentVars);
            Process process = processBuilder.start();
            currentProcess.set(process);
            
            StringBuilder output = new StringBuilder();
            StringBuilder error = new StringBuilder();
            
            // Leggi l'output standard e l'errore in thread separati
            Future<?> outputFuture = readStream(process.getInputStream(), output);
            Future<?> errorFuture = readStream(process.getErrorStream(), error);
            
            int exitCode = process.waitFor();
            outputFuture.get();
            errorFuture.get();
            
            if (exitCode != 0) {
                throw new CommandExecutionException(
                    "Command execution failed with exit code " + exitCode + ": " + error.toString());
            }
            
            return output.toString();
        } catch (IOException e) {
            throw new CommandExecutionException("Error executing command: " + command, e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new CommandExecutionException("Command execution interrupted: " + command, e);
        } catch (Exception e) {
            throw new CommandExecutionException("Unexpected error executing command: " + command, e);
        } finally {
            currentProcess.set(null);
        }
    }
    
    /**
     * {@inheritDoc}
     */
    @Override
    public String execute(String command, Map<String, String> environmentVars, long timeout, TimeUnit unit) 
            throws CommandExecutionException, CommandTimeoutException {
        Future<String> future = executor.submit(() -> execute(command, environmentVars));
        
        try {
            return future.get(timeout, unit);
        } catch (TimeoutException e) {
            future.cancel(true);
            interrupt();
            throw new CommandTimeoutException("Command execution timed out after " + timeout + " " + unit.name().toLowerCase());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            future.cancel(true);
            throw new CommandExecutionException("Command execution interrupted", e);
        } catch (Exception e) {
            future.cancel(true);
            throw new CommandExecutionException("Error executing command with timeout", e);
        }
    }
    
    /**
     * {@inheritDoc}
     */
    @Override
    public boolean interrupt() {
        Process process = currentProcess.get();
        if (process != null && process.isAlive()) {
            process.destroy();
            try {
                // Attendi un po' per la terminazione normale
                if (!process.waitFor(500, TimeUnit.MILLISECONDS)) {
                    // Se non termina, forza la terminazione
                    process.destroyForcibly();
                }
                return true;
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return false;
            }
        }
        return false;
    }
    
    /**
     * Crea un ProcessBuilder configurato con il comando e le variabili d'ambiente.
     * 
     * @param command Il comando da eseguire
     * @param environmentVars Variabili d'ambiente aggiuntive
     * @return Un ProcessBuilder configurato
     */
    private ProcessBuilder createProcessBuilder(String command, Map<String, String> environmentVars) {
        ProcessBuilder processBuilder;
        
        if (isWindows()) {
            processBuilder = new ProcessBuilder("cmd.exe", "/c", command);
        } else {
            processBuilder = new ProcessBuilder("/bin/sh", "-c", command);
        }
        
        // Aggiungi variabili d'ambiente
        Map<String, String> environment = processBuilder.environment();
        environment.putAll(environmentVars);
        
        // Reindirizza l'errore standard all'output standard
        processBuilder.redirectErrorStream(false);
        
        return processBuilder;
    }
    
    /**
     * Legge uno stream in un thread separato e accumula il contenuto in un StringBuilder.
     * 
     * @param inputStream Lo stream da leggere
     * @param output Il StringBuilder in cui accumulare l'output
     * @return Un Future che rappresenta il task di lettura
     */
    private Future<?> readStream(java.io.InputStream inputStream, StringBuilder output) {
        return executor.submit(() -> {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line).append(System.lineSeparator());
                }
            } catch (IOException e) {
                // Ignora le eccezioni di I/O durante la chiusura dello stream
            }
        });
    }
    
    /**
     * Verifica se il sistema operativo è Windows.
     * 
     * @return true se il sistema operativo è Windows, false altrimenti
     */
    private boolean isWindows() {
        return System.getProperty("os.name").toLowerCase().contains("win");
    }
}
