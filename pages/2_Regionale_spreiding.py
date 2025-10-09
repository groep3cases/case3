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
with tab1:

    st.write("""In de kaarten hieronder worden elektrische voertuigen die een geregistreerd kenteken hebben weergegeven. Er kan gefilterd
            worden op de belangrijkste soorten. De kenteken registratie postcode van de dataset is alleen gegeven als in het postcode gebied meer
            dan 10 dezelfde soort voertuigen geregistreed in verband met privacy. Houd er rekening dat de data is opgeschoond en grote uitschieters
            zijn verwijderd uit de datasets. Kijk op de homepagina voor meer informatie over de volledige dataset """)

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

    # --- Sanity check: verwijder negatieve of te kleine inwoneraantallen ---
    df_merged = df_merged.copy()
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

    df_filtered = df_filtered.copy()
    df_filtered['Percentage'] =  df_filtered['Aantal'] / df_filtered['aantal_inwoners'] * 100
    df_sorted = df_filtered.sort_values("Percentage", ascending=False)
    st.subheader("Top 10 postcodes met het hoogste percentage elektrische personenauto’s (t.o.v. inwoners)")
    st.dataframe(df_sorted[['Postcode','Aantal','aantal_inwoners','Percentage']].head(10))

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
        else:
            
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

    kleur_mapping = {
        'Niet bekend' : 'grey',
        'Goedkoop': 'lightgreen',
        'Duur': 'orange',
        'Zeer duur': 'red'
    }

    data['Color'] = data['CostCategory'].map(kleur_mapping)


    data = data.dropna(subset=['AddressInfo.Latitude', 'AddressInfo.Longitude'])


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
            radius=5,
            color=row['Color'],
            fill=True,
            fill_color=row['Color'],
            fill_opacity=0.8,
            tooltip=tooltip_text
        )
        if row['CostCategory'] == 'Niet bekend':
            marker.add_to(laag_nietbekend)
        elif row['CostCategory'] == 'Goedkoop':
            marker.add_to(laag_goedkoop)
        elif row['CostCategory'] == 'Duur':
            marker.add_to(laag_duur)
        elif row['CostCategory'] == 'Zeer duur':
            marker.add_to(laag_zeer_duur)

    laag_nietbekend.add_to(m)
    laag_goedkoop.add_to(m)
    laag_duur.add_to(m)
    laag_zeer_duur.add_to(m)


    folium.TileLayer(tiles="https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png", name='Zwart-wit', attr="Map tiles by Stamen Design, hosted by Stadia Maps").add_to(m)
    folium.TileLayer('OpenTopoMap', name='Topografie').add_to(m)
    folium.TileLayer('CartoDB positron', name='Licht thema').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='Donker thema').add_to(m)

    folium.LayerControl().add_to(m)


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

    m.save('kaarten/kaart1_case3.html')
    with open('kaarten/kaart1_case3.html', "r", encoding="utf-8") as f:
        html_data = f.read()

    components.html(html_data, height=650, width=None)

    st.write("""Hierboven is de kaart van Nederland weergegeven, waarbij de gebruikerskosten per oplaadpaal in euro per kilowattuur 
                is weergegeven. De gebrukerskosten van de oplaadpalen zijn hier onderverdeeld in categoriëen: 
                'Goedkoop(< €0,30/kWh)', 'Duur(€0,30/kWh : €0,40/kWh)' en 'Zeer duur(€0,40/kWh >)'.
                Wat op valt aan de kaart is dat er veel oplaadpalen in de randsteden staan. Verder is er geen duidelijk verband zichtbaar
                tussen plaats en prijs van een laadpaal. Veel data die onbeschikbaar in de prijs is of een niet publieke laadpaal of
                ontbrekend in de dataset.""")
    
    st.markdown("---")
    #-------------------------

    df = data.copy()
    df["jaar"] = pd.to_datetime(df["DateLastVerified"], errors="coerce").dt.year
    df["prijs"] = df["UsageCost"].str.extract(r"€\s?(\d+[.,]\d{2})")
    df["prijs"] = df["prijs"].str.replace(",", ".").astype(float)
    df_prijs_per_jaar = df[["jaar", "prijs"]].dropna()

    fig = px.scatter(
        data_frame=df,
        x='jaar',
        y='prijs',
        title='Gebruikerskosten (€/kWh) door de tijd',
        labels={'jaar': 'Jaar', 'prijs': 'Gebruikerskosten (€/kWh)'},
        opacity=0.6
    )
    gemiddelde_per_jaar = (
        df_prijs_per_jaar.groupby("jaar")["prijs"]
        .mean()
        .reset_index()
        .sort_values("jaar")
    )

    fig2 = px.line(
        data_frame=gemiddelde_per_jaar,
        x='jaar',
        y='prijs',
        title='Gemiddelde gebruikerskosten (€/kWh) per jaar',
        labels={
            'jaar': 'Jaar',
            'prijs': 'Gemiddelde gebruikerskosten (€/kWh)'
        },
        markers=True,
        template='plotly_white',
        line_shape='spline'
    )

    fig2.update_traces(fill="tozeroy")
    fig2.update_layout(
        hovermode="x unified",
        xaxis_title="Jaar",
        yaxis_title="Gemiddelde prijs per kWh (€)"
    )

    st.plotly_chart(fig)
    st.plotly_chart(fig2)

    st.write("""In de figuren is een tijdreeks te zien waarbij de gemiddelde gebruikerskosten van een laadpaal in Nederland
                is uitgezet tegen de tijd in jaren. Het is duidelijk te zien dat er een stijgend lijn is in prijs. """)

    st.markdown("---")

    data = pd.read_csv('data/OpenChargeMapNL.csv')
    data['AddressInfo.StateOrProvince'] = data['AddressInfo.StateOrProvince'].astype(str).str.strip()


    provincie_mapping = {
        # Noord-Holland
        'NH': 'Noord-Holland',
        'North-Holland': 'Noord-Holland',
        'North Holland': 'Noord-Holland',
        'Noord Holland': 'Noord-Holland',

        # Zuid-Holland
        'ZH': 'Zuid-Holland',
        'South-Holland': 'Zuid-Holland',
        'South Holland': 'Zuid-Holland',
        'Zuid Holland': 'Zuid-Holland',

        # Noord-Brabant
        'North Brabant': 'Noord-Brabant',

        # Utrecht
        'UT': 'Utrecht',

        # Friesland
        'FRL': 'Friesland',
        'Frisia': 'Friesland',
        'Fryslân': 'Friesland',

        # Buitenlandse of foutieve locaties
        'Brussels': 'Buitenland',
        'Antwerp': 'Buitenland',
        'Berlin': 'Buitenland',
        'None': None,
        'nan': None
    }

    data['AddressInfo.StateOrProvince'] = data['AddressInfo.StateOrProvince'].replace(provincie_mapping)
    data = data.dropna(subset=['AddressInfo.StateOrProvince', 'UsageCost'])


    def extract_price(text):
        match = re.search(r'€\s*([\d,.]+)', str(text))
        if match:
            value = match.group(1).replace(',', '.')
            try:
                return float(value)
            except ValueError:
                return None
        return None


    data['UsageCostClean'] = data['UsageCost'].apply(extract_price)


    data = data.dropna(subset=['UsageCostClean'])


    avg_costs = (
        data.groupby('AddressInfo.StateOrProvince')['UsageCostClean']
        .mean()
        .reset_index()
        .rename(columns={
            'AddressInfo.StateOrProvince': 'Provincie',
            'UsageCostClean': 'GemiddeldeKosten'
        })
    )


    avg_costs = avg_costs.sort_values(by='GemiddeldeKosten')


    fig, ax = plt.subplots(figsize=(16, 6))

    sns.barplot(
        data=avg_costs,
        x='Provincie',
        y='GemiddeldeKosten',
        palette='viridis',
        order=avg_costs['Provincie'],
        ax=ax
    )

    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    ax.set_title('Gemiddelde gebruikerskosten van oplaadpalen per provincie (€/kWh)')
    ax.set_xlabel('Provincie')
    ax.set_ylabel('Gemiddelde gebruikerskosten (€/kWh)')
    plt.tight_layout()
    st.pyplot(fig)

    st.write(""" De staafdiagram geeft de gemiddelde gebruikerskosten van een laadpaal in euro per kilowattuur per provincie
             weer. Uit de figuur kan men concluderen dat in de provincie Zuid-Holland gemiddeld de laagste gebruikerskosten 
             voor een laadpaal heeft en in Limburg deze gemiddeld het hoogst zijn.""")
    st.markdown("---")
