import streamlit as st
import streamlit.components.v1 as components 
import pandas as pd
import geopandas as gpd

st.title('Regionale spreiding')
st.write("""Hier wordt gekeken naar waar zicht laad punten bevinden in Nederland en hoe 
         de elektrische voertuigen zijn verspreid door het land.""")
st.markdown('---')

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

