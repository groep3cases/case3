# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 22:54:53 2025

@author: Marti
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sb
import streamlit as st

st.title("Analyse van laaddata")

cd = pd.read_csv("data/Charging_data.csv")
cd["charging_duration"] = pd.to_timedelta(cd["charging_duration"])
cd.sort_values("charging_duration", axis=0, inplace=True)
cd["charging_duration"] = cd["charging_duration"].dt.total_seconds() / 3600

plt.hist(cd["charging_duration"], bins=50)
plt.gca().xaxis.set_major_locator(ticker.MaxNLocator(nbins=25))
st.pyplot(plt.gcf()); plt.clf()

box = plt.boxplot(cd["max_charging_power [kW]"], orientation="horizontal", showmeans=True, meanline=True)
plt.legend([box["means"][0], box["medians"][0]],["Mean", "Median"])
plt.yticks([])
st.pyplot(plt.gcf()); plt.clf()

cd = cd.reset_index(drop=True)
sb.scatterplot(data = cd, x = "charging_duration", y="energy_delivered [kWh]", hue="N_phases", palette="plasma", alpha=0.6, edgecolor="k")
st.pyplot(plt.gcf()); plt.clf()

sb.lmplot(data=cd, x= "charging_duration", y= "energy_delivered [kWh]", hue="N_phases", palette="plasma", markers=["o", "s", "D"], scatter_kws={"alpha":0.6, "edgecolor":"k"}, height=4, aspect=1.2, ci=None)
st.pyplot(plt.gcf()); plt.clf()

sb.scatterplot(data=cd, x="energy_delivered [kWh]", y = "max_charging_power [kW]", hue="N_phases", palette="tab10")
st.pyplot(plt.gcf()); plt.clf()

cd["start_time"] = pd.to_datetime(cd["start_time"], errors="coerce")
cd["exit_time"] = pd.to_datetime(cd["exit_time"], errors="coerce")
cd["total_time"] = cd["exit_time"] - cd["start_time"]
cd["total_time"] = cd["total_time"].dt.total_seconds() / 3600
cd["max_charge_gotten"] = cd["charging_duration"] * cd["max_charging_power [kW]"]
cd["efficiency"] = cd["energy_delivered [kWh]"] / cd["max_charge_gotten"]

sb.scatterplot(data=cd, x= "efficiency", y="energy_delivered [kWh]", hue="N_phases", palette="tab10")
st.pyplot(plt.gcf()); plt.clf()

plt.hist(cd["efficiency"], bins=50)
st.pyplot(plt.gcf()); plt.clf()

cd["month_start_time"] = cd["start_time"].dt.month_name()
cd["month_exit_time"] = cd["exit_time"].dt.month_name()
cd["hour_start_time"] = cd["start_time"].dt.hour
cd["hour_exit_time"] = cd["exit_time"].dt.hour

plt.hist(cd["hour_start_time"], bins=20)
st.pyplot(plt.gcf()); plt.clf()

plt.hist(cd["hour_exit_time"], bins=24)
st.pyplot(plt.gcf()); plt.clf()

cd["wasted_energy"] = cd["max_charge_gotten"] - cd["energy_delivered [kWh]"]
cd.sort_values("exit_time", axis=0, inplace=True)
maanden = cd["month_exit_time"].unique()
sum_maanden = cd.groupby("month_exit_time")["energy_delivered [kWh]"].sum()
sum_maanden = sum_maanden.reindex(maanden)
cd = cd.reset_index(drop=True)
plt.plot(maanden, sum_maanden.values, marker="o")
st.pyplot(plt.gcf()); plt.clf()

sum_maanden_wasted = cd.groupby("month_exit_time")["wasted_energy"].sum()
sum_maanden_wasted = sum_maanden_wasted.reindex(maanden)
plt.plot(maanden, sum_maanden_wasted.values, marker="o")
st.pyplot(plt.gcf()); plt.clf()
