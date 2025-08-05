import tempfile
import subprocess
import os
import re
from mongo import fs
from typing import Union
from bson import ObjectId
from logica import generar_titulo_corto

#Escape robusto de caracteres LaTeX
def escapar_caracteres_latex(texto: str) -> str:
    reemplazos = {
        "\\": r"\textbackslash{}",
        "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
        "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for caracter, reemplazo in reemplazos.items():
        texto = texto.replace(caracter, reemplazo)

    texto = re.sub(r"(\d+),(\d+),(\d+)%", lambda m: f"{m.group(1)}.{m.group(2)}{m.group(3)}%", texto)
    return texto

#Validación previa del contenido LaTeX
def validar_contenido_latex(documento_latex: str,idioma: str = 'en') -> list:
    #Valida el contenido LaTeX considerando el idioma del documento
    errores = []
    config = obtener_config_idioma(idioma)


    contenido_match = re.search(
        rf"\\section\*\{{{config['seccion_contenido']}\}}(.*?)\\section\*\{{{config['seccion_enlaces']}\}}",
        documento_latex,
        re.DOTALL
    )
    if not contenido_match:
        errores.append("No se encontró la sección de contenido para validar.")
        return errores

    contenido = contenido_match.group(1).strip()

    if re.search(r"\d+,\d+,\d+%", contenido):
        errores.append("Porcentaje mal formateado (ej. 90,5,8%)")

    if contenido.count('"') % 2 != 0:
        errores.append("Comillas dobles sin cerrar")

    especiales = r"[#$%&_{}~^]"
    for match in re.finditer(especiales, contenido):
        pos = match.start()
        if pos == 0 or contenido[pos - 1] != "\\":
            errores.append(f" Carácter especial sin escapar: '{match.group()}' en posición {pos}")

    return errores

# Escape básico para URLs
def escapar_url(url: str) -> str:
    return url.replace("\\", "\\textbackslash{}").replace(" ", "%20")

# Mapeo de idiomas para LaTeX babel
def obtener_config_idioma(codigo_idioma: str) -> dict:
    #Retorna la configuración de babel y textos según el idioma detectado por Whisper

    configuraciones = {
        'es': {
            'babel': 'spanish',
            'seccion_contenido': 'Contenido',
            'seccion_enlaces': 'Contenido sugerido por gpt',
            'sin_enlaces': 'No se encontraron sugerencias relevantes.'
        },
        'en': {
            'babel': 'english',
            'seccion_contenido': 'Content',
            'seccion_enlaces': 'Gpt suggested content',
            'sin_enlaces': 'No relevant suggestions found.'
        }
    }

    config = configuraciones.get(codigo_idioma, configuraciones['en'])

    print(f"Validando secciones: '{config['seccion_contenido']}' y '{config['seccion_enlaces']}'")
    return config


#Generador de código LaTeX - MULTIIDIOMA
def generar_latex(titulo, texto_limpio, contenido_enriquecido=None, idioma='en'):
    texto_limpio = escapar_caracteres_latex(texto_limpio)
    titulo = escapar_caracteres_latex(titulo)
    
    #Obtener configuración del idioma
    config = obtener_config_idioma(idioma)
    
    print(f"Generando LaTeX en idioma: {idioma} (babel: {config['babel']})")

    #Contenido sugerido
    #Contenido sugerido
    if contenido_enriquecido:
        sugerencias = contenido_enriquecido.split("\n")  # Ajusta según cómo lo recibas
        contenido_sugerido = generar_itemize(sugerencias)
    else:
        contenido_sugerido = generar_itemize([])




    # PLANTILLA MULTIIDIOMA
    return f"""\\documentclass[12pt]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage[{config['babel']}]{{babel}}
\\usepackage{{lmodern}}
\\usepackage{{geometry}}
\\usepackage{{enumitem}}
\\usepackage{{url}}
\\usepackage[{config['babel']}]{{hyperref}}
\\geometry{{margin=2.5cm}}

\\title{{{titulo}}}
\\date{{}}

\\begin{{document}}

\\maketitle

\\section*{{{config['seccion_contenido']}}}
{texto_limpio}

\section*{{{config['seccion_enlaces']}}}
{contenido_sugerido}


\\end{{document}}"""

#Compilación en memoria con timeout AUMENTADO
def compilar_pdf_en_memoria(tex_code: str) -> Union[bytes, str]:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file_path = os.path.join(tmpdir, "document.tex")
            with open(tex_file_path, "w", encoding="utf-8") as f:
                f.write(tex_code)

            print(" Iniciando compilación LaTeX...")
            print(" Archivo TEX guardado en:", tex_file_path)

            # PRIMERA PASADA - compilación inicial
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "document.tex"],
                cwd=tmpdir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60  
            )

            if result.returncode != 0:
                print("Error al compilar LaTeX:")
                print("STDOUT:", result.stdout.decode('utf-8', errors='ignore'))
                print("STDERR:", result.stderr.decode('utf-8', errors='ignore'))
                return f"compilacion_fallida: {result.stderr.decode('utf-8', errors='ignore')}"

            pdf_path = os.path.join(tmpdir, "document.pdf")
            if not os.path.exists(pdf_path):
                print("Archivo PDF no generado")
                return "pdf_no_generado"
            
            if os.path.getsize(pdf_path) == 0:
                print("PDF generado está vacío")
                return "pdf_vacio"

            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
                print(f"PDF generado exitosamente. Tamaño: {len(pdf_bytes)} bytes")
                return pdf_bytes

    except subprocess.TimeoutExpired as e:
        print(f" LaTeX se quedó colgado tras {e.timeout} segundos")
        return f"compilacion_fallida: timeout tras {e.timeout} segundos"

    except Exception as e:
        print(" Error inesperado al compilar LaTeX:", str(e))
        return f"compilacion_fallida: {str(e)}"


#Guardar PDF en MongoDB
def guardar_pdf_en_mongo(pdf_bytes: bytes, metadata: dict) -> Union[str, ObjectId]:
    try:
        safe_metadata = {
            "titulo": metadata.get("titulo", "Sin título"),
            "fecha": metadata.get("fecha", "Sin fecha"),
            "texto_limpio": metadata.get("texto_limpio", ""),
            "idioma": metadata.get("idioma", "desconocido"),
            "contenido_enriquecido": metadata.get("contenido_enriquecido", "")
        }

        titulo_corto = generar_titulo_corto(metadata["titulo"])
        filename = f"{titulo_corto.replace(' ', '_')}_{metadata['fecha']}.pdf"

        print("Tamaño del PDF:", len(pdf_bytes))
        print("Nombre del archivo:", filename)
        print("Metadatos:", safe_metadata)

        file_id = fs.put(pdf_bytes, filename=filename, metadata={"origen": "flujo_transcripcion", **safe_metadata})
        print(f"PDF guardado en Mongo Atlas con ID: {file_id}")

        if fs.exists({"_id": file_id}):
            print(" Confirmado: PDF existe en Mongo")
            return str(file_id)
        else:
            print(" Error: PDF NO se encuentra en Mongo")
            return "no_encontrado"
    except Exception as e:
        print(" Error al guardar el PDF:", str(e))
        return "error"

#Flujo principal
def procesar_transcripcion(data: dict) -> str:
    contenido_enriquecido = data.get("contenido_enriquecido")
    idioma = data.get("idioma", "en")  # Idioma detectado por Whisper


    print(" Generando código LaTeX...")
    tex_code = generar_latex(
        titulo=data["titulo"],
        texto_limpio=data["texto_limpio"],
        contenido_enriquecido=contenido_enriquecido,
        idioma=idioma
    )

    print(" Código LaTeX generado:")
    print(tex_code)
    print("=" * 50)

    print(" Validando contenido LaTeX...")
    errores = validar_contenido_latex(tex_code,idioma)
    if errores:
        print("Errores detectados en el contenido LaTeX:")
        for err in errores:
            print(err)
        return "contenido_invalido"

    print("Compilando PDF...")
    pdf_bytes = compilar_pdf_en_memoria(tex_code)

    if isinstance(pdf_bytes, bytes):
        print(f" PDF en memoria generado. Tamaño: {len(pdf_bytes)} bytes")
        return guardar_pdf_en_mongo(pdf_bytes, data)
    print(f" Error en compilación: {pdf_bytes}")
    return "compilacion_fallida"


def generar_itemize(sugerencias: list[str]) -> str:
    if not sugerencias:
        return "\\textit{No se encontraron sugerencias relevantes.}"
    items = "\n".join([f"\\item {s}" for s in sugerencias])
    return f"\\begin{{itemize}}[leftmargin=*]\n{items}\n\\end{{itemize}}"
