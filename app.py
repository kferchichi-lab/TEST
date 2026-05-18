import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px  # Pour les graphiques
from io import BytesIO      # Pour l'export Excel

DICTIONNAIRE_CAUSES = {
    "R - Raclage du conteneur": [
        "Lopin déformé",
        "2 morceaux du lopin non alignés",
        "Conteneur encrassé",
        "Autre problème de raclage"
    ],
    "O - Outillage": [
        "Face de contact entre conteneur et filière",
        "Usure prématurée",
        "Casse outillage",
        "Changement de filière programmé"
    ],
    "H - Problème Hydraulique": [
        "Pression de bridage insuffisante",
        "Pression de chape instable",
        "Fuite d'huile vérin",
        "Problème de pompe"
    ],
    "T - Problème de Température": [
        "Température non homogène (Filière)",
        "Surchauffe conteneur",
        "Refroidissement lopin insuffisant"
    ],
    "Autres": [
        "Attente matière",
        "Pause opérateur",
        "Panne électrique générale"
    ]
}

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Suivi Arrêts TPR", page_icon="📝", layout="wide")

# --- FICHIER DE BASE DE DONNÉES ---
DB_FILE = "base_donnees_chapeaux.csv"

# Fonction pour sauvegarder les données dans le fichier CSV
def sauvegarder_donnees(data):
    df = pd.DataFrame([data])
    if not os.path.isfile(DB_FILE):
        df.to_csv(DB_FILE, index=False, sep=";", encoding="utf-8-sig")
    else:
        df.to_csv(DB_FILE, mode='a', index=False, header=False, sep=";", encoding="utf-8-sig")

# --- STYLE CSS ---
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

# --- SIDEBAR : CHOIX ET RAPPELS ---
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

# --- LOGOS ET TITRE ---
col_logo, col_titre = st.columns([1, 5])
with col_logo:
    st.image("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6q1BtDSDgVnJZFo0hOBfQJoDS6OYiub-qfQ&s", width=150)
with col_titre:
    st.markdown("## Tunisie Profilés d'Aluminium")
    st.markdown("#### Direction Maintenance et Travaux Neufs")
st.divider()

# --- NAVIGATION PAR ONGLETS ---
tab_saisie, tab_base, tab_stats = st.tabs(["➕ Nouvelle Saisie", "📊 Consulter la Base de Données", "📈 Analyse Graphique"])

# --- ONGLET 1 : FORMULAIRE DE SAISIE ---
with tab_saisie:
    if not presse_choisie:
        st.info("👈 Veuillez sélectionner une presse dans le menu à gauche pour accéder au formulaire.")
    else:
        st.subheader(f"📝 Saisie d'incident : {presse_choisie}")
        with st.form("form_diagnostic", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                date_j = st.date_input("Date de l'arrêt", datetime.now())
                poste = st.radio("Poste de travail", ["A", "B", "C"], horizontal=True)
                ref_filiere = st.text_input("Référence Filière", placeholder="Ex: 52000")
           
            with col2:
                num_lopin = st.text_input("Numéro du lopin", placeholder="Ex: 12")
                duree = st.number_input("Durée de l'arrêt (minutes)", min_value=0, step=1)
                cause = st.selectbox("Cause identifiée (Code)", [
                    "T - Problème de Température non homogène (Filière, conteneur, lopin)",
                    "H - Problème Hydraulique (Pression de bridage, de chape…)",
                    "O - Outillage : face de contact entre conteneur et filière (Usure, casse…)",
                    "R - Raclage du conteneur : Lopin déformé, 2 morceaux du lopin non alignés..",
                    "A - Autres..", 
                ])


            commentaire = st.text_area("Observations / Détails de l'incident")
            submitted = st.form_submit_button("ENREGISTRER L'INCIDENT")

        if submitted:
            if not ref_filiere or not num_lopin:
                st.error("Veuillez remplir les champs obligatoires (Filière et Lopin).")
            else:
                    # Préparation de la ligne de données
                nouvelle_entree = {
                "Date": date_j.strftime("%d/%m/%Y"),
                "Heure_Saisie": datetime.now().strftime("%H:%M:%S"),
                "Presse": presse_choisie,
                "Poste": poste,
                "Filiere": ref_filiere,
                "Lopin": num_lopin,
                "Duree_Min": duree,
                "Cause": cause,
                "Observations": commentaire
                }
            sauvegarder_donnees(nouvelle_entree)
            st.success(f"✅ Incident enregistré pour la {presse_choisie}")
                 
# --- ONGLET 2 : CONSULTATION DE LA BASE ---

with tab_base:
    st.subheader("📊 Historique Global des Arrêts")
    if os.path.isfile(DB_FILE):
        df_affichage = pd.read_csv(DB_FILE, sep=";")
        df_affichage['Date'] = df_affichage['Date'].astype(str).str[:10]

        
        colonnes_visibles = ['Date', 'Presse', 'Poste', 'Filiere', 'Lopin', 'Duree_Min', 'Cause']
        df_pour_affichage = df_affichage[[c for c in colonnes_visibles if c in df_affichage.columns]]
        # Sécurité : On force la colonne Duree_Min en numérique (évite le bug des gros chiffres)
        df_affichage['Duree_Min'] = pd.to_numeric(df_affichage['Duree_Min'], errors='coerce').fillna(0).astype(int)
        # Filtres interactifs
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtre_presse = st.multiselect("Filtrer par Presse :", options=df_affichage["Presse"].unique())
        with col_f2:
            filtre_cause = st.multiselect("Filtrer par Cause :", options=df_affichage["Cause"].unique())
       
        if filtre_presse:
            df_affichage = df_affichage[df_affichage["Presse"].isin(filtre_presse)]
        if filtre_cause:
            df_affichage = df_affichage[df_affichage["Cause"].isin(filtre_cause)]
           
        # Affichage du tableau (Le Grand Tableau)
        df_pour_affichage.columns = ['Date', 'Presse', 'Poste', 'Filière', 'Lopin', 'Durée (Min)', 'Cause de l\'arrêt']
            
        # Affichage du tableau propre, sans index, sur toute la largeur
        st.dataframe(df_pour_affichage, use_container_width=True, hide_index=True)

       
        # Bouton d'export Excel
        csv = df_affichage.to_csv(index=False, sep=";").encode('utf-8-sig')
        st.download_button(
            label="📥 Télécharger la base complète pour Excel",
            data=csv,
            file_name=f"base_arrets_TPR_{datetime.now().strftime('%d_%m_%Y')}.csv",
            mime="text/csv",
        )
    else:
        st.info("Aucune donnée n'a encore été enregistrée.")


# --- ONGLET 3 : ANALYSE GRAPHIQUE ---
with tab_stats:
    if os.path.isfile(DB_FILE):
        df_stats = pd.read_csv(DB_FILE, sep=";")
        st.subheader("Analyse des causes par Presse")
        
        # Sélecteur pour le graphique
        presse_filtre = st.multiselect("Sélectionner les presses à analyser :", options=df_stats["Presse"].unique(), default=df_stats["Presse"].unique())
        
        if presse_filtre:
            df_filtered = df_stats[df_stats["Presse"].isin(presse_filtre)]
            
            # Création du graphique en cercle (Pie Chart)
            # On groupe par 'Cause' et on compte les occurrences
            fig = px.pie(df_filtered, names='Cause', title=f"Répartition des causes - {', '.join(presse_filtre)}",
                         hole=0.4, # Pour en faire un Donut chart (plus moderne)
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            
            fig.update_traces(
                textposition='inside', 
                textinfo='percent'  # <--- On a supprimé '+label' pour n'avoir que le %
            )
    
    # Ajustement de la légende pour qu'elle soit bien lisible à droite
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
            
            # Optionnel : Répartition du temps d'arrêt
            st.divider()
            df_temp = df_filtered.copy()
    
    # On extrait juste la première lettre (le Code : T, H, O, R) pour l'affichage
            df_temp['Code_Cause'] = df_temp['Cause'].str[0] 

            st.subheader("Total des minutes d'arrêt par cause")
    
            fig2 = px.bar(
                df_temp, 
                x='Code_Cause', # On utilise le code court ici
                y='Duree_Min', 
                color='Presse', 
                barmode='group',
                title="Durée totale des arrêts par code de cause (min)",
                labels={'Code_Cause': 'Cause (Code)', 'Duree_Min': 'Minutes'},
                color_discrete_map={ # Optionnel : fixer les couleurs pour plus de clarté
                    "Presse 4": "#E63946", 
                    "Presse 6": "#457B9D", 
                    "Presse 7": "#2A9D8F"
                }
            )
            fig2.update_traces(marker_line_color='white', marker_line_width=1, opacity=0.9)
    # On force l'affichage des codes sans inclinaison
            fig2.update_layout(xaxis_tickangle=0)
    
            st.plotly_chart(fig2, use_container_width=True)

            # --- EXTRACTION DU CODE ---
            # On crée une nouvelle colonne 'Code' en prenant le 1er caractère
            df_filtered['Code'] = df_filtered['Cause'].str[0]
            
            # Groupement par Code
            tableau_somme = df_filtered.groupby('Code')['Duree_Min'].sum().reset_index()
            
            # Tri par durée décroissante
            tableau_somme = tableau_somme.sort_values(by='Duree_Min', ascending=False)
            
            # Renommer pour l'affichage
            tableau_somme.columns = ['Code Cause', 'Temps Total (Minutes)']
            
            # Affichage du tableau (hide_index=True pour enlever les chiffres 0, 1, 2 à gauche)

            col_vide, col_tab, col_espace, col_metrique = st.columns([1, 2, 0.5, 2])

            with col_tab:
                st.dataframe(
                    tableau_somme, 
                    use_container_width=False, 
                    hide_index=True,
                    width=400  # Vous pouvez ajuster cette valeur (en pixels) selon votre besoin
                )

            with col_metrique:
                st.markdown("<br><br>", unsafe_allow_html=True)
                total_general = tableau_somme['Temps Total (Minutes)'].sum()
                st.metric("TOTAL GÉNÉRAL", f"{total_general} min")
    
    # Petit rappel des codes en dessous pour l'utilisateur
            st.info("**Rappel des codes :** **T** : Problème de Température | **H** : Problème Hydraulique | **O** : Outillage | **R** : Raclage | **A** : Autres..")
    else:
        st.info("Enregistrez des données pour voir les graphiques.")

# --- FOOTER ---
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
