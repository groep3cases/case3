# ======================================================
# 🧭 DASHBOARD - Regionale Spreiding van Elektrisch Vervoer in Nederland
# Verbeterde versie met interactieve visualisaties en consistente stijl
# ======================================================

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import geopandas as gpd
import numpy as np
import folium
import json
import re
import plotly.express as px
from branca.element import Template, MacroElement

# ------------------------------------------------------
# 🏠 Algemene instellingen
# ------------------------------------------------------
st.set_page_config(page_title="Regionale spreiding EV's", layout="wide")
st.title("🚗 Regionale spreiding van elektrische voertuigen en laadpalen")

st.markdown("""
In dit dashboard wordt de regionale verdeling van elektrische voertuigen en laadpunten in Nederland weergegeven. 
Gebruik de tabs hieronder om inzicht te krijgen in:
- de spreiding van **elektrische voertuigen per postcodegebied**
- de **locatie en kostenstructuur van laadpalen**
""")

# ------------------------------------------------------
# Tabs
# ------------------------------------------------------
tab1, tab2 = st.tabs(["🚘 Voertuigen", "⚡ Laadpalen"])

# ------------------------------------------------------
# 🔹 TAB 1: VOERTUIGEN
# ------------------------------------------------------
with tab1:
    st.markdown("""
    ### Elektrische voertuigen per postcodegebied
    In de kaarten hieronder worden geregistreerde elektrische voertuigen weergegeven.
    Filter op type voertuig en bekijk de spreiding over Nederland.
    """)

    # Keuze voor voertuigsoort
    keuze = st.selectbox(
        "Kies voertuigtype:",
        ["Personenauto", "Bedrijfsauto", "Motorfiets", "Bromfiets"]
    )

    # Data inladen
    df = pd.read_csv("data/Brandstoffen_op_PC4_20251001.csv")
    gdf = gpd.read_file("data/cbs_pc4_2024_v1.gpkg")[['postcode', 'aantal_inwoners']]
    geojson_json = json.loads(gdf.to_crs("EPSG:4326").to_json())

    # Merge en filtering
    df_merged = df.merge(gdf, left_on="Postcode", right_on="postcode", how="left")
    df_merged = df_merged[df_merged["aantal_inwoners"] >= 1250]
    df_merged = df_merged[(df_merged["Brandstof"] == "E") & (df_merged["Voertuigsoort"] == keuze)]

    # Bereken percentage
    df_merged["Percentage"] = df_merged["Aantal"] / df_merged["aantal_inwoners"] * 100

    # ------------------------------------------------------
    # Interactieve kaart
    # ------------------------------------------------------
    st.subheader(f"📍 Aantal elektrische {keuze.lower()}s per postcodegebied")
    fig_map = px.choropleth_mapbox(
        df_merged,
        geojson=geojson_json,
        locations="Postcode",
        featureidkey="properties.postcode",
        color="Aantal",
        color_continuous_scale="viridis",
        mapbox_style="carto-positron",
        zoom=6.3,
        center={"lat": 52.1, "lon": 5.3},
        opacity=0.7,
        labels={"Aantal": "Aantal voertuigen"}
    )
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)

    # ------------------------------------------------------
    # Top 10 tabellen
    # ------------------------------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏆 Top 10 postcodes (absolute aantallen)")
        st.dataframe(df_merged.sort_values("Aantal", ascending=False).head(10)[["Postcode", "Aantal", "aantal_inwoners"]])

    with col2:
        st.subheader("📈 Top 10 postcodes (percentage t.o.v. inwoners)")
        st.dataframe(df_merged.sort_values("Percentage", ascending=False).head(10)[["Postcode", "Aantal", "aantal_inwoners", "Percentage"]])

    st.markdown("---")

# ------------------------------------------------------
# 🔹 TAB 2: LAADPALEN
# ------------------------------------------------------
with tab2:
    st.markdown("### Laadpalen en gebruikerskosten in Nederland")

    data = pd.read_csv('data/OpenChargeMapNL.csv')

    # ------------------------------------------------------
    # Voorbewerking prijs
    # ------------------------------------------------------
    def extract_cost(text):
        if pd.isna(text):
            return np.nan
        text = str(text).lower().replace(',', '.')
        match = re.search(r'€\s*([\d.]+)', text)
        if match:
            return float(match.group(1))
        match_fallback = re.search(r'(\d+\.\d+|\d+)', text)
        if match_fallback:
            value = float(match_fallback.group(1))
            if 'ct' in text and value > 1:
                value /= 100
            return value
        return np.nan

    data['ParsedCost'] = data['UsageCost'].apply(extract_cost)
    mediaan = data['ParsedCost'].median()
    data['FinalCost'] = data['ParsedCost'].fillna(mediaan)

    # Categorieën
    def cost_category(cost):
        if pd.isna(cost):
            return 'Niet bekend'
        elif cost < 0.30:
            return 'Goedkoop'
        elif cost < 0.40:
            return 'Duur'
        else:
            return 'Zeer duur'

    data['CostCategory'] = data['FinalCost'].apply(cost_category)

    # ------------------------------------------------------
    # KPI’s
    # ------------------------------------------------------
    avg_price = data['FinalCost'].mean()
    total_points = len(data)
    cheapest = data.loc[data['FinalCost'].idxmin()]

    col1, col2, col3 = st.columns(3)
    col1.metric("🔌 Aantal laadpunten", f"{total_points:,}")
    col2.metric("💶 Gemiddelde prijs (€/kWh)", f"{avg_price:.2f}")
    col3.metric("📍 Goedkoopste laadpaal", f"€{cheapest['FinalCost']:.2f}")

    # ------------------------------------------------------
    # Interactieve kaart Folium
    # ------------------------------------------------------
    data = data.dropna(subset=['AddressInfo.Latitude', 'AddressInfo.Longitude'])
    m = folium.Map(location=[52.3702, 4.8952], zoom_start=7, tiles='CartoDB positron')

    kleur_mapping = {
        'Niet bekend': 'grey',
        'Goedkoop': 'lightgreen',
        'Duur': 'orange',
        'Zeer duur': 'red'
    }

    for _, row in data.iterrows():
        tooltip_text = f"""
        <strong>Locatie:</strong> {row.get('AddressInfo.AddressLine1', 'Onbekend')}<br>
        <strong>Kosten:</strong> €{row['FinalCost']:.2f}/kWh<br>
        <strong>Categorie:</strong> {row['CostCategory']}
        """
        folium.CircleMarker(
            location=[row['AddressInfo.Latitude'], row['AddressInfo.Longitude']],
            radius=4,
            color=kleur_mapping[row['CostCategory']],
            fill=True,
            fill_color=kleur_mapping[row['CostCategory']],
            fill_opacity=0.7,
            tooltip=tooltip_text
        ).add_to(m)

    folium.LayerControl().add_to(m)

    # Legenda
    template = """
    {% macro html(this, kwargs) %}
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 160px;
        background-color: white;
        border:2px solid grey;
        z-index:9999;
        font-size:14px;
        padding: 10px;
        box-shadow: 3px 3px 6px rgba(0,0,0,0.3);
    ">
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

    m.save('kaarten/kaart_case_nieuw.html')
    with open('kaarten/kaart_case_nieuw.html', "r", encoding="utf-8") as f:
        html_data = f.read()

    components.html(html_data, height=650, width=None)

    st.markdown("---")

    # ------------------------------------------------------
    # Prijsontwikkeling in de tijd
    # ------------------------------------------------------
    data['jaar'] = pd.to_datetime(data['DateLastVerified'], errors='coerce').dt.year
    prijs_data = data[['jaar', 'FinalCost']].dropna()

    fig_trend = px.scatter(
        prijs_data,
        x='jaar',
        y='FinalCost',
        trendline="ols",
        color_discrete_sequence=["#00AEEF"],
        title="📊 Ontwikkeling gebruikerskosten van laadpalen door de jaren heen",
        labels={"jaar": "Jaar", "FinalCost": "Prijs (€/kWh)"}
    )
    fig_trend.update_layout(template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig_trend, use_container_width=True)

    # ------------------------------------------------------
    # Kosten per provincie
    # ------------------------------------------------------
    data['AddressInfo.StateOrProvince'] = data['AddressInfo.StateOrProvince'].astype(str).str.strip()
    provincie_mapping = {
        'NH': 'Noord-Holland', 'ZH': 'Zuid-Holland', 'UT': 'Utrecht',
        'FRL': 'Friesland', 'North Holland': 'Noord-Holland',
        'South Holland': 'Zuid-Holland', 'North Brabant': 'Noord-Brabant',
        'Fryslân': 'Friesland'
    }
    data['Provincie'] = data['AddressInfo.StateOrProvince'].replace(provincie_mapping)
    data = data.dropna(subset=['Provincie'])

    kosten_per_prov = (
        data.groupby('Provincie')['FinalCost']
        .mean()
        .reset_index()
        .sort_values('FinalCost')
    )

    fig_prov = px.bar(
        kosten_per_prov,
        x='Provincie',
        y='FinalCost',
        color='FinalCost',
        color_continuous_scale='viridis',
        title='📍 Gemiddelde gebruikerskosten per provincie (€/kWh)',
        labels={'FinalCost': 'Gemiddelde prijs (€/kWh)'}
    )
    fig_prov.update_layout(template='simple_white', xaxis_tickangle=-45)
    st.plotly_chart(fig_prov, use_container_width=True)
