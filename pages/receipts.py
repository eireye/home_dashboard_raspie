import streamlit as st
import anthropic
import base64
import pandas as pd
import os
from datetime import datetime
from pathlib import Path
import cv2
import tempfile

KATEGORIER = [
    "Mat & dagligvarer",
    "Restaurant & takeaway",
    "Hjem & interiør",
    "Helse & apotek",
    "Klær & sko",
    "Underholdning",
    "Bil",
    "Annet"
]

BETALERE = ["Eirik", "Mari", "Felleskonto"]

PARQUET_PATH = Path(os.getenv("RECEIPTS_PATH", "/home/eireye/kvitteringer/kvitteringer.parquet"))

def lagre_kvittering(data: dict):
    PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
    ny_rad = pd.DataFrame([data])
    if PARQUET_PATH.exists():
        eksisterende = pd.read_parquet(PARQUET_PATH)
        oppdatert = pd.concat([eksisterende, ny_rad], ignore_index=True)
    else:
        oppdatert = ny_rad
    oppdatert.to_parquet(PARQUET_PATH, index=False)

def analyser_kvittering(bilde_bytes: bytes) -> dict:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    bilde_b64 = base64.standard_b64encode(bilde_bytes).decode("utf-8")
    melding = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": bilde_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": """Analyser denne kvitteringen og returner KUN et JSON-objekt med følgende felt:
{
  "butikk": "navn på butikk/restaurant",
  "dato": "YYYY-MM-DD eller null hvis ukjent",
  "totalt": 123.45,
  "valuta": "NOK",
  "varer": ["vare 1", "vare 2"],
  "forslag_kategori": "en av: Mat & dagligvarer, Restaurant & takeaway, Hjem & interiør, Helse & apotek, Klær & sko, Underholdning, Bil, Annet"
}
Ikke inkluder noe annet enn JSON-objektet."""
                    }
                ],
            }
        ],
    )
    import json
    tekst = melding.content[0].text.strip()
    return json.loads(tekst)

def ta_bilde() -> bytes | None:
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return None
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return None
    _, buf = cv2.imencode('.jpg', frame)
    return buf.tobytes()

def show():
    st.markdown("### 🧾 Scan kvittering")

    if 'kvittering_steg' not in st.session_state:
        st.session_state.kvittering_steg = 'kamera'
    if 'bilde_bytes' not in st.session_state:
        st.session_state.bilde_bytes = None
    if 'analyse' not in st.session_state:
        st.session_state.analyse = None

    # STEG 1: Ta bilde
    if st.session_state.kvittering_steg == 'kamera':
        st.caption("Legg kvitteringen foran kameraet og trykk på knappen")
        if st.button("📷 Ta bilde", use_container_width=True):
            with st.spinner("Tar bilde..."):
                bilde = ta_bilde()
            if bilde:
                st.session_state.bilde_bytes = bilde
                st.session_state.kvittering_steg = 'analyserer'
                st.rerun()
            else:
                st.error("Kunne ikke ta bilde. Sjekk at kameraet er koblet til.")

        # Alternativ: last opp bilde
        st.caption("— eller last opp bilde —")
        opplastet = st.file_uploader("Last opp kvittering", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if opplastet:
            st.session_state.bilde_bytes = opplastet.read()
            st.session_state.kvittering_steg = 'analyserer'
            st.rerun()

    # STEG 2: Analyserer
    elif st.session_state.kvittering_steg == 'analyserer':
        with st.spinner("Analyserer kvittering med AI..."):
            try:
                resultat = analyser_kvittering(st.session_state.bilde_bytes)
                st.session_state.analyse = resultat
                st.session_state.kvittering_steg = 'bekreft'
                st.rerun()
            except Exception as e:
                st.error(f"Kunne ikke analysere: {e}")
                if st.button("Prøv igjen"):
                    st.session_state.kvittering_steg = 'kamera'
                    st.rerun()

    # STEG 3: Bekreft og klassifiser
    elif st.session_state.kvittering_steg == 'bekreft':
        analyse = st.session_state.analyse

        col_bilde, col_info = st.columns([1, 2])

        with col_bilde:
            st.image(st.session_state.bilde_bytes, use_container_width=True)

        with col_info:
            st.markdown(f"**{analyse.get('butikk', 'Ukjent butikk')}**")
            st.markdown(f"💰 **{analyse.get('totalt', '?')} {analyse.get('valuta', 'NOK')}**")
            st.caption(f"Dato: {analyse.get('dato', 'ukjent')}")

            if analyse.get('varer'):
                with st.expander("Varer"):
                    for vare in analyse['varer'][:8]:
                        st.caption(f"• {vare}")

        st.divider()

        # Kategori
        st.caption("Kategori:")
        forslag = analyse.get('forslag_kategori', 'Annet')
        forslag_idx = KATEGORIER.index(forslag) if forslag in KATEGORIER else 0
        valgt_kategori = st.session_state.get('valgt_kategori', forslag)

        kat_cols = st.columns(4)
        for i, kat in enumerate(KATEGORIER):
            with kat_cols[i % 4]:
                valgt = valgt_kategori == kat
                if st.button(f"{'✓ ' if valgt else ''}{kat}", key=f"kat_{i}", use_container_width=True):
                    st.session_state.valgt_kategori = kat
                    st.rerun()

        st.divider()

        # Betaler
        st.caption("Betalt av:")
        valgt_betaler = st.session_state.get('valgt_betaler', 'Felleskonto')
        bet_cols = st.columns(3)
        for i, betaler in enumerate(BETALERE):
            with bet_cols[i]:
                valgt = valgt_betaler == betaler
                if st.button(f"{'✓ ' if valgt else ''}{betaler}", key=f"bet_{i}", use_container_width=True):
                    st.session_state.valgt_betaler = betaler
                    st.rerun()

        st.divider()

        col_ok, col_avbryt = st.columns(2)
        with col_ok:
            if st.button("✅ Lagre", use_container_width=True):
                lagre_kvittering({
                    "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                    "tidspunkt": datetime.now().isoformat(),
                    "butikk": analyse.get('butikk'),
                    "dato": analyse.get('dato'),
                    "totalt": analyse.get('totalt'),
                    "valuta": analyse.get('valuta', 'NOK'),
                    "kategori": st.session_state.get('valgt_kategori', forslag),
                    "betalt_av": st.session_state.get('valgt_betaler', 'Felleskonto'),
                    "varer": str(analyse.get('varer', [])),
                    "gjennomgatt": False
                })
                st.success("Lagret!")
                # Reset
                st.session_state.kvittering_steg = 'kamera'
                st.session_state.bilde_bytes = None
                st.session_state.analyse = None
                st.session_state.pop('valgt_kategori', None)
                st.session_state.pop('valgt_betaler', None)
                st.rerun()

        with col_avbryt:
            if st.button("❌ Avbryt", use_container_width=True):
                st.session_state.kvittering_steg = 'kamera'
                st.session_state.bilde_bytes = None
                st.session_state.analyse = None
                st.rerun()
