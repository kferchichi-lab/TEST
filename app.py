import streamlit as st

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Calculateur Extrusion TPR", page_icon="📟", layout="wide")

# --- CORRECTION DU "CROP" ET STYLE DES BARRES ---
st.markdown("""
    <style>
        /* Réduction de la marge supérieure pour éviter l'effet 'coupé' */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
        }
        /* Style des barres de visualisation */
        .container-barre { width: 100%; background-color: #e0e0e0; border-radius: 5px; height: 25px; position: relative;}
        .barre-lopin { background-color: #808080; height: 100%; border-radius: 5px; transition: width 0.5s;}
        .barre-limite { background-color: #1a4332; height: 10px; border-radius: 5px; margin-top: 5px;}
        
        /* Style du bouton Calculer */
        div.stButton > button {width: 100%; font-weight: bold; background-color: #0047AB; color: white;}
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURATION TECHNIQUE PAR PRESSE ---
CONFIG_PRESSES = {
    "Presse 4": {"diametre": 228, "limite_longueur": 1100},
    "Presse 6": {"diametre": 178, "limite_longueur": 890},
    "Presse 7": {"diametre": 178, "limite_longueur": 1000},
}

# --- BARRE LATÉRALE ---
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
        st.warning("Sélectionnez une presse.")

# --- EN-TÊTE (Correction alignement logo/texte) ---
col_logo, col_titre = st.columns([1, 5])
with col_logo:
    # Utilisation de votre lien TPR
    st.image("https://scontent.fnbe1-2.fna.fbcdn.net/v/t39.30808-6/408929007_749166663924252_578772537697061170_n.jpg?_nc_cat=101&ccb=1-7&_nc_sid=1d70fc&_nc_ohc=outSX1TrNzMQ7kNvwH8dLos&_nc_oc=AdnayidTjVde0oO8dBewwk-Vo1bwbpm9MvDcBijNWzBt6b_52O9jssFyIDcLrqtW-bk&_nc_zt=23&_nc_ht=scontent.fnbe1-2.fna&_nc_gid=mw-_AZkaw4Oh_IX1S6ObVQ&oh=00_AfuIu1RSs4hY2piAZBZvukecG5Pl97xctCOBml-nIqgrIQ&oe=69A62B8A", width=140)

with col_titre:
    st.markdown("<br>", unsafe_allow_html=True) # Aligne le texte au centre de l'image
    st.markdown("## Tunisie Profilés d'Aluminium")
    st.markdown("#### Direction Maintenance et Travaux Neufs")

st.markdown("---")

# Arrêt si aucune presse n'est sélectionnée
if not presse_choisie:
    st.title("📟 Calculateur d'Extrusion")
