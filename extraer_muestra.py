import pdfplumber
import os

pdf_path = 'Listado_General_Definitivo_Zona_H_Ciclo_2026.pdf'

if not os.path.exists(pdf_path):
    print(f"❌ No se encontró el archivo '{pdf_path}' en la carpeta del proyecto.")
    print("Por favor, copiá el archivo PDF a: C:\\Proyectos\\SistemaConcursos\\")
else:
    try:
        with pdfplumber.open(pdf_path) as pdf:
            texto_muestra = ""
            # Extraemos las primeras 3 páginas
            for i in range(min(3, len(pdf.pages))):
                texto = pdf.pages[i].extract_text()
                if texto:
                    texto_muestra += f"\n--- PÁGINA {i+1} ---\n{texto}"
            
            # Guardamos la muestra completa
            with open('muestra_pdf.txt', 'w', encoding='utf-8') as f:
                f.write(texto_muestra)
                
            print("✅ Muestra guardada en: muestra_pdf.txt")
            print("\n" + "="*60)
            print("--- PRIMERAS 800 CARACTERES DE LA MUESTRA ---")
            print("="*60)
            print(texto_muestra[:800])
            print("\n" + "="*60)
            
    except Exception as e:
        print(f"❌ Error al leer el PDF: {e}")
