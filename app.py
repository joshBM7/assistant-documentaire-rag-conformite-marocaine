"""Interface Streamlit.   Lancement : streamlit run app.py   (l'API doit tourner sur API_URL)"""
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(page_title="Assistant RAG – conformité", page_icon="⚖️", layout="wide")
st.title("⚖️ Assistant documentaire – conformité des documents publics")
st.caption("Aide à la décision : les réponses sont fondées sur le corpus indexé et ne remplacent pas un avis juridique.")


@st.cache_data(ttl=60)
def get_documents():
    try:
        return requests.get(f"{API_URL}/documents", timeout=10).json()
    except Exception:
        return []


docs = get_documents()
tab_q, tab_c = st.tabs(["Poser une question", "Vérifier un document"])

with tab_q:
    domaines = sorted({d["domaine"] for d in docs if d["domaine"]})
    col1, col2 = st.columns([3, 1])
    question = col1.text_input("Votre question réglementaire")
    domaine = col2.selectbox("Domaine", ["(tous)"] + domaines)
    if st.button("Rechercher", type="primary") and question:
        with st.spinner("Recherche en cours…"):
            r = requests.post(
                f"{API_URL}/ask",
                json={"question": question, "domaine": None if domaine == "(tous)" else domaine},
                timeout=120,
            )
        if r.ok:
            data = r.json()
            if data["refused"]:
                st.warning(f"{data['answer']}  \n*Raison : {data['reason']}*")
            else:
                st.markdown(data["answer"])
            with st.expander(f"Sources consultées ({len(data['sources'])})"):
                for s in data["sources"]:
                    cited = int(s["ref"][1:]) in data["cited"]
                    st.markdown(f"**[{s['ref']}] {s['label']}** {'✅ citée' if cited else ''}")
                    st.text(s["text"][:700])
        else:
            st.error(f"Erreur API {r.status_code} : {r.text}")

with tab_c:
    if not docs:
        st.info("Aucun document indexé ou API inaccessible.")
    else:
        ref = st.selectbox("Texte de référence", [d["doc_id"] for d in docs], format_func=lambda i: next(d["titre"] or i for d in docs if d["doc_id"] == i))
        n = st.slider("Nombre maximal d'exigences", 5, 30, 15)
        up = st.file_uploader("Document à vérifier (PDF ou TXT)", type=["pdf", "txt"])
        if st.button("Lancer la vérification", type="primary") and up:
            with st.spinner("Analyse en cours (plusieurs appels au modèle)…"):
                r = requests.post(
                    f"{API_URL}/compliance",
                    files={"file": (up.name, up.getvalue())},
                    data={"ref": ref, "max_requirements": n},
                    timeout=600,
                )
            if r.ok:
                res = r.json()
                st.markdown(res["markdown"])
                st.download_button("Télécharger le rapport (.md)", res["markdown"], file_name="rapport_conformite.md")
            else:
                st.error(f"Erreur API {r.status_code} : {r.text}")
