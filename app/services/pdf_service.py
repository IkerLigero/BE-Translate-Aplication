import subprocess
import os
from pathlib import Path
from datetime import datetime, timedelta
from dateutil import parser # Importante para leer el texto de la DB

def generate_translation_pdf_bytes(data: dict) -> bytes:
    current_dir = Path(__file__).parent
    templates_dir = current_dir.parent / "templates"
    
    template_name = "template.typ"
    output_filename = f"temp_result_{data['id']}.pdf"
    output_path = templates_dir / output_filename

    # --- EL PARCHE DE FUERZA BRUTA ---
    raw_date = data.get('date')
    
    try:
        # 1. Si es un string (lo más probable en el Worker), lo convertimos a objeto
        if isinstance(raw_date, str):
            dt_obj = parser.parse(raw_date)
        else:
            dt_obj = raw_date

        # 2. LE SUMAMOS LA HORA SÍ O SÍ (Sin preguntar)
        local_date = dt_obj + timedelta(hours=1)
        formatted_date = local_date.strftime("%d/%m/%Y %H:%M")
        
    except Exception as e:
        print(f"Error en el parche de fecha: {e}")
        formatted_date = str(raw_date) # Si falla, al menos que no rompa la app

    command = [
        "typst",
        "compile",
        template_name,
        output_filename,
        "--input", f"id={data['id']}",
        "--input", f"source_lang={data['source_lang']}",
        "--input", f"target_lang={data['target_lang'].lower()}",
        "--input", f"original_text={data['original_text']}",
        "--input", f"translated_text={data.get('translated_text') or ''}",
        "--input", f"date={formatted_date}" # <--- Aquí va la fecha con la hora sumada
    ]
    
    try:
        result = subprocess.run(
            command,
            cwd=str(templates_dir),
            capture_output=True,
            text=True,
            check=True
        )

        if not output_path.exists():
            raise Exception("Typst did not generate the output file.")

        with open(output_path, "rb") as f:
            pdf_bytes = f.read()

        os.remove(output_path)
        return pdf_bytes

    except subprocess.CalledProcessError as e:
        print(f"--- CRITICAL TYPST ERROR ---\n{e.stderr}")
        raise Exception(f"Typst failed: {e.stderr}")
    except Exception as e:
        print(f"--- SYSTEM ERROR ---\n{str(e)}")
        raise e