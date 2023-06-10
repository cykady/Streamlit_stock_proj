import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd
import plotly.figure_factory as ff
import datetime

@st.cache_data
def load_data(benchmark_ticker,options, start, end):
    raw_data = yf.download(options, start=start, end=end)
    benchmark_data = yf.download(benchmark_ticker, start=start, end=end)
    return raw_data, benchmark_data

# @st.cache_resource
# def load_data_benchmark(benchmark_ticker, start, end):
#     benchmark_data = yf.download(benchmark_ticker, start=start, end=end)
#     benchmark_data(inplace=True)
#     return benchmark_data

def create_stock_allocation_table(options):
    dff = pd.DataFrame()
    for i in options:
        my_dic = {"Ticker": f"{i}", "Allocation in $": 1,}
        df_dictionary = pd.DataFrame([my_dic])
        dff = pd.concat([dff, df_dictionary], ignore_index=True)
    return dff

def calculate_investment_return(data,options,edited_df):
    _data = data.copy()
    if len(options) > 1:
        for i in options:
            _data[i]=(edited_df.loc[i][0])*_data[i]
    else:
        _data = (edited_df['Allocation in $'][0])*_data
    return _data

### Sidebar ###
with st.sidebar:
    col1, col2 = st.columns(2)
    with col1:
        end_date=st.date_input("End", datetime.date.today())
        benchmark_ticker = st.radio("Select Benchmark", ('^GSPC','^IXIC','^GDAXI','^FTSE'))
    with col2:
        start_date=st.date_input("Start", datetime.date.today()-datetime.timedelta(weeks=52))
        risk_free_ratio = st.number_input('Risk Free Ratio Return Over Year',min_value=0.0, value=0.0, step=0.1, format='%.2f')

    st.sidebar.title("Set Portfolio")

    options = st.sidebar.multiselect(
        'Stocks in Portfolio',
        ['AAPL', 'AMZN', 'INTC', 'NVDA', 'TSLA'])
    
    st.write('Portfolio Allocation')

    alloctaion_table = create_stock_allocation_table(options)
    alloctaion_table = alloctaion_table.set_index('Ticker')
    edited_df = st.experimental_data_editor(alloctaion_table)

    fig = px.pie(edited_df, values='Allocation in $', names=edited_df.index, color_discrete_sequence=px.colors.sequential.RdBu,hole=0.5)
    fig.update_layout(margin=dict(t=0, b=300, l=0, r=500))
    st.plotly_chart(fig)

### Variables ###

# Raw Data
raw_data, benchmark_raw_data = load_data(benchmark_ticker,options, start_date, end_date)

# Adjusted Close Price
df_adj_close = raw_data['Adj Close']

benchmark_raw_data = benchmark_raw_data['Adj Close']
benchmark_raw_data.name = benchmark_ticker
benchmark_raw_data.dropna(inplace=True)

# Daily Returns
df_adj_close_pct = df_adj_close.pct_change()
df_adj_close_pct.drop(index=df_adj_close_pct.index[0], axis=0, inplace=True)

df_adj_close_pct_benchmark = benchmark_raw_data.pct_change()

 # Normalized Returns
df_adj_close_pct_cumprod = (df_adj_close_pct + 1).cumprod()

df_adj_close_pct_benchmark_cumprod = (df_adj_close_pct_benchmark + 1).cumprod()

df_normalized_returns_benchmark = pd.concat([df_adj_close_pct_cumprod,df_adj_close_pct_benchmark_cumprod], axis=1)

# Portfolio Value with Allocation
invested_money_amount = edited_df['Allocation in $'].sum()

#Investment Stocks Return Table
investment_table_returns = calculate_investment_return(df_adj_close_pct_cumprod,options,edited_df)

#Investment Portfolio Value
if len(options) > 1:
    investment_table_returns_portfolio = investment_table_returns.sum(axis=1)
else:
    investment_table_returns_portfolio = investment_table_returns

# Portfolio Value
if len(options) > 1:
    df_adj_close_pct_cumprod_sum = df_adj_close_pct_cumprod.sum(axis=1)
else:
    df_adj_close_pct_cumprod_sum = df_adj_close_pct_cumprod

#Porfolio returns
portfolio_returns = (df_adj_close_pct_cumprod_sum[-1]/df_adj_close_pct_cumprod_sum[0]-1)*100
benchmark_returns = (df_adj_close_pct_benchmark_cumprod[-1]/df_adj_close_pct_benchmark_cumprod[1]-1)*100

#Portfolio pct change
portfolio_pct_change =df_adj_close_pct_cumprod_sum.pct_change()

st.write(benchmark_returns)
### Main Page ###

tab1, tab2, tab3, tab4 ,tab5= st.tabs(["Price", "Returns",'Investment','Portfolio', "Statistics"])
    
with tab1:
    close_price_fig = px.line(df_adj_close, title='Close Price')
    st.plotly_chart(close_price_fig)

with tab2:
    returns_fig = px.line(df_normalized_returns_benchmark, title='Returns')
    st.plotly_chart(returns_fig)
    col1, col2 = st.columns(2)
    with col1:
        st.table(df_normalized_returns_benchmark.iloc[-1])
    with col2:
        st.bar_chart(df_normalized_returns_benchmark.iloc[-1])

with tab3:
    investment_fig = px.line(investment_table_returns, title='Investment')
    st.plotly_chart(investment_fig)

with tab4:
    st.plotly_chart(px.line(investment_table_returns_portfolio, title='Portfolio Value'))
    col1, col2 = st.columns(2)
    with col1:
        
        sharpe_ratio = ((portfolio_pct_change.mean() - risk_free_ratio/252)/portfolio_pct_change.std())*(252**0.5)
        sharpe_ratio_benchmark = ((df_adj_close_pct_benchmark.mean() - risk_free_ratio/252)/df_adj_close_pct_benchmark.std())*(252**0.5)

        portfolio_comprehension = pd.DataFrame(
            columns=(['Benchmark','Portfolio']), 
            index=['Return %','Volatility','Sharpe Ratio'],
            data=[[round(benchmark_returns,4),round(portfolio_returns,4)],
                  [round(df_adj_close_pct_benchmark.std(),4),round(portfolio_pct_change.std(),4)],
                  [sharpe_ratio_benchmark,sharpe_ratio]])

        st.dataframe(portfolio_comprehension.style.highlight_max(axis=1))
        