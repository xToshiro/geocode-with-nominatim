# geocode
Código para georreferenciamento de dados com sistema de cache integrado.

# TramaGeoPyNeov1

TramaGeoPyNeov1 is a Python project designed for geocoding addresses using a local Nominatim server. It's tailored to process large datasets efficiently, caching results to minimize API requests and ensuring data integrity through periodic saves.

## Features

- **Local Nominatim Geocoding**: Utilizes a local instance of the Nominatim API to convert addresses into geographic coordinates.
- **Efficient Processing**: Implements caching mechanisms to store geocoded results and avoid unnecessary API calls.
- **Robust Error Handling**: Includes timeout handling for API requests and logs for tracking the geocoding process and errors.
- **Progress Tracking**: Utilizes `tqdm` for real-time progress updates during the geocoding process.
- **Periodic Data Saving**: Auto-saves progress every 10,000 addresses to prevent data loss.

## Requirements

This project requires Python 3 and several external libraries listed in `requirements.txt`.

## Installation

1. Clone the repository:

git clone https://github.com/xToshiro/geocode.git

2. Install the required packages:

pip install -r requirements.txt


## Usage

1. Ensure you have a local Nominatim server running and accessible.
2. Place your input CSV file in the project directory.
3. Adjust the configuration section in the script as needed (input file name, output file name, cache file name, etc.).
4. Run the script:

python TramaGeoPyNeov1.py

## File and Column Configuration

The script uses several key files and has specific configurations for address columns:

- **Input CSV File**: `data_input = 'dadosgeocode2018T1.csv'` - The source file containing addresses to be geocoded.
- **Output CSV File**: `data_output = 'dadosgeocodificados2018T1V1.csv'` - The destination file for geocoded results.
- **Cache File**: `cache_file = 'geocodeNEO_cachev1.json'` - Stores geocoding results to minimize API requests.
- **Log File**: `log_file = 'process_logNEOv1.txt'` - Records the process log and any errors encountered.
- **Nominatim Server**: `nominatim_ip = 'http://10.102.65.194/nominatim/'` - The local Nominatim API server address.
- **Country**: `country = 'Brazil'` - The default country context for geocoding queries.

### Address Columns Configuration

Addresses are processed based on configurations defined for emission (`emi`) and destination (`des`) addresses:

- **Emission (emi)** and **Destination (des)** configurations include columns for postal code (`cep_col`), municipality (`municipio_col`), state (`uf_col`), latitude (`lat_col`), longitude (`lon_col`), processed status (`processed_col`), geocoding precision (`precision_col`), and geocoding source (`source_col`).

## Geocoding Strategy and Caching Mechanism

`TramaGeoPyNeov1` employs a strategic approach to geocoding addresses, aiming to optimize accuracy and minimize unnecessary API requests. This strategy involves three attempts with decreasing levels of detail, complemented by an efficient caching mechanism.

### Three-Tiered Geocoding Attempts

For each address, the geocoding process is attempted in three stages, each with decreasing precision levels, to balance between geocoding accuracy and query specificity:

1. **First Attempt - CEP, Município, UF**: The most detailed query, including the postal code (CEP), municipality, and state (UF) along with the country. This attempt aims for the highest precision.

2. **Second Attempt - CEP, Município**: If the first attempt fails, the query is simplified to include only the postal code and municipality. This balances detail and broad matching.

3. **Third Attempt - CEP**: The final attempt uses only the postal code, providing a broader search scope that increases the chances of getting a result, albeit with potentially lower precision.

Each query is carefully crafted to use the relevant details based on the current level of attempt, ensuring that the geocoding process is as efficient and effective as possible.

### Caching Mechanism

To enhance efficiency, `TramaGeoPyNeov1` incorporates a caching mechanism. Before making an API request, the script checks if the current query's results are already stored in a cache file. If a match is found, the cached data is used, significantly reducing the need for API calls.

- **Cache Hit**: When a query matches an entry in the cache, the cached geographic coordinates are used, and the source is marked as 'CACHE'.

- **Cache Miss and API Request**: If there's no cache entry for the query, a request is made to the Nominatim API. Successful geocoding results are then stored in the cache for future use, with the source marked as 'API'.

This caching strategy not only speeds up the geocoding process by avoiding repeated queries for the same addresses but also helps in conserving API usage quotas and reducing the load on the geocoding service.

By utilizing a multi-level query strategy and a robust caching system, `TramaGeoPyNeov1` ensures efficient and effective geocoding of addresses, making it an ideal solution for processing large datasets with varying levels of address detail.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues to improve the project.

## License

TramaGeoPyNeov1 is licensed under the GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007. See [LICENSE](LICENSE) for more details.
