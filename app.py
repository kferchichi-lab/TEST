import streamlit as st
import plotly.express as px
import pandas as pd
import datetime
import pytz
import re
import time
import requests

st.set_page_config(
    page_title="Contrôle Réglementaire",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# INITIALISATION DES VARIABLES GLOBALES
# ==========================================
if "email_visiteur" not in st.session_state:
    st.session_state.email_visiteur = None
if "heartbeat_actif" not in st.session_state:
    st.session_state.heartbeat_actif = False

tab3 = None

TZ = pytz.timezone('Africa/Tunis')
SHEET_ID = "1ZK6VWg_gcCO70nt6DTyYogDeNeQUgovFmwWQufMVO-M"
URL_GOOGLE_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?gid=0#gid=0"
SEUIL_EN_LIGNE_SECONDES = 90  # Si heartbeat < 90s → En ligne

# ==========================================
# STYLE PREMIUM
# ==========================================
st.html("""
<style>
    [data-testid="stVVerticalBlockBorderBordered"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-left: 5px solid #1E3A8A !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.02) !important;
        padding: 20px !important;
    }
    .stSelectbox label p {
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        letter-spacing: 0.5px;
        margin-bottom: 6px !important;
    }
    div[data-baseweb="select"] {
        background-color: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        transition: all 0.25s ease-in-out !important;
    }
    div[data-baseweb="select"] > div {
        border: none !important;
        background-color: transparent !important;
    }
    div[data-baseweb="select"]:hover {
        border-color: #0EA5E9 !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.12) !important;
        cursor: pointer;
    }
    div[data-baseweb="select"] span {
        color: #0F172A !important;
        font-weight: 500 !important;
    }
    div[data-testid="stTabs"] button {
        font-size: 14px !important;
        font-weight: 600 !important;
        color: #64748B !important;
        background-color: #F8FAFC !important;
        padding: 10px 24px !important;
        margin-right: 8px !important;
        border-radius: 8px 8px 0px 0px !important;
        border: 1px solid #E2E8F0 !important;
        border-bottom: none !important;
        transition: all 0.2s ease !important;
    }
    div[data-testid="stTabs"] button:hover {
        color: #1E3A8A !important;
        background-color: #F1F5F9 !important;
    }
    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: #1E3A8A !important;
        background-color: #E0F2FE !important;
        border-color: #bae6fd !important;
        border-bottom: none !important;
        box-shadow: inset 0 3px 0px #0EA5E9 !important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-highlight-bar"] {
        background-color: transparent !important;
    }
</style>
""")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebarView"] {
        font-family: 'Inter', sans-serif !important;
        background-color: #F8FAFC !important;
    }
    [data-testid="stForm"], .stCornerRadius {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
        border-radius: 12px !important;
    }
    .stButton>button {
        background-color: #1E3A8A !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 500 !important;
        padding: 10px 24px !important;
        box-shadow: 0 2px 4px rgba(30, 58, 138, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# FONCTIONS API REST GOOGLE SHEETS
# ==========================================

def obtenir_access_token():
    try:
        import jwt as pyjwt
    except ImportError:
        return None
    try:
        private_key  = st.secrets["connections"]["gsheets"]["private_key"]
        client_email = st.secrets["connections"]["gsheets"]["client_email"]
        now = int(time.time())
        payload = {
            "iss":   client_email,
            "scope": "https://www.googleapis.com/auth/spreadsheets",
            "aud":   "https://oauth2.googleapis.com/token",
            "exp":   now + 3600,
            "iat":   now,
        }
        token_jwt = pyjwt.encode(payload, private_key, algorithm="RS256")
        resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": token_jwt},
            timeout=15
        )
        if resp.status_code == 200:
            return resp.json()["access_token"]
        return None
    except Exception:
        return None


def sheets_append(onglet, valeurs):
    """Ajoute une ligne dans un onglet Google Sheets."""
    token = obtenir_access_token()
    if not token:
        return False, "Token invalide"
    try:
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{onglet}!A:Z:append"
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            params={"valueInputOption": "RAW", "insertDataOption": "INSERT_ROWS"},
            json={"values": [valeurs]},
            timeout=15
        )
        return (True, "") if resp.status_code == 200 else (False, resp.text)
    except Exception as e:
        return False, str(e)


def sheets_lire(onglet, plage="A:Z"):
    """Lit toutes les lignes d'un onglet."""
    token = obtenir_access_token()
    if not token:
        return pd.DataFrame()
    try:
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{onglet}!{plage}"
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
        if resp.status_code != 200:
            return pd.DataFrame()
        valeurs = resp.json().get("values", [])
        if len(valeurs) <= 1:
            return pd.DataFrame()
        return pd.DataFrame(valeurs[1:], columns=valeurs[0])
    except Exception:
        return pd.DataFrame()


def sheets_ecrire_cellule(onglet, cellule, valeur):
    """Écrit une valeur dans une cellule précise."""
    token = obtenir_access_token()
    if not token:
        return False
    try:
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{onglet}!{cellule}"
        resp = requests.put(
            url,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            params={"valueInputOption": "RAW"},
            json={"values": [[valeur]]},
            timeout=15
        )
        return resp.status_code == 200
    except Exception:
        return False


def sheets_trouver_ligne_email(onglet, email):
    """Trouve le numéro de ligne d'un email dans l'onglet Presence (1-based, inclut header)."""
    token = obtenir_access_token()
    if not token:
        return None
    try:
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{onglet}!A:A"
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
        if resp.status_code != 200:
            return None
        valeurs = resp.json().get("values", [])
        for i, row in enumerate(valeurs):
            if row and row[0] == email:
                return i + 1  # 1-based
        return None
    except Exception:
        return None


# ==========================================
# FONCTIONS MÉTIER : LOGS + PRÉSENCE
# ==========================================

def ecrire_log(email):
    """Enregistre une visite dans l'onglet Logs."""
    maintenant = datetime.datetime.now(TZ).strftime("%d/%m/%Y %H:%M")
    return sheets_append("Logs", [maintenant, email])


def mettre_a_jour_presence(email):
    """
    Met à jour ou crée la ligne de présence du visiteur dans l'onglet Presence.
    Colonnes : Email | Derniere_activite | Statut
    """
    maintenant = datetime.datetime.now(TZ).strftime("%d/%m/%Y %H:%M:%S")
    ligne = sheets_trouver_ligne_email("Presence", email)

    if ligne:
        # Mettre à jour colonnes B et C de la ligne existante
        token = obtenir_access_token()
        if token:
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Presence!B{ligne}:C{ligne}"
            requests.put(
                url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                params={"valueInputOption": "RAW"},
                json={"values": [[maintenant, "En ligne"]]},
                timeout=15
            )
    else:
        # Créer nouvelle ligne
        sheets_append("Presence", [email, maintenant, "En ligne"])


def lire_presence():
    """Lit l'onglet Presence et calcule le statut temps réel."""
    df = sheets_lire("Presence", "A:C")
    if df.empty:
        return pd.DataFrame(columns=["Email", "Derniere_activite", "Statut", "Affichage"])

    maintenant = datetime.datetime.now(TZ)
    resultats = []

    for _, row in df.iterrows():
        email = row.get("Email", "")
        derniere = row.get("Derniere_activite", "")
        try:
            dt = datetime.datetime.strptime(derniere, "%d/%m/%Y %H:%M:%S")
            dt = TZ.localize(dt)
            delta = (maintenant - dt).total_seconds()

            if delta < SEUIL_EN_LIGNE_SECONDES:
                statut    = "🟢 En ligne"
                activite  = "Actif maintenant"
            elif delta < 300:
                statut    = "🟡 Récemment actif"
                minutes   = int(delta // 60)
                activite  = f"Actif il y a {minutes} min" if minutes > 0 else "Actif il y a quelques secondes"
            else:
                statut    = "🔴 Hors ligne"
                minutes   = int(delta // 60)
                heures    = int(minutes // 60)
                if heures > 0:
                    activite = f"Vu il y a {heures}h{minutes % 60:02d}"
                else:
                    activite = f"Vu il y a {minutes} min"
        except Exception:
            statut   = "⚪ Inconnu"
            activite = derniere

        resultats.append({
            "Email":             email,
            "Dernière activité": derniere,
            "Statut":            statut,
            "Activité":          activite,
        })

    return pd.DataFrame(resultats)


def lire_logs():
    """Lit l'onglet Logs."""
    return sheets_lire("Logs", "A:B")


# ==========================================
# CHARGEMENT DONNÉES RAPPORTS & PLANNING
# ==========================================
@st.cache_data(ttl=30)
def charger_donnees_sheet(nom_onglet):
    try:
        base_url = URL_GOOGLE_SHEET.split("/edit")[0]
        csv_url  = f"{base_url}/gviz/tq?tqx=out:csv&sheet={nom_onglet}"
        df = pd.read_csv(csv_url)
        return df.dropna(how='all')
    except Exception:
        return pd.DataFrame()

df_rapports = charger_donnees_sheet("Rapports")
df_planning = charger_donnees_sheet("Planning")

SOUS_EQUIPEMENTS = {
    "Installations électriques": [],
    "Equipements de levage": ["Transpalette", "Table élévatrice", "Potence", "Pont roulant",
                               "Plateforme de travail", "Nacelle", "Gerbeur", "Chariot élévateur",
                               "Palan électrique", "Ascenseur"],
    "Sécurité incendie": [],
    "Installations de gaz": ["Industrielle", "Chaudière"],
    "Appareil pression de gaz": []
}

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 4, 1])
    with col2:
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6q1BtDSDgVnJZFo0hOBfQJoDS6OYiub-qfQ&s", use_container_width=True)
    st.markdown("""
        <div style="text-align:center; margin-top:15px; margin-bottom:25px;">
            <h3 style="font-size:1.15rem; font-weight:700; margin-bottom:4px; color:#0F172A;">
                Tunisie Profilés d'Aluminium
            </h3>
            <p style="font-size:0.85rem; color:#64748B; margin:0; font-weight:500;
                      text-transform:uppercase; letter-spacing:0.5px;">
                Direction Maintenance & TN
            </p>
        </div>
    """, unsafe_allow_html=True)
    st.divider()
    st.markdown("<p style='font-weight:600; color:#334155; margin-bottom:0;'>🔐 Espace sécurisé</p>", unsafe_allow_html=True)
    role = st.selectbox("Profil utilisateur :", ["Visiteur", "Responsable"], label_visibility="collapsed")
    password_correct = False
    if role == "Responsable":
        password = st.text_input("Code d'accès :", type="password", placeholder="•••")
        if password == "admin123*":
            password_correct = True
            st.success("Accès administrateur validé")
            
            # Enregistrer la connexion responsable une seule fois par session
            if "responsable_log_enregistre" not in st.session_state:
                st.session_state.responsable_log_enregistre = True
                maintenant = datetime.datetime.now(TZ).strftime("%d/%m/%Y %H:%M")
                ecrire_log_responsable = lambda: sheets_append("Logs", [maintenant, "responsable@admin"])
                ecrire_log_responsable()
                
        elif password:
            st.error("Code d'accès incorrect")
# ==========================================
# CONTRÔLE D'ACCÈS
# ==========================================
def format_email_valide(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

acces_autorise = False
if role == "Responsable" and password_correct:
    acces_autorise = True
elif role == "Visiteur" and st.session_state.email_visiteur:
    acces_autorise = True

# Formulaire visiteur
if not acces_autorise and role == "Visiteur":
    st.markdown("""
        <div style="background:white; padding:20px; border-radius:12px; border-left:5px solid #0EA5E9;
                    box-shadow:0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom:20px;">
            <h4 style="margin:0; color:#1E3A8A;">🔑 Accès sécurisé aux rapports de contrôle réglementaire</h4>
            <p style="color:#64748B; font-size:13px;">Veuillez renseigner votre adresse e-mail professionnelle
            pour consulter les rapports et les plannings du site.</p>
        </div>
    """, unsafe_allow_html=True)
    email_saisi = st.text_input("Adresse e-mail :", placeholder="exemple@domain.com")
    if st.button("Valider l'accès", type="primary"):
        if format_email_valide(email_saisi):
            st.session_state.email_visiteur = email_saisi
            with st.spinner("Enregistrement de votre accès..."):
                succes, erreur = ecrire_log(email_saisi)
                mettre_a_jour_presence(email_saisi)
            if succes:
                st.success("✅ Accès accordé. Bienvenue !")
                st.rerun()
            else:
                st.error(f"❌ Erreur d'enregistrement : {erreur}")
                st.stop()
        else:
            st.error("Veuillez saisir une adresse e-mail valide.")

# ==========================================
# HEARTBEAT — Signal de vie toutes les 30s
# ==========================================
# Déterminer l'identifiant actif (visiteur ou responsable)
if role == "Responsable" and password_correct:
    email_actif = "responsable@admin"
elif role == "Visiteur" and st.session_state.email_visiteur:
    email_actif = st.session_state.email_visiteur
else:
    email_actif = None

if acces_autorise and email_actif:
    if "last_heartbeat" not in st.session_state:
        st.session_state.last_heartbeat = 0

    now_ts = time.time()
    if now_ts - st.session_state.last_heartbeat > 30:
        mettre_a_jour_presence(email_actif)
        st.session_state.last_heartbeat = now_ts

    st.markdown("""
        <script>
        setTimeout(function() {
            window.parent.document.querySelector('[data-testid="stApp"]').click();
        }, 30000);
        </script>
    """, unsafe_allow_html=True)
    # Initialiser le timestamp du dernier heartbeat
    if "last_heartbeat" not in st.session_state:
        st.session_state.last_heartbeat = 0

    now_ts = time.time()
    if now_ts - st.session_state.last_heartbeat > 30:
        mettre_a_jour_presence(st.session_state.email_visiteur)
        st.session_state.last_heartbeat = now_ts

    # Auto-refresh toutes les 30 secondes via st.rerun différé
    # (Streamlit re-exécute le script à chaque interaction utilisateur)
    # Pour forcer le refresh automatique on utilise un fragment vide
    st.markdown("""
        <script>
        setTimeout(function() {
            window.parent.document.querySelector('[data-testid="stApp"]').click();
        }, 30000);
        </script>
    """, unsafe_allow_html=True)

# ==========================================
# EN-TÊTE
# ==========================================
st.markdown("""
    <style>
    .stMarkdown div p, .stMarkdown div h1 { text-align: center !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div style="width:100%; text-align:center; margin:10px auto 35px auto;">
        <h1 style="text-align:center; font-size:2.6rem; font-weight:800; color:#0F172A;
                   margin:0 0 6px 0; letter-spacing:-1px; line-height:1.2;">
            Tableau de Bord Réglementaire
        </h1>
        <p style="text-align:center; font-size:1.05rem; color:#64748B; margin:0 auto;
                  font-weight:400; line-height:1.5; max-width:800px;">
            Suivi de conformité en temps réel — Synchronisé avec Direction Maintenance
        </p>
    </div>
""", unsafe_allow_html=True)

# ==========================================
# CONTENU PRINCIPAL
# ==========================================
if acces_autorise:

    val_total_rapports    = len(df_rapports) if not df_rapports.empty else 0
    val_controles_planifies = len(df_planning) if not df_planning.empty else 0
    if not df_planning.empty and "Statut" in df_planning.columns:
        val_alertes = len(df_planning[df_planning["Statut"].astype(str).str.strip().str.lower() == "non conforme"])
    else:
        val_alertes = 0

    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(f"""
            <div style="background:white; padding:22px; border-radius:12px;
                        box-shadow:0 4px 6px -1px rgba(0,0,0,0.05); border-left:5px solid #1E3A8A;">
                <p style="margin:0; font-size:12px; color:#64748B; font-weight:600;
                          text-transform:uppercase; letter-spacing:0.5px;">Total Rapports Archivés</p>
                <p style="margin:8px 0 0 0; font-size:34px; color:#0F172A; font-weight:700; line-height:1;">
                    {val_total_rapports}</p>
            </div>
        """, unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""
            <div style="background:white; padding:22px; border-radius:12px;
                        box-shadow:0 4px 6px -1px rgba(0,0,0,0.05); border-left:5px solid #0EA5E9;">
                <p style="margin:0; font-size:12px; color:#64748B; font-weight:600;
                          text-transform:uppercase; letter-spacing:0.5px;">Contrôles Planifiés</p>
                <p style="margin:8px 0 0 0; font-size:34px; color:#0F172A; font-weight:700; line-height:1;">
                    {val_controles_planifies}</p>
            </div>
        """, unsafe_allow_html=True)
    with kpi3:
        couleur = "#EF4444" if val_alertes > 0 else "#10B981"
        st.markdown(f"""
            <div style="background:white; padding:22px; border-radius:12px;
                        box-shadow:0 4px 6px -1px rgba(0,0,0,0.05); border-left:5px solid {couleur};">
                <p style="margin:0; font-size:12px; color:#64748B; font-weight:600;
                          text-transform:uppercase; letter-spacing:0.5px;">Alertes Non-Conformité</p>
                <p style="margin:8px 0 0 0; font-size:34px; color:{couleur}; font-weight:700; line-height:1;">
                    {val_alertes}</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- ONGLETS ---
    liste_onglets = ["📋 Rapports de contrôle archivés", "📅 Suivi de performance & Planification"]
    if role == "Responsable" and password_correct:
        liste_onglets.append("👥 Suivi des visites & Présence")

    onglets = st.tabs(liste_onglets)
    tab1 = onglets[0]
    tab2 = onglets[1]
    if len(onglets) > 2:
        tab3 = onglets[2]

    def convertir_lien(url):
        try:
            if "drive.google.com" in str(url) and "/file/d/" in str(url):
                fid = str(url).split("/file/d/")[1].split("/")[0]
                return f"https://drive.google.com/uc?export=download&id={fid}"
        except Exception:
            pass
        return url

    # ---- ONGLET 1 : RAPPORTS ----
    with tab1:
        st.markdown("""
            <style>
            .filter-title { text-align:center !important; font-weight:600; color:#1E293B;
                            margin-top:0; margin-bottom:15px; width:100%; }
            div[data-testid="stSelectbox"] label p { text-align:center !important; width:100%; display:block; }
            </style>
        """, unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<p class='filter-title'>Filtres de recherche avancés</p>", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            with c1: f_site   = st.selectbox("Site", ["Tous", "SGB", "MEG"])
            with c2: f_annee  = st.selectbox("Année", ["Tous", "2025", "2026"])
            with c3: f_cat    = st.selectbox("Domaine technique", ["Tous"] + list(SOUS_EQUIPEMENTS.keys()))
            with c4:
                opts = ["Tous"] + SOUS_EQUIPEMENTS[f_cat] if f_cat != "Tous" else ["Tous"] + [i for sub in SOUS_EQUIPEMENTS.values() for i in sub]
                f_sous_eq = st.selectbox("Sous-équipement", opts)

        st.markdown("<br><p style='font-size:1.2rem; font-weight:700; color:#0F172A; margin-bottom:10px;'>📂 Documents rattachés</p>", unsafe_allow_html=True)
        df_f = df_rapports.copy()
        if not df_f.empty:
            col_site = [c for c in df_f.columns if "site" in c.lower()]
            col_ex   = [c for c in df_f.columns if "exerc" in c.lower() or "ann" in c.lower()]
            col_cat  = [c for c in df_f.columns if "cat" in c.lower()]
            col_seq  = [c for c in df_f.columns if "sous" in c.lower()]
            col_lien = [c for c in df_f.columns if "lien" in c.lower() or "pdf" in c.lower()]
            col_date = [c for c in df_f.columns if "date" in c.lower() or "contr" in c.lower()]
            if f_site   != "Tous" and col_site: df_f = df_f[df_f[col_site[0]].astype(str).str.strip() == f_site]
            if f_annee  != "Tous" and col_ex:   df_f = df_f[pd.to_numeric(df_f[col_ex[0]], errors='coerce') == int(f_annee)]
            if f_cat    != "Tous" and col_cat:  df_f = df_f[df_f[col_cat[0]].astype(str).str.strip() == f_cat]
            if f_sous_eq != "Tous" and col_seq: df_f = df_f[df_f[col_seq[0]].astype(str).str.strip() == f_sous_eq]
            if col_lien: df_f[col_lien[0]] = df_f[col_lien[0]].apply(convertir_lien)
            if col_date: df_f[col_date[0]] = pd.to_datetime(df_f[col_date[0]], dayfirst=True, errors='coerce')

        if not df_f.empty:
            st.dataframe(df_f,
                column_config={
                    (col_lien[0] if col_lien else "Lien PDF"): st.column_config.LinkColumn("Action", display_text="📥 Télécharger PDF"),
                    (col_ex[0]   if col_ex   else "Exercice"): st.column_config.NumberColumn("Exercice", format="%d"),
                    (col_date[0] if col_date else "Date"):      st.column_config.DateColumn("Date de dernier contrôle", format="DD/MM/YYYY"),
                },
                hide_index=True, use_container_width=True)
        else:
            st.warning("Aucun rapport ne correspond aux critères sélectionnés.")

        st.markdown("<br><hr style='border-color:#E2E8F0;'><p style='font-size:1.2rem; font-weight:700; color:#0F172A;'>📊 Analyses globales</p>", unsafe_allow_html=True)
        if not df_rapports.empty:
            col_sc = [c for c in df_rapports.columns if "site" in c.lower()]
            col_cc = [c for c in df_rapports.columns if "cat" in c.lower()]
            if col_sc and col_cc:
                df_s = df_rapports[col_sc[0]].value_counts().reset_index(); df_s.columns = ['Site','Nombre']
                df_c = df_rapports[col_cc[0]].value_counts().reset_index(); df_c.columns = ['Domaine','Nombre']
                g1, g2 = st.columns(2)
                with g1:
                    fig = px.pie(df_s, values='Nombre', names='Site', hole=0.6,
                                 color_discrete_sequence=['#1E3A8A','#0EA5E9','#94A3B8'])
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=220,
                                      showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                with g2:
                    fig2 = px.bar(df_c.sort_values('Nombre'), x='Nombre', y='Domaine',
                                  orientation='h', text='Nombre', color_discrete_sequence=['#1E3A8A'])
                    fig2.update_traces(textposition='outside', cliponaxis=False)
                    fig2.update_layout(margin=dict(t=5,b=5,l=10,r=40), height=220,
                                       xaxis_title=None, yaxis_title=None,
                                       paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    fig2.update_xaxes(showgrid=True, gridcolor='#E2E8F0')
                    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})

        if role == "Responsable" and password_correct:
            with st.expander("🛠️ Panneau d'administration"):
                st.markdown(f"[Ouvrir le Google Sheets]({URL_GOOGLE_SHEET})")

    # ---- ONGLET 2 : PLANNING ----
    with tab2:
        st.markdown("<p style='font-size:1.2rem; font-weight:700; color:#0F172A;'>📅 Planification des contrôles obligatoires</p>", unsafe_allow_html=True)
        if not df_planning.empty:
            col_p = [c for c in df_planning.columns if "prochain" in c.lower() or "échéan" in c.lower()]
            st.dataframe(df_planning,
                column_config={(col_p[0] if col_p else "Prochain contrôle"): st.column_config.DateColumn("Échéance", format="DD/MM/YYYY")},
                hide_index=True, use_container_width=True)
        else:
            st.info("Aucun contrôle planifié.")
        if role == "Responsable" and password_correct:
            with st.expander("🛠️ Panneau d'administration"):
                st.markdown(f"[Modifier le calendrier]({URL_GOOGLE_SHEET})")

    # ---- ONGLET 3 : PRÉSENCE & VISITES ----
    if tab3 and role == "Responsable" and password_correct:
        with tab3:
            st.markdown("<p style='font-size:1.2rem; font-weight:700; color:#1E3A8A;'>👥 Suivi des visites & Présence en temps réel</p>", unsafe_allow_html=True)

            col_refresh, _ = st.columns([1, 5])
            with col_refresh:
                if st.button("🔄 Actualiser"):
                    st.rerun()

            # --- SECTION PRÉSENCE ---
            st.markdown("### 🟢 Présence en temps réel")
            st.caption(f"Un visiteur est considéré **En ligne** si son dernier signal date de moins de {SEUIL_EN_LIGNE_SECONDES}s. Mis à jour toutes les 30 secondes côté visiteur.")

            with st.spinner("Chargement de la présence..."):
                df_presence = lire_presence()

            if df_presence.empty:
                st.info("Aucun visiteur enregistré pour le moment.")
            else:
                nb_en_ligne = len(df_presence[df_presence["Statut"].str.contains("🟢")])
                nb_recent   = len(df_presence[df_presence["Statut"].str.contains("🟡")])
                nb_offline  = len(df_presence[df_presence["Statut"].str.contains("🔴")])

                p1, p2, p3 = st.columns(3)
                with p1:
                    st.markdown(f"""
                        <div style="background:#F0FDF4; padding:16px; border-radius:10px;
                                    border-left:4px solid #10B981; margin-bottom:16px;">
                            <p style="margin:0; font-size:11px; color:#064E3B; font-weight:700;
                                      text-transform:uppercase;">🟢 En ligne</p>
                            <p style="margin:4px 0 0 0; font-size:32px; color:#065F46; font-weight:800;">
                                {nb_en_ligne}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with p2:
                    st.markdown(f"""
                        <div style="background:#FFFBEB; padding:16px; border-radius:10px;
                                    border-left:4px solid #F59E0B; margin-bottom:16px;">
                            <p style="margin:0; font-size:11px; color:#78350F; font-weight:700;
                                      text-transform:uppercase;">🟡 Récemment actif</p>
                            <p style="margin:4px 0 0 0; font-size:32px; color:#92400E; font-weight:800;">
                                {nb_recent}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with p3:
                    st.markdown(f"""
                        <div style="background:#FEF2F2; padding:16px; border-radius:10px;
                                    border-left:4px solid #EF4444; margin-bottom:16px;">
                            <p style="margin:0; font-size:11px; color:#7F1D1D; font-weight:700;
                                      text-transform:uppercase;">🔴 Hors ligne</p>
                            <p style="margin:4px 0 0 0; font-size:32px; color:#991B1B; font-weight:800;">
                                {nb_offline}</p>
                        </div>
                    """, unsafe_allow_html=True)

                st.dataframe(
                    df_presence,
                    column_config={
                        "Email":             st.column_config.TextColumn("📧 Visiteur"),
                        "Dernière activité": st.column_config.TextColumn("🕐 Dernière activité"),
                        "Statut":            st.column_config.TextColumn("Statut"),
                        "Activité":          st.column_config.TextColumn("⏱️ Détail"),
                    },
                    hide_index=True,
                    use_container_width=True
                )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 📋 Historique complet des accès")

            with st.spinner("Chargement des logs..."):
                df_logs = lire_logs()

            if df_logs.empty:
                st.info("Aucun log enregistré.")
            else:
                nb_total  = len(df_logs)
                col_email = [c for c in df_logs.columns if "email" in c.lower() or "mail" in c.lower()]
                nb_uniq   = df_logs[col_email[0]].nunique() if col_email else 0

                l1, l2 = st.columns(2)
                with l1:
                    st.markdown(f"""
                        <div style="background:white; padding:16px; border-radius:10px;
                                    box-shadow:0 2px 6px rgba(0,0,0,0.05); border-left:4px solid #1E3A8A; margin-bottom:16px;">
                            <p style="margin:0; font-size:11px; color:#64748B; font-weight:600; text-transform:uppercase;">Total visites</p>
                            <p style="margin:4px 0 0 0; font-size:28px; color:#0F172A; font-weight:700;">{nb_total}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with l2:
                    st.markdown(f"""
                        <div style="background:white; padding:16px; border-radius:10px;
                                    box-shadow:0 2px 6px rgba(0,0,0,0.05); border-left:4px solid #0EA5E9; margin-bottom:16px;">
                            <p style="margin:0; font-size:11px; color:#64748B; font-weight:600; text-transform:uppercase;">Visiteurs uniques</p>
                            <p style="margin:4px 0 0 0; font-size:28px; color:#0F172A; font-weight:700;">{nb_uniq}</p>
                        </div>
                    """, unsafe_allow_html=True)

                st.dataframe(
                    df_logs,
                    column_config={
                        "Date":  st.column_config.TextColumn("📅 Date & Heure"),
                        "Email": st.column_config.TextColumn("📧 E-mail"),
                    },
                    hide_index=True,
                    use_container_width=True
                )
