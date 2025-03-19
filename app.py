
from pdf2image import convert_from_path
from pathlib import Path
from dotenv import dotenv_values
import streamlit as st
from openai import OpenAI
import json
import base64
from pydantic import BaseModel

from PIL import Image
import instructor

# Załadowanie zmiennych środowiskowych
env = dotenv_values(".env")

# Ścieżki do katalogów
FILES_FOR_ANALISIS_PATH = Path("files_for_analysis")
ALL_FILES_AFTER_ANALISIS_PATH = FILES_FOR_ANALISIS_PATH / "all_files_after_analisis"
FILES_REJECTED_PATH = FILES_FOR_ANALISIS_PATH / "applications_rejected"
FILES_ACCEPT_PATH = FILES_FOR_ANALISIS_PATH / "applications_accept"
pdf_path = FILES_FOR_ANALISIS_PATH / "wzor_fiszki_wypełniona.pdf"
output_path = FILES_FOR_ANALISIS_PATH / "wzor_fiszki_wypełniona.png"
# output_path = FILES_FOR_ANALISIS_PATH / "wzor_fiszki_wypełniona1.png"
#output_path = FILES_FOR_ANALISIS_PATH / "fiszka.png"
#output_path = FILES_FOR_ANALISIS_PATH / "fiszka_justyna.png"

# Tworzenie katalogów, jeśli nie istnieją
for path in [FILES_FOR_ANALISIS_PATH, FILES_ACCEPT_PATH, FILES_REJECTED_PATH, ALL_FILES_AFTER_ANALISIS_PATH]:
    path.mkdir(exist_ok=True)

# Konfiguracja OpenAI API
# OpenAI API key protection
if not st.session_state.get("openai_api_key"):
    if "OPENAI_API_KEY" in env:
        st.session_state["openai_api_key"] = env["OPENAI_API_KEY"]

    else:
        st.info("Dodaj swój klucz API OpenAI aby móc korzystać z tej aplikacji")
        st.session_state["openai_api_key"] = st.text_input("Klucz API", type="password")
        if st.session_state["openai_api_key"]:
            st.rerun()

if not st.session_state.get("openai_api_key"):
    st.stop()

st.success("Aplikacja gotowa do użycia")
st.write("Aplikacja do weryfikacji plików")


def get_openai_client():
    return OpenAI(api_key=st.session_state["openai_api_key"])


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



class ImageInfo(BaseModel):

    First_Name: str
    Surname: str
    Email: str
    Sex: str
    Punkt_8: bool
    Punkt_9: bool
    Punkt_10: bool
    Punkt_14: bool
    Punkt_15: bool




openai_client = get_openai_client()
instructor_openai_client = instructor.from_openai(openai_client)


if st.button("Przeanalizuj plik") and 'instructor_openai_client' in locals():
    if output_path.exists():
      
       
       
            try:
                
                gas_bill = instructor_openai_client.chat.completions.create(
                    model="gpt-4o",
                    response_model=ImageInfo,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Proszę wyodrębnić imię, nazwisko, email, płeć oraz określić czy w punktach 8, 9, 10, 14 i 15 zaznaczono TAK czy NIE.",
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
                st.write(output_path)
                st.write(gas_bill)
           
            except Exception as e:
                st.error(f"Błąd podczas uzyskiwania odpowiedzi z OpenAI: {e}")
    else:
        st.warning("Plik nie istnieje w katalogu files_for_analysis.")