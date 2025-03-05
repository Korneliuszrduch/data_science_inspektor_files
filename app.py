
from pathlib import Path
from dotenv import dotenv_values
import streamlit as st
from openai import OpenAI
import json
import base64
import instructor
from pydantic import BaseModel
from pdf2image import convert_from_path
from PIL import Image

# Załadowanie zmiennych środowiskowych
env = dotenv_values(".env")

# Ścieżki do katalogów
FILES_FOR_ANALISIS_PATH = Path("files_for_analysis")
ALL_FILES_AFTER_ANALISIS_PATH = FILES_FOR_ANALISIS_PATH / "all_files_after_analisis"
FILES_REJECTED_PATH = FILES_FOR_ANALISIS_PATH / "applications_rejected"
FILES_ACCEPT_PATH = FILES_FOR_ANALISIS_PATH / "applications_accept"
pdf_path = FILES_FOR_ANALISIS_PATH / "wzor_fiszki_wypełniona.pdf"
output_path = FILES_FOR_ANALISIS_PATH / "plik_skonwertowany.png"

# Tworzenie katalogów, jeśli nie istnieją
for path in [FILES_FOR_ANALISIS_PATH, FILES_ACCEPT_PATH, FILES_REJECTED_PATH, ALL_FILES_AFTER_ANALISIS_PATH]:
    path.mkdir(exist_ok=True)

# Konfiguracja OpenAI API
api_key = env.get("OPENAI_API_KEY")
if not api_key:
    st.warning("Brak klucza API OpenAI w pliku .env")
openai_client = OpenAI(api_key=api_key)

# Obsługa klucza API w sesji
if "openai_api_key" not in st.session_state:
    st.session_state["openai_api_key"] = api_key or st.text_input("Klucz API", type="password")
    if st.session_state["openai_api_key"]:
        st.rerun()

if not st.session_state.get("openai_api_key"):
    st.stop()

st.success("Aplikacja gotowa do użycia")
st.write("Aplikacja do weryfikacji plików")


def convert_pdf_to_png(pdf_path, output_path):
    """ Konwersja PDF na jeden obraz PNG zawierający wszystkie strony """
    if not pdf_path.exists():
        st.error(f"Plik PDF {pdf_path} nie istnieje.")
        return None
    
    images = convert_from_path(pdf_path, dpi=300)
    if not images:
        st.error("Nie udało się przekonwertować PDF na obraz.")
        return None
    
    widths, heights = zip(*(img.size for img in images))
    total_width = max(widths)
    total_height = sum(heights)
    
    combined_image = Image.new('RGB', (total_width, total_height))
    y_offset = 0
    for img in images:
        combined_image.paste(img, (0, y_offset))
        y_offset += img.size[1]
    
    combined_image.save(output_path, format="PNG")
    return output_path


def prepare_image_for_open_ai(output_path):
    """ Przygotowanie obrazu do wysłania do OpenAI """
    if not output_path.exists():
        st.error(f"Plik {output_path} nie istnieje.")
        return None
    
    with open(output_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    return f"data:image/png;base64,{image_data}"




if st.button("Przekonweruj plik pdf do png"):
    result = convert_pdf_to_png(pdf_path, output_path)
    if result:
        st.success("Konwersja zakończona pomyślnie!")
        st.image(output_path, caption="Skonwertowany obraz", use_column_width=True)

if st.button("Weryfikuj nowe pliki"):
    if output_path.exists():
        with open(output_path, "rb") as f:
            png_data = f.read()
        st.download_button(
            label="📥 Pobierz plik",
            data=png_data,
            file_name="wzor_fiszki_wypełniona.png",
            mime="image/png",
        )
    else:
        st.warning("Plik nie istnieje w katalogu files_for_analysis.")
        
  
 


  
  
        
# class ImageInfo(BaseModel):
#             First_Name: str
#             Surname: str
#             Sex: str
#             Email: str
#             Phone: int
#             Punkt_8: bool
#             Punkt_9: bool
#             Punkt_10: bool
            
#instructor_openai_client = instructor.from_openai(openai_client)

if st.button("Przeanalizuj plik"):
    if output_path.exists():


       
            
            
        
        image_data = prepare_image_for_open_ai(output_path)
         
        if image_data:
            
           # info = instructor_openai_client = instructor.from_openai(openai_client)
           
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                response_model=ImageInfo,
                messages=[
                    {
                        "role": "user",
                       "content": [
                            {
                                "type": "text",
                                "text": "dla punktu 8 i 10 odpowiedz jest zaznaczona czarnym punktem w odległości około 3 mm obok tak lub nie",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": prepare_image_for_open_ai(output_path),
                                    "detail": "high"
                                },
                            },
                        ],
                    },
                ],
            )
            #st.write(ImageInfo)
            print(response.choices[0].message.content)

        else:
            st.warning("Nie udało się przygotować obrazu do analizy.")
    else:
        st.warning("Plik nie istnieje.")
