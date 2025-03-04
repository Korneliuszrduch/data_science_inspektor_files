import json
import base64
from pathlib import Path
from dotenv import dotenv_values
import streamlit as st
from openai import OpenAI
import instructor
from pydantic import BaseModel

# Załadowanie zmiennych środowiskowych
env = dotenv_values(".env")

# Ścieżki do katalogów
FILES_FOR_ANALISIS_PATH = Path("files_for_analysis")
ALL_FILES_AFTER_ANALISIS_PATH = FILES_FOR_ANALISIS_PATH / "all_files_after_analisis"
FILES_REJECTED_PATH = FILES_FOR_ANALISIS_PATH / "applications_rejected"
FILES_ACCEPT_PATH = FILES_FOR_ANALISIS_PATH / "applications_accept"
#file_path = FILES_FOR_ANALISIS_PATH / "wzor_fiszki_wypełniona.png"
file_path = FILES_FOR_ANALISIS_PATH / "wzor_fiszki_wypełniona1.png"


# Tworzenie katalogów, jeśli nie istnieją
for path in [FILES_FOR_ANALISIS_PATH, FILES_ACCEPT_PATH, FILES_REJECTED_PATH, ALL_FILES_AFTER_ANALISIS_PATH]:
    path.mkdir(exist_ok=True)


openai_client = OpenAI(api_key=env.get("OPENAI_API_KEY"))

# Obsługa klucza API w sesji
if "openai_api_key" not in st.session_state:
    api_key = env.get("OPENAI_API_KEY")
    if api_key:
        st.session_state["openai_api_key"] = api_key
    else:
        st.info("Dodaj swój klucz API OpenAI, aby móc korzystać z tej aplikacji")
        st.session_state["openai_api_key"] = st.text_input("Klucz API", type="password")
        if st.session_state["openai_api_key"]:
            st.rerun()

if not st.session_state.get("openai_api_key"):  
    st.stop()

st.success("Aplikacja gotowa do użycia")

def prepare_image_for_open_ai(file_path):
    """ Przygotowanie obrazu do wysłania do OpenAI """
    if not file_path.exists():
        st.error(f"Plik {file_path} nie istnieje.")
        return None
    
    with open(file_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    
    return f"data:image/png;base64,{image_data}"

if st.button("Weryfikuj nowe pliki"):
    st.write("Kliknięto przycisk")
    if file_path.exists():
        with open(file_path, "rb") as f:
            pdf_data = f.read()
        st.download_button(
            label="📥 Pobierz plik",
            data=pdf_data,
            file_name="wzor_fiszki_wypełniona.png",
            mime="application/png",
        )
    else:
        st.warning("Plik nie istnieje w katalogu files_for_analysis.")


if st.button("Przeanalizuj plik"):
    st.write("Kliknięto przycisk")
    
    if file_path.exists():
       
        info = instructor_openai_client = instructor.from_openai(openai_client)

        class ImageInfo(BaseModel):

            First_Name: str
            Surname: str
            Sex: str
            Email: str
            Phone: int
            Punkt_8: bool
            Punkt_9: bool
            Punkt_10: bool      
                            

        image_data = prepare_image_for_open_ai(file_path)
    
        if image_data:
            info = instructor_openai_client.chat.completions.create(
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
                                    "url": prepare_image_for_open_ai(file_path),
                                    "detail": "high"
                                },
                            },
                        ],
                    },
                ],
            )

            st.json(info.model_dump())
        else:
            st.warning("Nie udało się przygotować obrazu do analizy.")
    else:
        st.warning("Plik PDF nie istnieje.")
