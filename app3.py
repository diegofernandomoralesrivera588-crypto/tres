import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import geopandas as gpd
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

st.set_page_config(
    page_title="Observatorio de Homicidios",
)

st.title("📊 Observatorio de Homicidios en Colombia (2024)")

# =====================
# DATOS
# =====================
data = pd.read_csv("3base.csv")
gdf = gpd.read_parquet("3base.parquet")

departamentos = sorted(data["departamento"].unique().tolist())
departamento = st.selectbox("🌍 Seleccione un departamento:", departamentos)

municipios = sorted(data[data["departamento"] == departamento]["municipio"].unique().tolist())
municipio = st.selectbox("🏘️ Seleccione un municipio:", municipios)

filtro = data[(data["departamento"] == departamento) & (data["municipio"] == municipio)]

tasa_mun = filtro["tasa_homicidios"].values[0]
tasa_dep = data[data["departamento"] == departamento]["tasa_homicidios"].mean()
tasa_nal = data["tasa_homicidios"].mean()

# =====================
# MÉTRICA PRINCIPAL
# =====================
st.metric(
    label=f"Tasa de homicidios en {municipio} (x 100.000 habitantes)",
    value=f"{tasa_mun:.2f}"
)

# =====================
# COMPARATIVO: MUNICIPIO, DEPTO, NACIONAL
# =====================
comparativo = pd.DataFrame({
    "Nivel": ["Municipio", "Departamento", "Nacional"],
    "Tasa": [tasa_mun, tasa_dep, tasa_nal]
})

fig_comp = px.line(
    comparativo,
    x="Nivel",
    y="Tasa",
    markers=True,
    title="📈 Comparación de tasas: municipio, departamento y país",
    color_discrete_sequence=["#6A1B9A"]
)
fig_comp.update_traces(text=comparativo["Tasa"], textposition="top center")
st.plotly_chart(fig_comp, use_container_width=True)

# =====================
# TOP MUNICIPIOS
# =====================
st.subheader("🏆 Ranking de municipios según homicidios en 2024")

ordenados = data.sort_values(by="homicidios", ascending=False)

top10_mas = ordenados.head(10)
top10_menos = ordenados.tail(10)

col1, col2 = st.columns(2)

with col1:
    fig_mas = px.pie(
        top10_mas,
        names="municipio",
        values="homicidios",
        title="🔴 Municipios con más homicidios",
        color_discrete_sequence=px.colors.sequential.OrRd
    )
    st.plotly_chart(fig_mas, use_container_width=True)

with col2:
    fig_menos = px.bar(
        top10_menos.sort_values("homicidios"),
        x="homicidios",
        y="municipio",
        orientation="h",
        title="🟢 Municipios con menos homicidios",
        text="homicidios",
        color_discrete_sequence=["#2E7D32"]
    )
    fig_menos.update_traces(textposition="outside")
    st.plotly_chart(fig_menos, use_container_width=True)

# =====================
# POR DEPARTAMENTO
# =====================
st.subheader("📌 Total de homicidios por departamento")

dep_data = (
    data.groupby("departamento")[["homicidios", "poblacion"]]
    .sum()
    .reset_index()
)
dep_data["tasa_homicidios"] = (dep_data["homicidios"] / dep_data["poblacion"] * 100000).round(2)

fig_dep = px.bar(
    dep_data.sort_values("tasa_homicidios", ascending=False).head(15),
    x="tasa_homicidios",
    y="departamento",
    orientation="h",
    title="📊 Departamentos con mayor tasa de homicidios (Top 15)",
    text="tasa_homicidios",
    color="tasa_homicidios",
    color_continuous_scale="Viridis"
)
fig_dep.update_traces(textposition="outside")
st.plotly_chart(fig_dep, use_container_width=True)

# =====================
# MAPA COROPLÉTICO
# =====================
st.subheader("🗺️ Distribución geográfica de homicidios en 2024")

purple_green = ["#F1EEF6", "#BDC9E1", "#74A9CF", "#0570B0", "#00441B"]
cmap_pg = LinearSegmentedColormap.from_list("PurpleGreen", purple_green)

vals = gdf["tasa_homicidios"].astype(float).to_numpy()
vmin, vmax = 0, np.nanpercentile(vals, 98)
n_trunc = int(np.sum(vals > vmax))

fig, ax = plt.subplots(1, 1, figsize=(5, 5), dpi=200)
gdf.plot(
    column="tasa_homicidios",
    ax=ax,
    cmap=cmap_pg,
    vmin=vmin,
    vmax=vmax,
    legend=True,
    edgecolor="#222",
    linewidth=0.2,
    missing_kwds={"color": "#EEEEEE", "edgecolor": "#222", "label": "Sin datos"}
)
ax.set_facecolor("white")
ax.axis("off")
cb = ax.get_figure().axes[-1]
cb.tick_params(labelsize=7)
cb.set_ylabel("Tasa por 100k hab.", fontsize=8)

if n_trunc > 0:
    ax.text(
        0.01,
        0.01,
        f"Escala truncada al p98 (↑{n_trunc})",
        transform=ax.transAxes,
        fontsize=6,
        color="gray"
    )

st.pyplot(fig)



