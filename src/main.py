import time
import threading
import traceback
from mt5_connector import MT5Connector
from trading_logic import TradingLogic
from display_manager import DisplayManager
from gui_manager import GUIManager
from datetime import datetime

# Istanza globale della GUI
gui_instance = None

def main():
    global gui_instance
    
    # Inizializza interfacce
    display = DisplayManager()
    
    # Crea la GUI
    gui_instance = GUIManager()
    
    # Attendi che la GUI sia pronta
    if not gui_instance.ready.wait(timeout=10):
        print("Timeout nell'inizializzazione della GUI")
        return
    
    # Verifica configurazione
    status_data = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": "Verifica file di configurazione..."
    }
    display.update("STATUS", status_data)
    if gui_instance:
        gui_instance.update("STATUS", status_data)
    
    # Valida config.json
    import sys
    sys.path.append('src')
    from config_validator import ConfigValidator
    valid, message = ConfigValidator.validate_config()
    if not valid:
        error_data = {
            "message": f"Errore configurazione: {message}\nTraceback:\n{traceback.format_exc()}"
        }
        display.update("ERROR", error_data)
        if gui_instance:
            gui_instance.update("ERROR", error_data)
        return
        
    # Valida access.json
    valid, message = ConfigValidator.validate_access()
    if not valid:
        error_data = {
            "message": f"Errore credenziali: {message}\nTraceback:\n{traceback.format_exc()}"
        }
        display.update("ERROR", error_data)
        if gui_instance:
            gui_instance.update("ERROR", error_data)
        return
    
    # Inizializza componenti
    mt5 = MT5Connector(error_logger=display.error_logger)
    logic = TradingLogic()
    
    # Verifica configurazione MT5
    status_data = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": "Verifica configurazione MT5..."
    }
    display.update("STATUS", status_data)
    if gui_instance:
        gui_instance.update("STATUS", status_data)
    
    # Inizializza MT5
    if not mt5.initialize():
        error_data = {
            "message": f"Errore nell'inizializzazione di MT5\nTraceback:\n{traceback.format_exc()}"
        }
        display.update("ERROR", error_data)
        if gui_instance:
            gui_instance.update("ERROR", error_data)
        return
        
    # Login
    if not mt5.login():
        error_data = {
            "message": f"Errore nel login a MT5\nTraceback:\n{traceback.format_exc()}"
        }
        display.update("ERROR", error_data)
        if gui_instance:
            gui_instance.update("ERROR", error_data)
        mt5.shutdown()
        return
        
    # Verifica terminale
    terminal_info = mt5.get_terminal_info()
    if terminal_info is None:
        error_data = {
            "message": f"Impossibile ottenere informazioni dal terminale\nTraceback:\n{traceback.format_exc()}"
        }
        display.update("ERROR", error_data)
        if gui_instance:
            gui_instance.update("ERROR", error_data)
        mt5.shutdown()
        return
        
    # Mostra stato sistema
    system_data = {
        "version": mt5.get_version(),
        "checks": {
            "AutoTrading": not terminal_info.tradeapi_disabled,
            "Trading": terminal_info.trade_allowed,
            "Connected": terminal_info.connected
        }
    }
    display.update("SYSTEM", system_data)
    if gui_instance:
        gui_instance.update("SYSTEM", system_data)
    
    # Verifica simbolo
    symbol = logic.trading_config["symbol"]
    symbol_info = mt5.get_symbol_info(symbol)
    
    if symbol_info is None:
        error_data = {
            "message": f"Simbolo {symbol} non trovato\nTraceback:\n{traceback.format_exc()}"
        }
        display.update("ERROR", error_data)
        if gui_instance:
            gui_instance.update("ERROR", error_data)
        mt5.shutdown()
        return
        
    if not mt5.select_symbol(symbol):
        error_data = {
            "message": f"Impossibile selezionare il simbolo {symbol}\nTraceback:\n{traceback.format_exc()}"
        }
        display.update("ERROR", error_data)
        if gui_instance:
            gui_instance.update("ERROR", error_data)
        mt5.shutdown()
        return
        
    # Mostra info simbolo
    symbol_data = {
        "name": symbol,
        "bid": symbol_info.bid,
        "ask": symbol_info.ask,
        "spread": symbol_info.spread,
        "digits": symbol_info.digits,
        "point": symbol_info.point,
        "vol_min": symbol_info.volume_min,
        "vol_max": symbol_info.volume_max,
        "vol_step": symbol_info.volume_step
    }
    display.update("SYMBOL", symbol_data)
    if gui_instance:
        gui_instance.update("SYMBOL", symbol_data)
    
    # Loop principale
    try:
        while True:
            try:
                # Aggiorna stato
                status_data = {
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "message": "Analisi mercato in corso..."
                }
                display.update("STATUS", status_data)
                if gui_instance:
                    gui_instance.update("STATUS", status_data)
                
                # Scarica dati storici
                df = mt5.get_historical_data(symbol, logic.trading_config["timeframe"])
                
                # Applica indicatori
                df = logic.apply_indicators(df)
                latest = df.iloc[-1]
                
                # Ottieni tick corrente
                symbol_info = mt5.get_symbol_info(symbol)
                
                # Aggiorna display mercato
                market_data = {
                    "symbol": symbol,
                    "spread": symbol_info.ask - symbol_info.bid,
                    "bid": symbol_info.bid,
                    "ask": symbol_info.ask,
                    "rsi": latest['rsi'],
                    "macd": latest['macd'],
                    "signal": latest['macd_signal'],
                    "bb_up": latest['upper_band'],
                    "bb_down": latest['lower_band']
                }
                display.update("MARKET", market_data)
                if gui_instance:
                    gui_instance.update("MARKET", market_data)
                
                # Analizza mercato
                analysis = logic.analyze_market(df)
                
                # Aggiorna display analisi
                display.update("ANALYSIS", analysis["analysis"])
                if gui_instance:
                    gui_instance.update("ANALYSIS", analysis["analysis"])
                
                # Aggiorna display segnali
                display.update("SIGNALS", analysis["conditions"])
                if gui_instance:
                    gui_instance.update("SIGNALS", analysis["conditions"])
                
                # Verifica profitto/perdita flottante
                current_price = symbol_info.ask
                total_profit = 0
                positions = mt5.positions_get()
                account_info = mt5.get_account_info()
                
                if positions is None:
                    # Verifica se ci sono errori
                    last_error = mt5.last_error()
                    if last_error[0] != 0:  # 0 significa nessun errore
                        error_data = {
                            "message": f"Errore nel recupero posizioni: ({last_error[0]}) {last_error[1]}"
                        }
                        display.update("ERROR", error_data)
                        continue
                else:
                    for pos in positions:
                        total_profit += pos.profit
                
                # Chiudi se profitto target o perdita massima
                if (account_info is not None and logic.check_floating_profit(current_price, account_info)) or total_profit <= -logic.trading_config["max_loss"]:
                    reason = "Profitto target raggiunto" if total_profit > 0 else "Stop loss raggiunto"
                    status_data = {
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "message": f"Chiusura posizioni: {reason}..."
                    }
                    display.update("STATUS", status_data)
                    if gui_instance:
                        gui_instance.update("STATUS", status_data)
                    
                    if mt5.close_all_positions():
                        # Log chiusura con dettagli
                        close_data = {
                            "reason": reason,
                            "profit": total_profit,
                            "indicators": {
                                "rsi": latest['rsi'],
                                "macd": latest['macd'],
                                "macd_signal": latest['macd_signal'],
                                "bb_up": latest['upper_band'],
                                "bb_down": latest['lower_band']
                            }
                        }
                        display.update("CLOSE", close_data)
                        if gui_instance:
                            gui_instance.update("CLOSE", close_data)
                            
                        # Reset delle posizioni nel trading logic
                        logic.open_positions = {"buy": [], "sell": []}
                    else:
                        last_error = mt5.last_error()
                        error_data = {
                            "message": f"Errore nella chiusura delle posizioni: ({last_error[0]}) {last_error[1]}\nTraceback:\n{traceback.format_exc()}"
                        }
                        display.update("ERROR", error_data)
                        if gui_instance:
                            gui_instance.update("ERROR", error_data)
                    continue

                # Verifica spread e margine
                spread = mt5.get_spread(symbol)
                account_info = mt5.get_account_info()
                if account_info is None:
                    error_data = {
                        "message": "Impossibile ottenere informazioni sull'account"
                    }
                    display.update("ERROR", error_data)
                    if gui_instance:
                        gui_instance.update("ERROR", error_data)
                    continue

                # Verifica posizioni stagnanti
                stagnant_positions = logic.check_stagnant_positions(datetime.now())
                if stagnant_positions:
                    status_data = {
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "message": "Chiusura posizioni stagnanti..."
                    }
                    display.update("STATUS", status_data)
                    if gui_instance:
                        gui_instance.update("STATUS", status_data)
                    
                    mt5.close_stagnant_positions(stagnant_positions)
                    for pos in stagnant_positions:
                        logic.remove_position(pos["direction"], pos["index"])

                # Aggiorna trailing stops
                logic.update_trailing_stops(current_price)
                
                # Applica modifiche trailing stop
                for direction in ["buy", "sell"]:
                    for pos in logic.open_positions[direction]:
                        if "ticket" in pos and pos.get("sl") != pos.get("original_sl"):
                            mt5.modify_position(pos["ticket"], sl=pos["sl"])

                # Verifica segnale
                signal = analysis["signal"]
                if signal in ['buy', 'sell'] and logic.can_trade(spread, account_info["margin_free"]):
                    # Verifica AutoTrading
                    if not terminal_info.trade_allowed:
                        error_data = {
                            "message": "AutoTrading disabilitato in MT5. Abilitare l'AutoTrading per continuare."
                        }
                        display.update("ERROR", error_data)
                        time.sleep(5)  # Attendi 5 secondi prima di riprovare
                        continue
                        
                    price = symbol_info.ask if signal == 'buy' else symbol_info.bid
                    
                    # Verifica distanza minima
                    if not logic.check_position_distance(signal, price):
                        status_data = {
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "message": f"Distanza minima non rispettata per {signal.upper()}"
                        }
                        display.update("STATUS", status_data)
                        if gui_instance:
                            gui_instance.update("STATUS", status_data)
                        continue
                    
                    # Verifica se aprire nuove posizioni
                    if logic.should_open_new_positions(signal, price):
                        # Calcola ATR medio
                        avg_atr = df['atr'].mean()
                        current_atr = df['atr'].iloc[-1]
                        
                        # Prepara ordine con SL/TP adattivi
                        order = logic.prepare_order(signal, price, symbol_info.point, current_atr, avg_atr)
                        
                        # Invia ordine
                        result = mt5.place_order(order)
                        
                        if result is None:
                            error_data = {
                                "message": f"Errore nell'invio dell'ordine {signal.upper()}: Nessuna risposta da MT5\nTraceback:\n{traceback.format_exc()}"
                            }
                            display.update("ERROR", error_data)
                            if gui_instance:
                                gui_instance.update("ERROR", error_data)
                        else:
                            if result.retcode == 10009:  # MT5_TRADE_RETCODE_DONE
                                # Aggiungi ticket alla posizione per il trailing stop
                                position = logic.open_positions[signal][-1]
                                position["ticket"] = result.order
                                position["original_sl"] = order["sl"]
                                position["open_time"] = datetime.now()
                            
                                trade_data = {
                                    "type": signal.upper(),
                                    "volume": order["volume"],
                                    "price": order["price"],
                                    "sl": order["sl"],
                                    "tp": order["tp"],
                                    "spread": spread,
                                    "conditions": analysis["conditions"],
                                    "indicators": {
                                        "rsi": latest['rsi'],
                                        "macd": latest['macd'],
                                        "macd_signal": latest['macd_signal'],
                                        "bb_up": latest['upper_band'],
                                        "bb_down": latest['lower_band'],
                                        "atr": latest['atr']
                                    },
                                    "market_condition": logic.get_market_condition(latest['atr'], df['atr'].mean()),
                                    "order_params": {
                                        "type_time": order["type_time"],
                                        "type_filling": order["type_filling"],
                                        "magic": order["magic"],
                                        "deviation": order["deviation"]
                                    }
                                }
                                display.update("TRADE", trade_data)
                                if gui_instance:
                                    gui_instance.update("TRADE", trade_data)
                                logic.increment_trade_count()
                            else:
                                error_data = {
                                    "message": f"Errore ordine {signal.upper()}: {result.comment} (Codice: {result.retcode})\nTraceback:\n{traceback.format_exc()}"
                                }
                                display.update("ERROR", error_data)
                                if gui_instance:
                                    gui_instance.update("ERROR", error_data)
                
            except Exception as e:
                error_data = {
                    "message": f"Errore durante l'analisi: {str(e)}\nTraceback:\n{traceback.format_exc()}"
                }
                display.update("ERROR", error_data)
                if gui_instance:
                    gui_instance.update("ERROR", error_data)
                
                # Attendi finché l'errore non viene risolto
                while display.paused:
                    try:
                        time.sleep(1)
                    except KeyboardInterrupt:
                        status_data = {
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "message": "Chiusura in corso..."
                        }
                        display.update("STATUS", status_data)
                        if gui_instance:
                            gui_instance.update("STATUS", status_data)
                        mt5.shutdown()
                        return
                continue
                
            # Attendi prima del prossimo ciclo
            time.sleep(1)
            
    except KeyboardInterrupt:
        status_data = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "message": "Chiusura in corso..."
        }
        display.update("STATUS", status_data)
        if gui_instance:
            gui_instance.update("STATUS", status_data)
        mt5.shutdown()
    except Exception as e:
        error_data = {
            "message": f"Errore critico: {str(e)}\nTraceback:\n{traceback.format_exc()}"
        }
        display.update("ERROR", error_data)
        if gui_instance:
            gui_instance.update("ERROR", error_data)
        time.sleep(5)  # Pausa per mostrare l'errore
        mt5.shutdown()

if __name__ == "__main__":
    main()
