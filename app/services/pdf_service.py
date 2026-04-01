import subprocess
import os
from pathlib import Path
from datetime import datetime, timedelta
from dateutil import parser

# This service generates a PDF file from the translation data using Typst and returns it as bytes.
def generate_translation_pdf_bytes(data: dict) -> bytes:
    
    # Define paths and command for Typst
    current_dir = Path(__file__).parent
    templates_dir = current_dir.parent / "templates"
    
    template_name = "template.typ"
    output_filename = f"temp_result_{data['id']}.pdf"
    output_path = templates_dir / output_filename
    raw_date = data.get('date')
    
    try:
        # If the date is a string, parse it; if it's already a datetime object, use it directly
        if isinstance(raw_date, str):
            dt_obj = parser.parse(raw_date)
        else:
            dt_obj = raw_date

        # Add one hour to the date (without asking)
        local_date = dt_obj + timedelta(hours=1)
        formatted_date = local_date.strftime("%d/%m/%Y %H:%M")
        
    except Exception as e:
        print(f"Error in date patch: {e}")
        formatted_date = str(raw_date) # If it fails, break the app

    # Build the command with all inputs as --input key=value
    command = [
        "typst", "compile", template_name, output_filename,
        "--input", f"id={data['id']}",
        "--input", f"source_lang={data['source_lang']}",
        "--input", f"target_lang={data['target_lang'].lower()}", 
        "--input", f"pdf_lang={data.get('pdf_lang', 'en')}", 
        "--input", f"original_text={data['original_text']}",
        "--input", f"translated_text={data.get('translated_text') or ''}",
        "--input", f"date={formatted_date}"
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