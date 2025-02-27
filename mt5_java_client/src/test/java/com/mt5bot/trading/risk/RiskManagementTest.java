package test.java.com.mt5bot.trading.risk;

import main.java.com.mt5bot.client.CommandExecutionException;
import main.java.com.mt5bot.client.MT5Commands;
import main.java.com.mt5bot.trading.event.TradingEvent;
import main.java.com.mt5bot.trading.event.TradingEventListener;
import main.java.com.mt5bot.trading.event.TradingEventManager;
import main.java.com.mt5bot.trading.model.Position;
import main.java.com.mt5bot.trading.model.Position.PositionType;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.logging.ConsoleHandler;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.logging.SimpleFormatter;

/**
 * Test del sistema di risk management.
 * Verifica il funzionamento dei componenti di risk management.
 */
public class RiskManagementTest implements TradingEventListener {
    
    private static final Logger LOGGER = Logger.getLogger(RiskManagementTest.class.getName());
    
    // Componenti del sistema
    private MT5Commands mt5Commands;
    private TradingEventManager eventManager;
    private DefaultRiskManager riskManager;
    private StagnantPositionHandler stagnantPositionHandler;
    private ProfitTargetHandler profitTargetHandler;
    private MarginProtector marginProtector;
    
    // Lista degli eventi ricevuti
    private final List<TradingEvent> events = new CopyOnWriteArrayList<>();
    
    /**
     * Implementazione mock di MT5Commands per i test.
     */
    static class MockMT5Commands extends MT5Commands {
        
        private final Map<Long, Position> positions = new HashMap<>();
        private long nextTicket = 1;
        private double balance = 1000.0;
        private double equity = 1000.0;
        private double marginFree = 900.0;
        private double marginLevel = 200.0;
        
        public MockMT5Commands() {
            super(null);
        }
        
        @Override
        public Map<String, Object> getAccountInfo() {
            Map<String, Object> result = new HashMap<>();
            Map<String, Object> accountInfo = new HashMap<>();
            
            accountInfo.put("balance", balance);
            accountInfo.put("equity", equity);
            accountInfo.put("margin_free", marginFree);
            accountInfo.put("margin_level", marginLevel);
            
            result.put("account_info", accountInfo);
            result.put("success", true);
            
            return result;
        }
        
        @Override
        public Map<String, Object> getPositions(String symbol) {
            Map<String, Object> result = new HashMap<>();
            List<Map<String, Object>> positionsList = new ArrayList<>();
            
            for (Position position : positions.values()) {
                if (symbol == null || symbol.equals(position.getSymbol())) {
                    Map<String, Object> positionData = new HashMap<>();
                    positionData.put("ticket", position.getTicket());
                    positionData.put("symbol", position.getSymbol());
                    positionData.put("type", position.getType() == PositionType.BUY ? "buy" : "sell");
                    positionData.put("volume", position.getVolume());
                    positionData.put("open_price", position.getOpenPrice());
                    positionData.put("sl", position.getStopLoss());
                    positionData.put("tp", position.getTakeProfit());
                    positionData.put("comment", position.getComment());
                    positionData.put("magic", position.getMagicNumber());
                    positionData.put("current_price", position.getCurrentPrice());
                    positionData.put("profit", position.getProfit());
                    
                    positionsList.add(positionData);
                }
            }
            
            result.put("positions", positionsList);
            result.put("success", true);
            
            return result;
        }
        
        @Override
        public Map<String, Object> marketBuy(String symbol, double volume, double stopLoss, double takeProfit, String comment, int magicNumber) {
            Map<String, Object> result = new HashMap<>();
            
            double openPrice = 1.2000;
            long ticket = nextTicket++;
            
            Position position = new Position(
                ticket, symbol, PositionType.BUY, volume, openPrice, LocalDateTime.now(),
                stopLoss, takeProfit, comment, magicNumber
            );
            position.updatePrice(openPrice);
            
            positions.put(ticket, position);
            
            result.put("ticket", ticket);
            result.put("symbol", symbol);
            result.put("volume", volume);
            result.put("type", "buy");
            result.put("price", openPrice);
            result.put("sl", stopLoss);
            result.put("tp", takeProfit);
            result.put("success", true);
            
            return result;
        }
        
        @Override
        public Map<String, Object> marketSell(String symbol, double volume, double stopLoss, double takeProfit, String comment, int magicNumber) {
            Map<String, Object> result = new HashMap<>();
            
            double openPrice = 1.2000;
            long ticket = nextTicket++;
            
            Position position = new Position(
                ticket, symbol, PositionType.SELL, volume, openPrice, LocalDateTime.now(),
                stopLoss, takeProfit, comment, magicNumber
            );
            position.updatePrice(openPrice);
            
            positions.put(ticket, position);
            
            result.put("ticket", ticket);
            result.put("symbol", symbol);
            result.put("volume", volume);
            result.put("type", "sell");
            result.put("price", openPrice);
            result.put("sl", stopLoss);
            result.put("tp", takeProfit);
            result.put("success", true);
            
            return result;
        }
        
        @Override
        public Map<String, Object> closePosition(long ticket, Double volume) {
            Map<String, Object> result = new HashMap<>();
            
            if (positions.containsKey(ticket)) {
                Position position = positions.get(ticket);
                positions.remove(ticket);
                
                result.put("ticket", ticket);
                result.put("symbol", position.getSymbol());
                result.put("volume", position.getVolume());
                result.put("profit", position.getProfit());
                result.put("success", true);
            } else {
                result.put("success", false);
                result.put("error", "Position not found");
            }
            
            return result;
        }
        
        @Override
        public Map<String, Object> checkSpread(String symbol) {
            Map<String, Object> result = new HashMap<>();
            
            // Simula uno spread
            int spread = 10;
            
            result.put("symbol", symbol);
            result.put("spread", spread);
            result.put("success", true);
            
            return result;
        }
        
        /**
         * Simula un movimento di prezzo per una posizione.
         * 
         * @param ticket Il ticket della posizione
         * @param priceDelta La variazione di prezzo
         */
        public void simulatePriceMove(long ticket, double priceDelta) {
            if (positions.containsKey(ticket)) {
                Position position = positions.get(ticket);
                double currentPrice = position.getCurrentPrice();
                position.updatePrice(currentPrice + priceDelta);
            }
        }
        
        /**
         * Simula un movimento di prezzo per tutte le posizioni.
         * 
         * @param priceDelta La variazione di prezzo
         */
        public void simulatePriceMoveAll(double priceDelta) {
            for (Position position : positions.values()) {
                double currentPrice = position.getCurrentPrice();
                position.updatePrice(currentPrice + priceDelta);
            }
        }
        
        /**
         * Simula un cambiamento del margine libero.
         * 
         * @param marginFree Il nuovo margine libero
         */
        public void simulateMarginFree(double marginFree) {
            this.marginFree = marginFree;
        }
        
        /**
         * Simula un cambiamento del livello di margine.
         * 
         * @param marginLevel Il nuovo livello di margine
         */
        public void simulateMarginLevel(double marginLevel) {
            this.marginLevel = marginLevel;
        }
        
        /**
         * Simula un cambiamento del saldo.
         * 
         * @param balance Il nuovo saldo
         */
        public void simulateBalance(double balance) {
            this.balance = balance;
        }
        
        /**
         * Simula un cambiamento dell'equity.
         * 
         * @param equity Il nuovo equity
         */
        public void simulateEquity(double equity) {
            this.equity = equity;
        }
    }
    
    /**
     * Inizializza il test.
     */
    public void setup() {
        // Configura il logger
        Logger rootLogger = Logger.getLogger("");
        rootLogger.setLevel(Level.INFO);
        ConsoleHandler handler = new ConsoleHandler();
        handler.setFormatter(new SimpleFormatter());
        handler.setLevel(Level.INFO);
        rootLogger.addHandler(handler);
        
        // Inizializza i componenti
        mt5Commands = new MockMT5Commands();
        eventManager = new TradingEventManager();
        riskManager = new DefaultRiskManager(mt5Commands, eventManager);
        stagnantPositionHandler = new StagnantPositionHandler(mt5Commands, eventManager);
        profitTargetHandler = new ProfitTargetHandler(mt5Commands, eventManager);
        marginProtector = new MarginProtector(mt5Commands, eventManager);
        
        // Registra il listener per gli eventi
        eventManager.addListener(this);
        
        // Configura i componenti
        stagnantPositionHandler.setMaxInactiveMinutes(50);
        stagnantPositionHandler.setMinProfitPips(5.0);
        stagnantPositionHandler.setCheckIntervalSeconds(60);
        
        profitTargetHandler.setProfitTargetPercent(2.0);
        profitTargetHandler.setCheckIntervalSeconds(30);
        
        marginProtector.setMinFreeMargin(50.0);
        marginProtector.setCriticalMarginLevel(150.0);
        marginProtector.setWarningMarginLevel(200.0);
        marginProtector.setCheckIntervalSeconds(10);
        
        riskManager.setMinFreeMargin(50.0);
        riskManager.setMaxSpreadPoints(20);
        riskManager.setMonitoringIntervalSeconds(30);
        
        // Aggiungi gli handler al risk manager
        riskManager.addRiskHandler(stagnantPositionHandler);
        riskManager.addRiskHandler(profitTargetHandler);
        riskManager.addRiskHandler(marginProtector);
    }
    
    /**
     * Esegue il test del sistema di risk management.
     */
    public void testRiskManagement() {
        try {
            LOGGER.info("=== Test del sistema di risk management ===");
            
            // Test 1: Verifica dello spread
            LOGGER.info("Test 1: Verifica dello spread");
            boolean spreadAcceptable = riskManager.isSpreadAcceptable("EURUSD");
            LOGGER.info("Spread accettabile: " + spreadAcceptable);
            
            // Test 2: Verifica del margine libero
            LOGGER.info("Test 2: Verifica del margine libero");
            boolean marginSufficient = riskManager.isFreeMarginSufficient();
            LOGGER.info("Margine libero sufficiente: " + marginSufficient);
            
            // Test 3: Apertura di una posizione
            LOGGER.info("Test 3: Apertura di una posizione");
            boolean canOpen = riskManager.canOpenPosition("EURUSD", 0.1, 1.1950, 1.2050);
            LOGGER.info("Può aprire posizione: " + canOpen);
            
            // Test 4: Simulazione di un margine libero insufficiente
            LOGGER.info("Test 4: Simulazione di un margine libero insufficiente");
            MockMT5Commands mockCommands = (MockMT5Commands) mt5Commands;
            mockCommands.simulateMarginFree(40.0);
            marginSufficient = riskManager.isFreeMarginSufficient();
            LOGGER.info("Margine libero sufficiente: " + marginSufficient);
            
            // Test 5: Simulazione di un livello di margine critico
            LOGGER.info("Test 5: Simulazione di un livello di margine critico");
            mockCommands.simulateMarginLevel(140.0);
            
            // Avvia il monitoraggio del risk management
            riskManager.startMonitoring();
            
            // Apri alcune posizioni
            mockCommands.marketBuy("EURUSD", 0.1, 1.1950, 1.2050, "Test", 12345);
            mockCommands.marketBuy("EURUSD", 0.1, 1.1950, 1.2050, "Test", 12345);
            mockCommands.marketBuy("EURUSD", 0.1, 1.1950, 1.2050, "Test", 12345);
            
            // Esegui il risk management
            riskManager.executeRiskManagement();
            
            // Test 6: Simulazione di un target di profitto raggiunto
            LOGGER.info("Test 6: Simulazione di un target di profitto raggiunto");
            mockCommands.simulateBalance(1000.0);
            mockCommands.simulateEquity(1020.0);
            mockCommands.simulatePriceMoveAll(0.0020); // +20 pips
            
            // Esegui il risk management
            riskManager.executeRiskManagement();
            
            // Ferma il monitoraggio del risk management
            riskManager.stopMonitoring();
            
            LOGGER.info("=== Test completati ===");
            
        } catch (CommandExecutionException e) {
            LOGGER.log(Level.SEVERE, "Errore durante il test", e);
        }
    }
    
    @Override
    public void onTradingEvent(TradingEvent event) {
        events.add(event);
        LOGGER.info("Evento ricevuto: " + event);
    }
    
    /**
     * Metodo principale.
     * 
     * @param args Gli argomenti della linea di comando
     */
    public static void main(String[] args) {
        RiskManagementTest test = new RiskManagementTest();
        test.setup();
        test.testRiskManagement();
    }
}
