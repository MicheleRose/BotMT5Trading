import json
import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
from datetime import datetime

class TradingLogic:
    def __init__(self):
        # Carica configurazione
        with open('config/config.json', 'r') as f:
            self.config = json.load(f)
            
        # Configurazione Trading
        self.trading_config = self.config['trading']
        
        # Configurazione indicatori
        self.rsi_config = self.config["indicators"]["rsi"]
        self.macd_config = self.config["indicators"]["macd"]
        self.bollinger_config = self.config["indicators"]["bollinger"]
        self.atr_config = self.config["indicators"]["atr"]
        
        # Configurazione SL/TP adattivi
        self.adaptive_sl_tp = self.config["adaptive_sl_tp"]
        
        # Configurazione gestione rischio
        self.risk_config = self.config["risk_management"]
        
        # Configurazione execution
        self.execution_config = self.config["execution"]
        
        # Contatori e stato
        self.trade_count = 0
        self.start_time = datetime.now()
        self.last_trade_time = datetime.now()
        self.open_positions: Dict[str, List[Dict]] = {
            "buy": [],
            "sell": []
        }
        
        # Stato trailing stop
        self.trailing_stops: Dict[str, float] = {}

    def check_trade_frequency(self) -> bool:
        """Verifica se è passato abbastanza tempo dall'ultimo trade"""
        if not hasattr(self, 'last_trade_time'):
            return True
            
        elapsed = (datetime.now() - self.last_trade_time).total_seconds()
        return elapsed >= self.trading_config["trade_frequency_seconds"]

    def check_capital_protection(self, account_info: dict) -> bool:
        """Verifica le soglie di protezione del capitale"""
        balance = account_info["balance"]
        thresholds = self.risk_config["capital_protection_thresholds"]
        
        # Trova la soglia appropriata
        current_threshold = None
        for threshold, risk in sorted(thresholds.items(), key=lambda x: int(x[0])):
            if balance <= int(threshold):
                current_threshold = risk
                break
                
        if current_threshold is None:
            return True
            
        # Calcola il rischio corrente
        total_risk = 0
        for direction in ["buy", "sell"]:
            for pos in self.open_positions[direction]:
                total_risk += pos["volume"]
                
        return (total_risk / balance) <= current_threshold

    def can_trade(self, spread: float, free_margin: float) -> bool:
        """Verifica se è possibile effettuare trading."""
        # Verifica spread
        if not self.check_spread(spread):
            return False
            
        # Verifica margine
        if not self.check_margin(free_margin):
            return False
        
        # Verifica numero massimo posizioni aperte
        total_positions = len(self.open_positions["buy"]) + len(self.open_positions["sell"])
        if total_positions >= self.trading_config["max_concurrent_trades"]:
            return False
            
        # Verifica frequenza trading
        if not self.check_trade_frequency():
            return False
            
        # In modalità strict, applica controlli aggiuntivi
        if self.trading_config["strict_mode"]:
            if not self.check_capital_protection({"balance": free_margin}):
                return False
                
        return True

    def prepare_order(self, signal: str, price: float, point: float, atr: float, avg_atr: float) -> Dict:
        """Prepara i parametri dell'ordine."""
        # Calcola volume
        volume = self.calculate_lot_size(signal)
        
        # Determina condizione del mercato e SL/TP
        market_condition = self.get_market_condition(atr, avg_atr)
        sl_tp_config = self.adaptive_sl_tp["market_conditions"][market_condition]
        
        # Usa ATR per SL/TP se disponibile e abilitato
        if self.adaptive_sl_tp["use_atr"] and atr > 0:
            sl_pips = atr * self.adaptive_sl_tp["sl_multiplier"]
            tp_pips = atr * self.adaptive_sl_tp["tp_multiplier"]
        else:
            sl_pips = self.adaptive_sl_tp["default_sl_pips"] * point
            tp_pips = self.adaptive_sl_tp["default_tp_pips"] * point
        
        # Calcola SL e TP
        stop_loss = price - sl_pips if signal == "buy" else price + sl_pips
        take_profit = price + tp_pips if signal == "buy" else price - tp_pips
        
        # Prepara l'ordine con i parametri corretti per MT5
        order = {
            "action": "TRADE_ACTION_DEAL",
            "symbol": self.trading_config["symbol"],
            "volume": volume,
            "type": "ORDER_TYPE_BUY" if signal == "buy" else "ORDER_TYPE_SELL",
            "price": price,
            "sl": stop_loss,
            "tp": take_profit,
            "deviation": self.execution_config["deviation"],
            "magic": self.execution_config["magic_number"],
            "comment": self.execution_config["order_comment"],
            "type_time": self.execution_config["type_time"],
            "type_filling": self.execution_config["type_filling"]
        }
        
        # Aggiungi alla lista delle posizioni aperte con tutti i parametri
        position = {
            "price": price,
            "volume": volume,
            "sl": stop_loss,
            "tp": take_profit,
            "open_time": datetime.now(),
            "order_params": {
                "type_time": self.execution_config["type_time"],
                "type_filling": self.execution_config["type_filling"],
                "magic": self.execution_config["magic_number"],
                "deviation": self.execution_config["deviation"]
            }
        }
        self.open_positions[signal].append(position)
        
        return order

    # [Resto del codice rimane invariato...]
    def calculate_rsi(self, close_prices: np.ndarray, period: int = None) -> np.ndarray:
        """Calcola il RSI (Relative Strength Index)"""
        if period is None:
            period = self.rsi_config["period"]
            
        delta = np.zeros_like(close_prices)
        delta[1:] = np.diff(close_prices)
        
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        avg_gain = np.zeros_like(close_prices)
        avg_loss = np.zeros_like(close_prices)
        
        avg_gain[:period] = np.nan
        avg_loss[:period] = np.nan
        
        for i in range(period, len(close_prices)):
            avg_gain[i] = np.mean(gain[i-period+1:i+1])
            avg_loss[i] = np.mean(loss[i-period+1:i+1])
        
        rs = avg_gain / np.where(avg_loss == 0, 1, avg_loss)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

    def calculate_macd(self, close_prices: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Calcola MACD (Moving Average Convergence Divergence)"""
        exp1 = pd.Series(close_prices).ewm(span=self.macd_config["fast_period"], adjust=False).mean()
        exp2 = pd.Series(close_prices).ewm(span=self.macd_config["slow_period"], adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=self.macd_config["signal_period"], adjust=False).mean()
        return macd.values, signal.values

    def calculate_bollinger_bands(self, close_prices: np.ndarray, period: int = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calcola le Bande di Bollinger"""
        if period is None:
            period = self.bollinger_config["period"]
            
        middle_band = pd.Series(close_prices).rolling(window=period).mean()
        std = pd.Series(close_prices).rolling(window=period).std()
        upper_band = middle_band + (std * self.bollinger_config["std_dev"])
        lower_band = middle_band - (std * self.bollinger_config["std_dev"])
        return upper_band.values, middle_band.values, lower_band.values

    def calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """Calcola l'Average True Range (ATR)"""
        period = self.atr_config["period"]
        
        tr = np.zeros_like(close)
        tr[0] = high[0] - low[0]
        
        for i in range(1, len(close)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i-1])
            lc = abs(low[i] - close[i-1])
            tr[i] = max(hl, hc, lc)
            
        atr = pd.Series(tr).rolling(window=period).mean().values
        return atr

    def get_market_condition(self, atr: float, avg_atr: float) -> str:
        """Determina la condizione del mercato basata sull'ATR"""
        if atr < 0.8 * avg_atr:
            return "calm"
        elif atr > 1.2 * avg_atr:
            return "volatile"
        return "normal"

    def apply_indicators(self, df):
        """Calcola indicatori base per l'analisi tecnica."""
        close_prices = df['close'].values
        
        df['rsi'] = self.calculate_rsi(close_prices)
        df['macd'], df['macd_signal'] = self.calculate_macd(close_prices)
        df['upper_band'], df['middle_band'], df['lower_band'] = self.calculate_bollinger_bands(close_prices)
        df['atr'] = self.calculate_atr(df['high'].values, df['low'].values, close_prices)
        df['volatility'] = df['close'].rolling(window=4).std()
        
        return df

    def analyze_market(self, df):
        """Analizza il mercato e genera segnali."""
        latest = df.iloc[-1]
        
        # Analisi parametri correnti
        rsi_status = "SOVRAVENDUTO" if latest['rsi'] < 30 else "SOVRCOMPRATO" if latest['rsi'] > 70 else "NEUTRALE"
        macd_trend = "RIALZISTA" if latest['macd'] > latest['macd_signal'] else "RIBASSISTA"
        price_position = "SOPRA BB" if latest['close'] > latest['upper_band'] else "SOTTO BB" if latest['close'] < latest['lower_band'] else "DENTRO BB"
        
        # Condizioni di trading
        buy_conditions = 0
        buy_rsi = latest['rsi'] < self.rsi_config["oversold"]
        buy_macd = latest['macd'] > latest['macd_signal']
        buy_bb = latest['close'] < latest['lower_band']
        if buy_rsi: buy_conditions += 1
        if buy_macd: buy_conditions += 1
        if buy_bb: buy_conditions += 1
        
        sell_conditions = 0
        sell_rsi = latest['rsi'] > self.rsi_config["overbought"]
        sell_macd = latest['macd'] < latest['macd_signal']
        sell_bb = latest['close'] > latest['upper_band']
        if sell_rsi: sell_conditions += 1
        if sell_macd: sell_conditions += 1
        if sell_bb: sell_conditions += 1
        
        # Generazione segnale
        signal = 'hold'
        
        # Verifica condizioni di mercato
        market_condition = self.get_market_condition(latest['atr'], df['atr'].mean())
        
        # In mercato calmo o normale, richiedi solo 1 condizione
        if market_condition in ["calm", "normal"]:
            if buy_conditions >= 1: signal = 'buy'
            elif sell_conditions >= 1: signal = 'sell'
        # In mercato volatile, richiedi 2 condizioni
        else:
            if buy_conditions >= 2: signal = 'buy'
            elif sell_conditions >= 2: signal = 'sell'
            
        return {
            'signal': signal,
            'analysis': {
                'rsi': latest['rsi'],
                'rsi_status': rsi_status,
                'macd': latest['macd'],
                'macd_trend': macd_trend,
                'price': latest['close'],
                'position': price_position,
                'atr': latest['atr'],
                'market_condition': self.get_market_condition(latest['atr'], df['atr'].mean())
            },
            'conditions': {
                'buy_conditions': buy_conditions,
                'sell_conditions': sell_conditions,
                'buy_rsi': buy_rsi,
                'buy_macd': buy_macd,
                'buy_bb': buy_bb,
                'sell_rsi': sell_rsi,
                'sell_macd': sell_macd,
                'sell_bb': sell_bb
            }
        }

    def calculate_lot_size(self, signal: str) -> float:
        """Calcola la dimensione del lotto in base al numero di operazioni."""
        lot_config = self.trading_config["lot_size"]
        base_lot = lot_config["initial"]
        increment = lot_config["increment"]
        every_n_trades = lot_config["increment_every"]
        
        # Calcola il numero di incrementi basato sulle operazioni aperte
        n_positions = len(self.open_positions[signal])
        n_increments = n_positions // every_n_trades
        
        # Applica il limite di rischio per trade
        max_lot = base_lot + (increment * ((self.trading_config["max_concurrent_trades"] // every_n_trades) - 1))
        calculated_lot = base_lot + (increment * n_increments)
        
        return min(calculated_lot, max_lot)

    def check_spread(self, spread: float) -> bool:
        """Verifica se lo spread è accettabile"""
        if not self.trading_config["spread_check"]["enabled"]:
            return True
            
        return spread <= self.trading_config["spread_check"]["max_spread_points"]

    def check_margin(self, free_margin: float) -> bool:
        """Verifica se il margine libero è sufficiente"""
        if not self.risk_config["margin_protection"]["enabled"]:
            return True
            
        return free_margin >= self.risk_config["margin_protection"]["min_free_margin"]

    def check_stagnant_positions(self, current_time: datetime) -> List[Dict]:
        """Verifica e restituisce le posizioni stagnanti"""
        if not self.trading_config["stagnant_trade"]["enabled"]:
            return []
            
        max_minutes = self.trading_config["stagnant_trade"]["max_minutes"]
        stagnant_positions = []
        
        for direction in ["buy", "sell"]:
            for i, pos in enumerate(self.open_positions[direction]):
                if "open_time" in pos:
                    elapsed = (current_time - pos["open_time"]).total_seconds() / 60
                    if elapsed >= max_minutes:
                        stagnant_positions.append({
                            "direction": direction,
                            "index": i,
                            "position": pos
                        })
                        
        return stagnant_positions

    def update_trailing_stops(self, current_price: float):
        """Aggiorna i trailing stop per le posizioni in profitto"""
        if not self.trading_config["trailing_stop"]["enabled"] or not self.trading_config["profit_trailing"]:
            return
            
        trailing_pips = self.trading_config["trailing_stop"]["pips"]
        symbol = self.trading_config["symbol"]
        settings = self.config["instrument_settings"].get(symbol, self.config["instrument_settings"]["default"])
        pip_value = settings["pip_value"]
        
        # Aggiorna trailing stop per posizioni long
        for pos in self.open_positions["buy"]:
            ticket = pos.get("ticket")
            if ticket and current_price > pos["price"]:
                profit_pips = (current_price - pos["price"]) / pip_value
                if profit_pips > trailing_pips:
                    new_sl = current_price - (trailing_pips * pip_value)
                    if ticket not in self.trailing_stops or new_sl > self.trailing_stops[ticket]:
                        pos["sl"] = new_sl
                        self.trailing_stops[ticket] = new_sl
                        
        # Aggiorna trailing stop per posizioni short
        for pos in self.open_positions["sell"]:
            ticket = pos.get("ticket")
            if ticket and current_price < pos["price"]:
                profit_pips = (pos["price"] - current_price) / pip_value
                if profit_pips > trailing_pips:
                    new_sl = current_price + (trailing_pips * pip_value)
                    if ticket not in self.trailing_stops or new_sl < self.trailing_stops[ticket]:
                        pos["sl"] = new_sl
                        self.trailing_stops[ticket] = new_sl

    def check_position_distance(self, signal: str, price: float) -> bool:
        """Verifica la distanza minima tra ordini."""
        if not self.open_positions[signal]:
            return True
            
        min_pips = self.trading_config["position_management"]["min_pips_between_orders"]
        last_position = self.open_positions[signal][-1]
        last_price = last_position["price"]
        
        # Ottieni le impostazioni dello strumento
        symbol = self.trading_config["symbol"]
        settings = self.config["instrument_settings"].get(
            symbol, 
            self.config["instrument_settings"]["default"]
        )
        
        # Converti la differenza in pips usando il moltiplicatore specifico
        price_diff = abs(price - last_price) * settings["pip_multiplier"]
            
        return price_diff >= min_pips

    def check_floating_profit(self, current_price: float, account_info: dict) -> bool:
        """Verifica se il profitto flottante ha raggiunto la soglia."""
        if not self.open_positions["buy"] and not self.open_positions["sell"]:
            return False
            
        target_percentage = self.trading_config["position_management"]["floating_profit_close"]
        total_profit = 0
        
        # Ottieni le impostazioni dello strumento
        symbol = self.trading_config["symbol"]
        settings = self.config["instrument_settings"].get(
            symbol, 
            self.config["instrument_settings"]["default"]
        )
        
        # Calcola profitto per posizioni long
        for pos in self.open_positions["buy"]:
            profit = (current_price - pos["price"]) * pos["volume"] * settings["profit_multiplier"]
            total_profit += profit
            
        # Calcola profitto per posizioni short
        for pos in self.open_positions["sell"]:
            profit = (pos["price"] - current_price) * pos["volume"] * settings["profit_multiplier"]
            total_profit += profit
            
        # Usa il capitale effettivo dell'account
        profit_percentage = (total_profit / account_info["balance"]) * 100
        
        return profit_percentage >= target_percentage

    def should_open_new_positions(self, signal: str, current_price: float) -> bool:
        """Verifica se aprire nuove posizioni basate sul movimento del prezzo"""
        if not self.open_positions[signal]:
            return len(self.open_positions[signal]) < self.trading_config["initial_trades"]
            
        last_position = self.open_positions[signal][-1]
        pip_step = self.trading_config["pip_step_for_new_trades"]
        
        # Ottieni le impostazioni dello strumento
        symbol = self.trading_config["symbol"]
        settings = self.config["instrument_settings"].get(symbol, self.config["instrument_settings"]["default"])
        
        # Calcola la differenza in pips
        price_diff = abs(current_price - last_position["price"]) * settings["pip_multiplier"]
        
        # Verifica se abbiamo raggiunto il pip step e non superato il massimo di trade
        return (price_diff >= pip_step and 
                len(self.open_positions[signal]) < self.trading_config["max_concurrent_trades"] and
                len(self.open_positions[signal]) % self.trading_config["trades_per_step"] == 0)

    def increment_trade_count(self):
        """Incrementa il contatore delle operazioni e aggiorna il timestamp."""
        self.trade_count += 1
        self.last_trade_time = datetime.now()

    def remove_position(self, signal: str, index: int):
        """Rimuove una posizione dalla lista delle posizioni aperte."""
        if 0 <= index < len(self.open_positions[signal]):
            ticket = self.open_positions[signal][index].get("ticket")
            if ticket and ticket in self.trailing_stops:
                del self.trailing_stops[ticket]
            self.open_positions[signal].pop(index)
