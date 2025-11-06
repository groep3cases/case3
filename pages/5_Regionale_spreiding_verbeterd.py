import streamlit as st
import streamlit.components.v1 as components 
import pandas as pd
import geopandas as gpd
import numpy as np
import folium
import re
from branca.element import Template, MacroElement
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns

st.title('Regionale spreiding')
st.write("""Hier wordt gekeken naar waar zicht laadpunten bevinden in Nederland en hoe 
         de elektrische voertuigen zijn verspreid door het land.""")

tab1, tab2 = st.tabs(["Voertuigen","Laadpalen"])

# ----------------------- TAB 1 -----------------------
with tab1:

    st.write("""In de kaarten hieronder worden elektrische voertuigen die een geregistreerd kenteken hebben weergegeven. Er kan gefilterd
            worden op de belangrijkste soorten. De kenteken registratie postcode van de dataset is alleen gegeven als in het postcode gebied meer
            dan 10 dezelfde soort voertuigen geregistreed in verband met privacy. Houd er rekening dat de data is opgeschoond en grote uitschieters
            zijn verwijderd uit de datasets. Kijk op de homepagina voor meer informatie over de volledige dataset.""")

    keuze = st.selectbox('Kies een kaart om te bekijken:',
                    ["Kaart 1 -- Personenauto's",
                     "Kaart 2 -- Bedrijfsauto's",
                     "Kaart 3 -- Motorfietsen",
                     "Kaart 4 -- Bromfietsen",
                     "Kaart 5 -- Totaal"])

    kaarten = {
            "Kaart 1 -- Personenauto's": "kaarten/kaarten_old/Personenauto_kaart.html",
            "Kaart 2 -- Bedrijfsauto's": "kaarten/kaarten_old/Bedrijfsauto_kaart.html",
            "Kaart 3 -- Motorfietsen": "kaarten/kaarten_old/Motorfiets_kaart.html",
            "Kaart 4 -- Bromfietsen": "kaarten/kaarten_old/Bromfiets_kaart.html",
            "Kaart 5 -- Totaal": "kaarten/kaarten_old/totaal_kaart.html"}

    html_path = kaarten[keuze]
    with open(html_path, "r", encoding="utf-8") as f:
        html_data = f.read()

    components.html(html_data, height=650, width=None)

    df = pd.read_csv("data/Brandstoffen_op_PC4_20251001.csv")
    gdf = gpd.read_file("data/cbs_pc4_2024_v1.gpkg")[['postcode','aantal_inwoners']]
    df_merged = df.merge(gdf, left_on="Postcode", right_on="postcode", how="left")

    df_merged.loc[df_merged["aantal_inwoners"] < 0, "aantal_inwoners"] = None 
    df_merged = df_merged[df_merged["aantal_inwoners"] >= 1250]

    df_filtered = df_merged[
        (df_merged["Aantal"] <= df_merged["aantal_inwoners"]) & 
        (df_merged["Brandstof"] == "E") &
        (df_merged["Voertuigsoort"] == "Personenauto")
    ]

    df_sorted = df_filtered.sort_values("Aantal", ascending=False)
    st.subheader("Top 10 postcodes met de meeste elektrische personenauto’s")
    st.dataframe(df_sorted[['Postcode','Aantal','aantal_inwoners']].head(10))

    df_filtered['Percentage'] =  df_filtered['Aantal'] / df_filtered['aantal_inwoners'] * 100
    df_sorted = df_filtered.sort_values("Percentage", ascending=False)
    st.subheader("Top 10 postcodes met het hoogste percentage elektrische personenauto’s (t.o.v. inwoners)")
    st.dataframe(df_sorted[['Postcode','Aantal','aantal_inwoners','Percentage']].head(10))

# ----------------------- TAB 2 -----------------------
with tab2:

    data = pd.read_csv('data/OpenChargeMapNL.csv')

    # Controleer kolomnamen
    st.write("Kolommen in CSV:", data.columns)

    # Kosten extraheren
    def extract_cost(text):
        if pd.isna(text):
            return np.nan
        text = str(text).lower().replace(',', '.')  
        match = re.search(r'€\s*([\d.]+)', text)   
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return np.nan
        match_fallback = re.search(r'(\d+\.\d+|\d+)', text)
        if match_fallback:
            try:
                value = float(match_fallback.group(1))
                if 'ct' in text and value > 1:
                    value = value / 100
                return value
            except ValueError:
                return np.nan
        return np.nan

    data['ParsedCost'] = data['UsageCost'].apply(extract_cost)
    mediaan = data['ParsedCost'].median()
    data['FinalCost'] = data['ParsedCost'].fillna(mediaan)

    def cost_category(cost):
        if cost == 0:
            return 'Niet bekend'
        elif cost < 0.30:
            return 'Goedkoop'
        elif cost < 0.40:
            return 'Duur'
        else:
            return 'Zeer duur'

    data['CostCategory'] = data['FinalCost'].apply(cost_category)
    kleur_mapping = {'Niet bekend' : 'grey', 'Goedkoop': 'lightgreen', 'Duur': 'orange', 'Zeer duur': 'red'}
    data['Color'] = data['CostCategory'].map(kleur_mapping)
    data = data.dropna(subset=['AddressInfo.Latitude', 'AddressInfo.Longitude'])

    # Folium kaart maken
    m = folium.Map(location=[52.3702, 4.8952], zoom_start=8, tiles='OpenStreetMap')

    laag_nietbekend = folium.FeatureGroup(name='Niet bekend')
    laag_goedkoop = folium.FeatureGroup(name='Goedkoop')
    laag_duur = folium.FeatureGroup(name='Duur')
    laag_zeer_duur = folium.FeatureGroup(name='Zeer duur')

    for _, row in data.iterrows():
        tooltip_text = f"""
        <strong>Locatie:</strong> {row.get('AddressInfo.AddressLine1', 'Onbekend')}<br>
        <strong>Oorspronkelijke tekst:</strong> {row.get('UsageCost', 'n.v.t.')}<br>
        <strong>Gebruikte prijs:</strong> €{row['FinalCost']:.2f}/kWh
        """
        marker = folium.CircleMarker(
            location=[row['AddressInfo.Latitude'], row['AddressInfo.Longitude']],
            radius=5, color=row['Color'], fill=True, fill_color=row['Color'], fill_opacity=0.8,
            tooltip=tooltip_text
        )
        if row['CostCategory'] == 'Niet bekend':
            marker.add_to(laag_nietbekend)
        elif row['CostCategory'] == 'Goedkoop':
            marker.add_to(laag_goedkoop)
        elif row['CostCategory'] == 'Duur':
            marker.add_to(laag_duur)
        else:
            marker.add_to(laag_zeer_duur)

    laag_nietbekend.add_to(m)
    laag_goedkoop.add_to(m)
    laag_duur.add_to(m)
    laag_zeer_duur.add_to(m)

    folium.LayerControl().add_to(m)
    m.save('kaarten/kaart1_case3.html')
    with open('kaarten/kaart1_case3.html', "r", encoding="utf-8") as f:
        html_data = f.read()
    components.html(html_data, height=650)

    # ------------------- Prijs door de tijd -------------------
    # Check of kolom bestaat
    if "DateLastVerified" in data.columns and "UsageCost" in data.columns:
        df_time = data.copy()
        df_time['jaar'] = pd.to_datetime(df_time["DateLastVerified"], errors="coerce").dt.year
        df_time['prijs'] = df_time["UsageCost"].str.extract(r"€\s?(\d+[.,]\d{2})")
        df_time['prijs'] = df_time['prijs'].str.replace(",", ".").astype(float)
        df_time = df_time.dropna(subset=['jaar','prijs'])

        fig = px.scatter(
            df_time, x='jaar', y='prijs', title='Gebruikerskosten (€/kWh) door de tijd',
            labels={'jaar': 'Jaar', 'prijs': 'Gebruikerskosten (€/kWh)'}, opacity=0.6
        )

        gemiddelde_per_jaar = df_time.groupby("jaar")["prijs"].mean().reset_index()
        fig2 = px.line(
            gemiddelde_per_jaar, x='jaar', y='prijs', markers=True,
            title='Gemiddelde gebruikerskosten (€/kWh) per jaar',
            labels={'jaar':'Jaar','prijs':'Gemiddelde prijs per kWh (€)'},
            template='plotly_white', line_shape='spline'
        )
        fig2.update_traces(fill="tozeroy")
        fig2.update_layout(hovermode="x unified")
        st.plotly_chart(fig)
        st.plotly_chart(fig2)
    else:
        st.warning("Kolommen 'DateLastVerified' of 'UsageCost' ontbreken in de dataset, grafiek door de tijd kan niet worden weergegeven.")
