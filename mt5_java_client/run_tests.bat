@echo off
echo ===================================
echo MT5 Trading Bot - Test Suite
echo ===================================

REM Verifica se la directory dei log esiste, altrimenti la crea
if not exist logs mkdir logs

REM Imposta le variabili di ambiente
set JAVA_OPTS=-Xms256m -Xmx512m

REM Compila il progetto se necessario
call mvn clean compile test-compile

REM Verifica se la compilazione è andata a buon fine
if %ERRORLEVEL% NEQ 0 (
    echo Errore durante la compilazione del progetto.
    exit /b %ERRORLEVEL%
)

echo.
echo Esecuzione dei test unitari...
echo.

REM Esegui i test unitari
call mvn test -Dtest=MarketDataServiceTest

echo.
echo Esecuzione dei test di integrazione...
echo.

REM Esegui i test di integrazione
call mvn test -Dtest=PythonJavaIntegrationTest

echo.
echo Esecuzione dei test di performance su serie storiche...
echo.

REM Esegui i test di performance su serie storiche
call mvn test -Dtest=HistoricalPerformanceTest

echo.
echo Esecuzione dei test di risk management...
echo.

REM Esegui i test di risk management
call mvn test -Dtest=RiskManagementTest

echo.
echo Tutti i test completati.
echo.

pause
