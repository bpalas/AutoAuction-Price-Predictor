
# Karcal Auto Auction Price Predictor 🚗

Este proyecto utiliza técnicas avanzadas de **Extracción de Información y Machine Learning** para predecir con alta precisión el precio final de vehículos en el sitio de subastas Karcal.

El núcleo de este proyecto fue un experimento para cuantificar el impacto de datos enriquecidos. Se comparó un modelo de Machine Learning entrenado con datos básicos (obtenidos por web scraping) contra un modelo entrenado con un conjunto de datos "enriquecido", donde se utilizó un **sistema avanzado de IA para extraer información detallada y estructurada desde documentos vehiculares no estructurados**, como el Certificado de Anotaciones Vigentes (CAV).

El resultado demostró que la calidad y profundidad de los datos es el factor más crítico para la precisión del modelo, logrando una **reducción del error de predicción superior al 99%**.

---

## 🔬 El Experimento: Modelo Básico vs. Modelo Enriquecido

Para medir el impacto de la extracción de datos detallada, se crearon dos conjuntos de datos y se entrenó un modelo `RandomForestRegressor` en cada uno.

### 1. Modelo Básico (Datos Limpios Básicos)
- **Fuente de Datos**: `data/clean/karcal_data_cleaned_raw.csv`
- **Procedimiento**: Este conjunto de datos se generó a partir del web scraping inicial. Contiene características estándar como marca, modelo, año y kilometraje, que fueron limpiadas y procesadas con métodos convencionales. Representa una base sólida pero limitada de información.

### 2. Modelo Enriquecido (Datos Extraídos con IA)
- **Fuente de Datos**: `data/clean/karcal_data_cleaned.csv`
- **Procedimiento**: Para crear este dataset, se utilizó un sistema de IA avanzado con un prompt específico para que actuara como un analista experto. El sistema recibió textos de documentos vehiculares chilenos (como el CAV y el listado de constancias) y extrajo información crucial que no está disponible de forma estructurada en el sitio web.

#### Prompt detallado de extracción de datos:

Usted es un sistema avanzado de análisis y extracción de datos, especializado en el procesamiento de documentos vehiculares chilenos.

Su principal función es analizar un conjunto de textos no estructurados que incluyen el **"Certificado de Anotaciones Vigentes (CAV)"** y el **"Listado Vehículo – Constancias"**, entre otros documentos de subastas, para un vehículo específico identificado por su patente.

Su objetivo es extraer con precisión la información solicitada y estructurarla en un único objeto JSON. La lógica de extracción debe seguir estrictamente las instrucciones detalladas para cada campo. Si un dato no se puede encontrar o deducir de los textos proporcionados, su valor en el JSON debe ser `null`.

La fecha actual a considerar para los cálculos de vigencia es **1 de agosto de 2025**.

Genere un nuevo objeto JSON que contenga la siguiente estructura y datos:

```json
{
  "estado_legal_y_documentacion": {
    "limitaciones_dominio_activas": "boolean", 
    "permiso_circulacion_vigente": "boolean", 
    "fecha_vencimiento_permiso_circulacion": "AAAA-MM-DD",
    "revision_tecnica_vigente": "boolean", 
    "fecha_vencimiento_revision_tecnica": "AAAA-MM-DD" 
  },
  "historial_propiedad": {
    "numero_propietarios": "integer", 
    "meses_dueño_actual": "integer" 
  },
  "multas_y_costos_directos": {
    "tiene_multas_anotadas": "boolean", 
    "monto_total_multas_utm": "float" 
  },
  "condicion_fisica_y_riesgos": {
    "funciona": "boolean", 
    "tiene_llaves": "boolean", 
    "observaciones_criticas": "[ string ]", 
    "es_chatarra": "boolean", 
    "grabado_patente_vidrios": "boolean" 
  }
}
````

**Instrucciones detalladas por campo:**

  - `limitaciones_dominio_activas`: Extraiga esta información de la sección "LIMITACIONES AL DOMINIO" del CAV. Será `true` si existen anotaciones vigentes, de lo contrario `false`.
  - `permiso_circulacion_vigente`: Deduzca la vigencia comparando la fecha de vencimiento del "Listado Vehículo – Constancias" con la fecha actual (1 de agosto de 2025).
  - `fecha_vencimiento_permiso_circulacion`: Extraiga la fecha exacta del "Listado Vehículo – Constancias".
  - `revision_tecnica_vigente`: Deduzca la vigencia comparando la fecha de vencimiento del "Listado Vehículo – Constancias" con la fecha actual (1 de agosto de 2025).
  - `fecha_vencimiento_revision_tecnica`: Extraiga la fecha exacta del "Listado Vehículo – Constancias".
  - `numero_propietarios`: Cuente el propietario actual y todos los "PROPIETARIOS ANTERIORES" listados en el CAV.
  - `meses_dueño_actual`: Calcule el número de meses transcurridos desde la "Fec. adquisición" del propietario actual en el CAV hasta la fecha actual (1 de agosto de 2025).
  - `tiene_multas_anotadas`: Será `true` si la columna "MULTAS" del "Listado Vehículo – Constancias" contiene un valor para el vehículo, de lo contrario `false`.
  - `monto_total_multas_utm`: Extraiga el valor numérico (puede ser flotante) de la columna "MULTAS". Si no hay multas, el valor debe ser 0.
  - `funciona`: Extraiga el estado de la columna "VEH. FUNCIONA" del "Listado". `true` si es "SI", `false` si es "NO".
  - `tiene_llaves`: Extraiga el estado de la columna "LLAVES" del "Listado". `true` si es "SI", `false` si es "NO".
  - `observaciones_criticas`: Extraiga cada una de las frases textuales de la columna "CONSTANCIAS" y agréguelas como elementos de una lista. Si no hay nada, la lista debe estar vacía.
  - `es_chatarra`: Será `true` si la palabra "CHATARRA" aparece en la columna "CONSTANCIAS", de lo contrario `false`.
  - `grabado_patente_vidrios`: Extraiga el estado de la columna "GRABADO DE PATENTE" del "Listado". `true` si es "SI", `false` si es "NO".

-----

## 📊 Análisis de Resultados

La comparación del rendimiento entre ambos modelos arrojó resultados concluyentes, demostrando el inmenso valor de los datos enriquecidos.

| Métrica | Modelo Básico (raw) | Modelo Enriquecido |
| :--- | :--- | :--- |
| **Error Absoluto Medio (MAE)** | "$1,316,000" | **$561** |
| **Coeficiente de Determinación (R²)**| 0.6737 | **1.0000** |

### Conclusiones del Experimento

1.  **Reducción Drástica del Error (MAE)**: El error promedio de predicción se redujo de **$1,316,000 a tan solo $561**. Esto implica que el modelo enriquecido es extraordinariamente más preciso, pasando de un error de más de un millón de pesos a uno prácticamente insignificante.

2.  **Precisión Explicativa Perfecta (R²)**: El R² saltó de **0.67 a 1.00**. Un R² de 0.67 indica que el modelo básico podía explicar el 67% de la variabilidad en los precios. En contraste, un R² de 1.00 significa que el modelo enriquecido puede explicar el **100% de la variabilidad del precio**, basándose en las características proporcionadas.

La conclusión es inequívoca: la información sobre la **condición real, el historial legal y administrativo del vehículo** no es solo información adicional, sino que son los predictores más potentes de su valor final en una subasta.

-----

## 📂 Estructura del Proyecto

El repositorio está organizado para reflejar el flujo de trabajo del experimento:

  * **`data/`**: Contiene todos los conjuntos de datos.
      * **`raw/`**: Datos brutos del web scraping.
      * **`processed/`**: Datos con el enriquecimiento de la IA, listos para modelado (`karcal_data_processed.csv`).
      * **`clean/`**: Almacena las dos versiones de datos utilizadas en la comparación: `karcal_data_cleaned_raw.csv` y `karcal_data_cleaned.csv`.
  * **`notebooks/`**: Jupyter Notebooks para EDA y los experimentos de modelado (`1.0-EDA-and-Modeling.ipynb`, `2.0-EDA-and-Modeling-Cleaned.ipynb`, `3.0-Model-Comparison.ipynb`).
  * **`src/`**: Código fuente modularizado para scraping y limpieza.

-----

## 🚀 Próximos Pasos

Este exitoso experimento abre la puerta a nuevas líneas de investigación y desarrollo:

  * **Expandir el Conjunto de Datos**: Aumentar el número de vehículos analizados para validar la robustez del modelo en un espectro más amplio del mercado.
  * **Experimentar con Knowledge Graphs**: Implementar grafos de conocimiento para modelar las relaciones entre entidades (vehículos, propietarios, multas, documentos). Esto podría descubrir patrones más complejos y generar características aún más potentes para modelos de ML y NLP.
  * **Explorar Nuevos Modelos**: Utilizar las características enriquecidas para entrenar modelos más avanzados, incluyendo arquitecturas de Deep Learning para el procesamiento de las "observaciones críticas" y otros textos no estructurados.
  * **Desarrollo de una API de Inferencia**: Crear un servicio que pueda recibir los documentos de un nuevo vehículo y entregar una predicción de precio en tiempo real.

<!-- end list -->

