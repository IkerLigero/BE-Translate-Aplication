import typst

def generate_translation_pdf(data: dict, output_path: str):
    # Creamos el string de Typst pasando las variables
    content = f"""
    #import "app/templates/template.typ": translation_report
    
    #translation_report(
        id: "{data['id']}",
        source_lang: "{data['source_lang']}",
        target_lang: "{data['target_lang']}",
        original_text: "{data['original_text']}",
        translated_text: "{data['translated_text']}",
        date: "{data['date']}"
    )
    """
    
    # Compilamos directamente a PDF
    typst.compile(content, output=output_path)