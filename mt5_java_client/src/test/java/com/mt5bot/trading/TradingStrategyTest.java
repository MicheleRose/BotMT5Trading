package test.java.com.mt5bot.trading;

import com.mt5bot.client.CommandExecutionException;
import com.mt5bot.client.MT5Commands;
import com.mt5bot.trading.event.TradingEvent;
import com.mt5bot.trading.event.TradingEventListener;
import com.mt5bot.trading.event.TradingEventManager;
import com.mt5bot.trading.manager.PositionManager;
import com.mt5bot.trading.manager.TrailingManager;
import com.mt5bot.trading.manager.VolatilityManager;
import com.mt5bot.trading.manager.VolatilityManager.VolatilityCategory;
import com.mt5bot.trading.model.Position;
import com.mt5bot.trading.model.Position.PositionType;
import com.mt5bot.trading.strategy.ScalingStrategy;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.logging.ConsoleHandler;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.logging.SimpleFormatter;

/**
 * Test della strategia di trading.
 * Verifica il funzionamento dei componenti implementati.
 */
public class TradingStrategyTest implements TradingEventListener {
    
    private static final Logger LOGGER = Logger.getLogger(TradingStrategyTest.class.getName());
    
    // Componenti del sistema
    private MT5Commands mt5Commands;
    private TradingEventManager eventManager;
    private PositionManager positionManager;
    private VolatilityManager volatilityManager;
    private TrailingManager trailingManager;
    private ScalingStrategy scalingStrategy;
    
    // Lista degli eventi ricevuti
    private final List<TradingEvent> events = new CopyOnWriteArrayList<>();
    
    /**
     * Implementazione mock di MT5Commands per i test.
     */
    static class MockMT5Commands extends MT5Commands {
        
        private final Map<Long, Position> positions = new HashMap<>();
        private long nextTicket = 1;
        
        public MockMT5Commands() {
            super(null);
        }
        
        @Override
        public Map<String, Object> getPositions(String symbol) {
            Map<String, Object> result = new HashMap<>();
            List<Map<String, Object>> positionsList = new CopyOnWriteArrayList<>();
            
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
        public Map<String, Object> modifyPosition(long ticket, double stopLoss, double takeProfit) {
            Map<String, Object> result = new HashMap<>();
            
            if (positions.containsKey(ticket)) {
                Position position = positions.get(ticket);
                position.updateLevels(stopLoss, takeProfit);
                
                result.put("ticket", ticket);
                result.put("sl", stopLoss);
                result.put("tp", takeProfit);
                result.put("success", true);
            } else {
                result.put("success", false);
                result.put("error", "Position not found");
            }
            
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
        public Map<String, Object> calculateVolatility(String symbol, String timeframe, int period) {
            Map<String, Object> result = new HashMap<>();
            
            // Simula un valore ATR
            double atr = 0.0045; // 45 pips
            
            result.put("symbol", symbol);
            result.put("timeframe", timeframe);
            result.put("period", period);
            result.put("volatility", atr);
            result.put("volatility_percent", atr * 100);
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
        positionManager = new PositionManager(mt5Commands, eventManager);
        volatilityManager = new VolatilityManager(mt5Commands, eventManager);
        trailingManager = new TrailingManager(mt5Commands, positionManager, eventManager);
        scalingStrategy = new ScalingStrategy(mt5Commands, positionManager, eventManager);
        
        // Registra il listener per gli eventi
        eventManager.addListener(this);
        
        // Configura i componenti
        trailingManager.setTrailingDistance(30.0);
        trailingManager.setActivationDistance(15.0);
        trailingManager.setUpdateInterval(1);
        
        volatilityManager.setLowVolatilityThreshold(30.0);
        volatilityManager.setHighVolatilityThreshold(60.0);
        volatilityManager.setSlAtrMultiplier(1.5);
        volatilityManager.setTpAtrMultiplier(2.0);
        
        scalingStrategy.setInitialPositions(3);
        scalingStrategy.setAdditionalPositions(4);
        scalingStrategy.setTriggerPips(15.0);
        scalingStrategy.setLotIncrement(0.01);
        scalingStrategy.setLotIncrementStep(4);
        scalingStrategy.setMaxPositions(20);
    }
    
    /**
     * Esegue il test della strategia di trading.
     */
    public void testTradingStrategy() {
        try {
            LOGGER.info("=== Test della strategia di trading ===");
            
            // Test 1: Aggiornamento ATR e categorizzazione volatilità
            LOGGER.info("Test 1: Aggiornamento ATR e categorizzazione volatilità");
            double atr = volatilityManager.updateAtr("EURUSD");
            VolatilityCategory category = volatilityManager.getVolatilityCategory("EURUSD");
            LOGGER.info("ATR: " + atr + " pips, Categoria: " + category);
            
            // Test 2: Calcolo SL/TP in base alla volatilità
            LOGGER.info("Test 2: Calcolo SL/TP in base alla volatilità");
            double entryPrice = 1.2000;
            double sl = volatilityManager.calculateStopLoss("EURUSD", entryPrice, true);
            double tp = volatilityManager.calculateTakeProfit("EURUSD", entryPrice, true);
            LOGGER.info("Entry: " + entryPrice + ", SL: " + sl + ", TP: " + tp);
            
            // Test 3: Apertura posizioni iniziali con scaling strategy
            LOGGER.info("Test 3: Apertura posizioni iniziali con scaling strategy");
            String groupId = scalingStrategy.startScaling(
                "EURUSD", PositionType.BUY, 0.1, sl, tp, "Test", 12345
            );
            positionManager.updatePositions();
            List<Position> positions = positionManager.getPositionsByGroup(groupId);
            LOGGER.info("Posizioni aperte: " + positions.size());
            
            // Test 4: Simulazione movimento prezzo e trailing stop
            LOGGER.info("Test 4: Simulazione movimento prezzo e trailing stop");
            trailingManager.start();
            
            // Simula un movimento di prezzo positivo
            MockMT5Commands mockCommands = (MockMT5Commands) mt5Commands;
            mockCommands.simulatePriceMoveAll(0.0020); // +20 pips
            
            // Aggiorna le posizioni e verifica il trailing stop
            positionManager.updatePositions();
            trailingManager.stop();
            
            // Test 5: Verifica scaling
            LOGGER.info("Test 5: Verifica scaling");
            scalingStrategy.checkScaling(groupId);
            positionManager.updatePositions();
            positions = positionManager.getPositionsByGroup(groupId);
            LOGGER.info("Posizioni dopo scaling: " + positions.size());
            
            // Test 6: Calcolo profitto aggregato
            LOGGER.info("Test 6: Calcolo profitto aggregato");
            double totalProfit = positionManager.getTotalProfitByGroup(groupId);
            LOGGER.info("Profitto totale: " + totalProfit);
            
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
        TradingStrategyTest test = new TradingStrategyTest();
        test.setup();
        test.testTradingStrategy();
    }
}
