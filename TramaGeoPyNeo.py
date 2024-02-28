# Coded by Jairo Ivo
# Talk is cheap. Show me the code. ― Linus Torvalds

# TramaGeoPyNeov1

#Bibliotecas
import pandas as pd
import os
import json
from datetime import datetime
import requests
from tqdm.auto import tqdm

# Configurações
data_input = 'dadosgeocode2018T1.csv'
data_output = 'dadosgeocodificados2018T1V10.csv'
cache_file = 'geocodeNEO_cachev10.json'
log_file = 'process_logNEOv10.txt'
nominatim_ip = 'http://10.102.65.194/nominatim/'
country = 'Brazil'

# Configuração das colunas de endereços
address_config = {
    'emi': {
        'cep_col': 'CEP_EMI',
        'municipio_col': 'MUNICIPIO_EMI',
        'uf_col': 'UF_EMI',
        'lat_col': 'latitude_emi',
        'lon_col': 'longitude_emi',
        'processed_col': 'emi_processed',
        'precision_col': 'emi_precision',
        'source_col': 'emi_source'
    },
    'des': {
        'cep_col': 'CEP_DES',
        'municipio_col': 'MUNICIPIO_DES',
        'uf_col': 'UF_DES',
        'lat_col': 'latitude_des',
        'lon_col': 'longitude_des',
        'processed_col': 'des_processed',
        'precision_col': 'des_precision',
        'source_col': 'des_source'
    }
}

# Função para registrar no log
def log_message(message):
    with open(log_file, "a") as log:
        log.write(f"{datetime.now()}: {message}\n")
        #print(f"{datetime.now()}: {message}\n")
        
# Função para verificar e carregar o arquivo de input
def load_input_file():
    if os.path.exists(data_input):
        df = pd.read_csv(data_input, low_memory=False)
        log_message(f"Arquivo de entrada {data_input} carregado com sucesso.")
        return df
    else:
        log_message(f"Erro: O arquivo de entrada {data_input} não foi encontrado.")
        raise FileNotFoundError(f"O arquivo de entrada {data_input} não foi encontrado.")

# Função para carregar ou inicializar o arquivo de output
def load_or_initialize_output_file(df_input):
    if os.path.exists(data_output):
        df_output = pd.read_csv(data_output, low_memory=False)
        log_message(f"Arquivo de saída {data_output} carregado com sucesso.")
    else:
        df_output = prepare_output_dataframe(df_input)
        df_output.to_csv(data_output, index=False)
        log_message(f"Arquivo de saída {data_output} criado com sucesso.")
    return df_output

def prepare_output_dataframe(df):
    for key, config in address_config.items():
        # Inicializa ou converte as colunas para os tipos desejados diretamente, sem usar .get()
        if config['lat_col'] not in df.columns:
            df[config['lat_col']] = 0.0  # Define um valor padrão para a coluna se ela não existir
        df[config['lat_col']] = pd.to_numeric(df[config['lat_col']], errors='coerce').astype(float)
        
        if config['lon_col'] not in df.columns:
            df[config['lon_col']] = 0.0
        df[config['lon_col']] = pd.to_numeric(df[config['lon_col']], errors='coerce').astype(float)
        
        if config['processed_col'] not in df.columns:
            df[config['processed_col']] = False
        df[config['processed_col']] = df[config['processed_col']].astype(bool)
        
        if config['precision_col'] not in df.columns:
            df[config['precision_col']] = 0
        df[config['precision_col']] = pd.to_numeric(df[config['precision_col']], errors='coerce').astype(int)
        
        if config['source_col'] not in df.columns:
            df[config['source_col']] = ''
        df[config['source_col']] = df[config['source_col']].astype(str)

    log_message("DataFrame de saída preparado com sucesso.")
    return df
    
def load_or_create_cache():
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            cache = json.load(f)
        log_message(f"Arquivo de cache carregado com sucesso: {cache_file}")
    else:
        cache = {}
        log_message(f"Arquivo de cache não encontrado. Um novo cache será criado: {cache_file}")
    return cache

# Função para salvar o cache atualizado
def save_cache(cache):
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=4)

# Função para geocodificar endereços usando a API Nominatim local
def geocode_address(query):
    try:
        request_url = f"{nominatim_ip}search?q={query}&format=json&addressdetails=1&countrycodes=br"
        # Define o timeout para a solicitação como 30 segundos
        response = requests.get(request_url, timeout=30)
        results = response.json()
        if results:
            result = results[0]  # Assume o primeiro resultado como o mais relevante
            lat = float(result['lat'])
            lon = float(result['lon'])
            return {'lat': lat, 'lon': lon}
    except requests.exceptions.Timeout:
        # Registra um log em caso de timeout
        log_message(f"Timeout na geocodificação para a query: {query}")
    except Exception as e:
        log_message(f"Erro na geocodificação: {e}")
    return None

# Função para inicializar o arquivo de log
def initialize_log_file():
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            f.write("")  # Cria um arquivo de log vazio
    log_message("Inicialização do script de processamento de dados.")

# Atualiza a função de geocodificação com cache e API para incluir os ajustes de tipo
def geocode_with_cache_and_api(df, address_type):
    cache = load_or_create_cache()
    processed_count = 0
    to_process = df[df[address_config[address_type]['processed_col']] == False]
    log_message(f"Iniciando geocodificação para {address_type}. Total de endereços a processar: {len(to_process)}.")

    for index in tqdm(to_process.index, desc=f"Geocodificando {address_type}"):
        row = df.loc[index]
        success = False
        for precision_level in [3, 2, 1]:
            # Ajuste na formação da query para usar o nome do município ao invés de códigos numéricos
            query_parts = [str(row[address_config[address_type][field]]) for field in ['cep_col', 'municipio_col', 'uf_col'][:precision_level]]
            if precision_level == 3:  # CEP, Município, UF
                query = f"{query_parts[0]}, {query_parts[1]}, {query_parts[2]}, {country}"
            elif precision_level == 2:  # CEP, Município
                query = f"{query_parts[0]}, {query_parts[1]}, {country}"
            else:  # CEP
                query = f"{query_parts[0]}, {country}"

            cache_key = "-".join(query_parts)

            if cache_key in cache:
                data = cache[cache_key]
                source = 'CACHE'
            else:
                geocoded_data = geocode_address(query)
                if geocoded_data:
                    data = {'lat': geocoded_data['lat'], 'lon': geocoded_data['lon'], 'precision': precision_level}
                    cache[cache_key] = data
                    source = 'API'
                else:
                    continue  # Falha na geocodificação, tenta o próximo nível de precisão

            # Atualização do DataFrame
            df.at[index, address_config[address_type]['lat_col']] = data['lat']
            df.at[index, address_config[address_type]['lon_col']] = data['lon']
            df.at[index, address_config[address_type]['precision_col']] = data['precision']
            df.at[index, address_config[address_type]['source_col']] = source
            df.at[index, address_config[address_type]['processed_col']] = True
            success = True
            break  # Sai do loop após sucesso na geocodificação

        if not success:
            df.at[index, address_config[address_type]['processed_col']] = False
            log_message(f"Endereço '{cache_key}' não geocodificado com sucesso.")

        processed_count += 1
        if processed_count % 10000 == 0:
            df.to_csv(data_output, index=False)
            save_cache(cache)
            log_message(f"Progresso salvo após processar {processed_count} endereços de {address_type}.")
            log_message("Cache atualizado.")

    save_cache(cache)
    df.to_csv(data_output, index=False)  # Salva os dados ao final do processamento
    log_message(f"Geocodificação para {address_type} concluída.")
    return df
    
#Principais funções para executar e ordem de geocodificação;
def main():
    initialize_log_file()
    if not os.path.exists(data_input):
        log_message(f"Arquivo de entrada não encontrado: {data_input}")
        print(f"Arquivo de entrada não encontrado: {data_input}")
        return

    df_input = load_input_file()
    df_output = load_or_initialize_output_file(df_input)
    df_output = prepare_output_dataframe(df_output)  # Garante que o DataFrame esteja preparado
    df_output = geocode_with_cache_and_api(df_output, 'emi')
    log_message("Geocodificação dos dados de emissão completa.")
    print("Geocodificação dos dados de emissão completa.")
    df_output = geocode_with_cache_and_api(df_output, 'des')
    log_message("Geocodificação dos dados de destino completa.")
    print("Geocodificação dos dados de destino completa.")
    df_output.to_csv(data_output, index=False)  # Salva o DataFrame final
    log_message("Geocodificação completa. Dados salvos.")
    print("Geocodificação completa. Dados salvos.")

if __name__ == "__main__":
    main()