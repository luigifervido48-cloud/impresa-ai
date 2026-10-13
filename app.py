import logging
import streamlit as st
from openai import OpenAI, OpenAIError

from app_helpers import (
    build_welcome_message,
    normalize_user_input,
)

logger = logging.getLogger(__name__)

st.set_page_config(page_title="ImpresaAI Pro", page_icon="📊", layout="wide")

st.title("📊 ImpresaAI Pro")
st.caption("Il consulente strategico per aziende, PMI e micro-attività")

st.markdown(
    """
    <style>
    [data-testid="stChatInputTextArea"],
    [data-testid="stChatMessageContent"] {
        direction: ltr !important;
        text-align: left !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": build_welcome_message()}
    ]

SYSTEM_PROMPT = """
Sei "ImpresaAI Pro", un consulente strategico aziendale di livello executive.

Obiettivo: analizzare rapidamente un’impresa, identificarne il volto competitivo, il collo di bottiglia operativo e costruire una strategia concreta.

Regole:
- Parla in italiano chiaro, diretto e professionale.
- Adatta il linguaggio alla scala aziendale: micro-attività, PMI o grande industria.
- Se l’utente non ha ancora specificato tutti i dati necessari, chiedi solo ciò che serve per continuare.
- Non fare domande inutili o generiche.
- Fai emergere i livelli di rischio, priorità e azioni concrete.
- Genera sempre una risposta con questa struttura esatta:

📊 [PROFILO ARCHITETTURA AZIENDALE]
- descrizione sintetica del business
- modello operativo
- punti di forza e debolezza
- priorità strategiche

📈 [STRATEGIA DI OTTIMIZZAZIONE]
- 3 step logici e sequenziali
- azioni concrete, misurabili e realistiche
- target da raggiungere nel breve e medio termine

🛑 [FALL-BACK RISK]
- errore operativo da evitare assolutamente
- rischio principale
- misura correttiva severa

Stile: incisivo, pratico, da consulente senior, mai generico.
"""

conversation = [
    msg for msg in st.session_state.messages if msg.get("role") != "system"
]
st.session_state.messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    *conversation,
]

with st.sidebar:
    st.header("⚙️ Pannello di Controllo")
    if st.button("Reset conversazione", use_container_width=True):
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": build_welcome_message()},
        ]
        st.rerun()
    st.caption("Accesso pubblico attivo. Consulente online.")

# Recupero automatico e sicuro della tua chiave API dai Secrets di Streamlit
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    client = OpenAI(api_key=openai_api_key)
except Exception as e:
    st.error("Errore di configurazione della chiave sul server. Contatta l'amministratore.")
    st.stop()

for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = normalize_user_input(
    st.chat_input("Descrivi il tuo business, il problema e il tuo obiettivo...")
)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""

        try:
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=st.session_state.messages,
                temperature=0.35,
                max_tokens=700,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    full_response += delta
                    response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)
        except OpenAIError as exc:
            logger.warning("OpenAI request failed (%s)", type(exc).__name__)
            response_placeholder.error(
                "Il server non ha risposto. Verifica che la chiave nei Secrets sia corretta e carica di credito."
            )
            st.session_state.messages.pop()
            st.stop()

        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )

