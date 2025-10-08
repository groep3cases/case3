import streamlit as st
from kaggleapi import download_dataset


st.title("Elektrische auto's in Nederland")

download_dataset('gillesdegoeij/case3datasets')

st.markdown("""
In deze Streamlit-app wordt inzicht gegeven in de wereld van **elektrische voertuigen in Nederland**.  
De nadruk ligt voornamelijk op **personenauto’s**. De gebruikte datasets zijn opgeslagen op **Kaggle** en worden opgehaald via een **API**.  
Naast de datasets van de **DLO** zijn er enkele aanvullende bronnen gebruikt voor een breder beeld.

---

### CBS – Gegevens per postcode (2024)
[Gegevens per postcode – CBS](https://www.cbs.nl/nl-nl/dossier/nederland-regionaal/geografische-data/gegevens-per-postcode)  
De *numerieke postcode (PC4)*-dataset van het CBS geeft inzicht in het inwoneraantal per postcodegebied in Nederland.  
Daarnaast bevat deze dataset geografische gegevens over de ligging en spreiding van postcodes.  
Deze informatie is gebruikt voor het maken van interactieve kaarten.

---

### RDW – Voertuigregistraties per postcode (2023)
[RDW voertuigregistraties](https://opendata.rdw.nl/stories/s/ivky-pcsj)  
Deze dataset toont hoeveel voertuigen van verschillende typen in Nederland geregistreerd staan per postcode.  
Omdat dit privacygevoelige informatie is, worden alleen voertuigsoorten weergegeven die **meer dan tien keer** binnen een postcode voorkomen.  
Zo is het niet mogelijk om individuele voertuigen te herleiden naar hun eigenaar.

---

### RDW – Gekentekende voertuigen en brandstofgegevens (2025)
- [Gekentekende voertuigen](https://opendata.rdw.nl/Voertuigen/Open-Data-RDW-Gekentekende_voertuigen/m9d7-ebf2/about_data)  
- [Brandstofgegevens](https://opendata.rdw.nl/Voertuigen/Open-Data-RDW-Gekentekende_voertuigen_brandstof/8ys7-d773/about_data)  

Deze twee datasets zijn gecombineerd om meer inzicht te krijgen in de eigenschappen van voertuigen,  
zoals het merk, de brandstofsoort en de datum van eerste toelating.

---

###  Open Charge Map API (2025)
[Open Charge Map](https://openchargemap.org/site)  
De Open Charge Map-API is gebruikt om informatie te verzamelen over de locaties van laadpunten in Nederland.  
Om de prestaties van de app te behouden, is een selectie van **1.000 laadpunten** gebruikt — genoeg om een representatief overzicht te tonen zonder overbodig veel data op te halen.  
Voor een volledig overzicht kan rechtstreeks worden verwezen naar de website van Open Charge Map.

---
""", unsafe_allow_html=True)



        

        
