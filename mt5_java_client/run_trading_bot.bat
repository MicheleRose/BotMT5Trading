@echo off
echo ===================================
echo MT5 Trading Bot - Avvio
echo ===================================

REM Verifica se la directory dei log esiste, altrimenti la crea
if not exist logs mkdir logs

REM Imposta le variabili di ambiente
set JAVA_OPTS=-Xms256m -Xmx512m

REM Compila il progetto se necessario
call mvn clean compile package -DskipTests

REM Verifica se la compilazione è andata a buon fine
if %ERRORLEVEL% NEQ 0 (
    echo Errore durante la compilazione del progetto.
    exit /b %ERRORLEVEL%
)

echo.
echo Avvio del Trading Bot...
echo.

REM Avvia il trading bot
java %JAVA_OPTS% -cp target/mt5-java-client-1.0-SNAPSHOT-jar-with-dependencies.jar main.java.com.mt5bot.trading.TradingBot config/trading_bot.properties

REM Verifica se l'esecuzione è andata a buon fine
if %ERRORLEVEL% NEQ 0 (
    echo Errore durante l'esecuzione del Trading Bot.
    exit /b %ERRORLEVEL%
)

echo.
echo Trading Bot terminato.
echo.

pause
