<h1 align="center"><br/><a href="https://sinapsis.tech/"><img alt="" src="https://github.com/Sinapsis-AI/brand-resources/blob/main/sinapsis_logo/4x/logo.png?raw=true" width="300"/></a><br/>Sinapsis EasyOCR
<br/></h1>
<h4 align="center">Reconocimiento de caracteres ópticos basados en EasyOCR (OCR) para imágenes</h4>
<p align="center"><a href="#installation">🐍 Instalación</a> •
<a href="#features">🚀 Características</a> •
<a href="#usage">📚 Ejemplo de uso</a> •
<a href="#webapp">🌐 Aplicación web</a> •
<a href="#documentation">📙 Documentación</a> •
<a href="#license">🔍 Licencia</a>


<strong>Sinapsis EasyOCR</strong> proporciona una implementación potente y flexible para extraer texto de imágenes usando el motor EasyOCR. Permite a los usuarios configurar y ejecutar fácilmente tareas OCR con una configuración mínima.

<h2 id="installation">🐍 Instalación</h2>

Instala el administrador de paquetes de tu elección. Alentamos el uso de <code>uv</code>


Ejemplo con <code>uv</code>:



```bash
  uv pip install sinapsis-easyocr --extra-index-url https://pypi.sinapsis.tech
```

o con solo <code>pip</code>:

```bash
  pip install sinapsis-easyocr --extra-index-url https://pypi.sinapsis.tech
```

<blockquote>

[!IMPORTANT]
Las plantillas pueden requerir dependencias adicionales. Para el desarrollo, recomendamos instalar el paquete con todas las dependencias opcionales:

</blockquote>

con <code>uv</code>:

```bash
  uv pip install sinapsis-easyocr[all] --extra-index-url https://pypi.sinapsis.tech
```

o con solo <code>pip</code>:

```bash
  pip install sinapsis-easyocr[all] --extra-index-url https://pypi.sinapsis.tech
```

<blockquote>

[! TIP]
Usa el comando de CLI <code>sinapsis info --all-template-names</code> para mostrar una lista con todos los nombres disponibles de Plantillas instalados con Sinapsis OCR.

[! TIP]
Usa el comando de CLI <code>sinapsis info --example-template-config EasyOCR</code> para producir un ejemplo Configuración de agente para la plantilla EasyOCR.

</blockquote>
<h2 id="features">🚀 Características</h2><h3>Plantillas soportadas</h3>
Este módulo incluye una plantilla adaptada para el motor EasyOCR:
<ul>
<li><strong>EasyOCR</strong>: Extrae texto de imágenes usando EasyOCR, junto con sus cajas de fijación y puntajes de confianza.</li>
</ul>

<details><summary><strong><span style="font-size: 1.25em;">EasyOCR Atributos</span></strong></summary>
</details>

<ul>
<li><strong><code>reader_params</code></strong> Parámetros para la inicialización del lector EasyOCR. Por defecto es <code>{"lang_list": ["en"]}</code>.</li>

<li><strong><code>read_text_params</code></strong> (dicta, opcional): Parámetros para el método EasyOCR readtext. Por defecto es <code>None</code>.</li>

<li><strong><code>get_full_text</code></strong> (bool): Ya sea para guardar texto detectado en un TextPacket. Por defecto es <code>False</code>.</li>
</ul>

<h2 id="usage">📚 Ejemplo de uso</h2>

<details><summary><strong><span style="font-size: 1.4em;">EasyOCR Ejemplo</span></strong></summary>
</details>


```yaml
agent:
  name: easyocr_inference
  description: agent to run inference with EasyOCR, performs on images read, recognition and save

templates:
- template_name: InputTemplate
  class_name: InputTemplate
  attributes: {}

- template_name: FolderImageDatasetCV2
  class_name: FolderImageDatasetCV2
  template_input: InputTemplate
  attributes:
    data_dir: dataset/input

- template_name: EasyOCR
  class_name: EasyOCR
  template_input: FolderImageDatasetCV2
  attributes: {}

- template_name: BBoxDrawer
  class_name: BBoxDrawer
  template_input: EasyOCR
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
La aplicación web proporciona una interfaz sencilla para extraer texto de imágenes usando EasyOCR. Cargue su imagen, y la aplicación la procesará y mostrará el texto detectado con cajas de fijación.

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

[! TIP]
Por defecto, la aplicación web utiliza EasyOCR. No se necesita configuración adicional.

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
<strong>NOTA</strong>: La url puede ser diferente, comprobar la salida

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
uv pip install sinapsis-easyocr[all] --extra-index-url https://pypi.sinapsis.tech
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
