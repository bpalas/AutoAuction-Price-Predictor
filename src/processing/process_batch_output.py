# -*- coding: utf-8 -*-

"""
Script para procesar los resultados de un batch de OpenAI, extraer la información
estructurada y unirla con un archivo CSV existente para crear un dataset enriquecido.
"""

import json
import pandas as pd
from pathlib import Path
import re

# --- 1. CONFIGURACIÓN DE RUTAS ---
# El script está en 'src/processing/', así que subimos DOS niveles para llegar a la raíz.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# --- ¡IMPORTANTE! MODIFICA ESTA LÍNEA CON EL NOMBRE DE TU ARCHIVO DE SALIDA ---
# Asegúrate de que este archivo esté en la carpeta 'data/batch_output_procesados/'
# Por tu captura de pantalla, parece que el archivo se llama 'batch_688d09996e...'
batch_output_file = 'batch_688d09996e208190baccb01eb575491e_output.jsonl' #<-- CAMBIA ESTO
# --- Rutas a los archivos de entrada y salida ---
# --------------------------------------------------------------------------------

# Rutas a los archivos de entrada y salida
RAW_CSV_PATH = PROJECT_ROOT / 'data' / 'raw' / 'karcal_data_raw.csv'
BATCH_JSONL_PATH = PROJECT_ROOT / 'data' / 'batch_output_procesados' / batch_output_file
PROCESSED_CSV_PATH = PROJECT_ROOT / 'data' / 'processed' / 'karcal_data_processed.csv'


def flatten_json(nested_json: dict) -> dict:
    """
    Aplanar un JSON anidado. Ej: {'a': {'b': 1}} -> {'a_b': 1}
    """
    out = {}

    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            # Convierte la lista de observaciones a un solo string separado por punto y coma
            out[name[:-1]] = "; ".join(map(str, x))
        else:
            out[name[:-1]] = x

    flatten(nested_json)
    return out

def process_and_extend_data():
    """
    Función principal que lee, procesa, une y guarda los datos.
    """
    print("🚀 Iniciando el proceso de enriquecimiento de datos...")

    # --- 2. Cargar el CSV original ---
    if not RAW_CSV_PATH.is_file():
        print(f"❌ ERROR: No se encontró el archivo CSV base en: {RAW_CSV_PATH}")
        return
    
    print(f"📄 Leyendo datos base desde: {RAW_CSV_PATH.name}")
    raw_df = pd.read_csv(RAW_CSV_PATH)
    # Asegurarnos de que la columna de la placa no tenga espacios extra
    raw_df['placa'] = raw_df['placa'].str.strip()

    # --- 3. Procesar el archivo de salida del Batch de OpenAI ---
    if not BATCH_JSONL_PATH.is_file():
        print(f"❌ ERROR: No se encontró el archivo de salida del batch en: {BATCH_JSONL_PATH}")
        print("👉 Asegúrate de que la variable 'batch_output_file' tenga el nombre correcto.")
        return

    print(f"🤖 Procesando el archivo de batch: {BATCH_JSONL_PATH.name}")
    
    new_data_rows = []
    errors = []

    with open(BATCH_JSONL_PATH, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            try:
                line_data = json.loads(line)

                # Extraer la patente del 'custom_id' (ej: 'BSWT31-1' -> 'BSWT31')
                custom_id = line_data.get('custom_id', '')
                vehicle_id = custom_id.split('-')[0]

                if not vehicle_id:
                    errors.append(f"Línea {i}: No se pudo obtener 'custom_id'.")
                    continue

                # Navegar la estructura para obtener la respuesta de la IA
                response_content_str = line_data.get('response', {}).get('body', {}).get('choices', [{}])[0].get('message', {}).get('content')
                
                if not response_content_str:
                    errors.append(f"Línea {i} ({vehicle_id}): No se encontró contenido en la respuesta.")
                    continue

                # El contenido es un string JSON, hay que cargarlo
                # A veces la IA devuelve el JSON dentro de un bloque de código markdown
                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_content_str)
                if json_match:
                    response_content_str = json_match.group(1)

                ai_data = json.loads(response_content_str)
                
                # Aplanar el JSON y añadir la patente para la unión
                flat_data = flatten_json(ai_data)
                flat_data['placa'] = vehicle_id
                
                new_data_rows.append(flat_data)

            except Exception as e:
                errors.append(f"Línea {i}: Error procesando - {e}")

    if not new_data_rows:
        print("❌ No se pudo extraer ninguna fila de datos nuevos del archivo de batch.")
        return

    print(f"✅ Se extrajeron datos para {len(new_data_rows)} vehículos.")
    if errors:
        print(f"⚠️ Se encontraron {len(errors)} errores durante el procesamiento.")
        # print("\n".join(errors[:5])) # Descomentar para ver los primeros 5 errores

    # --- 4. Unir los datos ---
    print("🔗 Uniendo los datos originales con los datos extraídos por la IA...")
    
    # Crear un DataFrame con los datos nuevos
    new_data_df = pd.DataFrame(new_data_rows)
    
    # Unir los dos DataFrames usando la columna 'placa'
    # 'how=left' para mantener todos los vehículos del archivo original
    extended_df = pd.merge(raw_df, new_data_df, on='placa', how='left')

    # --- 5. Guardar el resultado ---
    # Asegurarse de que el directorio de salida exista
    PROCESSED_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    extended_df.to_csv(PROCESSED_CSV_PATH, index=False, encoding='utf-8-sig')
    
    print("\n🎉 ¡Proceso completado con éxito!")
    print(f"💾 El archivo CSV enriquecido ha sido guardado en: {PROCESSED_CSV_PATH}")

# --- Ejecutar el script ---
if __name__ == "__main__":
    process_and_extend_data()