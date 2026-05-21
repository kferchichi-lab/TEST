import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px  # Pour les graphiques
from io import BytesIO      # Pour l'export Excel


DB_FILE = "base_donnees_chapeaux.csv"

DICTIONNAIRE_CODES = {
    "R": ["Lopin déformé", "2 morceaux du lopin non alignés", "Conteneur encrassé", "Autre problème de raclage"],
    "O": ["Face de contact entre conteneur et filière", "Usure prématurée du grain", "Casse outillage", "Mauvais centrage"],
    "H": ["Pression de bridage insuffisante", "Pression de chape instable", "Fuite d'huile vérin", "Problème de pompe", "Pression d'extrusion instable"],
    "T": ["Température non homogène du conteneur", "Température de filière inadéquate", "Refroidissement du lopin"],
    "A": ["Attente matière", "Pause opérateur", "Panne électrique générale"]
}

st.set_page_config(page_title="Suivi Arrêts TPR", page_icon="📝", layout="wide")


def sauvegarder_donnees(data):
    df = pd.DataFrame([data])
    if not os.path.isfile(DB_FILE):
        df.to_csv(DB_FILE, index=False, sep=";", encoding="utf-8-sig")
    else:
        df.to_csv(DB_FILE, mode='a', index=False, header=False, sep=";", encoding="utf-8-sig")

st.markdown("""
    <style>
        header { visibility: visible !important; height: 60px !important; }
        .block-container { padding-top: 2rem !important; }
        .temp-header { color: #0047AB; font-weight: bold; margin-bottom: 5px; }*

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
        
/* Cible TOUS les types de boutons : Standard, Téléchargement et Formulaire */
        div.stButton > button, 
        div.stDownloadButton > button, 
        div.stFormSubmitButton > button {
            width: 100% !important; 
            height: 3.5em !important; 
            border-radius: 12px !important; 
            border: none !important;
            background: linear-gradient(135deg, #0047AB 0%, #00264d 100%) !important;
            color: white !important; 
            font-size: 16px !important; 
            font-weight: 600 !important;
            box-shadow: 0 4px 15px rgba(0, 71, 171, 0.3) !important;
            transition: all 0.3s ease !important;
        }

        /* Effet au survol pour tous les boutons */
        div.stButton > button:hover, 
        div.stDownloadButton > button:hover, 
        div.stFormSubmitButton > button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 8px 25px rgba(0, 71, 171, 0.5) !important;
            background: linear-gradient(135deg, #0056cc 0%, #003366 100%) !important;
        }

        /* Forcer la couleur du texte à l'intérieur des balises <p> de Streamlit */
        div.stButton > button p, 
        div.stDownloadButton > button p, 
        div.stFormSubmitButton > button p {
            color: white !important;
        }
        </style>
    """, unsafe_allow_html=True)

CONFIG_PRESSES = {
    "Presse 4": {"diametre": 228},
    "Presse 6": {"diametre": 178},
    "Presse 7": {"diametre": 178},
}

with st.sidebar:
    st.header("⚙️ Configuration Machine")
    presse_choisie = st.selectbox("SÉLECTIONNER LA PRESSE :", options=list(CONFIG_PRESSES.keys()), index=None, placeholder="Choisir...")
  
    st.divider()
    st.markdown("<div class='temp-header'>🌡️ RAPPEL TEMPÉRATURES</div>", unsafe_allow_html=True)
    st.info("""
    - **Conteneur :** 400 - 430°C
    - **Filière :** 450°C
    - **Lopin (Plate) :** 440 - 470°C
    - **Lopin (Tubulaire) :** 470 - 510°C
    """)
    st.warning("⚠️ Tolérance : +/- 10°C")

col_logo, col_titre = st.columns([1, 5])
with col_logo:
    st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6q1BtDSDgVnJZFo0hOBfQJoDS6OYiub-qfQ&s", width=150)
with col_titre:
    st.markdown("## Tunisie Profilés d'Aluminium")
    st.markdown("#### Direction Maintenance et Travaux Neufs")
st.divider()

tab_saisie, tab_base, tab_stats = st.tabs(["➕ Nouvelle Saisie", "📊 Consulter la Base de Données", "📈 Analyse Graphique"])

with tab_saisie:
    if not presse_choisie:
        st.info("👈 Veuillez sélectionner une presse dans le menu à gauche pour accéder au formulaire.")
    else:
        st.subheader(f"📝 Saisie d'incident : {presse_choisie}")
        

        col1, col2 = st.columns(2)
        with col1:
            date_j = st.date_input("Date de l'arrêt", datetime.now())
            poste = st.radio("Poste de travail", ["A", "B", "C"], horizontal=True)
            ref_filiere = st.text_input("Référence Filière", placeholder="Ex: 52000")
       
        with col2:
            num_lopin = st.text_input("Numéro du lopin", placeholder="Ex: 12")
            duree = st.number_input("Durée de l'arrêt (minutes)", min_value=0, step=1)
            
            cause_principale = st.selectbox(
                "Nature de la Cause (Générale) :",
                options=[
                    "R - Raclage du conteneur",
                    "O - Outillage",
                    "H - Problème Hydraulique",
                    "T - Problème de Température",
                    "A - Autres"
                ],
                index=None,  
                placeholder="--- Choisir une cause générale ---", 
                key="cause_gnerale_select"
            )
            raisons_finales_texte = "Non spécifié"
            if cause_principale is not None:
                code_lettre = cause_principale[0]
                raisons_disponibles = DICTIONNAIRE_CODES.get(code_lettre, DICTIONNAIRE_CODES["A"])

                st.write("**Sélectionnez la ou les raisons détaillées :**")
                raisons_choisies = []

                for raison in raisons_disponibles:
                    if st.checkbox(raison, key=f"cb_{code_lettre}_{raison}"):
                        raisons_choisies.append(raison)

                raisons_finales_texte = ", ".join(raisons_choisies) if raisons_choisies else "Non spécifié"
                cause_finale = f"{cause_principale} : {raisons_finales_texte}"
            else:
                st.info("💡 Veuillez sélectionner une nature de cause pour voir les raisons détaillées.")

        commentaire = st.text_area("Observations / Détails de l'incident")
        
        with st.form("form_validation", clear_on_submit=True):
            submitted = st.form_submit_button("ENREGISTRER L'INCIDENT")
        if submitted:
            if not ref_filiere or not num_lopin:
                st.error("Veuillez remplir les champs obligatoires (Filière et Lopin).")
            elif raisons_finales_texte == "Non spécifié":
                st.warning("⚠️ Veuillez cocher au moins une raison détaillée avant d'enregistrer.")
            else:
                nouvelle_entree = {
                    "Date": date_j.strftime("%d/%m/%Y"),
                    "Heure_Saisie": datetime.now().strftime("%H:%M:%S"),
                    "Presse": presse_choisie,
                    "Poste": poste,
                    "Filiere": ref_filiere,
                    "Lopin": num_lopin,
                    "Duree_Min": duree,
                    "Cause": cause_finale, 
                    "Observations": commentaire
                }
                sauvegarder_donnees(nouvelle_entree)
                st.success(f"✅ Incident enregistré pour la {presse_choisie}")
with tab_base:
    st.subheader("📊 Historique Global des Arrêts")
    if os.path.isfile(DB_FILE):
        # 1. Chargement de la base
        df_affichage = pd.read_csv(DB_FILE, sep=";")
        
        # Sécurité : On s'assure que la colonne Cause existe et ne contient pas de lignes vides
        if "Cause" in df_affichage.columns:
            df_affichage['Cause'] = df_affichage['Cause'].fillna("A - Autres")
            
            # 2. CRÉATION D'UNE COLONNE DE RÉFÉRENCE PROPRE (Standardisation stricte)
            mapping_filtres = {
                "R": "R - Raclage du conteneur",
                "O": "O - Outillage",
                "H": "H - Problème Hydraulique",
                "T": "T - Problème de Température",
                "A": "A - Autres"
            }
            # On prend la première lettre, on la met en majuscule, et on applique le nom propre
            df_affichage['Cause_Filtre_Standard'] = df_affichage['Cause'].str[0].str.upper().map(mapping_filtres).fillna("A - Autres")
        else:
            df_affichage['Cause'] = "A - Autres"
            df_affichage['Cause_Filtre_Standard'] = "A - Autres"

        # Formatage de la date
        if 'Date' in df_affichage.columns:
            df_affichage['Date'] = df_affichage['Date'].astype(str).str[:10]
        if 'Duree_Min' in df_affichage.columns:
            df_affichage['Duree_Min'] = pd.to_numeric(df_affichage['Duree_Min'], errors='coerce').fillna(0).astype(int)

        # 3. INTERFACE DES FILTRES
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            options_presse = df_affichage["Presse"].unique() if "Presse" in df_affichage.columns else []
            filtre_presse = st.multiselect("Filtrer par Presse :", options=options_presse)
        with col_f2:
            # Ici, on affiche UNIQUEMENT les 5 causes propres et uniques triées
            options_cause = sorted(df_affichage["Cause_Filtre_Standard"].unique())
            filtre_cause = st.multiselect("Filtrer par Cause :", options=options_cause)
       
        # 4. APPLICATION APPRENDRE ET FILTRAGE DU DATAFRAME
        df_filtre = df_affichage.copy()
        
        if filtre_presse:
            df_filtre = df_filtre[df_filtre["Presse"].isin(filtre_presse)]
        if filtre_cause:
            # On applique le filtre sur notre colonne standardisée cachée
            df_filtre = df_filtre[df_filtre["Cause_Filtre_Standard"].isin(filtre_cause)]
           
        # 5. SÉLECTION ET RENOMMAGE DES COLONNES POUR L'AFFICHAGE
        colonnes_visibles = ['Date', 'Presse', 'Poste', 'Filiere', 'Lopin', 'Duree_Min', 'Cause']
        # On ne garde que les colonnes existantes
        colonnes_existantes = [c for c in colonnes_visibles if c in df_filtre.columns]
        
        df_pour_affichage = df_filtre[colonnes_existantes].copy()
        
        # Renommage propre pour le tableau final de l'utilisateur
        traductions = {
            'Date': 'Date', 'Presse': 'Presse', 'Poste': 'Poste', 
            'Filiere': 'Filière', 'Lopin': 'Lopin', 
            'Duree_Min': 'Durée (Min)', 'Cause': "Cause de l'arrêt"
        }
        df_pour_affichage.rename(columns=traductions, inplace=True)
            
        # Affichage du tableau final filtré
        st.dataframe(df_pour_affichage, use_container_width=True, hide_index=True)

        # 6. BOUTON DE TÉLÉCHARGEMENT
        csv = df_pour_affichage.to_csv(index=False, sep=";").encode('utf-8-sig')
        st.download_button(
            label="📥 Télécharger la base complète pour Excel",
            data=csv,
            file_name=f"base_arrets_TPR_{datetime.now().strftime('%d_%m_%Y')}.csv",
            mime="text/csv",
        )
    else:
        st.info("Aucune donnée n'a encore été enregistrée.")
with tab_stats:
    if os.path.isfile(DB_FILE):
        df_stats = pd.read_csv(DB_FILE, sep=";")
        st.subheader("Analyse des causes par Presse")
        
        presse_filtre = st.multiselect("Sélectionner les presses à analyser :", options=df_stats["Presse"].unique(), default=df_stats["Presse"].unique())
        
        if presse_filtre:
            df_filtered = df_stats[df_stats["Presse"].isin(presse_filtre)].copy()
            
            # 1. Sécurité pour les valeurs vides
            df_filtered['Cause'] = df_filtered['Cause'].fillna("A")
            
            # 2. On extrait UNIQUEMENT la première lettre (R, O, H, T, A) et on enlève les espaces
            df_filtered['Code_Lettre'] = df_filtered['Cause'].str[0].str.upper()
            
            # 3. On crée un dictionnaire de traduction pour avoir des noms parfaits et uniques
            mapping_noms = {
                "R": "R - Raclage du conteneur",
                "O": "O - Outillage",
                "H": "H - Problème Hydraulique",
                "T": "T - Problème de Température",
                "A": "A - Autres"
            }
            
            # 4. On applique le nom standardisé (si la lettre n'est pas dedans, on met "A - Autres")
            df_filtered['Cause_Standard'] = df_filtered['Code_Lettre'].map(mapping_noms).fillna("A - Autres")
            
            # 5. Sécurité d'affichage
            if df_filtered.empty:
                st.warning("⚠️ Aucune donnée valide trouvée pour les filtres sélectionnés.")
            else:
                # On utilise 'Cause_Standard' pour le graphique de répartition
                fig = px.pie(
                    df_filtered, 
                    names='Cause_Standard', # <-- Colonne parfaitement standardisée
                    title=f"Répartition des causes - {', '.join(presse_filtre)}",
                    hole=0.4, 
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                
                fig.update_traces(
                    textposition='inside', 
                    textinfo='percent'  
                )
        
                fig.update_layout(
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.05
                    )
                )
        
                st.plotly_chart(fig, use_container_width=True)

            st.divider()
            
            # --- CODE POUR LE GRAPH EN BARRES (fig2) ---
            df_temp = df_filtered.copy()
            # On réutilise la colonne Code_Lettre qu'on a déjà nettoyée et sécurisée
            df_temp['Code_Cause'] = df_temp['Code_Lettre']

            st.subheader("Total des minutes d'arrêt par cause")
    
            fig2 = px.bar(
                df_temp, 
                x='Code_Cause', 
                y='Duree_Min', 
                color='Presse', 
                barmode='group',
                title="Durée totale des arrêts par code de cause (min)",
                labels={'Code_Cause': 'Cause (Code)', 'Duree_Min': 'Minutes'},
                color_discrete_map={ 
                    "Presse 4": "#E63946", 
                    "Presse 6": "#457B9D", 
                    "Presse 7": "#2A9D8F"
                }
            )
            fig2.update_traces(marker_line_color='white', marker_line_width=1, opacity=0.9)
            fig2.update_layout(xaxis_tickangle=0)    
            st.plotly_chart(fig2, use_container_width=True)
    
            df_filtered['Code'] = df_filtered['Cause'].str[0]
            tableau_somme = df_filtered.groupby('Code')['Duree_Min'].sum().reset_index()
            tableau_somme = tableau_somme.sort_values(by='Duree_Min', ascending=False)          
            tableau_somme.columns = ['Code Cause', 'Temps Total (Minutes)']
            col_vide, col_tab, col_espace, col_metrique = st.columns([1, 2, 0.5, 2])

            with col_tab:
                st.dataframe(
                    tableau_somme, 
                    use_container_width=False, 
                    hide_index=True,
                    width=400  
                )

            with col_metrique:
                st.markdown("<br><br>", unsafe_allow_html=True)
                total_general = tableau_somme['Temps Total (Minutes)'].sum()
                st.metric("TOTAL GÉNÉRAL", f"{total_general} min")
    
            st.info("**Rappel des codes :** **T** : Problème de Température | **H** : Problème Hydraulique | **O** : Outillage | **R** : Raclage | **A** : Autres..")
    else:
        st.info("Enregistrez des données pour voir les graphiques.")

st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
st.markdown(
    f"""
    <div style="text-align: center; color: gray; font-size: 0.8em; border-top: 1px solid #eee; padding-top: 10px;">
        © 2026 TPR - Système de Suivi Maintenance <br>
        Direction Maintenance et Travaux Neufs - DMTN 
    </div>
    """, 
    unsafe_allow_html=True
)
