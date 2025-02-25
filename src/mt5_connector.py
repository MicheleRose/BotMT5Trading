import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
import json

class MT5Connector:
    def __init__(self, error_logger=None):
        # Carica credenziali da access.json
        with open('config/access.json', 'r') as f:
            credentials = json.load(f)
            self.account = credentials['mt5_account']
        self.error_logger = error_logger
        
    def initialize(self):
        """Inizializza la connessione con MT5."""
        return mt5.initialize()
        
    def get_version(self):
        """Ottiene la versione di MT5."""
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            return "N/A"
        return str(terminal_info.build)
        
    def login(self):
        """Effettua il login a MT5."""
        return mt5.login(
            login=self.account["login"],
            password=self.account["password"],
            server=self.account["server"]
        )
        
    def get_terminal_info(self):
        """Ottiene informazioni sul terminale."""
        return mt5.terminal_info()
        
    def get_symbol_info(self, symbol):
        """Ottiene informazioni su un simbolo."""
        return mt5.symbol_info(symbol)
        
    def select_symbol(self, symbol):
        """Seleziona un simbolo per il trading."""
        return mt5.symbol_select(symbol, True)
        
    def get_historical_data(self, symbol, timeframe, bars=200):
        """Scarica i dati storici."""
        try:
            # Mappa timeframe
            tf_map = {
                'M1': mt5.TIMEFRAME_M1,
                'M5': mt5.TIMEFRAME_M5,
                'M15': mt5.TIMEFRAME_M15,
                'M30': mt5.TIMEFRAME_M30,
                'H1': mt5.TIMEFRAME_H1,
                'H4': mt5.TIMEFRAME_H4,
                'D1': mt5.TIMEFRAME_D1
            }
            
            # Se il timeframe è una stringa, convertilo
            if isinstance(timeframe, str):
                if timeframe.upper() not in tf_map:
                    raise ValueError(f"Timeframe non valido: {timeframe}. Valori consentiti: {', '.join(tf_map.keys())}")
                timeframe = tf_map[timeframe.upper()]
            
            # Verifica che il simbolo sia selezionato
            if not mt5.symbol_select(symbol, True):
                raise ValueError(f"Impossibile selezionare il simbolo {symbol}")
            
            # Ottieni i dati
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
            if rates is None:
                raise ValueError(f"Nessun dato disponibile per {symbol} su timeframe {timeframe}")
                
            # Converti in DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
            
        except Exception as e:
            raise Exception(f"Errore nel download dei dati per {symbol}: {str(e)}")
        
    def place_order(self, request):
        """Invia un ordine di trading."""
        try:
            # Verifica che il simbolo sia selezionato
            if not mt5.symbol_select(request["symbol"], True):
                raise ValueError(f"Impossibile selezionare il simbolo {request['symbol']}")
            
            # Converti le stringhe delle costanti MT5 nei valori corretti
            if isinstance(request["action"], str):
                request["action"] = getattr(mt5, request["action"])
            if isinstance(request["type"], str):
                request["type"] = getattr(mt5, request["type"])
            if isinstance(request["type_time"], str):
                request["type_time"] = getattr(mt5, request["type_time"])
            if isinstance(request["type_filling"], str):
                request["type_filling"] = getattr(mt5, request["type_filling"])
            
            # Invia l'ordine
            result = mt5.order_send(request)
            if result is None:
                raise ValueError("MT5 non ha restituito alcun risultato per l'ordine")
            return result
            
        except Exception as e:
            if self.error_logger:
                import traceback
                self.error_logger.error(f"Errore nell'invio dell'ordine: {str(e)}\nTraceback:\n{traceback.format_exc()}")
            return None
        
    def close_position(self, position):
        """Chiude una posizione specifica."""
        try:
            # Verifica che il simbolo sia selezionato
            if not mt5.symbol_select(position["symbol"], True):
                raise ValueError(f"Impossibile selezionare il simbolo {position['symbol']}")
            
            # Ottieni il prezzo corrente
            symbol_info = mt5.symbol_info_tick(position["symbol"])
            if symbol_info is None:
                raise ValueError(f"Impossibile ottenere il prezzo per {position['symbol']}")
            
            # Usa il prezzo appropriato per la chiusura
            # MT5 usa ORDER_TYPE_BUY = 0 e ORDER_TYPE_SELL = 1
            close_price = symbol_info.ask if position["type"] == 1 else symbol_info.bid
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position["symbol"],
                "volume": position["volume"],
                "type": mt5.ORDER_TYPE_SELL if position["type"] == 0 else mt5.ORDER_TYPE_BUY,
                "position": position["ticket"],
                "price": close_price,
                "deviation": 1,
                "magic": 123456,
                "comment": "Close by AI Scalping Ultra",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result is None:
                last_error = mt5.last_error()
                raise ValueError(f"MT5 non ha restituito risultati. Errore: ({last_error[0]}) {last_error[1]}")
                
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                raise ValueError(f"Chiusura fallita con codice {result.retcode}: {result.comment}")
                
            return True
            
        except Exception as e:
            if self.error_logger:
                import traceback
                self.error_logger.error(
                    f"Errore nella chiusura della posizione {position['ticket']}: {str(e)}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )
            return False
            
    def close_all_positions(self):
        """Chiude tutte le posizioni aperte."""
        try:
            positions = mt5.positions_get()
            if positions is None:
                # Verifica se ci sono errori
                last_error = mt5.last_error()
                if last_error[0] != 0:  # 0 significa nessun errore
                    raise Exception(f"Errore MT5 ({last_error[0]}): {last_error[1]}")
                return True  # Nessuna posizione da chiudere
                
            success = True
            failed_positions = []
            
            for position in positions:
                pos_dict = position._asdict()
                if not self.close_position(pos_dict):
                    success = False
                    last_error = mt5.last_error()
                    failed_positions.append({
                        'ticket': pos_dict['ticket'],
                        'symbol': pos_dict['symbol'],
                        'type': pos_dict['type'],
                        'volume': pos_dict['volume'],
                        'error_code': last_error[0],
                        'error_msg': last_error[1]
                    })
            
            if not success:
                error_details = "\n".join([
                    f"Ticket: {p['ticket']}, Symbol: {p['symbol']}, "
                    f"Type: {p['type']}, Volume: {p['volume']}, "
                    f"Error: ({p['error_code']}) {p['error_msg']}"
                    for p in failed_positions
                ])
                raise Exception(f"Errore nella chiusura delle seguenti posizioni:\n{error_details}")
                    
            return success
            
        except Exception as e:
            error_msg = str(e)
            if "Errore nella chiusura delle seguenti posizioni" not in error_msg:
                last_error = mt5.last_error()
                if last_error[0] != 0:
                    error_msg = f"Errore MT5 ({last_error[0]}): {last_error[1]}"
            if self.error_logger:
                import traceback
                self.error_logger.error(
                    f"{error_msg}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )
            return False
            
    def last_error(self):
        """Ottiene l'ultimo errore da MT5."""
        error = mt5.last_error()
        if error is None:
            return (0, "Nessun errore")
        return error
        
    def get_spread(self, symbol):
        """Ottiene lo spread corrente in punti."""
        symbol_info = mt5.symbol_info_tick(symbol)
        if symbol_info is None:
            return None
        return int((symbol_info.ask - symbol_info.bid) * pow(10, mt5.symbol_info(symbol).digits))
        
    def get_account_info(self):
        """Ottiene le informazioni sull'account, incluso il margine libero."""
        account_info = mt5.account_info()
        if account_info is None:
            return None
        return account_info._asdict()
        
    def modify_position(self, ticket, sl=None, tp=None):
        """Modifica gli stop loss e take profit di una posizione."""
        try:
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                raise ValueError(f"Posizione {ticket} non trovata")
                
            position = position[0]._asdict()
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position["symbol"],
                "position": ticket,
                "sl": sl if sl is not None else position["sl"],
                "tp": tp if tp is not None else position["tp"]
            }
            
            result = mt5.order_send(request)
            if result is None:
                raise ValueError("MT5 non ha restituito alcun risultato per la modifica")
                
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                raise ValueError(f"Modifica fallita con codice {result.retcode}: {result.comment}")
                
            return True
            
        except Exception as e:
            if self.error_logger:
                import traceback
                self.error_logger.error(
                    f"Errore nella modifica della posizione {ticket}: {str(e)}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )
            return False
            
    def close_stagnant_positions(self, positions_list):
        """Chiude le posizioni stagnanti."""
        success = True
        for pos_info in positions_list:
            position = mt5.positions_get(ticket=pos_info["position"]["ticket"])
            if position is not None and len(position) > 0:
                if not self.close_position(position[0]._asdict()):
                    success = False
                    
        return success
        
    def positions_get(self):
        """Ottiene tutte le posizioni aperte."""
        return mt5.positions_get()
        
    def shutdown(self):
        """Chiude la connessione con MT5."""
        mt5.shutdown()
