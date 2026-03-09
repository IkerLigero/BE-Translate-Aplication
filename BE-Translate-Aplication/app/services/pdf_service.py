from fpdf import FPDF
import io

def generate_translation_pdf_bytes(data: dict) -> bytes:
    # 1. Crear el objeto PDF (A4, unidades en mm)
    pdf = FPDF()
    pdf.add_page()
    
    # 2. Configurar colores y fuentes (Arial es estándar en Windows)
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(44, 62, 80) # Gris oscuro profesional
    pdf.cell(100, 10, "TMS Report", ln=0)
    
    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(127, 140, 141) # Gris claro para el ID
    pdf.cell(0, 10, f"ID: {data['id']}", ln=1, align="R")
    
    # 3. Línea divisoria
    pdf.set_draw_color(189, 195, 199)
    pdf.line(10, 25, 200, 25)
    pdf.ln(10)
    
    # 4. Información de la traducción
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(30, 8, "Source:", ln=0)
    pdf.set_font("Arial", "", 11)
    pdf.cell(60, 8, str(data['source_lang']), ln=0)
    
    pdf.set_font("Arial", "B", 11)
    pdf.cell(30, 8, "Target:", ln=0)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, str(data['target_lang']), ln=1)
    
    pdf.set_font("Arial", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Generated on: {data['date']}", ln=1)
    pdf.ln(5)
    
    # 5. Bloque de Texto Original
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Original Text:", ln=1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, str(data['original_text']), border="T")
    pdf.ln(10)
    
    # 6. Bloque de Resultado (Gris claro)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Translated Result:", ln=1)
    pdf.set_fill_color(245, 245, 245) # Fondo gris suave
    pdf.set_font("Arial", "", 11)
    
    trans_text = str(data.get('translated_text') or "--- PENDIENTE DE TRADUCCIÓN ---")
    pdf.multi_cell(0, 8, trans_text, border=1, fill=True)
    
    # 7. Retornar bytes (FPDF2 devuelve bytes directamente con .output())
    return bytes(pdf.output())