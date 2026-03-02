import streamlit as st

st.set_page_config(page_title="Calculateur Extrusion TPR", page_icon="📟", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        /* Masquage du header Streamlit */
        header {visibility: hidden; height: 0px;}
        [data-testid="stHeader"] {display: none;}
        
        /* Configuration de base pour PC */
        .block-container {
            padding-top: 2rem !important; 
            padding-bottom: 1rem !important;
            padding-left: 5rem !important;
            padding-right: 5rem !important;
        }

        /* AJUSTEMENTS POUR SMARTPHONES (Écrans < 768px) */
        @media (max-width: 768px) {
            .block-container {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                padding-top: 1rem !important;
            }
            h2 { font-size: 1.2rem !important; }
            h4 { font-size: 0.9rem !important; }
            .stMetric { margin-bottom: 10px !important; }
        }

        /* Fix pour le logo */
        [data-testid="stImage"] img {
            max-width: 100%;
            height: auto;
            object-fit: contain !important;
        }

        /* Style des barres de visualisation */
        .container-barre { width: 100%; background-color: #e0e0e0; border-radius: 5px; height: 20px; position: relative;}
        .barre-lopin { background-color: #808080; height: 100%; border-radius: 5px; transition: width 0.5s;}
        .barre-limite { background-color: #1a4332; height: 8px; border-radius: 5px; margin-top: 4px;}
        
        /* Style du bouton */
        div.stButton > button {width: 100%; font-weight: bold; background-color: #0047AB; color: white; border: none; height: 3.5em; border-radius: 8px;}
    </style>
    """, unsafe_allow_html=True)
CONFIG_PRESSES = {
    "Presse 4": {"diametre": 228, "limite_longueur": 1150},
    "Presse 6": {"diametre": 178, "limite_longueur": 890},
    "Presse 7": {"diametre": 178, "limite_longueur": 1000},
}

with st.sidebar:
    st.header("⚙️ Configuration Machine")
    presse_choisie = st.selectbox(
        "Sélectionnez la Presse :",
        options=list(CONFIG_PRESSES.keys()),
        index=None,
        placeholder="Choisir une presse..."
    )
    
    if presse_choisie:
        conf = CONFIG_PRESSES[presse_choisie]
        st.success(f"**{presse_choisie}** active")
        st.info(f"📏 Limite : {conf['limite_longueur']} mm\n\n⭕ Diamètre : {conf['diametre']} mm")
    else:
        st.warning("Veuillez sélectionner une presse.")

col_logo, col_titre = st.columns([1, 4])
with col_logo:
    st.image("https://scontent.fnbe1-2.fna.fbcdn.net/v/t39.30808-6/408929007_749166663924252_578772537697061170_n.jpg?_nc_cat=101&ccb=1-7&_nc_sid=1d70fc&_nc_ohc=outSX1TrNzMQ7kNvwH8dLos&_nc_oc=AdnayidTjVde0oO8dBewwk-Vo1bwbpm9MvDcBijNWzBt6b_52O9jssFyIDcLrqtW-bk&_nc_zt=23&_nc_ht=scontent.fnbe1-2.fna&_nc_gid=mw-_AZkaw4Oh_IX1S6ObVQ&oh=00_AfuIu1RSs4hY2piAZBZvukecG5Pl97xctCOBml-nIqgrIQ&oe=69A62B8A", width=150)

with col_titre:
    # Petit espacement pour centrer verticalement avec le logo
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("<h2 style='margin: 0;'>Tunisie Profilés d'Aluminium</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='margin: 0; color: #555;'>Direction Maintenance et Travaux Neufs</h4>", unsafe_allow_html=True)

st.markdown("<hr style='margin: 1.5rem 0;'>", unsafe_allow_html=True)

# --- LOGIQUE PRINCIPALE ---
if not presse_choisie:
    st.title("📟 Calculateur d'Extrusion")
    st.info("👈 Veuillez d'abord choisir une presse dans le menu à gauche.")
    st.stop()

st.title(f"📟 Calculateur - {presse_choisie}")

# --- ENTRÉES ---
st.markdown("##### 📥 Paramètres d'entrée")
col_in1, col_in2 = st.columns(2)

with col_in1:
    type_billette = st.selectbox("Nature de la billette :", ["Primaire", "Recyclée"])
    p_m = st.number_input("P/m du profilé (kg/m)", value=None, format="%.3f", placeholder="Ex: 1.25")

with col_in2:
    n_ecoulements = st.number_input("Nombre d'écoulements", min_value=1, step=1)
    long_demandee = st.number_input("Longueur écoulée demandée (m)", value=None, format="%.2f", placeholder="Ex: 47")

st.write("") 
st.divider()

# --- CALCULS ---
poids_lineique_billette = 110.180 

if st.button("🧮 CALCULER LES VALEURS OPTIMALES"):
    if p_m and long_demandee:
        diametre_presse = CONFIG_PRESSES[presse_choisie]["diametre"]
        limite_max = CONFIG_PRESSES[presse_choisie]["limite_longueur"]
        
        k = 0.1 if type_billette == "Primaire" else 0.16
        long_culot_mm = k * diametre_presse
        poids_lopin = ((p_m * n_ecoulements) * long_demandee) + (poids_lineique_billette * (long_culot_mm / 1000))
        long_lopin_mm = (poids_lopin / poids_lineique_billette) * 1000

        if long_lopin_mm > limite_max:
            st.error(f"🚨 Valeurs non valides pour la {presse_choisie}")
            st.markdown(
                f"""
                <div style="background-color: #ff4b4b; padding: 20px; border-radius: 10px; border: 2px solid white;">
                    <h2 style="color: white; margin: 0; text-align: center;">
                        ⚠️ LOPIN TROP LONG ({long_lopin_mm:.2f} mm)
                    </h2>
                    <p style="color: white; text-align: center; font-size: 1.2em; margin-top: 10px;">
                        La limite pour la <b>{presse_choisie}</b> est de <b>{limite_max} mm</b>.<br>
                         Merci de ressaisir les données.
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(f"### 📋 Consignes Opérateur - {presse_choisie}")
            res_col1, res_col2 = st.columns([1, 2])
            
            with res_col1:
                st.info(f"📏 **CULOT MINIMAL: {long_culot_mm:.2f} mm**")
                st.metric("POIDS DU LOPIN", f"{poids_lopin:.3f} kg")
                st.metric("LONGUEUR LOPIN OPTIMALE", f"{long_lopin_mm:.2f} mm")

            with res_col2:
                st.write("\n")
                pourcent = min((long_lopin_mm / limite_max) * 100, 100)
                st.write(f"📊 **Longueur du lopin : {long_lopin_mm:.1f} mm**")
                st.markdown(f'<div class="container-barre"><div class="barre-lopin" style="width: {pourcent}%;"></div></div>', unsafe_allow_html=True)
                
                st.write(f"🏁 **Longueur maximale du lopin {presse_choisie} ({limite_max} mm)**")
                st.markdown('<div class="barre-limite" style="width: 100%;"></div>', unsafe_allow_html=True)
                
                st.success(f"✅ Réglages validés pour la {presse_choisie}.")
    else:
        st.warning("⚠️ Information manquante : Remplissez les champs P/m et Longueur.")

# --- PIED DE PAGE ---
st.markdown("<div style='height: 60px;'></div>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div style="text-align: center; color: gray; font-size: 0.8em; border-top: 1px solid #eee; padding-top: 10px;">
        © 2026 TPR - Système d'Assistance Technique | {presse_choisie} <br>
        Développé pour l'assistance opérateur en extrusion <br>
        Direction Maintenance et Travaux Neufs - DMTN 
    </div>
    """, 
    unsafe_allow_html=True
)
