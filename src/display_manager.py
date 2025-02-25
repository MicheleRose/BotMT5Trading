import os
import logging
from logging.handlers import RotatingFileHandler

class DisplayManager:
    def __init__(self):
        # Crea cartella logs se non esiste
        self.logs_dir = "logs"
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
            
        # Configura i logger
        self.setup_loggers()
        
        # Stato dell'interfaccia
        self.paused = False
        self.last_log = None
        
    def setup_loggers(self):
        """Configura i logger per journal ed errori."""
        # Journal logger
        self.journal_logger = logging.getLogger('journal')
        self.journal_logger.setLevel(logging.INFO)
        self.journal_logger.handlers = []  # Rimuovi handler esistenti
        journal_handler = RotatingFileHandler(
            os.path.join(self.logs_dir, 'journal.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        journal_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(message)s', '%Y-%m-%d %H:%M:%S')
        )
        self.journal_logger.addHandler(journal_handler)
        
        # Error logger
        self.error_logger = logging.getLogger('error')
        self.error_logger.setLevel(logging.ERROR)
        self.error_logger.handlers = []  # Rimuovi handler esistenti
        error_handler = RotatingFileHandler(
            os.path.join(self.logs_dir, 'error.log'),
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setFormatter(
            logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s\nStack trace:\n%(stack_info)s', '%Y-%m-%d %H:%M:%S')
        )
        self.error_logger.addHandler(error_handler)
    
    def format_trade_log(self, data: dict) -> str:
        """Formatta il log di un trade con tutti i parametri."""
        trade_type = data.get('type', '')
        volume = data.get('volume', 0)
        price = data.get('price', 0)
        sl = data.get('sl', 0)
        tp = data.get('tp', 0)
        spread = data.get('spread', 0)
        
        # Indicatori
        indicators = data.get('indicators', {})
        rsi = indicators.get('rsi', 0)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        bb_up = indicators.get('bb_up', 0)
        bb_down = indicators.get('bb_down', 0)
        
        # Condizioni
        conditions = data.get('conditions', {})
        buy_conditions = conditions.get('buy_conditions', '0/3')
        sell_conditions = conditions.get('sell_conditions', '0/3')
        
        message = (
            f"{trade_type}: "
            f"Volume={volume:.2f}, Price={price:.2f}, SL={sl:.2f}, TP={tp:.2f}, Spread={spread:.2f} | "
            f"RSI={rsi:.1f}, MACD={macd:.4f}/{macd_signal:.4f}, BB={bb_down:.2f}/{bb_up:.2f} | "
            f"Condizioni: BUY={buy_conditions}, SELL={sell_conditions}"
        )
        return message
        
    def format_close_log(self, data: dict) -> str:
        """Formatta il log di chiusura posizioni."""
        reason = data.get('reason', 'Non specificato')
        profit = data.get('profit', 0)
        indicators = data.get('indicators', {})
        
        message = (
            f"CHIUSURA: {reason} | "
            f"Profitto={profit:.2f} | "
            f"RSI={indicators.get('rsi', 0):.1f}, "
            f"MACD={indicators.get('macd', 0):.4f}/{indicators.get('macd_signal', 0):.4f}, "
            f"BB={indicators.get('bb_down', 0):.2f}/{indicators.get('bb_up', 0):.2f}"
        )
        return message
    
    def log_trade(self, data: dict):
        """Logga un'operazione di trading nel journal."""
        message = self.format_trade_log(data)
        self.journal_logger.info(message)
        self.last_log = f"TRADE: {message}"
        print(self.last_log)
        
    def log_close(self, data: dict):
        """Logga una chiusura posizioni nel journal."""
        message = self.format_close_log(data)
        self.journal_logger.info(message)
        self.last_log = message
        print(self.last_log)
    
    def log_error(self, message: str):
        """Logga un errore e mette in pausa l'applicazione."""
        import traceback
        stack_trace = traceback.extract_stack()[:-1]  # Escludi questa chiamata
        trace_str = ''.join(traceback.format_list(stack_trace))
        self.error_logger.error(message, stack_info=trace_str)
        self.paused = True
        self.last_log = f"ERRORE: {message}"
        print(self.last_log)
        
    def clear_error(self):
        """Rimuove l'errore e riprende l'esecuzione."""
        self.paused = False
        
    def update(self, section: str, data: dict):
        """Aggiorna una sezione dell'interfaccia."""
        if section == "TRADE":
            self.log_trade(data)
            
        elif section == "CLOSE":
            self.log_close(data)
            
        elif section == "ERROR":
            self.log_error(data.get('message', 'Errore sconosciuto'))
            
        elif section == "STATUS":
            message = f"{data.get('time', '')} - {data.get('message', '')}"
            print(message)
