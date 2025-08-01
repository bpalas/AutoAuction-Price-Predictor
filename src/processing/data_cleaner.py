import pandas as pd
import numpy as np
import os
import re
import json

# --- CONFIGURACIÓN DE RUTAS ---
# Lee desde la carpeta raw
INPUT_PATH = os.path.join('data', 'raw', 'karcal_data_raw.csv')
# Guarda en la carpeta processed
OUTPUT_DIR = os.path.join('data', 'clean')
OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'karcal_data_cleaned_raw.csv')

# --- FUNCIONES DE LIMPIEZA ROBUSTAS ---

def limpiar_valor_monetario(valor):
    """Extrae solo los dígitos de un string monetario."""
    if isinstance(valor, str):
        # re.sub(r'[^\d]', '', valor) -> Elimina todo lo que NO sea un dígito
        numeros = re.sub(r'[^\d]', '', valor)
        return pd.to_numeric(numeros, errors='coerce')
    return pd.to_numeric(valor, errors='coerce')

def limpiar_kilometraje(valor):
    """Convierte el kilometraje a número, manejando 'NO REGISTRA'."""
    if isinstance(valor, str):
        if 'no registra' in valor.lower():
            return np.nan # np.nan es la forma correcta de representar un valor faltante
        numeros = re.sub(r'[^\d]', '', valor)
        return pd.to_numeric(numeros, errors='coerce')
    return pd.to_numeric(valor, errors='coerce')
    
def contar_pujas(json_str):
    """Extrae el número de pujas desde el string JSON."""
    if isinstance(json_str, str):
        try:
            return len(json.loads(json_str))
        except (json.JSONDecodeError, TypeError):
            return 0
    return 0

# --- SCRIPT PRINCIPAL DE LIMPIEZA ---

print("Iniciando el script de limpieza...")

# 1. Cargar datos crudos
try:
    df = pd.read_csv(INPUT_PATH)
    print(f"Cargado exitosamente: {INPUT_PATH}")
except FileNotFoundError:
    print(f"Error: No se encontró el archivo {INPUT_PATH}. Asegúrate de ejecutar el scraper primero.")
    exit()

# 2. Aplicar limpieza
print("Limpiando columnas numéricas...")
df['oferta_ganadora'] = df['oferta_ganadora'].apply(limpiar_valor_monetario)
df['valor_inicial'] = df['valor_inicial'].apply(limpiar_valor_monetario)
df['kilometraje'] = df['kilometraje'].apply(limpiar_kilometraje)
df['cilindrada'] = df['cilindrada'].apply(lambda x: limpiar_valor_monetario(str(x)))
df['visitas'] = df['visitas'].apply(lambda x: limpiar_valor_monetario(str(x)))
df['año'] = pd.to_numeric(df['año'], errors='coerce')


# 3. Manejo de valores faltantes (NaN) creados en la limpieza
print("Manejando valores faltantes...")
# Eliminar filas donde el precio final (nuestro objetivo) es nulo
df.dropna(subset=['oferta_ganadora', 'año'], inplace=True)
# Rellenar kilometraje faltante con la mediana de su grupo por año
df['kilometraje'] = df.groupby('año')['kilometraje'].transform(lambda x: x.fillna(x.median()))
# Si aún quedan nulos (ej. un año con todos nulos), rellenar con la mediana global
df['kilometraje'].fillna(df['kilometraje'].median(), inplace=True)


# 4. Ingeniería de Características
print("Creando nuevas características (Feature Engineering)...")
current_year = 2025 # O pd.Timestamp.now().year
df['antiguedad'] = current_year - df['año']
df['km_por_año'] = df['kilometraje'] / (df['antiguedad'] + 1)
df['numero_pujas'] = df['historial_ofertas'].apply(contar_pujas)


# 5. Estandarizar columnas de texto (categóricas)
df['transmisión'] = df['transmisión'].str.upper().str.strip()
df['combustible'] = df['combustible'].str.upper().str.strip()


# 6. Seleccionar y reordenar columnas finales
columnas_finales = [
    'marca', 'modelo', 'año', 'antiguedad', 'oferta_ganadora', 'kilometraje', 
    'km_por_año', 'transmisión', 'combustible', 'cilindrada', 'visitas', 
    'numero_pujas', 'valor_inicial', 'mandante', 'placa', 
    'detail_url', 'image_url'
]
# Filtrar para evitar errores si alguna columna no existe
columnas_existentes = [col for col in columnas_finales if col in df.columns]
df_final = df[columnas_existentes]


# 7. Guardar el DataFrame limpio
print("Guardando datos limpios...")
os.makedirs(OUTPUT_DIR, exist_ok=True) # Crea la carpeta /processed si no existe
df_final.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')

print(f"¡Limpieza completada! Archivo guardado en: {OUTPUT_PATH}")