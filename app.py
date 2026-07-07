import streamlit as st
import streamlit.components.v1 as components
import plotly.express as px
import pandas as pd
import datetime
import pytz
import re
import time
import math
import requests
import calendar
import base64
import io
from weasyprint import HTML
import fitz  # PyMuPDF

def afficher_apercu_pdf(pdf_bytes, hauteur=800):
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        nb_pages = len(doc)
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=130)
            img_bytes = pix.tobytes("png")
            st.image(img_bytes, use_container_width=True)
            if nb_pages > 1:
                st.caption(f"Page {i + 1} / {nb_pages}")
        doc.close()
    except Exception as e:
        st.error(f"Impossible d'afficher l'aperçu du PDF : {e}")
        st.info("Vous pouvez tout de même télécharger le rapport ci-dessous.")
    
def afficher_apercu_pdf_grille(pdf_bytes, colonnes=2, largeur_colonne=380):
    """
    Affiche l'aperçu d'un PDF sous forme de grille (par défaut 2 colonnes),
    chaque colonne présentant une page du rapport, réduisant ainsi la taille
    d'affichage par rapport à un aperçu pleine largeur page par page.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        nb_pages = len(doc)
        cols = st.columns(colonnes)
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=110)
            img_bytes = pix.tobytes("png")
            col = cols[i % colonnes]
            with col:
                st.image(img_bytes, width=largeur_colonne)
                st.caption(f"Page {i + 1} / {nb_pages}")
        doc.close()
    except Exception as e:
        st.error(f"Impossible d'afficher l'aperçu du PDF : {e}")
        st.info("Vous pouvez tout de même télécharger le rapport ci-dessous.")


def generer_rapport_equipements_pdf(df_exigences, site_filtre):
    """
    Génère un rapport PDF de 5 pages pour un site spécifique (SGB ou MEG).
    """
    installations = [
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
    logo_url = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6q1BtDSDgVnJZFo0hOBfQJoDS6OYiub-qfQ&s"
    
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
        .page-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 16px;
            padding-bottom: 10px;
            border-bottom: 1px solid #E2E8F0;
        }}
        .page-header img {{
            height: 36px;
        }}
        .page-header-text {{
            font-size: 9.5pt;
            color: #64748B;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.4px;
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

    for ins in installations:
        # Filtrer par installation parmi les équipements du site
        df_ins = df_eq[df_eq.iloc[:, 2].astype(str).str.strip() == ins]
        
        html_content += f"""
        <div class="page">
            <div class="page-header">
                <img src="{logo_url}"/>
                <div class="page-header-text">Tunisie Profilés d'Aluminium — Direction Maintenance &amp; TN</div>
            </div>
            <div class="header-title" style="border-bottom: none; padding-bottom: 0;">Rapport d'Inspection Réglementaire</div>
            <div class="header-title">Site {site_filtre.upper()}</div>
            
            <div class="meta-info">
                <strong>Inspecteur technique :</strong> ............................................................<br>
                <strong>Accompagnant :</strong> ........................................................................<br>
                <strong>Date :</strong> .......................................................................................
            </div>
            
            <div class="category-title">{ins}</div>
            
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
        
        if not df_ins.empty:
            for _, row in df_ins.iterrows():
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
                    <td colspan="3" style="text-align:center; color:#94A3B8; font-style: italic;">Aucun équipement enregistré pour cette instalaltion sur ce site</td>
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


def generer_rapport_kpi_pdf(kpi_data, df_reserve, df_nature, carto_b64, logo_url):
    """
    Génère un rapport PDF premium regroupant tous les KPI de l'onglet KPI :
    Taux de réalisation 2026, Taux de respect de délai,
    cartographie du taux de non-conformité, et répartition par site et par pilote.
    """
    date_str = datetime.date.today().strftime('%d/%m/%Y')

    def barre(pct, couleur):
        pct = max(0, min(100, pct))
        return f"""<div style="background:#E2E8F0;border-radius:6px;height:14px;width:100%;overflow:hidden;">
            <div style="background:{couleur};height:100%;width:{pct}%;"></div></div>"""

    k1 = kpi_data["kpi1"]; k2 = kpi_data["kpi2"]

    # ---- Palettes de couleurs (cohérentes avec le tableau de bord Streamlit) ----
    COULEURS_SITE = {"SGB": "#1E3A8A", "MEG": "#0EA5E9"}
    COULEURS_NATURE = {
        "Technique": "#10B981", "Sécurité": "#F97316", "Organisation": "#84CC16",
        "Règlementation": "#EAB308", "Documentation": "#EC4899", "Energétique": "#64748B",
    }
    COULEURS_PILOTE = {
        "Maintenance": "#FACC15", "HSE": "#F97316", "BT": "#EF4444",
        "Chef service BT": "#3B82F6", "DMTN": "#A855F7", "RH": "#92400E", "DG": "#22C55E",
    }

    # ---- Helpers SVG (donut chart et bar chart horizontal, sans dépendance externe) ----
    def _polar(cx, cy, r, angle_deg):
        a = math.radians(angle_deg - 90)
        return (cx + r * math.cos(a), cy + r * math.sin(a))

    def _donut_path(cx, cy, r_out, r_in, a0, a1):
        p0o = _polar(cx, cy, r_out, a0)
        p1o = _polar(cx, cy, r_out, a1)
        p1i = _polar(cx, cy, r_in, a1)
        p0i = _polar(cx, cy, r_in, a0)
        large = 1 if (a1 - a0) > 180 else 0
        return (f"M {p0o[0]:.2f} {p0o[1]:.2f} "
                f"A {r_out:.2f} {r_out:.2f} 0 {large} 1 {p1o[0]:.2f} {p1o[1]:.2f} "
                f"L {p1i[0]:.2f} {p1i[1]:.2f} "
                f"A {r_in:.2f} {r_in:.2f} 0 {large} 0 {p0i[0]:.2f} {p0i[1]:.2f} Z")

    def _donut_chart(data, color_map, titre="", size=190):
        """data: dict {label: valeur numérique}. Retourne (svg, legend_html).
        Les pourcentages des petites parts sont affichés à l'extérieur (avec un
        trait de rappel) pour rester lisibles ; les grandes parts gardent le
        pourcentage centré à l'intérieur de l'anneau."""
        data = {k: v for k, v in data.items() if v and v > 0}
        total = sum(data.values())
        if not data or not total:
            return "", ""
        pad = 34  # marge latérale pour les étiquettes extérieures
        cx, cy = size / 2 + pad, size / 2 + 18
        r_out, r_in = size * 0.40, size * 0.40 * 0.58
        angle = 0.0
        slices, labels = "", ""
        for label, val in data.items():
            pct = val / total * 100
            a1 = angle + pct / 100 * 360
            color = color_map.get(label, "#94A3B8")
            slices += f'<path d="{_donut_path(cx,cy,r_out,r_in,angle,a1)}" fill="{color}" stroke="#ffffff" stroke-width="1.5"/>'
            mid = (angle + a1) / 2
            if pct >= 6:
                # part assez grande : pourcentage centré, en blanc, à l'intérieur de l'anneau
                lx, ly = _polar(cx, cy, (r_out + r_in) / 2, mid)
                labels += (f'<text x="{lx:.1f}" y="{ly:.1f}" font-size="11" font-weight="700" '
                           f'fill="#ffffff" text-anchor="middle" dominant-baseline="middle">{pct:.1f}%</text>')
            else:
                # petite part : trait de rappel + pourcentage à l'extérieur, dans la couleur de la part
                p0 = _polar(cx, cy, r_out, mid)
                p1 = _polar(cx, cy, r_out + 12, mid)
                anchor = "start" if p1[0] >= cx else "end"
                tx = p1[0] + (4 if anchor == "start" else -4)
                labels += (f'<line x1="{p0[0]:.1f}" y1="{p0[1]:.1f}" x2="{p1[0]:.1f}" y2="{p1[1]:.1f}" '
                           f'stroke="{color}" stroke-width="1.2"/>'
                           f'<text x="{tx:.1f}" y="{p1[1]:.1f}" font-size="9.5" font-weight="700" '
                           f'fill="{color}" text-anchor="{anchor}" dominant-baseline="middle">{pct:.1f}%</text>')
            angle = a1
        titre_svg = (f'<text x="{cx:.1f}" y="16" font-size="12.5" font-weight="700" fill="#0F172A" '
                     f'text-anchor="middle">{titre}</text>') if titre else ""
        w_total = size + 2 * pad
        svg = (f'<svg viewBox="0 0 {w_total} {size+22}" width="{w_total}" height="{size+22}" '
               f'xmlns="http://www.w3.org/2000/svg">{titre_svg}{slices}{labels}</svg>')
        legend = "".join(
            f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:8px;">'
            f'<span style="width:11px;height:11px;min-width:11px;border-radius:3px;'
            f'background:{color_map.get(l,"#94A3B8")};display:inline-block;"></span>'
            f'<span style="font-size:10pt;color:#334155;white-space:nowrap;">{l}</span></div>'
            for l in data.keys()
        )
        return svg, legend

    def _hbar_chart(data_pct, color_map, width=300, bar_h=18, gap=9, label_w=100):
        """data_pct: dict {label: pourcentage}, déjà trié décroissant."""
        if not data_pct:
            return ""
        max_pct = max(data_pct.values()) or 1
        chart_w = width - label_w - 50
        rows, y = "", 0
        for label, pct in data_pct.items():
            bw = max((pct / max_pct) * chart_w, 2)
            color = color_map.get(label, "#F59E0B")
            rows += (f'<text x="0" y="{y+bar_h*0.72:.1f}" font-size="9.5" fill="#334155">{label}</text>'
                      f'<rect x="{label_w}" y="{y}" width="{bw:.1f}" height="{bar_h}" rx="3" fill="{color}"/>'
                      f'<text x="{label_w+bw+6:.1f}" y="{y+bar_h*0.72:.1f}" font-size="9.5" fill="#334155">{pct:.1f}%</text>')
            y += bar_h + gap
        return (f'<svg viewBox="0 0 {width} {y}" width="{width}" height="{y}" '
                f'xmlns="http://www.w3.org/2000/svg">{rows}</svg>')

    # ---- Section 1 : Actions de contrôle — par site et par installation (source : PointsReserve) ----
    df_r = df_reserve.copy() if (df_reserve is not None and not df_reserve.empty) else pd.DataFrame()
    if not df_r.empty and "Nombre" in df_r.columns:
        df_r["Nombre"] = pd.to_numeric(df_r["Nombre"], errors="coerce").fillna(0)

    site_donut_svg, site_donut_legend = "", ""
    if not df_r.empty and "Site" in df_r.columns:
        site_donut_svg, site_donut_legend = _donut_chart(
            df_r.groupby("Site")["Nombre"].sum().to_dict(), COULEURS_SITE, "Répartition par site", size=210)

    def _ins_donut(site):
        if df_r.empty or "Installation" not in df_r.columns or "Site" not in df_r.columns:
            return ""
        d = df_r[df_r["Site"] == site].groupby("Installation")["Nombre"].sum().to_dict()
        svg, _ = _donut_chart(d, COULEURS_INS, site, size=185)
        return svg

    meg_ins_svg = _ins_donut("MEG")
    sgb_ins_svg = _ins_donut("SGB")
    toutes_ins = sorted(df_r["Installation"].dropna().unique().tolist()) if (not df_r.empty and "Installation" in df_r.columns) else []
    ins_legend_commune = "".join(
        f'<div style="display:flex;align-items:center;gap:7px;margin-bottom:8px;">'
        f'<span style="width:11px;height:11px;min-width:11px;border-radius:3px;'
        f'background:{COULEURS_INS.get(i,"#94A3B8")};display:inline-block;"></span>'
        f'<span style="font-size:9.5pt;color:#334155;">{i}</span></div>'
        for i in toutes_ins
    )

    # ---- Section 2 : Répartition par site — Nature et Pilote (source : PointsReserveNature) ----
    df_n = df_nature.copy() if (df_nature is not None and not df_nature.empty) else pd.DataFrame()
    if not df_n.empty and "Nombre" in df_n.columns:
        df_n["Nombre"] = pd.to_numeric(df_n["Nombre"], errors="coerce").fillna(0)

    def _nature_donut(site):
        if df_n.empty or "Nature" not in df_n.columns or "Site" not in df_n.columns:
            return "", ""
        d = df_n[df_n["Site"] == site].groupby("Nature")["Nombre"].sum().to_dict()
        return _donut_chart(d, COULEURS_NATURE, f"{site} — % par nature", size=185)

    def _pilote_bar(site):
        if df_n.empty or "Pilote" not in df_n.columns or "Site" not in df_n.columns:
            return ""
        sub = df_n[df_n["Site"] == site]
        total = sub["Nombre"].sum()
        compte = {}
        for _, row in sub.iterrows():
            for e in str(row.get("Pilote", "")).split("+"):
                e = e.strip()
                if not e:
                    continue
                compte[e] = compte.get(e, 0) + row["Nombre"]
        if not compte or not total:
            return ""
        pct_dict = {k: round(v / total * 100, 1) for k, v in sorted(compte.items(), key=lambda x: -x[1])}
        return _hbar_chart(pct_dict, COULEURS_PILOTE, width=300)

    sgb_nature_svg, sgb_nature_legend = _nature_donut("SGB")
    meg_nature_svg, meg_nature_legend = _nature_donut("MEG")
    sgb_pilote_svg = _pilote_bar("SGB")
    meg_pilote_svg = _pilote_bar("MEG")


    carto_html = ""
    if carto_b64:
        carto_html = f"""
        <div class="page">
            <div class="category-title">Taux de non-conformité des sites</div>
            <p style="font-size:10pt;color:#475569;margin-bottom:15px;">
            Cartographie de synthèse du taux de non-conformité par site et par installation,
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
        <div class="header-title">Rapport KPI</div>
        <div class="header-title">Contrôle Réglementaire</div>
        <div class="header-sub">Tunisie Profilés d'Aluminium — Direction Maintenance &amp; TN</div>
        <div class="meta-info">
            <b>Date d'édition :</b> {date_str}<br>
            <b>Objet :</b> Synthèse des indicateurs de performance du suivi de conformité réglementaire —
            taux de réalisation, respect des délais, non-conformités et actions de contrôle.
        </div>

        <div class="category-title">Indicateurs de performance</div>

       





        <div class="kpi-card" style="border-left-color:#0EA5E9;">
            <p class="kpi-title">1. Taux de réalisation 2026</p>
            <p class="kpi-desc">Proportion des visites réalisées dont l'écart entre la date réelle de contrôle
            et l'échéance théorique initiale du cycle n'excède pas 1 mois, par rapport au nombre total
            de visites réalisées.</p>
            <p class="kpi-value">{k1['taux']}%</p>
            {barre(k1['taux'], '#10B981')}
            <p style="font-size:9pt;color:#64748B;margin-top:8px;">{k1['realises']} réalisés / {k1['restants']} non réalisés
            — sur {k1['total']} visites planifiées</p>
        </div>

         <div class="kpi-card">
            <p class="kpi-title">2. Taux de respect de délai de visite</p>
            <p class="kpi-desc">Proportion des contrôles réglementaires dont l'échéance théorique est comprise
            entre le 01/01/2026 et le 31/12/2026, effectivement réalisés (date réelle de visite enregistrée)
            par rapport au nombre total de contrôles dus sur cette période.</p>
            <p class="kpi-value">{k2['taux']}%</p>
            {barre(k2['taux'], '#0EA5E9')}
            <p style="font-size:9pt;color:#64748B;margin-top:8px;">{k2['respectes']} respectés / {k2['respectes']} réalisés</p>
        </div>


    </div>

    {carto_html}

    <div class="page">
        <div class="category-title">Répartition par site et par installation</div>
        <p style="font-size:10pt;color:#475569;margin-bottom:15px;">
        Répartition des actions de contrôle relevées, par site et par installation.</p>

        <div style="display:flex;justify-content:center;gap:30px;align-items:center;margin-bottom:10px;">
            <div>
                {site_donut_svg if site_donut_svg else "<p style='color:#94A3B8;font-size:9pt;'>Aucune donnée</p>"}
            </div>
            <div>{site_donut_legend}</div>
        </div>

        <p style="font-weight:700;font-size:12pt;color:#0F172A;text-align:center;margin:20px 0 12px 0;">
        Répartition par installation</p>

        <div style="display:flex;justify-content:center;align-items:center;gap:15px;">
            <div style="flex:1;text-align:center;">
                {meg_ins_svg if meg_ins_svg else "<p style='color:#94A3B8;font-size:9pt;'>Aucune donnée MEG</p>"}
            </div>
            <div style="flex:0 0 170px;">{ins_legend_commune}</div>
            <div style="flex:1;text-align:center;">
                {sgb_ins_svg if sgb_ins_svg else "<p style='color:#94A3B8;font-size:9pt;'>Aucune donnée SGB</p>"}
            </div>
        </div>
    </div>

    <div class="page">
        <div class="category-title">Répartition par site : Nature et Pilote</div>
        <p style="font-size:10pt;color:#475569;margin-bottom:15px;">
        Répartition des actions de contrôle relevées, par nature et par pilote, pour chaque site.</p>

        <p style="font-weight:700;font-size:12pt;color:#0F172A;margin:10px 0 12px 0;">SGB</p>
        <div style="display:flex;align-items:center;gap:25px;margin-bottom:25px;">
            <div style="flex:0 0 auto;">
                {sgb_nature_svg if sgb_nature_svg else "<p style='color:#94A3B8;font-size:9pt;'>Aucune donnée</p>"}
            </div>
            <div style="flex:0 0 150px;">{sgb_nature_legend}</div>
            <div style="flex:1;">
                {sgb_pilote_svg if sgb_pilote_svg else "<p style='color:#94A3B8;font-size:9pt;'>Aucune donnée</p>"}
            </div>
        </div>

        <p style="font-weight:700;font-size:12pt;color:#0F172A;margin:10px 0 12px 0;">MEG</p>
        <div style="display:flex;align-items:center;gap:25px;">
            <div style="flex:0 0 auto;">
                {meg_nature_svg if meg_nature_svg else "<p style='color:#94A3B8;font-size:9pt;'>Aucune donnée</p>"}
            </div>
            <div style="flex:0 0 150px;">{meg_nature_legend}</div>
            <div style="flex:1;">
                {meg_pilote_svg if meg_pilote_svg else "<p style='color:#94A3B8;font-size:9pt;'>Aucune donnée</p>"}
            </div>
        </div>
    </div>

    </body></html>
    """


    return HTML(string=html_content).write_pdf()


def generer_rapport_pilote_pdf(pilote_choisi, df_filtre, logo_url):
    """
    Génère un rapport PDF (format paysage) listant, pour un pilote donné, toutes les actions de
    la codification (classeur externe) qui le concernent — une page par installation
    (= un onglet du classeur source), sous forme de fiche de suivi terrain :
    Equipement | Actions | Responsable | Etat (Immédiat/Sous-traitant*/Planifié*) | Réalisation (O/N) | Observation.
    df_filtre doit contenir les colonnes : Installation, Designation, Observation, Code, Nature.
    """
    date_str = datetime.date.today().strftime('%d/%m/%Y')
    installations = list(dict.fromkeys(df_filtre["Installation"].tolist()))  # ordre stable, sans doublons
    total_general = len(df_filtre)
    nom_responsable = SOUS_PILOTE_NOMS.get(pilote_choisi, pilote_choisi)

    html_content = f"""
    <html>
    <head>
    <style>
        @page {{
            size: A4 landscape;
            margin: 15mm 12mm;
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
        .page {{ page-break-after: always; }}
        .page:last-child {{ page-break-after: avoid; }}
        .header-title {{
            text-align: center;
            font-size: 16pt;
            font-weight: bold;
            color: #1E3A8A;
            margin-bottom: 14px;
            text-transform: uppercase;
            border-bottom: 2px solid #1E3A8A;
            padding-bottom: 8px;
        }}
        .page-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #E2E8F0;
        }}
        .page-header img {{ height: 32px; }}
        .page-header-text {{
            font-size: 9.5pt;
            color: #64748B;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }}
        .meta-info {{
            margin-bottom: 14px;
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            padding: 10px 15px;
            border-radius: 6px;
            line-height: 1.7;
            font-size: 10.5pt;
        }}
        .category-title {{
            font-size: 13pt;
            color: #0EA5E9;
            font-weight: bold;
            margin-top: 6px;
            margin-bottom: 10px;
            border-left: 4px solid #0EA5E9;
            padding-left: 8px;
        }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 14px; }}
        th, td {{ border: 1px solid #CBD5E1; padding: 6px; text-align: left; font-size: 8.5pt; vertical-align: middle; }}
        th {{
            background-color: #1406BE; color: #FFFFFF; font-weight: bold;
            text-align: center; font-size: 8.5pt;
        }}
        .col-equip  {{ width: 13%; }}
        .col-action {{ width: 22%; }}
        .col-resp   {{ width: 10%; text-align: center; }}
        .col-etat   {{ width: 7%; text-align: center; }}
        .col-real   {{ width: 9%; text-align: center; }}
        .col-obs    {{ width: 25%; }}
        .td-chk {{ text-align: center; }}
        .checkbox-box {{
            display: inline-block;
            width: 13px;
            height: 13px;
            border: 1.5px solid #1E293B;
            border-radius: 3px;
        }}
        .footnote {{
            font-size: 8pt;
            color: #475569;
            margin-top: 4px;
        }}
        .total-badge {{
            display: inline-block; background:#0EA5E9; color:white; font-weight:700;
            padding:3px 12px; border-radius:12px; font-size:9pt; margin-left:8px;
        }}
        .table-synthese th {{
            background-color: #1406BE; color: #FFFFFF; font-weight: bold;
            text-align: center; font-size: 9pt;
        }}
        .table-synthese td {{
            font-size: 9.5pt;
        }}
        .table-synthese .ligne-total td {{
            font-weight: bold;
            background-color: #F1F5F9;
        }}
        .synthese-cadre {{
            border: 1.5px solid #1E3A8A;
            border-radius: 6px;
            padding: 12px 15px;
            margin-top: 10px;
            min-height: 260px;
        }}
        .synthese-titre {{
            font-size: 11pt;
            font-weight: bold;
            color: #1E3A8A;
            margin-bottom: 10px;
        }}
    </style>
    </head>
    <body>
    """

    for ins in installations:
        d_ins = df_filtre[df_filtre["Installation"] == ins]
        html_content += f"""
        <div class="page">
            <div class="page-header">
                <img src="{logo_url}"/>
                <div class="page-header-text">Tunisie Profilés d'Aluminium — Direction Maintenance &amp; TN</div>
            </div>
            <div class="header-title" style="border-bottom: none; padding-bottom: 0;">Plan d'actions - Contrôle réglementaire</div>
            <div class="meta-info">
                <strong>Sous-pilote :</strong> {nom_responsable}<br>
                <strong>Installation :</strong> {ins}<br>
                <strong>Date d'édition :</strong> {date_str}
            </div>
            <div class="category-title">{ins} <span class="total-badge">{len(d_ins)} action(s)</span></div>
            <table>
                <thead>
                    <tr>
                        <th class="col-equip" rowspan="2">Equipement</th>
                        <th class="col-action" rowspan="2">Actions</th>
                        <th class="col-resp" rowspan="2">Responsable</th>
                        <th colspan="3">Etat de suivi</th>
                        <th class="col-real" rowspan="2">Réalisation<br>(O/N)</th>
                        <th class="col-obs" rowspan="2">Suivi d'avancement *</th>
                    </tr>
                    <tr>
                        <th class="col-etat">Immédiat</th>
                        <th class="col-etat">Sous-traitant*</th>
                        <th class="col-etat">Planifié*</th>
                    </tr>
                </thead>
                <tbody>
        """
        if not d_ins.empty:
            for equip, span, observation in _lignes_avec_rowspan(d_ins):
                html_content += "<tr>"
                if span is not None:
                    html_content += f'<td rowspan="{span}">{equip}</td>'
                html_content += f"""
                        <td>{observation}</td>
                        <td class="col-resp"></td>
                        <td class="td-chk"><span class="checkbox-box"></span></td>
                        <td class="td-chk"><span class="checkbox-box"></span></td>
                        <td class="td-chk"><span class="checkbox-box"></span></td>
                        <td></td>
                        <td></td>
                    </tr>
                """
        else:
            html_content += """
                <tr><td colspan="8" style="text-align:center;color:#94A3B8;font-style:italic;">Aucune action</td></tr>
            """
        html_content += """
                </tbody>
            </table>
            <div class="footnote">(*) Suivi d'avancement : Date de réalisation, Besoin PDR, Lancement DA, Nom de sous-traitant...</div>
        </div>
        """

    footnote_synthese = ('<div class="footnote">(*) Suivi d\'avancement : Date de réalisation, Besoin PDR, '
                          'Lancement DA, Nom de sous-traitant...</div>')

    lignes_synthese_tableau = ""
    for ins in installations:
        nb_ins = len(df_filtre[df_filtre["Installation"] == ins])
        lignes_synthese_tableau += f"""
                    <tr>
                        <td>{ins}</td>
                        <td style="text-align:center;">{nb_ins}</td>
                        <td style="text-align:center;"></td>
                    </tr>
        """

    html_content += f"""
    <div class="page">
        <div class="page-header">
            <img src="{logo_url}"/>
            <div class="page-header-text">Tunisie Profilés d'Aluminium — Direction Maintenance &amp; TN</div>
        </div>
        <div class="header-title">Plan d'actions - Contrôle réglementaire</div>
        <div class="meta-info">
            <strong>Sous-pilote :</strong> {nom_responsable}<br>
            <strong>Total des actions :</strong> {total_general} action(s)<br>
            <strong>Date d'édition :</strong> {date_str}
        </div>

        <table class="table-synthese">
            <thead>
                <tr>
                    <th style="width:50%;">Installation</th>
                    <th style="width:25%;">Nombre d'actions</th>
                    <th style="width:25%;">Taux de réalisation</th>
                </tr>
            </thead>
            <tbody>
                {lignes_synthese_tableau}
                <tr class="ligne-total">
                    <td>Total</td>
                    <td style="text-align:center;">{total_general}</td>
                    <td style="text-align:center;"></td>
                </tr>
            </tbody>
        </table>

        <div class="synthese-cadre">
            <div class="synthese-titre">Synthèse / Observations et remarques</div>
        </div>
    </div>
    </body>
    </html>
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
# Classeur externe "Classification des actions CR 2026" : un onglet par installation,
# colonnes Désignation | Observation | Code (T/S/E/D/O/R). Utilisé pour le rapport PDF par pilote.
CODIF_SHEET_ID = "119hyynlCiIUzf-17iiSkcPnaEr2oCiFC"
SEUIL_EN_LIGNE_SECONDES = 90
calendar.setfirstweekday(0)

PERIODICITE = {
    "Installations électriques": 6,
    "Equipements de levage":     12,
    "Sécurité incendie":         12,
    "Installations de gaz":      12,
    "Appareil pression de gaz":  12,
}
COULEURS_INS = {
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

    /* Champ e-mail (page de connexion visiteur) : fond gris, coins arrondis, style aligné sur la maquette */
    div[data-testid="stTextInput"] input{
        background-color:#F1F5F9!important;
        border:1px solid #E2E8F0!important;
        border-radius:8px!important;
        padding:12px 16px!important;
        font-size:14px!important;
        color:#334155!important;
    }
    div[data-testid="stTextInput"] input:focus{
        border-color:#0EA5E9!important;
        box-shadow:0 0 0 3px rgba(14,165,233,0.12)!important;
        background-color:#FFFFFF!important;
    }
    div[data-testid="stTextInput"] input::placeholder{color:#94A3B8!important;}

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
        background-color:#16A34A!important;
        color:white!important;
        border-radius:8px!important;
        border:none!important;
        font-weight:600!important;
    }
    .stDownloadButton>button:hover{background-color:#15803D!important;}
    button[kind="primary"]{
        background-color:#1E3A8A!important;
        color:white!important;
        border-radius:8px!important;
        border:none!important;
        font-weight:600!important;
    }
    button[kind="primary"]:hover{background-color:#1D4ED8!important;}
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
        entetes = [str(c).strip() for c in valeurs[0]]
        nb_col = len(entetes)
        # Complète les lignes trop courtes avec des cellules vides (Google Sheets omet les cellules vides en fin de ligne)
        lignes = [ (r + [""]*(nb_col-len(r)))[:nb_col] for r in valeurs[1:] ]
        df = pd.DataFrame(lignes,columns=entetes)
        # Nettoie les espaces superflus dans toutes les valeurs texte pour éviter les non-correspondances silencieuses
        for c in df.columns:
            if df[c].dtype == object:
                df[c] = df[c].astype(str).str.strip()
        return df
    except Exception:
        return pd.DataFrame()

def _obtenir_token_scope(scope):
    """Comme obtenir_access_token(), mais permet de demander un scope OAuth différent
    (ex: Drive en lecture) avec le même compte de service."""
    try:
        import jwt as pyjwt
        private_key  = st.secrets["connections"]["gsheets"]["private_key"]
        client_email = st.secrets["connections"]["gsheets"]["client_email"]
        now = int(time.time())
        payload = {"iss":client_email,"scope":scope,
                   "aud":"https://oauth2.googleapis.com/token","exp":now+3600,"iat":now}
        token_jwt = pyjwt.encode(payload, private_key, algorithm="RS256")
        resp = requests.post("https://oauth2.googleapis.com/token",
            data={"grant_type":"urn:ietf:params:oauth:grant-type:jwt-bearer","assertion":token_jwt},timeout=15)
        return resp.json()["access_token"] if resp.status_code==200 else None
    except Exception:
        return None


def codif_charger_classeur(sheet_id):
    """Télécharge le classeur de codification via l'API Google Drive (fonctionne même si le
    fichier est un .xlsx uploadé et jamais converti en Google Sheets natif, contrairement à
    l'API Sheets). Retourne (dict {nom_onglet: DataFrame_brut_sans_entete}, message_erreur)."""
    token = _obtenir_token_scope("https://www.googleapis.com/auth/drive.readonly")
    if not token:
        return None, "Impossible d'obtenir un jeton d'accès Google (scope Drive)."
    try:
        url = f"https://www.googleapis.com/drive/v3/files/{sheet_id}?alt=media"
        resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
        if resp.status_code in (403, 404):
            try:
                email = st.secrets["connections"]["gsheets"]["client_email"]
            except Exception:
                email = "(voir le champ client_email de vos secrets)"
            return None, (f"Accès refusé au fichier de codification. Partagez-le (en lecture) "
                           f"avec le compte de service : {email}")
        if resp.status_code != 200:
            return None, f"Erreur API Google Drive ({resp.status_code}) : {resp.text[:300]}"
        classeur = pd.read_excel(io.BytesIO(resp.content), sheet_name=None, header=None, engine="openpyxl")
        return classeur, None
    except Exception as e:
        return None, f"Erreur inattendue lors de la lecture du fichier Excel : {e}"


def _detecter_entete_et_nettoyer_codif(valeurs):
    """Prend les lignes brutes (liste de listes) d'un onglet du classeur de codification et
    retourne un DataFrame propre avec les colonnes Designation | Observation | Code.
    Cherche automatiquement la ligne d'en-tête, en tolérant les différents intitulés utilisés
    selon les onglets (ex: 'Désignation'/'Rapport' pour l'équipement,
    'Observation'/'Organes examinés NC'/'Problème' pour l'action), et complète (forward-fill)
    les cellules d'équipement fusionnées verticalement dans la feuille source."""
    if not valeurs:
        return pd.DataFrame()

    MOTS_CLES_EQUIP = ["désignation", "designation", "équipement", "equipement", "rapport"]
    MOTS_CLES_OBS   = ["observation", "organe", "examin", "problème", "probleme", "action"]

    idx_entete = None
    for i, ligne in enumerate(valeurs):
        cellules = [str(c).strip().lower() for c in ligne]
        a_equip = any(any(mc in c for mc in MOTS_CLES_EQUIP) for c in cellules)
        a_obs   = any(any(mc in c for mc in MOTS_CLES_OBS) for c in cellules)
        if a_equip and a_obs:
            idx_entete = i
            break
    if idx_entete is None:
        return pd.DataFrame()

    entetes = [str(c).strip() for c in valeurs[idx_entete]]
    nb_col = len(entetes)
    lignes = valeurs[idx_entete + 1:]
    lignes = [(list(r) + [""] * (nb_col - len(r)))[:nb_col] for r in lignes]
    df = pd.DataFrame(lignes, columns=entetes)

    def _trouver_colonne(colonnes, groupes_mots_cles):
        """Cherche la colonne correspondant au groupe de mots-clés le plus spécifique possible
        (on essaie groupe par groupe, du plus spécifique au plus générique, et on ne retombe sur
        un groupe générique — ex: 'rapport', 'action' — que si aucune colonne plus spécifique
        n'a matché, pour éviter de capturer par erreur une autre colonne du même onglet)."""
        for groupe in groupes_mots_cles:
            for c in colonnes:
                if any(mc in c.lower() for mc in groupe):
                    return c
        return None

    col_desig = _trouver_colonne(df.columns, [
        ["désignation", "designation", "équipement", "equipement"],
        ["rapport"],
    ])
    col_obs = _trouver_colonne(df.columns, [
        ["observation"],
        ["organe", "examin"],
        ["problème", "probleme"],
        ["action"],
    ])
    col_code  = next((c for c in df.columns if c.strip().lower() in ("c", "code")), None)
    if not (col_desig and col_obs and col_code):
        return pd.DataFrame()

    df = df[[col_desig, col_obs, col_code]].copy()
    df.columns = ["Designation", "Observation", "Code"]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
        df[c] = df[c].replace("nan", "")
    df["Designation"] = df["Designation"].replace("", pd.NA).ffill().fillna("")
    df["Code"] = df["Code"].str.upper()
    df = df[(df["Observation"] != "") & (df["Code"] != "")]
    df = df[df["Code"].isin(NATURE_PILOTE.keys())]
    return df.reset_index(drop=True)


def _codes_pour_pilote(pilote_choisi):
    """Retourne la liste des codes (T,S,E,D,O,R) dont le champ Pilote (potentiellement
    combiné avec '+') contient l'entité choisie."""
    codes = []
    for code, (_, pilote_str) in NATURE_PILOTE.items():
        entites = [e.strip() for e in pilote_str.split("+") if e.strip()]
        if pilote_choisi in entites:
            codes.append(code)
    return codes


def _lignes_avec_rowspan(d_ins):
    """Regroupe les lignes consécutives ayant le même Equipement (Designation) pour permettre
    une fusion de cellules (rowspan) dans le tableau PDF.
    Retourne une liste de tuples (equipement_ou_None, rowspan_ou_None, observation)."""
    valeurs = d_ins["Designation"].tolist()
    obs = d_ins["Observation"].tolist()
    lignes = []
    i, n = 0, len(valeurs)
    while i < n:
        j = i
        while j < n and valeurs[j] == valeurs[i]:
            j += 1
        span = j - i
        lignes.append((valeurs[i], span, obs[i]))
        for k in range(i + 1, j):
            lignes.append((None, None, obs[k]))
        i = j
    return lignes



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


def ajouter_equipement(site, installation, sous_eq, nombre):
    """Ajoute une ligne équipement dans Exigences."""
    return sheets_append("Exigences", ["Equipement", site, installation, sous_eq, str(nombre), ""])


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
# Actions de contrôle (onglet dédié "PointsReserve")
# ==========================================
def lire_points_reserve():
    """Lit l'onglet PointsReserve : Site | Installation | Sous_equipement | Nombre."""
    return sheets_lire("PointsReserve", "A:D")


def ajouter_point_reserve(site, installation, sous_eq, nombre):
    """Ajoute une ligne dans l'onglet PointsReserve."""
    return sheets_append("PointsReserve", [site, installation, sous_eq, str(nombre)])


# ==========================================
# Actions de contrôle PAR NATURE (onglet dédié "PointsReserveNature")
# Table KPI : Site | Installation | Nombre de actions | Nature | Pilote
# Le pilote est déduit automatiquement du code de la nature.
# ==========================================
NATURE_PILOTE = {
    "T": ("Technique",      "Maintenance"),
    "S": ("Sécurité",       "HSE"),
    "E": ("Energétique",    "BT + Maintenance"),
    "D": ("Documentation",  "BT + HSE"),
    "O": ("Organisation",   "DMTN + Chef service BT"),
    "R": ("Règlementation", "BT + HSE + RH + DG"),
}

# Nom du sous-pilote (personne responsable) associé à chaque entité de pilotage.
# Les entités non listées ici (ex: DMTN) affichent l'entité elle-même à défaut de nom connu.
SOUS_PILOTE_NOMS = {
    "Maintenance":     "Saber BEN CHAABEN",
    "HSE":             "Montassar MEHRABI",
    "BT":              "Aïcha BELLAKHAL",
    "Chef service BT": "Aïcha BELLAKHAL",
    "RH":              "Aïcha BELLAKHAL",
    "DG":              "Aïcha BELLAKHAL",
}

def lire_points_reserve_nature():
    """Lit l'onglet PointsReserveNature : Site | Installation | Nombre | Nature | Pilote."""
    return sheets_lire("PointsReserveNature", "A:E")


def ajouter_point_reserve_nature(site, installation, nombre, code_nature):
    """Ajoute une ligne dans l'onglet PointsReserveNature. Le pilote est calculé depuis le code de la nature."""
    nature_nom, pilote = NATURE_PILOTE[code_nature]
    return sheets_append("PointsReserveNature", [site, installation, str(nombre), nature_nom, pilote])


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

# ==========================================
# EN-TÊTE (toujours affiché en premier, connecté ou non)
# ==========================================
# --> Renseignez ici le nom (ou le chemin) de votre fichier image PNG déjà importé
MAINTENANCE_ICON_PATH = "unnamed.png"

col_titre, col_icone = st.columns([5,1])
with col_titre:
    st.markdown("""<div class="app-header-block" style="width:100%;margin:10px auto 0 auto;">
    <h1 style="text-align:center;font-size:2.6rem;font-weight:800;color:#0F172A;margin:0 0 6px 0;letter-spacing:-1px;line-height:1.2;">Tableau de Bord Réglementaire</h1>
    <p style="text-align:center;font-size:1.05rem;color:#64748B;margin:0 auto;font-weight:400;line-height:1.5;max-width:800px;">L'amélioration continue.. Notre trajectoire..</p>
</div>""",unsafe_allow_html=True)
with col_icone:
    st.image(MAINTENANCE_ICON_PATH, use_container_width=True)

if not acces_autorise and role=="Visiteur":
    st.markdown("""<div style="margin-bottom:14px;">
        <p style="color:#0F172A;font-size:15px;font-weight:700;margin:0 0 6px 0;">Adresse e-mail :</p>
        <p style="color:#64748B;font-size:13.5px;margin:0;line-height:1.5;">Veuillez renseigner votre adresse e-mail.</p>
    </div>""",unsafe_allow_html=True)
    email_saisi=st.text_input("Adresse e-mail :",placeholder="exemple@domain.com",label_visibility="collapsed")
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
# CONTENU PRINCIPAL
# ==========================================
if acces_autorise:
    val_total=len(df_rapports) if not df_rapports.empty else 0

    # ---- Contrôles réalisés en 2026 / total des contrôles suivis (même dédup que les KPI) ----
    col_reelle_hdr = [c for c in df_rapports.columns if "reelle" in c.lower() or "réelle" in c.lower()]
    col_ins_hdr    = [c for c in df_rapports.columns if "ins" in c.lower()]
    col_site_hdr   = [c for c in df_rapports.columns if "site" in c.lower()]
    col_label_hdr  = [c for c in df_rapports.columns if "equip" in c.lower() or "label" in c.lower() or "nom" in c.lower()]
    col_date_hdr   = [c for c in df_rapports.columns if "date" in c.lower() and "reelle" not in c.lower() and "réelle" not in c.lower() and "prochaine" not in c.lower() and "planifi" not in c.lower()]

    # ---- Contrôles 2026 réalisés PAR SITE (SGB / MEG), PAR CATÉGORIE d'installation (et non par équipement) ----
    # Périodicité : Installations électriques = 2 campagnes/an, les 4 autres catégories = 1 campagne/an
    # => 2 + 1 + 1 + 1 + 1 = 6 campagnes attendues par site sur l'année 2026
    def _nb_campagnes_attendues_hdr(installation):
        return round(12 / PERIODICITE.get(installation, 12))

    TOTAL_CATEGORIES_PAR_SITE = sum(_nb_campagnes_attendues_hdr(ins) for ins in PERIODICITE.keys())  # = 6

    nb_ctrl_site = {"SGB": 0, "MEG": 0}
    if not df_rapports.empty and col_ins_hdr and col_date_hdr:
        df_hdr = df_rapports.copy()
        df_hdr["_date_brute"]  = pd.to_datetime(df_hdr[col_date_hdr[0]], dayfirst=True, errors='coerce')
        df_hdr["_date_reelle"] = pd.to_datetime(df_hdr[col_reelle_hdr[0]], dayfirst=True, errors='coerce') if col_reelle_hdr else pd.NaT
        df_hdr = df_hdr.dropna(subset=["_date_brute"])
        df_realises_hdr = df_hdr[df_hdr["_date_reelle"].notna() & (df_hdr["_date_reelle"].dt.year == 2026)]
        if col_site_hdr and col_ins_hdr:
            for site_h in ("SGB", "MEG"):
                df_site_h = df_realises_hdr[df_realises_hdr[col_site_hdr[0]].astype(str).str.strip().str.upper() == site_h]
                total_site = 0
                for ins_h in PERIODICITE.keys():
                    attendu_h = _nb_campagnes_attendues_hdr(ins_h)
                    df_grp_h  = df_site_h[df_site_h[col_ins_hdr[0]].astype(str).str.strip() == ins_h]
                    nb_camp_h = df_grp_h["_date_brute"].nunique() if not df_grp_h.empty else 0
                    total_site += min(nb_camp_h, attendu_h)
                nb_ctrl_site[site_h] = total_site

    def _pct_et_couleur(nb, total):
        pct = round(nb/total*100) if total>0 else 0
        couleur = "#10B981" if pct>=80 else "#F97316" if pct>=50 else "#EF4444"
        return pct, couleur

    pct_sgb, couleur_sgb = _pct_et_couleur(nb_ctrl_site["SGB"], TOTAL_CATEGORIES_PAR_SITE)
    pct_meg, couleur_meg = _pct_et_couleur(nb_ctrl_site["MEG"]-1, TOTAL_CATEGORIES_PAR_SITE)

    k1,k2=st.columns(2)
    with k1:
        st.markdown(f"""<div style="background:white;padding:22px;border-radius:12px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);border-left:5px solid #1E3A8A;height:118px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;">
            <p style="margin:0;font-size:12px;color:#64748B;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Total Rapports Archivés</p>
            <p style="margin:8px 0 0 0;font-size:34px;color:#0F172A;font-weight:700;line-height:1;">{val_total}</p></div>""",unsafe_allow_html=True)
    with k2:
        st.markdown(f"""<div style="background:white;padding:22px;border-radius:12px;box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);border-left:5px solid #0EA5E9;height:118px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;gap:8px;">
            <p style="margin:0;font-size:12px;color:#64748B;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Contrôles Réalisés 2026</p>
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:11px;color:#334155;font-weight:700;width:32px;flex-shrink:0;">SGB</span>
                <div style="flex:1;height:8px;background:#E2E8F0;border-radius:4px;overflow:hidden;">
                    <div style="width:{pct_sgb}%;height:100%;background:{couleur_sgb};border-radius:4px;"></div>
                </div>
                <span style="font-size:11px;color:{couleur_sgb};font-weight:700;white-space:nowrap;width:70px;text-align:right;">{nb_ctrl_site["SGB"]}/{TOTAL_CATEGORIES_PAR_SITE} ({pct_sgb}%)</span>
            </div>
            <div style="display:flex;align-items:center;gap:8px;">
                <span style="font-size:11px;color:#334155;font-weight:700;width:32px;flex-shrink:0;">MEG</span>
                <div style="flex:1;height:8px;background:#E2E8F0;border-radius:4px;overflow:hidden;">
                    <div style="width:{pct_meg}%;height:100%;background:{couleur_meg};border-radius:4px;"></div>
                </div>
                <span style="font-size:11px;color:{couleur_meg};font-weight:700;white-space:nowrap;width:70px;text-align:right;">{nb_ctrl_site["MEG"]-1}/{TOTAL_CATEGORIES_PAR_SITE} ({pct_meg}%)</span>
            </div></div>""",unsafe_allow_html=True)

    st.markdown("<br>",unsafe_allow_html=True)

    liste_onglets = ["📋 Rapports CR","📅 Planification","📌 Exigences"]
    if role == "Responsable" and password_correct:
        liste_onglets.append("👥 Statistiques")
    liste_onglets.append("📊 KPI")
    onglets = st.tabs(liste_onglets)
    tab1, tab2, tab_exigences = onglets[0], onglets[1], onglets[2]
    tab3 = None
    tab_kpi = None
    _idx = 3
    if role == "Responsable" and password_correct:
        tab3 = onglets[_idx]; _idx += 1
    tab_kpi = onglets[_idx]

    def convertir_lien(url):
        try:
            if "drive.google.com" in str(url) and "/file/d/" in str(url):
                file_id = str(url).split('/file/d/')[1].split('/')[0]
                return f"https://drive.google.com/file/d/{file_id}/preview"
        except Exception: pass
        return url
    
    # ---- ONGLET 1 : RAPPORTS ----
    with tab1:
        st.markdown("""<style>
            .filter-title{text-align:center!important;font-weight:600;color:#1E293B;margin-top:0;margin-bottom:15px;width:100%;}
            div[data-testid="stSelectbox"] label p{text-align:center!important;width:100%;display:block;}
        </style>""",unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("<p class='filter-title'>Filtres de recherche</p>",unsafe_allow_html=True)
            c1,c2,c3,c4=st.columns(4)
            with c1: f_site =st.selectbox("Site",["Tous","SGB","MEG"])
            with c2: f_annee=st.selectbox("Année",["Tous","2025","2026"])
            with c3: f_ins  =st.selectbox("Installation",["Tous"]+list(SOUS_EQUIPEMENTS.keys()))
            with c4:
                opts=["Tous"]+SOUS_EQUIPEMENTS[f_ins] if f_ins!="Tous" else ["Tous"]+[i for sub in SOUS_EQUIPEMENTS.values() for i in sub]
                f_sous_eq=st.selectbox("Sous-équipement",opts)

        st.markdown("<br><p style='font-size:1.2rem;font-weight:700;color:#0F172A;margin-bottom:10px;'>📂 Documents rattachés</p>",unsafe_allow_html=True)
        df_f=df_rapports.copy()
        col_site=[c for c in df_f.columns if "site" in c.lower()]
        col_ex  =[c for c in df_f.columns if "exerc" in c.lower() or "ann" in c.lower()]
        col_ins =[c for c in df_f.columns if "ins" in c.lower()]
        col_seq =[c for c in df_f.columns if "sous" in c.lower()]
        col_lien=[c for c in df_f.columns if "lien" in c.lower() or "pdf" in c.lower()]
        col_date=[c for c in df_f.columns if "date" in c.lower() or "contr" in c.lower()]
        if not df_f.empty:
            if f_site !="Tous" and col_site: df_f=df_f[df_f[col_site[0]].astype(str).str.strip()==f_site]
            if f_annee!="Tous" and col_ex:   df_f=df_f[pd.to_numeric(df_f[col_ex[0]],errors='coerce')==int(f_annee)]
            if f_ins  !="Tous" and col_ins:  df_f=df_f[df_f[col_ins[0]].astype(str).str.strip()==f_ins]
            if f_sous_eq!="Tous" and col_seq:df_f=df_f[df_f[col_seq[0]].astype(str).str.strip()==f_sous_eq]
            if col_lien: df_f[col_lien[0]]=df_f[col_lien[0]].apply(convertir_lien)
            if col_date: df_f[col_date[0]]=pd.to_datetime(df_f[col_date[0]],dayfirst=True,errors='coerce')
        if not df_f.empty:
            col_reelle_doc=[c for c in df_f.columns if "reelle" in c.lower() or "réelle" in c.lower()]
            if col_reelle_doc: df_f=df_f.drop(columns=col_reelle_doc)
            col_planifiee_doc=[c for c in df_f.columns if "planifi" in c.lower()]
            if col_planifiee_doc: df_f=df_f.drop(columns=col_planifiee_doc)
            col_prochaine_doc=[c for c in df_f.columns if "prochaine" in c.lower()]
            if col_prochaine_doc: df_f=df_f.drop(columns=col_prochaine_doc)
            st.dataframe(df_f,column_config={
                (col_lien[0] if col_lien else "Lien PDF"):st.column_config.LinkColumn("Action",display_text="Voir le rapport"),
                (col_ex[0]   if col_ex   else "Année"):st.column_config.NumberColumn("Année",format="%d"),
                (col_date[0] if col_date else "Date"):    st.column_config.DateColumn("Date de dernier contrôle",format="DD/MM/YYYY"),
            },hide_index=True,use_container_width=True)
        else:
            st.warning("Aucun rapport ne correspond aux critères sélectionnés.")

        st.markdown("<br><hr style='border-color:#E2E8F0;'><p style='font-size:1.2rem;font-weight:700;color:#0F172A;'>📊 Gestion des rapports</p>",unsafe_allow_html=True)
        if not df_rapports.empty:
            col_sc=[c for c in df_rapports.columns if "site" in c.lower()]
            col_cc=[c for c in df_rapports.columns if "ins" in c.lower()]
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
        st.markdown("<br><p style='font-size:1.2rem;font-weight:700;color:#0F172A;'>📅 Prochaines échéances</p>",unsafe_allow_html=True)

        # ---- FILTRES ÉCHÉANCES ----
        with st.container(border=True):
            st.markdown("<p style='font-weight:600;color:#1E293B;margin:0 0 10px 0;font-size:13px;'>🔍 Filtrer les échéances</p>",unsafe_allow_html=True)
            fc1,fc2,fc3=st.columns(3)
            with fc1: f_ech_site=st.selectbox("Site",["Tous","SGB","MEG"],key="f_ech_site")
            with fc2: f_ech_ins =st.selectbox("Installation",["Tous"]+list(PERIODICITE.keys()),key="f_ech_ins")
            with fc3:
                opts_seq=["Tous"]+SOUS_EQUIPEMENTS.get(f_ech_ins,[]) if f_ech_ins!="Tous" else ["Tous"]+[i for sub in SOUS_EQUIPEMENTS.values() for i in sub]
                f_ech_seq=st.selectbox("Sous-équipement",opts_seq,key="f_ech_seq")

        if not df_rapports.empty:
            col_ins_r  =[c for c in df_rapports.columns if "ins" in c.lower()]
            col_date_r =[c for c in df_rapports.columns if "date" in c.lower() and "reelle" not in c.lower() and "réelle" not in c.lower() and "prochaine" not in c.lower()]
            col_site_r =[c for c in df_rapports.columns if "site" in c.lower()]
            col_label_r=[c for c in df_rapports.columns if "equip" in c.lower() or "label" in c.lower() or "nom" in c.lower()]
            col_reelle =[c for c in df_rapports.columns if "reelle" in c.lower() or "réelle" in c.lower()]
            col_prochaine_r=[c for c in df_rapports.columns if "prochaine" in c.lower()]

            if col_ins_r and col_date_r:
                df_ech=df_rapports.copy()
                # Identifiant stable = numéro de ligne réel dans le Sheet (header=ligne1, donc +2)
                df_ech["_ligne_sheet"]=df_ech.index+2
                df_ech["_date_brute"]=pd.to_datetime(df_ech[col_date_r[0]],dayfirst=True,errors='coerce')

                if col_reelle:
                    df_ech["_date_reelle"]=pd.to_datetime(df_ech[col_reelle[0]],dayfirst=True,errors='coerce')
                else:
                    df_ech["_date_reelle"]=pd.NaT

                if col_prochaine_r:
                    df_ech["_prochaine_manuelle"]=pd.to_datetime(df_ech[col_prochaine_r[0]],dayfirst=True,errors='coerce')
                else:
                    df_ech["_prochaine_manuelle"]=pd.NaT

                # Date de dernière visite = date réelle si dispo, sinon date planifiée initiale
                df_ech["_date"]=df_ech["_date_reelle"].combine_first(df_ech["_date_brute"])
                df_ech=df_ech.dropna(subset=["_date"])

                # Déduplication
                cles=[]
                if col_site_r:  cles.append(col_site_r[0])
                cles.append(col_ins_r[0])
                if col_label_r: cles.append(col_label_r[0])
                df_ech=df_ech.sort_values("_date_brute",ascending=True)
                df_ech=df_ech.drop_duplicates(subset=cles,keep="last")

                today_dt=pd.Timestamp.today().normalize()

                def calc_prochaine(row):
                    # Priorité à une échéance saisie manuellement par le responsable,
                    # sinon calcul automatique selon la périodicité de l'installation
                    if pd.notna(row["_prochaine_manuelle"]):
                        return row["_prochaine_manuelle"]
                    mois=PERIODICITE.get(str(row[col_ins_r[0]]).strip(),12)
                    return row["_date"]+pd.DateOffset(months=mois)

                df_ech["Prochaine échéance"]=df_ech.apply(calc_prochaine,axis=1)
                df_ech["Jours restants"]=(df_ech["Prochaine échéance"]-today_dt).dt.days
                df_ech["Statut"]=df_ech["Jours restants"].apply(
                    lambda j:"⚠️ Dépassé" if j<0 else "🔴 Urgent" if j<30 else "🟡 Proche" if j<90 else "🟢 OK")

                cols_affich=[]
                if col_site_r:  cols_affich.append(col_site_r[0])
                if col_label_r: cols_affich.append(col_label_r[0])
                cols_affich+=[col_ins_r[0],"_date_reelle","Prochaine échéance","Jours restants","Statut","_ligne_sheet"]
                df_show=df_ech[cols_affich].sort_values("Prochaine échéance")

                # ---- APPLICATION DES FILTRES ----
                df_show_filtre=df_show.copy()
                if f_ech_site!="Tous" and col_site_r:
                    df_show_filtre=df_show_filtre[df_show_filtre[col_site_r[0]].astype(str).str.strip()==f_ech_site]
                if f_ech_ins!="Tous" and col_ins_r:
                    df_show_filtre=df_show_filtre[df_show_filtre[col_ins_r[0]].astype(str).str.strip()==f_ech_ins]
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
                        # Visiteur : lecture seule
                        cols_visiteur=[]
                        if col_site_r:  cols_visiteur.append(col_site_r[0])
                        if col_label_r: cols_visiteur.append(col_label_r[0])
                        cols_visiteur+=[col_ins_r[0],"_date_reelle","Prochaine échéance","Jours restants","Statut"]
                        st.dataframe(df_show_filtre[cols_visiteur],column_config={
                            "_date_reelle":       st.column_config.DateColumn("📅 Date de dernière visite",format="DD/MM/YYYY"),
                            "Prochaine échéance": st.column_config.DateColumn("⏭️ Prochaine échéance",format="DD/MM/YYYY"),
                            "Jours restants":     st.column_config.NumberColumn("Jours restants",format="%d j"),
                        },hide_index=True,use_container_width=True)
                    else:
                        # Responsable : édition de la date de dernière visite ET de la prochaine échéance
                        st.markdown("""<div style='background:#EFF6FF;border-left:4px solid #2a78d6;padding:10px 14px;border-radius:6px;margin-bottom:10px;'>
                            <p style='margin:0;font-size:12px;color:#1e40af;font-weight:600;'>✏️ Mode responsable — Modifiez la <b>Date de dernière visite</b> et/ou la <b>Prochaine échéance</b> puis sauvegardez. Par défaut, la prochaine échéance est calculée automatiquement selon la périodicité ; toute date saisie ici la remplace.</p>
                        </div>""",unsafe_allow_html=True)
                        cols_resp=[]
                        if col_site_r:  cols_resp.append(col_site_r[0])
                        if col_label_r: cols_resp.append(col_label_r[0])
                        cols_resp+=[col_ins_r[0],"_date_reelle","Prochaine échéance","Jours restants","Statut","_ligne_sheet"]
                        df_editable=df_show_filtre[cols_resp].copy()
                        df_editable["_date_reelle"]=pd.to_datetime(df_editable["_date_reelle"],errors='coerce')
                        df_editable["Prochaine échéance"]=pd.to_datetime(df_editable["Prochaine échéance"],errors='coerce')
                        edited_df=st.data_editor(df_editable,column_config={
                            "_date_reelle":       st.column_config.DateColumn("✅ Date de dernière visite",format="DD/MM/YYYY",help="Saisissez ici la date réelle du dernier contrôle effectué"),
                            "Prochaine échéance": st.column_config.DateColumn("⏭️ Prochaine échéance",format="DD/MM/YYYY",help="Calculée automatiquement, modifiable si besoin"),
                            "Jours restants":     st.column_config.NumberColumn("Jours restants",format="%d j"),
                            "_ligne_sheet":       None,
                        },disabled=[c for c in df_editable.columns if c not in ("_date_reelle","Prochaine échéance")],hide_index=True,use_container_width=True,key="editor_dates_reelles")

                        if not col_prochaine_r:
                            st.caption("ℹ️ Pour que la « Prochaine échéance » modifiée soit conservée après actualisation, ajoutez une colonne « Prochaine_echeance » dans l'onglet « Rapports » du Google Sheet.")

                        if st.button("💾 Sauvegarder les modifications",type="primary"):
                            with st.spinner("Mise à jour dans Google Sheets..."):
                                nb_maj=0
                                erreurs=[]
                                for idx,row_edit in edited_df.iterrows():
                                    num_ligne_sheet=int(row_edit["_ligne_sheet"])

                                    # -- Date de dernière visite --
                                    nouvelle_date=row_edit["_date_reelle"]
                                    ancienne_date=df_editable.loc[idx,"_date_reelle"]
                                    dates_diff=False
                                    if pd.isna(nouvelle_date) and pd.isna(ancienne_date): dates_diff=False
                                    elif pd.isna(nouvelle_date)!=pd.isna(ancienne_date): dates_diff=True
                                    elif not pd.isna(nouvelle_date) and nouvelle_date!=ancienne_date: dates_diff=True
                                    if dates_diff and not pd.isna(nouvelle_date):
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

                                    # -- Prochaine échéance (surcharge manuelle) --
                                    if col_prochaine_r:
                                        nouvelle_prochaine=row_edit["Prochaine échéance"]
                                        ancienne_prochaine=df_editable.loc[idx,"Prochaine échéance"]
                                        prochaine_diff=False
                                        if pd.isna(nouvelle_prochaine) and pd.isna(ancienne_prochaine): prochaine_diff=False
                                        elif pd.isna(nouvelle_prochaine)!=pd.isna(ancienne_prochaine): prochaine_diff=True
                                        elif not pd.isna(nouvelle_prochaine) and nouvelle_prochaine!=ancienne_prochaine: prochaine_diff=True
                                        if prochaine_diff and not pd.isna(nouvelle_prochaine):
                                            num_col_p=df_rapports.columns.tolist().index(col_prochaine_r[0])+1
                                            lettre_col_p=chr(64+num_col_p)
                                            prochaine_str=nouvelle_prochaine.strftime("%d/%m/%Y")
                                            ok_p, msg_p = sheets_ecrire_cellule_v2("Rapports",f"{lettre_col_p}{num_ligne_sheet}",prochaine_str)
                                            if ok_p:
                                                nb_maj+=1
                                            else:
                                                erreurs.append(f"Ligne {num_ligne_sheet} (prochaine échéance): {msg_p}")
                            if nb_maj>0:
                                st.success(f"✅ {nb_maj} modification(s) enregistrée(s) !")
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
                            j=d.day; ins=str(row[col_ins_r[0]]).strip()
                            col_c=COULEURS_INS.get(ins,"#94a3b8")
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
                    inss_du_mois={str(r[col_ins_r[0]]).strip() for evts_list in details_evt.values() for r in evts_list}
                    for ins,couleur in COULEURS_INS.items():
                        opacity="1" if ins in inss_du_mois else "0.3"
                        st.markdown(f"""<div style='display:flex;align-items:center;gap:8px;margin-bottom:5px;opacity:{opacity};'>
                            <span style='width:10px;height:10px;border-radius:2px;background:{couleur};display:inline-block;flex-shrink:0;'></span>
                            <span style='font-size:11px;color:#475569;'>{ins}</span>
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
                            c_ins  =str(row_ctrl[col_ins_r[0]]).strip()
                            c_site =str(row_ctrl[col_site_r[0]]).strip()  if col_site_r  else ""
                            c_label=str(row_ctrl[col_label_r[0]]).strip() if col_label_r else ""
                            c_date =row_ctrl["_date_brute"]
                            c_reel =row_ctrl["_date_reelle"]
                            c_next =row_ctrl["Prochaine échéance"]
                            c_jours=int(row_ctrl["Jours restants"])
                            c_stat =row_ctrl["Statut"]
                            c_col  =COULEURS_INS.get(c_ins,"#94a3b8")
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
                                f"<p style='margin:0 0 8px 0;font-size:12px;font-weight:700;color:#1E293B;'>{c_ins}</p>"
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

        def lien_apercu_drive(lien: str) -> str:
            """Convertit un lien Google Drive en lien d'aperçu (preview) qui s'ouvre
            directement dans Drive sans télécharger le fichier."""
            if not lien:
                return lien
            m = re.search(r"/file/d/([a-zA-Z0-9_-]+)", lien)
            if not m:
                m = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", lien)
            if m:
                file_id = m.group(1)
                return f"https://drive.google.com/file/d/{file_id}/preview"
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
                lien_apercu = lien_apercu_drive(lien_contrat)

                st.markdown(
                    "<div style='background:white;padding:16px 20px;border-radius:10px;"
                    "box-shadow:0 2px 8px rgba(0,0,0,0.05);border-left:4px solid #1E3A8A;"
                    "display:flex;align-items:center;justify-content:space-between;'>"
                    "<span style='font-size:14px;font-weight:600;color:#1E293B;'>📑 Contrat d'abonnement 2026</span>"
                    "<span>"
                    f"<a href='{lien_apercu}' target='_blank' rel='noopener' style='text-decoration:none;background:#1E3A8A;"
                    "color:white;padding:8px 14px;border-radius:6px;font-size:13px;font-weight:600;margin-right:8px;'>"
                    "👁️ Consulter</a>"
                    f"<a href='{lien_dl}' download target='_blank' rel='noopener' style='text-decoration:none;background:#16A34A;"
                    "color:white;padding:8px 14px;border-radius:6px;font-size:13px;font-weight:600;'>"
                    "📥 Télécharger</a>"
                    "</span>"
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
        if "ins_exig_sel" not in st.session_state: 
            st.session_state.ins_exig_sel = None

    # Niveau 1 : choix du site
        st.markdown("<p style='font-size:13px;color:#64748B;font-weight:600;margin-bottom:8px;'>Sélectionnez un site :</p>", unsafe_allow_html=True)
        s1, s2, s3 = st.columns([1, 1, 3])
    
        with s1:
            actif_sgb = (st.session_state.site_exig_sel == "SGB")
            if st.button("🏢 SGB", use_container_width=True, type="primary" if actif_sgb else "secondary"):
                st.session_state.site_exig_sel = "SGB"
                st.session_state.ins_exig_sel = None  # Reset l'installation si on change de site
                st.rerun()
            
        with s2:
            actif_meg = (st.session_state.site_exig_sel == "MEG")
            if st.button("🏢 MEG", use_container_width=True, type="primary" if actif_meg else "secondary"):
                st.session_state.site_exig_sel = "MEG"
                st.session_state.ins_exig_sel = None  # Reset l'installation si on change de site
                st.rerun()

    # --- CORRECTION DE LA LOGIQUE D'AFFICHAGE ---
    # On se base TOUJOURS sur le session_state actuel, pas sur le clic du bouton direct
        if st.session_state.site_exig_sel:
            site_sel = st.session_state.site_exig_sel
            st.markdown(f"<p style='font-size:13px;color:#64748B;font-weight:600;margin:16px 0 8px 0;'>Installations — Site {site_sel} :</p>", unsafe_allow_html=True)

            df_site = df_equip[df_equip["Site"] == site_sel] if not df_equip.empty else pd.DataFrame()

            NOMS_COURTS_INS = {
                "Installations électriques": "⚡ Électriques",
                "Equipements de levage":     "🏗️ Levage",
                "Sécurité incendie":         "🔥 Incendie",
                "Installations de gaz":      "🔵 Gaz",
                "Appareil pression de gaz":  "⚙️ Pression gaz",
            }

        # Création dynamique des boutons des installations
            ins_cols = st.columns(5)
            for i, (ins, couleur) in enumerate(COULEURS_INS.items()):
                with ins_cols[i % 5]:
                    nb_total_ins = int(df_site[df_site["Installation"] == ins]["Nombre"].sum()) if not df_site.empty else 0
                    actif_ins = (st.session_state.ins_exig_sel == ins)
                    label_court = NOMS_COURTS_INS.get(ins, ins)
                
                    if st.button(f"{label_court} ({nb_total_ins})", key=f"ins_btn_{ins}", use_container_width=True,
                                 type="primary" if actif_ins else "secondary",
                                 help=f"{nb_total_ins} équipement(s) au total"):
                        st.session_state.ins_exig_sel = ins
                        st.rerun()

        # Niveau 3 : sous-équipements de l'istallation choisie
            if st.session_state.ins_exig_sel:
                ins_sel = st.session_state.ins_exig_sel
                st.markdown(f"<p style='font-size:13px;color:#64748B;font-weight:600;margin:16px 0 8px 0;'>Sous-équipements — {ins_sel} ({site_sel}) :</p>", unsafe_allow_html=True)

                df_ins = df_site[df_site["Installation"] == ins_sel] if not df_site.empty else pd.DataFrame()
                couleur_ins = COULEURS_INS.get(ins_sel, "#94a3b8")

                if df_ins.empty:
                    st.info(f"Aucun sous-équipement enregistré pour {ins_sel} sur le site {site_sel}.")
                else:
                    eq_cols = st.columns(3)
                    for idx, (_, row_eq) in enumerate(df_ins.iterrows()):
                        with eq_cols[idx % 3]:
                            st.markdown(
                                f"<div style='background:white;border-left:4px solid {couleur_ins};"
                                "padding:14px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.05);margin-bottom:10px;'>"
                                f"<p style='margin:0;font-size:13px;font-weight:600;color:#1E293B;'>{row_eq.get('Sous_equipement','')}</p>"
                                f"<p style='margin:6px 0 0 0;font-size:24px;font-weight:800;color:{couleur_ins};'>{int(row_eq.get('Nombre',0))}</p>"
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
                                    ok, err = ajouter_equipement(site_sel, ins_sel, nouv_seq.strip(), nouv_nb)
                                    if ok:
                                        st.success("✅ Ajouté !")
                                        st.rerun()
                                    else:
                                        st.error(f"Erreur : {err}")
                                else:
                                    st.warning("Veuillez saisir un nom.")

                        if not df_ins.empty:
                            st.markdown("<br>**Supprimer un sous-équipement :**", unsafe_allow_html=True)
                            for orig_idx, row_eq in df_ins.iterrows():
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
            st.info("👆 Sélectionnez un site (SGB ou MEG) pour voir les installations")

        st.divider()

        if not df_exig.empty:
            st.markdown("### 📄 Check-lists des équipements contractés")
            col_sgb, col_meg = st.columns(2)
            date_str = datetime.date.today().strftime('%d_%m_%Y')

            with col_sgb:
                st.markdown(
                    "<div style='background:white;padding:16px 20px;border-radius:10px;"
                    "box-shadow:0 2px 8px rgba(0,0,0,0.05);border-left:4px solid #1E3A8A;"
                    "margin-bottom:10px;'>"
                    "<span style='font-size:14px;font-weight:600;color:#1E293B;'>📑 Rapport d'inspection — SGB</span>"
                    "</div>", unsafe_allow_html=True)
                if st.button("👁️ Consulter le rapport", use_container_width=True, key="consult_sgb", type="primary"):
                    with st.spinner("Préparation du rapport SGB..."):
                        try:
                            st.session_state["pdf_sgb"] = generer_rapport_equipements_pdf(df_exig, "SGB")
                        except Exception as e:
                            st.session_state["pdf_sgb"] = None
                            st.error(f"Erreur PDF SGB : {e}")
                if st.session_state.get("pdf_sgb"):
                    afficher_apercu_pdf(st.session_state["pdf_sgb"])
                    st.download_button(
                        label="📥 Télécharger le rapport SGB",
                        data=st.session_state["pdf_sgb"],
                        file_name=f"Rapport_Inspection_SGB_{date_str}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="dl_sgb"
                    )

            with col_meg:
                st.markdown(
                    "<div style='background:white;padding:16px 20px;border-radius:10px;"
                    "box-shadow:0 2px 8px rgba(0,0,0,0.05);border-left:4px solid #1E3A8A;"
                    "margin-bottom:10px;'>"
                    "<span style='font-size:14px;font-weight:600;color:#1E293B;'>📑 Rapport d'inspection — MEG</span>"
                    "</div>", unsafe_allow_html=True)
                if st.button("👁️ Consulter le rapport", use_container_width=True, key="consult_meg", type="primary"):
                    with st.spinner("Préparation du rapport MEG..."):
                        try:
                            st.session_state["pdf_meg"] = generer_rapport_equipements_pdf(df_exig, "MEG")
                        except Exception as e:
                            st.session_state["pdf_meg"] = None
                            st.error(f"Erreur PDF MEG : {e}")
                if st.session_state.get("pdf_meg"):
                    afficher_apercu_pdf(st.session_state["pdf_meg"])
                    st.download_button(
                        label="📥 Télécharger le rapport MEG",
                        data=st.session_state["pdf_meg"],
                        file_name=f"Rapport_Inspection_MEG_{date_str}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="dl_meg"
                    )
                    


    

    
    # ---- ONGLET 3 : PRÉSENCE & VISITES ----
    if tab3 and role=="Responsable" and password_correct:
        with tab3:
            st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#1E3A8A;'>👥 Suivi des visiteurs</p>",unsafe_allow_html=True)
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
            st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#1E3A8A;'>📊 Indicateurs de performance</p>",unsafe_allow_html=True)
            col_r_kpi,_=st.columns([1,5])
            with col_r_kpi:
                if st.button("🔄",key="refresh_kpi"): st.cache_data.clear(); st.rerun()

            # ---- Préparation des données de contrôle (même logique que l'onglet Planification) ----
            col_ins_k   = [c for c in df_rapports.columns if "ins" in c.lower()]
            col_date_k  = [c for c in df_rapports.columns if "date" in c.lower() and "reelle" not in c.lower() and "réelle" not in c.lower() and "prochaine" not in c.lower() and "planifi" not in c.lower()]
            col_site_k  = [c for c in df_rapports.columns if "site" in c.lower()]
            col_label_k = [c for c in df_rapports.columns if "equip" in c.lower() or "label" in c.lower() or "nom" in c.lower()]
            col_reelle_k= [c for c in df_rapports.columns if "reelle" in c.lower() or "réelle" in c.lower()]
            col_planifiee_k = [c for c in df_rapports.columns if "planifi" in c.lower()]

            if df_rapports.empty or not col_ins_k or not col_date_k:
                st.info("Données insuffisantes dans l'onglet « Rapports » pour calculer les KPI.")
                kpi_data = None
            else:
                df_k = df_rapports.copy()
                df_k["_date_brute"]  = pd.to_datetime(df_k[col_date_k[0]], dayfirst=True, errors='coerce')
                df_k["_date_reelle"] = pd.to_datetime(df_k[col_reelle_k[0]], dayfirst=True, errors='coerce') if col_reelle_k else pd.NaT
                # Date planifiée de référence pour le respect de délai : si la colonne dédiée existe
                # dans le Sheet on l'utilise, sinon (tant qu'elle n'a pas été ajoutée) on considère
                # provisoirement que la date planifiée = la date de dernière visite (donc toujours respecté).
                if col_planifiee_k:
                    df_k["_date_planifiee"] = pd.to_datetime(df_k[col_planifiee_k[0]], dayfirst=True, errors='coerce')
                else:
                    df_k["_date_planifiee"] = df_k["_date_reelle"]
                df_k = df_k.dropna(subset=["_date_brute"])

                cles_k=[]
                if col_site_k:  cles_k.append(col_site_k[0])
                cles_k.append(col_ins_k[0])
                if col_label_k: cles_k.append(col_label_k[0])
                df_k = df_k.sort_values("_date_brute", ascending=True)
                df_k = df_k.drop_duplicates(subset=cles_k, keep="last")

                # ---- KPI 1 : Taux de réalisation 2026, calculé PAR INSTALLATION (et non par équipement) ----
                # Contrôles attendus en 2026 selon la périodicité de chaque installation :
                #   - Installations électriques : périodicité 6 mois -> 2 contrôles/an
                #   - Les 4 autres types        : périodicité 12 mois -> 1 contrôle/an
                # => 2 sites (SGB, MEG) x (1 élec x2 + 4 autres x1) = 12 contrôles attendus au total sur l'année

                SITES_SUIVIS = ["SGB", "MEG"]
                INSTALLATIONS_SUIVIES = list(PERIODICITE.keys())

                def nb_campagnes_attendues(installation):
                    return round(12 / PERIODICITE.get(installation, 12))

                nb_total_2026 = sum(nb_campagnes_attendues(ins) for ins in INSTALLATIONS_SUIVIES) * len(SITES_SUIVIS)

                # Un contrôle est compté comme réalisé en 2026 dès lors que sa DATE RÉELLE de visite
                # tombe en 2026, quelle que soit l'année de l'échéance théorique associée.
                df_realises_2026 = df_k[df_k["_date_reelle"].notna() & (df_k["_date_reelle"].dt.year == 2026)].copy()
                if col_site_k:
                    df_realises_2026 = df_realises_2026[df_realises_2026[col_site_k[0]].astype(str).str.strip().isin(SITES_SUIVIS)]

                nb_realises_2026 = 0
                for site in SITES_SUIVIS:
                    for ins in INSTALLATIONS_SUIVIES:
                        attendu = nb_campagnes_attendues(ins)
                        df_grp = df_realises_2026[df_realises_2026[col_ins_k[0]].astype(str).str.strip() == ins]
                        if col_site_k:
                            df_grp = df_grp[df_grp[col_site_k[0]].astype(str).str.strip() == site]
                        # Une "campagne" réalisée = une date réelle distincte (mois/échéance) pour cette
                        # installation sur ce site, plafonnée au nombre de contrôles attendus par an.
                        nb_campagnes_realisees = df_grp["_date_brute"].nunique() if not df_grp.empty else 0
                        nb_realises_2026 += min(nb_campagnes_realisees, attendu)

                nb_restants_2026 = nb_total_2026 - nb_realises_2026
                taux1 = round(nb_realises_2026/nb_total_2026*100,1) if nb_total_2026>0 else 0
                


                # ---- KPI 2 : Taux de respect de délai de visite (écart ≤ 1 mois entre date planifiée et date de dernière visite) ----
                # On ne considère que les contrôles dont la visite a réellement eu lieu en 2026
                # (certains contrôles réalisés figurent avec une date réelle en 2025 et ne doivent pas être comptés ici).
                df_realises_k = df_k[df_k["_date_reelle"].notna() & (df_k["_date_reelle"].dt.year == 2026)].copy()
                nb_visites_realisees = len(df_realises_k)
                if nb_visites_realisees > 0:
                    df_realises_k["_ecart"] = (df_realises_k["_date_reelle"] - df_realises_k["_date_planifiee"]).dt.days.abs()
                    nb_respectes = int((df_realises_k["_ecart"] <= 31).sum())
                else:
                    nb_respectes = 0
                nb_non_respectes = nb_visites_realisees - nb_respectes
                taux2 = round(nb_respectes/nb_visites_realisees*100,1) if nb_visites_realisees>0 else 0



                kpi_data = {
                    "kpi1": {"taux":taux1, "realises":nb_realises_2026, "restants":nb_restants_2026, "total":nb_total_2026},
                    "kpi2": {"taux":taux2, "respectes":nb_respectes, "non_respectes":nb_non_respectes, "total":nb_visites_realisees}
                }




                k1c,k2c = st.columns(2)

                with k1c:
                    st.markdown("<p style='text-align:center;font-weight:600;color:#1E293B;font-size:14px;'>Taux de réalisation 2026</p></p>",unsafe_allow_html=True)
                    if nb_total_2026>0:
                        dfp1=pd.DataFrame({"Statut":["Réalisés","Restants"],"Nombre":[nb_realises_2026,nb_restants_2026]})
                        fig1=px.pie(dfp1,values="Nombre",names="Statut",hole=0.6,color="Statut",
                                    color_discrete_map={"Réalisés":"#10B981","Restants":"#EF4444"})
                        fig1.update_traces(textposition='inside',textinfo='percent')
                        fig1.update_layout(margin=dict(t=10,b=10,l=10,r=10),height=260,showlegend=False,
                                            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig1,use_container_width=True,config={'displayModeBar':False})
                        st.markdown(f"<p style='text-align:center;font-size:13px;color:#64748B;'>{taux1}% réalisés ({nb_realises_2026}/{nb_total_2026} contrôles d'installation)</p>",unsafe_allow_html=True)
                    else:
                        st.info("Aucune échéance d'installation en 2026.")

                with k2c:
                    st.markdown("<p style='text-align:center;font-weight:600;color:#1E293B;font-size:14px;'>Respect délai de visite (≤ 1 mois)</p>",unsafe_allow_html=True)
                    if nb_visites_realisees>0:
                        dfp2=pd.DataFrame({"Statut":["Respecté","Non respecté"],"Nombre":[nb_respectes,nb_non_respectes]})
                        fig2=px.pie(dfp2,values="Nombre",names="Statut",hole=0.6,color="Statut",
                                    color_discrete_map={"Respecté":"#0EA5E9","Non respecté":"#EF4444"})
                        fig2.update_traces(textposition='inside',textinfo='percent')
                        fig2.update_layout(margin=dict(t=10,b=10,l=10,r=10),height=260,showlegend=False,
                                            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(fig2,use_container_width=True,config={'displayModeBar':False})
                        st.markdown(f"<p style='text-align:center;font-size:13px;color:#64748B;'>{taux2}% respectés ({nb_respectes}/{nb_visites_realisees})</p>",unsafe_allow_html=True)
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

            # ================= Actions de contrôle =================
            st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#0F172A;'>📌 Actions de contrôle</p>",unsafe_allow_html=True)

            with st.spinner("Chargement des actions..."):
                df_reserve = lire_points_reserve()

            with st.expander("➕ Ajouter une action"):
                r1,r2,r3,r4 = st.columns([1,1.5,1.5,1])
                with r1:
                    res_site = st.selectbox("Site",["SGB","MEG"],key="res_site_new")
                with r2:
                    res_ins = st.selectbox("Installation",list(PERIODICITE.keys()),key="res_ins_new")
                with r3:
                    res_seq = st.text_input("Sous-équipement",key="res_seq_new")
                with r4:
                    res_nb = st.number_input("Nb points",min_value=1,value=1,key="res_nb_new")
                if st.button("💾 Enregistrer",key="btn_add_reserve"):
                    if res_seq.strip():
                        ok,err = ajouter_point_reserve(res_site,res_ins,res_seq.strip(),res_nb)
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
                    st.markdown("<p style='font-weight:600;color:#1E293B;margin:0 0 10px 0;font-size:13px;'>🔍 Filtrer les Actions de contrôle</p>",unsafe_allow_html=True)
                    fr1,fr2,fr3 = st.columns(3)
                    sites_dispo = ["Tous"]+sorted(df_reserve["Site"].dropna().unique().tolist()) if "Site" in df_reserve.columns else ["Tous"]
                    inss_dispo  = ["Tous"]+sorted(df_reserve["Installation"].dropna().unique().tolist()) if "Installation" in df_reserve.columns else ["Tous"]
                    with fr1: f_res_site = st.selectbox("Site",sites_dispo,key="f_res_site")
                    with fr2: f_res_ins  = st.selectbox("Installation",inss_dispo,key="f_res_ins")
                    with fr3: f_res_seq  = st.text_input("Recherche sous-équipement",key="f_res_seq")

                df_reserve_f = df_reserve.copy()
                if f_res_site!="Tous" and "Site" in df_reserve_f.columns:
                    df_reserve_f = df_reserve_f[df_reserve_f["Site"]==f_res_site]
                if f_res_ins!="Tous" and "Installation" in df_reserve_f.columns:
                    df_reserve_f = df_reserve_f[df_reserve_f["Installation"]==f_res_ins]
                if f_res_seq.strip() and "Sous_equipement" in df_reserve_f.columns:
                    df_reserve_f = df_reserve_f[df_reserve_f["Sous_equipement"].astype(str).str.contains(f_res_seq.strip(),case=False,na=False)]

                st.dataframe(df_reserve_f.rename(columns={
                    "Site":"Site","Installation":"Installation","Sous_equipement":"Sous équipement","Nombre":"Nombre des actions de contrôle"
                }),hide_index=True,use_container_width=True)

                st.markdown("<br>",unsafe_allow_html=True)

                # --- Répartition par site : graphique centré ---
                csite1,csite2,csite3 = st.columns([1,2,1])
                with csite2:
                    if "Site" in df_reserve_f.columns and not df_reserve_f.empty:
                        df_by_site = df_reserve_f.groupby("Site")["Nombre"].sum().reset_index()
                        figS = px.pie(df_by_site,values="Nombre",names="Site",hole=0.6,
                                      color_discrete_sequence=['#1E3A8A','#0EA5E9','#94A3B8'])
                        figS.update_traces(textposition='inside',textinfo='percent+label')
                        figS.update_layout(title="Répartition par site",title_x=0.5,margin=dict(t=40,b=10,l=10,r=10),height=280,
                                            paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                        st.plotly_chart(figS,use_container_width=True,config={'displayModeBar':False})
                    else:
                        st.info("Aucune donnée à afficher pour le graphe par site.")

                st.markdown("<br>",unsafe_allow_html=True)
                st.markdown("<p style='font-weight:700;font-size:14px;color:#0F172A;text-align:center;margin-bottom:10px;'>Répartition par installation</p>",unsafe_allow_html=True)

                # --- Répartition par installation : MEG (gauche) | légende (milieu) | SGB (droite) ---
                if "Installation" in df_reserve_f.columns and "Site" in df_reserve_f.columns and not df_reserve_f.empty:
                    all_inss = sorted(df_reserve_f["Installation"].dropna().unique().tolist())
                    palette = px.colors.qualitative.Set1
                    color_map = {ins: palette[i % len(palette)] for i,ins in enumerate(all_inss)}

                    gins1,gins2,gins3 = st.columns([2,1,2])

                    with gins1:
                        df_meg_ins = df_reserve_f[df_reserve_f["Site"]=="MEG"].groupby("Installation")["Nombre"].sum().reset_index()
                        if not df_meg_ins.empty:
                            figMEG = px.pie(df_meg_ins,values="Nombre",names="Installation",hole=0.6,
                                             color="Installation",color_discrete_map=color_map)
                            figMEG.update_traces(textposition='inside',textinfo='percent',showlegend=False)
                            figMEG.update_layout(title="MEG",title_x=0.5,showlegend=False,
                                                  margin=dict(t=40,b=10,l=10,r=10),height=260,
                                                  paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(figMEG,use_container_width=True,config={'displayModeBar':False})
                        else:
                            st.info("Aucune donnée MEG.")

                    with gins2:
                        legende_items = "".join(
                            f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:12px;'>"
                            f"<span style='width:12px;height:12px;min-width:12px;border-radius:3px;background:{color_map[ins]};display:inline-block;'></span>"
                            f"<span style='font-size:11.5px;color:#334155;'>{ins}</span>"
                            f"</div>"
                            for ins in all_inss
                        )
                        legende_html = f"<div style='padding-top:35px;'>{legende_items}</div>"
                        st.markdown(legende_html,unsafe_allow_html=True)

                    with gins3:
                        df_sgb_ins = df_reserve_f[df_reserve_f["Site"]=="SGB"].groupby("Installation")["Nombre"].sum().reset_index()
                        if not df_sgb_ins.empty:
                            figSGB = px.pie(df_sgb_ins,values="Nombre",names="Installation",hole=0.6,
                                             color="Installation",color_discrete_map=color_map)
                            figSGB.update_traces(textposition='inside',textinfo='percent',showlegend=False)
                            figSGB.update_layout(title="SGB",title_x=0.5,showlegend=False,
                                                  margin=dict(t=40,b=10,l=10,r=10),height=260,
                                                  paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(figSGB,use_container_width=True,config={'displayModeBar':False})
                        else:
                            st.info("Aucune donnée SGB.")
                else:
                    st.info("Aucune donnée à afficher pour le graphe par installation.")

                with st.expander("🗑️ Supprimer une action"):
                    for orig_idx,row_r in df_reserve.iterrows():
                        dcx1,dcx2 = st.columns([5,1])
                        with dcx1:
                            st.write(f"{row_r.get('Site','')} — {row_r.get('Installation','')} — {row_r.get('Sous_equipement','')} — {row_r.get('Nombre',0)} pt(s)")
                        with dcx2:
                            if st.button("🗑️",key=f"del_res_{orig_idx}"):
                                num_ligne_sheet = orig_idx+2
                                if supprimer_ligne_generique("PointsReserve",num_ligne_sheet,4):
                                    st.success("Supprimé !")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("Erreur lors de la suppression.")

            # ================= Actions de contrôle PAR NATURE =================
            st.markdown("<br><hr style='border-color:#E2E8F0;'>",unsafe_allow_html=True)
            st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#0F172A;'>🧭 Actions de contrôle par nature</p>",unsafe_allow_html=True)

            with st.spinner("Chargement des actions par nature..."):
                df_nature = lire_points_reserve_nature()

            with st.expander("➕ Ajouter une ligne"):
                nt1,nt2,nt3,nt4 = st.columns([1,1.5,1,1.5])
                with nt1:
                    nat_site = st.selectbox("Site",["SGB","MEG"],key="nat_site_new")
                with nt2:
                    nat_ins = st.selectbox("Installation",list(PERIODICITE.keys()),key="nat_ins_new")
                with nt3:
                    nat_nb = st.number_input("Nb points",min_value=1,value=1,key="nat_nb_new")
                with nt4:
                    nat_code = st.selectbox("Nature",list(NATURE_PILOTE.keys()),
                                             format_func=lambda c: f"{c} — {NATURE_PILOTE[c][0]}",key="nat_code_new")
                nat_pilote_auto = NATURE_PILOTE[nat_code][1]
                st.markdown(
                    f"<p style='font-size:12.5px;color:#64748B;margin-top:-4px;'>Pilote assigné automatiquement : "
                    f"<b style='color:#1E3A8A;'>{nat_pilote_auto}</b></p>",unsafe_allow_html=True)
                if st.button("💾 Enregistrer",key="btn_add_nature"):
                    ok,err = ajouter_point_reserve_nature(nat_site,nat_ins,nat_nb,nat_code)
                    if ok:
                        st.success("✅ Ligne ajoutée !")
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Erreur : {err}")

            if df_nature.empty:
                st.info("Aucune donnée enregistrée. Utilisez le formulaire ci-dessus pour en ajouter.")
            else:
                if "Nombre" in df_nature.columns:
                    df_nature["Nombre"] = pd.to_numeric(df_nature["Nombre"],errors="coerce").fillna(0).astype(int)

                with st.container(border=True):
                    st.markdown("<p style='font-weight:600;color:#1E293B;margin:0 0 10px 0;font-size:13px;'>🔍 Filtrer</p>",unsafe_allow_html=True)
                    fn1,fn2 = st.columns(2)
                    sites_dispo_n = ["Tous"]+sorted(df_nature["Site"].dropna().unique().tolist()) if "Site" in df_nature.columns else ["Tous"]
                    inss_dispo_n  = ["Tous"]+sorted(df_nature["Installation"].dropna().unique().tolist()) if "Installation" in df_nature.columns else ["Tous"]
                    with fn1: f_nat_site = st.selectbox("Site",sites_dispo_n,key="f_nat_site")
                    with fn2: f_nat_ins  = st.selectbox("Installation",inss_dispo_n,key="f_nat_ins")

                df_nature_f = df_nature.copy()
                if f_nat_site!="Tous" and "Site" in df_nature_f.columns:
                    df_nature_f = df_nature_f[df_nature_f["Site"]==f_nat_site]
                if f_nat_ins!="Tous" and "Installation" in df_nature_f.columns:
                    df_nature_f = df_nature_f[df_nature_f["Installation"]==f_nat_ins]

                st.dataframe(df_nature_f.rename(columns={
                    "Site":"Site","Installation":"Installation","Nombre":"Nombre des actions","Nature":"Nature","Pilote":"Pilote"
                }),hide_index=True,use_container_width=True)

                st.markdown("<br>",unsafe_allow_html=True)
                st.markdown("<p style='font-weight:700;font-size:14px;color:#0F172A;text-align:center;margin-bottom:10px;'>Répartition par site : Nature et Pilote</p>",unsafe_allow_html=True)

                # --- Grille 2x2 : ligne 1 = SGB (Nature | Pilote), ligne 2 = MEG (Nature | Pilote) ---
                all_natures = [v[0] for v in NATURE_PILOTE.values()]
                palette_nat = px.colors.qualitative.Set2
                color_map_nat = {n: palette_nat[i % len(palette_nat)] for i,n in enumerate(all_natures)}

                # Les pilotes sont parfois combinés (ex: "BT + Maintenance", "BT + HSE + RH + DG").
                # On isole chaque entité (Maintenance, BT, HSE, RH, DG, DMTN, Chef service BT, ...)
                # pour calculer un % propre à chacune, même quand elle est partagée entre plusieurs natures.
                entites_atomiques = sorted(set(
                    e.strip() for v in NATURE_PILOTE.values() for e in v[1].split("+") if e.strip()
                ))
                palette_pil = px.colors.qualitative.Set1
                color_map_pil = {p: palette_pil[i % len(palette_pil)] for i,p in enumerate(entites_atomiques)}

                def _pie_nature_site(df_src, site, color_map, titre):
                    if "Nombre" not in df_src.columns or "Nature" not in df_src.columns or "Site" not in df_src.columns:
                        st.info(f"Aucune donnée {site}.")
                        return
                    d = df_src[df_src["Site"]==site].groupby("Nature")["Nombre"].sum().reset_index()
                    if d.empty:
                        st.info(f"Aucune donnée {site}.")
                        return
                    fig = px.pie(d,values="Nombre",names="Nature",hole=0.6,color="Nature",color_discrete_map=color_map)
                    fig.update_traces(textposition='inside',textinfo='percent')
                    fig.update_layout(title=titre,title_x=0.5,margin=dict(t=40,b=10,l=10,r=10),height=280,
                                       paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                                       legend=dict(font=dict(size=9)))
                    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})

                def _bar_pilote_site(df_src, site, color_map, titre):
                    if "Nombre" not in df_src.columns or "Pilote" not in df_src.columns or "Site" not in df_src.columns:
                        st.info(f"Aucune donnée {site}.")
                        return
                    d = df_src[df_src["Site"]==site]
                    if d.empty:
                        st.info(f"Aucune donnée {site}.")
                        return
                    total = d["Nombre"].sum()
                    compte = {}
                    for _,row in d.iterrows():
                        for e in str(row["Pilote"]).split("+"):
                            e = e.strip()
                            if not e: continue
                            compte[e] = compte.get(e,0) + row["Nombre"]
                    if not compte or total==0:
                        st.info(f"Aucune donnée {site}.")
                        return
                    dd = pd.DataFrame({"Pilote":list(compte.keys()),"Nombre":list(compte.values())})
                    dd["Pourcentage"] = (dd["Nombre"]/total*100).round(1)
                    dd = dd.sort_values("Pourcentage",ascending=True)
                    fig = px.bar(dd,x="Pourcentage",y="Pilote",orientation="h",text="Pourcentage",
                                 color="Pilote",color_discrete_map=color_map)
                    fig.update_traces(texttemplate='%{text}%',textposition='outside',cliponaxis=False)
                    fig.update_layout(title=titre,title_x=0.5,showlegend=False,
                                       xaxis_title="% des actions",yaxis_title="",
                                       margin=dict(t=40,b=10,l=10,r=30),height=280,
                                       paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig,use_container_width=True,config={'displayModeBar':False})

                if {"Nature","Pilote","Site","Nombre"}.issubset(df_nature_f.columns):
                    with g2: _bar_pilote_site(df_nature_f,"SGB",color_map_pil,"SGB — % par pilote")
                    g3,g4 = st.columns(2)
                    with g3: _pie_nature_site(df_nature_f,"MEG",color_map_nat,"MEG — % par nature")
                    with g4: _bar_pilote_site(df_nature_f,"MEG",color_map_pil,"MEG — % par pilote")
                else:
                    st.info("Aucune donnée à afficher pour les graphes.")

                with st.expander("🗑️ Supprimer une ligne"):
                    for orig_idx,row_n in df_nature.iterrows():
                        dnx1,dnx2 = st.columns([5,1])
                        with dnx1:
                            st.write(f"{row_n.get('Site','')} — {row_n.get('Installation','')} — {row_n.get('Nombre',0)} pt(s) — {row_n.get('Nature','')} — {row_n.get('Pilote','')}")
                        with dnx2:
                            if st.button("🗑️",key=f"del_nat_{orig_idx}"):
                                num_ligne_sheet = orig_idx+2
                                if supprimer_ligne_generique("PointsReserveNature",num_ligne_sheet,5):
                                    st.success("Supprimé !")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error("Erreur lors de la suppression.")

            # ================= RAPPORT PDF PAR PILOTE (CODIFICATION EXTERNE) =================
            st.markdown("<br><hr style='border-color:#E2E8F0;'>",unsafe_allow_html=True)
            st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#0F172A;'>📄 Rapport des actions par Pilote</p>",unsafe_allow_html=True)

            entites_pilote_codif = sorted(set(
                e.strip() for v in NATURE_PILOTE.values() for e in v[1].split("+") if e.strip()
            ))
            cpil1,cpil2 = st.columns([3,1])
            with cpil1:
                pilote_codif_choisi = st.selectbox("Pilote",entites_pilote_codif,key="pilote_codif_select")
            with cpil2:
                st.write("")
                st.write("")
                lancer_rapport_pilote = st.button("👁️ Générer",use_container_width=True,key="btn_gen_rapport_pilote",type="primary")

            if lancer_rapport_pilote:
                with st.spinner("Lecture du classeur de codification..."):
                    classeur, err = codif_charger_classeur(CODIF_SHEET_ID)
                    if err:
                        st.session_state["pdf_pilote"] = None
                        st.error(err)
                    elif not classeur:
                        st.session_state["pdf_pilote"] = None
                        st.warning("Aucun onglet trouvé dans le classeur de codification.")
                    else:
                        frames = []
                        for onglet, df_brut in classeur.items():
                            valeurs = df_brut.fillna("").astype(str).values.tolist()
                            d = _detecter_entete_et_nettoyer_codif(valeurs)
                            if not d.empty:
                                d["Installation"] = onglet
                                frames.append(d)
                        if not frames:
                            st.session_state["pdf_pilote"] = None
                            st.warning("Aucune donnée exploitable trouvée dans les onglets du classeur "
                                       "(colonnes Désignation/Observation/Code introuvables).")
                        else:
                            df_codif = pd.concat(frames,ignore_index=True)
                            df_codif["Nature"] = df_codif["Code"].map(lambda c: NATURE_PILOTE.get(c,("",""))[0])
                            codes_ok = _codes_pour_pilote(pilote_codif_choisi)
                            df_filtre_codif = df_codif[df_codif["Code"].isin(codes_ok)]
                            if df_filtre_codif.empty:
                                st.session_state["pdf_pilote"] = None
                                st.info(f"Aucune action trouvée pour le pilote « {pilote_codif_choisi} » "
                                        f"(codes recherchés : {', '.join(codes_ok) if codes_ok else '—'}).")
                            else:
                                try:
                                    st.session_state["pdf_pilote"] = generer_rapport_pilote_pdf(
                                        pilote_codif_choisi, df_filtre_codif,
                                        "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6q1BtDSDgVnJZFo0hOBfQJoDS6OYiub-qfQ&s"
                                    )
                                    st.session_state["nb_actions_pilote"] = len(df_filtre_codif)
                                    st.session_state["pilote_pdf_nom"] = pilote_codif_choisi
                                except Exception as e:
                                    st.session_state["pdf_pilote"] = None
                                    st.error(f"Erreur lors de la génération du PDF : {e}")

            if st.session_state.get("pdf_pilote"):
                st.success(f"{st.session_state.get('nb_actions_pilote',0)} action(s) trouvée(s) pour "
                           f"« {st.session_state.get('pilote_pdf_nom','')} ».")
                afficher_apercu_pdf_grille(st.session_state["pdf_pilote"], colonnes=2)
                st.download_button(
                    label="📥 Télécharger le rapport PDF",
                    data=st.session_state["pdf_pilote"],
                    file_name=f"Rapport_{st.session_state.get('pilote_pdf_nom','pilote')}_{datetime.date.today().strftime('%d_%m_%Y')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="dl_pilote"
                )

            # ================= RAPPORT PDF PREMIUM =================
            st.markdown("<br><hr style='border-color:#E2E8F0;'>",unsafe_allow_html=True)
            st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#0F172A;'>📄 Rapport PDF </p>",unsafe_allow_html=True)
           
            if kpi_data is None:
                st.info("Le rapport PDF nécessite des données KPI disponibles (onglet « Rapports » non vide).")
            else:
                st.markdown(
                    "<div style='background:white;padding:16px 20px;border-radius:10px;"
                    "box-shadow:0 2px 8px rgba(0,0,0,0.05);border-left:4px solid #1E3A8A;"
                    "margin-bottom:10px;'>"
                    "<span style='font-size:14px;font-weight:600;color:#1E293B;'>📑 Rapport PDF — Synthèse KPI</span>"
                    "</div>", unsafe_allow_html=True)
                if st.button("👁️ Consulter le rapport", use_container_width=True, key="consult_kpi", type="primary"):
                    with st.spinner("Préparation du rapport PDF..."):
                        try:
                            st.session_state["pdf_kpi"] = generer_rapport_kpi_pdf(
                                kpi_data,
                                df_reserve,
                                df_nature,
                                carto_b64,
                                "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR6q1BtDSDgVnJZFo0hOBfQJoDS6OYiub-qfQ&s"
                            )
                        except Exception as e:
                            st.session_state["pdf_kpi"] = None
                            st.error(f"Erreur lors de la génération du PDF : {e}")
                if st.session_state.get("pdf_kpi"):
                    afficher_apercu_pdf_grille(st.session_state["pdf_kpi"], colonnes=2)
                    st.download_button(
                        label="📥 Télécharger le rapport PDF",
                        data=st.session_state["pdf_kpi"],
                        file_name=f"Rapport_KPI_{datetime.date.today().strftime('%d_%m_%Y')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="dl_kpi"
                    )

    # ---- ONGLET 4 : KPI (Visiteur — vue simplifiée en lecture seule) ----
    if tab_kpi and role=="Visiteur":
        with tab_kpi:
            st.markdown("<p style='font-size:1.2rem;font-weight:700;color:#1E3A8A;'>📊 Actions de contrôle par nature</p>",unsafe_allow_html=True)

            with st.spinner("Chargement des actions par nature..."):
                df_nature_v = lire_points_reserve_nature()

            if df_nature_v.empty:
                st.info("Aucune donnée disponible pour le moment.")
            else:
                if "Nombre" in df_nature_v.columns:
                    df_nature_v["Nombre"] = pd.to_numeric(df_nature_v["Nombre"],errors="coerce").fillna(0).astype(int)

                if "site_kpi_visiteur" not in st.session_state:
                    st.session_state.site_kpi_visiteur = "SGB"

                bcol1,bcol2,_ = st.columns([1,1,4])
                with bcol1:
                    if st.button("🏭 SGB", key="btn_kpi_sgb", type=("primary" if st.session_state.site_kpi_visiteur=="SGB" else "secondary"), use_container_width=True):
                        st.session_state.site_kpi_visiteur = "SGB"
                        st.rerun()
                with bcol2:
                    if st.button("🏭 MEG", key="btn_kpi_meg", type=("primary" if st.session_state.site_kpi_visiteur=="MEG" else "secondary"), use_container_width=True):
                        st.session_state.site_kpi_visiteur = "MEG"
                        st.rerun()

                site_choisi = st.session_state.site_kpi_visiteur
                st.markdown(f"<p style='font-weight:700;font-size:14px;color:#0F172A;text-align:center;margin:14px 0 10px 0;'>Répartition — Site {site_choisi}</p>",unsafe_allow_html=True)

                all_natures_v = [v[0] for v in NATURE_PILOTE.values()]
                palette_nat_v = px.colors.qualitative.Set2
                color_map_nat_v = {n: palette_nat_v[i % len(palette_nat_v)] for i,n in enumerate(all_natures_v)}

                entites_atomiques_v = sorted(set(
                    e.strip() for v in NATURE_PILOTE.values() for e in v[1].split("+") if e.strip()
                ))
                palette_pil_v = px.colors.qualitative.Set1
                color_map_pil_v = {p: palette_pil_v[i % len(palette_pil_v)] for i,p in enumerate(entites_atomiques_v)}

                if {"Nature","Pilote","Site"}.issubset(df_nature_v.columns):
                    vg1,vg2 = st.columns(2)
                    with vg1:
                        dv = df_nature_v[df_nature_v["Site"]==site_choisi].groupby("Nature")["Nombre"].sum().reset_index()
                        if dv.empty:
                            st.info(f"Aucune donnée {site_choisi}.")
                        else:
                            figv1 = px.pie(dv,values="Nombre",names="Nature",hole=0.6,color="Nature",color_discrete_map=color_map_nat_v)
                            figv1.update_traces(textposition='inside',textinfo='percent')
                            figv1.update_layout(title=f"{site_choisi} — % par nature",title_x=0.5,margin=dict(t=40,b=10,l=10,r=10),height=300,
                                                 paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',legend=dict(font=dict(size=9)))
                            st.plotly_chart(figv1,use_container_width=True,config={'displayModeBar':False})
                    with vg2:
                        dsite = df_nature_v[df_nature_v["Site"]==site_choisi]
                        total_v = dsite["Nombre"].sum()
                        compte_v = {}
                        for _,row in dsite.iterrows():
                            for e in str(row["Pilote"]).split("+"):
                                e = e.strip()
                                if not e: continue
                                compte_v[e] = compte_v.get(e,0) + row["Nombre"]
                        if not compte_v or total_v==0:
                            st.info(f"Aucune donnée {site_choisi}.")
                        else:
                            ddv = pd.DataFrame({"Pilote":list(compte_v.keys()),"Nombre":list(compte_v.values())})
                            ddv["Pourcentage"] = (ddv["Nombre"]/total_v*100).round(1)
                            ddv = ddv.sort_values("Pourcentage",ascending=True)
                            figv2 = px.bar(ddv,x="Pourcentage",y="Pilote",orientation="h",text="Pourcentage",
                                           color="Pilote",color_discrete_map=color_map_pil_v)
                            figv2.update_traces(texttemplate='%{text}%',textposition='outside',cliponaxis=False)
                            figv2.update_layout(title=f"{site_choisi} — % par pilote",title_x=0.5,showlegend=False,
                                                 xaxis_title="% des actions",yaxis_title="",
                                                 margin=dict(t=40,b=10,l=10,r=30),height=300,
                                                 paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
                            st.plotly_chart(figv2,use_container_width=True,config={'displayModeBar':False})
                else:
                    st.info("Aucune donnée à afficher pour les graphes.")
