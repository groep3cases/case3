
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px


st.set_page_config(page_title="Laaddata Dashboard", layout="wide")

st.title("🔌 Analyse van Laaddata")
st.markdown("""
Dit dashboard geeft inzicht in het laadgedrag van elektrische voertuigen.  
Je kunt interactief verkennen **hoe lang er geladen wordt**, **hoeveel energie er geleverd wordt**,  
en **hoe efficiënt het laden verloopt per fase en per periode in het jaar**.
""")


cd = pd.read_csv("data/Charging_data.csv")


cd["charging_duration"] = pd.to_timedelta(cd["charging_duration"]).dt.total_seconds() / 3600
cd["N_phases"] = cd["N_phases"].astype("Int64").astype(str)
cd["N_phases"] = pd.Categorical(cd["N_phases"], categories=[str(p) for p in [1, 2, 3]])
cd["start_time"] = pd.to_datetime(cd["start_time"], errors="coerce")
cd["exit_time"] = pd.to_datetime(cd["exit_time"], errors="coerce")


cd["total_time"] = (cd["exit_time"] - cd["start_time"]).dt.total_seconds() / 3600
cd["max_charge_gotten"] = cd["charging_duration"] * cd["max_charging_power [kW]"]
cd["efficiency"] = cd["energy_delivered [kWh]"] / cd["max_charge_gotten"]
cd["efficiency_percent"] = cd["efficiency"] * 100
cd["wasted_energy"] = cd["max_charge_gotten"] - cd["energy_delivered [kWh]"]
cd["hour_exit_time"] = cd["exit_time"].dt.hour
cd["month_exit_time"] = cd["exit_time"].dt.month_name()


phase_colors = {"1": "#ff7f0e", "2": "#d62728", "3": "#9467bd"}
min_duration, max_duration = float(cd["charging_duration"].min()), float(cd["charging_duration"].max())


col1, col2, col3 = st.columns(3)
col1.metric("Gem. Laadduur", f"{cd['charging_duration'].mean():.2f} uur")
col2.metric("Gem. Efficiëntie", f"{cd['efficiency_percent'].mean():.1f}%")
col3.metric("Totale Energie", f"{cd['energy_delivered [kWh]'].sum():,.0f} kWh")

st.markdown("---")


tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔋 Laadduur Distributie",
    "⚡ Energie & Fasen",
    "📈 Efficiëntie",
    "🕒 Tijdsanalyse",
    "📅 Maandverbruik"
])


with tab1:
    st.subheader("Verdeling van de Laadduur")
    st.markdown("""
    Deze grafiek laat zien **hoe lang voertuigen gemiddeld aan de laadpaal staan**.  
    Korte laadsessies kunnen wijzen op tussentijds laden, terwijl langere laadsessies duiden op volledig opladen.  
    Door het bereik te selecteren, kun je zien in welke duur het grootste deel van de laadsessies plaatsvindt.
    """)

    start, end = st.slider("Selecteer laadduur (uren):", min_value=min_duration, max_value=max_duration,
                           value=(min_duration, max_duration), step=0.25)

    filtered = cd[(cd["charging_duration"] >= start) & (cd["charging_duration"] <= end)]

    fig = px.histogram(
        filtered,
        x="charging_duration",
        nbins=50,
        marginal="box",
        title=f"Verdeling Laadduur ({start:.1f}–{end:.1f} uur)",
        color_discrete_sequence=["#00A3E0"]
    )
    fig.add_vline(x=filtered["charging_duration"].mean(), line_dash="dash", line_color="red",
                  annotation_text="Gemiddelde", annotation_position="top right")

    fig.update_layout(template="plotly_white", xaxis_title="Laadduur [uren]", yaxis_title="Frequentie")
    st.plotly_chart(fig, use_container_width=True)


with tab2:
    st.subheader("Laadduur vs Geleverde Energie per Fase")
    st.markdown("""
    In deze visualisatie zie je het **verband tussen de laaddduur en de hoeveelheid energie die geleverd wordt**.  
    De kleur geeft aan op hoeveel fasen (1, 2 of 3) er geladen is — meer fasen betekent meestal een hogere laadsnelheid.  
    De regressielijnen (trendlines) laten het gemiddelde verband per fase zien.
    """)

    unique_phases = sorted(cd["N_phases"].dropna().unique())
    selected_phases = st.multiselect("Selecteer fasen:", options=unique_phases, default=unique_phases)

    scatter_start, scatter_end = st.slider(
        "Selecteer laadduur range (uren):",
        min_value=min_duration,
        max_value=max_duration,
        value=(min_duration, max_duration),
        step=0.25
    )

    filtered2 = cd[
        (cd["N_phases"].isin(selected_phases)) &
        (cd["charging_duration"] >= scatter_start) &
        (cd["charging_duration"] <= scatter_end)
    ]

    fig = px.scatter(
        filtered2,
        x="charging_duration",
        y="energy_delivered [kWh]",
        color="N_phases",
        trendline="ols",
        color_discrete_map=phase_colors,
        hover_data={"charging_duration": ":.2f", "energy_delivered [kWh]": ":.1f"},
        title=f"Laadduur vs Geleverde Energie ({scatter_start:.1f}–{scatter_end:.1f} uur)"
    )
    fig.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color="black")))
    fig.update_layout(template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    💡 **Interpretatie:**  
    - Sessies met **3 fasen** leveren doorgaans meer energie in kortere tijd.  
    - De spreiding bij 1 fase is groter, wat aangeeft dat laadtijden daar minder efficiënt benut worden.
    """)


with tab3:
    st.subheader("Efficiëntieverdeling per Fase")
    st.markdown("""
    Efficiëntie geeft aan **hoeveel van de maximale laadcapaciteit daadwerkelijk gebruikt is**.  
    Een efficiëntie van 100% betekent dat de auto continu op vol vermogen heeft geladen.  
    In de praktijk ligt dit lager, omdat de laadsnelheid afneemt naarmate de accu voller raakt.
    """)

    eff_start, eff_end = st.slider("Selecteer efficiëntiebereik (%):", min_value=0, max_value=100,
                                   value=(0, 100), step=1)
    filtered_eff = cd[(cd["efficiency_percent"] >= eff_start) & (cd["efficiency_percent"] <= eff_end)]

    fig = px.violin(
        filtered_eff,
        y="efficiency_percent",
        x="N_phases",
        color="N_phases",
        color_discrete_map=phase_colors,
        box=True,
        points="all",
        title="Efficiëntieverdeling per Fase"
    )
    fig.update_layout(template="plotly_white", yaxis_title="Efficiëntie [%]", xaxis_title="Aantal Fasen")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    💡 **Interpretatie:**  
    - Laadsessies met **3 fasen** zijn meestal efficiënter.  
    - De spreiding bij **1 fase** laat zien dat er vaak laadverliezen optreden.
    """)

    st.subheader("Verspilde Energie vs Efficiëntie")
    st.markdown("""
    In onderstaande grafiek is te zien **hoeveel energie verspild is ten opzichte van de efficiëntie**.  
    Verspilde energie ontstaat bijvoorbeeld doordat de auto nog is aangesloten nadat de accu vol is.
    """)

    remove_outliers = st.checkbox("Verwijder uitschieters", value=False)

    filtered_eff2 = filtered_eff.copy()
    if remove_outliers:
        filtered_eff2 = filtered_eff2[filtered_eff2["wasted_energy"] < filtered_eff2["wasted_energy"].quantile(0.95)]

    fig = px.scatter(
        filtered_eff2,
        x="efficiency_percent",
        y="wasted_energy",
        color="N_phases",
        color_discrete_map=phase_colors,
        trendline="ols",
        title="Verspilde Energie vs Efficiëntie"
    )
    fig.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color="black")))
    fig.update_layout(template="plotly_white", xaxis_title="Efficiëntie [%]", yaxis_title="Verspilde Energie [kWh]")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    💡 **Interpretatie:**  
    - Hoe lager de efficiëntie, hoe meer energie er verspild wordt.  
    - Bij 3 fasen is de verspilling doorgaans lager.
    """)


with tab4:
    st.subheader("Laadmomenten per Uur en Maand")
    st.markdown("""
    Deze heatmap laat zien **op welke momenten van de dag en in welke maanden** het meest wordt geladen.  
    Donkere kleuren geven aan dat er in die periode veel laadsessies hebben plaatsgevonden.
    """)

    heatmap_data = cd.groupby(["month_exit_time", "hour_exit_time"]).size().reset_index(name="Aantal")
    fig = px.density_heatmap(
        heatmap_data,
        x="hour_exit_time",
        y="month_exit_time",
        z="Aantal",
        color_continuous_scale="Blues",
        title="Laadmomenten per Maand en Uur"
    )
    fig.update_layout(template="plotly_white", xaxis_title="Uur van de Dag", yaxis_title="Maand")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    💡 **Interpretatie:**  
    - Pieken in de avonduren wijzen op **thuisladen**.  
    - Drukkere maanden kunnen samenhangen met vakanties of seizoensgebonden ritpatronen.
    """)


with tab5:
    st.subheader("Maandelijks Energieverbruik")
    st.markdown("""
    Hieronder zie je de totale **geleverde energie** en de **verspilde energie** per maand.  
    Dit maakt het mogelijk om te zien in welke maanden het laadgedrag efficiënter of intensiever was.
    """)

    monthly_data = cd.groupby("month_exit_time")[["energy_delivered [kWh]", "wasted_energy"]].sum().reset_index()
    monthly_data = monthly_data.sort_values("month_exit_time")

    fig = px.bar(
        monthly_data,
        x="month_exit_time",
        y=["energy_delivered [kWh]", "wasted_energy"],
        barmode="stack",
        color_discrete_map={
            "energy_delivered [kWh]": "#2ca02c",
            "wasted_energy": "#d62728"
        },
        title="Maandelijkse Energieverdeling"
    )
    fig.update_layout(template="plotly_white", xaxis_title="Maand", yaxis_title="Energie [kWh]")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    💡 **Interpretatie:**  
    - Een stijgende lijn in geleverde energie kan duiden op **meer elektrisch rijden** in latere maanden.  
    - Relatief veel verspilde energie kan wijzen op **auto’s die lang aangesloten blijven na het laden**.
    """)



