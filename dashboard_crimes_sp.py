import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import requests
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu
from datetime import datetime

# 1) Configuração da página
st.set_page_config(
    page_title="Dashboard de Dados Criminais - SP",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2) Carrega fonte Inter e CSS customizado
def load_assets():
    st.markdown("""
    <!-- Fonte Inter -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        html, body, [class*="css"]  {
            font-family: 'Inter', sans-serif;
        }
        :root {
          --primary: #1E3A8A;
          --bg: #F5F7F9;
          --card-radius: 12px;
          --padding: 16px;
        }
        body {
          background-color: var(--bg);
        }
        .card {
          background: white;
          border-radius: var(--card-radius);
          padding: var(--padding);
          box-shadow: 0 4px 12px rgba(0,0,0,0.05);
          margin-bottom: 24px;
        }
        .grid-container {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 24px;
          margin-top: 24px;
        }
    </style>
    """, unsafe_allow_html=True)

# 3) Carrega animação Lottie
def load_lottie(url):
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return None

# 4) Carregar e preparar os dados (igual à sua função original)
@st.cache_data
def load_data():
    df = pd.read_csv('dados_criminais_limpos.csv')
    df['DATA_REGISTRO'] = pd.to_datetime(df['DATA_REGISTRO'], errors='coerce', format='%d/%m/%Y')
    df['DATA_OCORRENCIA_BO'] = pd.to_datetime(df['DATA_OCORRENCIA_BO'], errors='coerce')
    df['ANO_OCORRENCIA'] = df['DATA_OCORRENCIA_BO'].dt.year
    df['MES_OCORRENCIA'] = df['DATA_OCORRENCIA_BO'].dt.month
    df['ANO_REGISTRO'] = df['DATA_REGISTRO'].dt.year
    df['MES_REGISTRO'] = df['DATA_REGISTRO'].dt.month
    df['MES_ANO_OCORRENCIA'] = df.apply(
        lambda x: f"{int(x['MES_OCORRENCIA']):02d}/{int(x['ANO_OCORRENCIA'])}"
        if pd.notna(x['MES_OCORRENCIA']) and pd.notna(x['ANO_OCORRENCIA'])
        else "Desconhecido",
        axis=1
    )
    df['MES_ANO_REGISTRO'] = df.apply(
        lambda x: f"{int(x['MES_REGISTRO']):02d}/{int(x['ANO_REGISTRO'])}"
        if pd.notna(x['MES_REGISTRO']) and pd.notna(x['ANO_REGISTRO'])
        else "Desconhecido",
        axis=1
    )
    return df

def main():
    load_assets()

    # animação Lottie
    lottie = load_lottie("https://lottie.host/70ea53ab-9142-4979-9e92-dfcb05f587a7/w3gn6bKXHD.json")
    if lottie:
        st_lottie(lottie, height=120, key="crime")

    st.title("🚨 Dashboard de Dados Criminais - São Paulo")
    st.markdown("### Análise interativa de ocorrências criminais em municípios de SP")

    # sidebar com menu e filtros
    df = load_data()
    with st.sidebar:
        menu = option_menu(
            "📋 Navegação",
            ["Distribuição", "Temporal", "Municípios", "Rubricas", "Mapas"],
            icons=["bar-chart", "calendar", "geo-alt", "list-task", "map"],
            menu_icon="cast",
            default_index=0
        )
        st.header("Filtros")

        # Período de registro
        anos = sorted(df['ANO_REGISTRO'].dropna().astype(int).unique())
        ano_sel = st.slider("Registro (anos)", min(anos), max(anos), (min(anos), max(anos)))
        df = df[(df['ANO_REGISTRO'] >= ano_sel[0]) & (df['ANO_REGISTRO'] <= ano_sel[1])]

        # Municípios
        mun_opts = sorted(df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].dropna().unique())
        sel_muns = st.multiselect("Municípios", mun_opts, default=mun_opts[:3])
        if sel_muns:
            df = df[df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].isin(sel_muns)]

        # Tipos de crime
        crime_opts = sorted(df['NATUREZA_APURADA'].dropna().unique())
        sel_crimes = st.multiselect("Natureza Apurada", crime_opts, default=crime_opts[:5])
        if sel_crimes:
            df = df[df['NATUREZA_APURADA'].isin(sel_crimes)]

        # Rubricas e condutas
        rub_opts = sorted(df['RUBRICA'].dropna().unique())
        sel_rub = st.multiselect("Rubricas", rub_opts)
        if sel_rub:
            df = df[df['RUBRICA'].isin(sel_rub)]

        cond_opts = sorted(df['DESCR_CONDUTA'].dropna().unique())
        sel_cond = st.multiselect("Condutas", cond_opts)
        if sel_cond:
            df = df[df['DESCR_CONDUTA'].isin(sel_cond)]

        st.markdown("---")

    if df.empty:
        st.warning("Sem dados para os filtros selecionados.")
        return

    # métricas nativas
    crime_mais_comum = df['NATUREZA_APURADA'].mode().iloc[0] if not df.empty else "N/A"
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total de Ocorrências", f"{len(df):,}")
    c2.metric("Tipos de Crime", df['NATUREZA_APURADA'].nunique())
    c3.metric("Municípios", df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].nunique())
    c4.metric("Crime Mais Comum", crime_mais_comum)

    # abas
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Distribuição",
        "📅 Temporal",
        "🏙️ Municípios",
        "📑 Rubricas",
        "📍 Mapas"
    ])

    with tab1:
        st.header("Top 10 Crimes")
        top10 = df['NATUREZA_APURADA'].value_counts().head(10).reset_index()
        top10.columns = ['Crime','Qtd']
        fig1 = px.bar(top10, x='Crime', y='Qtd',
                      color='Qtd', color_continuous_scale='Blues',
                      template='plotly_white')
        fig1.update_layout(xaxis_title="", yaxis_title="Ocorrências", height=450)

        # Distribuição local + horário
        hora = pd.to_datetime(df['HORA_OCORRENCIA_BO'], errors='coerce').dt.hour.value_counts().sort_index()
        fig2 = px.line(x=hora.index, y=hora.values,
                       title="Ocorrências por Hora", markers=True)
        fig2.update_layout(xaxis_title="Hora", yaxis_title="Qtd", height=450)

        # grid container
        st.markdown('<div class="grid-container">', unsafe_allow_html=True)
        for fig in (fig1, fig2):
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        st.header("Evolução Anual de Registros")
        temp = df.groupby('ANO_REGISTRO').size().reset_index(name='Qtd')
        fig = px.line(temp, x='ANO_REGISTRO', y='Qtd',
                      title="Registros por Ano", markers=True)
        fig.update_layout(xaxis_title="Ano", yaxis_title="Ocorrências", height=450)
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.header("Ocorrências por Município")
        mun = df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].value_counts().reset_index()
        mun.columns = ['Município','Qtd']
        fig = px.bar(mun, x='Município', y='Qtd',
                     color='Qtd', color_continuous_scale='Blues', height=450)
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.header("Top Rubricas")
        rub = df['RUBRICA'].value_counts().head(15).reset_index()
        rub.columns = ['Rubrica','Qtd']
        fig = px.bar(rub, x='Rubrica', y='Qtd',
                     color='Qtd', color_continuous_scale='Blues', height=450)
        fig.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    with tab5:
        st.header("Mapa de Ocorrências")
        # certifique-se de ter colunas LATITUDE e LONGITUDE no seu CSV
        geo = df.dropna(subset=['LATITUDE','LONGITUDE'])
        if not geo.empty:
            mapa = pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=pdk.ViewState(
                    latitude=geo['LATITUDE'].mean(),
                    longitude=geo['LONGITUDE'].mean(),
                    zoom=10
                ),
                layers=[pdk.Layer(
                    "ScatterplotLayer",
                    data=geo,
                    get_position=["LONGITUDE","LATITUDE"],
                    get_radius=50,
                    get_color=[255,0,0,160],
                    pickable=True
                )]
            )
            st.pydeck_chart(mapa)
        else:
            st.info("Sem coordenadas para plotar no mapa.")

    st.markdown("---")
    st.caption("Dashboard desenvolvido para análise de dados criminais de SP (2024-2025)")

if __name__ == "__main__":
    main()
