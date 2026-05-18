import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==============================================================================
# CONFIGURATION & CONSTANTES
# ==============================================================================
DB_FILE = "base_arrets_tpr.csv"  # Modifiez le nom selon votre fichier réel

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
# ONGLET 1 : SAISIE D'UN ARRÊT (LISTES DYNAMIQUES HORS FORMULAIRE)
# ==============================================================================
with tab_saisie:
    st.subheader("📝 Enregistrement d'un Arrêt")
    
    # Sélecteurs dynamiques placés HORS du formulaire pour éviter le blocage de rafraîchissement
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

    raison_detaillee = st.selectbox(
        "Raison détaillée :",
        options=raisons_disponibles,
        key=f"raison_detaillee_{code_lettre}"
    )

    cause_finale = f"{cause_principale} : {raison_detaillee}"

    # Formulaire contenant le reste des inputs et le bouton de soumission réglementaire
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
# ONGLET 2 : HISTORIQUE GLOBAL (NETTOYÉ ET EXPORTABLE)
# ==============================================================================
with tab_base:
    st.subheader("📊 Historique Global des Arrêts")
    if os.path.isfile(DB_FILE):
        df_affichage = pd.read_csv(DB_FILE, sep=";")
        
        # Nettoyage visuel de la date (Heure masquée)
        df_affichage['Date'] = pd.to_datetime(df_affichage['Date'], errors='coerce').dt.strftime('%d/%m/%Y')
        
        colonnes_visibles = ['Date', 'Presse', 'Poste', 'Filiere', 'Lopin', 'Cause']
        df_pour_affichage = df_affichage[[c for c in colonnes_visibles if c in df_affichage.columns]]

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtre_presse = st.multiselect("Filtrer par Presse :", options=df_affichage["Presse"].unique(), key="f_presse")
        with col_f2:
            filtre_cause = st.multiselect("Filtrer par Cause :", options=df_affichage["Cause"].unique(), key="f_cause")
        
        if filtre_presse:
            df_pour_affichage = df_pour_affichage[df_pour_affichage["Presse"].isin(filtre_presse)]
        if filtre_cause:
            df_pour_affichage = df_pour_affichage[df_pour_affichage["Cause"].isin(filtre_cause)]
            
        st.dataframe(df_pour_affichage, use_container_width=True, hide_index=True)
        
        csv = df_affichage.to_csv(index=False, sep=";").encode('utf-8-sig')
        st.download_button(
            label="📥 Télécharger la base complète pour Excel",
            data=csv,
            file_name=f"base_arrets_TPR_{datetime.now().strftime('%d_%m_%Y')}.csv",
            mime="text/csv",
        )
    else:
        st.info("Aucune donnée n'a encore été enregistrée.")

# ==============================================================================
# ONGLET 3 : STATISTIQUES & GRAPHIQUES (CENTRAGE HTML, SOMME FIXÉE & HOVER PLOTLY)
# ==============================================================================
with tab_stats:
    import plotly.express as px
    
    st.subheader("📈 Analyse Statistique des Temps d'Arrêt")
    if os.path.isfile(DB_FILE):
        df_stats = pd.read_csv(DB_FILE, sep=";")
        
        # Résolution du bug de concaténation de texte : conversion mathématique forcée
        df_stats['Duree_Min'] = pd.to_numeric(df_stats['Duree_Min'], errors='coerce').fillna(0)
        
        presse_filtre = st.multiselect("Sélectionner la ou les Presses :", options=sorted(df_stats["Presse"].unique()), default=df_stats["Presse"].unique())
        
        if presse_filtre:
            df_filtered = df_stats[df_stats["Presse"].isin(presse_filtre)].copy()
            df_filtered['Code Cause'] = df_filtered['Cause'].str[0]
            
            # Groupement mathématique pour nettoyer les segments des barres Plotly
            df_grouped = df_filtered.groupby(['Presse', 'Code Cause'])['Duree_Min'].sum().reset_index()
            tableau_somme = df_filtered.groupby('Code Cause')['Duree_Min'].sum().reset_index().sort_values(by='Duree_Min', ascending=False)
            
            tableau_somme['Duree_Min'] = tableau_somme['Duree_Min'].astype(int)
            total_general = int(tableau_somme['Duree_Min'].sum())
            
            # --- SECTION TABLEAU HTML CENTRÉ & EFFET HOVER ---
            col_vide, col_tab, col_espace, col_metrique = st.columns([0.5, 3, 0.5, 2])
            
            with col_tab:
                html_table = f"""
                <style>
                    .custom-table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                    .custom-table th {{ background-color: #f8f9fb; color: #0047AB; text-align: center !important; padding: 12px; border-bottom: 2px solid #0047AB; font-weight: bold; }}
                    .custom-table td {{ text-align: center !important; padding: 10px; border-bottom: 1px solid #eee; color: #333; transition: all 0.2s ease; }}
                    .custom-table tr:hover td {{ background-color: #eef4ff !important; color: #0047AB !important; cursor: pointer; font-weight: bold; }}
                    .custom-table tr:last-child td {{ border-bottom: none; }}
                </style>
                <table class="custom-table">
                    <thead><tr><th>Code Cause</th><th>Temps Total (Minutes)</th></tr></thead>
                    <tbody>
                """
                for _, row in tableau_somme.iterrows():
                    html_table += f"<tr><td>{row['Code Cause']}</td><td>{int(row['Duree_Min'])}</td></tr>"
                html_table += "</tbody></table>"
                st.markdown(html_table, unsafe_allow_html=True)
                
            with col_metrique:
                st.markdown("<br>", unsafe_allow_html=True)
                st.metric(label="TOTAL GÉNÉRAL DES ARRÊTS", value=f"{total_general} min")
                
            # --- SECTION GRAPH_BARRES UNIFORMES AVEC COULEURS & HOVER ---
            st.markdown("<br>", unsafe_allow_html=True)
            fig2 = px.bar(
                df_grouped, 
                x='Code Cause', 
                y='Duree_Min', 
                color='Presse', 
                barmode='group',
                title="Durée totale des arrêts par cause (min)",
                labels={'Code Cause': 'Cause (Code)', 'Duree_Min': 'Minutes'},
                color_discrete_map={"Presse 4": "#E63946", "Presse 6": "#457B9D", "Presse 7": "#2A9D8F"}
            )
            fig2.update_traces(
                hoverinfo="all",
                hovertemplate="<b>Presse:</b> %{fullData.name}<br><b>Temps:</b> %{y} min<extra></extra>",
                marker_line_width=1,
                marker_line_color="white",
                marker_opacity=0.85
            )
            fig2.update_layout(hovermode="closest", xaxis_tickangle=0)
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Aucune donnée disponible pour générer des graphiques.")
