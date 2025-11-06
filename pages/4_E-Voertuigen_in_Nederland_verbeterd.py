import pandas as pd
import plotly.express as px
import streamlit as st

st.title("E-Voertuigen in Nederland")
st.write("Hier wordt gekeken naar verschillende statistieken van de elektrische personenwagens in Nederland.")
st.markdown("---")

def simple_linear_fit(x_series, y_series):
    x = pd.to_numeric(x_series, errors="coerce").dropna()
    y = pd.to_numeric(y_series, errors="coerce").dropna()
    df_fit = pd.DataFrame({"x": x, "y": y}).dropna()
    if len(df_fit) < 2:
        return None, None
    x = df_fit["x"]
    y = df_fit["y"]
    xbar = x.mean()
    ybar = y.mean()
    denom = ((x - xbar) ** 2).sum()
    if denom == 0:
        return None, None
    a = ((x - xbar) * (y - ybar)).sum() / denom
    b = ybar - a * xbar
    return a, b

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
fig.update_layout(
    xaxis_tickangle=45,
    hovermode="x unified",
    yaxis=dict(range=[0, top_merken["Aantal_voertuigen"].max() * 1.15])
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.write("""De grafieken tonen de trend van de eerste tenaamstelling van elektrische personenauto’s 
            in Nederland — het moment waarop een kenteken voor het eerst werd geregistreerd.""")

trend_df = pd.read_csv("data/aantal_elektrische_autos_per_jaar.csv")
trend_df = trend_df.sort_values("jaar")
trend_df["jaar"] = pd.to_numeric(trend_df["jaar"], errors="coerce")
trend_df["aantal"] = pd.to_numeric(trend_df["aantal"], errors="coerce")

jaar_min, jaar_max = int(trend_df["jaar"].min()), int(trend_df["jaar"].max())
jaar_range = st.slider("Selecteer het jaarbereik:", min_value=jaar_min, max_value=jaar_max, value=(max(jaar_min, 2000), jaar_max), step=1)

filtered_df = trend_df[(trend_df["jaar"] >= jaar_range[0]) & (trend_df["jaar"] <= jaar_range[1])].copy()
filtered_df["cumulatief"] = filtered_df["aantal"].cumsum()

fit_start = max(jaar_range[0], 2018)
fit_df = filtered_df[filtered_df["jaar"] >= fit_start].dropna(subset=["jaar", "aantal"]).copy()
a, b = simple_linear_fit(fit_df["jaar"], fit_df["aantal"])

forecast_horizon = 3
future_years = list(range(int(filtered_df["jaar"].max()) + 1, int(filtered_df["jaar"].max()) + 1 + forecast_horizon))

forecast_df = pd.DataFrame(columns=["jaar", "aantal_voorspeld"])
if a is not None and b is not None and len(future_years) > 0:
    forecast_df = pd.DataFrame({
        "jaar": future_years,
        "aantal_voorspeld": [a * y + b for y in future_years]
    })
    forecast_df["aantal_voorspeld"] = forecast_df["aantal_voorspeld"].clip(lower=0)

fig_bar = px.bar(
    filtered_df,
    x="jaar",
    y="aantal",
    title=f"Aantal nieuwe elektrische personenauto's per jaar ({jaar_range[0]}–{jaar_range[1]})",
    labels={"jaar": "Jaar", "aantal": "Nieuwe voertuigen per jaar"},
    template="plotly_white"
)
fig_bar.update_layout(
    hovermode="x unified",
    yaxis=dict(range=[0, max(filtered_df["aantal"].max(), (forecast_df["aantal_voorspeld"].max() if not forecast_df.empty else 0)) * 1.15])
)

filtered_df["yoy_pct"] = filtered_df["aantal"].pct_change() * 100
fig_bar.update_traces(
    customdata=filtered_df["yoy_pct"],
    hovertemplate="Jaar=%{x}<br>Aantal=%{y:,}<br>YoY=%{customdata:.1f}%<extra></extra>"
)

if not forecast_df.empty:
    fig_bar.add_scatter(
        x=forecast_df["jaar"],
        y=forecast_df["aantal_voorspeld"],
        mode="lines+markers",
        name=f"Voorspelling (+{forecast_horizon} jaar)",
        line=dict(dash="dash")
    )

st.plotly_chart(fig_bar, use_container_width=True)

fig_line = px.line(
    filtered_df,
    x="jaar",
    y="cumulatief",
    title=f"Cumulatieve groei van elektrische personenauto's ({jaar_range[0]}–{jaar_range[1]})",
    labels={"jaar": "Jaar", "cumulatief": "Totaal aantal voertuigen"},
    template="plotly_white",
    markers=True
)
fig_line.update_traces(fill="tozeroy")

ymax_cum = filtered_df["cumulatief"].max()
fig_line.update_layout(
    hovermode="x unified",
    xaxis_title="Jaar",
    yaxis_title="Totaal aantal elektrische voertuigen",
    yaxis=dict(range=[0, ymax_cum * 1.08])
)

if not forecast_df.empty:
    last_year = int(filtered_df["jaar"].max())
    last_cum = float(filtered_df.loc[filtered_df["jaar"] == last_year, "cumulatief"].values[0])
    cum_vals = []
    running = last_cum
    for v in forecast_df["aantal_voorspeld"]:
        running += float(v)
        cum_vals.append(running)
    cum_forecast_df = pd.DataFrame({"jaar": forecast_df["jaar"], "cumulatief_voorspeld": cum_vals})

    fig_line.add_scatter(
        x=cum_forecast_df["jaar"],
        y=cum_forecast_df["cumulatief_voorspeld"],
        mode="lines+markers",
        name=f"Cumulatief (voorspelling +{forecast_horizon} jaar)",
        line=dict(dash="dash")
    )

st.plotly_chart(fig_line, use_container_width=True)

st.write("De voorspelling is gebaseerd op een eenvoudige lineaire trend van de meest recente jaren binnen het geselecteerde bereik.")

st.markdown("---")

df_prijs = pd.read_csv("data/merken_catalogusprijs_jaar_2015_2025.csv")

top20 = (
    df_prijs.groupby("merk")["catalogusprijs"]
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
    xaxis_tickangle=-45,
    hovermode="x unified",
    yaxis_tickformat="€,"
)
st.plotly_chart(fig_top20, use_container_width=True)

gem_per_jaar = (
    df_prijs.groupby("jaar")["catalogusprijs"]
      .mean()
      .reset_index()
      .sort_values("jaar")
)

fig_line_prijs = px.line(
    gem_per_jaar,
    x="jaar",
    y="catalogusprijs",
    title="Gemiddelde catalogusprijs van elektrische auto's (2015 – 2025)",
    labels={"jaar": "Jaar", "catalogusprijs": "Gemiddelde catalogusprijs (€)"},
    template="plotly_white",
    markers=True
)
fig_line_prijs.update_traces(fill="tozeroy")

ymax_p = gem_per_jaar["catalogusprijs"].max()
fig_line_prijs.update_layout(
    hovermode="x unified",
    xaxis_title="Jaar",
    yaxis_title="Gemiddelde catalogusprijs (€)",
    yaxis=dict(range=[0, ymax_p * 1.08]),
    yaxis_tickformat="€,"
)
st.plotly_chart(fig_line_prijs, use_container_width=True)

st.write("Om de dataset niet te groot te maken is er alleen gekeken naar data tussen 2015 en 2025.")

