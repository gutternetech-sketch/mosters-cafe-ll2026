import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

st.set_page_config(
    page_title="Mosters Café - LL 2026",
    page_icon="☕",
    layout="wide"
)

CSV_FILE = "vagter.csv"
LOGO_FILE = "logo.png"
PDF_FILE = "vagtplan.pdf"
TIMEZONE = ZoneInfo("Europe/Copenhagen")
AAR = 2026

st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}
.hero {
    text-align: center;
    padding: 1.5rem 1rem 1rem 1rem;
}
.hero h1 {
    font-size: clamp(2rem, 6vw, 4rem);
    margin-bottom: 0.2rem;
}
.hero p {
    font-size: 1.1rem;
    opacity: 0.75;
}
.shift-card {
    border-radius: 18px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 3px 14px rgba(0,0,0,0.07);
    border: 1px solid rgba(0,0,0,0.06);
}
.blue {
    background: linear-gradient(135deg, #d9ecff, #eef7ff);
}
.green {
    background: linear-gradient(135deg, #ddf7df, #f1fff1);
}
.common {
    background: linear-gradient(135deg, #fff1cf, #fff9e8);
}
.person-pill {
    display: inline-block;
    background: rgba(255,255,255,0.75);
    padding: 0.25rem 0.55rem;
    border-radius: 999px;
    margin: 0.15rem;
    font-size: 0.9rem;
}
.helper-pill {
    display: inline-block;
    background: #f56e5f;
    color: white;
    padding: 0.25rem 0.6rem;
    border-radius: 999px;
    margin: 0.15rem;
    font-size: 0.9rem;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)


def load_data():
    df = pd.read_csv(CSV_FILE)
    df = df.fillna("")

    expected_cols = ["dag", "vogn", "start", "slut", "personer", "hjaelpere"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    return df


def split_liste(tekst):
    if not tekst:
        return []

    return [
        p.strip()
        for p in str(tekst).split(";")
        if p.strip()
    ]


def get_all_personer(df):
    personer = []

    for item in df["personer"]:
        personer.extend(split_liste(item))

    return sorted(set(personer))


def person_har_vagt(personer, navn):
    navn = str(navn).strip().lower()

    navne = [
        p.strip().lower()
        for p in split_liste(personer)
    ]

    return navn in navne


def lav_datetime(row, kolonne):
    dato_del = str(row["dag"]).strip().split(" ")[-1]
    dag, måned = dato_del.split("/")

    time, minut = str(row[kolonne]).split(":")

    return datetime(
        AAR,
        int(måned),
        int(dag),
        int(time),
        int(minut),
        tzinfo=TIMEZONE
    )


def tilfoej_tidspunkter(df):
    df = df.copy()

    df["start_datetime"] = df.apply(
        lambda row: lav_datetime(row, "start"),
        axis=1
    )

    df["slut_datetime"] = df.apply(
        lambda row: lav_datetime(row, "slut"),
        axis=1
    )

    df.loc[
        df["slut_datetime"] <= df["start_datetime"],
        "slut_datetime"
    ] = df["slut_datetime"] + timedelta(days=1)

    return df


def card_class(vogn):
    vogn = str(vogn).lower()

    if "blå" in vogn:
        return "blue"
    if "grøn" in vogn:
        return "green"

    return "common"


def show_shift_card(row):
    css = card_class(row["vogn"])

    personer_html = "".join(
        [
            f"<span class='person-pill'>{p}</span>"
            for p in split_liste(row["personer"])
        ]
    )

    hjaelpere_html = "".join(
        [
            f"<span class='helper-pill'>{h}</span>"
            for h in split_liste(row["hjaelpere"])
        ]
    )

    helper_section = ""
    if hjaelpere_html:
        helper_section = f"<div style='margin-top:0.4rem;'>🙋 {hjaelpere_html}</div>"

    html = f"""
    <div class="shift-card {css}">
        <strong>{row["dag"]} · {row["vogn"]}</strong><br>
        🕒 {row["start"]} - {row["slut"]}<br>
        <div style="margin-top:0.5rem;">👥 {personer_html}</div>
        {helper_section}
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def show_thank_you_card():
    st.markdown("""
    <div class="shift-card common" style="text-align:center;">
        <h3>☕ Tusind tak for en skøn Landslejr</h3>
        <p>Det har været en fornøjelse at have dig med i Caféen.</p>
        <p><strong>- Hilsen Caféudvalget</strong></p>
    </div>
    """, unsafe_allow_html=True)


df = load_data()

df = df[
    ~df["vogn"].str.contains("opstart|fælles|aktivitet", case=False, na=False)
]

df = tilfoej_tidspunkter(df)
alle_personer = get_all_personer(df)


if Path(LOGO_FILE).exists():
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.image(LOGO_FILE, width=150)

st.markdown("""
<div class="hero">
    <h1>☕ Mosters Café - LL 2026</h1>
    <p>Find dine vagter eller se den samlede vagtplan</p>
</div>
""", unsafe_allow_html=True)


tab_vagtplan, tab_mine_vagter, tab_skema = st.tabs(
    ["📅 Samlede vagter", "👤 Mine vagter", "📋 Skema"]
)


with tab_vagtplan:
    st.subheader("📅 Samlede vagter")

    col1, col2 = st.columns(2)

    with col1:
        dage = ["Alle dage"] + list(df["dag"].drop_duplicates())
        valgt_dag = st.selectbox("Vælg dag", dage)

    with col2:
        vogne = ["Alle vogne"] + list(df["vogn"].drop_duplicates())
        valgt_vogn = st.selectbox("Vælg vogn", vogne)

    vis_df = df.copy()

    if valgt_dag != "Alle dage":
        vis_df = vis_df[vis_df["dag"] == valgt_dag]

    if valgt_vogn != "Alle vogne":
        vis_df = vis_df[vis_df["vogn"] == valgt_vogn]

    if len(vis_df) == 0:
        st.warning("Ingen vagter fundet.")
    else:
        for _, row in vis_df.iterrows():
            show_shift_card(row)


with tab_mine_vagter:
    st.subheader("👤 Mine vagter")

    if not alle_personer:
        st.warning("Der blev ikke fundet nogen navne i vagtplanen.")
    else:
        valgt_person = st.selectbox(
            "Vælg dit navn",
            alle_personer,
            index=None,
            placeholder="Vælg navn..."
        )

        if valgt_person:
            nu = datetime.now(TIMEZONE)

            mine_vagter = df[
                df["personer"].apply(
                    lambda x: person_har_vagt(x, valgt_person)
                )
            ]

            mine_vagter = mine_vagter[
                mine_vagter["slut_datetime"] > nu
            ]

            if len(mine_vagter) == 0:
                show_thank_you_card()
            else:
                st.success(f"{valgt_person} har {len(mine_vagter)} kommende vagt(er).")

                for _, row in mine_vagter.iterrows():
                    show_shift_card(row)
        else:
            st.info("Vælg dit navn for at se dine vagter.")


with tab_skema:
    st.subheader("📋 Skema")

    st.write("Her kan du hente den originale vagtplan som PDF.")

    # Debug info
    pdf_path = Path(PDF_FILE)
    st.write(f"Debug: Looking for PDF at: `{pdf_path.absolute()}`")
    st.write(f"Debug: PDF exists: {pdf_path.exists()}")
    
    # List files in current directory
    cwd = Path.cwd()
    files_in_dir = list(cwd.glob("*"))
    st.write(f"Debug: Files in directory ({cwd}): {[f.name for f in files_in_dir]}")

    if pdf_path.exists():
        with open(PDF_FILE, "rb") as pdf_file:
            PDFbyte = pdf_file.read()

        st.download_button(
            label="📥 Download skema som PDF",
            data=PDFbyte,
            file_name="Mosters_Cafe_Vagtplan.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.warning(
            "PDF-filen blev ikke fundet. "
            "Læg vagtplan.pdf i samme mappe som app.py."
        )