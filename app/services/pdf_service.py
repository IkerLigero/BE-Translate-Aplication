import subprocess
import os
from pathlib import Path

def generate_translation_pdf_bytes(data: dict) -> bytes:
    
    # Route configuration
    current_dir = Path(__file__).parent
    templates_dir = current_dir.parent / "templates"
    
    template_name = "template.typ"
    output_filename = f"temp_result_{data['id']}.pdf"
    output_path = templates_dir / output_filename

    # Preparation of the command for Typst
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
        "--input", f"date={data['date']}"
    ]
    
    try:
        # Execution of Typst
        # The secret is 'cwd', which places Typst inside /app/templates
        # Runs the script.
        result = subprocess.run(
            command,
            cwd=str(templates_dir),
            capture_output=True,
            text=True,
            check=True
        )

        # Reading the generated PDF
        if not output_path.exists():
            raise Exception("Typst did not generate the output file.")

        with open(output_path, "rb") as f:
            pdf_bytes = f.read()

        # Automatic cleanup of the temporary file
        os.remove(output_path)

        return pdf_bytes

    except subprocess.CalledProcessError as e:
        # If Typst fails, capture the error for FastAPI log
        error_output = e.stderr if e.stderr else e.stdout
        print(f"--- CRITICAL TYPST ERROR ---\n{error_output}")
        raise Exception(f"Typst failed: {error_output}")
    except Exception as e:
        print(f"--- SYSTEM ERROR ---\n{str(e)}")
        raise e