import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="ImpresaAI Pro", layout="centered")
st.title("📊 ImpresaAI Pro v2.0")
st.subheader("Il Consulente Strategico per la tua Azienda")

# Inizializzazione chiavi e client nella sessione del browser
if "openai_key" not in st.session_state:
    st.session_state.openai_key = ""

# Barra laterale protetta per l'inserimento della chiave API in totale sicurezza
with st.sidebar:
    st.header("⚙️ Configurazione")
    st.session_state.openai_key = st.text_input("Inserisci OpenAI API Key:", type="password")
    st.caption("La tua chiave viene gestita in sicurezza all'interno del tuo browser.")

# Blocco dell'applicazione se manca la chiave
if not st.session_state.openai_key:
    st.info("Per favore, inserisci la tua nuova OpenAI API Key nella barra laterale sinistra per iniziare.")
    st.stop()

# Inizializzazione del client OpenAI
client = OpenAI(api_key=st.session_state.openai_key)

# Il cuore del sistema: Il prompt ingegneristico basato su Macchina a Stati Finiti
SYSTEM_PROMPT = """
Tu sei "ImpresaAI Pro", un sistema di intelligenza artificiale per l'audit aziendale strutturato come una Macchina a Stati Finiti.
STATO 1: INPUT_COLLECTION
Se l'utente non ha ancora fornito i dati aziendali, richiedi questi parametri in modo chiaro ed esigi una risposta:
1. Settore (Cosa vende e a chi?)
2. Scala (Micro-attività, PMI o Grande Industria?)
3. Collo di Bottiglia (Qual è il problema principale?)
4. Budget (Zero, Basso o Strutturato?)

STATO 2: RUNTIME_PROMPT_TUNING
Una volta ricevuti i dati, adatta istantaneamente la tua semantica. Se l'utente è una micro-attività usa termini pratici e locali. Se è una grande industria usa metriche corporate (KPI, EBITDA, Supply Chain).
Genera sempre l'output in tre sezioni:
- 📊 [PROFILO ARCHITETTURA AZIENDALE]
- 📈 [STRATEGIA DI OTTIMIZZAZIONE] (In 3 step logici e sequenziali)
- 🛑 [FALL-BACK RISK] (Avviso brutale sull'errore operativo da evitare assolutamente)
"""

# Inizializzazione della memoria della chat
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Messaggio iniziale di sbarramento per bloccare risposte vaghe
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Benvenuto in ImpresaAI Pro. Per elaborare la tua strategia aziendale su misura, ho bisogno di mappare il tuo business.\n\nPer favore, indicami:\n1. Il tuo **settore** e cosa vendi\n2. La **dimensione** della tua azienda (Micro-attività, PMI, Grande industria)\n3. Il tuo **collo di bottiglia** (problema principale oggi)\n4. Il tuo **budget** (Zero, Basso, Strutturato)"
    })

# Mostra la cronologia dei messaggi a schermo (escludendo il prompt di sistema)
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# Gestione dell'invio dei messaggi da parte del cliente
if user_input := st.chat_input("Inserisci i dati della tua azienda qui..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
        
    # Chiamata in tempo reale ai server di OpenAI
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        # Generazione in streaming del testo (effetto macchina da scrivere)
        stream = client.chat.completions.create(
            model="gpt-4o-mini", # Modello ultra-veloce ed estremamente economico
            messages=st.session_state.messages,
            stream=True
        )
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                full_response += chunk.choices[0].delta.content
                response_placeholder.write(full_response)
                
        st.session_state.messages.append({"role": "assistant", "content": full_response})
