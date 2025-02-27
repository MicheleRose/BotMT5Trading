@echo off
echo === Compilazione e esecuzione del test del sistema di risk management ===

rem Crea directory per i file compilati
echo Creazione directory build...
if not exist "build" mkdir build

rem Compila le classi Java
echo Compilazione delle classi Java...
javac -d build src\main\java\com\mt5bot\client\*.java src\main\java\com\mt5bot\trading\event\*.java src\main\java\com\mt5bot\trading\model\*.java src\main\java\com\mt5bot\trading\risk\*.java src\test\java\com\mt5bot\trading\risk\RiskManagementTest.java

if %ERRORLEVEL% neq 0 (
    echo Errore durante la compilazione!
    exit /b %ERRORLEVEL%
)

rem Esegui il test
echo Esecuzione del test...
java -cp build com.mt5bot.trading.risk.RiskManagementTest

echo Test completato!
