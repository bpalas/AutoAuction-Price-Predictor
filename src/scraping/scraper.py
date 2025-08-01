import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import json # Para  el historial de pujas

# --- CONFIGURACIÓN ---
# Directorio de salida para el CSV
OUTPUT_DIR = os.path.join('data', 'raw')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'karcal_data_raw.csv')
BASE_URL = "https://www.karcal.cl"
NUM_PAGES_TO_SCRAPE = 20


# --- FUNCIÓN PARA EXTRAER DATOS DE LA PÁGINA DE DETALLE ---
def scrape_detail_page(detail_url):
    """
    Visita la página de detalle de un auto y extrae toda la información adicional.
    """
    try:
        response = requests.get(detail_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        detail_data = {}

        # 1. Extraer especificaciones del auto
        spec_elements = soup.find_all('div', class_='especificacion')
        for spec in spec_elements:
            spans = spec.find_all('span')
            if len(spans) == 2:
                # Limpia el nombre de la clave (ej. 'Kilometraje:') y lo convierte a minúsculas
                key = spans[0].text.replace(':', '').strip().lower()
                value = spans[1].text.strip()
                detail_data[key] = value

        # 2. Extraer oferta ganadora
        winner_bid = soup.find('h2', class_='monto-ganador')
        detail_data['oferta_ganadora'] = winner_bid.text.strip() if winner_bid else None

        # 3. Extraer URLs de los informes PDF
        report_links = soup.find_all('div', class_='detalleBotonera')
        reports = {}
        for link in report_links:
            a_tag = link.find('a')
            if a_tag and a_tag.get('href'):
                report_name = a_tag.find('span', class_=False).text.strip()
                report_url = a_tag.get('href')
                if not report_url.startswith('http'):
                    report_url = BASE_URL + report_url
                reports[report_name] = report_url
        detail_data['informes_pdf'] = json.dumps(reports, ensure_ascii=False)

        # 4. Extraer historial de ofertas y guardarlo como JSON
        history_table = soup.find('div', class_='panel-ofertas')
        bids_history = []
        if history_table:
            rows = history_table.find('tbody').find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) == 3:
                    bid = {
                        'usuario': cols[0].text.strip(),
                        'cantidad_ofertas': cols[1].text.strip(),
                        'valor_ultima_oferta': cols[2].text.strip()
                    }
                    bids_history.append(bid)
        # Convertir la lista de diccionarios a un string JSON
        detail_data['historial_ofertas'] = json.dumps(bids_history, ensure_ascii=False)

        return detail_data

    except requests.exceptions.RequestException as e:
        print(f"  -> Error al procesar detalle {detail_url}: {e}")
        return None

# --- SCRIPT PRINCIPAL ---
all_cars_data = []

print("Iniciando el scraping...")

for page_num in range(1, NUM_PAGES_TO_SCRAPE + 1):
    list_url = f"{BASE_URL}/Listado/Index/30199?NumPag={page_num}"
    print(f"Scrapeando página de listado: {page_num}")

    try:
        response = requests.get(list_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        car_containers = soup.find_all('div', class_='caluga-card')
        if not car_containers:
            print("No se encontraron más autos. Terminando.")
            break

        for car in car_containers:
            car_data = {}
            
            # Info desde la página de listado
            details = car.find_all('p', class_='nombre-bien')
            car_data['marca'] = details[0].text.strip() if len(details) > 0 else None
            car_data['modelo'] = details[1].text.strip() if len(details) > 1 else None
            car_data['listado_año'] = details[2].text.strip() if len(details) > 2 else None

            car_data['valor_inicial'] = car.find('p', class_='minimo').text.strip() if car.find('p', class_='minimo') else None
            
            # URL de la imagen
            image_tag = car.find('img')
            car_data['image_url'] = image_tag.get('src') if image_tag else None

            # URL de la ficha de detalle
            detail_link = car.find('a')
            if detail_link and detail_link.get('href'):
                detail_url = BASE_URL + detail_link.get('href')
                car_data['detail_url'] = detail_url
                
                print(f"  -> Obteniendo detalles de: {car_data.get('marca')} {car_data.get('modelo')}")
                # Obtener datos de la página de detalle
                detail_info = scrape_detail_page(detail_url)
                if detail_info:
                    # Unir la información del listado con la del detalle
                    car_data.update(detail_info)
            
            all_cars_data.append(car_data)
            time.sleep(0.1) # Pequeña pausa entre autos

    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a la página de listado {page_num}: {e}")
        continue

    time.sleep(0.2) # Pausa respetuosa entre páginas

print(f"\nScraping finalizado. Se recolectaron datos de {len(all_cars_data)} autos.")

# --- GUARDAR DATOS ---
if all_cars_data:
    # Asegurarse de que el directorio de salida exista
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    df = pd.DataFrame(all_cars_data)
    
    # Reordenar columnas para mejor legibilidad (opcional)
    column_order = ['marca', 'modelo', 'año', 'oferta_ganadora', 'kilometraje', 'transmisión', 'combustible', 
                    'placa', 'valor_inicial', 'detail_url', 'image_url', 'historial_ofertas', 'informes_pdf']
    # Filtrar para que solo existan columnas que de verdad se encontraron
    df = df.reindex(columns=[col for col in column_order if col in df.columns] + 
                           [col for col in df.columns if col not in column_order])

    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"Datos guardados exitosamente en: {OUTPUT_FILE}")
else:
    print("No se recolectaron datos para guardar.")