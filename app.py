import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==============================================================================
# CONFIGURATION & CONSTANTES
# ==============================================================================
DB_FILE = "base_arrets_tpr.csv"

DICTIONNAIRE_CODES = {
    "R": ["Lopin déformé", "2 morceaux du lopin non alignés", "Conteneur encrassé", "Autre problème de raclage"],
    "O": ["Face de contact entre conteneur et filière", "Usure prématurée", "Casse outillage", "Changement de filière programmé"],
    "H": ["Pression de bridage insuffisante", "Pression de chape instable", "Fuite d'huile vérin", "Problème de pompe"],
    "T": ["Température non homogène (Filière)", "Surchauffe conteneur", "Refroidissement lopin insuffisant"],
    "A": ["Attente matière", "Pause opérateur", "Panne électrique générale"]
}

st.set_page_config(layout="wide")

# ==============================================================================
# NAVIGATION PAR ONGLETS
# ==============================================================================
tab_saisie, tab_base, tab_stats = st.tabs(["📝 Saisie Arrêt", "📊 Historique Global", "📈 Statistiques & Graphiques"])

# ==============================================================================
# ONGLET 1 : SAISIE D'UN ARRÊT (CASES À COCHER DYNAMIQUES HORS FORMULAIRE)
# ==============================================================================
with tab_saisie:
    st.subheader("📝 Enregistrement d'un Arrêt")
    
    # Sélecteur de la cause générale
    cause_principale = st.selectbox(
        "Nature de la Cause (Générale) :",
        options=[
            "R - Raclage du conteneur",
            "O - Outillage",
            "H - Problème Hydraulique",
            "T - Problème de Température",
            "A - Autres"
        ],
        key="cause_gnerale_select"
    )

    code_lettre = cause_principale[0]
    raisons_disponibles = DICTIONNAIRE_CODES.get(code_lettre, DICTIONNAIRE_CODES["A"])

    # --- LISTE À COCHER DES ÉLÉMENTS (DYNAMIQUE) ---
    st.write("**Sélectionnez la ou les raisons détaillées :**")
    raisons_choisies = []
    
    # On crée une case à cocher pour chaque élément de la liste
    for raison in raisons_disponibles:
        # Clé unique pour chaque case combinant la lettre et la raison pour éviter les conflits Streamlit
        if st.checkbox(raison, key=f"cb_{code_lettre}_{raison}"):
            raisons_choisies.append(raison)

    # Si l'opérateur coche plusieurs cases, on les rassemble (ex: "Lopin déformé, Conteneur encrassé")
    # Si aucune case n'est cochée, on met "Non spécifié" par sécurité
    raisons_finales_texte = ", ".join(raisons_choisies) if raisons_choisies else "Non spécifié"

    # Construction de la chaîne complète pour le CSV
    cause_finale = f"{cause_principale} : {raisons_finales_texte}"

    # Formulaire contenant le reste des inputs et le bouton obligatoire
    with st.form(key="formulaire_saisie"):
        col1, col2, col3 = st.columns(3)
        with col1:
            presse = st.selectbox("Presse :", ["Presse 4", "Presse 6", "Presse 7"])
            poste = st.selectbox("Poste :", ["A", "B", "C"])
        with col2:
            filiere = st.text_input("Référence Filière :", placeholder="Ex: 52000")
            lopin = st.number_input("Numéro Lopin :", min_value=1, step=1)
        with col3:
            duree = st.number_input("Durée de l'arrêt (Minutes) :", min_value=1, step=1)
            
        bouton_validation = st.form_submit_button(label="💾 Enregistrer l'arrêt")
        
        if bouton_validation:
            if raisons_finales_texte == "Non spécifié":
                st.warning("⚠️ Veuillez cocher au moins une raison détaillée avant d'enregistrer.")
            else:
                nouvelle_entree = {
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Presse": presse,
                    "Poste": poste,
                    "Filiere": filiere,
                    "Lopin": lopin,
                    "Duree_Min": duree,
                    "Cause": cause_finale
                }
                df_nouveau = pd.DataFrame([nouvelle_entree])
                
                if not os.path.isfile(DB_FILE):
                    df_nouveau.to_csv(DB_FILE, index=False, sep=";")
                else:
                    df_nouveau.to_csv(DB_FILE, mode='a', header=False, index=False, sep=";")
                    
                st.success("L'arrêt a été enregistré avec succès !")

# ==============================================================================
# ONGLET 2 : HISTORIQUE GLOBAL
# ==============================================================================
with tab_base:
    st.subheader("📊 Historique Global des Arrêts")
    if os.path.isfile(DB_FILE):
        df_affichage = pd.read_csv(DB_
