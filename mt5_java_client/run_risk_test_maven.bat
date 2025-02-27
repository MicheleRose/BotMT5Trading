@echo off
echo === Compilazione e esecuzione del test del sistema di risk management con Maven ===

rem Compila il progetto
echo Compilazione del progetto...
mvn clean compile

if %ERRORLEVEL% neq 0 (
    echo Errore durante la compilazione!
    exit /b %ERRORLEVEL%
)

rem Esegui i test
echo Esecuzione dei test...
mvn test -Dtest=RiskManagementTest

if %ERRORLEVEL% neq 0 (
    echo Errore durante l'esecuzione dei test!
    exit /b %ERRORLEVEL%
)

rem Esegui il test manualmente
echo Esecuzione del test manuale...
mvn exec:java -Dexec.mainClass="com.mt5bot.trading.risk.RiskManagementTest"

echo Test completato!
