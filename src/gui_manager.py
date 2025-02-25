import tkinter as tk
from tkinter import ttk
import threading
import queue
import sys
from datetime import datetime

class GUIManager:
    def __init__(self):
        # Coda per la comunicazione tra thread
        self.update_queue = queue.Queue()
        self.ready = threading.Event()
        
        # Avvia GUI in un thread separato
        self.gui_thread = threading.Thread(target=self._run_gui)
        self.gui_thread.daemon = True
        self.gui_thread.start()
        
        # Attendi che la GUI sia pronta
        self.ready.wait(timeout=10)
        
    def _run_gui(self):
        """Avvia l'interfaccia grafica in un thread separato."""
        try:
            # Crea la finestra principale
            self.root = tk.Tk()
            self.root.title("AI Scalping Ultra v2.0")
            self.root.geometry("800x600")
            
            # Gestore chiusura
            self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
            
            # Configura il tema
            style = ttk.Style()
            style.theme_use('clam')
            style.configure("Green.TLabel", foreground="green")
            style.configure("Red.TLabel", foreground="red")
            style.configure("Header.TLabel", font=('Helvetica', 10, 'bold'))
            
            # Crea l'interfaccia
            self._create_widgets()
            
            # Avvia il thread per gli aggiornamenti
            self.update_thread = threading.Thread(target=self._process_updates)
            self.update_thread.daemon = True
            self.update_thread.start()
            
            # Segnala che la GUI è pronta
            self.ready.set()
            
            # Avvia il loop di eventi
            self.root.mainloop()
            
        except Exception as e:
            print(f"Errore nell'inizializzazione della GUI: {str(e)}")
            self.ready.set()  # Segnala comunque per evitare deadlock
            
    def _create_widgets(self):
        """Crea tutti i widget dell'interfaccia."""
        # Header
        header = ttk.Frame(self.root, padding="5")
        header.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(header, text="AI SCALPING ULTRA v2.0", style="Header.TLabel").pack(side=tk.LEFT)
        self.status_var = tk.StringVar(value="Inizializzazione...")
        ttk.Label(header, textvariable=self.status_var).pack(side=tk.RIGHT)
        
        # Market Data
        market_frame = ttk.LabelFrame(self.root, text="MERCATO", padding="5")
        market_frame.pack(fill=tk.X, padx=5, pady=5)
        self.market_data = {
            'symbol': tk.StringVar(value="-"),
            'spread': tk.StringVar(value="-"),
            'bid': tk.StringVar(value="-"),
            'ask': tk.StringVar(value="-"),
            'rsi': tk.StringVar(value="-"),
            'macd': tk.StringVar(value="-"),
            'signal': tk.StringVar(value="-"),
            'bb_up': tk.StringVar(value="-"),
            'bb_down': tk.StringVar(value="-")
        }
        
        row = 0
        ttk.Label(market_frame, text="Simbolo:").grid(row=row, column=0, sticky=tk.W)
        ttk.Label(market_frame, textvariable=self.market_data['symbol']).grid(row=row, column=1, sticky=tk.W)
        
        row += 1
        ttk.Label(market_frame, text="Spread:").grid(row=row, column=0, sticky=tk.W)
        spread_frame = ttk.Frame(market_frame)
        spread_frame.grid(row=row, column=1, sticky=tk.W)
        ttk.Label(spread_frame, textvariable=self.market_data['spread']).pack(side=tk.LEFT)
        
        row += 1
        ttk.Label(market_frame, text="Bid/Ask:").grid(row=row, column=0, sticky=tk.W)
        bid_ask_frame = ttk.Frame(market_frame)
        bid_ask_frame.grid(row=row, column=1, sticky=tk.W)
        ttk.Label(bid_ask_frame, textvariable=self.market_data['bid']).pack(side=tk.LEFT)
        ttk.Label(bid_ask_frame, text=" / ").pack(side=tk.LEFT)
        ttk.Label(bid_ask_frame, textvariable=self.market_data['ask']).pack(side=tk.LEFT)
        
        row += 1
        ttk.Label(market_frame, text="RSI:").grid(row=row, column=0, sticky=tk.W)
        ttk.Label(market_frame, textvariable=self.market_data['rsi']).grid(row=row, column=1, sticky=tk.W)
        
        row += 1
        ttk.Label(market_frame, text="MACD:").grid(row=row, column=0, sticky=tk.W)
        ttk.Label(market_frame, textvariable=self.market_data['macd']).grid(row=row, column=1, sticky=tk.W)
        
        row += 1
        ttk.Label(market_frame, text="Signal:").grid(row=row, column=0, sticky=tk.W)
        ttk.Label(market_frame, textvariable=self.market_data['signal']).grid(row=row, column=1, sticky=tk.W)
        
        row += 1
        ttk.Label(market_frame, text="BB:").grid(row=row, column=0, sticky=tk.W)
        bb_frame = ttk.Frame(market_frame)
        bb_frame.grid(row=row, column=1, sticky=tk.W)
        ttk.Label(bb_frame, textvariable=self.market_data['bb_up']).pack(side=tk.LEFT)
        ttk.Label(bb_frame, text=" / ").pack(side=tk.LEFT)
        ttk.Label(bb_frame, textvariable=self.market_data['bb_down']).pack(side=tk.LEFT)
        
        # Analysis
        analysis_frame = ttk.LabelFrame(self.root, text="ANALISI", padding="5")
        analysis_frame.pack(fill=tk.X, padx=5, pady=5)
        self.analysis_data = {
            'rsi': tk.StringVar(value="-"),
            'rsi_status': tk.StringVar(value="-"),
            'macd': tk.StringVar(value="-"),
            'macd_trend': tk.StringVar(value="-"),
            'price': tk.StringVar(value="-"),
            'position': tk.StringVar(value="-")
        }
        
        row = 0
        ttk.Label(analysis_frame, text="RSI:").grid(row=row, column=0, sticky=tk.W)
        rsi_frame = ttk.Frame(analysis_frame)
        rsi_frame.grid(row=row, column=1, sticky=tk.W)
        ttk.Label(rsi_frame, textvariable=self.analysis_data['rsi']).pack(side=tk.LEFT)
        ttk.Label(rsi_frame, text=" (").pack(side=tk.LEFT)
        ttk.Label(rsi_frame, textvariable=self.analysis_data['rsi_status']).pack(side=tk.LEFT)
        ttk.Label(rsi_frame, text=")").pack(side=tk.LEFT)
        
        row += 1
        ttk.Label(analysis_frame, text="MACD:").grid(row=row, column=0, sticky=tk.W)
        macd_frame = ttk.Frame(analysis_frame)
        macd_frame.grid(row=row, column=1, sticky=tk.W)
        ttk.Label(macd_frame, textvariable=self.analysis_data['macd']).pack(side=tk.LEFT)
        ttk.Label(macd_frame, text=" (").pack(side=tk.LEFT)
        ttk.Label(macd_frame, textvariable=self.analysis_data['macd_trend']).pack(side=tk.LEFT)
        ttk.Label(macd_frame, text=")").pack(side=tk.LEFT)
        
        row += 1
        ttk.Label(analysis_frame, text="Prezzo:").grid(row=row, column=0, sticky=tk.W)
        price_frame = ttk.Frame(analysis_frame)
        price_frame.grid(row=row, column=1, sticky=tk.W)
        ttk.Label(price_frame, textvariable=self.analysis_data['price']).pack(side=tk.LEFT)
        ttk.Label(price_frame, text=" (").pack(side=tk.LEFT)
        ttk.Label(price_frame, textvariable=self.analysis_data['position']).pack(side=tk.LEFT)
        ttk.Label(price_frame, text=")").pack(side=tk.LEFT)
        
        # Signals
        signals_frame = ttk.LabelFrame(self.root, text="SEGNALI", padding="5")
        signals_frame.pack(fill=tk.X, padx=5, pady=5)
        self.signals_data = {
            'buy_conditions': tk.StringVar(value="0/3"),
            'sell_conditions': tk.StringVar(value="0/3"),
            'rsi_check': tk.StringVar(value="✗"),
            'macd_check': tk.StringVar(value="✗"),
            'bb_check': tk.StringVar(value="✗")
        }
        
        # Condizioni
        conditions_frame = ttk.Frame(signals_frame)
        conditions_frame.pack(fill=tk.X)
        ttk.Label(conditions_frame, text="BUY: ").pack(side=tk.LEFT)
        ttk.Label(conditions_frame, textvariable=self.signals_data['buy_conditions']).pack(side=tk.LEFT)
        ttk.Label(conditions_frame, text=" | SELL: ").pack(side=tk.LEFT)
        ttk.Label(conditions_frame, textvariable=self.signals_data['sell_conditions']).pack(side=tk.LEFT)
        
        # Indicatori
        indicators_frame = ttk.Frame(signals_frame)
        indicators_frame.pack(fill=tk.X)
        ttk.Label(indicators_frame, text="RSI: ").pack(side=tk.LEFT)
        ttk.Label(indicators_frame, textvariable=self.signals_data['rsi_check'], style="Green.TLabel").pack(side=tk.LEFT)
        ttk.Label(indicators_frame, text=" | MACD: ").pack(side=tk.LEFT)
        ttk.Label(indicators_frame, textvariable=self.signals_data['macd_check'], style="Red.TLabel").pack(side=tk.LEFT)
        ttk.Label(indicators_frame, text=" | BB: ").pack(side=tk.LEFT)
        ttk.Label(indicators_frame, textvariable=self.signals_data['bb_check'], style="Red.TLabel").pack(side=tk.LEFT)
        
        # Trades
        trades_frame = ttk.LabelFrame(self.root, text="ULTIMO TRADE", padding="5")
        trades_frame.pack(fill=tk.X, padx=5, pady=5)
        self.trades_data = {
            'type': tk.StringVar(value="-"),
            'volume': tk.StringVar(value="-"),
            'price': tk.StringVar(value="-"),
            'sl': tk.StringVar(value="-"),
            'tp': tk.StringVar(value="-"),
            'spread': tk.StringVar(value="-")
        }
        
        row = 0
        ttk.Label(trades_frame, text="Tipo:").grid(row=row, column=0, sticky=tk.W)
        ttk.Label(trades_frame, textvariable=self.trades_data['type']).grid(row=row, column=1, sticky=tk.W)
        
        row += 1
        ttk.Label(trades_frame, text="Volume:").grid(row=row, column=0, sticky=tk.W)
        ttk.Label(trades_frame, textvariable=self.trades_data['volume']).grid(row=row, column=1, sticky=tk.W)
        
        row += 1
        ttk.Label(trades_frame, text="Prezzo:").grid(row=row, column=0, sticky=tk.W)
        ttk.Label(trades_frame, textvariable=self.trades_data['price']).grid(row=row, column=1, sticky=tk.W)
        
        row += 1
        ttk.Label(trades_frame, text="SL/TP:").grid(row=row, column=0, sticky=tk.W)
        sl_tp_frame = ttk.Frame(trades_frame)
        sl_tp_frame.grid(row=row, column=1, sticky=tk.W)
        ttk.Label(sl_tp_frame, textvariable=self.trades_data['sl'], style="Red.TLabel").pack(side=tk.LEFT)
        ttk.Label(sl_tp_frame, text=" / ").pack(side=tk.LEFT)
        ttk.Label(sl_tp_frame, textvariable=self.trades_data['tp'], style="Green.TLabel").pack(side=tk.LEFT)
        
        row += 1
        ttk.Label(trades_frame, text="Spread:").grid(row=row, column=0, sticky=tk.W)
        ttk.Label(trades_frame, textvariable=self.trades_data['spread']).grid(row=row, column=1, sticky=tk.W)
        
        # Log
        log_frame = ttk.LabelFrame(self.root, text="ULTIMO LOG", padding="5")
        log_frame.pack(fill=tk.X, padx=5, pady=5)
        self.log_label = ttk.Label(log_frame, text="-")
        self.log_label.pack(fill=tk.X)
        
        # Error
        error_frame = ttk.Frame(self.root, padding="5")
        error_frame.pack(fill=tk.X, padx=5, pady=5)
        self.error_label = ttk.Label(error_frame, text="", style="Red.TLabel", wraplength=780)
        self.error_label.pack(fill=tk.X)
        
    def _on_closing(self):
        """Gestisce la chiusura della finestra."""
        try:
            # Termina il thread degli aggiornamenti
            if hasattr(self, 'update_thread') and self.update_thread.is_alive():
                self.update_queue.put(('QUIT', None))  # Segnale di uscita
                self.update_thread.join(timeout=1)
            
            # Chiudi la finestra
            if self.root:
                self.root.quit()
                self.root.destroy()
            
            # Termina il processo principale
            import os
            os._exit(0)
        except:
            # In caso di errore, forza la chiusura
            os._exit(1)
        
    def update(self, section: str, data: dict):
        """Aggiorna una sezione dell'interfaccia."""
        try:
            self.update_queue.put((section, data.copy()))
        except Exception as e:
            print(f"Errore nell'aggiornamento GUI: {str(e)}")
            
    def _process_updates(self):
        """Processa gli aggiornamenti in un thread separato."""
        while True:
            try:
                # Attendi un aggiornamento con timeout
                section, data = self.update_queue.get(timeout=1)
                
                # Controlla segnale di uscita
                if section == 'QUIT':
                    break
                    
                # Processa l'aggiornamento
                if section == "STATUS":
                    self.status_var.set(f"{data.get('time', '')} - {data.get('message', '')}")
                    
                elif section == "MARKET":
                    for key in self.market_data:
                        if key in data:
                            if isinstance(data[key], (int, float)):
                                if key == 'spread':
                                    self.market_data[key].set(f"{data[key]:.1f}")
                                elif key in ['bid', 'ask', 'bb_up', 'bb_down']:
                                    self.market_data[key].set(f"{data[key]:.2f}")
                                elif key in ['macd', 'signal']:
                                    self.market_data[key].set(f"{data[key]:.4f}")
                                else:
                                    self.market_data[key].set(f"{data[key]:.1f}")
                            else:
                                self.market_data[key].set(str(data[key]))
                            
                elif section == "ANALYSIS":
                    for key in self.analysis_data:
                        if key in data:
                            if isinstance(data[key], (int, float)):
                                if key == 'price':
                                    self.analysis_data[key].set(f"{data[key]:.2f}")
                                elif key == 'macd':
                                    self.analysis_data[key].set(f"{data[key]:.4f}")
                                else:
                                    self.analysis_data[key].set(f"{data[key]:.1f}")
                            else:
                                self.analysis_data[key].set(str(data[key]))
                            
                elif section == "SIGNALS":
                    for key in self.signals_data:
                        if key in data:
                            if key in ['rsi_check', 'macd_check', 'bb_check']:
                                self.signals_data[key].set("✓" if data[key] else "✗")
                            else:
                                self.signals_data[key].set(str(data[key]))
                            
                elif section == "TRADE":
                    for key in self.trades_data:
                        if key in data:
                            if isinstance(data[key], (int, float)):
                                self.trades_data[key].set(f"{data[key]:.2f}")
                            else:
                                self.trades_data[key].set(str(data[key]))
                    # Aggiorna anche il log
                    log_msg = f"{data.get('type', '-')}: Volume={data.get('volume', 0):.2f}, Price={data.get('price', 0):.2f}, SL={data.get('sl', 0):.2f}, TP={data.get('tp', 0):.2f}"
                    self.log_label.configure(text=log_msg)
                            
                elif section == "ERROR":
                    self.error_label.configure(text=data.get('message', ''))
                    # Pulisci il log in caso di errore
                    self.log_label.configure(text="-")
                    
            except queue.Empty:
                # Timeout, continua il loop
                continue
            except Exception as e:
                print(f"Errore nell'aggiornamento sezione {section}: {str(e)}")
            finally:
                if section != 'QUIT':
                    self.update_queue.task_done()
