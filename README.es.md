<h1 align="center">
<br>
<a href="https://sinapsis.tech/">
  <img
    src="https://github.com/Sinapsis-AI/brand-resources/blob/main/sinapsis_logo/4x/logo.png?raw=true"
    alt="" width="300">
</a>
<br>
Sinapsis
<br>
</h1>

<h4 align="center">Construye y administra flujos de trabajo de IA por medio de agentes modulares y escalables, basados en plantillas reutilizables y compuestas  </h4>

<p align="center">
<a href="#installation">🐍 Instalación</a> •
<a href="#quickstart">⚡ Inicio rápido</a> •
<a href="#features">🎯 Características</a> •
<a href="#examples">👀 Ejemplos</a> •
<a href="#docker">🐳 Imágenes de docker</a> •
<a href="#documentation">📙 Documentación</a> •
<a href="#packages">📚 Paquetes de sinapsis disponibles</a>
<a href="#license">🔍 Licencia</a>
</p>

<h4 align="center">
  <b>Te damos la bienvenida a Sinapsis.</b>

  La plataforma nativa de IA todo-en-uno, que integra las más poderosas e innovadoras herramientas de IA: visión por computadoras, procesamiento de lenguaje natural, IA generativa, procesamiento de habla, análisis de series de tiempo, y más. Ya sea que estés construyendo, experimentando o desarrollando, Sinapsis te permitirá crear flujos de trabajo integrados, desbloquear nuevas posibilidades y acelerar la innovación con IA como nunca antes. Únete a darle forma al futuro de la IA.
</h4>

<h2 id="installation">🐍 Instalación</h2>

> [!IMPORTANT]
> Sinapsis requiere Python 3.10 o posterior.
>

Recomendamos el uso de <code>uv</code>, aunque cualquier administrador de paquetes debería funcionar. Si necesitas instalar <code>uv</code>, por favor revisa la [documentación oficial](https://docs.astral.sh/uv/getting-started/installation/#installation-methods).



1. Instala usando tu administrador de paquetes de preferencia:

Ejemplo con <code>uv</code>:
```bash
  uv pip install sinapsis --extra-index-url https://pypi.sinapsis.tech
```
 O con <code>pip</code>:
```bash
  pip install sinapsis --extra-index-url https://pypi.sinapsis.tech
```


<h2 id="quickstart">⚡ Inicio rápido</h2>

<details>
<summary><strong><span style="font-size: 1.4em;">Uso de la interfaz de línea de comandos (CLI) </span></strong></summary>

La CLI de Sinapsis provee una manera fácil de ejecutar agentes y obtener información sobre las plantillas: 

```bash
# Ejecutar un agente con un archivo de configuración
sinapsis run config.yml

# Ejecutar un agente con perfilador
sinapsis run config.yml --enable-profiler

# Enlistar las plantillas disponibles
sinapsis info --all-template-names

# Obtener información detallada sobre una plantilla específica
sinapsis info --template NombreDeLaPlantilla

# Obtener un ejemplo de configuración de plantilla
sinapsis info --example-template-config NombreDeLaPlantilla

# Mostrar información de todas las plantillas
sinapsis info --all
```
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">📖 ¡Hola mundo! en Sinapsis</span></strong></summary>

**Crea un archivo de configuración llamado mi_agente_de_prueba.yml:**

```yaml
agent:
  name: mi_agente_de_prueba

templates:
- template_name: InputTemplate-1
  class_name: InputTemplate
  attributes: {}

- template_name: HelloWorld-1
  class_name: HelloWorld
  template_input: InputTemplate-1
  attributes:
    display_text: "¡Hola, esta es mi primera plantilla!"
```
También puedes probar con los agentes disponibles en el directorio <code>src/configs/</code>

**Ejecuta el agente:**
```bash
sinapsis run mi_agente_de_prueba.yml
```

**Resultado**

```console
... | DEBUG |  mi_agente_de_prueba:__instantiate_templates:105 - Initialized template: InputTemplate-1
... | DEBUG |  mi_agente_de_prueba:__instantiate_templates:105 - Initialized template: HelloWorld-1
... | DEBUG |  mi_agente_de_prueba:_log_agent_execution_order:119 - Execution Order
... | DEBUG |  mi_agente_de_prueba:_log_agent_execution_order:122 - Order: <<0>>, template name: <<InputTemplate-1>>
... | DEBUG |  mi_agente_de_prueba:_log_agent_execution_order:122 - Order: <<1>>, template name: <<HelloWorld-1>>
... | INFO |  mi_agente_de_prueba:_lazy_init:63 - Agent and templates initialized
... | INFO |  mi_agente_de_prueba:signal_block_if_needed:156 - Signaling block mode for HelloWorld-1 no: 2/2
... | INFO |  mi_agente_de_prueba:all_templates_finished:192 - All templates returned finished, stopping execution...
... | DEBUG | .../run_agent_from_config.py:run_agent_from_config:41 - result: DataContainer(container_id=abc..., images=[], audios=[], texts=[TextPacket(content='¡Hola, esta es mi primera plantilla!!', id='abc...', source='HelloWorld-1', modified_by_templates=['HelloWorld-1'], embedding=[], generic_data={}, annotations=None)], time_series=[], binary_data=[], generic_data={})

```
</details>

<h2 id="features">🎯 Características</h2>

<details>
<summary><strong><span style="font-size: 1.4em;">Agentes</span></strong></summary>

- Flujos de trabajo declarativos
- Múltiples modos de ejecución:
  - Generador
  - Ejecución única
  - Ejecución continua
- Organización de plantillas sofisticada:
  - Orden de ejecución topológico
  - Ejecución de plantillas en paralelo
  - Bloques de control de ejecución
- Capacidades de perfilado integradas:
  - Rastreo de tiempos de ejecución
- Manejo de estado:
  - Actualización de atributos dinámica
- Manejo de errores
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">Plantillas</span></strong></summary>

- Componentes independientes
- Ejecución modular centrada en tareas
- Evaluación estricta o perezosa
- Definiciones de plantillas dinámicas
- Plantillas compuestas
- Sub-agentes

</details>

<details>
<summary><strong><span style="font-size: 1.4em;">Contenedores de datos</span></strong></summary>

- Transporte universal de datos
- Diseño agnóstico de dominio
- Soporte nativo para imágenes, audio, texto, series de tiempo
- Datos multimodales

</details>

<details>
<summary><strong><span style="font-size: 1.4em;">General</span></strong></summary>

- Validación de datos y seguridad de tipos por medio de Pydantic
- Archivos de configuración basados en YAML
- Interfaz de línea de comandos
</details>

<h2 id="examples">👀 Ejemplos</h2>

Aquí puedes encontrar algunas implementaciones específicas de plantillas:

* **Plantillas estáticas**
  *  [Plantilla "Hola mundo"](src/sinapsis/templates/hello_world.py)
  * [Lectores de video](https://github.com/Sinapsis-ai/sinapsis-data-tools/tree/main/packages/sinapsis_data_readers)

* **Plantillas dinámicas**
  * [Sinapsis LangChain](https://github.com/Sinapsis-ai/sinapsis-langchain)



<details id="docker">
<summary><strong><span style="font-size: 1.4em;">🐳 Imágenes de docker</span></strong></summary>


Sinapsis provee imágenes de docker con todas las dependencias pre-configuradas. Cuando quieras usar docker para probar una aplicación dentro del proyecto, asegúrate de que las imágenes base de sinapsis están instaladas en el sistema. Para construir las imágenes:

1. **Clona el repositorio**:
 ```bash
git clone git@github.com:Sinapsis-ai/sinapsis.git
cd sinapsis
```

2. **Construye la imagen**
```bash
docker compose -f docker/compose.yaml build
```

Esto creará dos imágenes de docker:
- **sinapsis:base**: Contiene el administrador de paquetes <code>uv</code>, git con soporte de SSH y ambiente Python 3.10.
- **sinapsis-nvidia:base**: Igual que sinapsis-base, con soporte adicional para aceleración de GPU con CUDA 12.4.0.
</details>


<h2 id="documentation">📙 Documentación</h2>

La documentación se encuentra disponible en el [sitio web de sinapsis](https://docs.sinapsis.tech/docs)

Los tutoriales para distintos proyectos se encuentran disponibles en [el sitio de tutoriales de sinapsis](https://docs.sinapsis.tech/tutorials)

<h2 id="packages">📚 Paquetes de sinapsis disponibles</h2>

El sistema de sinapsis contiene una lista de paquetes públicos con plantillas que cubren un amplio rango de tareas, por ejemplo: visión de computadoras, series de tiempo, procesamiento de lenguaje natural, modelos de lenguaje (LLM), entre otros. Estos paquetes incluyen:

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis anomaly detection</span></strong></summary>

* [sinapsis-anomaly-detection](https://github.com/Sinapsis-ai/sinapsis-anomaly-detection)
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis chatbots</span></strong></summary>

* [sinapsis-chatbots](https://github.com/Sinapsis-ai/sinapsis-chatbots)
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis data tools</span></strong></summary>

* [sinapsis-data-tools](https://github.com/Sinapsis-ai/sinapsis-data-tools)
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis framework converter</span></strong></summary>

* [sinapsis-framework-converter](https://github.com/Sinapsis-ai/sinapsis-framework-comverter)
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis huggingface</span></strong></summary>

* [sinapsis-huggingface](https://github.com/Sinapsis-ai/sinapsis-huggingface)
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis image transforms</span></strong></summary>

* [sinapsis-image-transforms](https://github.com/Sinapsis-ai/sinapsis-image-transforms)
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis langchain</span></strong></summary>

* [sinapsis-langchain-readers](https://github.com/Sinapsis-ai/sinapsis-langchain)
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis ocr</span></strong></summary>

* [sinapsis-ocr](https://github.com/Sinapsis-ai/sinapsis-ocr)
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis object detection</span></strong></summary>

* [sinapsis-object-detection](https://github.com/Sinapsis-ai/sinapsis-object-detection)
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis openai</span></strong></summary>

* [sinapsis-openai](https://github.com/Sinapsis-ai/sinapsis-openai)
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis retina face trt</span></strong></summary>

* [sinapsis-retina-face-trt](https://github.com/Sinapsis-ai/sinapsis-retina-face-trt)
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis speech</span></strong></summary>

* [sinapsis-speech](https://github.com/Sinapsis-ai/sinapsis-speech)
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis time series</span></strong></summary>

* [sinapsis-time-series](https://github.com/Sinapsis-ai/sinapsis-time-series)
</details>

<details>
<summary><strong><span style="font-size: 1.4em;">sinapsis trackers</span></strong></summary>

* [sinapsis-trackers](https://github.com/Sinapsis-ai/sinapsis-trackers)
</details>

<h2 id="license">🔍 Licencia</h2>

Este proyecto está incluido bajo la licencia AGPLv3, que fomenta la colaboración abierta e intercambio. Para más detalles, favor de consultar el archivo de [licencia](LICENSE).
Para uso comercial, por favor consulta nuestro [sitio oficial](https://sinapsis.tech) para información sobre como conseguir una licencia comercial.



