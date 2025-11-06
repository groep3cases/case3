import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import geopandas as gpd
import numpy as np
import folium
import re
import json
from branca.element import Template, MacroElement
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------------------------
# 🧭 Titel & Introductie
# ---------------------------------------------------------------
st.title("Regionale spreiding")
st.write("""
Hier wordt gekeken naar waar zich laadpunten bevinden in Nederland en hoe 
de elektrische voertuigen zijn verspreid door het land.
""")

tab1, tab2 = st.tabs(["🚗 Voertuigen", "⚡ Laadpalen"])

# ---------------------------------------------------------------
# TAB 1 – Elektrische voertuigen
# ---------------------------------------------------------------
with tab1:
    st.write("""
    In de kaarten hieronder worden elektrische voertuigen weergegeven die een geregistreerd kenteken hebben. 
    Er kan gefilterd worden op voertuigsoort. De kentekenregistratiepostcode is alleen opgenomen in gebieden 
    met meer dan 10 voertuigen van hetzelfde type (i.v.m. privacy). 
    Houd er rekening mee dat de data is opgeschoond — zie de homepagina voor meer informatie.
    """)

    keuze = st.selectbox(
        "Kies een kaart om te bekijken:",
        [
            "Kaart 1 -- Personenauto's",
            "Kaart 2 -- Bedrijfsauto's",
            "Kaart 3 -- Motorfietsen",
            "Kaart 4 -- Bromfietsen",
            "Kaart 5 -- Totaal"
        ]
    )

    kaarten = {
        "Kaart 1 -- Personenauto's": "kaarten/kaarten_old/Personenauto_kaart.html",
        "Kaart 2 -- Bedrijfsauto's": "kaarten/kaarten_old/Bedrijfsauto_kaart.html",
        "Kaart 3 -- Motorfietsen": "kaarten/kaarten_old/Motorfiets_kaart.html",
        "Kaart 4 -- Bromfietsen": "kaarten/kaarten_old/Bromfiets_kaart.html",
        "Kaart 5 -- Totaal": "kaarten/kaarten_old/totaal_kaart.html"
    }

    html_path = kaarten[keuze]
    with open(html_path, "r", encoding="utf-8") as f:
        html_data = f.read()

    components.html(html_data, height=650)

    # ------------------------------
    # 📊 Data inladen en samenvoegen
    # ------------------------------
    df = pd.read_csv("data/Brandstoffen_op_PC4_20251001.csv")
    gdf = gpd.read_file("data/cbs_pc4_2024_v1.gpkg")

    # Kolomnamen checken en hernoemen indien nodig
    if 'PC4' in gdf.columns and 'postcode' not in gdf.columns:
        gdf = gdf.rename(columns={'PC4': 'postcode'})

    # Alleen relevante kolommen behouden, inclusief geometrie
    gdf = gdf[['postcode', 'aantal_inwoners', 'geometry']]

    # Data samenvoegen
    df_merged = df.merge(gdf, left_on="Postcode", right_on="postcode", how="left")
    df_merged.loc[df_merged["aantal_inwoners"] < 0, "aantal_inwoners"] = None
    df_merged = df_merged[df_merged["aantal_inwoners"] >= 1250]

    df_filtered = df_merged[
        (df_merged["Aantal"] <= df_merged["aantal_inwoners"]) &
        (df_merged["Brandstof"] == "E") &
        (df_merged["Voertuigsoort"] == "Personenauto")
    ].copy()

    # Top 10 absolute aantallen
    df_sorted = df_filtered.sort_values("Aantal", ascending=False)
    st.subheader("🏙️ Top 10 postcodes met de meeste elektrische personenauto’s")
    st.dataframe(df_sorted[['Postcode', 'Aantal', 'aantal_inwoners']].head(10))

    # Top 10 percentages
    df_filtered['Percentage'] = df_filtered['Aantal'] / df_filtered['aantal_inwoners'] * 100
    df_sorted = df_filtered.sort_values("Percentage", ascending=False)
    st.subheader("📈 Top 10 postcodes met hoogste percentage elektrische personenauto’s (t.o.v. inwoners)")
    st.dataframe(df_sorted[['Postcode', 'Aantal', 'aantal_inwoners', 'Percentage']].head(10))

# ---------------------------------------------------------------
# TAB 2 – Laadpalen
# ---------------------------------------------------------------
with tab2:
    data = pd.read_csv("data/OpenChargeMapNL.csv")

    # -----------------------------------------------------------
    # 💶 Gebruikerskosten extractie
    # -----------------------------------------------------------
    def extract_cost(text):
        if pd.isna(text):
            return np.nan
        text = str(text).lower().replace(",", ".")
        match = re.search(r"€\s*([\d.]+)", text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return np.nan
        match_fallback = re.search(r"(\d+\.\d+|\d+)", text)
        if match_fallback:
            try:
                value = float(match_fallback.group(1))
                if "ct" in text and value > 1:
                    value = value / 100
                return value
            except ValueError:
                return np.nan
        return np.nan

    data["ParsedCost"] = data["UsageCost"].apply(extract_cost)
    data["FinalCost"] = data["ParsedCost"].fillna(data["ParsedCost"].median())

    def cost_category(cost):
        if cost == 0:
            return "Niet bekend"
        elif cost < 0.30:
            return "Goedkoop"
        elif cost < 0.40:
            return "Duur"
        else:
            return "Zeer duur"

    data["CostCategory"] = data["FinalCost"].apply(cost_category)
    kleur_mapping = {"Niet bekend": "grey", "Goedkoop": "lightgreen", "Duur": "orange", "Zeer duur": "red"}
    data["Color"] = data["CostCategory"].map(kleur_mapping)
    data = data.dropna(subset=["AddressInfo.Latitude", "AddressInfo.Longitude"])

    # -----------------------------------------------------------
    # 🗺️ Folium kaart
    # -----------------------------------------------------------
    m = folium.Map(location=[52.3702, 4.8952], zoom_start=8, tiles="OpenStreetMap")

    lagen = {cat: folium.FeatureGroup(name=cat) for cat in kleur_mapping.keys()}

    for _, row in data.iterrows():
        tooltip_text = f"""
        <strong>Locatie:</strong> {row.get('AddressInfo.AddressLine1', 'Onbekend')}<br>
        <strong>Oorspronkelijke tekst:</strong> {row.get('UsageCost', 'n.v.t.')}<br>
        <strong>Gebruikte prijs:</strong> €{row['FinalCost']:.2f}/kWh
        """
        marker = folium.CircleMarker(
            location=[row["AddressInfo.Latitude"], row["AddressInfo.Longitude"]],
            radius=5,
            color=row["Color"],
            fill=True,
            fill_color=row["Color"],
            fill_opacity=0.8,
            tooltip=tooltip_text
        )
        lagen[row["CostCategory"]].add_child(marker)

    for layer in lagen.values():
        layer.add_to(m)

    folium.TileLayer("CartoDB positron", name="Licht thema").add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="Donker thema").add_to(m)
    folium.LayerControl().add_to(m)

    # Legenda toevoegen
    template = """
    {% macro html(this, kwargs) %}
    <div style="position: fixed; bottom: 50px; left: 50px; width: 160px;
        background-color: white; border:2px solid grey; z-index:9999;
        font-size:14px; padding: 10px; box-shadow: 3px 3px 6px rgba(0,0,0,0.3);">
        <b>Kosten legenda</b><br>
        &nbsp;<i class="fa fa-circle" style="color:grey"></i>&nbsp;Niet bekend<br>
        &nbsp;<i class="fa fa-circle" style="color:lightgreen"></i>&nbsp;Goedkoop<br>
        &nbsp;<i class="fa fa-circle" style="color:orange"></i>&nbsp;Duur<br>
        &nbsp;<i class="fa fa-circle" style="color:red"></i>&nbsp;Zeer duur<br>
    </div>
    {% endmacro %}
    """
    macro = MacroElement()
    macro._template = Template(template)
    m.get_root().add_child(macro)

    m.save("kaarten/laadpalen_map.html")
    with open("kaarten/laadpalen_map.html", "r", encoding="utf-8") as f:
        html_data = f.read()
    components.html(html_data, height=650)

    # -----------------------------------------------------------
    # 📈 Tijdreeks van kosten
    # -----------------------------------------------------------
    df = data.copy()
    df["jaar"] = pd.to_datetime(df["DateLastVerified"], errors="coerce").dt.year
    df["prijs"] = df["ParsedCost"]

    fig = px.scatter(
        df,
        x="jaar",
        y="prijs",
        title="Gebruikerskosten (€/kWh) door de tijd",
        labels={"jaar": "Jaar", "prijs": "Gebruikerskosten (€/kWh)"},
        opacity=0.6,
        template="plotly_white"
    )

    gemiddelde_per_jaar = df.groupby("jaar")["prijs"].mean().reset_index().sort_values("jaar")

    fig2 = px.line(
        gemiddelde_per_jaar,
        x="jaar",
        y="prijs",
        title="Gemiddelde gebruikerskosten (€/kWh) per jaar",
        markers=True,
        template="plotly_white",
        line_shape="spline"
    )
    fig2.update_traces(fill="tozeroy")

    st.plotly_chart(fig)
    st.plotly_chart(fig2)

    # -----------------------------------------------------------
    # 📊 Gemiddelde kosten per provincie (verbeterd)
    # -----------------------------------------------------------
    provincie_mapping = {
        'NH': 'Noord-Holland', 'ZH': 'Zuid-Holland', 'UT': 'Utrecht', 'NB': 'Noord-Brabant',
        'FRL': 'Friesland', 'GR': 'Groningen', 'OV': 'Overijssel', 'GE': 'Gelderland',
        'ZE': 'Zeeland', 'FL': 'Flevoland', 'DR': 'Drenthe', 'LI': 'Limburg',
        'North Holland': 'Noord-Holland', 'South Holland': 'Zuid-Holland',
        'North Brabant': 'Noord-Brabant', 'Fryslân': 'Friesland',
        'Gelderland Province': 'Gelderland', 'Overijssel Province': 'Overijssel'
    }

    data["Provincie"] = data["AddressInfo.StateOrProvince"].replace(provincie_mapping)
    echte_provincies = [
        "Groningen", "Friesland", "Drenthe", "Overijssel", "Flevoland",
        "Gelderland", "Utrecht", "Noord-Holland", "Zuid-Holland",
        "Zeeland", "Noord-Brabant", "Limburg"
    ]
    data = data[data["Provincie"].isin(echte_provincies)]
    data = data[(data["FinalCost"] > 0) & (data["FinalCost"] < 1.5)]

    kosten_per_prov = (
        data.groupby("Provincie")["FinalCost"]
        .mean()
        .reset_index()
        .sort_values("FinalCost", ascending=True)
    )

    fig_prov = px.bar(
        kosten_per_prov,
        x="Provincie",
        y="FinalCost",
        text="FinalCost",
        color="FinalCost",
        color_continuous_scale="RdYlGn_r",
        title="💡 Gemiddelde gebruikerskosten per provincie (€/kWh)",
        labels={"FinalCost": "Gemiddelde prijs (€/kWh)"}
    )

    fig_prov.update_traces(texttemplate="€%{text:.2f}", textposition="outside")
    fig_prov.update_layout(
        template="plotly_white",
        xaxis_title=None,
        yaxis_title="Gemiddelde prijs (€/kWh)",
        coloraxis_showscale=False,
        xaxis_tickangle=-45,
        margin=dict(l=40, r=40, t=80, b=120)
    )

    st.plotly_chart(fig_prov, use_container_width=True)
