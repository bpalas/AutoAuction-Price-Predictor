import pandas as pd
import numpy as np
import os
import re
import json

# --- CONFIGURACIÓN DE RUTAS ---
# CAMBIO: Se actualizan las rutas para el nuevo archivo y el nuevo destino.
INPUT_PATH = os.path.join('data', 'processed', 'karcal_data_processed.csv')
OUTPUT_DIR = os.path.join('data', 'clean') # Directorio para datos listos para ML
OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'karcal_data_cleaned.csv')

# --- FUNCIONES DE LIMPIEZA ROBUSTAS ---

def limpiar_valor_monetario(valor):
    """Extrae solo los dígitos de un string monetario o de texto."""
    if isinstance(valor, str):
        # re.sub(r'[^\d]', '', valor) -> Elimina todo lo que NO sea un dígito
        numeros = re.sub(r'[^\d]', '', valor)
        return pd.to_numeric(numeros, errors='coerce')
    return pd.to_numeric(valor, errors='coerce')

def limpiar_booleano(valor):
    """Convierte valores de texto ('True', 'False') o booleanos a 1 o 0."""
    if isinstance(valor, str):
        if valor.lower() == 'true':
            return 1
        elif valor.lower() == 'false':
            return 0
    elif isinstance(valor, bool):
        return int(valor)
    return 0 # Asumir 0 (Falso) para valores nulos o no reconocidos

def contar_pujas(json_str):
    """Extrae el número de pujas desde el string JSON."""
    if isinstance(json_str, str):
        try:
            # Carga el JSON y cuenta los elementos en la lista
            return len(json.loads(json_str))
        except (json.JSONDecodeError, TypeError):
            return 0
    return 0

# --- SCRIPT PRINCIPAL DE LIMPIEZA ---

print("Iniciando el script de limpieza para Machine Learning...")

# 1. Cargar datos procesados
try:
    df = pd.read_csv(INPUT_PATH)
    print(f"Cargado exitosamente: {INPUT_PATH}")
except FileNotFoundError:
    print(f"Error: No se encontró el archivo {INPUT_PATH}. Asegúrate de que el archivo exista.")
    exit()

# 2. Renombrar columnas para facilitar el manejo (opcional pero recomendado)
# Nombres largos y con caracteres especiales pueden ser problemáticos
df.rename(columns={
    'estado_legal_y_documentacion_limitaciones_dominio_activas': 'limitaciones_dominio',
    'estado_legal_y_documentacion_permiso_circulacion_vigente': 'permiso_circulacion_vigente',
    'estado_legal_y_documentacion_revision_tecnica_vigente': 'revision_tecnica_vigente',
    'historial_propiedad_numero_propietarios': 'numero_propietarios',
    'historial_propiedad_meses_dueño_actual': 'meses_dueño_actual',
    'multas_y_costos_directos_tiene_multas_anotadas': 'tiene_multas',
    'multas_y_costos_directos_monto_total_multas_utm': 'monto_multas_utm',
    'condicion_fisica_y_riesgos_funciona': 'funciona',
    'condicion_fisica_y_riesgos_tiene_llaves': 'tiene_llaves',
    'condicion_fisica_y_riesgos_es_chatarra': 'es_chatarra'
}, inplace=True)


# 3. Aplicar limpieza a columnas clave
print("Limpiando y transformando columnas...")

# Columnas monetarias y numéricas con texto
df['oferta_ganadora'] = df['oferta_ganadora'].apply(limpiar_valor_monetario)
df['valor_inicial'] = df['valor_inicial'].apply(limpiar_valor_monetario)
df['kilometraje'] = df['kilometraje'].apply(limpiar_valor_monetario)
df['cilindrada'] = df['cilindrada'].apply(limpiar_valor_monetario)
df['visitas'] = df['visitas'].apply(limpiar_valor_monetario)

# Columnas booleanas (convertir a 1/0)
bool_cols = ['limitaciones_dominio', 'permiso_circulacion_vigente', 'revision_tecnica_vigente', 
             'tiene_multas', 'funciona', 'tiene_llaves', 'es_chatarra']
for col in bool_cols:
    if col in df.columns:
        df[col] = df[col].apply(limpiar_booleano)

# Columnas de texto (estandarizar)
df['transmisión'] = df['transmisión'].str.upper().str.strip()
df['combustible'] = df['combustible'].str.upper().str.strip()
df['tracción'] = df['tracción'].str.upper().str.strip()

# Conversiones numéricas directas
df['año'] = pd.to_numeric(df['año'], errors='coerce')
df['numero_propietarios'] = pd.to_numeric(df['numero_propietarios'], errors='coerce')
df['meses_dueño_actual'] = pd.to_numeric(df['meses_dueño_actual'], errors='coerce')
df['monto_multas_utm'] = pd.to_numeric(df['monto_multas_utm'], errors='coerce')


# 4. Ingeniería de Características (Feature Engineering)
print("Creando nuevas características...")
current_year = pd.Timestamp.now().year
df['antiguedad'] = current_year - df['año']
# Evitar división por cero si antiguedad es 0 (auto del año actual)
df['km_por_año'] = df['kilometraje'] / (df['antiguedad'] + 1)
df['numero_pujas'] = df['historial_ofertas'].apply(contar_pujas)
# Crear característica: ratio entre oferta ganadora y valor inicial
df['ratio_oferta_inicial'] = df['oferta_ganadora'] / df['valor_inicial']


# 5. Manejo de valores faltantes (NaN)
print("Manejando valores faltantes...")
# Eliminar filas donde el precio (objetivo) o el año son nulos
df.dropna(subset=['oferta_ganadora', 'año'], inplace=True)
# Convertir año a entero después de eliminar nulos
df['año'] = df['año'].astype(int)

# Imputación de valores faltantes
# Para km, usar la mediana del grupo por año. Luego la mediana global.
df['kilometraje'] = df.groupby('año')['kilometraje'].transform(lambda x: x.fillna(x.median()))
df['kilometraje'].fillna(df['kilometraje'].median(), inplace=True)
# Para otras numéricas, rellenar con la mediana es una opción segura
for col in ['cilindrada', 'visitas', 'numero_propietarios', 'meses_dueño_actual']:
    if col in df.columns:
        df[col].fillna(df[col].median(), inplace=True)
# Para multas, rellenar con 0 es lo más lógico (si no hay dato, no hay multa)
df['monto_multas_utm'].fillna(0, inplace=True)
# Rellenar km_por_año (si quedó algún nulo)
df['km_por_año'].fillna(df['km_por_año'].median(), inplace=True)


# 6. Seleccionar y reordenar columnas finales para el modelo
# Se eliminan columnas de texto libre, URLs, JSONs originales y fechas que no se usarán.
print("Seleccionando columnas finales para el modelo...")
columnas_modelo = [
    # ---- Variable Objetivo ----
    'oferta_ganadora',
    # ---- Features Principales ----
    'marca', 'modelo', 'año', 'antiguedad', 'kilometraje', 'km_por_año',
    'transmisión', 'combustible', 'cilindrada', 'tracción',
    # ---- Features de Subasta ----
    'valor_inicial', 'numero_pujas', 'visitas', 'ratio_oferta_inicial', 'mandante',
    # ---- Features de Condición e Historial ----
    'numero_propietarios', 'meses_dueño_actual', 'funciona', 'tiene_llaves',
    'es_chatarra',
    # ---- Features Legales y de Multas ----
    'limitaciones_dominio', 'permiso_circulacion_vigente', 'revision_tecnica_vigente',
    'tiene_multas', 'monto_multas_utm'
]

# Filtrar para evitar errores si alguna columna no existe en el dataframe
columnas_existentes = [col for col in columnas_modelo if col in df.columns]
df_final = df[columnas_existentes]


# 7. Guardar el DataFrame limpio
print("Guardando datos limpios...")
os.makedirs(OUTPUT_DIR, exist_ok=True) # Crea la carpeta /clean si no existe
df_final.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')

print(f"¡Limpieza completada! Archivo listo para ML guardado en: {OUTPUT_PATH}")
print(f"Dimensiones del dataframe final: {df_final.shape}")
print("\nPrimeras 5 filas del dataframe limpio:")
print(df_final.head())
