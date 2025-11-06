import streamlit as st
import streamlit.components.v1 as components 
import pandas as pd
import geopandas as gpd
import numpy as np
import folium
from folium.plugins import MarkerCluster
import re
from branca.element import Template, MacroElement
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns


st.title('Regionale spreiding')
st.write("""
Hier wordt gekeken naar waar zicht laadpunten bevinden in Nederland en hoe elektrische voertuigen zijn verspreid door het land.
""")


tab1, tab2 = st.tabs(["Voertuigen","Laadpalen"])


with tab1:

    st.write("""
In de kaarten hieronder worden elektrische voertuigen die een geregistreerd kenteken hebben weergegeven. Er kan gefilterd
worden op de belangrijkste soorten. De kenteken registratie postcode van de dataset is alleen gegeven als in het postcode gebied meer
dan 10 dezelfde soort voertuigen geregistreerd zijn in verband met privacy. Kijk op de homepagina voor meer informatie over de volledige dataset.
""")

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
    components.html(html_data, height=650)

    
    df = pd.read_csv("data/Brandstoffen_op_PC4_20251001.csv")
    gdf = gpd.read_file("data/cbs_pc4_2024_v1.gpkg")[['postcode','aantal_inwoners']]
    df_merged = df.merge(gdf, left_on="Postcode", right_on="postcode", how="left")
    df_merged = df_merged.copy()
    df_merged.loc[df_merged["aantal_inwoners"] < 0, "aantal_inwoners"] = None 
    df_merged = df_merged[df_merged["aantal_inwoners"] >= 1250]

    df_filtered = df_merged[
        (df_merged["Aantal"] <= df_merged["aantal_inwoners"]) &
        (df_merged["Brandstof"] == "E") &
        (df_merged["Voertuigsoort"] == "Personenauto")
    ]

   
    df_sorted = df_filtered.sort_values("Aantal", ascending=False)
    top10_aantal = df_sorted.head(10)

    fig_top10 = px.bar(
        top10_aantal,
        x='Aantal',
        y='Postcode',
        orientation='h',
        text='Aantal',
        title='Top 10 postcodes met de meeste elektrische personenauto’s',
        template='plotly_white'
    )
    fig_top10.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_top10)

    df_filtered = df_filtered.copy()
    df_filtered['Percentage'] = df_filtered['Aantal'] / df_filtered['aantal_inwoners'] * 100
    df_sorted_pct = df_filtered.sort_values("Percentage", ascending=False)
    top10_pct = df_sorted_pct.head(10)

    fig_pct = px.bar(
        top10_pct,
        x='Percentage',
        y='Postcode',
        orientation='h',
        text='Percentage',
        title='Top 10 postcodes met hoogste percentage elektrische personenauto’s',
        template='plotly_white'
    )
    fig_pct.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_pct)


with tab2:

    data = pd.read_csv('data/OpenChargeMapNL.csv')

  
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
    kleur_mapping = {'Niet bekend':'grey','Goedkoop':'lightgreen','Duur':'orange','Zeer duur':'red'}
    data['Color'] = data['CostCategory'].map(kleur_mapping)
    data = data.dropna(subset=['AddressInfo.Latitude', 'AddressInfo.Longitude'])

   
    m = folium.Map(location=[52.3702, 4.8952], zoom_start=8, tiles='OpenStreetMap')
    cluster = MarkerCluster().add_to(m)
    for _, row in data.iterrows():
        tooltip_text = f"{row.get('AddressInfo.AddressLine1','Onbekend')} - €{row['FinalCost']:.2f}/kWh"
        folium.CircleMarker(
            location=[row['AddressInfo.Latitude'], row['AddressInfo.Longitude']],
            radius=5,
            color=row['Color'],
            fill=True,
            fill_color=row['Color'],
            fill_opacity=0.8,
            tooltip=tooltip_text
        ).add_to(cluster)

    folium.LayerControl().add_to(m)
    m.save('kaarten/kaart1_case3.html')
    with open('kaarten/kaart1_case3.html', "r", encoding="utf-8") as f:
        html_data = f.read()
    components.html(html_data, height=650)

    st.write("""
Hierboven is de kaart van Nederland weergegeven, waarbij de gebruikerskosten per oplaadpaal in euro per kilowattuur 
worden weergegeven.
""")

   
    df['jaar'] = pd.to_datetime(df["DateLastVerified"], errors="coerce").dt.year
    df["prijs"] = df["UsageCost"].str.extract(r"€\s?(\d+[.,]\d{2})")[0]
    df["prijs"] = df["prijs"].str.replace(",", ".").astype(float)
    df_prijs_per_jaar = df[["jaar", "prijs"]].dropna()

    gemiddelde_per_jaar = df_prijs_per_jaar.groupby("jaar")["prijs"].mean().reset_index()

    fig_time = px.scatter(df_prijs_per_jaar, x='jaar', y='prijs', opacity=0.6, labels={'jaar':'Jaar','prijs':'€/kWh'})
    fig_time.add_scatter(x=gemiddelde_per_jaar['jaar'], y=gemiddelde_per_jaar['prijs'], mode='lines+markers', name='Gemiddelde', line=dict(color='red'))
    fig_time.update_layout(title='Gebruikerskosten van laadpalen door de tijd')
    st.plotly_chart(fig_time)

    
    data['AddressInfo.StateOrProvince'] = data['AddressInfo.StateOrProvince'].astype(str).str.strip()
    provincie_mapping = {
        'NH':'Noord-Holland','North-Holland':'Noord-Holland','North Holland':'Noord-Holland','Noord Holland':'Noord-Holland',
        'ZH':'Zuid-Holland','South-Holland':'Zuid-Holland','South Holland':'Zuid-Holland','Zuid Holland':'Zuid-Holland',
        'North Brabant':'Noord-Brabant','UT':'Utrecht','FRL':'Friesland','Frisia':'Friesland','Fryslân':'Friesland',
        'Brussels':'Buitenland','Antwerp':'Buitenland','Berlin':'Buitenland','None':None,'nan':None
    }
    data['AddressInfo.StateOrProvince'] = data['AddressInfo.StateOrProvince'].replace(provincie_mapping)
    data = data.dropna(subset=['AddressInfo.StateOrProvince', 'UsageCost'])
    data['UsageCostClean'] = data['UsageCost'].apply(lambda x: float(re.sub(r'[^\d,.]', '', str(x)).replace(',', '.')) if re.search(r'\d', str(x)) else np.nan)
    data = data.dropna(subset=['UsageCostClean'])

    avg_costs = data.groupby('AddressInfo.StateOrProvince')['UsageCostClean'].mean().reset_index()
    avg_costs = avg_costs.rename(columns={'AddressInfo.StateOrProvince':'Provincie','UsageCostClean':'GemiddeldeKosten'}).sort_values('GemiddeldeKosten')

    fig_prov = px.bar(
        avg_costs,
        x='Provincie',
        y='GemiddeldeKosten',
        color='GemiddeldeKosten',
        color_continuous_scale='viridis',
        text='GemiddeldeKosten',
        title='Gemiddelde gebruikerskosten van oplaadpalen per provincie (€/kWh)'
    )
    fig_prov.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_prov)

