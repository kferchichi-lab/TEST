import streamlit as st

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Calculateur Extrusion TPR", page_icon="📟", layout="wide")

# Style CSS pour les barres et l'ergonomie
st.markdown("""
    <style>
        .block-container {padding-top: 1.5rem;}
        .container-barre { width: 100%; background-color: #e0e0e0; border-radius: 5px; height: 25px; position: relative;}
        .barre-lopin { background-color: #808080; height: 100%; border-radius: 5px; transition: width 0.5s;}
        .barre-limite { background-color: #1a4332; height: 10px; border-radius: 5px; margin-top: 5px;}
        div.stButton > button {width: 100%; font-weight: bold; background-color: #0047AB; color: white;}
    </style>
    """, unsafe_allow_html=True)

# --- CONFIGURATION TECHNIQUE PAR PRESSE ---
CONFIG_PRESSES = {
    "Presse 4": {"diametre": 228, "limite_longueur": 1100},
    "Presse 6": {"diametre": 178, "limite_longueur": 890},
    "Presse 7": {"diametre": 178, "limite_longueur": 1000},
}

# --- BARRE LATÉRALE (CHOIX DE LA PRESSE) ---
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

# --- ENTÊTE ---
col_logo, col_titre = st.columns([1, 4])
with col_logo:
    # Utilisation de votre lien image TPR
    st.image("https://scontent.fnbe1-2.fna.fbcdn.net/v/t39.30808-6/408929007_749166663924252_578772537697061170_n.jpg?_nc_cat=101&ccb=1-7&_nc_sid=1d70fc&_nc_ohc=outSX1TrNzMQ7kNvwH8dLos&_nc_oc=AdnayidTjVde0oO8dBewwk-Vo1bwbpm9MvDcBijNWzBt6b_52O9jssFyIDcLrqtW-bk&_nc_zt=23&_nc_ht=scontent.fnbe1-2.fna&_nc_gid=mw-_AZkaw4Oh_IX1S6ObVQ&oh=00_AfuIu1RSs4hY2piAZBZvukecG5Pl97xctCOBml-nIqgrIQ&oe=69A62B8A", width=120)

with col_titre:
    st.markdown("### Tunisie Profilés d'Aluminium")
    st.subheader("Direction Maintenance et Travaux Neufs")

st.markdown("---")

# Arrêt si aucune presse n'est sélectionnée
if not presse_choisie:
    st.title("📟 Calculateur d'Extrusion")
    st.info("👈 Veuillez d'abord choisir une presse dans le menu à gauche.")
    st.stop()

st.title(f"📟 Calculateur - {presse_choisie}")

# --- SECTION 1 : SAISIE DES DONNÉES ---
st.header("📥 Paramètres d'entrée")
col1, col2 = st.columns(2)

with col1:
    type_billette = st.selectbox("Nature de la billette :", ["Primaire", "Recyclée"])
    p_m = st.number_input("P/m du profilé (kg/m)", value=None, format="%.3f", placeholder="Ex: 1.25")

with col2:
    n_ecoulements = st.number_input("Nombre d'écoulements", min_value=1, step=1)
    long_demandee = st.number_input("Longueur écoulée demandée (m)", value=None, format="%.2f", placeholder="Ex: 47")

st.divider()

# --- SECTION 2 : CALCULS DYNAMIQUES ---
poids_lineique_billette = 110.180  # kg/m

if st.button("🧮 CALCULER LES VALEURS OPTIMALES"):
    if p_m and long_demandee:
        
        # Récupération des paramètres de la presse choisie
        diametre_presse = CONFIG_PRESSES[presse_choisie]["diametre"]
        limite_max = CONFIG_PRESSES[presse_choisie]["limite_longueur"]
        
        # Calcul du culot
        k = 0.1 if type_billette == "Primaire" else 0.16
        long_culot_mm = k * diametre_presse

        # Calcul du poids et de la longueur
        poids_lopin = ((p_m * n_ecoulements) * long_demandee) + (poids_lineique_billette * (long_culot_mm / 1000))
        long_lopin_mm = (poids_lopin / poids_lineique_billette) * 1000

        # Vérification de la sécurité
        if long_lopin_mm > limite_max:
            st.error(f"🚨 ALERTE SÉCURITÉ : {presse_choisie}")
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
                st.info(f"📏 **CULOT : {long_culot_mm:.2f} mm**")
                st.metric(label="POIDS DU LOPIN", value=f"{poids_lopin:.3f} kg")
                st.metric(label="LONGUEUR LOPIN OPTIMALE", value=f"{long_lopin_mm:.2f} mm")

            with res_col2:
                st.write("\n")
                # Calcul du pourcentage par rapport à la limite de la presse choisie
                pourcent = min((long_lopin_mm / limite_max) * 100, 100)
                
                st.write(f"📊 **Progression du Lopin ({long_lopin_mm:.1f} mm)**")
                st.markdown(f'<div class="container-barre"><div class="barre-lopin" style="width: {pourcent}%;"></div></div>', unsafe_allow_html=True)
                
                st.write(f"🏁 **Limite de la {presse_choisie} ({limite_max} mm)**")
                st.markdown('<div class="barre-limite" style="width: 100%;"></div>', unsafe_allow_html=True)
                
                st.success(f"✅ Réglages validés pour la {presse_choisie}.")
    else:
        st.warning("⚠️ Information manquante : Vérifiez le P/m ou la Longueur.")

# --- PIED DE PAGE ---
st.markdown("<br>", unsafe_allow_html=True)
st.caption(f"© 2026 TPR - Système d'Assistance Technique | {presse_choisie if presse_choisie else 'Sélectionner presse'}")
st.caption("Développé pour l'assistance opérateur en extrusion.")
