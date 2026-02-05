import streamlit as st
from pypdf import PdfReader
import google.generativeai as genai

# --- API KEY ---
GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
# Ayarlar
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# --- SAYFA YAPISI ---
st.set_page_config(page_title="Akıllı Ders Asistanı", layout="wide")
st.title("🎓 Akıllı Ders Asistanı")

# --- HAFIZA (SESSION STATE) ---
# Eğer hafızada 'mesajlar' yoksa, boş bir liste oluştur.
if "messages" not in st.session_state:
    st.session_state.messages = []

# Eğer hafızada 'pdf_metni' yoksa, boş olarak başlat.
if "pdf_context" not in st.session_state:
    st.session_state.pdf_context = ""

# --- YAN MENÜ (SIDEBAR) ---
# Dosya yükleme işini sola alalım ki sohbet ekranı geniş olsun.
with st.sidebar:
    st.header("📂 Döküman Yükle")
    uploaded_file = st.file_uploader("Ders Notunu Seç (PDF)", type="pdf")
    
    # Dosya yüklendiğinde ve henüz işlenmediyse
    if uploaded_file and st.session_state.pdf_context == "":
        with st.spinner("PDF taranıyor..."):
            reader = PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            
            # Okunan metni hafızaya atıyoruz, artık unutmaz.
            st.session_state.pdf_context = text
            st.success(f"✅ Hazır! {len(text)} karakter okundu.")
            
    # Temizle butonu
    if st.button("Sohbeti Temizle"):
        st.session_state.messages = []
        st.rerun()

# --- SOHBET GEÇMİŞİNİ GÖSTER ---
# Hafızadaki her mesajı ekrana basıyoruz
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- KULLANICI GİRİŞİ ---
# Yeni 'chat_input' özelliği (WhatsApp gibi alt bar)
if prompt := st.chat_input("Sorunu yaz..."):
    
    # 1. Kullanıcı mesajını ekrana bas ve hafızaya ekle
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 2. Cevap üret
    if st.session_state.pdf_context:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Düşünüyor...")
            
            try:
                # Yapay Zekaya Gidecek Büyük Prompt
                # Hem PDF'i, hem eski konuşmaları, hem yeni soruyu birleştiriyoruz.
                
                gecmis_sohbet = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages])
                
                full_prompt = f"""
                Sen bir üniversite asistanısın. Aşağıdaki PDF içeriğine göre cevap ver.
                
                PDF İÇERİĞİ:
                {st.session_state.pdf_context}
                
                SOHBET GEÇMİŞİ:
                {gecmis_sohbet}
                
                YENİ SORU:
                {prompt}
                """
                
                response = model.generate_content(full_prompt)
                answer = response.text
                
                # Cevabı ekrana bas
                message_placeholder.markdown(answer)
                
                # Cevabı hafızaya ekle
                st.session_state.messages.append({"role": "assistant", "content": answer})
                
            except Exception as e:
                message_placeholder.error(f"Hata: {e}")
    else:
        st.warning("Lütfen önce sol menüden bir PDF yükleyin.")