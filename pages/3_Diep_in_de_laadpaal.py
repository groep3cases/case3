# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 22:54:53 2025

@author: Marti
"""

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

st.title("Analyse van laaddata")

cd = pd.read_csv("data/Charging_data.csv")
cd["charging_duration"] = pd.to_timedelta(cd["charging_duration"])
cd.sort_values("charging_duration", axis=0, inplace=True)
cd["charging_duration"] = cd["charging_duration"].dt.total_seconds() / 3600
cd["N_phases"] = cd["N_phases"].astype("Int64").astype(str)
cd["N_phases"] = pd.Categorical(cd["N_phases"], categories=[str(p) for p in [1, 2, 3]])

min_duration = float(cd["charging_duration"].min())
max_duration = float(cd["charging_duration"].max())

phase_colors = {
    1: "#ff7f0e",
    2: "#d62728",
    3: "#1f77b4"
}

st.write("Er zijn diverse onderdelen waarnaar gekeken kan worden, zoals wanneer er geladen wordt, hoe veel er geladen wordt en wat de verschillende niveau's zijn voor laden. Al deze dingen beginnen echter met een simpele vraag: Hoe lang wordt er geladen? Dit is belangrijk om te weten en te verklaren wat de rest van de data ons zegt.")

st.write("In de plot hieronder is een distributie weergegeven hoe lang er aan een laadpaal geladen is. Door deze distributie te analyseren, is te achterhalen hoe goed mensen in het algemeen laden en hoeveel energie ze verbruiken.")

start, end = st.slider(
    "Select charging duration range (hours):",
    min_value=min_duration,
    max_value=max_duration,
    value=(min_duration, max_duration),
    step=0.25
)
filtered = cd[(cd["charging_duration"] >= start) & (cd["charging_duration"] <= end)]

fig = px.histogram(
    filtered,
    x="charging_duration",
    nbins=50,
    title=f"Charging Duration Histogram ({start:.1f} - {end:.1f} hours)",
    labels={"charging_duration": "Charging Duration [hours]"},
)

fig.update_layout(
    bargap=0.05,
    xaxis=dict(title="Charging Duration [hours]"),
    yaxis=dict(title="Frequency"),
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)


st.write("In de plot hieronder is gekeken naar de hoeveelheid gebruikte energie over de tijd die een auto aan de lader heeft gezeten. Hierbij is ook onderscheid gemaakt tussen het aantal fases waarop geladen wordt. Het aantal fases is een mate voor hoeveel stroom er door de kabels kan, door er meer stroomkabels aan toe te voegen.")

st.write("In de plot is duidelijk te zien dat er een verband is tussen het aantal fases en de stroom die geleverd kan worden over de tijd. Echter is ook te zien dat er meerdere lineaire lijnen aanwezig zijn in 1 fase (in de volgende plot wordt dit meer besproken).")

unique_phases = sorted(cd["N_phases"].dropna().unique())

selected_phases = []
cols = st.columns(len(unique_phases))
for i, phase in enumerate(unique_phases):
    if cols[i].checkbox(f"{int(phase)} phases", value=True):
        selected_phases.append(phase)

st.markdown("### Select range for charging duration in scatter plot")
scatter_start, scatter_end = st.slider(
    "Adjust x-axis range [hours]:",
    min_value=min_duration,
    max_value=max_duration,
    value=(min_duration, max_duration),
    step=0.25,
    key="scatter_slider"
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
    color_discrete_map=phase_colors,
    category_orders={"N_phases": ["1","2","3"]},
    title=f"Charging Duration vs Energy Delivered ({scatter_start:.1f} - {scatter_end:.1f} hours)",
    labels={
        "charging_duration": "Charging Duration [hours]",
        "energy_delivered [kWh]": "Energy Delivered [kWh]",
        "N_phases": "Number of Phases"
    },
)
fig.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color="black")))
fig.update_layout(template="plotly_white")
st.plotly_chart(fig, use_container_width=True)


st.write("In deze scatterplot wordt (op een aparte manier) de efficiëntie berekent van de laadtijden. Dit is echter niet de focus van deze plot en de efficiëntie komt verder in deze sectie terug. Deze plot is bedoeld om te laten zien dat er verschillende niveau's zijn waarop geladen wordt. Hierdoor is te zien dat bij 3 fases er ook 3 niveau's zijn waarop geladen wordt.")

st.write("De reden waarom niet alles op dezelfde lijn zit, is omdat een auto laden dynamisch werkt. Als het kan, wordt de maximale hoeveelheid stroom geleverd, maar naarmate de accu vol raakt, zal de mate van laden steeds verder af nemen. Er is ook voor gekozen om geen weergave te maken van hoe lang elk punt laadt, om overzichtelijkheid te behouden.")

unique_phases_3 = sorted(cd["N_phases"].dropna().unique())
st.markdown("**Select which N_phases to display for this plot:**")
cols3 = st.columns(len(unique_phases_3))
selected_phases_3 = []
for i, phase in enumerate(unique_phases_3):
    if cols3[i].checkbox(f"{int(phase)} phases", value=True, key=f"phase3_{i}"):
        selected_phases_3.append(phase)

filtered3 = cd[cd["N_phases"].isin(selected_phases_3)]
fig = px.scatter(
    filtered3,
    x="energy_delivered [kWh]",
    y="max_charging_power [kW]",
    color="N_phases",
    color_discrete_map=phase_colors,
    category_orders={"N_phases": ["1","2","3"]},
    title="Energy Delivered vs Max Charging Power",
    labels={
        "energy_delivered [kWh]": "Energy Delivered [kWh]",
        "max_charging_power [kW]": "Max Charging Power [kW]",
        "N_phases": "Number of Phases"
    },
)
fig.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color="black")))
fig.update_layout(template="plotly_white")
st.plotly_chart(fig, use_container_width=True)



st.write("In het figuur hieronder wordt een mate van efficiëntie weergegeven met hoe vaak dit voor komt. Ook is te zien welke efficiëntie iedere fase heeft, in vergelijking met de volledige efficiëntie.")

cd["start_time"] = pd.to_datetime(cd["start_time"], errors="coerce")
cd["exit_time"] = pd.to_datetime(cd["exit_time"], errors="coerce")
cd["total_time"] = cd["exit_time"] - cd["start_time"]
cd["total_time"] = cd["total_time"].dt.total_seconds() / 3600
cd["max_charge_gotten"] = cd["charging_duration"] * cd["max_charging_power [kW]"]
cd["efficiency"] = cd["energy_delivered [kWh]"] / cd["max_charge_gotten"]
cd["efficiency_percent"] = cd["efficiency"] * 100

min_eff = 0
max_eff = 100

eff_start, eff_end = st.slider(
    "Select efficiency range (%):",
    min_value=min_eff,
    max_value=max_eff,
    value=(min_eff, max_eff),
    step=1,
)
filtered_eff = cd[
    (cd["efficiency_percent"] >= eff_start)
    & (cd["efficiency_percent"] <= eff_end)
]

fig = px.histogram(
    filtered_eff,
    x="efficiency_percent",
    color="N_phases",
    nbins=50,
    barmode="relative",
    title=f"Charging Efficiency Distribution by Phases ({eff_start:.0f}% – {eff_end:.0f}%)",
    labels={
        "efficiency_percent": "Charging Efficiency [%]",
        "N_phases": "Number of Phases",
        "count": "Percentage of Total"
    },
)
fig.update_layout(
    bargap=0.05,
    xaxis=dict(title="Efficiency [%]"),
    yaxis=dict(title="Frequency"),
    template="plotly_white",
    legend_title_text="N_phases"
)
st.plotly_chart(fig, use_container_width=True)



st.write("Hoe efficiënt iedere fase is, is ook op een andere manier te laten zien, namelijk via een scatterplot. Deze manier is minder overzichtelijk, maar laat wel een duidelijke trend zien dat de hoeveelheid energie die verspild wordt en de mate van efficiéntie sterk samen hangen.")

cd["wasted_energy"] = cd["max_charge_gotten"] - cd["energy_delivered [kWh]"]

eff_start2, eff_end2 = st.slider(
    "Select efficiency range for scatter plot (%):",
    min_value=0.0,
    max_value=100.0,
    value=(0.0, 100.0),
    step=1.0,
    key="eff_slider2"
)

remove_outliers = st.checkbox("Remove outliers (limit per N_phases)", value=False)

unique_phases_eff = sorted(cd["N_phases"].dropna().unique())
st.markdown("**Select which N_phases to display:**")
cols_eff = st.columns(len(unique_phases_eff))
selected_phases_eff = []
for i, phase in enumerate(unique_phases_eff):
    if cols_eff[i].checkbox(f"{int(phase)} phases", value=True, key=f"eff2_phase_{i}"):
        selected_phases_eff.append(phase)

filtered_eff2 = cd[
    (cd["efficiency_percent"] >= eff_start2)
    & (cd["efficiency_percent"] <= eff_end2)
    & (cd["N_phases"].isin(selected_phases_eff))
]

if remove_outliers and not filtered_eff2.empty:
    limits = {}
    for phase in filtered_eff2["N_phases"].unique():
        subset = filtered_eff2[filtered_eff2["N_phases"] == phase]
        if len(subset) >= 2:
            sorted_vals = sorted(subset["wasted_energy"], reverse=True)
            second_max = sorted_vals[1] if len(sorted_vals) > 1 else sorted_vals[0]
            limits[phase] = second_max * 1.10
        else:
            limits[phase] = subset["wasted_energy"].max()

    filtered_eff2 = filtered_eff2[
        filtered_eff2.apply(lambda r: r["wasted_energy"] <= limits.get(r["N_phases"], np.inf), axis=1)
    ]

fig = px.scatter(
    filtered_eff2,
    x="efficiency_percent",
    y="wasted_energy",
    color="N_phases",
    color_discrete_map=phase_colors,
    category_orders={"N_phases": ["1","2","3"]},
    title=f"Wasted Energy vs Efficiency ({eff_start2:.0f}% – {eff_end2:.0f}%)",
    labels={
        "efficiency_percent": "Efficiency [%]",
        "wasted_energy": "Wasted Energy [kWh]",
        "N_phases": "Number of Phases"
    },
)
fig.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color="black")))
fig.update_layout(template="plotly_white")
st.plotly_chart(fig, use_container_width=True)



st.write("Naast de efficiëntie, kan er ook nog gekeken worden naar wanneer er op een dag geladen wordt en hoe vaak dat voor komt. In de onderstaande histogram wordt de mogelijkheid gegeven om de begintijd of de eindtijd te bekijken.")

cd["month_start_time"] = cd["start_time"].dt.month_name()
cd["month_exit_time"] = cd["exit_time"].dt.month_name()
cd["hour_start_time"] = cd["start_time"].dt.hour
cd["hour_exit_time"] = cd["exit_time"].dt.hour

hist_options = ["hour_start_time", "hour_exit_time"]
hist_labels = {
    "hour_start_time": "Hour of Start Time",
    "hour_exit_time": "Hour of Exit Time"
}
selected_hist = st.selectbox("Choose histogram:", options=hist_options, format_func=lambda x: hist_labels[x])

fig = px.histogram(
    cd,
    x=selected_hist,
    nbins=23,
    title=f"{hist_labels[selected_hist]} Distribution",
    labels={selected_hist: hist_labels[selected_hist]},
)
fig.update_layout(
    xaxis=dict(title=hist_labels[selected_hist]),
    yaxis=dict(title="Frequency"),
    template="plotly_white",
    bargap=0.05
)
st.plotly_chart(fig, use_container_width=True)



st.write("Ten slotte kan er gekeken worden naar de maand en hoeveel energie er gebruikt wordt. Hieruit kan gehaald worden dat het energiegebruik toe neemt naarmate het jaar vordert. Dit kan komen doordat de mensne op vakantie gaan, doordat er preparaties gemaakt moeten worden voor een vakantie of voor een compleet andere reden die niet te achterhalen is uit deze histogram.")

cd.sort_values("exit_time", axis=0, inplace=True)
maanden = cd["month_exit_time"].unique()
sum_maanden = cd.groupby("month_exit_time")["energy_delivered [kWh]"].sum()
sum_maanden = sum_maanden.reindex(maanden)
sum_maanden_wasted = cd.groupby("month_exit_time")["wasted_energy"].sum()
sum_maanden_wasted = sum_maanden_wasted.reindex(maanden)
cd = cd.reset_index(drop=True)

plot_options = ["Delivered Energy", "Wasted Energy"]
selected_plot = st.selectbox("Select which monthly plot to display:", plot_options)
if selected_plot == "Delivered Energy":
    y_values = sum_maanden.values
    y_label = "Energy Delivered [kWh]"
else:
    y_values = sum_maanden_wasted.values
    y_label = "Wasted Energy [kWh]"

fig = px.line(
    x=maanden,
    y=y_values,
    markers=True,
    title=f"{selected_plot} per Month",
    labels={"x": "Month", "y": y_label}
)
fig.update_layout(template="plotly_white")
st.plotly_chart(fig, use_container_width=True)










