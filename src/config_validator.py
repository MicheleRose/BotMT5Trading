import json
from typing import Tuple, Dict, Any

class ConfigValidator:
    @staticmethod
    def validate_config() -> Tuple[bool, str]:
        """Valida il file config.json"""
        try:
            with open('config/config.json', 'r') as f:
                config = json.load(f)
            
            # Verifica sezione trading
            if 'trading' not in config:
                return False, "Sezione 'trading' mancante in config.json"
                
            trading = config['trading']
            required_trading = {
                'broker': str,
                'symbol': str,
                'timeframe': str,
                'initial_trades': int,
                'max_concurrent_trades': int,
                'pip_step_for_new_trades': (int, float),
                'trades_per_step': int,
                'max_loss': (int, float),
                'adaptive_risk': bool,
                'profit_trailing': bool,
                'strict_mode': bool,
                'trade_frequency_seconds': int
            }
            
            for key, type_ in required_trading.items():
                if key not in trading:
                    return False, f"Campo '{key}' mancante nella sezione trading"
                if not isinstance(trading[key], type_):
                    return False, f"Campo '{key}' deve essere di tipo {type_}"
            
            # Verifica lot_size
            if 'lot_size' not in trading:
                return False, "Sezione 'lot_size' mancante in trading"
                
            lot_size = trading['lot_size']
            required_lot_size = {
                'initial': (int, float),
                'increment': (int, float),
                'increment_every': int
            }
            
            for key, type_ in required_lot_size.items():
                if key not in lot_size:
                    return False, f"Campo '{key}' mancante in lot_size"
                if not isinstance(lot_size[key], type_):
                    return False, f"Campo '{key}' deve essere di tipo {type_}"
            
            # Verifica spread_check
            if 'spread_check' not in trading:
                return False, "Sezione 'spread_check' mancante in trading"
                
            spread_check = trading['spread_check']
            required_spread_check = {
                'max_spread_points': (int, float),
                'enabled': bool
            }
            
            for key, type_ in required_spread_check.items():
                if key not in spread_check:
                    return False, f"Campo '{key}' mancante in spread_check"
                if not isinstance(spread_check[key], type_):
                    return False, f"Campo '{key}' deve essere di tipo {type_}"
            
            # Verifica trailing_stop
            if 'trailing_stop' not in trading:
                return False, "Sezione 'trailing_stop' mancante in trading"
                
            trailing_stop = trading['trailing_stop']
            required_trailing_stop = {
                'pips': (int, float),
                'enabled': bool
            }
            
            for key, type_ in required_trailing_stop.items():
                if key not in trailing_stop:
                    return False, f"Campo '{key}' mancante in trailing_stop"
                if not isinstance(trailing_stop[key], type_):
                    return False, f"Campo '{key}' deve essere di tipo {type_}"
            
            # Verifica stagnant_trade
            if 'stagnant_trade' not in trading:
                return False, "Sezione 'stagnant_trade' mancante in trading"
                
            stagnant_trade = trading['stagnant_trade']
            required_stagnant_trade = {
                'max_minutes': int,
                'enabled': bool
            }
            
            for key, type_ in required_stagnant_trade.items():
                if key not in stagnant_trade:
                    return False, f"Campo '{key}' mancante in stagnant_trade"
                if not isinstance(stagnant_trade[key], type_):
                    return False, f"Campo '{key}' deve essere di tipo {type_}"
            
            # Verifica position_management
            if 'position_management' not in trading:
                return False, "Sezione 'position_management' mancante in trading"
                
            pos_mgmt = trading['position_management']
            required_pos_mgmt = {
                'min_pips_between_orders': (int, float),
                'floating_profit_close': (int, float),
                'hedge_protection': bool
            }
            
            for key, type_ in required_pos_mgmt.items():
                if key not in pos_mgmt:
                    return False, f"Campo '{key}' mancante in position_management"
                if not isinstance(pos_mgmt[key], type_):
                    return False, f"Campo '{key}' deve essere di tipo {type_}"
            
            # Verifica sezione risk_management
            if 'risk_management' not in config:
                return False, "Sezione 'risk_management' mancante in config.json"
                
            risk = config['risk_management']
            required_risk = {
                'max_drawdown_percentage': (int, float),
                'max_risk_per_trade': (int, float)
            }
            
            for key, type_ in required_risk.items():
                if key not in risk:
                    return False, f"Campo '{key}' mancante in risk_management"
                if not isinstance(risk[key], type_):
                    return False, f"Campo '{key}' deve essere di tipo {type_}"
            
            # Verifica margin_protection
            if 'margin_protection' not in risk:
                return False, "Sezione 'margin_protection' mancante in risk_management"
                
            margin_protection = risk['margin_protection']
            required_margin_protection = {
                'min_free_margin': (int, float),
                'enabled': bool
            }
            
            for key, type_ in required_margin_protection.items():
                if key not in margin_protection:
                    return False, f"Campo '{key}' mancante in margin_protection"
                if not isinstance(margin_protection[key], type_):
                    return False, f"Campo '{key}' deve essere di tipo {type_}"

            # Verifica capital_protection_thresholds
            if 'capital_protection_thresholds' not in risk:
                return False, "Sezione 'capital_protection_thresholds' mancante in risk_management"
            
            thresholds = risk['capital_protection_thresholds']
            if not isinstance(thresholds, dict):
                return False, "capital_protection_thresholds deve essere un dizionario"
            for key, value in thresholds.items():
                if not isinstance(int(key), int) or not isinstance(value, (int, float)):
                    return False, "capital_protection_thresholds deve avere chiavi intere e valori numerici"

            # Verifica sezione execution
            if 'execution' not in config:
                return False, "Sezione 'execution' mancante in config.json"
                
            execution = config['execution']
            required_execution = {
                'order_type': str,
                'deviation': int,
                'magic_number': int,
                'order_comment': str,
                'type_filling': str,
                'type_time': str
            }
            
            for key, type_ in required_execution.items():
                if key not in execution:
                    return False, f"Campo '{key}' mancante in execution"
                if not isinstance(execution[key], type_):
                    return False, f"Campo '{key}' deve essere di tipo {type_}"
            
            # Verifica sezione adaptive_sl_tp
            if 'adaptive_sl_tp' not in config:
                return False, "Sezione 'adaptive_sl_tp' mancante in config.json"
                
            adaptive = config['adaptive_sl_tp']
            required_adaptive = {
                'use_atr': bool,
                'atr_periods': int,
                'sl_multiplier': (int, float),
                'tp_multiplier': (int, float),
                'default_sl_pips': int,
                'default_tp_pips': int
            }
            
            for key, type_ in required_adaptive.items():
                if key not in adaptive:
                    return False, f"Campo '{key}' mancante in adaptive_sl_tp"
                if not isinstance(adaptive[key], type_):
                    return False, f"Campo '{key}' deve essere di tipo {type_}"
            
            # Verifica market_conditions
            if 'market_conditions' not in adaptive:
                return False, "Sezione 'market_conditions' mancante in adaptive_sl_tp"
                
            conditions = adaptive['market_conditions']
            required_conditions = ['calm', 'normal', 'volatile']
            for condition in required_conditions:
                if condition not in conditions:
                    return False, f"Condizione '{condition}' mancante in market_conditions"
                if not isinstance(conditions[condition], dict):
                    return False, f"Condizione '{condition}' deve essere un dizionario"
                if 'sl_pips' not in conditions[condition] or 'tp_pips' not in conditions[condition]:
                    return False, f"sl_pips o tp_pips mancante in condizione '{condition}'"
                if not isinstance(conditions[condition]['sl_pips'], (int, float)) or not isinstance(conditions[condition]['tp_pips'], (int, float)):
                    return False, f"sl_pips e tp_pips devono essere numeri in condizione '{condition}'"
            
            # Verifica sezione indicators
            if 'indicators' not in config:
                return False, "Sezione 'indicators' mancante in config.json"
                
            indicators = config['indicators']
            required_indicators = ['rsi', 'macd', 'bollinger', 'adx', 'stochastic', 'atr']
            for ind in required_indicators:
                if ind not in indicators:
                    return False, f"Indicatore '{ind}' mancante nella sezione indicators"
            
            # Verifica valori specifici
            if not 0 < lot_size['initial'] <= 100:
                return False, "lot_size.initial deve essere tra 0 e 100"
            if not 0 < lot_size['increment'] <= 1:
                return False, "lot_size.increment deve essere tra 0 e 1"
            
            timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']
            if trading['timeframe'] not in timeframes:
                return False, f"timeframe deve essere uno tra: {', '.join(timeframes)}"

            # Verifica valori execution
            order_types = ['market', 'limit', 'stop']
            if execution['order_type'] not in order_types:
                return False, f"order_type deve essere uno tra: {', '.join(order_types)}"

            filling_types = ['IOC', 'FOK', 'RETURN']
            if execution['type_filling'] not in filling_types:
                return False, f"type_filling deve essere uno tra: {', '.join(filling_types)}"

            time_types = ['GTC', 'DAY', 'SPECIFIED']
            if execution['type_time'] not in time_types:
                return False, f"type_time deve essere uno tra: {', '.join(time_types)}"
            
            return True, "Configurazione valida"
            
        except FileNotFoundError:
            return False, "File config.json non trovato"
        except json.JSONDecodeError:
            return False, "File config.json non è un JSON valido"
        except Exception as e:
            return False, f"Errore durante la validazione di config.json: {str(e)}"
    
    @staticmethod
    def validate_access() -> Tuple[bool, str]:
        """Valida il file access.json"""
        try:
            with open('config/access.json', 'r') as f:
                access = json.load(f)
            
            if 'mt5_account' not in access:
                return False, "Sezione 'mt5_account' mancante in access.json"
            
            account = access['mt5_account']
            required_fields = {
                'login': int,
                'password': str,
                'server': str
            }
            
            for key, type_ in required_fields.items():
                if key not in account:
                    return False, f"Campo '{key}' mancante in mt5_account"
                if not isinstance(account[key], type_):
                    return False, f"Campo '{key}' deve essere di tipo {type_}"
            
            # Verifica valori specifici
            if account['login'] <= 0:
                return False, "login deve essere un numero positivo"
            if not account['password']:
                return False, "password non può essere vuota"
            if not account['server']:
                return False, "server non può essere vuoto"
            
            return True, "Configurazione accesso valida"
            
        except FileNotFoundError:
            return False, "File access.json non trovato"
        except json.JSONDecodeError:
            return False, "File access.json non è un JSON valido"
        except Exception as e:
            return False, f"Errore durante la validazione di access.json: {str(e)}"
