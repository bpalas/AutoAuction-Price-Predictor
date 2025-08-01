import pandas as pd
import requests
import json
import os
import re
import fitz  # PyMuPDF

# --- CONFIGURACIÓN DE RUTAS ---
# Ajusta estas rutas según la estructura de tu proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW_DATA_PATH = os.path.join(BASE_DIR, 'data', 'raw', 'karcal_data_raw.csv')
PDF_DIR = os.path.join(BASE_DIR, 'reports', 'pdf')
TXT_DIR = os.path.join(BASE_DIR, 'reports', 'txt_prompts')

# --- FUNCIONES AUXILIARES ---

def sanitize_filename(name):
    """Limpia un string para que sea un nombre de archivo válido."""
    name = re.sub(r'[^\w\s-]', '', name).strip()
    name = re.sub(r'[-\s]+', '_', name)
    return name

def pdf_to_text(pdf_path):
    """Convierte un archivo PDF a un string de texto."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        print(f"  -> Error al convertir PDF {os.path.basename(pdf_path)}: {e}")
        return ""

def process_vehicle_reports(row):
    """
    Descarga, convierte y consolida los informes de un vehículo en un solo archivo de texto.
    """
    # Usar la patente como identificador único, o el índice si no hay patente
    vehicle_id = row['placa'] if pd.notna(row['placa']) else f"vehiculo_{row.name}"
    print(f"\n--- Procesando Vehículo ID: {vehicle_id} ---")
    
    # Crear directorios específicos para los PDFs de este auto
    vehicle_pdf_dir = os.path.join(PDF_DIR, vehicle_id)
    os.makedirs(vehicle_pdf_dir, exist_ok=True)

    try:
        # El campo 'informes_pdf' es un string, hay que cargarlo como JSON
        report_links = json.loads(row['informes_pdf'])
    except (json.JSONDecodeError, TypeError):
        print(f"  -> No se encontraron informes o el formato es inválido para {vehicle_id}.")
        return

    consolidated_text = ""
    
    # Iterar sobre cada informe (ej. "Certificado de Anotaciones", "Listado Vehículo")
    for report_name, url in report_links.items():
        if not url:
            continue
        
        sanitized_report_name = sanitize_filename(report_name)
        pdf_filename = f"{sanitized_report_name}.pdf"
        pdf_path = os.path.join(vehicle_pdf_dir, pdf_filename)
        
        # 1. Descargar el PDF
        try:
            print(f"  -> Descargando '{report_name}'...")
            response = requests.get(url, timeout=20)
            response.raise_for_status() # Lanza un error si la descarga falla
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
        except requests.exceptions.RequestException as e:
            print(f"  -> Falló la descarga de {url}: {e}")
            continue

        # 2. Convertir PDF a Texto
        report_text = pdf_to_text(pdf_path)

        # 3. Añadir al texto consolidado con separadores claros
        consolidated_text += f"--- INICIO {report_name.upper()} ---\n"
        consolidated_text += report_text
        consolidated_text += f"\n--- FIN {report_name.upper()} ---\n\n"

    # 4. Guardar el archivo de texto final consolidado
    if consolidated_text:
        output_txt_path = os.path.join(TXT_DIR, f"{vehicle_id}.txt")
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(consolidated_text)
        print(f"  -> ✅ Archivo de texto guardado en: {output_txt_path}")

# --- FUNCIÓN PRINCIPAL ---

def main():
    """Función principal que orquesta el proceso."""
    # Crear los directorios de salida si no existen
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(TXT_DIR, exist_ok=True)

    # Cargar los datos
    try:
        df_raw = pd.read_csv(RAW_DATA_PATH)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de datos en {RAW_DATA_PATH}")
        return

    # Procesar cada fila (vehículo) en el DataFrame
    # Para una prueba rápida, puedes usar df_raw.head(5) en lugar de df_raw
    for index, row in df_raw.iterrows():
        process_vehicle_reports(row)

    print("\nProceso completado.")


if __name__ == '__main__':
    main()