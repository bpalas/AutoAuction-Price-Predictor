
# Karcal Auto Auction Price Predictor 🚗

Este proyecto utiliza machine learning para predecir el precio final de vehículos en el sitio de subastas Karcal. A través de web scraping, se recolectaron y procesaron datos históricos de subastas para entrenar un modelo predictivo robusto.

El objetivo principal es no solo predecir precios con alta precisión, sino también entender qué factores del mercado (como marca, kilometraje y año) tienen el mayor impacto en el valor de un vehículo.

## 📂 Estructura del Proyecto

El repositorio está organizado de la siguiente manera para mantener un flujo de trabajo limpio y modular:

* **`data/`**: Contiene todos los conjuntos de datos del proyecto.
    * **`raw/`**: Almacena los datos brutos (`karcal_data_raw.csv`) obtenidos directamente del script de web scraping, sin ninguna modificación.
    * **`processed/`**: Guarda los datos limpios y procesados (`karcal_data_processed.csv`) que están listos para ser utilizados en el análisis y el modelado.

* **`notebooks/`**: Contiene los Jupyter Notebooks utilizados para el análisis exploratorio de datos (EDA), la visualización y el desarrollo inicial de modelos. El archivo principal es `1.0-EDA-and-Modeling.ipynb`.

* **`src/`**: Almacena todo el código fuente de Python en forma de scripts reutilizables.
    * **`scraping/`**: Incluye el script `scraper.py`, responsable de recolectar los datos desde karcal.cl.
    * **`processing/`**: Contiene el script `data_cleaner.py`, que toma los datos crudos, los limpia, transforma y guarda como datos procesados.

## 📊 Descripción de los Datos

Se manejan dos conjuntos de datos principales: los datos crudos y los procesados.

### Datos Crudos (`karcal_data_raw.csv`)

Estos son los datos tal como fueron extraídos del sitio web. Contienen toda la información disponible, incluyendo campos con formatos inconsistentes y datos complejos como JSON.

| Columna | Descripción |
| :--- | :--- |
| `marca`, `modelo`, `año` | Información básica del vehículo. |
| `oferta_ganadora` | El precio final como texto (ej. "$10.000.000"). |
| `kilometraje` | Kilometraje como texto, puede contener "NO REGISTRA". |
| `transmisión`, `combustible` | Detalles técnicos del vehículo. |
| `placa`, `tracción` | Información de registro y técnica. |
| `valor_inicial` | El precio de partida de la subasta como texto. |
| `detail_url`, `image_url`| Enlaces al detalle del producto y su imagen. |
| `historial_ofertas` | Un string en formato JSON con el detalle de todas las pujas. |
| `informes_pdf` | Un string en formato JSON con enlaces a los documentos PDF. |
| `visitas`, `mandante` | Conteo de visitas a la página y la entidad que vende el auto. |

### Datos Procesados (`karcal_data_processed.csv`)

Este es el conjunto de datos limpio, listo para el análisis. Las columnas han sido transformadas a formatos numéricos, se han manejado los valores faltantes y se han creado nuevas características predictivas.

| Columna | Descripción |
| :--- | :--- |
| `marca`, `modelo` | Identificadores del vehículo (texto). |
| `año` | Año de fabricación (numérico). |
| `antiguedad` | **(Nueva)** Años de antigüedad del vehículo (calculado). |
| `oferta_ganadora` | **(Variable Objetivo)** Precio final de venta (numérico). |
| `kilometraje` | Kilometraje del vehículo (numérico, valores nulos imputados). |
| `km_por_año` | **(Nueva)** Kilometraje promedio por año de antigüedad (numérico). |
| `transmisión`, `combustible` | Características técnicas (texto estandarizado). |
| `cilindrada`, `visitas` | Detalles técnicos y de popularidad (numérico). |
| `numero_pujas` | **(Nueva)** Cantidad total de ofertas recibidas (calculado desde JSON). |
| `valor_inicial` | Precio de partida de la subasta (numérico). |
| `mandante`, `placa` | Información adicional de la venta y del vehículo. |
| `detail_url`, `image_url`| URLs de referencia. |

## 📈 Conclusiones Preliminares

El análisis exploratorio de los datos procesados ha revelado varias tendencias clave en el mercado de subastas de Karcal:

1.  **Influencia de Antigüedad y Kilometraje:** Como era de esperar, la **antigüedad** y el **kilometraje** son dos de los factores con mayor impacto negativo en la `oferta_ganadora`. A medida que estos aumentan, el precio de venta tiende a disminuir de forma consistente.

2.  **Jerarquía de Marcas:** Existe una jerarquía de precios muy clara entre las **marcas**. Marcas premium como BMW, Mercedes-Benz o Audi tienen rangos de precios (mínimos, máximos y promedios) significativamente más altos que marcas de volumen como Chevrolet, Suzuki o Hyundai.

3.  **Impacto de la Transmisión:** Se observa una diferencia en el precio promedio de venta entre vehículos con transmisión **automática** y **mecánica**, siendo generalmente los automáticos más cotizados para modelos similares.

4.  **Popularidad como Indicador:** El número de **visitas** y, en especial, el **`numero_pujas`**, actúan como buenos indicadores del interés del mercado. Un alto número de pujas está correlacionado con precios de venta más altos, superando a menudo el valor inicial de forma significativa.

## 🚀 Próximos Pasos

* Optimizar los hiperparámetros del modelo de Machine Learning (`RandomForestRegressor`) para mejorar la precisión.
* Utilizar técnicas de XAI (como SHAP) para analizar en profundidad las predicciones individuales del modelo.
* Desarrollar una aplicación web simple con Streamlit o Flask para interactuar con el modelo y obtener predicciones en tiempo real.