import streamlit as st
from kaggleapi import download_dataset
from kaggleapi import download_kaarten

st.title("Elektrische auto's in Nederland")

download_dataset('gillesdegoeij/case3datasets')
download_kaarten("https://github.com/groep3cases/case3/releases/download/v1/kaarten.zip")

tab1, tab2 = st.tabs(["Samenvatting","Bronnen"])
with tab1:
    st.markdown("""
    In deze Streamlit-app wordt inzicht gegeven in de wereld van **elektrische voertuigen in Nederland**.  
    De nadruk ligt voornamelijk op **personenauto’s**. De gebruikte datasets zijn opgeslagen op **Kaggle** en worden opgehaald via een **API**.  
    Naast de datasets van de **DLO** zijn er enkele aanvullende bronnen gebruikt voor een breder beeld.
    
    ---
    
    ### Belangrijkste bevindingen
    #### Voertuigen
    De drie populairste merken van elektrische personenauto's die ooit zijn aangeschaft in Nederland:
                1. Toyota 2. Kia. 3. Volvo
    Elektrische auto's zijn al heel lang een concept maar vanaf 2016 is dit aantal enorm gestegen. In de grafieken is een duidelijke stijgende lijn 
    te zien van de aanschaf van elektrische auto's. De gemiddelde prijs van deze auto's is de laatste jaren eigenlijk verbazing wekkend weinig veranderd. 
    Dit heeft waarschijnlijk te maken met dat de productie van elektrische auto's goedkoper werd maar door inflatie de kosten gelijk bleven. 
    Ook is er te zien dat merken zoals Ferrari en Aston martin ook volledig elektrische auto's maken en ook in nederland worden verkocht. Hier hangt
    wel een flink prijs kaartje aan. 
                
    #### Spreiding
    In de randstad bevindt zich het hoogste aantal elektrische voertuigen. Percentueel gezien zijn er postcodes die een hoger percentage elektrische auto's
    ten opzichte van inwoners hebben. In noord-Nederland hebben ze het wat minder met eleketrische auto's. Het is ook duidelijk te zien dat in de randstad 
    ook de meeste laadpalen staan. Heel logisch natuurlijk, meer auto's, meer palen. De gemiddelde prijs van de laden is de afgelopen jaren ook gestegen van
    0.30 euro in 2020 tot ruim het dubbele in 2025. 
                
    #### Laadpaal
    Hier is gekeken naar de data van een laadpaal op een willekeurige locatie. Mensen laden gemiddeld hun auto tussen de 2 en 4 uur lang op.
    Optimaal wil je je auto opladen in de nacht want dan is de laadpaal vaak beschikbaar. In de wintermaanden wordt de laadpaal minder vaak gebruikt
    dan later in het jaar. 
    
    ---

    #### Verbeteringen
    In dit dashboard is enkel gekeken naar elelktrische voertuigen. Voor een breder beeld is de vergelijking met benzine en diesel auto's belangrijk.
    Vragen zoals: Hoeveel nieuwe auto's zijn elektrisch? Wat is het prijsverschil tussen elektrisch en niet elektrisch? zijn nu niet behandeld. Ook de
    groei van verschillende elektrische merken/modellen is niet volledig weergegeven. Ook is in deze app gekekeken naar een enkele laadpaal voor 
    de data.
                
    
    """)

with tab2:
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



            

            
