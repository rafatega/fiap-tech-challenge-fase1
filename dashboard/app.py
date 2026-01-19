import os
from typing import Any, Dict
import altair as alt
import pandas as pd
import requests
import streamlit as st

API_BASE = os.getenv(
    "API_BASE", "https://fiap-tech-challenge-fase1-18ng.onrender.com").rstrip("/")

st.set_page_config(page_title="Dashboard - Books & API Metrics", layout="wide")
st.title("Dashboard - Books Dataset + API Performance")

# Helpers


@st.cache_data(ttl=30)
def fetch_json(path: str, headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    url = f"{API_BASE}{path}"
    r = requests.get(url, headers=headers or {}, timeout=20)
    r.raise_for_status()
    return r.json()


def human_ms(x: float) -> str:
    return f"{x:.2f} ms"


# Sidebar

st.sidebar.header("Config")
st.sidebar.write("Base da API:")
st.sidebar.code(API_BASE)

# DATASET (STATS)

st.subheader("Estatísticas do Dataset (Books)")

col1, col2, col3 = st.columns(3)

overview = fetch_json("/api/v1/stats/overview")

with col1:
    st.metric("Total de livros", overview.get("total_livros", 0))
with col2:
    st.metric("Preço médio (£)", overview.get("preco_medio", 0.0))
with col3:
    dist = overview.get("distribuicao_ratings", {}) or {}
    st.metric("Ratings distintos", len(dist))

st.write("### Distribuição de Ratings")
if dist:
    df_ratings = (
        pd.DataFrame(
            [{"rating": int(k), "count": int(v)} for k, v in dist.items()]
        )
        .sort_values("rating")
        .set_index("rating")
    )
    st.bar_chart(df_ratings)
else:
    st.info("Sem dados de distribuição de ratings.")

st.divider()

st.write("### Estatísticas por Categoria")
cats = fetch_json("/api/v1/stats/categories")
if cats:
    df_cats = pd.DataFrame.from_dict(cats, orient="index").reset_index().rename(
        columns={"index": "categoria"})
    df_cats["count"] = pd.to_numeric(
        df_cats["count"], errors="coerce").fillna(0).astype(int)
    df_cats = df_cats.sort_values("count", ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        st.dataframe(df_cats, use_container_width=True, hide_index=True)
    with c2:
        # Top 15 categorias por volume
        top_df = (
            df_cats[["categoria", "count"]]
            .sort_values("count", ascending=False)
            .head(15)
        )

        chart = (
            alt.Chart(top_df)
            .mark_bar()
            .encode(
                x=alt.X("categoria:N", sort=alt.SortField(
                    field="count", order="descending")),
                y=alt.Y("count:Q"),
                tooltip=["categoria:N", "count:Q"],
            )
        )

        st.write("Top categorias (quantidade)")
        st.altair_chart(chart, use_container_width=True)
else:
    st.info("Sem dados de categorias.")
