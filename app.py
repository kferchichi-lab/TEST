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
    # ---- ONGLET 1 : RAPPORTS ----
    with tab1:
        st.markdown("""
            <style>
            .filter-title { text-align:center !important; font-weight:600; color:#1E293B; margin-top:0; margin-bottom:15px; width:100%; }
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
                    fig = px.pie(df_s, values='Nombre', names='Site', hole=0.6, color_discrete_sequence=['#1E3A8A','#0EA5E9','#94A3B8'])
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(margin=dict(t=10,b=10,l=10,r=10), height=220, showlegend=False, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                with g2:
                    fig2 = px.bar(df_c.sort_values('Nombre'), x='Nombre', y='Domaine', orientation='h', text='Nombre', color_discrete_sequence=['#1E3A8A'])
                    fig2.update_traces(textposition='outside', cliponaxis=False)
                    fig2.update_layout(margin=dict(t=5,b=5,l=10,r=40), height=220, xaxis_title=None, yaxis_title=None, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
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

        # ---- TOUTE CETTE SECTION EST MAINTENANT CORRECTEMENT IMBRIQUÉE DANS L'ONGLET 2 ----
        st.markdown("<br><p style='font-size:1.2rem; font-weight:700; color:#0F172A;'>📅 Prochaines échéances calculées</p>", unsafe_allow_html=True)

        PERIODICITE = {
            "Installations électriques": 6,   # mois
            "Equipements de levage":     12,
            "Sécurité incendie":         12,
            "Installations de gaz":      12,
            "Appareil pression de gaz":  12,
        }

        COULEURS_CAT = {
            "Installations électriques": "#2a78d6",
            "Equipements de levage":     "#1baf7a",
            "Sécurité incendie":         "#e34948",
            "Installations de gaz":      "#eda100",
            "Appareil pression de gaz":  "#4a3aa7",
        }

        if not df_rapports.empty:
            col_cat_r  = [c for c in df_rapports.columns if "cat" in c.lower()]
            col_date_r = [c for c in df_rapports.columns if "date" in c.lower()]
            col_site_r = [c for c in df_rapports.columns if "site" in c.lower()]
            col_label_r= [c for c in df_rapports.columns if "equip" in c.lower() or "label" in c.lower() or "nom" in c.lower()]

            if col_cat_r and col_date_r:
                df_ech = df_rapports.copy()
                df_ech["_date"] = pd.to_datetime(df_ech[col_date_r[0]], dayfirst=True, errors='coerce')
                df_ech = df_ech.dropna(subset=["_date"])

                today_dt = pd.Timestamp.today().normalize()

                def calc_prochaine(row):
                    cat = str(row[col_cat_r[0]]).strip()
                    mois = PERIODICITE.get(cat, 12)
                    return row["_date"] + pd.DateOffset(months=mois)

                df_ech["Prochaine échéance"] = df_ech.apply(calc_prochaine, axis=1)
                df_ech["Jours restants"]     = (df_ech["Prochaine échéance"] - today_dt).dt.days

                def statut(j):
                    if j < 0:   return "⚠️ Dépassé"
                    if j < 30:  return "🔴 Urgent"
                    if j < 90:  return "🟡 Proche"
                    return "🟢 OK"

                df_ech["Statut"] = df_ech["Jours restants"].apply(statut)

                cols_affich = []
                if col_site_r:  cols_affich.append(col_site_r[0])
                if col_label_r: cols_affich.append(col_label_r[0])
                cols_affich += [col_cat_r[0], "_date", "Prochaine échéance", "Jours restants", "Statut"]

                df_show = df_ech[cols_affich].sort_values("Prochaine échéance")

                col_cfg = {
                    "_date":              st.column_config.DateColumn("Dernier contrôle", format="DD/MM/YYYY"),
                    "Prochaine échéance": st.column_config.DateColumn("Prochaine échéance", format="DD/MM/YYYY"),
                    "Jours restants":     st.column_config.NumberColumn("Jours restants", format="%d j"),
                }

                left_col, right_col = st.columns([1.5, 1])

                with left_col:
                    st.dataframe(df_show, column_config=col_cfg, hide_index=True, use_container_width=True)

                with right_col:
                    import calendar
                    calendar.setfirstweekday(0)

                    if "cal_mois" not in st.session_state:
                        st.session_state.cal_mois = today_dt.month
                    if "cal_annee" not in st.session_state:
                        st.session_state.cal_annee = today_dt.year
                    if "jour_selectionne" not in st.session_state:
                        st.session_state.jour_selectionne = None

                    # Navigation des mois
                    nav1, nav2, nav3 = st.columns([1, 3, 1])
                    with nav1:
                        if st.button("◀", key="prev_month"):
                            if st.session_state.cal_mois == 1:
                                st.session_state.cal_mois = 12
                                st.session_state.cal_annee -= 1
                            else:
                                st.session_state.cal_mois -= 1
                            st.session_state.jour_selectionne = None
                            st.rerun()
                    with nav2:
                        MOIS_FR = ["","Janvier","Février","Mars","Avril","Mai","Juin","Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
                        st.markdown(f"<p style='text-align:center;font-weight:600;font-size:14px;margin:0;padding-top:4px;'>{MOIS_FR[st.session_state.cal_mois]} {st.session_state.cal_annee}</p>", unsafe_allow_html=True)
                    with nav3:
                        if st.button("▶", key="next_month"):
                            if st.session_state.cal_mois == 12:
                                st.session_state.cal_mois = 1
                                st.session_state.cal_annee += 1
                            else:
                                st.session_state.cal_mois += 1
                            st.session_state.jour_selectionne = None
                            st.rerun()

                    m_view = st.session_state.cal_mois
                    a_view = st.session_state.cal_annee

                    # Extraction des événements du mois
                    evenements = {}
                    details_evenements = {}
                    for _, row in df_ech.iterrows():
                        d = row["Prochaine échéance"]
                        if pd.notna(d) and d.month == m_view and d.year == a_view:
                            jour = d.day
                            cat_brute = str(row[col_cat_r[0]]).strip()
                            
                            couleur = "#94a3b8"
                            for key_cat, col_val in COULEURS_CAT.items():
                                if key_cat.lower().strip() == cat_brute.lower():
                                    couleur = col_val
                                    break
                                    
                            if jour not in evenements:
                                evenements[jour] = []
                                details_evenements[jour] = []
                            evenements[jour].append(couleur)
                            details_evenements[jour].append(row)

                    # --- RENDU CALENDRIER COMPACT ---
                    jours_abbr = ["Lu","Ma","Me","Je","Ve","Sa","Di"]
                    cal_html = "<table style='width:100%; border-collapse:collapse; table-layout:fixed; margin:auto;'>"
                    cal_html += "<tr>" + "".join(f"<th style='color:#94a3b8; font-size:11px; padding:2px 0; text-align:center; font-weight:500; width:14%;'>{j}</th>" for j in jours_abbr) + "</tr>"

                    cal_obj = calendar.monthcalendar(a_view, m_view)
                    for semaine in cal_obj:
                        cal_html += "<tr>"
                        for jour in semaine:
                            if jour == 0:
                                cal_html += "<td style='padding:2px; text-align:center;'></td>"
                            else:
                                is_today = (jour == today_dt.day and m_view == today_dt.month and a_view == today_dt.year)
                                evts = evenements.get(jour, [])

                                if is_today:
                                    cell_style = "background:#1E3A8A; color:white; border-radius:50%; font-weight:600;"
                                elif evts:
                                    cell_style = f"background:{evts[0]}; color:white; border-radius:50%; font-weight:600;"
                                else:
                                    cell_style = "color:#334155;"

                                dot_html = ""
                                if len(evts) > 1:
                                    dot_html = f"<div style='font-size:7px; color:white; line-height:1; margin-top:-2px;'>+{len(evts)-1}</div>"

                                cal_html += f"""
                                <td style='padding:3px 0; text-align:center;'>
                                    <div style='width:24px; height:24px; margin:auto; display:flex; flex-direction:column;
                                    align-items:center; justify-content:center; {cell_style} font-size:10px;'>
                                        {jour}{dot_html}
                                    </div>
                                </td>"""
                        cal_html += "</tr>"
                    cal_html += "</table>"
                    st.markdown(cal_html, unsafe_allow_html=True)

                    # ---- LÉGENDE FIXE TOUJOURS VIVE ----
                    st.markdown("<div style='margin-top:12px; border-top:1px dashed #E2E8F0; padding-top:8px;'></div>", unsafe_allow_html=True)
                    for cat, couleur in COULEURS_CAT.items():
                        st.markdown(f"""
                            <div style='display:flex; align-items:center; gap:8px; margin-bottom:5px;'>
                                <span style='width:10px; height:10px; border-radius:2px; background:{couleur}; display:inline-block; flex-shrink:0;'></span>
                                <span style='font-size:11px; color:#475569;'>{cat}</span>
                            </div>""", unsafe_allow_html=True)

        # ========================================================
            # ZONE HORIZONTALE EN DESSOUS DES TABLEAUX ET CALENDRIER
            # ========================================================
            st.markdown("<div style='margin-top:20px; border-top:2px solid #E2E8F0; padding-top:15px;'></div>", unsafe_allow_html=True)
            
            jours_avec_evenements = sorted(list(details_evenements.keys()))
            
            if jours_avec_evenements:
                if st.session_state.jour_selectionne not in jours_avec_evenements:
                    st.session_state.jour_selectionne = jours_avec_evenements[0]
                
                index_defaut = jours_avec_evenements.index(st.session_state.jour_selectionne)
                
                # Alignement du titre et du selectbox
                c_title, c_select = st.columns([2, 1])
                with c_title:
                    st.markdown(f"### 📋 Contrôles prévus le {st.session_state.jour_selectionne}/{m_view}/{a_view}")
                with c_select:
                    choix_inspect = st.selectbox(
                        "🔍 Choisir la date à inspecter :",
                        options=jours_avec_evenements,
                        index=index_defaut,
                        format_func=lambda x: f"Jour {x} ({len(details_evenements[x])} contrôle(s))",
                        key="global_inspect_jour",
                        label_visibility="collapsed"
                    )
                    st.session_state.jour_selectionne = choix_inspect

                # --- AFFICHAGE HORIZONTAL DES CARTES ---
                jour_actif = st.session_state.jour_selectionne
                list_ctrls = details_evenements.get(jour_actif, [])
                
                if list_ctrls:
                    # Crée dynamiquement autant de colonnes qu'il y a de contrôles ce jour-là
                    cols_cards = st.columns(len(list_ctrls))
                    
                    for idx, row_ctrl in enumerate(list_ctrls):
                        with cols_cards[idx]:
                            c_cat = str(row_ctrl[col_cat_r[0]]).strip()
                            c_site = str(row_ctrl[col_site_r[0]]).strip() if col_site_r else ""
                            c_label = str(row_ctrl[col_label_r[0]]).strip() if col_label_r else ""
                            c_couleur = COULEURS_CAT.get(c_cat, "#94a3b8")
                            
                            # Carte descriptive premium horizontale
                            st.markdown(f"""
                            <div style='background:#F8FAFC; border-top:4px solid {c_couleur}; padding:12px; border-radius:6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); min-height:90px;'>
                                <p style='margin:0; font-size:12px; font-weight:700; color:#1E293B;'>{c_cat}</p>
                                <p style='margin:6px 0 0 0; font-size:11px; color:#475569;'>🏢 Site : <b>{c_site}</b></p>
                                {'<p style="margin:4px 0 0 0; font-size:11px; color:#64748B;">⚙️ ' + c_label + '</p>' if c_label else ''}
                            </div>
                            """, unsafe_allow_html=True)
            else:
                st.info("ℹ️ Aucun contrôle n'est planifié pour le mois sélectionné.")
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
