# -*- coding: utf-8 -*-

"""
Script para procesar archivos de texto de patentes en lotes (batch) utilizando la API de OpenAI.

Este script realiza los siguientes pasos:
1.  Define y crea la estructura de carpetas para el proyecto.
2.  Carga un prompt desde un archivo externo.
3.  Lee archivos .txt desde la carpeta de entrada especificada.
4.  Asigna un ID único a cada tarea basado en el nombre del archivo de patente.
5.  Genera un archivo JSONL con todas las tareas y lo guarda en una carpeta de salida.
6.  Pide confirmación al usuario antes de enviar el lote a OpenAI.
7.  Sube el archivo JSONL y crea el trabajo de batch.
"""

# --- Parte 1: Configuración e Inicialización ---
import json
import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Carga variables de entorno (asegúrate de que tu .env esté en la raíz del proyecto)
load_dotenv()

# --- Configuración de Rutas del Proyecto ---
# El script está en 'src/inference/', así que subimos TRES niveles para llegar a la raíz del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Ruta al archivo que contiene el prompt del sistema.
prompt_file_path = PROJECT_ROOT / 'prompts' / 'prompt.txt'

# Carpeta de entrada para los archivos .txt de patentes.
input_folder_path = PROJECT_ROOT / 'reports' / 'txt_prompts'

# Carpeta de salida para guardar los archivos .jsonl que se envían a la API.
batch_json_folder_path = PROJECT_ROOT / 'data' / 'batch_json_generados'

# Carpeta de salida para los resultados procesados del batch (para un script posterior).
batch_output_folder_path = PROJECT_ROOT / 'data' / 'batch_output_procesados'

# --- Creación de Carpetas ---
# Asegura que todas las carpetas necesarias existan antes de empezar.
input_folder_path.mkdir(parents=True, exist_ok=True)
batch_json_folder_path.mkdir(parents=True, exist_ok=True)
batch_output_folder_path.mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / 'prompts').mkdir(parents=True, exist_ok=True)

# --- Configuración del Proceso ---
# Define el tamaño máximo de cada trozo de texto para no exceder el límite de tokens.
chunk_size = 5000

# --- Funciones Auxiliares ---
def load_prompt_from_file(filename: Path) -> str:
    """Carga el prompt desde una ruta específica."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error CRÍTICO: El archivo de prompt '{filename}' no se encontró.")
        raise
    except Exception as e:
        print(f"Error CRÍTICO al leer el archivo de prompt '{filename}': {e}")
        raise

def split_text_in_chunks(texto: str, tamano_chunk: int) -> list:
    """Divide un texto largo en fragmentos más pequeños."""
    return [texto[i:i+tamano_chunk] for i in range(0, len(texto), tamano_chunk)]

# --- Inicialización del Cliente y Carga del Prompt ---
try:
    client = OpenAI()
    print("✅ Cliente de OpenAI inicializado correctamente.")
except Exception as e:
    print(f"Error CRÍTICO al inicializar el cliente de OpenAI: {e}")
    raise

final_system_prompt = load_prompt_from_file(prompt_file_path)
print("✅ Prompt del sistema cargado correctamente.")

# --- Parte 2: Generación de Tareas para el Batch ---
print("\nIniciando la generación de tareas para el batch...")
batch_tasks_list = []

archivos_txt = list(input_folder_path.glob('*.txt'))

if not archivos_txt:
    print(f"⚠️ ADVERTENCIA: No se encontraron archivos .txt en la carpeta '{input_folder_path}'.")
else:
    print(f"Procesando {len(archivos_txt)} archivos desde: '{input_folder_path}'")
    for txt_file in archivos_txt:
        try:
            # Intenta leer el archivo con codificación UTF-8.
            texto = txt_file.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Si falla, intenta con cp1252, común en sistemas Windows.
            try:
                texto = txt_file.read_text(encoding='cp1252')
            except Exception as e:
                print(f"Error al leer el archivo {txt_file.name}: {e}. Saltando archivo.")
                continue
        except Exception as e:
            print(f"Error inesperado con el archivo {txt_file.name}: {e}. Saltando archivo.")
            continue

        # Divide el texto en chunks si es necesario.
        chunks = split_text_in_chunks(texto, chunk_size) if len(texto) > chunk_size else [texto]

        # Genera una tarea por cada chunk, usando el nombre del archivo como ID base.
        for idx, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            # El custom_id ahora es la patente (nombre del archivo sin extensión).
            custom_id = f"{txt_file.stem}-{idx+1}"

            task_item = {
                "custom_id": custom_id,
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4.1-mini",
                    "temperature": 0.1,
                    "max_tokens": 4000,
                    "response_format": {"type": "json_object"}, # Para asegurar salida en JSON
                    "messages": [
                        {"role": "system", "content": final_system_prompt},
                        {"role": "user", "content": chunk}
                    ],
                }
            }
            batch_tasks_list.append(task_item)

print(f"\n✅ Generación de tareas completada.")
print(f"Número total de tareas generadas para el batch: {len(batch_tasks_list)}")

# --- Parte 3: Creación y Envío del Archivo Batch ---
if not batch_tasks_list:
    print("No se generaron tareas. El proceso de batch ha finalizado sin envío.")
else:
    # Confirmación del usuario antes de proceder.
    user_confirmation_envio = input(f"Se han generado {len(batch_tasks_list)} tareas. ¿Deseas proceder con el envío del batch a OpenAI? (s/N): ")

    if user_confirmation_envio.lower() != 's':
        print("Envío del batch cancelado por el usuario.")
    else:
        print("\nProcediendo con la creación del archivo batch y envío a OpenAI...")

        # Genera un nombre de archivo único con timestamp.
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        batch_input_filename = f"batch_input_{timestamp}.jsonl"
        batch_input_filepath = batch_json_folder_path / batch_input_filename

        # Convierte la lista de tareas a formato JSONL y guarda el archivo.
        try:
            with open(batch_input_filepath, 'w', encoding='utf-8') as f:
                for task in batch_tasks_list:
                    f.write(json.dumps(task) + '\n')
            print(f"✅ Archivo batch guardado en: '{batch_input_filepath}'")
        except Exception as e:
            print(f"Error CRÍTICO al guardar el archivo JSONL: {e}")
            raise

        # Procede a subir el archivo y crear el job.
        try:
            # Paso 1: Subir el archivo .jsonl a OpenAI.
            print(f"Subiendo archivo '{batch_input_filepath.name}' a OpenAI...")
            with open(batch_input_filepath, 'rb') as f:
                openai_batch_file_object = client.files.create(
                    file=f,
                    purpose="batch"
                )
            print(f"✅ Archivo subido a OpenAI con ID: {openai_batch_file_object.id}")

            # Paso 2: Crear el job de batch.
            print("Creando el job de batch en OpenAI...")
            openai_batch_job_object = client.batches.create(
                input_file_id=openai_batch_file_object.id,
                endpoint="/v1/chat/completions",
                completion_window="24h"
            )
            print(f"🚀 ¡Éxito! Job de batch enviado con ID: {openai_batch_job_object.id}")
            print("Puedes monitorear el estado en tu dashboard de OpenAI o usando la API.")

        except Exception as e:
            print(f"Error CRÍTICO durante el envío del batch a OpenAI: {e}")