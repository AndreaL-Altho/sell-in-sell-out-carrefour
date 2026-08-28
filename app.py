import os
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Configuration de la page
st.set_page_config(
    page_title="Analyse Sell-In / Sell-Out Carrefour",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Tableau de Bord — Sell-In / Sell-Out Carrefour (en KG)")

# 2. Barre latérale
st.sidebar.header("📁 Chargement des données")
file_sell_in = st.sidebar.file_uploader(
    "Fichier Sell-In (CARREFOUR_IN.xlsx)", type=["xlsx"]
)
file_sell_out = st.sidebar.file_uploader(
    "Fichier Sell-Out (Nielsen.xlsx)", type=["xlsx"]
)


# Fonction d'affichage d'image mise à jour (width="stretch" évite les warnings)
def show_notebook_image(path: str, caption: str):
    if os.path.exists(path):
        st.image(path, caption=caption, width="stretch")
    else:
        st.warning(f"⚠️ L'image `{path}` n'a pas été trouvée.")


# 3. Onglets
tab_notebook, tab_excel, tab_lag = st.tabs(
    [
        "📸 Graphiques du Notebook",
        "🔍 Analyse Dynamique (Excel)",
        "⏱️ Décalage Temporel (Lag)",
    ]
)

# ONGLET 1 : NOTEBOOK
with tab_notebook:
    st.header("Visualisations issues de l'analyse Notebook")
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("1. Évolution Temporelle Globale")
        show_notebook_image(
            "images/courbe_sell_in_out.png",
            "Sell-In vs Sell-Out sur le périmètre EAN réellement couvert",
        )

        st.subheader("3. Flux Net d'Approvisionnement (Gap)")
        show_notebook_image(
            "images/flux_net_gap.png",
            "Écart d'approvisionnement (Sell-In − Sell-Out en KG)",
        )

    with col_right:
        st.subheader("2. Variation Cumulée du Stock (Proxy)")
        show_notebook_image(
            "images/proxy_stock.png", "Stock proxy cumulé (théorique)"
        )

        st.subheader("4. Régimes d'Approvisionnement (2025-2026)")
        show_notebook_image(
            "images/regimes_2025_2026.png",
            "Classification : Accumulation vs Déstockage",
        )

# ONGLET 2 : DYNAMIQUE EXCEL
with tab_excel:
    if file_sell_in and file_sell_out:
        df_in = pd.read_excel(file_sell_in)
        df_out = pd.read_excel(file_sell_out)

        eans_in = set(df_in["CODE EAN"].dropna().unique())
        eans_out = set(df_out["UPC"].dropna().unique())
        eans_communs = sorted(list(eans_in.intersection(eans_out)))

        df_in_filtered = df_in[df_in["CODE EAN"].isin(eans_communs)]
        df_out_filtered = df_out[df_out["UPC"].isin(eans_communs)]

        st.header("📈 Indicateurs Clés (Périmètre Commun)")
        m1, m2, m3 = st.columns(3)
        m1.metric("EAN Communiqués", len(eans_communs))
        m2.metric(
            "Total Sell-In (KG)", f"{df_in_filtered['CARREFOUR'].sum():,.0f} kg"
        )
        m3.metric(
            "Total Sell-Out (KG)",
            f"{df_out_filtered['CARREFOUR'].sum():,.0f} kg",
        )

        df_in_grp = (
            df_in_filtered.groupby("DATE")["CARREFOUR"].sum().reset_index()
        )
        df_in_grp.columns = ["DATE", "SELL_IN_KG"]

        df_out_grp = (
            df_out_filtered.groupby("DATE")["CARREFOUR"].sum().reset_index()
        )
        df_out_grp.columns = ["DATE", "SELL_OUT_KG"]

        df_compare = pd.merge(df_in_grp, df_out_grp, on="DATE", how="inner")

        st.subheader("Évolution globale Sell-In vs Sell-Out")
        fig_dyn = px.line(
            df_compare,
            x="DATE",
            y=["SELL_IN_KG", "SELL_OUT_KG"],
            labels={"value": "Volume (KG)", "variable": "Légende"},
            title="Comparaison Temporelle Dynamique",
        )
        st.plotly_chart(fig_dyn, width="stretch")

        st.subheader("🔍 Zoom par Référence (EAN)")
        selected_ean = st.selectbox("Sélectionner un EAN :", eans_communs)

        df_ean_in = (
            df_in_filtered[df_in_filtered["CODE EAN"] == selected_ean]
            .groupby("DATE")["CARREFOUR"]
            .sum()
            .reset_index()
        )
        df_ean_out = (
            df_out_filtered[df_out_filtered["UPC"] == selected_ean]
            .groupby("DATE")["CARREFOUR"]
            .sum()
            .reset_index()
        )
        df_ean_comp = pd.merge(
            df_ean_in,
            df_ean_out,
            on="DATE",
            how="outer",
            suffixes=("_IN", "_OUT"),
        ).fillna(0)

        fig_bar = px.bar(
            df_ean_comp,
            x="DATE",
            y=["CARREFOUR_IN", "CARREFOUR_OUT"],
            barmode="group",
            labels={"value": "KG", "variable": "Flux"},
            title=f"Volumes pour l'EAN {selected_ean}",
        )
        st.plotly_chart(fig_bar, width="stretch")
    else:
        st.info("👈 Dépose tes fichiers Excel dans le menu latéral à gauche.")

# ONGLET 3 : LAG
with tab_lag:
    st.header("Corrélation et Décalage d'Achat (Lag)")
    show_notebook_image(
        "images/correlation_lags.png",
        "Corrélation Sell-In / Sell-Out selon le nombre de semaines de décalage",
    )