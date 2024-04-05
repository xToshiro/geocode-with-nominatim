import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext, Label
import pandas as pd
import threading
import requests
import json
import logging
import os

# Configuração do logging
LOG_FILE = "geocoding.log"
CACHE_FILE = "geocoding_cache.json"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

# Sinalizador global para interromper a geocodificação
stop_geocoding = False
nominatim_ip = 'http://10.102.65.194/nominatim/'

def log_message(message):
    logging.info(message)

def load_or_create_cache():
    if not os.path.isfile(CACHE_FILE):
        with open(CACHE_FILE, 'w') as file:
            json.dump({}, file)
        log_message("New cache file created.")
    try:
        with open(CACHE_FILE, 'r') as file:
            cache = json.load(file)
    except json.JSONDecodeError:
        log_message("Cache file is corrupted. Creating a new one.")
        cache = {}
    return cache

def update_cache(cache):
    with open(CACHE_FILE, 'w') as file:
        json.dump(cache, file, indent=4)

def geocode_address(query, precision_level):
    try:
        request_url = f"{nominatim_ip}search?q={query}&format=json&addressdetails=1&countrycodes=br"
        response = requests.get(request_url, timeout=30)
        results = response.json()
        if results:
            result = results[0]
            lat = float(result['lat'])
            lon = float(result['lon'])
            return {'lat': lat, 'lon': lon, 'precision': precision_level}
    except requests.exceptions.Timeout:
        log_message(f"Timeout na geocodificação para a query: {query}")
    except Exception as e:
        log_message(f"Erro na geocodificação: {e}")
    return None

def geocode_addresses(input_file, selected_columns, progress_callback, finished_callback, status_callback):
    global stop_geocoding
    status_callback("Preparing data... This may take some time...")
    df_input = pd.read_excel(input_file)
    
    cache = load_or_create_cache()
    
    # Define o caminho do arquivo de saída com antecedência
    output_file = os.path.splitext(input_file)[0] + "_geocoded.xlsx"
    
    status_callback("Geocoding data...")
    for index, row in df_input.iterrows():
        if stop_geocoding:
            break
        
        # Verifica se o endereço já foi geocodificado para evitar processamento duplicado
        if pd.notna(row.get('Latitude')) and pd.notna(row.get('Longitude')):
            progress_callback(index + 1, df_input.shape[0])
            continue  # Se já geocodificado, passa para o próximo endereço
        
        success = False
        for precision_level in range(len(selected_columns), 0, -1):
            address_parts = [str(row[col]).strip() for col in selected_columns[:precision_level]]
            address = ', '.join(address_parts) + ', br'
            cache_key = '-'.join(address_parts)
            
            if cache_key in cache:
                result = cache[cache_key]
            else:
                result = geocode_address(address, precision_level)
                if result:
                    cache[cache_key] = result
                    update_cache(cache)
                else:
                    continue  # Próximo nível de precisão

            if result:
                df_input.at[index, 'Latitude'] = result['lat']
                df_input.at[index, 'Longitude'] = result['lon']
                df_input.at[index, 'Precision'] = result['precision']
                progress_callback(index + 1, df_input.shape[0])
                success = True
                # Salva o DataFrame após cada geocodificação com sucesso
                df_input.to_excel(output_file, index=False)
                break

        if not success:
            log_message(f"Endereço '{cache_key}' não foi geocodificado com sucesso.")
    
    update_cache(cache)
    finished_callback(output_file, not stop_geocoding)


class GeocodeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Transporte e Meio Ambiente(Trama) - Geocoding App with Local Nominatim API - APP")
        self.geometry("700x550")
        
        self.nominatim_ip = tk.StringVar(value=nominatim_ip)
        
        self.create_widgets()
        self.file_path = ""
        self.column_checkboxes = []
        self.selected_columns = []
        
    def create_widgets(self):
        self.file_label = tk.Label(self, text="No file selected")
        self.file_label.pack(pady=10)
        
        self.browse_button = tk.Button(self, text="Browse", command=self.browse_file)
        self.browse_button.pack()

        self.api_frame = tk.LabelFrame(self, text="Nominatim API Settings")
        self.api_frame.pack(pady=10, fill="x", expand="no")
        
        self.api_label = tk.Label(self.api_frame, text="API IP:")
        self.api_label.pack(side=tk.LEFT, padx=5)
        
        self.api_entry = tk.Entry(self.api_frame, textvariable=self.nominatim_ip, width=50)
        self.api_entry.pack(side=tk.LEFT, padx=5)
        
        self.test_api_button = tk.Button(self.api_frame, text="Test", command=self.test_nominatim_api)
        self.test_api_button.pack(side=tk.LEFT, padx=5)
        
        self.api_status = Label(self.api_frame, text="●", fg="red", font=("TkDefaultFont", 16))
        self.api_status.pack(side=tk.LEFT, padx=5)
        
        self.columns_frame = tk.LabelFrame(self, text="Columns")
        self.columns_scroll = scrolledtext.ScrolledText(self.columns_frame, width=50, height=10, wrap=tk.WORD)
        self.columns_scroll.pack()
        self.columns_frame.pack(pady=10, fill="both", expand="yes")
        
        self.status_label = tk.Label(self, text="")
        self.status_label.pack(pady=10)

        self.start_button = tk.Button(self, text="Start Geocoding", command=self.start_geocoding)
        self.start_button.pack(pady=5)
        
        self.stop_button = tk.Button(self, text="Stop Geocoding", command=self.stop_geocoding, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.progress_label = tk.Label(self, text="Progress: 0/0")
        self.progress_label.pack(pady=5)
        
        self.progress = ttk.Progressbar(self, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.pack(pady=20)

    def test_nominatim_api(self):
        try:
            response = requests.get(self.nominatim_ip.get(), timeout=5)
            if response.status_code == 200:
                self.api_status.config(fg="green")
                messagebox.showinfo("API Test", "Nominatim API is online.")
            else:
                self.api_status.config(fg="red")
                messagebox.showerror("API Test", "Nominatim API is offline.")
        except:
            self.api_status.config(fg="red")
            messagebox.showerror("API Test", "Nominatim API is offline.")

    def browse_file(self):
        global stop_geocoding
        stop_geocoding = False
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            self.file_path = file_path
            self.file_label.config(text=f"File: {os.path.basename(file_path)}")
            self.display_column_checkboxes(file_path)

    def display_column_checkboxes(self, file_path):
        for widget in self.columns_frame.winfo_children():
            widget.destroy()
        
        df = pd.read_excel(file_path)
        self.selected_columns = []
        for col in df.columns:
            var = tk.BooleanVar()
            chk = tk.Checkbutton(self.columns_frame, text=col, variable=var)
            chk.pack(anchor='w')
            self.column_checkboxes.append((var, col))
    
    def update_progress(self, current, total):
        self.progress['value'] = (current / total) * 100
        self.progress_label.config(text=f"Progress: {current}/{total}")
        self.update_idletasks()

    def finished_geocoding(self, output_file, success):
        if success:
            messagebox.showinfo("Complete", f"Geocoding complete. Output saved to {output_file}")
        else:
            messagebox.showinfo("Stopped", "Geocoding stopped by user.")
        self.start_button['state'] = tk.NORMAL
        self.stop_button['state'] = tk.DISABLED
    
    def update_status(self, message):
        self.status_label.config(text=message)
        self.update_idletasks()

    def start_geocoding(self):
        global stop_geocoding
        stop_geocoding = False
        selected_columns = [col for var, col in self.column_checkboxes if var.get()]
        if not self.file_path or not selected_columns:
            messagebox.showerror("Error", "Please select a file and at least one column.")
            return
        self.start_button['state'] = tk.DISABLED
        self.stop_button['state'] = tk.NORMAL
        threading.Thread(target=geocode_addresses, args=(self.file_path, selected_columns, self.update_progress, self.finished_geocoding, self.update_status)).start()

    def stop_geocoding(self):
        global stop_geocoding
        stop_geocoding = True
        self.stop_button['state'] = tk.DISABLED

if __name__ == "__main__":
    app = GeocodeApp()
    app.mainloop()
