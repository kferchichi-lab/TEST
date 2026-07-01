import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import pandas as pd
import datetime
import pytz
import re
import time
import requests
import calendar
import base64
from weasyprint import HTML

def generer_rapport_equipements_pdf(df_exigences, site_filtre):
    """
    Génère un rapport PDF de 5 pages pour un site spécifique (SGB ou MEG).
    """
    categories = [
        "Installations électriques",
        "Equipements de levage",
        "Sécurité incendie",
        "Installations de gaz",
        "Appareil pression de gaz"
    ]
    
    # 1. Filtrer uniquement les lignes de type "Equipement"
    df_eq = df_exigences[df_exigences.iloc[:, 0].astype(str).str.strip().str.lower() == "equipement"]
    
    # 2. Filtrer selon le Site (Colonne index 1)
    df_eq = df_eq[df_eq.iloc[:, 1].astype(str).str.strip().str.upper() == site_filtre.upper()]

    html_content = f"""
    <html>
    <head>
    <style>
        @page {{
            size: A4 portrait;
            margin: 20mm 15mm;
            @bottom-right {{
                content: "Page " counter(page) " / " counter(pages);
                font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
                font-size: 9pt;
                color: #64748B;
            }}
        }}
        body {{
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            color: #1E293B;
            margin: 0;
            padding: 0;
            font-size: 10pt;
        }}
        .page {{
            page-break-after: always;
        }}
        .page:last-child {{
            page-break-after: avoid;
        }}
        .header-title {{
            text-align: center;
            font-size: 18pt;
            font-weight: bold;
            color: #1E3A8A;
            margin-bottom: 20px;
            text-transform: uppercase;
            border-bottom: 2px solid #1E3A8A;
            padding-bottom: 10px;
        }}
        .meta-info {{
            margin-bottom: 25px;
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            padding: 15px;
            border-radius: 6px;
            line-height: 1.8;
            font-size: 11pt;
        }}
        .category-title {{
            font-size: 14pt;
            color: #0EA5E9;
            font-weight: bold;
            margin-top: 10px;
            margin-bottom: 15px;
            border-left: 4px solid #0EA5E9;
            padding-left: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        th, td {{
            border: 1px solid #CBD5E1;
            padding: 10px;
            text-align: left;
        }}
        th {{
            background-color: #1E3A8A;
            color: white;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 9pt;
        }}
        .col-sub {{ width: 60%; }}
        .col-nb {{ width: 20%; text-align: center; }}
        .col-chk {{ width: 20%; text-align: center; }}
        .td-center {{ text-align: center; }}
        
        .checkbox-box {{
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 1px solid #475569;
            border-radius: 2px;
            margin-top: 3px;
        }}
        .signature-section {{
            margin-top: 40px;
            width: 100%;
            border-top: 1px dashed #CBD5E1;
            padding-top: 15px;
        }}
        .signature-title {{
            font-weight: bold;
            text-decoration: underline;
            margin-bottom: 60px;
        }}
    </style>
    </head>
    <body>
    """

    for cat in categories:
        # Filtrer par catégorie parmi les équipements du site
        df_cat = df_eq[df_eq.iloc[:, 2].astype(str).str.strip() == cat]
        
        html_content += f"""
        <div class="page">
            <div class="header-title">Rapport d'Inspection Réglementaire — Site {site_filtre.upper()}</div>
            
            <div class="meta-info">
                <strong>Inspecteur technique :</strong> ............................................................<br>
                <strong>Accompagnant :</strong> ........................................................................<br>
                <strong>Date :</strong> .......................................................................................
            </div>
            
            <div class="category-title">{cat}</div>
            
            <table>
                <thead>
                    <tr>
                        <th class="col-sub">Sous-équipements</th>
                        <th class="col-nb">Nombre</th>
                        <th class="col-chk">Case à cocher</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        if not df_cat.empty:
            for _, row in df_cat.iterrows():
                sous_eq = row.iloc[3] if pd.notna(row.iloc[3]) else "-"
                nombre = row.iloc[4] if pd.notna(row.iloc[4]) else "0"
                html_content += f"""
                    <tr>
                        <td>{sous_eq}</td>
                        <td class="td-center">{nombre}</td>
                        <td class="td-center"><span class="checkbox-box"></span></td>
                    </tr>
                """
        else:
            html_content += """
                <tr>
                    <td colspan="3" style="text-align:center; color:#94A3B8; font-style: italic;">Aucun équipement enregistré pour cette catégorie sur ce site</td>
                </tr>
            """
            
        html_content += """
                </tbody>
            </table>
            
            <div class="signature-section">
                <div class="signature-title">Signature :</div>
            </div>
        </div>
        """
        
    html_content += """
    </body>
    </html>
    """
    
    return HTML(string=html_content).write_pdf()


def generer_rapport_kpi_pdf(kpi_data, df_reserve, carto_b64, logo_url):
    """
    Génère un rapport PDF premium regroupant tous les KPI de l'onglet KPI :
    Taux de réalisation 2026, Taux planifié, Taux de respect de délai,
    cartographie du taux de non-conformité, et points de réserve.
    """
    date_str = datetime.date.today().strftime('%d/%m/%Y')

    def barre(pct, couleur):
        pct = max(0, min(100, pct))
        return f"""<div style="background:#E2E8F0;border-radius:6px;height:14px;width:100%;overflow:hidden;">
            <div style="background:{couleur};height:100%;width:{pct}%;"></div></div>"""

    k1 = kpi_data["kpi1"]; k2 = kpi_data["kpi2"]; k3 = kpi_data["kpi3"]

    html_reserve_rows = ""
    if df_reserve is not None and not df_reserve.empty:
        for _, r in df_reserve.iterrows():
            html_reserve_rows += (f"<tr><td>{r.get('Site','')}</td><td>{r.get('Categorie','')}</td>"
                                   f"<td>{r.get('Sous_equipement','')}</td>"
                                   f"<td style='text-align:center;'>{r.get('Nombre',0)}</td></tr>")
    else:
        html_reserve_rows = "<tr><td colspan='4' style='text-align:center;color:#94A3B8;'>Aucun point de réserve enregistré</td></tr>"

    site_rows, cat_rows = "", ""
    if df_reserve is not None and not df_reserve.empty and "Site" in df_reserve.columns:
        tot = df_reserve["Nombre"].sum()
        for site, grp in df_reserve.groupby("Site")["Nombre"].sum().items():
            pct = round(grp/tot*100,1) if tot else 0
            site_rows += (f"""<div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;font-size:10pt;margin-bottom:3px;">
                <span>{site}</span><span>{pct}% ({grp})</span></div>{barre(pct,'#1E3A8A')}</div>""")
    if df_reserve is not None and not df_reserve.empty and "Categorie" in df_reserve.columns:
        tot = df_reserve["Nombre"].sum()
        for cat, grp in df_reserve.groupby("Categorie")["Nombre"].sum().items():
            pct = round(grp/tot*100,1) if tot else 0
            cat_rows += (f"""<div style="margin-bottom:10px;">
                <div style="display:flex;justify-content:space-between;font-size:10pt;margin-bottom:3px;">
                <span>{cat}</span><span>{pct}% ({grp})</span></div>{barre(pct,'#0EA5E9')}</div>""")

    carto_html = ""
    if carto_b64:
        carto_html = f"""
        <div class="page">
            <div class="category-title">🗺️ Taux de non-conformité de site</div>
            <p style="font-size:10pt;color:#475569;margin-bottom:15px;">
            Cartographie de synthèse du taux de non-conformité par site et par catégorie d'équipement,
            établie lors de la campagne de contrôle réglementaire 2026.</p>
            <img src="data:image/png;base64,{carto_b64}" style="width:100%;border-radius:8px;border:1px solid #E2E8F0;"/>
        </div>"""

    html_content = f"""
    <html><head><style>
        @page {{ size: A4 portrait; margin: 20mm 15mm;
            @bottom-right {{ content: "Page " counter(page) " / " counter(pages);
                font-family:'Helvetica Neue',Helvetica,Arial,sans-serif; font-size:9pt; color:#64748B; }} }}
        body {{ font-family:'Helvetica Neue',Helvetica,Arial,sans-serif; color:#1E293B; margin:0; padding:0; font-size:10pt; }}
        .page {{ page-break-after: always; }}
        .page:last-child {{ page-break-after: avoid; }}
        .logo-box {{ text-align:center; margin-bottom:8px; }}
        .logo-box img {{ height:58px; }}
        .header-title {{ text-align:center; font-size:20pt; font-weight:bold; color:#1E3A8A; margin:6px 0 4px 0;
            text-transform:uppercase; letter-spacing:0.5px; }}
        .header-sub {{ text-align:center; font-size:11pt; color:#64748B; margin-bottom:22px; }}
        .meta-info {{ background:#F8FAFC; border:1px solid #E2E8F0; border-radius:6px; padding:14px 16px;
            font-size:10pt; line-height:1.7; margin-bottom:25px; }}
        .category-title {{ font-size:15pt; color:#0EA5E9; font-weight:bold; border-left:4px solid #0EA5E9;
            padding-left:10px; margin:10px 0 16px 0; }}
        .kpi-card {{ background:#F8FAFC; border:1px solid #E2E8F0; border-left:5px solid #1E3A8A; border-radius:8px;
            padding:18px; margin-bottom:18px; }}
        .kpi-title {{ font-size:13pt; font-weight:700; color:#0F172A; margin:0 0 6px 0; }}
        .kpi-desc {{ font-size:9.5pt; color:#475569; margin:0 0 12px 0; line-height:1.5; }}
        .kpi-value {{ font-size:26pt; font-weight:800; color:#1E3A8A; margin:0 0 10px 0; }}
        table {{ width:100%; border-collapse:collapse; margin-bottom:20px; }}
        th, td {{ border:1px solid #CBD5E1; padding:8px 10px; text-align:left; font-size:9pt; }}
        th {{ background:#1E3A8A; color:white; text-transform:uppercase; font-size:8.5pt; font-weight:bold; }}
    </style></head><body>

    <div class="page">
        <div class="logo-box"><img src="{logo_url}"/></div>
        <div class="header-title">Rapport KPI — Contrôle Réglementaire</div>
        <div class="header-sub">Tunisie Profilés d'Aluminium — Direction Maintenance &amp; TN</div>
        <div class="meta-info">
            <b>Date d'édition :</b> {date_str}<br>
            <b>Objet :</b> Synthèse des indicateurs clés de performance (KPI) du suivi de conformité réglementaire —
            taux de réalisation, planification, respect des délais, non-conformités et points de réserve.
        </div>

        <div class="category-title">📊 Indicateurs clés de performance</div>

        <div class="kpi-card">
            <p class="kpi-title">1. Taux de réalisation 2026</p>
            <p class="kpi-desc">Proportion des contrôles réglementaires dont l'échéance théorique est comprise
            entre le 01/01/2026 et le 31/12/2026, effectivement réalisés (date réelle de visite enregistrée)
            par rapport au nombre total de contrôles dus sur cette période.</p>
            <p class="kpi-value">{k1['taux']}%</p>
            {barre(k1['taux'], '#10B981')}
            <p style="font-size:9pt;color:#64748B;margin-top:8px;">{k1['realises']} réalisés / {k1['restants']} restants
            — sur {k1['total']} contrôle(s) dû(s) en 2026</p>
        </div>

        <div class="kpi-card" style="border-left-color:#1E3A8A;">
            <p class="kpi-title">2. Taux planifié</p>
            <p class="kpi-desc">Part des contrôles pour lesquels une date réelle de visite a été effectivement
            saisie, par rapport à ceux pour lesquels le système utilise encore la date de la dernière visite
            connue comme estimation de planification.</p>
            <p class="kpi-value">{k2['taux']}%</p>
            {barre(k2['taux'], '#1E3A8A')}
            <p style="font-size:9pt;color:#64748B;margin-top:8px;">{k2['avec_reelle']} avec date réelle / {k2['estimes']} estimé(s)
            — sur {k2['total']} contrôle(s) au total</p>
        </div>

        <div class="kpi-card" style="border-left-color:#0EA5E9;">
            <p class="kpi-title">3. Taux de respect de délai de visite</p>
            <p class="kpi-desc">Proportion des visites réalisées dont l'écart entre la date réelle de contrôle
            et l'échéance théorique initiale du cycle n'excède pas 3 jours, par rapport au nombre total
            de visites réalisées.</p>
            <p class="kpi-value">{k3['taux']}%</p>
            {barre(k3['taux'], '#0EA5E9')}
            <p style="font-size:9pt;color:#64748B;margin-top:8px;">{k3['respectes']} respecté(s) / {k3['non_respectes']} non respecté(s)
            — sur {k3['total']} visite(s) réalisée(s)</p>
        </div>
    </div>

    {carto_html}

    <div class="page">
        <div class="category-title">📌 Points de réserve</div>
        <p style="font-size:10pt;color:#475569;margin-bottom:15px;">
        Liste consolidée des points de réserve relevés par site, catégorie et sous-équipement.</p>
        <table>
            <thead><tr><th>Site</th><th>Catégorie</th><th>Sous équipement</th><th>Nbre points</th></tr></thead>
            <tbody>{html_reserve_rows}</tbody>
        </table>

        <div style="display:flex;gap:30px;">
            <div style="flex:1;">
                <p style="font-weight:700;font-size:11pt;color:#0F172A;margin-bottom:10px;">Répartition par site</p>
                {site_rows if site_rows else "<p style='color:#94A3B8;font-size:9pt;'>Aucune donnée</p>"}
            </div>
            <div style="flex:1;">
                <p style="font-weight:700;font-size:11pt;color:#0F172A;margin-bottom:10px;">Répartition par catégorie</p>
                {cat_rows if cat_rows else "<p style='color:#94A3B8;font-size:9pt;'>Aucune donnée</p>"}
            </div>
        </div>
    </div>

    </body></html>
    """

    return HTML(string=html_content).write_pdf()


st.set_page_config(
    page_title="Contrôle Réglementaire",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# INITIALISATION
# ==========================================
if "email_visiteur"   not in st.session_state: st.session_state.email_visiteur   = None
if "heartbeat_actif"  not in st.session_state: st.session_state.heartbeat_actif  = False
if "cal_mois"         not in st.session_state: st.session_state.cal_mois         = datetime.date.today().month
if "cal_annee"        not in st.session_state: st.session_state.cal_annee        = datetime.date.today().year
if "jour_selectionne" not in st.session_state: st.session_state.jour_selectionne = None

tab3 = None
TZ       = pytz.timezone('Africa/Tunis')
SHEET_ID = "1ZK6VWg_gcCO70nt6DTyYogDeNeQUgovFmwWQufMVO-M"
URL_GOOGLE_SHEET = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?gid=0#gid=0"
SEUIL_EN_LIGNE_SECONDES = 90
calendar.setfirstweekday(0)

PERIODICITE = {
    "Installations électriques": 6,
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
MOIS_FR = ["","Janvier","Février","Mars","Avril","Mai","Juin",
           "Juillet","Août","Septembre","Octobre","Novembre","Décembre"]
SOUS_EQUIPEMENTS = {
    "Installations électriques": [],
    "Equipements de levage": ["Transpalette","Table élévatrice","Potence","Pont roulant",
                               "Plateforme de travail","Nacelle","Gerbeur","Chariot élévateur","Palan électrique","Ascenseur"],
    "Sécurité incendie": [],
    "Installations de gaz": ["Industrielle","Chaudière"],
    "Appareil pression de gaz": []
}

LUCID_CARTOGRAPHIE_URL = "https://lucid.app/lucidspark/088f02a4-bdb7-4c79-8e28-64e05fc773c3/edit?beaconFlowId=69403DCAA7251095&invitationId=inv_16e69b3a-177f-4fb1-922e-fd6c28f294d5&page=0_0"

def _charger_cartographie_b64():
    """Charge l'image de cartographie du taux de non-conformité en base64 (fichier local)."""
    try:
        with open("Cartographie.png", "rb") as f:
            return base64.b64encode(f.read()).decode("ascii")
    except Exception:
        return None

# ==========================================
# STYLE
# ==========================================
st.html("""<style>
    [data-testid="stVVerticalBlockBorderBordered"]{background-color:#FFFFFF!important;border:1px solid #E2E8F0!important;border-left:5px solid #1E3A8A!important;border-radius:12px!important;box-shadow:0 4px 15px rgba(0,0,0,0.02)!important;padding:20px!important;}
    .stSelectbox label p{color:#475569!important;font-weight:600!important;font-size:13px!important;}
    div[data-baseweb="select"]{background-color:#F8FAFC!important;border:1px solid #CBD5E1!important;border-radius:8px!important;}
    div[data-baseweb="select"]>div{border:none!important;background-color:transparent!important;}
    div[data-baseweb="select"]:hover{border-color:#0EA5E9!important;background-color:#FFFFFF!important;box-shadow:0 0 0 3px rgba(14,165,233,0.12)!important;}
    div[data-baseweb="select"] span{color:#0F172A!important;font-weight:500!important;}
    div[data-testid="stTabs"] button{font-size:14px!important;font-weight:600!important;color:#64748B!important;background-color:#F8FAFC!important;padding:10px 24px!important;margin-right:8px!important;border-radius:8px 8px 0px 0px!important;border:1px solid #E2E8F0!important;border-bottom:none!important;}
    div[data-testid="stTabs"] button:hover{color:#1E3A8A!important;background-color:#F1F5F9!important;}
    div[data-testid="stTabs"] button[aria-selected="true"]{color:#1E3A8A!important;background-color:#E0F2FE!important;border-color:#bae6fd!important;border-bottom:none!important;box-shadow:inset 0 3px 0px #0EA5E9!important;}
    div[data-testid="stTabs"] [data-baseweb="tab-highlight-bar"]{background-color:transparent!important;}
</style>""")

st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html,body,[data-testid="stAppViewContainer"],[data-testid="stSidebarView"]{font-family:'Inter',sans-serif!important;background-color:#F8FAFC!important;}
    [data-testid="stForm"],.stCornerRadius{background-color:#FFFFFF!important;border:1px solid #E2E8F0!important;border-radius:12px!important;}
    .stButton>button{background-color:#1E3A8A!important;color:white!important;border-radius:8px!important;border:none!important;font-weight:500!important;padding:10px 24px!important;}

    /* === FIX ROBUSTE : empêche les boutons de s'écraser/se casser verticalement ===
       Cause réelle : les colonnes Streamlit rétrécissent (flex-shrink) au lieu de
       passer à la ligne quand il n'y a pas assez de place horizontale.
       Solution : autoriser le retour à la ligne (flex-wrap) + bloquer le rétrécissement
       des colonnes + forcer le texte des boutons sur une seule ligne (nowrap). */

    div[data-testid="stHorizontalBlock"]{
        flex-wrap:wrap!important;
        row-gap:10px!important;
        column-gap:10px!important;
    }
    div[data-testid="column"]{
        flex:0 1 auto!important;
        width:auto!important;
        min-width:max-content!important;
    }
    .stButton, .stDownloadButton{
        width:auto!important;
    }
    .stButton>button, .stDownloadButton>button,
    div[data-testid="stButton"] button,
    div[data-testid="stDownloadButton"] button,
    button[kind="primary"], button[kind="secondary"],
    button[data-testid^="baseButton"]{
        white-space:nowrap!important;
        width:auto!important;
        min-width:unset!important;
        height:auto!important;
        line-height:1.3!important;
        font-size:14px!important;
        padding:10px 18px!important;
        display:inline-flex!important;
        align-items:center!important;
        justify-content:center!important;
    }
    /* Les libellés des boutons sont parfois dans un <p> ou <div> imbriqué
       qui possède son propre comportement de retour à la ligne : on le neutralise. */
    .stButton>button *, .stDownloadButton>button *,
    div[data-testid="stButton"] button *,
    div[data-testid="stDownloadButton"] button *,
    button[kind="primary"] *, button[kind="secondary"] *{
        white-space:nowrap!important;
    }
    .stDownloadButton>button{
        background-color:#1E3A8A!important;
        color:white!important;
        border-radius:8px!important;
        border:none!important;
        font-weight:600!important;
    }
    .stDownloadButton>button:hover{background-color:#1D4ED8!important;}
</style>""", unsafe_allow_html=True)

# ==========================================
# API GOOGLE SHEETS
# ==========================================
def obtenir_access_token():
    try:
        import jwt as pyjwt
        private_key  = st.secrets["connections"]["gsheets"]["private_key"]
        client_email = st.secrets["connections"]["gsheets"]["client_email"]
        now = int(time.time())
        payload = {"iss":client_email,"scope":"https://www.googleapis.com/auth/spreadsheets",
                   "aud":"https://oauth2.googleapis.com/token","exp":now+3600,"iat":now}
        token_jwt = pyjwt.encode(payload, private_key, algorithm="RS256")
        resp = requests.post("https://oauth2.googleapis.com/token",
            data={"grant_type":"urn:ietf:params:oauth:grant-type:jwt-bearer","assertion":token_jwt},timeout=15)
        return resp.json()["access_token"] if resp.status_code==200 else None
    except Exception:
        return None

def sheets_append(onglet, valeurs):
    token = obtenir_access_token()
    if not token: return False,"Token invalide"
    try:
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{onglet}!A:Z:append"
        resp = requests.post(url,headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
            params={"valueInputOption":"RAW","insertDataOption":"INSERT_ROWS"},json={"values":[valeurs]},timeout=15)
        return (True,"") if resp.status_code==200 else (False,resp.text)
    except Exception as e:
        return False,str(e)

def sheets_lire(onglet, plage="A:Z"):
    token = obtenir_access_token()
    if not token: return pd.DataFrame()
    try:
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{onglet}!{plage}"
        resp = requests.get(url,headers={"Authorization":f"Bearer {token}"},timeout=15)
        if resp.status_code!=200: return pd.DataFrame()
        valeurs = resp.json().get("values",[])
        if len(valeurs)<=1: return pd.DataFrame()
        return pd.DataFrame(valeurs[1:],columns=valeurs[0])
    except Exception:
        return pd.DataFrame()

def sheets_ecrire_cellule(onglet, cellule, valeur):
    ok, _ = sheets_ecrire_cellule_v2(onglet, cellule, valeur)
    return ok

def sheets_ecrire_cellule_v2(onglet, cellule, valeur):
    """Écrit une valeur dans une cellule précise. Retourne (ok, message_erreur)."""
    token = obtenir_access_token()
    if not token: return False, "Token invalide"
    try:
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{onglet}!{cellule}"
        resp = requests.put(url,headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
            params={"valueInputOption":"RAW"},json={"values":[[valeur]]},timeout=15)
        if resp.status_code == 200:
            return True, ""
        return False, f"HTTP {resp.status_code}: {resp.text[:200]}"
    except Exception as e:
        return False, str(e)

def sheets_trouver_ligne_email(onglet, email):
    token = obtenir_access_token()
    if not token: return None
    try:
        url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{onglet}!A:A"
        resp = requests.get(url,headers={"Authorization":f"Bearer {token}"},timeout=15)
        if resp.status_code!=200: return None
        for i,row in enumerate(resp.json().get("values",[])):
            if row and row[0]==email: return i+1
        return None
    except Exception:
        return None

def ecrire_log(email):
    maintenant = datetime.datetime.now(TZ).strftime("%d/%m/%Y %H:%M")
    return sheets_append("Logs",[maintenant,email])

def mettre_a_jour_presence(email):
    maintenant = datetime.datetime.now(TZ).strftime("%d/%m/%Y %H:%M:%S")
    ligne = sheets_trouver_ligne_email("Presence",email)
    if ligne:
        token = obtenir_access_token()
        if token:
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Presence!B{ligne}:C{ligne}"
            requests.put(url,headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},
                params={"valueInputOption":"RAW"},json={"values":[[maintenant,"En ligne"]]},timeout=15)
    else:
        sheets_append("Presence",[email,maintenant,"En ligne"])

def lire_presence():
    df = sheets_lire("Presence","A:C")
    if df.empty: return pd.DataFrame(columns=["Email","Derniere_activite","Statut","Activite"])
    maintenant = datetime.datetime.now(TZ)
    resultats = []
    for _,row in df.iterrows():
        email=row.get("Email",""); derniere=row.get("Derniere_activite","")
        try:
            dt=TZ.localize(datetime.datetime.strptime(derniere,"%d/%m/%Y %H:%M:%S"))
            delta=(maintenant-dt).total_seconds()
            if delta<SEUIL_EN_LIGNE_SECONDES: statut="🟢 En ligne"; activite="Actif maintenant"
            elif delta<300:
                m=int(delta//60); statut="🟡 Récemment actif"; activite=f"Actif il y a {m} min" if m>0 else "Actif il y a quelques secondes"
            else:
                m=int(delta//60); h=int(m//60); statut="🔴 Hors ligne"
                activite=f"Vu il y a {h}h{m%60:02d}" if h>0 else f"Vu il y a {m} min"
        except Exception:
            statut="⚪ Inconnu"; activite=derniere
        resultats.append({"Email":email,"Dernière activité":derniere,"Statut":statut,"Activité":activite})
    return pd.DataFrame(resultats)

def lire_logs():
    return sheets_lire("Logs","A:B")
def lire_exigences():
    """Lit l'onglet Exigences."""
    return sheets_lire("Exigences", "A:F")

def ecrire_contrat(lien_pdf):
    """Met à jour ou crée la ligne du contrat dans l'onglet Exigences."""
    df = lire_exigences()
    token = obtenir_access_token()
    if not token:
        return False, "Token invalide"

    if not df.empty and "Type" in df.columns:
        ligne_contrat = df[df["Type"] == "Contrat"]
        if not ligne_contrat.empty:
            num_ligne = ligne_contrat.index[0] + 2
            url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Exigences!F{num_ligne}"
            resp = requests.put(url,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                params={"valueInputOption": "RAW"},
                json={"values": [[lien_pdf]]}, timeout=15)
            return (resp.status_code == 200), ""

    return sheets_append("Exigences", ["Contrat", "", "", "", "", lien_pdf])


def supprimer_contrat():
    """Vide le lien du contrat."""
    df = lire_exigences()
    token = obtenir_access_token()
    if not token or df.empty or "Type" not in df.columns:
        return False
    ligne_contrat = df[df["Type"] == "Contrat"]
    if ligne_contrat.empty:
        return False
    num_ligne = ligne_contrat.index[0] + 2
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Exigences!F{num_ligne}"
    resp = requests.put(url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        params={"valueInputOption": "RAW"},
        json={"values": [[""]]}, timeout=15)
    return resp.status_code == 200


def ajouter_equipement(site, categorie, sous_eq, nombre):
    """Ajoute une ligne équipement dans Exigences."""
    return sheets_append("Exigences", ["Equipement", site, categorie, sous_eq, str(nombre), ""])


def supprimer_equipement_ligne(num_ligne_sheet):
    """Vide une ligne équipement (remplace par des cellules vides)."""
    token = obtenir_access_token()
    if not token: return False
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Exigences!A{num_ligne_sheet}:F{num_ligne_sheet}"
    resp = requests.put(url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        params={"valueInputOption": "RAW"},
        json={"values": [["", "", "", "", "", ""]]}, timeout=15)
    return resp.status_code == 200


# ==========================================
# POINTS DE RÉSERVE (onglet dédié "PointsReserve")
# ==========================================
def lire_points_reserve():
    """Lit l'onglet PointsReserve : Site | Categorie | Sous_equipement | Nombre."""
    return sheets_lire("PointsReserve", "A:D")


def ajouter_point_reserve(site, categorie, sous_eq, nombre):
    """Ajoute une ligne dans l'onglet PointsReserve."""
    return sheets_append("PointsReserve", [site, categorie, sous_eq, str(nombre)])


def supprimer_ligne_generique(onglet, num_ligne_sheet, nb_colonnes):
    """Vide une ligne (remplace par des cellules vides) dans un onglet donné, sur nb_colonnes colonnes (A..)."""
    token = obtenir_access_token()
    if not token: return False
    derniere_col = chr(ord('A') + nb_colonnes - 1)
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/{onglet}!A{num_ligne_sheet}:{derniere_col}{num_ligne_sheet}"
    resp = requests.put(url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        params={"valueInputOption": "RAW"},
        json={"values": [[""] * nb_colonnes]}, timeout=15)
    return resp.status_code == 200
# ==========================================
# CHARGEMENT DONNÉES
# ==========================================
@st.cache_data(ttl=30)
def charger_donnees_sheet(nom_onglet):
    try:
        base_url = URL_GOOGLE_SHEET.split("/edit")[0]
        df = pd.read_csv(f"{base_url}/gviz/tq?tqx=out:csv&sheet={nom_onglet}")
        return df.dropna(how='all')
    except Exception:
        return pd.DataFrame()

df_rapports = charger_donnees_sheet("Rapports")
df_planning = charger_donnees_sheet("Planning")

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown("<br>",unsafe_allow_html=True)
    _,c2,_=st.columns([1,4,1])
    with c2:
        st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6q1BtDSDgVnJZFo0hOBfQJoDS6OYiub-qfQ&s",use_container_width=True)
    st.markdown("""<div style="text-align:center;margin-top:15px;margin-bottom:25px;">
        <h3 style="font-size:1.15rem;font-weight:700;margin-bottom:4px;color:#0F172A;">Tunisie Profilés d'Aluminium</h3>
        <p style="font-size:0.85rem;color:#64748B;margin:0;font-weight:500;text-transform:uppercase;letter-spacing:0.5px;">Direction Maintenance & TN</p>
    </div>""",unsafe_allow_html=True)
    st.divider()
    st.markdown("<p style='font-weight:600;color:#334155;margin-bottom:0;'>🔐 Espace sécurisé</p>",unsafe_allow_html=True)
    role=st.selectbox("Profil :",["Visiteur","Responsable"],label_visibility="collapsed")
    password_correct=False
    if role=="Responsable":
        password=st.text_input("Code d'accès :",type="password",placeholder="•••")
        if password=="admin123*":
            password_correct=True
            st.success("Accès administrateur validé")
            if "responsable_log_enregistre" not in st.session_state:
                st.session_state.responsable_log_enregistre=True
                now_str=datetime.datetime.now(TZ).strftime("%d/%m/%Y %H:%M")
                sheets_append("Logs",[now_str,"responsable@admin"])
        elif password:
            st.error("Code d'accès incorrect")

# ==========================================
# CONTRÔLE D'ACCÈS
# ==========================================
def format_email_valide(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+",email) is not None

acces_autorise=(role=="Responsable" and password_correct) or (role=="Visiteur" and st.session_state.email_visiteur)

if not acces_autorise and role=="Visiteur":
    st.markdown("""<div style="background:white;padding:20px;border-radius:12px;border-left:5px solid #0EA5E9;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);margin-bottom:20px;">
        <h4 style="margin:0;color:#1E3A8A;">🔑 Accès sécurisé aux rapports de contrôle réglementaire</h4>
        <p style="color:#64748B;font-size:13px;">Veuillez renseigner votre adresse e-mail professionnelle pour consulter les rapports et les plannings du site.</p>
    </div>""",unsafe_allow_html=True)
    email_saisi=st.text_input("Adresse e-mail :",placeholder="exemple@domain.com")
    if st.button("Valider l'accès",type="primary"):
        if format_email_valide(email_saisi):
            st.session_state.email_visiteur=email_saisi
            with st.spinner("Enregistrement de votre accès..."):
                succes,erreur=ecrire_log(email_saisi)
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
# HEARTBEAT
# ==========================================
if role=="Responsable" and password_correct: email_actif="responsable@admin"
elif role=="Visiteur" and st.session_state.email_visiteur: email_actif=st.session_state.email_visiteur
else: email_actif=None

if acces_autorise and email_actif:
    if "last_heartbeat" not in st.session_state: st.session_state.last_heartbeat=0
    now_ts=time.time()
    if now_ts-st.session_state.last_heartbeat>30:
        mettre_a_jour_presence(email_actif)
        st.session_state.last_heartbeat=now_ts
    st.markdown("""<script>setTimeout(function(){window.parent.document.querySelector('[data-testid="stApp"]').click();},30000);</script>""",unsafe_allow_html=True)

# ==========================================
# EN-TÊTE
# ==========================================
st.markdown("""<style>.stMarkdown div p,.stMarkdown div h1{text-align:center!important;}</style>""",unsafe_allow_html=True)
st.markdown("""<div style="width:100%;text-align:center;margin:10px auto 35px auto;">
    <h1 style="text-align:center;font-size:2.6rem;font-weight:800;color:#0F172A;margin:0 0 6px 0;letter-spacing:-1px;line-height:1.2;">Tableau de Bord Réglementaire</h1>
    <p style="text-align:center;font-size:1.05rem;color:#64748B;margin:0 auto;font-weight:400;line-height:1.5;max-width:800px;">Suivi de conformité en temps réel — Synchronisé avec Direction Maintenance</p>
</div>""",unsafe_allow_html=True)

# ==========================================
# CONTENU PRINCIPAL
# ==========================================
if acces_autorise:
    val_total=len(df_rapports) if not df_rapports.empty else 0
    val_plan =len(df_planning) if not df_planning.empty else 0
    val_alert=len(df_planning[df_planning["Statut"].astype(str).str.strip().str.lower()=="non conforme"]) if not df_planning.empty and "Statut" in df_planning.columns else 0

    k1,k2,k3=st.columns(3)
    with k1:
        st.markdown(f"""<div style="background:white;padding:22px;border-radius:12px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);border-left:5px solid #1E3A8A;">
            <p style="margin:0;font-size:12px;color:#64748B;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Total Rapports Archivés</p>
            <p style="margin:8px 0 0 0;font-size:34px;color:#0F172A;font-weight:700;line-height:1;">{val_total}</p></div>""",unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div style="background:white;padding:22px;border-radius:12px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);border-left:5px solid #0EA5E9;">
            <p style="margin:0;font-size:12px;color:#64748B;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Contrôles Planifiés</p>
            <p style="margin:8px 0 0 0;font-size:34px;color:#0F172A;font-weight:700;line-height:1;">{val_plan}</p></div>""",unsafe_allow_html=True)
    with k3:
        ca="#EF4444" if val_alert>0 else "#10B981"
        st.markdown(f"""<div style="background:white;padding:22px;border-radius:12px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);border-left:5px solid {ca};">
            <p style="margin:0;font-size:12px;color:#64748B;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Alertes Non-Conformité</p>
            <p style="margin:8px 0 0 0;font-size:34px;color:{ca};font-weight:700;line-height:1;">{val_alert}</p></div>""",unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    liste_onglets = ["📋 Rapports de contrôle archivés","📅 Suivi de performance & Planification","📌 Exigences"]
    if role == "Responsable" and password_correct:
        liste_onglets.append("👥 Statistiques")
        liste_onglets.append("📊 KPI")
    onglets = st.tabs(liste_onglets)
    tab1, tab2, tab_exigences = onglets[0], onglets[1], onglets[2]
    tab_kpi = None
    if len(onglets) > 3: tab3 = onglets[3]
    if len(onglets) > 4: tab_kpi = onglets[4]

    def convertir_lien(url):
        try:
            if "drive.google.com" in str(url) and "/file/d/" in str(url):
                return f"https://drive.google.com/uc?export=download&id={str(url).split('/file/d/')[1].split('/')[0]}"
        except Exception: pass
        return url

    # ---- ONGLET 1 : RAPPORTS ----
    with tab1:
        st.markdown("""<style>
            .filter-title{text-align:center!important;font-weight:600;color:#1E293B;margin-top:0;margin-bottom:15px;width:100%;}
            div[data-testid="stSelectbox"] label p{text-align:center!important;width:100%;display:block;}
        </style>""",unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<p class='filter-title'>Filtres de recherche avancés</p>",unsafe_allow_html=True)
            c1,c2,c3,c4=st.columns(4)
            with c1: f_site =st.selectbox("Site",["Tous","SGB","MEG"])
            with c2: f_annee=st.selectbox("Année",["Tous","2025","2026"])
            with c3: f_cat  =st.selectbox("Domaine technique",["Tous"]+list(SOUS_EQUIPEMENTS.keys()))
            with c4:
                opts=["Tous"]+SOUS_EQUIPEMENTS[f_cat] if f_cat!="Tous" else ["Tous"]+[i for sub in SOUS_EQUIPEMENTS.values() for i in sub]
                f_sous_eq=st.selectbox("Sous-équipement",opts)

        st.markdown("<br><p style='font-size:1.2rem;font-weight:700;color:#0F172A;margin-bottom:10px;'>📂 Documents rattachés</p>",unsafe_allow_html=True)
        df_f=df_rapports.copy()
        col_site=[c for c in df_f.columns if "site" in c.lower()]
        col_ex  =[c for c in df_f.columns if "exerc" in c.lower() or "ann" in c.lower()]
        col_cat =[c for c in df_f.columns if "cat" in c.lower()]
        col_seq =[c for c in df_f.columns if "sous" in c.lower()]
        col_lien=[c for c in df_f.columns if "lien" in c.lower() or "pdf" in c.lower()]
        col_date=[c for c in df_f.columns if "date" in c.lower() or "contr" in c.lower()]
        if not df_f.empty:
            if f_site !="Tous" and col_site: df_f=df_f[df_f[col_site[0]].astype(str).str.strip()==f_site]
            if f_annee!="Tous" and col_ex:   df_f=df_f[pd.to_numeric(df_f[col_ex[0]],errors='coerce')==int(f_annee)]
            if f_cat  !="Tous" and col_cat:  df_f=df_f[df_f[col_cat[0]].astype(str).str.strip()==f_cat]
            if f_sous_eq!="Tous" and col_seq:df_f=df_f[df_f[col_seq[0]].astype(str).str.strip()==f_sous_eq]
            if col_lien: df_f[col_lien[0]]=df_f[col_lien[0]].apply(convertir_lien)
            if col_date: df_f[col_date[0]]=pd.to_datetime(df_f[col_date[0]],dayfirst=True,errors='coerce')
        if not df_f.empty:
            st.dataframe(df_f,column_config={
                (col_lien[0] if col_lien else "Lien PDF"):st.column_config.LinkColumn("Action",display_text="📥 Télécharger PDF"),
                (col_ex[0]   if col_ex   else "Exercice"):st.column_config.NumberColumn("Exercice",format="%d"),
                (col_date[0] if col_date else "Date"):    st.column_config.DateColumn("Date de dernier contrôle",format="DD/MM/YYYY"),
            },hide_index=True,use_container_width=True)
        else:
            st.warning("Aucun rapport ne correspond aux critères sélectionnés.")

        st.markdown("<br><hr style='border-color:#E2E8F0;'><p style='font-size:1.2rem;font-weight:700;color:#0F172A;'>📊 Analyses globales</p>",unsafe_allow_html=True)
        if not df_rapports.empty:
            col_sc=[c for c in df_rapports.columns if "site" in c.lower()]
            col_cc=[c for c in df_rapports.columns if "cat" in c.lower()]
            if col_sc and col_cc:
                df_s=df_rapports[col_sc[0]].value_counts().reset_index(); df_s.columns=['Site','Nombre']
                df_c=df_rapports[col_cc[0]].value_counts().reset_index(); df_c.columns=['Domaine','Nombre']
                g1,g2=st.columns(2)
                with g1:
                    fig=px.pie(df_s,values='Nombre',names='Site',hole=0.6,color_discrete_sequence=['#1E3A8A','#0EA5E9','#94A3B8'])
                    fig.update_traces(textposition='inside',textinfo='percent+label')
                    fig.update_layout(margin=dict(t=10,b=10,l=10,r=10),height=220,showlegend=False,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})
                with g2:
                    fig2=px.bar(df_c.sort_values('Nombre'),x='Nombre',y='Domaine',orientation='h',text='Nombre',color_discrete_sequence=['#1E3A8A'])
                    fig2.update_traces(textposition='outside',cliponaxis=False)
                    fig2.update_layout(margin=dict(t=5,b=5,l=10,r=40),height=220,xaxis_title=None,yaxis_title=None,paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                    fig2.update_xaxes(showgrid=True,gridcolor='#E2E8F0')
                    st.plotly_chart(fig2,use_container_width=True,config={'displayModeBar':False})
        if role=="Responsable" and password_correct:
            with st.expander("🛠️ Panneau d'administration"):
                st.markdown(f"[Ouvrir le Google Sheets]({URL_GOOGLE_SHEET})")

    # ---- ONGLET 2 : PLANNING ----
    with tab2:
        st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#0F172A;'>📅 Planification des contrôles obligatoires</p>",unsafe_allow_html=True)
        if not df_planning.empty:
            col_p=[c for c in df_planning.columns if "prochain" in c.lower() or "échéan" in c.lower()]
            st.dataframe(df_planning,
                column_config={(col_p[0] if col_p else "Prochain contrôle"):st.column_config.DateColumn("Échéance",format="DD/MM/YYYY")},
                hide_index=True,use_container_width=True)
        else:
            st.info("Aucun contrôle planifié.")
        if role=="Responsable" and password_correct:
            with st.expander("🛠️ Panneau d'administration"):
                st.markdown(f"[Modifier le calendrier]({URL_GOOGLE_SHEET})")

        st.markdown("<br><p style='font-size:1.2rem;font-weight:700;color:#0F172A;'>📅 Prochaines échéances calculées</p>",unsafe_allow_html=True)

        # ---- FILTRES ÉCHÉANCES ----
        with st.container(border=True):
            st.markdown("<p style='font-weight:600;color:#1E293B;margin:0 0 10px 0;font-size:13px;'>🔍 Filtrer les échéances</p>",unsafe_allow_html=True)
            fc1,fc2,fc3=st.columns(3)
            with fc1: f_ech_site=st.selectbox("Site",["Tous","SGB","MEG"],key="f_ech_site")
            with fc2: f_ech_cat =st.selectbox("Catégorie",["Tous"]+list(PERIODICITE.keys()),key="f_ech_cat")
            with fc3:
                opts_seq=["Tous"]+SOUS_EQUIPEMENTS.get(f_ech_cat,[]) if f_ech_cat!="Tous" else ["Tous"]+[i for sub in SOUS_EQUIPEMENTS.values() for i in sub]
                f_ech_seq=st.selectbox("Sous-équipement",opts_seq,key="f_ech_seq")

        if not df_rapports.empty:
            col_cat_r  =[c for c in df_rapports.columns if "cat" in c.lower()]
            col_date_r =[c for c in df_rapports.columns if "date" in c.lower()]
            col_site_r =[c for c in df_rapports.columns if "site" in c.lower()]
            col_label_r=[c for c in df_rapports.columns if "equip" in c.lower() or "label" in c.lower() or "nom" in c.lower()]
            col_reelle =[c for c in df_rapports.columns if "reelle" in c.lower() or "réelle" in c.lower()]

            if col_cat_r and col_date_r:
                df_ech=df_rapports.copy()
                # Identifiant stable = numéro de ligne réel dans le Sheet (header=ligne1, donc +2)
                df_ech["_ligne_sheet"]=df_ech.index+2
                df_ech["_date_brute"]=pd.to_datetime(df_ech[col_date_r[0]],dayfirst=True,errors='coerce')

                if col_reelle:
                    df_ech["_date_reelle"]=pd.to_datetime(df_ech[col_reelle[0]],dayfirst=True,errors='coerce')
                else:
                    df_ech["_date_reelle"]=pd.NaT

                # Date de référence = réelle si dispo, sinon planifiée
                df_ech["_date"]=df_ech["_date_reelle"].combine_first(df_ech["_date_brute"])
                df_ech=df_ech.dropna(subset=["_date"])

                # Déduplication
                cles=[]
                if col_site_r:  cles.append(col_site_r[0])
                cles.append(col_cat_r[0])
                if col_label_r: cles.append(col_label_r[0])
                df_ech=df_ech.sort_values("_date_brute",ascending=True)
                df_ech=df_ech.drop_duplicates(subset=cles,keep="last")

                today_dt=pd.Timestamp.today().normalize()

                def calc_prochaine(row):
                    mois=PERIODICITE.get(str(row[col_cat_r[0]]).strip(),12)
                    return row["_date"]+pd.DateOffset(months=mois)

                df_ech["Prochaine échéance"]=df_ech.apply(calc_prochaine,axis=1)
                df_ech["Jours restants"]=(df_ech["Prochaine échéance"]-today_dt).dt.days
                df_ech["Statut"]=df_ech["Jours restants"].apply(
                    lambda j:"⚠️ Dépassé" if j<0 else "🔴 Urgent" if j<30 else "🟡 Proche" if j<90 else "🟢 OK")

                # Colonne unifiée pour visiteurs
                df_ech["Date du contrôle"]=df_ech["_date_reelle"].combine_first(df_ech["_date_brute"])

                cols_affich=[]
                if col_site_r:  cols_affich.append(col_site_r[0])
                if col_label_r: cols_affich.append(col_label_r[0])
                cols_affich+=[col_cat_r[0],"_date_brute","_date_reelle","Date du contrôle","Prochaine échéance","Jours restants","Statut","_ligne_sheet"]
                df_show=df_ech[cols_affich].sort_values("Prochaine échéance")

                # ---- APPLICATION DES FILTRES ----
                df_show_filtre=df_show.copy()
                if f_ech_site!="Tous" and col_site_r:
                    df_show_filtre=df_show_filtre[df_show_filtre[col_site_r[0]].astype(str).str.strip()==f_ech_site]
                if f_ech_cat!="Tous" and col_cat_r:
                    df_show_filtre=df_show_filtre[df_show_filtre[col_cat_r[0]].astype(str).str.strip()==f_ech_cat]
                if f_ech_seq!="Tous" and col_label_r:
                    df_show_filtre=df_show_filtre[df_show_filtre[col_label_r[0]].astype(str).str.strip().str.contains(f_ech_seq,case=False,na=False)]

                # KPIs statut
                nb_depasse=len(df_show_filtre[df_show_filtre["Statut"]=="⚠️ Dépassé"])
                nb_urgent =len(df_show_filtre[df_show_filtre["Statut"]=="🔴 Urgent"])
                nb_proche =len(df_show_filtre[df_show_filtre["Statut"]=="🟡 Proche"])
                nb_ok     =len(df_show_filtre[df_show_filtre["Statut"]=="🟢 OK"])

                kf1,kf2,kf3,kf4=st.columns(4)
                with kf1:
                    st.markdown(f"""<div style="background:#FEF2F2;padding:10px;border-radius:8px;border-left:3px solid #EF4444;margin-bottom:12px;">
                        <p style="margin:0;font-size:10px;color:#7F1D1D;font-weight:600;text-transform:uppercase;">⚠️ Dépassé</p>
                        <p style="margin:2px 0 0 0;font-size:22px;color:#991B1B;font-weight:700;">{nb_depasse}</p></div>""",unsafe_allow_html=True)
                with kf2:
                    st.markdown(f"""<div style="background:#FFF1F0;padding:10px;border-radius:8px;border-left:3px solid #e34948;margin-bottom:12px;">
                        <p style="margin:0;font-size:10px;color:#7F1D1D;font-weight:600;text-transform:uppercase;">🔴 Urgent</p>
                        <p style="margin:2px 0 0 0;font-size:22px;color:#e34948;font-weight:700;">{nb_urgent}</p></div>""",unsafe_allow_html=True)
                with kf3:
                    st.markdown(f"""<div style="background:#FFFBEB;padding:10px;border-radius:8px;border-left:3px solid #eda100;margin-bottom:12px;">
                        <p style="margin:0;font-size:10px;color:#78350F;font-weight:600;text-transform:uppercase;">🟡 Proche</p>
                        <p style="margin:2px 0 0 0;font-size:22px;color:#eda100;font-weight:700;">{nb_proche}</p></div>""",unsafe_allow_html=True)
                with kf4:
                    st.markdown(f"""<div style="background:#F0FDF4;padding:10px;border-radius:8px;border-left:3px solid #10B981;margin-bottom:12px;">
                        <p style="margin:0;font-size:10px;color:#064E3B;font-weight:600;text-transform:uppercase;">🟢 OK</p>
                        <p style="margin:2px 0 0 0;font-size:22px;color:#10B981;font-weight:700;">{nb_ok}</p></div>""",unsafe_allow_html=True)

                left_col,right_col=st.columns([1.5,1])

                # ---- COLONNE GAUCHE : TABLEAU ----
                with left_col:
                    if role!="Responsable" or not password_correct:
                        # Visiteur : une seule colonne de date
                        cols_visiteur=[]
                        if col_site_r:  cols_visiteur.append(col_site_r[0])
                        if col_label_r: cols_visiteur.append(col_label_r[0])
                        cols_visiteur+=[col_cat_r[0],"Date du contrôle","Prochaine échéance","Jours restants","Statut"]
                        st.dataframe(df_show_filtre[cols_visiteur],column_config={
                            "Date du contrôle":   st.column_config.DateColumn("📅 Date du contrôle",format="DD/MM/YYYY"),
                            "Prochaine échéance": st.column_config.DateColumn("⏭️ Prochaine échéance",format="DD/MM/YYYY"),
                            "Jours restants":     st.column_config.NumberColumn("Jours restants",format="%d j"),
                        },hide_index=True,use_container_width=True)
                    else:
                        # Responsable : deux dates + édition
                        st.markdown("""<div style='background:#EFF6FF;border-left:4px solid #2a78d6;padding:10px 14px;border-radius:6px;margin-bottom:10px;'>
                            <p style='margin:0;font-size:12px;color:#1e40af;font-weight:600;'>✏️ Mode responsable — Modifiez la colonne <b>Date réelle visite</b> puis sauvegardez.</p>
                        </div>""",unsafe_allow_html=True)
                        cols_resp=[]
                        if col_site_r:  cols_resp.append(col_site_r[0])
                        if col_label_r: cols_resp.append(col_label_r[0])
                        cols_resp+=[col_cat_r[0],"_date_brute","_date_reelle","Prochaine échéance","Jours restants","Statut","_ligne_sheet"]
                        df_editable=df_show_filtre[cols_resp].copy()
                        df_editable["_date_reelle"]=pd.to_datetime(df_editable["_date_reelle"],errors='coerce')
                        edited_df=st.data_editor(df_editable,column_config={
                            "_date_brute":        st.column_config.DateColumn("📅 Date planifiée",format="DD/MM/YYYY"),
                            "_date_reelle":       st.column_config.DateColumn("✅ Date réelle visite",format="DD/MM/YYYY",help="Saisissez ici la date réelle du contrôle effectué"),
                            "Prochaine échéance": st.column_config.DateColumn("⏭️ Prochaine échéance",format="DD/MM/YYYY"),
                            "Jours restants":     st.column_config.NumberColumn("Jours restants",format="%d j"),
                            "_ligne_sheet":       None,
                        },disabled=[c for c in df_editable.columns if c!="_date_reelle"],hide_index=True,use_container_width=True,key="editor_dates_reelles")

                        if st.button("💾 Sauvegarder les dates réelles",type="primary"):
                            with st.spinner("Mise à jour dans Google Sheets..."):
                                nb_maj=0
                                erreurs=[]
                                for idx,row_edit in edited_df.iterrows():
                                    nouvelle_date=row_edit["_date_reelle"]
                                    ancienne_date=df_editable.loc[idx,"_date_reelle"]
                                    dates_diff=False
                                    if pd.isna(nouvelle_date) and pd.isna(ancienne_date): dates_diff=False
                                    elif pd.isna(nouvelle_date)!=pd.isna(ancienne_date): dates_diff=True
                                    elif not pd.isna(nouvelle_date) and nouvelle_date!=ancienne_date: dates_diff=True
                                    if dates_diff and not pd.isna(nouvelle_date):
                                        num_ligne_sheet=int(row_edit["_ligne_sheet"])
                                        if col_reelle:
                                            num_col=df_rapports.columns.tolist().index(col_reelle[0])+1
                                        else:
                                            num_col=len(df_rapports.columns)+1
                                        lettre_col=chr(64+num_col)
                                        date_str=nouvelle_date.strftime("%d/%m/%Y")
                                        ok, msg = sheets_ecrire_cellule_v2("Rapports",f"{lettre_col}{num_ligne_sheet}",date_str)
                                        if ok:
                                            nb_maj+=1
                                        else:
                                            erreurs.append(f"Ligne {num_ligne_sheet}: {msg}")
                            if nb_maj>0:
                                st.success(f"✅ {nb_maj} date(s) enregistrée(s) !")
                            if erreurs:
                                st.error("❌ Erreurs : " + " | ".join(erreurs))
                            if nb_maj>0 or erreurs:
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.info("Aucune modification détectée.")

                # ---- COLONNE DROITE : CALENDRIER ----
                with right_col:
                    m_view=st.session_state.cal_mois
                    a_view=st.session_state.cal_annee

                    nav1,nav2,nav3=st.columns([1,3,1])
                    with nav1:
                        if st.button("◀",key="prev_month"):
                            if st.session_state.cal_mois==1: st.session_state.cal_mois=12; st.session_state.cal_annee-=1
                            else: st.session_state.cal_mois-=1
                            st.session_state.jour_selectionne=None; st.rerun()
                    with nav2:
                        st.markdown(f"<p style='text-align:center;font-weight:600;font-size:14px;margin:0;padding-top:4px;'>{MOIS_FR[m_view]} {a_view}</p>",unsafe_allow_html=True)
                    with nav3:
                        if st.button("▶",key="next_month"):
                            if st.session_state.cal_mois==12: st.session_state.cal_mois=1; st.session_state.cal_annee+=1
                            else: st.session_state.cal_mois+=1
                            st.session_state.jour_selectionne=None; st.rerun()

                    m_view=st.session_state.cal_mois
                    a_view=st.session_state.cal_annee

                    # Événements du mois (sur df_ech complet, pas filtré)
                    evenements={}; details_evt={}
                    for _,row in df_ech.iterrows():
                        d=row["Prochaine échéance"]
                        if pd.notna(d) and d.month==m_view and d.year==a_view:
                            j=d.day; cat=str(row[col_cat_r[0]]).strip()
                            col_c=COULEURS_CAT.get(cat,"#94a3b8")
                            evenements.setdefault(j,[]).append(col_c)
                            details_evt.setdefault(j,[]).append(row)

                    # En-tête jours
                    jours_abbr=["Lu","Ma","Me","Je","Ve","Sa","Di"]
                    cols_hdr=st.columns(7)
                    for i,j in enumerate(jours_abbr):
                        with cols_hdr[i]:
                            st.markdown(f"<p style='text-align:center;font-size:10px;color:#94a3b8;font-weight:500;margin:0;padding:2px 0;'>{j}</p>",unsafe_allow_html=True)

                    # CSS boutons calendrier
                    st.markdown("""<style>
                        section[data-testid="stSidebar"] ~ div button[kind="secondary"]{min-height:28px!important;height:28px!important;width:28px!important;border-radius:50%!important;font-size:11px!important;padding:0!important;line-height:1!important;}
                    </style>""",unsafe_allow_html=True)

                    today_dt2=datetime.date.today()
                    for semaine in calendar.monthcalendar(a_view,m_view):
                        cols_sem=st.columns(7)
                        for i,jour in enumerate(semaine):
                            with cols_sem[i]:
                                if jour==0:
                                    st.markdown("<div style='height:28px;'></div>",unsafe_allow_html=True)
                                else:
                                    evts    =evenements.get(jour,[])
                                    is_today=(jour==today_dt2.day and m_view==today_dt2.month and a_view==today_dt2.year)
                                    is_sel  =(jour==st.session_state.jour_selectionne)
                                    has_evt =len(evts)>0

                                    if has_evt:
                                        bg=evts[0]
                                        outline="outline:2.5px solid #0F172A;outline-offset:1px;" if is_sel else ""
                                        st.markdown(f"<div style='width:28px;height:28px;border-radius:50%;background:{bg};color:white;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;margin:auto;margin-bottom:-30px;position:relative;z-index:1;pointer-events:none;{outline}'>{jour}</div>",unsafe_allow_html=True)
                                        if st.button("​",key=f"cal_{a_view}_{m_view}_{jour}",help=f"{len(evts)} contrôle(s)"):
                                            st.session_state.jour_selectionne=jour; st.rerun()
                                    elif is_today:
                                        st.markdown(f"<div style='width:28px;height:28px;border-radius:50%;background:#1E3A8A;color:white;font-size:11px;font-weight:600;display:flex;align-items:center;justify-content:center;margin:auto;'>{jour}</div>",unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"<div style='width:28px;height:28px;display:flex;align-items:center;justify-content:center;margin:auto;font-size:11px;color:#334155;'>{jour}</div>",unsafe_allow_html=True)

                    # Légende
                    st.markdown("<div style='margin-top:12px;border-top:1px dashed #E2E8F0;padding-top:8px;'></div>",unsafe_allow_html=True)
                    cats_du_mois={str(r[col_cat_r[0]]).strip() for evts_list in details_evt.values() for r in evts_list}
                    for cat,couleur in COULEURS_CAT.items():
                        opacity="1" if cat in cats_du_mois else "0.3"
                        st.markdown(f"""<div style='display:flex;align-items:center;gap:8px;margin-bottom:5px;opacity:{opacity};'>
                            <span style='width:10px;height:10px;border-radius:2px;background:{couleur};display:inline-block;flex-shrink:0;'></span>
                            <span style='font-size:11px;color:#475569;'>{cat}</span>
                        </div>""",unsafe_allow_html=True)

                # ---- DÉTAIL JOUR SÉLECTIONNÉ ----
                jour_sel=st.session_state.jour_selectionne
                if jour_sel and jour_sel in details_evt:
                    nb_c=len(details_evt[jour_sel])
                    st.markdown(f"""<div style='margin-top:20px;padding:12px 16px;background:#F0F9FF;border-left:4px solid #0EA5E9;border-radius:8px;margin-bottom:12px;'>
                        <p style='margin:0;font-size:14px;font-weight:600;color:#0C4A6E;'>📋 {nb_c} contrôle(s) planifié(s) le {jour_sel} {MOIS_FR[m_view]} {a_view}</p>
                    </div>""",unsafe_allow_html=True)
                    nb_cols=min(nb_c,4)
                    card_cols=st.columns(nb_cols)
                    for idx,row_ctrl in enumerate(details_evt[jour_sel]):
                        with card_cols[idx%nb_cols]:
                            c_cat  =str(row_ctrl[col_cat_r[0]]).strip()
                            c_site =str(row_ctrl[col_site_r[0]]).strip()  if col_site_r  else ""
                            c_label=str(row_ctrl[col_label_r[0]]).strip() if col_label_r else ""
                            c_date =row_ctrl["_date_brute"]
                            c_reel =row_ctrl["_date_reelle"]
                            c_next =row_ctrl["Prochaine échéance"]
                            c_jours=int(row_ctrl["Jours restants"])
                            c_stat =row_ctrl["Statut"]
                            c_col  =COULEURS_CAT.get(c_cat,"#94a3b8")
                            date_fmt=c_date.strftime("%d/%m/%Y") if pd.notna(c_date) else "—"
                            reel_fmt=c_reel.strftime("%d/%m/%Y") if pd.notna(c_reel) else None
                            next_fmt=c_next.strftime("%d/%m/%Y") if pd.notna(c_next) else "—"
                            j_txt  =f"⚠️ {abs(c_jours)}j de retard" if c_jours<0 else f"Dans {c_jours} j"
                            if reel_fmt:
                                date_ctrl_html=(
                                    "<p style='margin:0 0 2px 0;font-size:10px;color:#94a3b8;'>Date réelle visite</p>"
                                    f"<p style='margin:0 0 6px 0;font-size:11px;color:#059669;font-weight:600;'>✅ {reel_fmt}</p>"
                                    "<p style='margin:0 0 2px 0;font-size:10px;color:#94a3b8;'>Date planifiée initiale</p>"
                                    f"<p style='margin:0 0 6px 0;font-size:11px;color:#94a3b8;text-decoration:line-through;'>{date_fmt}</p>"
                                )
                            else:
                                date_ctrl_html=(
                                    "<p style='margin:0 0 2px 0;font-size:10px;color:#94a3b8;'>Date planifiée</p>"
                                    f"<p style='margin:0 0 6px 0;font-size:11px;color:#334155;font-weight:500;'>{date_fmt}</p>"
                                )
                            label_html = ("<p style='margin:0 0 4px 0;font-size:11px;color:#64748B;'>⚙️ "+c_label+"</p>") if c_label else ""
                            carte_html=(
                                f"<div style='background:white;border-top:4px solid {c_col};padding:14px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.06);margin-bottom:8px;'>"
                                f"<p style='margin:0 0 8px 0;font-size:12px;font-weight:700;color:#1E293B;'>{c_cat}</p>"
                                f"<p style='margin:0 0 4px 0;font-size:11px;color:#475569;'>🏢 <b>{c_site}</b></p>"
                                f"{label_html}"
                                "<hr style='border:none;border-top:1px solid #F1F5F9;margin:8px 0;'>"
                                f"{date_ctrl_html}"
                                "<p style='margin:0 0 2px 0;font-size:10px;color:#94a3b8;'>Prochaine échéance</p>"
                                f"<p style='margin:0 0 6px 0;font-size:11px;color:#334155;font-weight:500;'>{next_fmt}</p>"
                                f"<span style='display:inline-block;padding:3px 8px;border-radius:4px;font-size:10px;font-weight:600;background:{c_col}22;color:{c_col};'>{c_stat} — {j_txt}</span>"
                                "</div>"
                            )
                            st.markdown(carte_html, unsafe_allow_html=True)
                elif evenements and jour_sel is None:
                    st.info("💡 Cliquez sur un jour coloré du calendrier pour voir les détails du contrôle.")
    # ---- ONGLET EXIGENCES ----
    with tab_exigences:
        st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#0F172A;margin-bottom:15px;'>📌 Exigences réglementaires</p>", unsafe_allow_html=True)

        df_exig = lire_exigences()

    # ===== SECTION 1 : CONTRAT D'ABONNEMENT =====
        st.markdown("### 📄 Contrat d'abonnement 2026")

        def lien_telechargement_direct(lien: str) -> str:
            """Convertit un lien Google Drive (vue/partage) en lien de téléchargement direct.
            Si ce n'est pas un lien Google Drive reconnu, renvoie le lien tel quel."""
            if not lien:
                return lien
            m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", lien)
            if not m:
                m = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", lien)
            if m:
                file_id = m.group(1)
                return f"https://drive.google.com/uc?export=download&id={file_id}"
            return lien

        lien_contrat = ""
        if not df_exig.empty and "Type" in df_exig.columns:
            ligne_c = df_exig[df_exig["Type"] == "Contrat"]
            if not ligne_c.empty:
                lien_contrat = str(ligne_c.iloc[0].get("Lien_PDF", "")).strip()

        col_contrat, col_action = st.columns([5, 1])
        with col_contrat:
            if lien_contrat and lien_contrat.lower() != "nan":
                lien_dl = lien_telechargement_direct(lien_contrat)
                st.markdown(
                    "<div style='background:white;padding:16px 20px;border-radius:10px;"
                    "box-shadow:0 2px 8px rgba(0,0,0,0.05);border-left:4px solid #1E3A8A;"
                    "display:flex;align-items:center;justify-content:space-between;'>"
                    "<span style='font-size:14px;font-weight:600;color:#1E293B;'>📑 Contrat d'abonnement 2026</span>"
                    f"<a href='{lien_dl}' download target='_blank' rel='noopener' style='text-decoration:none;background:#1E3A8A;"
                    "color:white;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:600;'>"
                    "📥 Ouvrir / Télécharger</a>"
                    "</div>", unsafe_allow_html=True)
            else:
                st.info("Aucun contrat n'a encore été ajouté.")

        if role == "Responsable" and password_correct:
            with st.expander("✏️ Gérer le contrat (Responsable)"):
                nouveau_lien = st.text_input("Lien Google Drive du contrat PDF :",
                    value=lien_contrat if lien_contrat.lower() != "nan" else "",
                    placeholder="https://drive.google.com/file/d/...")
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("💾", use_container_width=True):
                        if nouveau_lien.strip():
                            ok, err = ecrire_contrat(nouveau_lien.strip())
                            if ok:
                                st.success("✅ Contrat mis à jour !")
                                st.rerun()
                            else:
                                st.error(f"Erreur : {err}")
                        else:
                            st.warning("Veuillez coller un lien.")
                with bc2:
                    if st.button("🗑️", use_container_width=True):
                        if supprimer_contrat():
                            st.success("✅ Contrat supprimé.")
                            st.rerun()
                        else:
                            st.error("Erreur lors de la suppression.")

        st.markdown("<br><hr style='border-color:#E2E8F0;'>", unsafe_allow_html=True)     
        

    # ===== SECTION 3 : LISTE DES ÉQUIPEMENTS (ARBORESCENCE) =====
        st.markdown("### 🏭 Liste des équipements soumis au contrôle")

        df_equip = pd.DataFrame()
        if not df_exig.empty and "Type" in df_exig.columns:
            df_equip = df_exig[df_exig["Type"] == "Equipement"].copy()
            if "Nombre" in df_equip.columns:
                df_equip["Nombre"] = pd.to_numeric(df_equip["Nombre"], errors="coerce").fillna(0).astype(int)

    # Initialisation propre du Session State
        if "site_exig_sel" not in st.session_state: 
            st.session_state.site_exig_sel = None
        if "cat_exig_sel" not in st.session_state: 
            st.session_state.cat_exig_sel = None

    # Niveau 1 : choix du site
        st.markdown("<p style='font-size:13px;color:#64748B;font-weight:600;margin-bottom:8px;'>Sélectionnez un site :</p>", unsafe_allow_html=True)
        s1, s2, s3 = st.columns([1, 1, 3])
    
        with s1:
            actif_sgb = (st.session_state.site_exig_sel == "SGB")
            if st.button("🏢 SGB", use_container_width=True, type="primary" if actif_sgb else "secondary"):
                st.session_state.site_exig_sel = "SGB"
                st.session_state.cat_exig_sel = None  # Reset la catégorie si on change de site
                st.rerun()
            
        with s2:
            actif_meg = (st.session_state.site_exig_sel == "MEG")
            if st.button("🏢 MEG", use_container_width=True, type="primary" if actif_meg else "secondary"):
                st.session_state.site_exig_sel = "MEG"
                st.session_state.cat_exig_sel = None  # Reset la catégorie si on change de site
                st.rerun()

    # --- CORRECTION DE LA LOGIQUE D'AFFICHAGE ---
    # On se base TOUJOURS sur le session_state actuel, pas sur le clic du bouton direct
        if st.session_state.site_exig_sel:
            site_sel = st.session_state.site_exig_sel
            st.markdown(f"<p style='font-size:13px;color:#64748B;font-weight:600;margin:16px 0 8px 0;'>Catégories — Site {site_sel} :</p>", unsafe_allow_html=True)

            df_site = df_equip[df_equip["Site"] == site_sel] if not df_equip.empty else pd.DataFrame()

            NOMS_COURTS_CAT = {
                "Installations électriques": "⚡ Électriques",
                "Equipements de levage":     "🏗️ Levage",
                "Sécurité incendie":         "🔥 Incendie",
                "Installations de gaz":      "🔵 Gaz",
                "Appareil pression de gaz":  "⚙️ Pression gaz",
            }

        # Création dynamique des boutons de catégories
            cat_cols = st.columns(5)
            for i, (cat, couleur) in enumerate(COULEURS_CAT.items()):
                with cat_cols[i % 5]:
                    nb_total_cat = int(df_site[df_site["Categorie"] == cat]["Nombre"].sum()) if not df_site.empty else 0
                    actif_cat = (st.session_state.cat_exig_sel == cat)
                    label_court = NOMS_COURTS_CAT.get(cat, cat)
                
                    if st.button(f"{label_court} ({nb_total_cat})", key=f"cat_btn_{cat}", use_container_width=True,
                                 type="primary" if actif_cat else "secondary",
                                 help=f"{nb_total_cat} équipement(s) au total"):
                        st.session_state.cat_exig_sel = cat
                        st.rerun()

        # Niveau 3 : sous-équipements de la catégorie choisie
            if st.session_state.cat_exig_sel:
                cat_sel = st.session_state.cat_exig_sel
                st.markdown(f"<p style='font-size:13px;color:#64748B;font-weight:600;margin:16px 0 8px 0;'>Sous-équipements — {cat_sel} ({site_sel}) :</p>", unsafe_allow_html=True)

                df_cat = df_site[df_site["Categorie"] == cat_sel] if not df_site.empty else pd.DataFrame()
                couleur_cat = COULEURS_CAT.get(cat_sel, "#94a3b8")

                if df_cat.empty:
                    st.info(f"Aucun sous-équipement enregistré pour {cat_sel} sur le site {site_sel}.")
                else:
                    eq_cols = st.columns(3)
                    for idx, (_, row_eq) in enumerate(df_cat.iterrows()):
                        with eq_cols[idx % 3]:
                            st.markdown(
                                f"<div style='background:white;border-left:4px solid {couleur_cat};"
                                "padding:14px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.05);margin-bottom:10px;'>"
                                f"<p style='margin:0;font-size:13px;font-weight:600;color:#1E293B;'>{row_eq.get('Sous_equipement','')}</p>"
                                f"<p style='margin:6px 0 0 0;font-size:24px;font-weight:800;color:{couleur_cat};'>{int(row_eq.get('Nombre',0))}</p>"
                                "</div>", unsafe_allow_html=True)

            # Gestion (ajout/suppression) — responsable uniquement
                if role == "Responsable" and password_correct:
                    with st.expander("✏️ Gérer les sous-équipements (Responsable)"):
                        st.markdown("**Ajouter un sous-équipement :**")
                        ac1, ac2, ac3 = st.columns([2, 1, 1])
                        with ac1:
                            nouv_seq = st.text_input("Nom du sous-équipement", key="nouv_seq_nom")
                        with ac2:
                            nouv_nb = st.number_input("Nombre", min_value=1, value=1, key="nouv_seq_nb")
                        with ac3:
                            st.write("")
                            st.write("")
                            if st.button("➕ Ajouter", use_container_width=True):
                                if nouv_seq.strip():
                                    ok, err = ajouter_equipement(site_sel, cat_sel, nouv_seq.strip(), nouv_nb)
                                    if ok:
                                        st.success("✅ Ajouté !")
                                        st.rerun()
                                    else:
                                        st.error(f"Erreur : {err}")
                                else:
                                    st.warning("Veuillez saisir un nom.")

                        if not df_cat.empty:
                            st.markdown("<br>**Supprimer un sous-équipement :**", unsafe_allow_html=True)
                            for orig_idx, row_eq in df_cat.iterrows():
                                dc1, dc2 = st.columns([5, 1])
                                with dc1:
                                    st.write(f"{row_eq.get('Sous_equipement','')} — {int(row_eq.get('Nombre',0))} unité(s)")
                                with dc2:
                                    if st.button("🗑️", key=f"del_eq_{orig_idx}"):
                                        num_ligne_sheet = orig_idx + 2
                                        if supprimer_equipement_ligne(num_ligne_sheet):
                                            st.success("Supprimé !")
                                            st.cache_data.clear()
                                            st.rerun()
                                        else:
                                            st.error("Erreur lors de la suppression.")
        else:
            st.info("👆 Sélectionnez un site (SGB ou MEG) pour voir les catégories d'équipements.")

        st.divider()

        if not df_exig.empty:
            st.markdown("### 📥 Téléchargement des check-lists")
        
            col_sgb, col_meg = st.columns(2)
            date_str = datetime.date.today().strftime('%d_%m_%Y')
        
            with col_sgb:
                with st.spinner("Préparation du rapport SGB..."):
                    try:
                        pdf_sgb = generer_rapport_equipements_pdf(df_exig, "SGB")
                        st.download_button(
                            label="📄 Rapport PDF — SGB",
                            data=pdf_sgb,
                            file_name=f"Rapport_Inspection_SGB_{date_str}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erreur PDF SGB : {e}")
                    
            with col_meg:
                with st.spinner("Préparation du rapport MEG..."):
                    try:
                        pdf_meg = generer_rapport_equipements_pdf(df_exig, "MEG")
                        st.download_button(
                            label="📄 Rapport PDF — MEG",
                            data=pdf_meg,
                            file_name=f"Rapport_Inspection_MEG_{date_str}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erreur PDF MEG : {e}")
                    


    

    
    # ---- ONGLET 3 : PRÉSENCE & VISITES ----
    if tab3 and role=="Responsable" and password_correct:
        with tab3:
            st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#1E3A8A;'>👥 Suivi des visites & Présence en temps réel</p>",unsafe_allow_html=True)
            col_r,_=st.columns([1,5])
            with col_r:
                if st.button("🔄"): st.rerun()
            st.markdown("### 🟢 Présence en temps réel")
            with st.spinner("Chargement..."):
                df_presence=lire_presence()
            if df_presence.empty:
                st.info("Aucun visiteur enregistré.")
            else:
                nb_en_ligne=len(df_presence[df_presence["Statut"].str.contains("🟢")])
                nb_recent  =len(df_presence[df_presence["Statut"].str.contains("🟡")])
                nb_offline =len(df_presence[df_presence["Statut"].str.contains("🔴")])
                p1,p2,p3=st.columns(3)
                with p1:
                    st.markdown(f"""<div style="background:#F0FDF4;padding:16px;border-radius:10px;border-left:4px solid #10B981;margin-bottom:16px;">
                        <p style="margin:0;font-size:11px;color:#064E3B;font-weight:700;text-transform:uppercase;">🟢 En ligne</p>
                        <p style="margin:4px 0 0 0;font-size:32px;color:#065F46;font-weight:800;">{nb_en_ligne}</p></div>""",unsafe_allow_html=True)
                with p2:
                    st.markdown(f"""<div style="background:#FFFBEB;padding:16px;border-radius:10px;border-left:4px solid #F59E0B;margin-bottom:16px;">
                        <p style="margin:0;font-size:11px;color:#78350F;font-weight:700;text-transform:uppercase;">🟡 Récemment actif</p>
                        <p style="margin:4px 0 0 0;font-size:32px;color:#92400E;font-weight:800;">{nb_recent}</p></div>""",unsafe_allow_html=True)
                with p3:
                    st.markdown(f"""<div style="background:#FEF2F2;padding:16px;border-radius:10px;border-left:4px solid #EF4444;margin-bottom:16px;">
                        <p style="margin:0;font-size:11px;color:#7F1D1D;font-weight:700;text-transform:uppercase;">🔴 Hors ligne</p>
                        <p style="margin:4px 0 0 0;font-size:32px;color:#991B1B;font-weight:800;">{nb_offline}</p></div>""",unsafe_allow_html=True)
                st.dataframe(df_presence,column_config={
                    "Email":st.column_config.TextColumn("📧 Visiteur"),
                    "Dernière activité":st.column_config.TextColumn("🕐 Dernière activité"),
                    "Statut":st.column_config.TextColumn("Statut"),
                    "Activité":st.column_config.TextColumn("⏱️ Détail")},
                    hide_index=True,use_container_width=True)

            st.markdown("<br>",unsafe_allow_html=True)
            st.markdown("### 📋 Historique complet des accès")
            with st.spinner("Chargement des logs..."):
                df_logs=lire_logs()
            if df_logs.empty:
                st.info("Aucun log enregistré.")
            else:
                nb_total=len(df_logs)
                col_em=[c for c in df_logs.columns if "email" in c.lower() or "mail" in c.lower()]
                nb_uniq=df_logs[col_em[0]].nunique() if col_em else 0
                l1,l2=st.columns(2)
                with l1:
                    st.markdown(f"""<div style="background:white;padding:16px;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.05);border-left:4px solid #1E3A8A;margin-bottom:16px;">
                        <p style="margin:0;font-size:11px;color:#64748B;font-weight:600;text-transform:uppercase;">Total visites</p>
                        <p style="margin:4px 0 0 0;font-size:28px;color:#0F172A;font-weight:700;">{nb_total}</p></div>""",unsafe_allow_html=True)
                with l2:
                    st.markdown(f"""<div style="background:white;padding:16px;border-radius:10px;box-shadow:0 2px 6px rgba(0,0,0,0.05);border-left:4px solid #0EA5E9;margin-bottom:16px;">
                        <p style="margin:0;font-size:11px;color:#64748B;font-weight:600;text-transform:uppercase;">Visiteurs uniques</p>
                        <p style="margin:4px 0 0 0;font-size:28px;color:#0F172A;font-weight:700;">{nb_uniq}</p></div>""",unsafe_allow_html=True)
                st.dataframe(df_logs,column_config={
                    "Date":st.column_config.TextColumn("📅 Date & Heure"),
                    "Email":st.column_config.TextColumn("📧 E-mail")},
                    hide_index=True,use_container_width=True)

    # ---- ONGLET 4 : KPI (Responsable uniquement) ----
    if tab_kpi and role=="Responsable" and password_correct:
        with tab_kpi:
            st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#1E3A8A;'>📊 Indicateurs clés de performance (KPI)</p>",unsafe_allow_html=True)
            col_r_kpi,_=st.columns([1,5])
            with col_r_kpi:
                if st.button("🔄",key="refresh_kpi"): st.cache_data.clear(); st.rerun()

            # ---- Préparation des données de contrôle (même logique que l'onglet Planification) ----
            col_cat_k   = [c for c in df_rapports.columns if "cat" in c.lower()]
            col_date_k  = [c for c in df_rapports.columns if "date" in c.lower()]
            col_site_k  = [c for c in df_rapports.columns if "site" in c.lower()]
            col_label_k = [c for c in df_rapports.columns if "equip" in c.lower() or "label" in c.lower() or "nom" in c.lower()]
            col_reelle_k= [c for c in df_rapports.columns if "reelle" in c.lower() or "réelle" in c.lower()]

            if df_rapports.empty or not col_cat_k or not col_date_k:
                st.info("Données insuffisantes dans l'onglet « Rapports » pour calculer les KPI.")
                kpi_data = None
            else:
                df_k = df_rapports.copy()
                df_k["_date_brute"]  = pd.to_datetime(df_k[col_date_k[0]], dayfirst=True, errors='coerce')
                df_k["_date_reelle"] = pd.to_datetime(df_k[col_reelle_k[0]], dayfirst=True, errors='coerce') if col_reelle_k else pd.NaT
                df_k = df_k.dropna(subset=["_date_brute"])

                cles_k=[]
                if col_site_k:  cles_k.append(col_site_k[0])
                cles_k.append(col_cat_k[0])
                if col_label_k: cles_k.append(col_label_k[0])
                df_k = df_k.sort_values("_date_brute", ascending=True)
                df_k = df_k.drop_duplicates(subset=cles_k, keep="last")

                # ---- KPI 1 : Taux de réalisation 2026 (échéances théoriques comprises entre 01/01/2026 et 31/12/2026) ----
                df_2026 = df_k[df_k["_date_brute"].dt.year == 2026]
                nb_total_2026    = len(df_2026)
                nb_realises_2026 = int(df_2026["_date_reelle"].notna().sum())
                nb_restants_2026 = nb_total_2026 - nb_realises_2026
                taux1 = round(nb_realises_2026/nb_total_2026*100,1) if nb_total_2026>0 else 0

                # ---- KPI 2 : Taux planifié — dates réelles saisies vs estimées via la dernière visite ----
                nb_total_all   = len(df_k)
                nb_avec_reelle = int(df_k["_date_reelle"].notna().sum())
                nb_estimes     = nb_total_all - nb_avec_reelle
                taux2 = round(nb_avec_reelle/nb_total_all*100,1) if nb_total_all>0 else 0

                # ---- KPI 3 : Taux de respect de délai de visite (écart ≤ 3j vs échéance théorique initiale) ----
                df_realises_k = df_k[df_k["_date_reelle"].notna()].copy()
                nb_visites_realisees = len(df_realises_k)
                if nb_visites_realisees > 0:
                    df_realises_k["_ecart"] = (df_realises_k["_date_reelle"] - df_realises_k["_date_brute"]).dt.days.abs()
                    nb_respectes = int((df_realises_k["_ecart"] <= 3).sum())
                else:
                    nb_respectes = 0
                nb_non_respectes = nb_visites_realisees - nb_respectes
                taux3 = round(nb_respectes/nb_visites_realisees*100,1) if nb_visites_realisees>0 else 0

                kpi_data = {
                    "kpi1": {"taux":taux1, "realises":nb_realises_2026, "restants":nb_restants_2026, "total":nb_total_2026},
                    "kpi2": {"taux":taux2, "avec_reelle":nb_avec_reelle, "estimes":nb_estimes, "total":nb_total_all},
                    "kpi3": {"taux":taux3, "respectes":nb_respectes, "non_respectes":nb_non_respectes, "total":nb_visites_realisees},
                }

                k1c,k2c,k3c = st.columns(3)

                with k1c:
                    st.markdown("<p style='text-align:center;font-weight:600;color:#1E293B;font-size:14px;'>Taux de réalisation 2026</p>",unsafe_allow_html=True)
                    if nb_total_2026>0:
                        dfp1=pd.DataFrame({"Statut":["Réalisés","Restants"],"Nombre":[nb_realises_2026,nb_restants_2026]})
                        fig1=px.pie(dfp1,values="Nombre",names="Statut",hole=0.6,color="Statut",
                                    color_discrete_map={"Réalisés":"#10B981","Restants":"#EF4444"})
                        fig1.update_traces(textposition='inside',textinfo='percent+label')
                        fig1.update_layout(margin=dict(t=10,b=10,l=10,r=10),height=260,showlegend=False,
                                            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig1,use_container_width=True,config={'displayModeBar':False})
                        st.markdown(f"<p style='text-align:center;font-size:13px;color:#64748B;'>{taux1}% réalisés ({nb_realises_2026}/{nb_total_2026})</p>",unsafe_allow_html=True)
                    else:
                        st.info("Aucun contrôle avec échéance théorique en 2026.")

                with k2c:
                    st.markdown("<p style='text-align:center;font-weight:600;color:#1E293B;font-size:14px;'>Taux planifié</p>",unsafe_allow_html=True)
                    if nb_total_all>0:
                        dfp2=pd.DataFrame({"Statut":["Date réelle saisie","Estimée (dernière visite)"],"Nombre":[nb_avec_reelle,nb_estimes]})
                        fig2=px.pie(dfp2,values="Nombre",names="Statut",hole=0.6,color="Statut",
                                    color_discrete_map={"Date réelle saisie":"#1E3A8A","Estimée (dernière visite)":"#F59E0B"})
                        fig2.update_traces(textposition='inside',textinfo='percent+label')
                        fig2.update_layout(margin=dict(t=10,b=10,l=10,r=10),height=260,showlegend=False,
                                            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig2,use_container_width=True,config={'displayModeBar':False})
                        st.markdown(f"<p style='text-align:center;font-size:13px;color:#64748B;'>{taux2}% avec date réelle ({nb_avec_reelle}/{nb_total_all})</p>",unsafe_allow_html=True)
                    else:
                        st.info("Aucune donnée disponible.")

                with k3c:
                    st.markdown("<p style='text-align:center;font-weight:600;color:#1E293B;font-size:14px;'>Respect délai de visite (≤3j)</p>",unsafe_allow_html=True)
                    if nb_visites_realisees>0:
                        dfp3=pd.DataFrame({"Statut":["Respecté","Non respecté"],"Nombre":[nb_respectes,nb_non_respectes]})
                        fig3=px.pie(dfp3,values="Nombre",names="Statut",hole=0.6,color="Statut",
                                    color_discrete_map={"Respecté":"#0EA5E9","Non respecté":"#EF4444"})
                        fig3.update_traces(textposition='inside',textinfo='percent+label')
                        fig3.update_layout(margin=dict(t=10,b=10,l=10,r=10),height=260,showlegend=False,
                                            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig3,use_container_width=True,config={'displayModeBar':False})
                        st.markdown(f"<p style='text-align:center;font-size:13px;color:#64748B;'>{taux3}% respecté ({nb_respectes}/{nb_visites_realisees})</p>",unsafe_allow_html=True)
                    else:
                        st.info("Aucune visite réalisée à ce jour.")

            st.markdown("<br><hr style='border-color:#E2E8F0;'>",unsafe_allow_html=True)

            # ================= TAUX DE NON-CONFORMITÉ DE SITE (CARTOGRAPHIE) =================
            st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#0F172A;'>🗺️ Taux de non-conformité de site</p>",unsafe_allow_html=True)

            carto_b64 = _charger_cartographie_b64()
            if carto_b64:
                vc1,vc2 = st.columns([5,1])
                with vc2:
                    st.markdown(f"<a href='{LUCID_CARTOGRAPHIE_URL}' target='_blank' style='display:inline-block;background:#1E3A8A;color:white;padding:8px 14px;border-radius:8px;text-decoration:none;font-weight:600;font-size:13px;text-align:center;'>🔗 Ouvrir dans Lucid</a>",unsafe_allow_html=True)
                components.html(f"""
                <div id="carto-viewer" style="position:relative;width:100%;height:620px;overflow:hidden;
                     background:#F8FAFC;border:1px solid #E2E8F0;border-radius:12px;">
                  <img id="carto-img" src="data:image/png;base64,{carto_b64}"
                       style="position:absolute;top:0;left:0;transform-origin:0 0;cursor:grab;user-select:none;max-width:none;visibility:hidden;"
                       draggable="false"/>
                  <div style="position:absolute;bottom:14px;right:14px;display:flex;gap:8px;z-index:10;">
                    <button id="carto-zoom-in" style="width:36px;height:36px;border-radius:8px;border:1px solid #CBD5E1;background:white;font-size:16px;font-weight:700;cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,0.08);">➕</button>
                    <button id="carto-zoom-out" style="width:36px;height:36px;border-radius:8px;border:1px solid #CBD5E1;background:white;font-size:16px;font-weight:700;cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,0.08);">➖</button>
                    <button id="carto-reset" style="width:36px;height:36px;border-radius:8px;border:1px solid #CBD5E1;background:white;font-size:15px;cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,0.08);">⟳</button>
                  </div>
                  <div style="position:absolute;top:10px;left:14px;font-size:11px;color:#64748B;background:rgba(255,255,255,0.85);
                       padding:4px 10px;border-radius:6px;">🖱️ Molette pour zoomer • Glisser pour déplacer</div>
                </div>
                <script>
                (function(){{
                    let baseScale=1, scale=1, posX=0, posY=0, isDragging=false, startX=0, startY=0;
                    const viewer=document.getElementById('carto-viewer');
                    const img=document.getElementById('carto-img');

                    function apply(){{ img.style.transform = 'translate('+posX+'px,'+posY+'px) scale('+scale+')'; }}

                    function fitToView(){{
                        const cw = viewer.clientWidth, ch = viewer.clientHeight;
                        const nw = img.naturalWidth, nh = img.naturalHeight;
                        if(!nw || !nh) return;
                        baseScale = Math.min(cw/nw, ch/nh);
                        scale = baseScale;
                        posX = (cw - nw*scale)/2;
                        posY = (ch - nh*scale)/2;
                        img.style.visibility = 'visible';
                        apply();
                    }}

                    function zoom(factor){{
                        scale*=factor;
                        scale=Math.max(baseScale*0.9, Math.min(scale, baseScale*8));
                        apply();
                    }}

                    if(img.complete && img.naturalWidth){{ fitToView(); }}
                    img.addEventListener('load', fitToView);

                    document.getElementById('carto-zoom-in').addEventListener('click', function(){{ zoom(1.25); }});
                    document.getElementById('carto-zoom-out').addEventListener('click', function(){{ zoom(0.8); }});
                    document.getElementById('carto-reset').addEventListener('click', fitToView);
                    img.addEventListener('wheel', function(e){{
                        e.preventDefault();
                        zoom(e.deltaY<0 ? 1.1 : 0.9);
                    }}, {{passive:false}});
                    img.addEventListener('mousedown', function(e){{ isDragging=true; startX=e.clientX-posX; startY=e.clientY-posY; img.style.cursor='grabbing'; }});
                    window.addEventListener('mouseup', function(){{ isDragging=false; img.style.cursor='grab'; }});
                    window.addEventListener('mousemove', function(e){{ if(!isDragging) return; posX=e.clientX-startX; posY=e.clientY-startY; apply(); }});
                }})();
                </script>
                """, height=630, scrolling=False)
            else:
                st.warning("⚠️ Fichier « Cartographie.png » introuvable. Placez-le dans le même dossier que l'application (à côté de app.py) pour l'afficher ici.")
                st.markdown(f"[🔗 Consulter la cartographie sur Lucid]({LUCID_CARTOGRAPHIE_URL})")

            st.markdown("<br><hr style='border-color:#E2E8F0;'>",unsafe_allow_html=True)

            # ================= POINTS DE RÉSERVE =================
            st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#0F172A;'>📌 Points de réserve</p>",unsafe_allow_html=True)

            with st.spinner("Chargement des points de réserve..."):
                df_reserve = lire_points_reserve()

            with st.expander("➕ Ajouter un point de réserve"):
                r1,r2,r3,r4 = st.columns([1,1.5,1.5,1])
                with r1:
                    res_site = st.selectbox("Site",["SGB","MEG"],key="res_site_new")
                with r2:
                    res_cat = st.selectbox("Catégorie",list(PERIODICITE.keys()),key="res_cat_new")
                with r3:
                    res_seq = st.text_input("Sous-équipement",key="res_seq_new")
                with r4:
                    res_nb = st.number_input("Nb points",min_value=1,value=1,key="res_nb_new")
                if st.button("💾 Enregistrer",key="btn_add_reserve"):
                    if res_seq.strip():
                        ok,err = ajouter_point_reserve(res_site,res_cat,res_seq.strip(),res_nb)
                        if ok:
                            st.success("✅ Point de réserve ajouté !")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Erreur : {err}")
                    else:
                        st.warning("Veuillez saisir un sous-équipement.")

            if df_reserve.empty:
                st.info("Aucun point de réserve enregistré. Utilisez le formulaire ci-dessus pour en ajouter.")
            else:
                if "Nombre" in df_reserve.columns:
                    df_reserve["Nombre"] = pd.to_numeric(df_reserve["Nombre"],errors="coerce").fillna(0).astype(int)

                with st.container(border=True):
                    st.markdown("<p style='font-weight:600;color:#1E293B;margin:0 0 10px 0;font-size:13px;'>🔍 Filtrer les points de réserve</p>",unsafe_allow_html=True)
                    fr1,fr2,fr3 = st.columns(3)
                    sites_dispo = ["Tous"]+sorted(df_reserve["Site"].dropna().unique().tolist()) if "Site" in df_reserve.columns else ["Tous"]
                    cats_dispo  = ["Tous"]+sorted(df_reserve["Categorie"].dropna().unique().tolist()) if "Categorie" in df_reserve.columns else ["Tous"]
                    with fr1: f_res_site = st.selectbox("Site",sites_dispo,key="f_res_site")
                    with fr2: f_res_cat  = st.selectbox("Catégorie",cats_dispo,key="f_res_cat")
                    with fr3: f_res_seq  = st.text_input("Recherche sous-équipement",key="f_res_seq")

                df_reserve_f = df_reserve.copy()
                if f_res_site!="Tous" and "Site" in df_reserve_f.columns:
                    df_reserve_f = df_reserve_f[df_reserve_f["Site"]==f_res_site]
                if f_res_cat!="Tous" and "Categorie" in df_reserve_f.columns:
                    df_reserve_f = df_reserve_f[df_reserve_f["Categorie"]==f_res_cat]
                if f_res_seq.strip() and "Sous_equipement" in df_reserve_f.columns:
                    df_reserve_f = df_reserve_f[df_reserve_f["Sous_equipement"].astype(str).str.contains(f_res_seq.strip(),case=False,na=False)]

                st.dataframe(df_reserve_f.rename(columns={
                    "Site":"Site","Categorie":"Catégorie","Sous_equipement":"Sous équipement","Nombre":"Nbre points de réserve"
                }),hide_index=True,use_container_width=True)

                st.markdown("<br>",unsafe_allow_html=True)
                gr1,gr2 = st.columns(2)
                with gr1:
                    if "Site" in df_reserve_f.columns and not df_reserve_f.empty:
                        df_by_site = df_reserve_f.groupby("Site")["Nombre"].sum().reset_index()
                        figS = px.pie(df_by_site,values="Nombre",names="Site",hole=0.6,
                                      color_discrete_sequence=['#1E3A8A','#0EA5E9','#94A3B8'])
                        figS.update_traces(textposition='inside',textinfo='percent+label')
                        figS.update_layout(title="Répartition par site",margin=dict(t=40,b=10,l=10,r=10),height=280,
                                            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(figS,use_container_width=True,config={'displayModeBar':False})
                    else:
                        st.info("Aucune donnée à afficher pour le graphe par site.")
                with gr2:
                    if "Categorie" in df_reserve_f.columns and not df_reserve_f.empty:
                        df_by_cat = df_reserve_f.groupby("Categorie")["Nombre"].sum().reset_index()
                        figC = px.pie(df_by_cat,values="Nombre",names="Categorie",hole=0.6,
                                      color_discrete_sequence=px.colors.qualitative.Set2)
                        figC.update_traces(textposition='inside',textinfo='percent')
                        figC.update_layout(title="Répartition par catégorie",margin=dict(t=40,b=10,l=10,r=10),height=280,
                                            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(figC,use_container_width=True,config={'displayModeBar':False})
                    else:
                        st.info("Aucune donnée à afficher pour le graphe par catégorie.")

                with st.expander("🗑️ Supprimer un point de réserve"):
                    for orig_idx,row_r in df_reserve.iterrows():
                        dcx1,dcx2 = st.columns([5,1])
                        with dcx1:
                            st.write(f"{row_r.get('Site','')} — {row_r.get('Categorie','')} — {row_r.get('Sous_equipement','')} — {row_r.get('Nombre',0)} pt(s)")
                        with dcx2:
                            if st.button("🗑️",key=f"del_res_{orig_idx}"):
                                num_ligne_sheet = orig_idx+2
                                if supprimer_ligne_generique("PointsReserve",num_ligne_sheet,4):
                                    st.success("Supprimé !")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("Erreur lors de la suppression.")

            # ================= RAPPORT PDF PREMIUM =================
            st.markdown("<br><hr style='border-color:#E2E8F0;'>",unsafe_allow_html=True)
            st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#0F172A;'>📄 Rapport PDF </p>",unsafe_allow_html=True)
           
            if kpi_data is None:
                st.info("Le rapport PDF nécessite des données KPI disponibles (onglet « Rapports » non vide).")
            else:
                with st.spinner("Préparation du rapport PDF..."):
                    try:
                        pdf_kpi = generer_rapport_kpi_pdf(
                            kpi_data,
                            df_reserve,
                            carto_b64,
                            "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6q1BtDSDgVnJZFo0hOBfQJoDS6OYiub-qfQ&s"
                        )
                        st.download_button(
                            label="📄 Télécharger le rapport PDF",
                            data=pdf_kpi,
                            file_name=f"Rapport_KPI_{datetime.date.today().strftime('%d_%m_%Y')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Erreur lors de la génération du PDF : {e}")
