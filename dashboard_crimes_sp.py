import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from streamlit_lottie import st_lottie
from streamlit_option_menu import option_menu
from datetime import date, datetime, timedelta
import calendar
import re

# --- Configuração da página ---
st.set_page_config(
    page_title="Dashboard Analítico de Dados Criminais - SP",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Fonte e CSS customizado ---
def load_assets():
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
      html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
      :root { 
        --primary: #1E3A8A; 
        --secondary: #3B82F6;
        --accent: #EF4444;
        --bg: #F8FAFC; 
        --card-bg: #FFFFFF;
        --text: #1E293B;
        --text-light: #64748B;
        --card-radius: 12px; 
        --padding: 20px; 
      }
      body { background-color: var(--bg); color: var(--text); }
      h1, h2, h3, h4 { color: var(--primary); font-weight: 600; }
      .card { 
        background: var(--card-bg); 
        border-radius: var(--card-radius); 
        padding: var(--padding);
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
        margin-bottom: 24px; 
        border: 1px solid rgba(0,0,0,0.05);
      }
      .metric-card {
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        color: white;
        border-radius: var(--card-radius);
        padding: var(--padding);
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
      }
      .metric-value {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 5px;
      }
      .metric-label {
        font-size: 14px;
        opacity: 0.9;
        font-weight: 500;
      }
      .insight-card {
        background: #FFFBEB;
        border-left: 4px solid #F59E0B;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 16px;
      }
      .insight-title {
        font-weight: 600;
        color: #92400E;
        margin-bottom: 8px;
      }
      .grid-container { 
        display: grid; 
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 24px; 
        margin-top: 24px; 
      }
      .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        margin-bottom: 16px;
      }
      .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F1F5F9;
        border-radius: 8px;
        padding: 10px 16px;
        font-weight: 500;
      }
      .stTabs [aria-selected="true"] {
        background-color: var(--primary);
        color: white;
      }
      .small-text {
        font-size: 12px;
        color: var(--text-light);
      }
      .stDataFrame {
        border-radius: var(--card-radius);
      }
      .correlation-matrix {
        border-radius: var(--card-radius);
        overflow: hidden;
      }
      .trend-indicator-up {
        color: #10B981;
        font-weight: 500;
      }
      .trend-indicator-down {
        color: #EF4444;
        font-weight: 500;
      }
      .trend-indicator-neutral {
        color: #6B7280;
        font-weight: 500;
      }
      .section-title {
        margin-top: 32px;
        margin-bottom: 16px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(0,0,0,0.1);
      }
      .filter-section {
        background: #F1F5F9;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
      }
    </style>
    """, unsafe_allow_html=True)

# --- Animação Lottie ---
def load_lottie(url):
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

# --- Carrega e prepara os dados ---
@st.cache_data
def load_data():
    df = pd.read_csv('dados_criminais_limpos.csv')
    
    # Converte datas
    df['DATA_REGISTRO'] = pd.to_datetime(df['DATA_REGISTRO'], dayfirst=True, errors='coerce')
    df['DATA_OCORRENCIA_BO'] = pd.to_datetime(df['DATA_OCORRENCIA_BO'], errors='coerce')
    
    # Componentes temporais
    df['ANO_REGISTRO'] = df['DATA_REGISTRO'].dt.year
    df['MES_REGISTRO'] = df['DATA_REGISTRO'].dt.month
    df['ANO_OCORRENCIA'] = df['DATA_OCORRENCIA_BO'].dt.year
    df['MES_OCORRENCIA'] = df['DATA_OCORRENCIA_BO'].dt.month
    df['DIA_SEMANA'] = df['DATA_OCORRENCIA_BO'].dt.day_name()
    df['HORA_DIA'] = pd.to_datetime(df['HORA_OCORRENCIA_BO'], format='%H:%M:%S', errors='coerce').dt.hour
    df['PERIODO_DIA'] = df['HORA_DIA'].apply(categorize_period)
    
    # Cria campo para dia/noite
    df['TURNO'] = df['HORA_DIA'].apply(lambda x: 'Noturno (18h-6h)' if (x >= 18 or x < 6) else 'Diurno (6h-18h)' if pd.notna(x) else 'Desconhecido')
    
    # Cria campo para fim de semana
    df['FIM_DE_SEMANA'] = df['DIA_SEMANA'].apply(lambda x: 'Fim de Semana' if x in ['Saturday', 'Sunday'] else 'Dia de Semana' if pd.notna(x) else 'Desconhecido')
    
    # Colunas de texto
    text_columns = [
        'DESCR_SUBTIPOLOCAL', 'BAIRRO', 'LOGRADOURO', 'NUMERO_LOGRADOURO',
        'NOME_DELEGACIA_CIRCUNSCRIÇÃO', 'NOME_MUNICIPIO_CIRCUNSCRIÇÃO',
        'RUBRICA', 'DESCR_CONDUTA', 'NATUREZA_APURADA', 'MES_ANO'
    ]
    
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].fillna('Não informado').astype(str)
    
    # Categoriza tipos de crimes
    df['CATEGORIA_CRIME'] = df['NATUREZA_APURADA'].apply(categorize_crime)
    
    # Categoriza locais
    df['TIPO_LOCAL'] = df['DESCR_SUBTIPOLOCAL'].apply(categorize_location)
    
    # Calcula tempo entre ocorrência e registro
    df['DIAS_ATE_REGISTRO'] = (df['DATA_REGISTRO'] - df['DATA_OCORRENCIA_BO']).dt.days
    
    # Identifica registros com coordenadas válidas
    df['TEM_COORDENADAS'] = (~df['LATITUDE'].isna() & ~df['LONGITUDE'].isna() & 
                            (df['LATITUDE'] != 0) & (df['LONGITUDE'] != 0))
    
    # Cria campo para mês/ano formatado
    df['MES_ANO_FORMATADO'] = df['DATA_OCORRENCIA_BO'].dt.strftime('%b/%Y')
    
    # Cria campo para delegacia simplificada (remove prefixos comuns)
    df['DELEGACIA_SIMPLES'] = df['NOME_DELEGACIA_CIRCUNSCRIÇÃO'].apply(simplify_delegacia)
    
    return df

# --- Funções auxiliares ---
def categorize_period(hour):
    if pd.isna(hour):
        return "Desconhecido"
    elif 5 <= hour < 12:
        return "Manhã (5h-12h)"
    elif 12 <= hour < 18:
        return "Tarde (12h-18h)"
    elif 18 <= hour < 22:
        return "Noite (18h-22h)"
    else:
        return "Madrugada (22h-5h)"

def categorize_crime(crime):
    crime = crime.upper()
    if 'FURTO' in crime:
        return 'Crimes contra o patrimônio (Furto)'
    elif 'ROUBO' in crime:
        return 'Crimes contra o patrimônio (Roubo)'
    elif 'HOMICÍDIO' in crime or 'HOMICIDIO' in crime:
        return 'Crimes contra a vida'
    elif 'LESÃO' in crime or 'LESAO' in crime:
        return 'Crimes contra a pessoa'
    elif 'ESTUPRO' in crime or 'VULNERÁVEL' in crime or 'VULNERAVEL' in crime:
        return 'Crimes sexuais'
    elif 'DROGAS' in crime or 'ENTORPECENTE' in crime or 'TRÁFICO' in crime:
        return 'Crimes relacionados a drogas'
    else:
        return 'Outros crimes'

def categorize_location(location):
    location = location.upper()
    if 'VIA PÚBLICA' in location or 'PUBLICA' in location or 'RUA' in location:
        return 'Via pública'
    elif 'CASA' in location or 'RESIDÊNCIA' in location or 'RESIDENCIA' in location:
        return 'Residência'
    elif 'COMÉRCIO' in location or 'COMERCIO' in location or 'LOJA' in location:
        return 'Estabelecimento comercial'
    elif 'ESCOLA' in location or 'ENSINO' in location or 'EDUCAÇÃO' in location:
        return 'Instituição de ensino'
    elif 'TRANSPORTE' in location or 'ÔNIBUS' in location or 'TREM' in location:
        return 'Transporte público'
    else:
        return 'Outros locais'

def simplify_delegacia(delegacia):
    # Remove prefixos comuns como "DEL.POL." ou "01º D.P."
    simplified = re.sub(r'^(DEL\.POL\.|[0-9]+º D\.P\.) ', '', delegacia)
    return simplified

def calculate_crime_rate(df, group_col):
    """Calcula taxa de crimes por grupo (ex: por município)"""
    counts = df.groupby(group_col).size().reset_index(name='total_crimes')
    
    # Aqui normalmente usaríamos dados populacionais, mas como não temos,
    # vamos usar o total de crimes como base para comparação relativa
    total = counts['total_crimes'].sum()
    counts['crime_rate'] = (counts['total_crimes'] / total) * 1000  # Taxa por 1000 ocorrências
    
    return counts

def get_crime_trends(df, time_col='MES_ANO_FORMATADO', crime_col='NATUREZA_APURADA'):
    """Analisa tendências de crimes ao longo do tempo"""
    # Agrupa por período e tipo de crime
    trends = df.groupby([time_col, crime_col]).size().reset_index(name='count')
    
    # Pivota para ter crimes como colunas
    pivot = trends.pivot(index=time_col, columns=crime_col, values='count').fillna(0)
    
    # Calcula variação percentual
    pct_change = pivot.pct_change() * 100
    
    return pivot, pct_change

def get_top_crime_correlations(df):
    """Identifica correlações entre diferentes variáveis"""
    # Cria dummies para variáveis categóricas
    cat_vars = ['CATEGORIA_CRIME', 'TIPO_LOCAL', 'PERIODO_DIA', 'FIM_DE_SEMANA', 'TURNO']
    dummies = pd.get_dummies(df[cat_vars])
    
    # Calcula matriz de correlação
    corr_matrix = dummies.corr()
    
    # Extrai correlações mais fortes (excluindo autocorrelações)
    corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            if abs(corr_matrix.iloc[i, j]) > 0.1:  # Limiar de correlação
                corr_pairs.append({
                    'var1': corr_matrix.columns[i],
                    'var2': corr_matrix.columns[j],
                    'correlation': corr_matrix.iloc[i, j]
                })
    
    # Ordena por força da correlação (absoluta)
    corr_pairs = sorted(corr_pairs, key=lambda x: abs(x['correlation']), reverse=True)
    
    return corr_pairs[:10]  # Retorna top 10 correlações

def get_crime_hotspots(df, location_col='BAIRRO', crime_col='NATUREZA_APURADA'):
    """Identifica hotspots de crimes por localização"""
    # Agrupa por localização e tipo de crime
    hotspots = df.groupby([location_col, crime_col]).size().reset_index(name='count')
    
    # Identifica os locais com maior incidência para cada tipo de crime
    top_locations = hotspots.sort_values('count', ascending=False).groupby(crime_col).head(3)
    
    return top_locations

def get_reporting_efficiency(df):
    """Analisa eficiência no registro de ocorrências"""
    # Filtra para remover outliers e valores negativos
    valid_days = df[(df['DIAS_ATE_REGISTRO'] >= 0) & (df['DIAS_ATE_REGISTRO'] <= 365)]
    
    # Agrupa por delegacia
    efficiency = valid_days.groupby('DELEGACIA_SIMPLES')['DIAS_ATE_REGISTRO'].agg(
        ['mean', 'median', 'count']
    ).reset_index()
    
    # Renomeia colunas
    efficiency.columns = ['Delegacia', 'Média de Dias', 'Mediana de Dias', 'Total de Registros']
    
    # Ordena por mediana (mais robusta que média)
    efficiency = efficiency.sort_values('Mediana de Dias')
    
    return efficiency

def get_temporal_patterns(df):
    """Analisa padrões temporais nos crimes"""
    # Por hora do dia
    hour_pattern = df.groupby('HORA_DIA').size().reset_index(name='count')
    
    # Por dia da semana
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_pattern = df.groupby('DIA_SEMANA').size().reset_index(name='count')
    weekday_pattern['DIA_SEMANA_ORDER'] = pd.Categorical(
        weekday_pattern['DIA_SEMANA'], categories=weekday_order, ordered=True
    )
    weekday_pattern = weekday_pattern.sort_values('DIA_SEMANA_ORDER')
    
    # Por mês
    month_pattern = df.groupby('MES_OCORRENCIA').size().reset_index(name='count')
    month_pattern = month_pattern.sort_values('MES_OCORRENCIA')
    
    return hour_pattern, weekday_pattern, month_pattern

def get_crime_type_distribution(df, group_col='CATEGORIA_CRIME'):
    """Analisa distribuição de tipos de crimes"""
    distribution = df.groupby(group_col).size().reset_index(name='count')
    distribution['percentage'] = (distribution['count'] / distribution['count'].sum()) * 100
    distribution = distribution.sort_values('count', ascending=False)
    
    return distribution

def get_comparative_analysis(df, group_col='NOME_MUNICIPIO_CIRCUNSCRIÇÃO'):
    """Realiza análise comparativa entre grupos (ex: municípios)"""
    # Total de crimes por grupo
    total_by_group = df.groupby(group_col).size().reset_index(name='total_crimes')
    
    # Tipos de crimes mais comuns por grupo
    top_crimes_by_group = df.groupby([group_col, 'NATUREZA_APURADA']).size().reset_index(name='count')
    top_crimes_by_group = top_crimes_by_group.sort_values(['count'], ascending=False)
    
    # Períodos mais comuns por grupo
    period_by_group = df.groupby([group_col, 'PERIODO_DIA']).size().reset_index(name='count')
    
    return total_by_group, top_crimes_by_group, period_by_group

def generate_insights(df):
    """Gera insights automáticos baseados nos dados"""
    insights = []
    
    # Insight 1: Horários de maior ocorrência
    hour_pattern, _, _ = get_temporal_patterns(df)
    if not hour_pattern.empty:
        peak_hour = hour_pattern.loc[hour_pattern['count'].idxmax(), 'HORA_DIA']
        insights.append({
            'title': 'Horário de Maior Risco',
            'description': f'O horário com maior número de ocorrências é às {int(peak_hour)}h, '
                          f'representando um ponto crítico para atenção das autoridades.'
        })
    
    # Insight 2: Relação entre tipo de crime e local
    crime_location = df.groupby(['CATEGORIA_CRIME', 'TIPO_LOCAL']).size().reset_index(name='count')
    crime_location = crime_location.sort_values('count', ascending=False)
    if not crime_location.empty:
        top_pair = crime_location.iloc[0]
        insights.append({
            'title': 'Padrão Crime-Local',
            'description': f'Há uma forte associação entre {top_pair["CATEGORIA_CRIME"]} e '
                          f'{top_pair["TIPO_LOCAL"]}, sugerindo um padrão específico de ocorrências.'
        })
    
    # Insight 3: Eficiência no registro
    efficiency = get_reporting_efficiency(df)
    if not efficiency.empty:
        best_delegacia = efficiency.iloc[0]['Delegacia']
        worst_delegacia = efficiency.iloc[-1]['Delegacia']
        insights.append({
            'title': 'Eficiência no Registro',
            'description': f'A delegacia {best_delegacia} apresenta o menor tempo médio para registro de ocorrências, '
                          f'enquanto {worst_delegacia} tem o maior tempo, indicando possíveis diferenças operacionais.'
        })
    
    # Insight 4: Tendência temporal
    recent_df = df[df['ANO_OCORRENCIA'] >= df['ANO_OCORRENCIA'].max() - 1]
    monthly_counts = recent_df.groupby('MES_ANO_FORMATADO').size().reset_index(name='count')
    if len(monthly_counts) >= 2:
        last_month = monthly_counts.iloc[-1]['count']
        prev_month = monthly_counts.iloc[-2]['count']
        pct_change = ((last_month - prev_month) / prev_month) * 100
        direction = "aumento" if pct_change > 0 else "redução"
        insights.append({
            'title': 'Tendência Recente',
            'description': f'Houve um {direction} de {abs(pct_change):.1f}% nas ocorrências entre os dois últimos '
                          f'períodos analisados, indicando uma mudança significativa no padrão criminal.'
        })
    
    # Insight 5: Concentração geográfica
    location_counts = df.groupby('BAIRRO').size().reset_index(name='count')
    location_counts = location_counts.sort_values('count', ascending=False)
    if not location_counts.empty:
        top_locations = location_counts.head(3)['BAIRRO'].tolist()
        insights.append({
            'title': 'Concentração Geográfica',
            'description': f'Os bairros {", ".join(top_locations)} concentram o maior número de ocorrências, '
                          f'sugerindo áreas prioritárias para ações preventivas.'
        })
    
    return insights

# --- Função principal ---
def main():
    # Aplica estilos e animação
    load_assets()
    lottie = load_lottie("https://assets8.lottiefiles.com/packages/lf20_j1adxtyb.json")
    if lottie:
        with st.container():
            col1, col2 = st.columns([1, 5])
            with col1:
                st_lottie(lottie, height=120)
            with col2:
                st.title("🔍 Dashboard Analítico de Dados Criminais - SP")
                st.markdown("### Análise avançada de padrões e tendências criminais")
    else:
        st.title("🔍 Dashboard Analítico de Dados Criminais - SP")
        st.markdown("### Análise avançada de padrões e tendências criminais")

    # Carrega dados
    df = load_data()

    # --- Sidebar de filtros ---
    with st.sidebar:
        menu = option_menu(
            "📋 Navegação",
            ["📊 Visão Geral", "🔎 Análise Aprofundada", "📈 Tendências", "🗺️ Análise Geográfica", "⚖️ Análise Comparativa"],
            icons=["graph-up", "search", "arrow-up-right", "geo-alt", "bar-chart"],
            menu_icon="cast",
            default_index=0
        )
        
        st.header("Filtros Avançados")
        
        with st.expander("⏱️ Filtros Temporais", expanded=True):
            # Filtro de intervalo de datas
            min_date = df['DATA_OCORRENCIA_BO'].min().date()
            max_date = df['DATA_OCORRENCIA_BO'].max().date()
            
            start_date, end_date = st.date_input(
                "Período de Ocorrência",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
            
            # Filtro de período do dia
            periodos = ['Manhã (5h-12h)', 'Tarde (12h-18h)', 'Noite (18h-22h)', 'Madrugada (22h-5h)', 'Desconhecido']
            sel_periodo = st.multiselect("Período do Dia", periodos, default=[])
            
            # Filtro de dia da semana
            dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            dias_en = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dias_map = dict(zip(dias_semana, dias_en))
            sel_dias = st.multiselect("Dia da Semana", dias_semana, default=[])
            sel_dias_en = [dias_map[dia] for dia in sel_dias]
        
        with st.expander("📍 Filtros Geográficos", expanded=True):
            # Filtro de município
            municipios = sorted(df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].unique())
            sel_mun = st.multiselect("Municípios", municipios, default=[])
            
            # Filtro de bairro (dependente do município selecionado)
            if sel_mun:
                bairros = sorted(df[df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].isin(sel_mun)]['BAIRRO'].unique())
            else:
                bairros = sorted(df['BAIRRO'].unique())
            sel_bairro = st.multiselect("Bairros", bairros, default=[])
            
            # Filtro de delegacia
            delegacias = sorted(df['DELEGACIA_SIMPLES'].unique())
            sel_del = st.multiselect("Delegacias", delegacias, default=[])
            
            # Filtro de tipo de local
            tipos_local = sorted(df['TIPO_LOCAL'].unique())
            sel_local = st.multiselect("Tipo de Local", tipos_local, default=[])
        
        with st.expander("🏷️ Filtros de Categorização", expanded=True):
            # Filtro de categoria de crime
            categorias = sorted(df['CATEGORIA_CRIME'].unique())
            sel_cat = st.multiselect("Categoria de Crime", categorias, default=[])
            
            # Filtro de natureza apurada (dependente da categoria)
            if sel_cat:
                naturezas = sorted(df[df['CATEGORIA_CRIME'].isin(sel_cat)]['NATUREZA_APURADA'].unique())
            else:
                naturezas = sorted(df['NATUREZA_APURADA'].unique())
            sel_nat = st.multiselect("Natureza Apurada", naturezas, default=[])
            
            # Filtro de rubrica
            rubricas = sorted(df['RUBRICA'].unique())
            sel_rub = st.multiselect("Rubricas", rubricas, default=[])
            
            # Filtro de conduta
            condutas = sorted(df['DESCR_CONDUTA'].unique())
            sel_cond = st.multiselect("Condutas", condutas, default=[])
        
        # Botão para limpar todos os filtros
        if st.button("Limpar Todos os Filtros"):
            st.experimental_rerun()
        
        st.markdown("---")
        st.markdown('<p class="small-text">Desenvolvido com técnicas avançadas de análise de dados</p>', unsafe_allow_html=True)

    # Aplicação dos filtros
    filtered_df = df.copy()
    
    # Filtros temporais
    if isinstance(start_date, date) and isinstance(end_date, date):
        filtered_df = filtered_df[
            (filtered_df['DATA_OCORRENCIA_BO'].dt.date >= start_date) &
            (filtered_df['DATA_OCORRENCIA_BO'].dt.date <= end_date)
        ]
    
    if sel_periodo:
        filtered_df = filtered_df[filtered_df['PERIODO_DIA'].isin(sel_periodo)]
    
    if sel_dias_en:
        filtered_df = filtered_df[filtered_df['DIA_SEMANA'].isin(sel_dias_en)]
    
    # Filtros geográficos
    if sel_mun:
        filtered_df = filtered_df[filtered_df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].isin(sel_mun)]
    
    if sel_bairro:
        filtered_df = filtered_df[filtered_df['BAIRRO'].isin(sel_bairro)]
    
    if sel_del:
        filtered_df = filtered_df[filtered_df['DELEGACIA_SIMPLES'].isin(sel_del)]
    
    if sel_local:
        filtered_df = filtered_df[filtered_df['TIPO_LOCAL'].isin(sel_local)]
    
    # Filtros de categorização
    if sel_cat:
        filtered_df = filtered_df[filtered_df['CATEGORIA_CRIME'].isin(sel_cat)]
    
    if sel_nat:
        filtered_df = filtered_df[filtered_df['NATUREZA_APURADA'].isin(sel_nat)]
    
    if sel_rub:
        filtered_df = filtered_df[filtered_df['RUBRICA'].isin(sel_rub)]
    
    if sel_cond:
        filtered_df = filtered_df[filtered_df['DESCR_CONDUTA'].isin(sel_cond)]

    # Verificação de dados após filtragem
    if filtered_df.empty:
        st.warning("Não há dados para os filtros selecionados. Por favor, ajuste os critérios de filtro.")
        return

    # --- Conteúdo principal baseado na navegação ---
    if menu == "📊 Visão Geral":
        show_overview(filtered_df, df)
    elif menu == "🔎 Análise Aprofundada":
        show_detailed_analysis(filtered_df)
    elif menu == "📈 Tendências":
        show_trends(filtered_df)
    elif menu == "🗺️ Análise Geográfica":
        show_geographic_analysis(filtered_df)
    elif menu == "⚖️ Análise Comparativa":
        show_comparative_analysis(filtered_df)

    # Rodapé
    st.markdown("---")
    st.caption("Dashboard analítico desenvolvido com técnicas avançadas de ciência de dados | Dados de SP (2024–2025)")

# --- Funções para cada seção do dashboard ---
def show_overview(filtered_df, original_df):
    st.header("Visão Geral dos Dados Criminais")
    
    # Métricas principais com comparação ao total
    total_original = len(original_df)
    total_filtered = len(filtered_df)
    pct_of_total = (total_filtered / total_original) * 100
    
    st.markdown(f"<p>Mostrando <b>{total_filtered:,}</b> ocorrências ({pct_of_total:.1f}% do total)</p>", unsafe_allow_html=True)
    
    # Métricas em cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_filtered:,}</div>
            <div class="metric-label">Total de Ocorrências</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        crime_count = filtered_df['NATUREZA_APURADA'].nunique()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{crime_count}</div>
            <div class="metric-label">Tipos de Crime</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        mun_count = filtered_df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].nunique()
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{mun_count}</div>
            <div class="metric-label">Municípios</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        # Calcular a média de dias entre ocorrência e registro
        valid_days = filtered_df[filtered_df['DIAS_ATE_REGISTRO'] >= 0]['DIAS_ATE_REGISTRO']
        avg_days = valid_days.median() if not valid_days.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_days:.1f}</div>
            <div class="metric-label">Mediana de Dias até Registro</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Insights automáticos
    st.subheader("Insights Principais")
    insights = generate_insights(filtered_df)
    
    for insight in insights:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-title">📌 {insight['title']}</div>
            <div>{insight['description']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Distribuição por categoria de crime
    st.subheader("Distribuição por Categoria de Crime")
    crime_dist = get_crime_type_distribution(filtered_df)
    
    if not crime_dist.empty:
        fig = px.pie(
            crime_dist, 
            values='count', 
            names='CATEGORIA_CRIME',
            title='Distribuição de Ocorrências por Categoria',
            color_discrete_sequence=px.colors.sequential.Blues_r,
            hole=0.4
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    # Distribuição temporal
    st.subheader("Padrões Temporais")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        hour_pattern, _, _ = get_temporal_patterns(filtered_df)
        
        if not hour_pattern.empty and hour_pattern['HORA_DIA'].notna().any():
            fig = px.line(
                hour_pattern, 
                x='HORA_DIA', 
                y='count',
                title='Distribuição por Hora do Dia',
                markers=True
            )
            fig.update_layout(
                xaxis_title="Hora do Dia",
                yaxis_title="Número de Ocorrências",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados de hora do dia insuficientes para visualização.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        _, weekday_pattern, _ = get_temporal_patterns(filtered_df)
        
        if not weekday_pattern.empty and weekday_pattern['DIA_SEMANA'].notna().any():
            # Traduzir dias da semana para português
            dias_pt = {
                'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
                'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
            }
            weekday_pattern['DIA_PT'] = weekday_pattern['DIA_SEMANA'].map(dias_pt)
            
            fig = px.bar(
                weekday_pattern, 
                x='DIA_PT', 
                y='count',
                title='Distribuição por Dia da Semana',
                color='count',
                color_continuous_scale='Blues'
            )
            fig.update_layout(
                xaxis_title="Dia da Semana",
                yaxis_title="Número de Ocorrências",
                height=350
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados de dia da semana insuficientes para visualização.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Mapa de calor: Relação entre Categoria de Crime e Tipo de Local
    st.subheader("Relação entre Categoria de Crime e Tipo de Local")
    
    # Criar tabela de contingência
    crime_location = pd.crosstab(
        filtered_df['CATEGORIA_CRIME'], 
        filtered_df['TIPO_LOCAL'],
        normalize='index'  # Normaliza por linha (categoria de crime)
    )
    
    if not crime_location.empty:
        fig = px.imshow(
            crime_location,
            labels=dict(x="Tipo de Local", y="Categoria de Crime", color="Proporção"),
            x=crime_location.columns,
            y=crime_location.index,
            color_continuous_scale='Blues',
            aspect="auto"
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("""
        <p class="small-text">
        O mapa de calor acima mostra a proporção de cada tipo de local dentro de cada categoria de crime.
        Cores mais escuras indicam maior concentração de ocorrências.
        </p>
        """, unsafe_allow_html=True)
    else:
        st.info("Dados insuficientes para gerar o mapa de calor.")
    
    # Top 10 naturezas específicas
    st.subheader("Top 10 Naturezas de Crime")
    
    natureza_counts = filtered_df['NATUREZA_APURADA'].value_counts().reset_index()
    natureza_counts.columns = ['Natureza', 'Quantidade']
    
    if not natureza_counts.empty:
        fig = px.bar(
            natureza_counts.head(10),
            x='Quantidade',
            y='Natureza',
            orientation='h',
            title='Top 10 Naturezas de Crime',
            color='Quantidade',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            yaxis={'categoryorder':'total ascending'},
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Dados insuficientes para gerar o gráfico de naturezas de crime.")

def show_detailed_analysis(filtered_df):
    st.header("Análise Aprofundada")
    
    # Tabs para diferentes análises detalhadas
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔄 Correlações", "⏱️ Eficiência", "🔍 Padrões Específicos", "📊 Estatísticas Avançadas"
    ])
    
    with tab1:
        st.subheader("Análise de Correlações")
        
        # Correlação entre variáveis categóricas
        st.markdown("### Correlações entre Fatores Criminais")
        
        corr_pairs = get_top_crime_correlations(filtered_df)
        
        if corr_pairs:
            # Criar dataframe para visualização
            corr_df = pd.DataFrame(corr_pairs)
            
            # Simplificar nomes das variáveis para melhor visualização
            corr_df['var1'] = corr_df['var1'].apply(lambda x: x.replace('CATEGORIA_CRIME_', '').replace('TIPO_LOCAL_', '').replace('PERIODO_DIA_', ''))
            corr_df['var2'] = corr_df['var2'].apply(lambda x: x.replace('CATEGORIA_CRIME_', '').replace('TIPO_LOCAL_', '').replace('PERIODO_DIA_', ''))
            
            # Formatar correlação como percentual
            corr_df['strength'] = corr_df['correlation'].apply(lambda x: f"{x:.2f}")
            
            # Criar gráfico de barras para correlações
            fig = px.bar(
                corr_df,
                x='strength',
                y=corr_df.apply(lambda row: f"{row['var1']} ↔ {row['var2']}", axis=1),
                orientation='h',
                title='Principais Correlações entre Fatores',
                color='correlation',
                color_continuous_scale='RdBu_r',
                range_color=[-1, 1]
            )
            fig.update_layout(
                yaxis_title="Pares de Fatores",
                xaxis_title="Força da Correlação",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("""
            <p class="small-text">
            O gráfico acima mostra as correlações mais significativas entre diferentes fatores.
            Valores próximos a 1 indicam forte correlação positiva, valores próximos a -1 indicam forte correlação negativa,
            e valores próximos a 0 indicam pouca ou nenhuma correlação.
            </p>
            """, unsafe_allow_html=True)
        else:
            st.info("Dados insuficientes para análise de correlações.")
        
        # Análise de padrões temporais por categoria
        st.markdown("### Padrões Temporais por Categoria de Crime")
        
        # Criar heatmap de hora do dia vs categoria de crime
        if 'HORA_DIA' in filtered_df.columns and filtered_df['HORA_DIA'].notna().any():
            # Agrupar por hora e categoria
            hour_category = pd.crosstab(
                filtered_df['HORA_DIA'], 
                filtered_df['CATEGORIA_CRIME'],
                normalize='columns'  # Normaliza por coluna (categoria)
            )
            
            if not hour_category.empty:
                fig = px.imshow(
                    hour_category,
                    labels=dict(x="Categoria de Crime", y="Hora do Dia", color="Proporção"),
                    x=hour_category.columns,
                    y=hour_category.index,
                    color_continuous_scale='Viridis',
                    aspect="auto"
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                <p class="small-text">
                O mapa de calor acima mostra a distribuição de ocorrências por hora do dia para cada categoria de crime.
                Cores mais intensas indicam maior concentração de ocorrências naquele horário para a categoria específica.
                </p>
                """, unsafe_allow_html=True)
            else:
                st.info("Dados insuficientes para gerar o mapa de calor temporal.")
        else:
            st.info("Dados de hora do dia insuficientes para análise temporal.")
    
    with tab2:
        st.subheader("Análise de Eficiência")
        
        # Eficiência no registro de ocorrências por delegacia
        st.markdown("### Tempo Médio de Registro por Delegacia")
        
        efficiency = get_reporting_efficiency(filtered_df)
        
        if not efficiency.empty and len(efficiency) > 1:
            # Filtrar para delegacias com pelo menos 10 registros
            efficiency_filtered = efficiency[efficiency['Total de Registros'] >= 10]
            
            if not efficiency_filtered.empty:
                # Ordenar por mediana
                efficiency_sorted = efficiency_filtered.sort_values('Mediana de Dias')
                
                fig = px.bar(
                    efficiency_sorted.head(15),
                    x='Mediana de Dias',
                    y='Delegacia',
                    orientation='h',
                    title='Delegacias com Menor Tempo de Registro (Mediana de Dias)',
                    color='Total de Registros',
                    color_continuous_scale='Viridis',
                    hover_data=['Média de Dias', 'Total de Registros']
                )
                fig.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Mostrar também as delegacias com maior tempo
                fig = px.bar(
                    efficiency_sorted.tail(15).sort_values('Mediana de Dias', ascending=False),
                    x='Mediana de Dias',
                    y='Delegacia',
                    orientation='h',
                    title='Delegacias com Maior Tempo de Registro (Mediana de Dias)',
                    color='Total de Registros',
                    color_continuous_scale='Viridis',
                    hover_data=['Média de Dias', 'Total de Registros']
                )
                fig.update_layout(
                    yaxis={'categoryorder':'total descending'},
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Dados insuficientes para análise de eficiência (mínimo de 10 registros por delegacia).")
        else:
            st.info("Dados insuficientes para análise de eficiência.")
        
        # Distribuição do tempo até registro
        st.markdown("### Distribuição do Tempo até Registro")
        
        valid_days = filtered_df[(filtered_df['DIAS_ATE_REGISTRO'] >= 0) & (filtered_df['DIAS_ATE_REGISTRO'] <= 30)]
        
        if not valid_days.empty:
            fig = px.histogram(
                valid_days,
                x='DIAS_ATE_REGISTRO',
                nbins=30,
                title='Distribuição do Tempo até Registro (até 30 dias)',
                color_discrete_sequence=['#1E3A8A']
            )
            fig.update_layout(
                xaxis_title="Dias até Registro",
                yaxis_title="Número de Ocorrências",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Estatísticas descritivas
            stats = valid_days['DIAS_ATE_REGISTRO'].describe()
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Média", f"{stats['mean']:.1f} dias")
            col2.metric("Mediana", f"{stats['50%']:.1f} dias")
            col3.metric("Mínimo", f"{stats['min']:.1f} dias")
            col4.metric("Máximo", f"{stats['max']:.1f} dias")
        else:
            st.info("Dados insuficientes para análise de tempo até registro.")
    
    with tab3:
        st.subheader("Padrões Específicos")
        
        # Análise de padrões específicos por tipo de crime
        st.markdown("### Padrões por Tipo de Crime")
        
        # Seletor de categoria de crime para análise detalhada
        categories = sorted(filtered_df['CATEGORIA_CRIME'].unique())
        
        if categories:
            selected_category = st.selectbox(
                "Selecione uma categoria de crime para análise detalhada:",
                categories
            )
            
            # Filtrar dados para a categoria selecionada
            category_df = filtered_df[filtered_df['CATEGORIA_CRIME'] == selected_category]
            
            if not category_df.empty:
                # Distribuição por natureza específica
                natureza_counts = category_df['NATUREZA_APURADA'].value_counts().reset_index()
                natureza_counts.columns = ['Natureza', 'Quantidade']
                
                if not natureza_counts.empty:
                    fig = px.pie(
                        natureza_counts,
                        values='Quantidade',
                        names='Natureza',
                        title=f'Distribuição de Naturezas em {selected_category}',
                        hole=0.4
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
                
                # Análise temporal para a categoria
                col1, col2 = st.columns(2)
                
                with col1:
                    # Por hora do dia
                    hour_counts = category_df.groupby('HORA_DIA').size().reset_index(name='count')
                    
                    if not hour_counts.empty and hour_counts['HORA_DIA'].notna().any():
                        fig = px.line(
                            hour_counts,
                            x='HORA_DIA',
                            y='count',
                            title=f'Distribuição por Hora do Dia - {selected_category}',
                            markers=True
                        )
                        fig.update_layout(
                            xaxis_title="Hora do Dia",
                            yaxis_title="Número de Ocorrências",
                            height=350
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Por dia da semana
                    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                    weekday_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                    weekday_map = dict(zip(weekday_order, weekday_pt))
                    
                    weekday_counts = category_df.groupby('DIA_SEMANA').size().reset_index(name='count')
                    
                    if not weekday_counts.empty and weekday_counts['DIA_SEMANA'].notna().any():
                        weekday_counts['DIA_PT'] = weekday_counts['DIA_SEMANA'].map(weekday_map)
                        
                        fig = px.bar(
                            weekday_counts,
                            x='DIA_PT',
                            y='count',
                            title=f'Distribuição por Dia da Semana - {selected_category}',
                            color='count',
                            color_continuous_scale='Blues'
                        )
                        fig.update_layout(
                            xaxis_title="Dia da Semana",
                            yaxis_title="Número de Ocorrências",
                            height=350
                        )
                        st.plotly_chart(fig, use_container_width=True)
                
                # Locais mais comuns para a categoria
                st.markdown(f"### Locais Mais Comuns para {selected_category}")
                
                local_counts = category_df.groupby(['TIPO_LOCAL', 'BAIRRO']).size().reset_index(name='count')
                local_counts = local_counts.sort_values('count', ascending=False)
                
                if not local_counts.empty:
                    # Agrupar por tipo de local
                    tipo_local_counts = category_df['TIPO_LOCAL'].value_counts().reset_index()
                    tipo_local_counts.columns = ['Tipo de Local', 'Quantidade']
                    
                    fig = px.bar(
                        tipo_local_counts.head(10),
                        x='Quantidade',
                        y='Tipo de Local',
                        orientation='h',
                        title=f'Tipos de Local Mais Comuns - {selected_category}',
                        color='Quantidade',
                        color_continuous_scale='Blues'
                    )
                    fig.update_layout(
                        yaxis={'categoryorder':'total ascending'},
                        height=400
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Mostrar tabela com os bairros mais afetados
                    st.markdown(f"### Bairros Mais Afetados - {selected_category}")
                    
                    bairro_counts = category_df['BAIRRO'].value_counts().reset_index()
                    bairro_counts.columns = ['Bairro', 'Quantidade']
                    
                    st.dataframe(
                        bairro_counts.head(15),
                        use_container_width=True,
                        hide_index=True
                    )
            else:
                st.info(f"Não há dados suficientes para a categoria {selected_category}.")
        else:
            st.info("Dados insuficientes para análise por categoria de crime.")
    
    with tab4:
        st.subheader("Estatísticas Avançadas")
        
        # Análise de sazonalidade
        st.markdown("### Análise de Sazonalidade")
        
        # Por mês
        month_counts = filtered_df.groupby('MES_OCORRENCIA').size().reset_index(name='count')
        month_counts = month_counts.sort_values('MES_OCORRENCIA')
        
        if not month_counts.empty and len(month_counts) > 1:
            # Adicionar nomes dos meses
            month_names = {
                1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
            }
            month_counts['Mês'] = month_counts['MES_OCORRENCIA'].map(month_names)
            
            fig = px.line(
                month_counts,
                x='Mês',
                y='count',
                title='Sazonalidade Mensal',
                markers=True
            )
            fig.update_layout(
                xaxis_title="Mês",
                yaxis_title="Número de Ocorrências",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes para análise de sazonalidade mensal.")
        
        # Estatísticas por turno e fim de semana
        st.markdown("### Comparativo por Turno e Dia da Semana")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Por turno
            turno_counts = filtered_df['TURNO'].value_counts().reset_index()
            turno_counts.columns = ['Turno', 'Quantidade']
            
            if not turno_counts.empty:
                fig = px.pie(
                    turno_counts,
                    values='Quantidade',
                    names='Turno',
                    title='Distribuição por Turno',
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Dados insuficientes para análise por turno.")
        
        with col2:
            # Por fim de semana vs dia de semana
            fds_counts = filtered_df['FIM_DE_SEMANA'].value_counts().reset_index()
            fds_counts.columns = ['Tipo de Dia', 'Quantidade']
            
            if not fds_counts.empty:
                fig = px.pie(
                    fds_counts,
                    values='Quantidade',
                    names='Tipo de Dia',
                    title='Fim de Semana vs. Dia de Semana',
                    hole=0.4
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Dados insuficientes para análise por tipo de dia.")
        
        # Análise de distribuição por período do dia e categoria
        st.markdown("### Distribuição por Período do Dia e Categoria")
        
        periodo_categoria = pd.crosstab(
            filtered_df['PERIODO_DIA'],
            filtered_df['CATEGORIA_CRIME'],
            normalize='columns'
        )
        
        if not periodo_categoria.empty:
            fig = px.imshow(
                periodo_categoria,
                labels=dict(x="Categoria de Crime", y="Período do Dia", color="Proporção"),
                x=periodo_categoria.columns,
                y=periodo_categoria.index,
                color_continuous_scale='Viridis',
                aspect="auto"
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("""
            <p class="small-text">
            O mapa de calor acima mostra a distribuição de ocorrências por período do dia para cada categoria de crime.
            Cores mais intensas indicam maior concentração de ocorrências naquele período para a categoria específica.
            </p>
            """, unsafe_allow_html=True)
        else:
            st.info("Dados insuficientes para análise por período e categoria.")

def show_trends(filtered_df):
    st.header("Análise de Tendências")
    
    # Verificar se há dados suficientes para análise temporal
    if 'DATA_OCORRENCIA_BO' not in filtered_df.columns or filtered_df['DATA_OCORRENCIA_BO'].isna().all():
        st.warning("Dados temporais insuficientes para análise de tendências.")
        return
    
    # Criar dataframe com dados mensais
    df_monthly = filtered_df.copy()
    df_monthly['MES_ANO'] = df_monthly['DATA_OCORRENCIA_BO'].dt.strftime('%Y-%m')
    
    monthly_counts = df_monthly.groupby('MES_ANO').size().reset_index(name='count')
    monthly_counts = monthly_counts.sort_values('MES_ANO')
    
    if len(monthly_counts) <= 1:
        st.warning("Dados temporais insuficientes para análise de tendências (mínimo de 2 períodos).")
        return
    
    # Tendência geral
    st.subheader("Tendência Geral de Ocorrências")
    
    fig = px.line(
        monthly_counts,
        x='MES_ANO',
        y='count',
        title='Evolução Mensal de Ocorrências',
        markers=True
    )
    
    # Adicionar linha de tendência
    x = list(range(len(monthly_counts)))
    y = monthly_counts['count'].values
    
    if len(x) > 1:
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        
        fig.add_scatter(
            x=monthly_counts['MES_ANO'],
            y=p(x),
            mode='lines',
            name='Tendência',
            line=dict(color='red', dash='dash')
        )
    
    fig.update_layout(
        xaxis_title="Mês/Ano",
        yaxis_title="Número de Ocorrências",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Calcular taxa de crescimento
    if len(monthly_counts) >= 2:
        first_count = monthly_counts.iloc[0]['count']
        last_count = monthly_counts.iloc[-1]['count']
        
        if first_count > 0:
            growth_rate = ((last_count - first_count) / first_count) * 100
            growth_direction = "aumento" if growth_rate > 0 else "redução"
            
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-title">📈 Tendência Geral</div>
                <div>Houve um {growth_direction} de {abs(growth_rate):.1f}% nas ocorrências entre o primeiro e o último período analisado.</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Tendências por categoria de crime
    st.subheader("Tendências por Categoria de Crime")
    
    # Agrupar por mês e categoria
    category_monthly = df_monthly.groupby(['MES_ANO', 'CATEGORIA_CRIME']).size().reset_index(name='count')
    
    # Obter categorias com mais ocorrências
    top_categories = filtered_df['CATEGORIA_CRIME'].value_counts().head(5).index.tolist()
    
    if top_categories:
        # Filtrar para as principais categorias
        category_monthly_filtered = category_monthly[category_monthly['CATEGORIA_CRIME'].isin(top_categories)]
        
        if not category_monthly_filtered.empty:
            fig = px.line(
                category_monthly_filtered,
                x='MES_ANO',
                y='count',
                color='CATEGORIA_CRIME',
                title='Evolução Mensal por Categoria de Crime',
                markers=True
            )
            fig.update_layout(
                xaxis_title="Mês/Ano",
                yaxis_title="Número de Ocorrências",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados insuficientes para análise de tendências por categoria.")
    else:
        st.info("Dados insuficientes para análise de tendências por categoria.")
    
    # Análise de variação percentual
    st.subheader("Variação Percentual Mensal")
    
    if len(monthly_counts) > 1:
        # Calcular variação percentual
        monthly_counts['pct_change'] = monthly_counts['count'].pct_change() * 100
        
        # Remover primeiro registro (NaN)
        monthly_pct = monthly_counts.dropna()
        
        if not monthly_pct.empty:
            fig = px.bar(
                monthly_pct,
                x='MES_ANO',
                y='pct_change',
                title='Variação Percentual Mensal',
                color='pct_change',
                color_continuous_scale='RdBu_r',
                range_color=[-50, 50]
            )
            fig.update_layout(
                xaxis_title="Mês/Ano",
                yaxis_title="Variação Percentual (%)",
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Identificar meses com maior variação
            max_increase = monthly_pct.loc[monthly_pct['pct_change'].idxmax()]
            max_decrease = monthly_pct.loc[monthly_pct['pct_change'].idxmin()]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">📈 Maior Aumento</div>
                    <div>O maior aumento ocorreu em {max_increase['MES_ANO']}, com variação de +{max_increase['pct_change']:.1f}%.</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class="insight-card">
                    <div class="insight-title">📉 Maior Redução</div>
                    <div>A maior redução ocorreu em {max_decrease['MES_ANO']}, com variação de {max_decrease['pct_change']:.1f}%.</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Dados insuficientes para análise de variação percentual.")
    else:
        st.info("Dados insuficientes para análise de variação percentual.")
    
    # Análise de sazonalidade por dia da semana
    st.subheader("Padrões Semanais ao Longo do Tempo")
    
    # Agrupar por mês e dia da semana
    weekday_monthly = df_monthly.groupby(['MES_ANO', 'DIA_SEMANA']).size().reset_index(name='count')
    
    if not weekday_monthly.empty and weekday_monthly['DIA_SEMANA'].notna().any():
        # Traduzir dias da semana
        dias_pt = {
            'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
            'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
        }
        weekday_monthly['DIA_PT'] = weekday_monthly['DIA_SEMANA'].map(dias_pt)
        
        # Criar heatmap
        weekday_pivot = weekday_monthly.pivot(index='DIA_PT', columns='MES_ANO', values='count')
        
        if not weekday_pivot.empty:
            # Reordenar dias da semana
            dias_ordem = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            weekday_pivot = weekday_pivot.reindex(dias_ordem)
            
            fig = px.imshow(
                weekday_pivot,
                labels=dict(x="Mês/Ano", y="Dia da Semana", color="Ocorrências"),
                x=weekday_pivot.columns,
                y=weekday_pivot.index,
                color_continuous_scale='Viridis',
                aspect="auto"
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("""
            <p class="small-text">
            O mapa de calor acima mostra a distribuição de ocorrências por dia da semana ao longo dos meses.
            Cores mais intensas indicam maior concentração de ocorrências.
            </p>
            """, unsafe_allow_html=True)
        else:
            st.info("Dados insuficientes para análise de padrões semanais.")
    else:
        st.info("Dados insuficientes para análise de padrões semanais.")

def show_geographic_analysis(filtered_df):
    st.header("Análise Geográfica")
    
    # Análise por município
    st.subheader("Distribuição por Município")
    
    municipio_counts = filtered_df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].value_counts().reset_index()
    municipio_counts.columns = ['Município', 'Quantidade']
    
    if not municipio_counts.empty:
        fig = px.bar(
            municipio_counts.head(15),
            x='Quantidade',
            y='Município',
            orientation='h',
            title='Top 15 Municípios com Mais Ocorrências',
            color='Quantidade',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            yaxis={'categoryorder':'total ascending'},
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Dados insuficientes para análise por município.")
    
    # Análise por bairro
    st.subheader("Hotspots por Bairro")
    
    # Permitir seleção de município para análise de bairros
    municipios = sorted(filtered_df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].unique())
    
    if municipios:
        selected_municipio = st.selectbox(
            "Selecione um município para análise detalhada de bairros:",
            municipios
        )
        
        # Filtrar para o município selecionado
        municipio_df = filtered_df[filtered_df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'] == selected_municipio]
        
        if not municipio_df.empty:
            # Análise por bairro
            bairro_counts = municipio_df['BAIRRO'].value_counts().reset_index()
            bairro_counts.columns = ['Bairro', 'Quantidade']
            
            if not bairro_counts.empty:
                fig = px.bar(
                    bairro_counts.head(15),
                    x='Quantidade',
                    y='Bairro',
                    orientation='h',
                    title=f'Top 15 Bairros com Mais Ocorrências em {selected_municipio}',
                    color='Quantidade',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(
                    yaxis={'categoryorder':'total ascending'},
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Análise de tipos de crime por bairro
                st.markdown(f"### Tipos de Crime por Bairro em {selected_municipio}")
                
                # Selecionar os 5 bairros com mais ocorrências
                top_bairros = bairro_counts['Bairro'].head(5).tolist()
                
                if top_bairros:
                    # Filtrar para os bairros selecionados
                    bairros_df = municipio_df[municipio_df['BAIRRO'].isin(top_bairros)]
                    
                    # Agrupar por bairro e categoria de crime
                    bairro_crime = bairros_df.groupby(['BAIRRO', 'CATEGORIA_CRIME']).size().reset_index(name='count')
                    
                    if not bairro_crime.empty:
                        fig = px.bar(
                            bairro_crime,
                            x='BAIRRO',
                            y='count',
                            color='CATEGORIA_CRIME',
                            title=f'Distribuição de Crimes nos Top 5 Bairros de {selected_municipio}',
                            barmode='group'
                        )
                        fig.update_layout(
                            xaxis_title="Bairro",
                            yaxis_title="Número de Ocorrências",
                            height=500
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Dados insuficientes para análise de crimes por bairro.")
                else:
                    st.info("Dados insuficientes para análise de crimes por bairro.")
            else:
                st.info(f"Dados insuficientes para análise de bairros em {selected_municipio}.")
        else:
            st.info(f"Dados insuficientes para análise de bairros em {selected_municipio}.")
    else:
        st.info("Dados insuficientes para análise por bairro.")
    
    # Análise de endereços específicos
    st.subheader("Endereços com Maior Incidência")
    
    # Agrupar por logradouro e número
    endereco_counts = filtered_df.groupby(['NOME_MUNICIPIO_CIRCUNSCRIÇÃO', 'BAIRRO', 'LOGRADOURO', 'NUMERO_LOGRADOURO']).size().reset_index(name='count')
    endereco_counts = endereco_counts.sort_values('count', ascending=False)
    
    if not endereco_counts.empty:
        # Criar coluna de endereço completo
        endereco_counts['Endereço Completo'] = endereco_counts.apply(
            lambda x: f"{x['LOGRADOURO']}, {x['NUMERO_LOGRADOURO']}, {x['BAIRRO']}, {x['NOME_MUNICIPIO_CIRCUNSCRIÇÃO']}",
            axis=1
        )
        
        # Mostrar tabela com os endereços mais frequentes
        st.dataframe(
            endereco_counts[['Endereço Completo', 'count']].head(20).rename(columns={'count': 'Ocorrências'}),
            use_container_width=True,
            hide_index=True
        )
        
        # Gráfico para os top 10 endereços
        top_enderecos = endereco_counts.head(10).copy()
        
        fig = px.bar(
            top_enderecos,
            x='count',
            y='Endereço Completo',
            orientation='h',
            title='Top 10 Endereços com Mais Ocorrências',
            color='count',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            yaxis={'categoryorder':'total ascending'},
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Análise de tipos de crime por endereço
        st.markdown("### Tipos de Crime por Endereço")
        
        # Selecionar os 5 endereços com mais ocorrências
        top_enderecos_list = endereco_counts.head(5)
        
        # Criar dataframe com endereços completos
        endereco_df = filtered_df.copy()
        endereco_df['Endereço Completo'] = endereco_df.apply(
            lambda x: f"{x['LOGRADOURO']}, {x['NUMERO_LOGRADOURO']}, {x['BAIRRO']}, {x['NOME_MUNICIPIO_CIRCUNSCRIÇÃO']}",
            axis=1
        )
        
        # Filtrar para os endereços selecionados
        top_enderecos_df = pd.DataFrame()
        
        for _, row in top_enderecos_list.iterrows():
            mask = (
                (endereco_df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'] == row['NOME_MUNICIPIO_CIRCUNSCRIÇÃO']) &
                (endereco_df['BAIRRO'] == row['BAIRRO']) &
                (endereco_df['LOGRADOURO'] == row['LOGRADOURO']) &
                (endereco_df['NUMERO_LOGRADOURO'] == row['NUMERO_LOGRADOURO'])
            )
            top_enderecos_df = pd.concat([top_enderecos_df, endereco_df[mask]])
        
        if not top_enderecos_df.empty:
            # Agrupar por endereço e categoria de crime
            endereco_crime = top_enderecos_df.groupby(['Endereço Completo', 'CATEGORIA_CRIME']).size().reset_index(name='count')
            
            if not endereco_crime.empty:
                fig = px.bar(
                    endereco_crime,
                    x='Endereço Completo',
                    y='count',
                    color='CATEGORIA_CRIME',
                    title='Distribuição de Crimes nos Top 5 Endereços',
                    barmode='stack'
                )
                fig.update_layout(
                    xaxis_title="Endereço",
                    yaxis_title="Número de Ocorrências",
                    height=500,
                    xaxis={'tickangle': 45}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Dados insuficientes para análise de crimes por endereço.")
        else:
            st.info("Dados insuficientes para análise de crimes por endereço.")
    else:
        st.info("Dados insuficientes para análise de endereços.")
    
    # Análise por delegacia
    st.subheader("Análise por Delegacia")
    
    delegacia_counts = filtered_df['DELEGACIA_SIMPLES'].value_counts().reset_index()
    delegacia_counts.columns = ['Delegacia', 'Quantidade']
    
    if not delegacia_counts.empty:
        fig = px.bar(
            delegacia_counts.head(15),
            x='Quantidade',
            y='Delegacia',
            orientation='h',
            title='Top 15 Delegacias com Mais Ocorrências',
            color='Quantidade',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            yaxis={'categoryorder':'total ascending'},
            height=600
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Análise de tipos de crime por delegacia
        st.markdown("### Tipos de Crime por Delegacia")
        
        # Selecionar as 5 delegacias com mais ocorrências
        top_delegacias = delegacia_counts['Delegacia'].head(5).tolist()
        
        if top_delegacias:
            # Filtrar para as delegacias selecionadas
            delegacias_df = filtered_df[filtered_df['DELEGACIA_SIMPLES'].isin(top_delegacias)]
            
            # Agrupar por delegacia e categoria de crime
            delegacia_crime = delegacias_df.groupby(['DELEGACIA_SIMPLES', 'CATEGORIA_CRIME']).size().reset_index(name='count')
            
            if not delegacia_crime.empty:
                fig = px.bar(
                    delegacia_crime,
                    x='DELEGACIA_SIMPLES',
                    y='count',
                    color='CATEGORIA_CRIME',
                    title='Distribuição de Crimes nas Top 5 Delegacias',
                    barmode='stack'
                )
                fig.update_layout(
                    xaxis_title="Delegacia",
                    yaxis_title="Número de Ocorrências",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Dados insuficientes para análise de crimes por delegacia.")
        else:
            st.info("Dados insuficientes para análise de crimes por delegacia.")
    else:
        st.info("Dados insuficientes para análise por delegacia.")

def show_comparative_analysis(filtered_df):
    st.header("Análise Comparativa")
    
    # Seleção de variáveis para comparação
    st.subheader("Comparação entre Variáveis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        compare_options = [
            "Categoria de Crime", "Município", "Tipo de Local", 
            "Período do Dia", "Dia da Semana", "Turno"
        ]
        
        var1 = st.selectbox(
            "Selecione a primeira variável:",
            compare_options,
            index=0
        )
    
    with col2:
        # Filtrar para não repetir a primeira variável
        var2_options = [opt for opt in compare_options if opt != var1]
        
        var2 = st.selectbox(
            "Selecione a segunda variável:",
            var2_options,
            index=0
        )
    
    # Mapear seleções para colunas do dataframe
    var_map = {
        "Categoria de Crime": "CATEGORIA_CRIME",
        "Município": "NOME_MUNICIPIO_CIRCUNSCRIÇÃO",
        "Tipo de Local": "TIPO_LOCAL",
        "Período do Dia": "PERIODO_DIA",
        "Dia da Semana": "DIA_SEMANA",
        "Turno": "TURNO"
    }
    
    var1_col = var_map[var1]
    var2_col = var_map[var2]
    
    # Criar tabela de contingência
    contingency = pd.crosstab(
        filtered_df[var1_col],
        filtered_df[var2_col]
    )
    
    if not contingency.empty:
        # Visualização como heatmap
        st.markdown(f"### Relação entre {var1} e {var2}")
        
        fig = px.imshow(
            contingency,
            labels=dict(x=var2, y=var1, color="Ocorrências"),
            x=contingency.columns,
            y=contingency.index,
            color_continuous_scale='Blues',
            aspect="auto"
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Normalizar por linha para mostrar proporções
        contingency_norm = contingency.div(contingency.sum(axis=1), axis=0)
        
        st.markdown(f"### Proporção de {var2} por {var1}")
        
        fig = px.imshow(
            contingency_norm,
            labels=dict(x=var2, y=var1, color="Proporção"),
            x=contingency_norm.columns,
            y=contingency_norm.index,
            color_continuous_scale='Viridis',
            aspect="auto"
        )
        fig.update_layout(height=600)
        st.plotly_chart(fig, use_container_width=True)
        
        # Mostrar tabela de dados
        st.markdown(f"### Tabela de Dados: {var1} vs {var2}")
        
        # Adicionar totais
        contingency_with_totals = contingency.copy()
        contingency_with_totals['Total'] = contingency_with_totals.sum(axis=1)
        contingency_with_totals.loc['Total'] = contingency_with_totals.sum()
        
        st.dataframe(
            contingency_with_totals,
            use_container_width=True
        )
    else:
        st.info(f"Dados insuficientes para análise comparativa entre {var1} e {var2}.")
    
    # Análise comparativa entre municípios
    st.subheader("Comparação entre Municípios")
    
    # Selecionar municípios para comparação
    municipios = sorted(filtered_df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].unique())
    
    if len(municipios) >= 2:
        selected_municipios = st.multiselect(
            "Selecione municípios para comparação:",
            municipios,
            default=municipios[:min(5, len(municipios))]
        )
        
        if len(selected_municipios) >= 2:
            # Filtrar para os municípios selecionados
            municipios_df = filtered_df[filtered_df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].isin(selected_municipios)]
            
            if not municipios_df.empty:
                # Comparação por categoria de crime
                st.markdown("### Distribuição de Categorias de Crime por Município")
                
                # Agrupar por município e categoria
                mun_categoria = municipios_df.groupby(['NOME_MUNICIPIO_CIRCUNSCRIÇÃO', 'CATEGORIA_CRIME']).size().reset_index(name='count')
                
                # Calcular proporções dentro de cada município
                mun_total = mun_categoria.groupby('NOME_MUNICIPIO_CIRCUNSCRIÇÃO')['count'].sum().reset_index()
                mun_total.columns = ['NOME_MUNICIPIO_CIRCUNSCRIÇÃO', 'total']
                
                mun_categoria = mun_categoria.merge(mun_total, on='NOME_MUNICIPIO_CIRCUNSCRIÇÃO')
                mun_categoria['proportion'] = mun_categoria['count'] / mun_categoria['total']
                
                fig = px.bar(
                    mun_categoria,
                    x='NOME_MUNICIPIO_CIRCUNSCRIÇÃO',
                    y='proportion',
                    color='CATEGORIA_CRIME',
                    title='Proporção de Categorias de Crime por Município',
                    barmode='stack',
                    labels={
                        'NOME_MUNICIPIO_CIRCUNSCRIÇÃO': 'Município',
                        'proportion': 'Proporção'
                    }
                )
                fig.update_layout(
                    yaxis_title="Proporção",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Comparação por período do dia
                st.markdown("### Distribuição por Período do Dia")
                
                # Agrupar por município e período
                mun_periodo = municipios_df.groupby(['NOME_MUNICIPIO_CIRCUNSCRIÇÃO', 'PERIODO_DIA']).size().reset_index(name='count')
                
                # Calcular proporções
                mun_periodo = mun_periodo.merge(mun_total, on='NOME_MUNICIPIO_CIRCUNSCRIÇÃO')
                mun_periodo['proportion'] = mun_periodo['count'] / mun_periodo['total']
                
                fig = px.bar(
                    mun_periodo,
                    x='NOME_MUNICIPIO_CIRCUNSCRIÇÃO',
                    y='proportion',
                    color='PERIODO_DIA',
                    title='Proporção de Ocorrências por Período do Dia',
                    barmode='stack',
                    labels={
                        'NOME_MUNICIPIO_CIRCUNSCRIÇÃO': 'Município',
                        'proportion': 'Proporção'
                    }
                )
                fig.update_layout(
                    yaxis_title="Proporção",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Comparação por tipo de local
                st.markdown("### Distribuição por Tipo de Local")
                
                # Agrupar por município e tipo de local
                mun_local = municipios_df.groupby(['NOME_MUNICIPIO_CIRCUNSCRIÇÃO', 'TIPO_LOCAL']).size().reset_index(name='count')
                
                # Calcular proporções
                mun_local = mun_local.merge(mun_total, on='NOME_MUNICIPIO_CIRCUNSCRIÇÃO')
                mun_local['proportion'] = mun_local['count'] / mun_local['total']
                
                fig = px.bar(
                    mun_local,
                    x='NOME_MUNICIPIO_CIRCUNSCRIÇÃO',
                    y='proportion',
                    color='TIPO_LOCAL',
                    title='Proporção de Ocorrências por Tipo de Local',
                    barmode='stack',
                    labels={
                        'NOME_MUNICIPIO_CIRCUNSCRIÇÃO': 'Município',
                        'proportion': 'Proporção'
                    }
                )
                fig.update_layout(
                    yaxis_title="Proporção",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Comparação de eficiência no registro
                st.markdown("### Comparação de Tempo até Registro")
                
                # Filtrar para remover outliers e valores negativos
                valid_days = municipios_df[(municipios_df['DIAS_ATE_REGISTRO'] >= 0) & (municipios_df['DIAS_ATE_REGISTRO'] <= 30)]
                
                if not valid_days.empty:
                    # Agrupar por município
                    mun_efficiency = valid_days.groupby('NOME_MUNICIPIO_CIRCUNSCRIÇÃO')['DIAS_ATE_REGISTRO'].agg(
                        ['mean', 'median', 'count']
                    ).reset_index()
                    
                    # Renomear colunas
                    mun_efficiency.columns = ['Município', 'Média de Dias', 'Mediana de Dias', 'Total de Registros']
                    
                    # Ordenar por mediana
                    mun_efficiency = mun_efficiency.sort_values('Mediana de Dias')
                    
                    fig = px.bar(
                        mun_efficiency,
                        x='Município',
                        y='Mediana de Dias',
                        title='Mediana de Dias até Registro por Município',
                        color='Total de Registros',
                        color_continuous_scale='Viridis'
                    )
                    fig.update_layout(
                        yaxis_title="Mediana de Dias",
                        height=500
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Dados insuficientes para análise de tempo até registro.")
            else:
                st.info("Dados insuficientes para comparação entre municípios.")
        else:
            st.info("Selecione pelo menos 2 municípios para comparação.")
    else:
        st.info("Dados insuficientes para comparação entre municípios (mínimo de 2 municípios).")
    
    # Análise comparativa entre períodos
    st.subheader("Comparação entre Períodos")
    
    # Verificar se há dados suficientes para análise temporal
    if 'DATA_OCORRENCIA_BO' not in filtered_df.columns or filtered_df['DATA_OCORRENCIA_BO'].isna().all():
        st.info("Dados temporais insuficientes para comparação entre períodos.")
        return
    
    # Criar dataframe com dados mensais
    df_monthly = filtered_df.copy()
    df_monthly['MES_ANO'] = df_monthly['DATA_OCORRENCIA_BO'].dt.strftime('%Y-%m')
    
    # Obter lista de períodos disponíveis
    periodos = sorted(df_monthly['MES_ANO'].unique())
    
    if len(periodos) >= 2:
        # Selecionar períodos para comparação
        selected_periods = st.multiselect(
            "Selecione períodos para comparação:",
            periodos,
            default=periodos[-min(2, len(periodos)):]  # Selecionar os 2 últimos períodos por padrão
        )
        
        if len(selected_periods) >= 2:
            # Filtrar para os períodos selecionados
            periodos_df = df_monthly[df_monthly['MES_ANO'].isin(selected_periods)]
            
            if not periodos_df.empty:
                # Comparação por categoria de crime
                st.markdown("### Distribuição de Categorias de Crime por Período")
                
                # Agrupar por período e categoria
                periodo_categoria = periodos_df.groupby(['MES_ANO', 'CATEGORIA_CRIME']).size().reset_index(name='count')
                
                # Calcular proporções dentro de cada período
                periodo_total = periodo_categoria.groupby('MES_ANO')['count'].sum().reset_index()
                periodo_total.columns = ['MES_ANO', 'total']
                
                periodo_categoria = periodo_categoria.merge(periodo_total, on='MES_ANO')
                periodo_categoria['proportion'] = periodo_categoria['count'] / periodo_categoria['total']
                
                fig = px.bar(
                    periodo_categoria,
                    x='MES_ANO',
                    y='proportion',
                    color='CATEGORIA_CRIME',
                    title='Proporção de Categorias de Crime por Período',
                    barmode='stack',
                    labels={
                        'MES_ANO': 'Período',
                        'proportion': 'Proporção'
                    }
                )
                fig.update_layout(
                    yaxis_title="Proporção",
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Comparação por município
                st.markdown("### Distribuição por Município")
                
                # Agrupar por período e município
                periodo_municipio = periodos_df.groupby(['MES_ANO', 'NOME_MUNICIPIO_CIRCUNSCRIÇÃO']).size().reset_index(name='count')
                
                # Calcular proporções
                periodo_municipio = periodo_municipio.merge(periodo_total, on='MES_ANO')
                periodo_municipio['proportion'] = periodo_municipio['count'] / periodo_municipio['total']
                
                # Filtrar para os top 10 municípios
                top_municipios = filtered_df['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].value_counts().head(10).index.tolist()
                periodo_municipio_filtered = periodo_municipio[periodo_municipio['NOME_MUNICIPIO_CIRCUNSCRIÇÃO'].isin(top_municipios)]
                
                if not periodo_municipio_filtered.empty:
                    fig = px.bar(
                        periodo_municipio_filtered,
                        x='MES_ANO',
                        y='proportion',
                        color='NOME_MUNICIPIO_CIRCUNSCRIÇÃO',
                        title='Proporção de Ocorrências por Município',
                        barmode='stack',
                        labels={
                            'MES_ANO': 'Período',
                            'proportion': 'Proporção',
                            'NOME_MUNICIPIO_CIRCUNSCRIÇÃO': 'Município'
                        }
                    )
                    fig.update_layout(
                        yaxis_title="Proporção",
                        height=500
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Dados insuficientes para comparação por município.")
                
                # Comparação por dia da semana
                st.markdown("### Distribuição por Dia da Semana")
                
                # Agrupar por período e dia da semana
                periodo_dia = periodos_df.groupby(['MES_ANO', 'DIA_SEMANA']).size().reset_index(name='count')
                
                # Calcular proporções
                periodo_dia = periodo_dia.merge(periodo_total, on='MES_ANO')
                periodo_dia['proportion'] = periodo_dia['count'] / periodo_dia['total']
                
                # Traduzir dias da semana
                dias_pt = {
                    'Monday': 'Segunda', 'Tuesday': 'Terça', 'Wednesday': 'Quarta',
                    'Thursday': 'Quinta', 'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
                }
                periodo_dia['DIA_PT'] = periodo_dia['DIA_SEMANA'].map(dias_pt)
                
                if not periodo_dia.empty and periodo_dia['DIA_SEMANA'].notna().any():
                    fig = px.bar(
                        periodo_dia,
                        x='MES_ANO',
                        y='proportion',
                        color='DIA_PT',
                        title='Proporção de Ocorrências por Dia da Semana',
                        barmode='stack',
                        labels={
                            'MES_ANO': 'Período',
                            'proportion': 'Proporção',
                            'DIA_PT': 'Dia da Semana'
                        }
                    )
                    fig.update_layout(
                        yaxis_title="Proporção",
                        height=500
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Dados insuficientes para comparação por dia da semana.")
            else:
                st.info("Dados insuficientes para comparação entre períodos.")
        else:
            st.info("Selecione pelo menos 2 períodos para comparação.")
    else:
        st.info("Dados insuficientes para comparação entre períodos (mínimo de 2 períodos).")

if __name__ == "__main__":
    main()
