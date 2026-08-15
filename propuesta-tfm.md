# Propuesta de TFM

## Objetivo

Diseñar y desarrollar un sistema de recomendación explicable de métodos de aprendizaje supervisado que, a partir de un formulario sobre las características del problema del usuario (tamaño y tipo de datos, naturaleza de la variable respuesta, necesidad de interpretabilidad, sospecha de no linealidad, etc.) y del dataset real aportado por este, sugiera el método más adecuado justificando la recomendación (bias-variance tradeoff, tabla comparativa de métodos de ISLR, flowchart de selección de modelos).

Esta justificación se apoyará en dos capas de visualización integradas en el propio flujo del recomendador:

- **Visualización exploratoria (EDA) del dataset del usuario**: distribuciones, correlaciones y outliers, que ayudan a motivar por qué se sugiere un método u otro (p. ej. detectar no linealidad o alta dimensionalidad antes de recomendar).
- **Visualización de resultados del modelo**: fronteras de decisión, residuos, importancia de variables o curvas ROC, tanto del método recomendado como de las alternativas que el usuario decida comparar.

Además, el sistema permitirá al usuario solicitar de forma interactiva el entrenamiento y comparación de métodos alternativos sobre su propio dataset, para contrastar visualmente y en métricas la recomendación inicial.

Como objetivo secundario, se validará empíricamente si las heurísticas didácticas en las que se basa el recomendador se sostienen frente al rendimiento real de los métodos sobre un benchmark de datasets, aportando así una contribución de investigación más allá de la propia herramienta.

## Estado del arte

### Herramientas de exploración/visualización de algoritmos ("playgrounds")

Existen varias herramientas interactivas orientadas a construir intuición sobre cómo se comportan distintos algoritmos de aprendizaje:

- **TensorFlow Playground** (playground.tensorflow.org): visualización en tiempo real del entrenamiento de redes neuronales, permitiendo configurar capas, neuronas, tasa de aprendizaje y regularización. Limitado a datasets sintéticos predefinidos (círculos, espirales, XOR); no admite la carga de datos propios sin modificar el código fuente.
- **Decision Boundary Playground** y **ML Algorithm Visualizer**: comparan visualmente regresión logística, SVM, KNN, árboles de decisión y k-means sobre datasets sintéticos, mostrando fronteras de decisión en tiempo real. Tampoco permiten cargar un dataset propio, solo datasets predefinidos o puntos añadidos manualmente.
- **Simple ML Playground** (dvtools.in): sí permite cargar un CSV propio, pero es una herramienta genérica sin ningún tipo de guía teórica ni justificación pedagógica de resultados.
- El ejemplo **"Classifier Comparison" de scikit-learn** es la referencia académica más citada para comparar visualmente distintos clasificadores, aunque es un notebook estático, no una herramienta interactiva.

En conjunto, estas herramientas cubren bien la construcción de intuición visual, pero ninguna combina la posibilidad de trabajar sobre datos reales del usuario con una explicación didáctica del comportamiento de cada método.

### Sistemas de recomendación de algoritmos (algorithm selection / meta-learning)

El problema de seleccionar automáticamente el algoritmo más adecuado para un problema dado ("algorithm selection problem") es un área de investigación activa dentro de AutoML y meta-learning:

- **Auto-WEKA**: selección conjunta de algoritmo e hiperparámetros mediante optimización bayesiana (SMAC), tratando la elección de modelo como un problema de optimización sobre una métrica de rendimiento.
- **AMLBID**: framework basado en meta-learning con una fase de aprendizaje (meta-características de datasets y rendimiento de 8 algoritmos sobre datasets históricos) y una fase de recomendación (sugiere pipeline e hiperparámetros para un dataset nuevo).
- Líneas de investigación más recientes (2022-2025) exploran distintas categorías de meta-características (estadísticas, information-theoretic, de complejidad, landmarking) para predecir qué algoritmo rendirá mejor en un dataset no visto, así como representaciones aprendidas de datasets (p. ej. TRIO, mediante embeddings de grafos) para mejorar la recomendación.

Estos sistemas sí trabajan sobre datasets reales y consiguen buen rendimiento predictivo, pero funcionan como cajas negras entrenadas sobre metadatos de rendimiento histórico: no ofrecen una justificación pedagógica de la recomendación en términos de los criterios teóricos que se enseñan en un curso de aprendizaje estadístico (sesgo-varianza, interpretabilidad vs. flexibilidad, supuestos del método), y no permiten al usuario cuestionar interactivamente la recomendación probando alternativas sobre su propio dataset.

### Gap identificado

No se ha encontrado ninguna herramienta que combine simultáneamente:

1. Una recomendación basada en las características del problema del usuario, justificada explícitamente con los criterios teóricos de un curso de aprendizaje estadístico (no solo en metadatos de rendimiento histórico).
2. La posibilidad de trabajar directamente sobre el dataset real aportado por el usuario, con visualización exploratoria y de resultados integrada.
3. Un modo interactivo de comparación, en el que el usuario pueda solicitar el entrenamiento de métodos alternativos sobre su propio dataset para contrastarlos con la recomendación inicial.

Este hueco constituye la motivación y el punto de partida de la propuesta de TFM.

## Metodología

1. **Selección de un benchmark de datasets** (p. ej. subconjunto de OpenML-CC18 o UCI) que cubra distintas combinaciones de características: tamaño de muestra (n pequeño/grande), dimensionalidad (p bajo/alto), linealidad esperada, nivel de ruido y tipo de variable respuesta (clasificación/regresión).
2. **Cálculo del rendimiento real de referencia**: para cada dataset del benchmark, entrenar y validar mediante cross-validation todos los métodos candidatos del temario de ISLR, obteniendo un ranking real de rendimiento por dataset.
3. **Evaluación del recomendador**: pasar las características de cada dataset por el formulario/recomendador basado en heurísticas de ISLR y comparar su sugerencia contra el ranking real obtenido en el paso anterior.
4. **Comparación contra baselines**: repetir la evaluación con una selección aleatoria de método como cota inferior y, opcionalmente, con un recomendador de meta-learning tipo AMLBID como cota superior, para poder situar el rendimiento del enfoque heurístico entre ambos.

La evaluación de la calidad pedagógica de las explicaciones generadas queda fuera del alcance de esta primera versión del TFM; se documentarán de forma cualitativa 2-3 casos de uso ilustrativos en la memoria, dejando una evaluación pedagógica más formal (rúbrica, panel de revisión) como línea de trabajo futuro.

## Métricas

- **Top-1 hit rate**: porcentaje de datasets en los que el método recomendado coincide con el mejor método real, admitiendo como acierto los que queden dentro de un margen razonable (p. ej. 1 desviación estándar del mejor resultado).
- **Regret**: diferencia de rendimiento entre el método recomendado y el mejor método real, para medir cuánto se pierde cuando la recomendación no es la óptima.
- **Correlación de ranking (Spearman)** entre el orden de métodos sugerido por el recomendador y el orden real de rendimiento obtenido en el benchmark.
