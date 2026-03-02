import streamlit as st

st.set_page_config(page_title="Calculateur Extrusion TPR", page_icon="📟", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        /* On rend le header système visible pour la flèche mobile */
        header {
            visibility: visible !important;
            height: 60px !important;
        }
        
        /* --- CONFIGURATION PC (Par défaut) --- */
        .block-container {
            padding-top: 5rem !important; /* On augmente ici pour éviter le crop PC */
            padding-bottom: 2rem !important;
            padding-left: 5rem !important;
            padding-right: 5rem !important;
        }
        /* --- LOGIQUE DE CENTRAGE PC --- */
        .header-container {
            text-align: center;
            margin-bottom: 2rem;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }

        .header-logo img {
            transition: transform 0.3s ease;
        }
        .header-logo img:hover {
            transform: scale(1.05);
        }

        /* --- CONFIGURATION SMARTPHONE --- */
        @media (max-width: 768px) {
            .block-container {
                padding-top: 3.5rem !important; /* Un peu moins pour mobile pour garder votre 'très bon' rendu */
                padding-left: 1.5rem !important;
                padding-right: 1.5rem !important;
            }
            
            [data-testid="stImage"] {
                margin-top: 10px !important;
            }
        }

        /* Sécurité pour l'image (Logo) */
        [data-testid="stImage"] img {
            max-width: 100%;
            height: auto;
            object-fit: contain !important;
        }
       /* Style des barres de visualisation */
        .container-barre { width: 100%; background-color: #e0e0e0; border-radius: 5px; height: 20px; position: relative;}
        .barre-lopin { background-color: #808080; height: 100%; border-radius: 5px; transition: width 0.5s;}
        .barre-limite { background-color: #1a4332; height: 8px; border-radius: 5px; margin-top: 4px;}
        
       /* --- BOUTON CALCULER PREMIUM --- */
        div.stButton > button {
            width: 100%; 
            height: 3.8em;
            border-radius: 12px;
            border: none;
            
            /* Dégradé de bleu professionnel */
            background: linear-gradient(135deg, #0047AB 0%, #00264d 100%);
            color: white !important;
            font-size: 18px !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px;
            
            /* Ombre portée pour le relief */
            box-shadow: 0 4px 15px rgba(0, 71, 171, 0.3);
            transition: all 0.3s ease-in-out;
            cursor: pointer;
        }

        /* --- EFFET AU SURVOL (HOVER) --- */
        div.stButton > button:hover {
            background: linear-gradient(135deg, #0056d6 0%, #0047AB 100%) !important;
            color: white !important;
            box-shadow: 0 6px 20px rgba(0, 71, 171, 0.5) !important;
            transform: translateY(-2px); /* Le bouton remonte légèrement */
            border: none !important;
        }

        /* --- EFFET AU CLIC (ACTIVE) --- */
        div.stButton > button:active {
            transform: translateY(1px) scale(0.98);
            box-shadow: 0 2px 10px rgba(0, 71, 171, 0.2) !important;
        }
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
# --- EN-TÊTE CENTRÉ (LOGO + NOM + DIRECTION) ---
st.markdown(f"""
    <div class="header-container">
        <div class="header-logo">
            <img src="https://scontent.fnbe1-2.fna.fbcdn.net/v/t39.30808-6/408929007_749166663924252_578772537697061170_n.jpg?_nc_cat=101&ccb=1-7&_nc_sid=1d70fc&_nc_ohc=outSX1TrNzMQ7kNvwH8dLos&_nc_oc=AdnayidTjVde0oO8dBewwk-Vo1bwbpm9MvDcBijNWzBt6b_52O9jssFyIDcLrqtW-bk&_nc_zt=23&_nc_ht=scontent.fnbe1-2.fna&_nc_gid=mw-_AZkaw4Oh_IX1S6ObVQ&oh=00_AfuIu1RSs4hY2piAZBZvukecG5Pl97xctCOBml-nIqgrIQ&oe=69A62B8A" width="140">
        </div>
        <h1 style="color:#00264d; margin-top:15px; margin-bottom:5px;">Tunisie Profilés d'Aluminium</h1>
        <p style="color:#64748b; font-size:1.2rem; margin-bottom:0;">Direction Maintenance et Travaux Neufs</p>
    </div>
    <hr style="margin-bottom: 2rem; opacity: 0.1;">
""", unsafe_allow_html=True)
    
if presse_choisie:
    conf = CONFIG_PRESSES[presse_choisie]
    st.success(f"**{presse_choisie}** active")
    st.info(f"📏 Limite : {conf['limite_longueur']} mm\n\n⭕ Diamètre : {conf['diametre']} mm")
else:
    st.warning("Veuillez sélectionner une presse.")

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
