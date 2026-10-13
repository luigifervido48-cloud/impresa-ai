import hmac
import logging

import streamlit as st
from openai import OpenAI, OpenAIError

logger = logging.getLogger(__name__)


def normalize_user_input(value):
    """Return a trimmed string from the user input."""
    if value is None:
        return ""
    return str(value).strip()


def validate_api_key(api_key):
    """Validate that an OpenAI API key is present and return the sanitized value."""
    normalized_key = normalize_user_input(api_key)
    if not normalized_key:
        raise ValueError("Inserisci una OpenAI API Key valida.")
    if not normalized_key.startswith("sk-"):
        raise ValueError("La chiave OpenAI non sembra valida. Controlla che inizi con 'sk-'.")
    return normalized_key


def build_welcome_message():
    """Return the initial consultant-style onboarding message."""
    return (
        "Benvenuto in ImpresaAI Pro.\n\n"
        "Per preparare un'analisi mirata, descrivi l'impresa rispondendo, anche "
        "approssimativamente, alle domande pertinenti:\n\n"
        "1. In quale settore operi, quali prodotti o servizi offri e in quale area geografica?\n"
        "2. Chi sono i clienti principali e come raggiungi/acquisisci i clienti "
        "(canali, ciclo di vendita, frequenza di riacquisto)?\n"
        "3. Come genera ricavi l'attività? Se disponibili, indica fatturato o volumi, "
        "prezzi medi, margini e principali costi.\n"
        "4. Come si svolge l'operatività: processi critici, capacità, fornitori, "
        "dimensione del team e colli di bottiglia?\n"
        "5. Quali sono oggi i principali concorrenti o alternative e il tuo elemento "
        "di differenziazione?\n"
        "6. Qual è il problema prioritario, quale risultato vuoi ottenere e in quale "
        "orizzonte temporale?\n"
        "7. Quali indicatori monitori già, quale budget/risorse puoi dedicare e quali "
        "vincoli devo considerare?\n\n"
        "Puoi rispondere per punti; se un dato non è disponibile, scrivi "
        "\"non disponibile\". Ti farò domande di approfondimento solo dove servono."
    )


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

try:
    access_password = st.secrets["ACCESS_PASSWORD"]
except (FileNotFoundError, KeyError):
    st.error(
        "Configurazione mancante: imposta ACCESS_PASSWORD nei Secrets di Streamlit."
    )
    st.stop()

if not isinstance(access_password, str) or not access_password:
    st.error("ACCESS_PASSWORD deve essere configurata come testo non vuoto.")
    st.stop()

if "autenticato" not in st.session_state:
    st.session_state.autenticato = False

if not st.session_state.autenticato:
    st.markdown("### 🔒 Piattaforma privata")
    st.info("Inserisci la password fornita dall'amministratore per accedere.")
    pass_input = st.text_input("Password di accesso", type="password")
    if st.button("Accedi", use_container_width=True):
        if hmac.compare_digest(
            pass_input.encode("utf-8"), access_password.encode("utf-8")
        ):
            st.session_state.autenticato = True
            st.rerun()
        st.error("Password errata. Accesso negato.")
    st.stop()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": build_welcome_message()}
    ]

SYSTEM_PROMPT = """
Sei "ImpresaAI Pro", un consulente strategico aziendale di livello executive.

Obiettivo: comprendere in modo strutturato l'impresa, individuare cause e priorità e formulare raccomandazioni concrete, tecnicamente motivate e misurabili.

Regole:
- Usa italiano professionale e un lessico tecnico appropriato, spiegando i termini specialistici quando utile.
- Adatta profondità e raccomandazioni al settore, alla dimensione, alla maturità e alle risorse dell'impresa.
- In fase di raccolta dati, fai domande specifiche e pertinenti prima di trarre conclusioni. Organizza le domande in piccoli blocchi (massimo 5 per turno), evita di ripetere informazioni già fornite e chiedi approfondimenti solo sui punti che cambiano davvero l'analisi.
- Indaga, quando rilevante, su: offerta e modello di ricavo; segmento clienti e area geografica; canali commerciali e ciclo di vendita; fatturato, volumi, prezzi, margini e costi; processi, capacità produttiva, fornitori e organizzazione; concorrenza e posizionamento; indicatori già monitorati; obiettivo, orizzonte temporale, budget e vincoli.
- Non richiedere dati riservati o identificativi non necessari. Se un dato non è disponibile, proponi una stima esplicitamente qualificata oppure procedi dichiarando il limite.
- Distingui sempre fatti forniti dall'utente, ipotesi e conclusioni. Non inventare dati, benchmark, normative o risultati garantiti. Indica le informazioni mancanti che potrebbero modificare la raccomandazione.
- Argomenta le proposte con il nesso tra problema, causa probabile, intervento e risultato atteso. Se i dati lo consentono, mostra formule, priorità, dipendenze, rischi e trade-off.
- Definisci KPI con formula o criterio di calcolo, valore iniziale se noto, target realistico, scadenza e responsabile/funzione suggerita. Non presentare target non supportati come previsioni certe.
- Durante la raccolta, rispondi con le domande successive più utili; non forzare un rapporto completo quando mancano dati essenziali. Quando i dati bastano, oppure se l'utente chiede esplicitamente una valutazione preliminare, usa questa struttura:

📊 [PROFILO ARCHITETTURA AZIENDALE]
- sintesi del business, modello operativo e posizionamento
- evidenze disponibili, punti di forza, criticità e cause probabili
- ipotesi e lacune informative rilevanti

📈 [STRATEGIA DI OTTIMIZZAZIONE]
- 3-5 interventi sequenziali con motivazione, attività, priorità e orizzonte temporale
- KPI misurabili, target e modalità di verifica, coerenti con i dati disponibili
- risorse, dipendenze e trade-off principali

🛑 [FALL-BACK RISK]
- rischio prioritario e relativo impatto/probabilità, qualificati se non quantificabili
- errore operativo da evitare e misura di mitigazione
- prossimo passo concreto e dato da monitorare

Stile: professionale, analitico, argomentato e concreto; evita generalità e raccomandazioni non collegate al caso.
"""

conversation = [
    msg for msg in st.session_state.messages if msg.get("role") != "system"
]
st.session_state.messages = [
    {"role": "system", "content": SYSTEM_PROMPT},
    *conversation,
]

with st.sidebar:
    st.header("⚙️ Pannello di controllo")
    if st.button("Reset conversazione", use_container_width=True):
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": build_welcome_message()},
        ]
        st.rerun()

    if st.button("Esci", use_container_width=True):
        st.session_state.autenticato = False
        st.session_state.pop("messages", None)
        st.rerun()

    st.caption("Le credenziali sono configurate nei Secrets del server.")

try:
    openai_api_key = validate_api_key(st.secrets["OPENAI_API_KEY"])
except (FileNotFoundError, KeyError):
    st.error(
        "Configurazione mancante: imposta OPENAI_API_KEY nei Secrets di Streamlit."
    )
    st.stop()
except ValueError as exc:
    st.error(f"Configurazione API non valida: {exc}")
    st.stop()

client = OpenAI(api_key=openai_api_key)

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
                max_tokens=1500,
                stream=True,
            )

            for chunk in stream:
                delta = (
                    chunk.choices[0].delta.content
                    if chunk.choices and chunk.choices[0].delta
                    else None
                )
                if delta:
                    full_response += delta
                    response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)
        except OpenAIError as exc:
            logger.warning("OpenAI request failed (%s)", type(exc).__name__)
            response_placeholder.error(
                "La richiesta a OpenAI non è riuscita. Verifica la chiave API, "
                "la connessione e i limiti del tuo account, quindi riprova."
            )
            st.session_state.messages.pop()
            st.stop()

        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )
