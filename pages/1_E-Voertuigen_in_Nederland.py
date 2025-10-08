import pandas as pd
import plotly.express as px
import streamlit as st

st.title("E-Voertuigen in Nederland")
st.write("Hier wordt gekeken naar verschillende statistieken van de Elektrische personenwagens in Nederland.")
st.markdown("---")

df = pd.read_csv("data/elektrische_voertuigen_2025v2.csv")
top_merken = (
    df.groupby("merk", dropna=False)
      .size()
      .reset_index(name="Aantal_voertuigen")
      .rename(columns={"merk": "Merk"})
      .sort_values("Aantal_voertuigen", ascending=False)
      .head(10)
)
fig = px.bar(
    top_merken,
    x="Merk",
    y="Aantal_voertuigen",
    title="Top 10 merken (elektrische personenauto's 2025)",
    template="plotly_white",
    labels={"Merk": "Merk", "Aantal_voertuigen": "Aantal voertuigen"},
)
fig.update_layout(xaxis_tickangle=45)
st.plotly_chart(fig)

st.markdown("---")
st.write("""De grafieken tonen de trend van de eerste tenaamstelling van elektrische personenauto’s 
            in Nederland — het moment waarop een kenteken voor het eerst werd geregistreerd.""")

trend_df = pd.read_csv("data/aantal_elektrische_autos_per_jaar.csv")
trend_df = trend_df.sort_values("jaar")

jaar_range = st.slider(
    "Selecteer het jaarbereik:",
    min_value=1951,
    max_value=2025,
    value=(2000, 2025),
    step=1
)

filtered_df = trend_df[
    (trend_df["jaar"] >= jaar_range[0]) &
    (trend_df["jaar"] <= jaar_range[1])
].copy()

filtered_df["cumulatief"] = filtered_df["aantal"].cumsum()

fig_bar = px.bar(
    filtered_df,
    x="jaar",
    y="aantal",
    title=f"Aantal nieuwe elektrische personenauto's per jaar ({jaar_range[0]}–{jaar_range[1]})",
    labels={"jaar": "Jaar", "aantal": "Aantal voertuigen"},
    template="plotly_white"
)
fig_bar.update_layout(
    hovermode="x unified",
    xaxis_title="Jaar",
    yaxis_title="Nieuwe voertuigen per jaar"
)
st.plotly_chart(fig_bar, use_container_width=True)

fig_line = px.line(
    filtered_df,
    x="jaar",
    y="cumulatief",
    title=f"Cumulatieve groei van elektrische personenauto's ({jaar_range[0]}–{jaar_range[1]})",
    labels={"jaar": "Jaar", "cumulatief": "Totaal aantal voertuigen"},
    template="plotly_white",
    line_shape="spline",
    markers=True
)
fig_line.update_traces(fill="tozeroy")
fig_line.update_layout(
    hovermode="x unified",
    xaxis_title="Jaar",
    yaxis_title="Totaal aantal elektrische voertuigen"
)
st.plotly_chart(fig_line, use_container_width=True)

st.write("""De bovenstaande visualisatie laat zien dat er in 2025 meer dan 1,5 miljoen elektrische voertuigen in Nederland geregistreerd 
            staan. Volgens officiële bronnen, zoals het CBS en de RVO, bedraagt het daadwerkelijke aantal volledig elektrische 
            personenauto’s echter ongeveer 600.000. Dit verschil ontstaat doordat de gebruikte RDW-dataset alle voertuigen bevat die 
            ooit in Nederland geregistreerd zijn, ongeacht of ze nog actief zijn. Hierdoor worden ook voertuigen meegeteld die inmiddels 
            gesloopt, geëxporteerd of uitgeschreven zijn. De grafiek toont daardoor niet het actuele aantal elektrische auto’s op de weg, 
            maar een historisch totaal van alle voertuigen die ooit als elektrisch zijn geregistreerd.""")
st.markdown("---")


df = pd.read_csv("data/merken_catalogusprijs_jaar_2015_2025.csv")

top20 = (
    df.groupby("merk")["catalogusprijs"]
      .mean()
      .sort_values(ascending=False)
      .head(20)
      .reset_index()
)

fig_top20 = px.bar(
    top20,
    x="merk",
    y="catalogusprijs",
    title="Top 20 duurste merken (gemiddelde catalogusprijs 2015 – 2025)",
    labels={"merk": "Merk", "catalogusprijs": "Gemiddelde catalogusprijs (€)"},
    template="plotly_white"
)
fig_top20.update_layout(
    xaxis_title="Merk",
    yaxis_title="Gemiddelde catalogusprijs (€)",
    xaxis_tickangle=-45
)
st.plotly_chart(fig_top20, use_container_width=True)

gem_per_jaar = (
    df.groupby("jaar")["catalogusprijs"]
      .mean()
      .reset_index()
      .sort_values("jaar")
)

fig_line = px.line(
    gem_per_jaar,
    x="jaar",
    y="catalogusprijs",
    title="Gemiddelde catalogusprijs van elektrische auto's (2015 – 2025)",
    labels={"jaar": "Jaar", "catalogusprijs": "Gemiddelde catalogusprijs (€)"},
    template="plotly_white",
    markers=True,
    line_shape="spline"
)
fig_line.update_traces(fill="tozeroy")
fig_line.update_layout(
    hovermode="x unified",
    xaxis_title="Jaar",
    yaxis_title="Gemiddelde catalogusprijs (€)"
)
st.plotly_chart(fig_line, use_container_width=True)
st.write("""Om de dataset niet te groot te maken is er alleen gekeken naar data tussen 2015 en 2025. Dit
            is een goede tijdsperiode omdat het verkoop van elektrische personenauto's in deze jaren hard
            is gestegen.""")


