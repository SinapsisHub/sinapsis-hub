<h1 align="center"><br/><a href="https://sinapsis.tech/"><img alt="" src="https://github.com/Sinapsis-AI/brand-resources/blob/main/sinapsis_logo/4x/logo.png?raw=true" width="300"/></a><br/>Sinapsis DocTR
<br/></h1>
<h4 align="center">Reconocimiento de caracteres ópticos basados en DocTR (OCR) para imágenes</h4>
<p align="center"><a href="#installation">🐍 Instalación</a> •
<a href="#features">🚀 Características</a> •
<a href="#usage">📚 Ejemplo de uso</a> •
<a href="#webapp">🌐 Aplicación web</a> •
<a href="#documentation">📙 Documentación</a> •
<a href="#license">🔍 Licencia</a>


<strong>Sinapsis DocTR</strong> proporciona una implementación potente y flexible para extraer texto de imágenes usando el motor DocTR OCR. Permite a los usuarios configurar y ejecutar fácilmente tareas OCR con una configuración mínima.

<h2 id="installation">🐍 Instalación</h2>

Instala el administrador de paquetes de tu elección. Alentamos el uso de <code>uv</code>


Ejemplo con <code>uv</code>:



```bash
  uv pip install sinapsis-doctr --extra-index-url https://pypi.sinapsis.tech
```

o con solo <code>pip</code>:

```bash
  pip install sinapsis-doctr --extra-index-url https://pypi.sinapsis.tech
```

<blockquote>

[!IMPORTANT]
Las plantillas pueden requerir dependencias adicionales. Para el desarrollo, recomendamos instalar el paquete con todas las dependencias opcionales:

</blockquote>

con <code>uv</code>:

```bash
  uv pip install sinapsis-doctr[all] --extra-index-url https://pypi.sinapsis.tech
```

o con solo <code>pip</code>:

```bash
  pip install sinapsis-doctr[all] --extra-index-url https://pypi.sinapsis.tech
```

<blockquote>

[! TIP]
Usa el comando de CLI <code>sinapsis info --all-template-names</code> para mostrar una lista con todos los nombres disponibles de Plantillas instalados con Sinapsis OCR.

[! TIP]
Usa el comando de CLI <code>sinapsis info --example-template-config DocTROCRPrediction</code> para producir un ejemplo Agente config para la plantilla de DocTROCRPrediction.

</blockquote>
<h2 id="features">🚀 Características</h2><h3>Plantillas soportadas</h3>
Este módulo incluye una plantilla adaptada para el motor DocTR OCR:
<ul>
<li><strong>DocTROCRPrediction</strong>: Utiliza el modelo OCR de DocTR para extraer texto, cajas atadas y puntajes de confianza de imágenes.</li>
</ul>

<details><summary><strong><span style="font-size: 1.25em;">DocTROCRPrediction Attributes</span></strong></summary>
</details>

<ul>
<li><strong><code>recognized_characters_as_labels</code></strong> (bool): Ya sea para usar caracteres reconocidos como etiquetas. Por defecto es <code>False</code>.</li>

<li><strong><code>artefact_type_as_labels</code></strong> (bool): Ya sea para usar el tipo de artefacto como etiquetas. Por defecto es <code>False</code>.</li>

<li><strong><code>det_arch</code></strong> (str): Arquitectura de detección para usar. Por defecto es <code>"fast_base"</code>.</li>

<li><strong><code>reco_arch</code></strong> (str): Recognition architecture to use. Por defecto es <code>"crnn_vgg16_bn"</code>.</li>

<li><strong><code>pretrained</code></strong> (bool): Ya sea para usar modelos preentrenados. Por defecto es <code>True</code>.</li>

<li><strong><code>pretrained_backbone</code></strong> Ya sea para usar la columna vertebral preentrenada. Por defecto es ¨C22C.</li>

<li><strong>¨C23C</strong> (bool): Ya sea para asumir páginas son rectas. Por defecto es ¨C24C.</li>

<li><strong>¨C25C</strong> (bool): Ya sea para preservar la relación de aspecto. Por defecto es ¨C26C.</li>

<li><strong>¨C27C</strong> (bool): Ya sea para usar relleno simétrico. Por defecto es ¨C28C.</li>

<li><strong>¨C29C</strong> (bool): Ya sea exportar como cajas rectas. Por defecto es ¨C30C.</li>

<li><strong>¨C31C</strong> Ya sea para detectar la orientación. Por defecto es ¨C32C.</li>

<li><strong>¨C33C</strong> Ya sea para aclarar páginas. Por defecto es ¨C34C.</li>

<li><strong>¨C35C</strong> Ya sea para detectar el lenguaje. Por defecto es ¨C36C.</li>
</ul>

<h2 id="usage">📚 Ejemplo de uso</h2>

<details><summary><strong><span style="font-size: 1.4em;">DocTR Ejemplo</span></strong></summary>
</details>


```yaml
agent:
  name: doctr_prediction
  description: agent to run inference with DocTR, performs on images read, recognition and save

templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}

- template_name: FolderImageDatasetCV2
  class_name: FolderImageDatasetCV2
  template_input: InputTemplate
  attributes:
    data_dir: dataset/input

- template_name: DocTROCRPrediction
  class_name: DocTROCRPrediction
  template_input: FolderImageDatasetCV2
  attributes:
    recognized_characters_as_labels: True

- template_name: BBoxDrawer
  class_name: BBoxDrawer
  template_input: DocTROCRPrediction
  attributes:
    draw_confidence: True
    draw_extra_labels: True

- template_name: ImageSaver
  class_name: ImageSaver
  template_input: BBoxDrawer
  attributes:
    save_dir: output
    root_dir: dataset
```



Para correr, simplemente usa:

```bash
sinapsis run name_of_the_config.yml
```
<h2 id="webapp">🌐 Aplicación web</h2>
La aplicación web proporciona una interfaz sencilla para extraer texto de imágenes usando DocTR OCR. Cargue su imagen, y la aplicación la procesará y mostrará el texto detectado con cajas de fijación.

<blockquote>

[!IMPORTANT]
Para ejecutar la aplicación primero necesitas clonar el repositorio sinapsis-ocr:

</blockquote>

```bash
git clone https://github.com/Sinapsis-ai/sinapsis-ocr.git
cd sinapsis-ocr
```

<blockquote>

[!NOTE]
Si desea habilitar el intercambio de aplicaciones externas en Gradio, <code>export GRADIO_SHARE_APP=True</code>

[!IMPORTANT]
Para utilizar DocTR en la aplicación web, establece la variable ambiente:
 <code>AGENT_CONFIG_PATH=/app/packages/sinapsis_doctr/src/sinapsis_doctr/configs/doctr_demo.yaml</code>

</blockquote>


<details><summary id="docker"><strong><span style="font-size: 1.4em;">🐳 Docker</span></strong></summary>
</details>


<strong>IMPORTANTE</strong> Esta imagen del docker depende de la sinapsis: imagen de fondo. Por favor consulta el sitio web oficial de  <a href="https://github.com/Sinapsis-ai/sinapsis?tab=readme-ov-file#docker">sinapsis</a> para instrucciones sobre construir con Docker.
<ol>
<li><strong>Construir la imagen sinapsis-ocr</strong>:</li>
</ol>

```bash
docker compose -f docker/compose.yaml build
```
<ol start="2">
<li><strong>Iniciar el contenedor de aplicaciones</strong>:</li>
</ol>

```bash
docker compose -f docker/compose_app.yaml up
```
<ol start="3">
<li><strong>Compruebe el estado</strong>:</li>
</ol>

```bash
docker logs -f sinapsis-ocr-app
```
<ol start="4">
<li>Los registros mostrarán la URL para acceder a la aplicación web, por ejemplo:</li>
</ol>
<strong>NOTA</strong>: La url puede ser diferente, comprobar la salida de los registros

```bash
Running on local URL:  http://127.0.0.1:7860
```
<ol start="5">
<li>Para detener la aplicación:</li>
</ol>

```bash
docker compose -f docker/compose_app.yaml down
```




<details><summary id="uv"><strong><span style="font-size: 1.4em;">💻 UV</span></strong></summary>
</details>


Para ejecutar la aplicación web utilizando <code>uv</code> administrador de paquetes, por favor:
<ol>
<li><strong>Crear el entorno virtual y sincronizar las dependencias</strong>:</li>
</ol>

```bash
uv sync --frozen
```
<ol start="2">
<li><strong>Instalar paquetes</strong>:</li>
</ol>

```bash
uv pip install sinapsis-doctr[all] --extra-index-url https://pypi.sinapsis.tech
```
<ol start="3">
<li><strong>Ejecute la aplicación web</strong>:</li>
</ol>

```bash
uv run webapps/gradio_ocr.py
```
<ol start="4">
<li><strong>El terminal mostrará la URL para acceder a la aplicación web, por ejemplo.</strong>:</li>
</ol>

```bash
Running on local URL:  http://127.0.0.1:7860
```

NOTA: La url puede ser diferente, comprobar la salida de la terminal
<ol start="5">
<li>Para detener la aplicación pulse <code>Control + C</code> en el terminal</li>
</ol>

<h2 id="documentation">📙 Documentación</h2>
La documentación para este y otros paquetes de sinapsis está disponible en <a href="https://docs.sinapsis.tech/docs">web de sinapsis</a>

Los tutoriales para diferentes proyectos dentro de sinapsis están disponibles en <a href="https://docs.sinapsis.tech/tutorials">sinapsis tutoriales página</a>
<h2 id="license">🔍 Licencia</h2>
Este proyecto está licenciado bajo la licencia AGPLv3, que fomenta la colaboración abierta y el intercambio. Para más detalles, consulta el archivo <a href="LICENSE">LICENSE</a>.

Para uso comercial, consulta el  <a href="https://sinapsis.tech"> sitio web oficial de Sinapsis</a> para información sobre la obtención de una licencia comercial.
