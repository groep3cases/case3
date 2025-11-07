import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.title("E-Voertuigen in Nederland")
st.write("Hier wordt gekeken naar verschillende statistieken van de elektrische personenwagens in Nederland.")
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
fig.update_layout(xaxis_tickangle=45, hovermode="x unified", yaxis=dict(range=[0, top_merken["Aantal_voertuigen"].max() * 1.15]))
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.write("De grafieken tonen de trend van de eerste tenaamstelling van elektrische personenauto’s in Nederland — het moment waarop een kenteken voor het eerst werd geregistreerd.")

trend_df = pd.read_csv("data/aantal_elektrische_autos_per_jaar.csv").sort_values("jaar")
trend_df["jaar"] = pd.to_numeric(trend_df["jaar"], errors="coerce")
trend_df["aantal"] = pd.to_numeric(trend_df["aantal"], errors="coerce")
jaar_min, jaar_max = int(trend_df["jaar"].min()), int(trend_df["jaar"].max())

jaar_range = st.slider("Selecteer het jaarbereik:", min_value=jaar_min, max_value=jaar_max, value=(max(jaar_min, 2000), jaar_max), step=1)

filtered_df = trend_df[(trend_df["jaar"] >= jaar_range[0]) & (trend_df["jaar"] <= jaar_range[1])].copy()
filtered_df["cumulatief"] = filtered_df["aantal"].cumsum()

last_n = 5
fit_df = filtered_df.dropna(subset=["jaar", "aantal"]).tail(last_n)
a, b = np.polyfit(fit_df["jaar"].values, fit_df["aantal"].values, 1)
future_years = np.arange(int(filtered_df["jaar"].max()) + 1, int(filtered_df["jaar"].max()) + 4)
future_pred = a * future_years + b
future_pred = np.clip(future_pred, 0, None)

fig_bar = go.Figure()
fig_bar.add_trace(go.Bar(x=filtered_df["jaar"], y=filtered_df["aantal"], name="Nieuwe elektrische auto's", marker_color="cornflowerblue"))
fig_bar.add_trace(go.Bar(x=future_years, y=future_pred, name="Voorspelling (+3 jaar)", marker_color="lightgray"))
ymax_bar = max(filtered_df["aantal"].max(), (future_pred.max() if len(future_pred) else 0))
xmax_bar = future_years[-1] if len(future_years) else int(filtered_df["jaar"].max())
fig_bar.update_layout(
    title="Nieuwe elektrische auto's per jaar & verwachte groei",
    xaxis_title="Jaar",
    yaxis_title="Nieuwe voertuigen per jaar",
    template="plotly_white",
    hovermode="x unified",
    yaxis=dict(range=[0, ymax_bar * 1.15]),
    xaxis=dict(range=[jaar_range[0] - 0.5, xmax_bar + 0.5])
)
st.plotly_chart(fig_bar, use_container_width=True)

future_cum = [filtered_df["cumulatief"].iloc[-1] + float(np.sum(future_pred[:i+1])) for i in range(len(future_pred))]
fig_cumu = go.Figure()
fig_cumu.add_trace(go.Bar(x=filtered_df["jaar"], y=filtered_df["cumulatief"], name="Cumulatief", marker_color="cornflowerblue"))
fig_cumu.add_trace(go.Bar(x=future_years, y=future_cum, name="Voorspelling (+3 jaar)", marker_color="lightgray"))
ymax_cum = max(filtered_df["cumulatief"].max(), (max(future_cum) if len(future_cum) else 0))
xmax_line = future_years[-1] if len(future_years) else int(filtered_df["jaar"].max())
fig_cumu.update_layout(
    title="Cumulatieve groei van elektrische auto's & verwachte ontwikkeling",
    xaxis_title="Jaar",
    yaxis_title="Totaal aantal elektrische voertuigen",
    template="plotly_white",
    hovermode="x unified",
    yaxis=dict(range=[0, ymax_cum * 1.08]),
    xaxis=dict(range=[jaar_range[0] - 0.5, xmax_line + 0.5])
)
st.plotly_chart(fig_cumu, use_container_width=True)

st.write("De voorspelling is gebaseerd op een eenvoudige lineaire trend van de meest recente jaren binnen het geselecteerde bereik.")
st.markdown("---")

df_price = pd.read_csv("data/merken_catalogusprijs_jaar_2015_2025.csv")

top20 = (
    df_price.groupby("merk")["catalogusprijs"]
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
fig_top20.update_layout(xaxis_title="Merk", yaxis_title="Gemiddelde catalogusprijs (€)", xaxis_tickangle=-45, hovermode="x unified", yaxis_tickformat="€,.0f")
st.plotly_chart(fig_top20, use_container_width=True)

gem_per_jaar = df_price.groupby("jaar")["catalogusprijs"].mean().reset_index().sort_values("jaar")
fig_line_prijs = px.line(
    gem_per_jaar,
    x="jaar",
    y="catalogusprijs",
    title="Gemiddelde catalogusprijs van elektrische auto's (2015 – 2025)",
    labels={"jaar": "Jaar", "catalogusprijs": "Gemiddelde catalogusprijs (€)"},
    template="plotly_white",
    markers=True
)
ymax_p = gem_per_jaar["catalogusprijs"].max()
fig_line_prijs.update_traces(fill="tozeroy")
fig_line_prijs.update_layout(hovermode="x unified", xaxis_title="Jaar", yaxis_title="Gemiddelde catalogusprijs (€)", yaxis=dict(range=[0, ymax_p * 1.08]), yaxis_tickformat="€,.0f")
st.plotly_chart(fig_line_prijs, use_container_width=True)

st.markdown("---")
st.write("### Marktdiversiteit: aantal merken met elektrische auto's per jaar")
df_div = pd.read_csv("data/merken_catalogusprijs_jaar_2015_2025.csv")
merk_per_jaar = df_div.groupby("jaar")["merk"].nunique().reset_index(name="Aantal_merken").sort_values("jaar")
fig_div = px.line(
    merk_per_jaar,
    x="jaar",
    y="Aantal_merken",
    title="Aantal merken met elektrische auto's per jaar",
    labels={"jaar": "Jaar", "Aantal_merken": "Aantal merken"},
    template="plotly_white",
    markers=True
)
fig_div.update_layout(hovermode="x unified", yaxis=dict(range=[0, merk_per_jaar["Aantal_merken"].max() * 1.1]))
st.plotly_chart(fig_div, use_container_width=True)

st.write("Een stijgend aantal merken duidt op een groeiende en concurrerende EV-markt, met meer keuzes voor consumenten en snellere innovatie.")
