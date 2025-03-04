import json
import pdfplumber
from pathlib import Path
from dotenv import dotenv_values
import streamlit as st
from openai import OpenAI

# Wczytanie zmiennych środowiskowych
env = dotenv_values(".env")

# Ścieżki do katalogów
FILES_FOR_ANALISIS_PATH = Path("files_for_analysis")
ALL_FILES_AFTER_ANALISIS_PATH = FILES_FOR_ANALISIS_PATH / "all_files_after_analisis"
FILES_REJECTED_PATH = FILES_FOR_ANALISIS_PATH / "applications_rejected"
FILES_ACCEPT_PATH = FILES_FOR_ANALISIS_PATH / "applications_accept"
file_path = FILES_FOR_ANALISIS_PATH / "wzor_fiszki_wypełniona2.pdf"

# Klient OpenAI
openai_client = OpenAI(api_key=env.get("OPENAI_API_KEY"))

if "openai_api_key" not in st.session_state:
    api_key = env.get("OPENAI_API_KEY")
    if api_key:
        st.session_state["openai_api_key"] = api_key
    else:
        st.info("Dodaj swój klucz API OpenAI, aby móc korzystać z tej aplikacji")
        st.session_state["openai_api_key"] = st.text_input("Klucz API", type="password")
        if st.session_state["openai_api_key"]:
            st.rerun()

if not st.session_state["openai_api_key"]:
    st.stop()

st.write("GOTOWI")

# Funkcja do wykrywania zaznaczonej opcji na podstawie checkboxów (obrazów)
def detect_selection_from_images(page, keyword_positions):
    detected = "Nie znaleziono"
    for img in page.images:
        img_x, img_y = img['x0'], img['y0']
        for keyword, (x_pos, y_pos) in keyword_positions.items():
            if abs(img_x - x_pos) < 10 and abs(img_y - y_pos) < 10:
                detected = keyword
    return detected

# Funkcja do ekstrakcji zaznaczonych opcji
def extract_selected_options_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        punkt_8_positions = {"tak": (110, 520), "nie": (110, 540)}
        punkt_10_positions = {"tak": (113, 750), "nie": (113, 730)}  # Poprawione współrzędne
        
        answer_8 = detect_selection_from_images(pdf.pages[0], punkt_8_positions)
        answer_10 = detect_selection_from_images(pdf.pages[1], punkt_10_positions)
    
    return {"Punkt 8": answer_8, "Punkt 10": answer_10}

# Tworzenie katalogów, jeśli nie istnieją
for path in [FILES_FOR_ANALISIS_PATH, FILES_ACCEPT_PATH, FILES_REJECTED_PATH, ALL_FILES_AFTER_ANALISIS_PATH]:
    path.mkdir(exist_ok=True)

if st.button("Weryfikuj nowe pliki"):
    st.write("Kliknięto przycisk")
    if file_path.exists():
        with open(file_path, "rb") as f:
            pdf_data = f.read()
        st.download_button(
            label="📥 Pobierz plik PDF",
            data=pdf_data,
            file_name="wzor_fiszki_wypełniona.pdf",
            mime="application/pdf",
        )
    else:
        st.warning("Plik nie istnieje w katalogu files_for_analysis.")

if st.button("Przeanalizuj plik"):
    st.write("Kliknięto przycisk")
    if file_path.exists():
        result = extract_selected_options_from_pdf(file_path)
        st.json(result)
    
        # Wysłanie wyników do OpenAI w celu analizy
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": f"Odpowiedzi w formularzu:\n{json.dumps(result, ensure_ascii=False)}"}
            ]
        )
        
        st.write("Odpowiedź OpenAI:")
        st.text(response.choices[0].message.content)
    else:
        st.warning("Plik PDF nie istnieje.")
