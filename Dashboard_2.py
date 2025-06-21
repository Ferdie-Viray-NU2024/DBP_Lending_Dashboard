import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import plotly.figure_factory as ff
import pandas as pd
import folium
import matplotlib
from folium.plugins import MarkerCluster
from branca.colormap import linear

import os
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="DLS Lending Dashboard", page_icon=":bar_chart:", layout="wide",initial_sidebar_state="expanded")

st.title(" :bar_chart: DLS Lending Dashboard")
st.markdown('<style>div.block-container{padding-top:2rem;}</style>', unsafe_allow_html=True)

fl = st.file_uploader(":file_folder: Upload a file", type=(["csv","xlsx","xls"]))
if fl is not None:
    filename = fl.name
    st.write(filename)
    df = pd.read_excel(filename, engine="openpyxl")
else:
    #os.chdir(r"C:\Users\ROG STRIX\PycharmProjects\PythonProject")
    #df = pd.read_excel("DATASET_PYTHON CLEANED.xlsx")
    df = pd.read_excel("DATASET_PYTHON CLEANED.xlsx", engine="openpyxl")

#df_yearend = pd.read_excel("DATASET_PYTHON CLEANED_YEAREND.xlsx")
df_yearend = pd.read_excel("DATASET_PYTHON CLEANED_YEAREND.xlsx", engine="openpyxl")

col1, col2 = st.columns((2))

df["CUTOFF_DATE"] = pd.to_datetime(df["CUTOFF_DATE"])
df_yearend["CUTOFF_DATE"] = pd.to_datetime(df["CUTOFF_DATE"])

#Getting the min and max year
start_year = pd.to_datetime(df["CUTOFF_DATE"]).min()
end_year = pd.to_datetime(df["CUTOFF_DATE"]).max()

with col1:
    date1 = pd.to_datetime(st.date_input("Start Year: ", start_year))

with col2:
    date2 = pd.to_datetime(st.date_input("End Year: ", end_year))

df = df[(df["CUTOFF_DATE"] >= date1) & (df["CUTOFF_DATE"] <= date2)].copy()
df_yearend = df_yearend[(df["CUTOFF_DATE"] >= date1) & (df_yearend["CUTOFF_DATE"] <= date2)].copy()

st.sidebar.header("Select a Filter: ")

#Create for Year
year = st.sidebar.multiselect("Select Calendar Year: ", df["YEAR"].unique())
if not year:
    year = [2024.0]
    df2 = df.copy()
    df2_ye = df_yearend.copy()
else:
    df2 = df[df["YEAR"].isin(year)]
    df2_ye = df_yearend[df_yearend["YEAR"].isin(year)]

#Create for Region
region = st.sidebar.multiselect("Select Region/Location: ", df["Region"].unique())
if not region:
    df3 = df2.copy()
    df3_ye = df2_ye.copy()
else:
    df3 = df2[df["Region"].isin(region)]
    df3_ye = df2_ye[df_yearend["Region"].isin(region)]

#Create for Lending Group
lending_group = st.sidebar.multiselect("Select Lending Group: ", df["LG"].unique())

#Filter Data based on Year, Region, Lending Group
if not year and not region and not lending_group:
    filtered_df = df
    filtered_df_cutoff = df_yearend
elif not region and not lending_group:
    filtered_df = df[df["YEAR"].isin(year)]
    filtered_df_cutoff = df_yearend[df_yearend["YEAR"].isin(year)]
elif not year and not lending_group:
    filtered_df = df[df["Region"].isin(region)]
    filtered_df_cutoff = df_yearend[df_yearend["Region"].isin(region)]
elif region and lending_group:
    filtered_df = df3[df["Region"].isin(region) & df3["LG"].isin(lending_group)]
    filtered_df_cutoff = df3_ye[df_yearend["Region"].isin(region) & df3_ye["LG"].isin(lending_group)]
elif year and lending_group:
    filtered_df = df3[df["YEAR"].isin(year) & df3["LG"].isin(lending_group)]
    filtered_df_cutoff = df3_ye[df_yearend["YEAR"].isin(year) & df3_ye["LG"].isin(lending_group)]
elif year and region:
    filtered_df = df3[df["YEAR"].isin(year) & df3["Region"].isin(region)]
    filtered_df_cutoff = df3_ye[df_yearend["YEAR"].isin(year) & df3_ye["Region"].isin(region)]
elif lending_group:
    filtered_df = df3[df3["LG"].isin(lending_group)]
    filtered_df_cutoff = df3_ye[df3_ye["LG"].isin(lending_group)]
else:
    filtered_df = df3[df3["YEAR"].isin(year) & df3["Region"].isin(region) & df3["LG"].isin(lending_group)]
    filtered_df_cutoff = df3_ye[df3_ye["YEAR"].isin(year) & df3_ye["Region"].isin(region) & df3_ye["LG"].isin(lending_group)]

filtered_df.sort_values("MONTH_ID", ascending=True, inplace=True)
filtered_df_cutoff.sort_values("MONTH_ID", ascending=True, inplace=True)

####################### TIME SERIES ANALYSIS

df_timeseries = df.groupby(by=["SEQ", "MONTH_YEAR"], as_index=False).agg({"Sum of Sum of Loan Portfolio": "sum", "NPL": "sum","BORROWER_COUNT":"sum"})
df_timeseries.sort_values("SEQ", ascending=True, inplace=True)

st.subheader("Time Series Analysis (December 2019 - March 2025)")

df_timeseries["Formatted_Loan_Portfolio"] = df_timeseries["Sum of Sum of Loan Portfolio"].apply(lambda x: f"{x / 1e9:.1f}Bn")
df_timeseries["Formatted_NPL"] = df_timeseries["NPL"].apply(lambda x: f"{x / 1e9:.1f}Bn")

trace1 = go.Scatter(
    x=df_timeseries["MONTH_YEAR"],
    y=df_timeseries["Sum of Sum of Loan Portfolio"],
    mode="lines+markers",
    name="Loan Portfolio (₱)",
    text=df_timeseries["Formatted_Loan_Portfolio"],  # Add formatted text for Loan Portfolio
    textposition="top center",
    marker=dict(size=6),
    line=dict(width=2)
)
trace2 = go.Scatter(
    x=df_timeseries["MONTH_YEAR"],
    y=df_timeseries["NPL"],
    mode="lines+markers",
    name="NPL(₱)",
    text=df_timeseries["Formatted_NPL"],  # Add formatted text for NPL
    textposition="top center",
    marker=dict(size=6),
    line=dict(width=2)
)

layout = go.Layout(
    xaxis=dict(title="Month-Year"),
    yaxis=dict(
        title="Loan Portfolio (₱)",
        tickprefix="₱",
        tickformat=".1s"
    ),
    yaxis2=dict(
        title="NPL (₱)",
        overlaying="y",
        side="right",
        tickprefix="₱",
        tickformat=".1s"
    ),
    template="gridon",
    height=500,
    width=1000
)

fig2 = go.Figure(data=[trace1, trace2], layout=layout)
fig2.update_traces(yaxis="y2", selector=dict(name="NPL(₱)"))
st.plotly_chart(fig2, use_container_width=True)

######

with st.expander("View data of time series", expanded=True):
    columns_to_keep = ["MONTH_YEAR", "Sum of Sum of Loan Portfolio", "NPL", "BORROWER_COUNT"]
    display_df = df_timeseries[columns_to_keep].copy()  # Use df_timeseries instead of linechart

    def format_currency(value):
        try:
            value = float(value)
            return "₱{:,.2f}".format(value)
        except ValueError:
            return value

    display_df["Sum of Sum of Loan Portfolio"] = display_df["Sum of Sum of Loan Portfolio"].apply(format_currency)
    display_df["NPL"] = display_df["NPL"].apply(format_currency)

    display_df["BORROWER_COUNT"] = display_df["BORROWER_COUNT"].apply(lambda x: "{:,.0f}".format(x) if pd.notnull(x) else x)

    display_df = display_df.rename(columns={
        "MONTH_YEAR": "MONTH_YEAR",
        "Sum of Sum of Loan Portfolio": "Loan Portfolio (₱)",
        "NPL": "NPL (₱)",
        "BORROWER_COUNT": "Borrower Count"
    })

    display_df["NPL Rate"] = display_df["NPL (₱)"].apply(lambda x: float(str(x).replace('₱', '').replace(',', '')) if '₱' in str(x) else x) / display_df["Loan Portfolio (₱)"].apply(lambda x: float(str(x).replace('₱', '').replace(',', '')) if '₱' in str(x) else x)
    display_df["NPL Rate"] = display_df["NPL Rate"].apply(lambda x: f"{x * 100:.2f}%")
    #borrower_count_sum = df_timeseries.groupby("MONTH_YEAR")["BORROWER_COUNT"].sum().reset_index()
    #display_df = display_df.merge(borrower_count_sum, on="MONTH_YEAR", how="left")
    st.write(display_df.T.style.background_gradient(cmap="Blues"))
    csv = df_timeseries[columns_to_keep].to_csv(index=False).encode("utf-8")  # Use df_timeseries here as well

    st.download_button(
        "Download Data",
        data=csv,
        file_name="Time Series.csv",
        mime="text/csv",
        help='Click here to download the CSV file'
    )

col3, col4 = st.columns((2))

category_df = filtered_df.groupby(by=["MONTH_ID", "MONTH_YEAR"], as_index=False).agg({"Sum of Sum of Loan Portfolio": "sum", "NPL": "sum"})
category_df.sort_values("MONTH_ID", ascending=True, inplace=True)

category_df['OPB (in ₱Bn)'] = category_df["Sum of Sum of Loan Portfolio"] / 1e9
category_df['NPL (in ₱Bn)'] = category_df["NPL"] / 1e9

category_df_melted = pd.melt(category_df,
                             id_vars=["MONTH_YEAR"],
                             value_vars=["OPB (in ₱Bn)", "NPL (in ₱Bn)"],
                             var_name="Field", value_name="Value")

category_df_melted['Text'] = category_df_melted['Value'].apply(lambda x: f"{x:,.2f}")

formatted_years = [str(int(y)) for y in year]
formatted_year_string = ", ".join(formatted_years)

with col3:
    st.subheader(f"Loan Portfolio by Month (Quarterly) - CY {formatted_year_string}")
    fig = px.bar(category_df_melted,
                 x="MONTH_YEAR",
                 y="Value",
                 color="Field",
                 text= "Text",
                 labels={"Value": "Amount (in ₱ Billion)",
                         "Field": "Field",
                         "MONTH_YEAR": "Month-Year"},
                 template="seaborn")
    fig.update_layout(barmode='group')
    st.plotly_chart(fig, use_container_width=True, height=200)


with col4:
    st.subheader(f"Loan Portfolio by Lending Group - CY {formatted_year_string}")
    fig = px.pie(filtered_df_cutoff, values="Sum of Sum of Loan Portfolio", names="LG", hole = 0.5)
    fig.update_traces(text = filtered_df_cutoff["LG"], textposition="outside")
    st.plotly_chart(fig, use_container_width=True, height=200)


cl1, cl2 = st.columns((2))

category_df["Sum of Sum of Loan Portfolio"] = category_df["Sum of Sum of Loan Portfolio"].apply(lambda x: "₱{:,.2F}".format(x))
category_df["NPL"] = category_df["NPL"].apply(lambda x: "₱{:,.2F}".format(x))

columns_to_keep2 = {
    "MONTH_YEAR": "Month-Year",
    "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)",
    "NPL":"Non-Performing Loans (₱)"
}

display_df = category_df[list(columns_to_keep2.keys())].copy()
display_df.rename(columns=columns_to_keep2, inplace=True)

with cl1:
    with st.expander("Loan Portfolio by Month-Year",expanded=True):
        st.write(display_df)
        csv = display_df.to_csv(index = False).encode("utf-8")
        st.download_button("Download Data", data = csv, file_name = "Loans.csv",mime = "text/csv",
                           help='Click here to download CSV file')

with cl2:
    with st.expander("Loan Portfolio by Lending Group",expanded=True):
        lgroup = filtered_df_cutoff.groupby(by="LG", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        lgroup = lgroup.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)

        lgroup.rename(columns={
            "LG": "Lending Group",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)

        lgroup["Total Loan Portfolio (₱)"] = lgroup["Total Loan Portfolio (₱)"].apply(lambda x: f"₱{x:,.2f}")
        #st.table(lgroup.style.background_gradient(cmap="Oranges"))
        st.table(lgroup)

        csv_df = filtered_df_cutoff.groupby(by="LG", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        csv_df = csv_df.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)
        csv_df.rename(columns={
            "LG": "Lending Group",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)
        csv = csv_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv,
            file_name="Lending_Group.csv",
            mime="text/csv",
            help="Click here to download CSV file"
        )


st.subheader(f"Hierarchical view of Loan Portfolio per Region - CY {formatted_year_string}")
filtered_df_cutoff["Formatted Value"] = filtered_df_cutoff["Sum of Sum of Loan Portfolio"].apply(lambda x: f"₱{x:,.0f}")
filtered_df_cutoff["Custom Text"] = filtered_df_cutoff["Region"] + "<br>" + filtered_df_cutoff["Formatted Value"]

fig3 = px.treemap(
    filtered_df_cutoff,
    path=["YEAR", "Region"],
    values="Sum of Sum of Loan Portfolio",
    hover_data={"Sum of Sum of Loan Portfolio": ":,.0f"},
    color="Region",
)

fig3.update_traces(
    textinfo="label+value+percent parent",
    texttemplate="%{label}<br>₱%{value:,.0f}<br>%{percentParent:.2%}",
    hovertemplate="<b>%{label}</b><br>Amount: ₱%{value:,.0f}<br>Parent Share: %{percentParent:.2%}<extra></extra>",
    textfont=dict(size=16)
)
st.plotly_chart(fig3, use_container_width=True)


chart1, chart2 = st.columns((2))
with chart1:
    st.subheader(f"Loan Portfolio by Account Type  - CY {formatted_year_string}")
    fig = px.pie(filtered_df_cutoff, values = "Sum of Sum of Loan Portfolio", names = "Account/Loan Type", template = "plotly_dark")
    fig.update_traces(text = filtered_df_cutoff["Account/Loan Type"], textposition = "inside")
    st.plotly_chart(fig, use_container_width=True)

with chart2:
    st.subheader(f"Loan Portfolio by Customer /Asset Size - CY {formatted_year_string}")
    fig = px.pie(filtered_df_cutoff, values = "Sum of Sum of Loan Portfolio", names = "Customer Size", template = "gridon")
    fig.update_traces(text = filtered_df_cutoff["Customer Size"], textposition = "outside")
    st.plotly_chart(fig, use_container_width=True)



cl3, cl4 = st.columns((2))
with cl3:
    with st.expander("Loan Portfolio by Account Type"):
        lgroup2 = filtered_df_cutoff.groupby(by="Account/Loan Type", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        lgroup2 = lgroup2.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)

        lgroup2.rename(columns={
            "Account/Loan Type": "Account / Loan Type",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)

        lgroup2["Total Loan Portfolio (₱)"] = lgroup2["Total Loan Portfolio (₱)"].apply(lambda x: f"₱{x:,.2f}")
        #st.table(lgroup2.style.background_gradient(cmap="Oranges"))
        st.table(lgroup2)

        csv_df2 = filtered_df_cutoff.groupby(by="Account/Loan Type", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        csv_df2 = csv_df2.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)
        csv_df2.rename(columns={
            "Account/Loan Type": "Account / Loan Type",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)
        csv2 = csv_df2.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv2,
            file_name="Account/Loan.csv",
            mime="text/csv",
            help="Click here to download CSV file"
        )

with cl4:
    with st.expander("Loan Portfolio by Customer / Asset Size"):
        lgroup3 = filtered_df_cutoff.groupby(by="Customer Size", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        lgroup3 = lgroup3.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)

        lgroup3.rename(columns={
            "Customer Size": "Customer / Asset Size",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)

        lgroup3["Total Loan Portfolio (₱)"] = lgroup3["Total Loan Portfolio (₱)"].apply(lambda x: f"₱{x:,.2f}")
        #st.table(lgroup3.style.background_gradient(cmap="Oranges"))
        st.table(lgroup3)

        csv_df3 = filtered_df_cutoff.groupby(by="Customer Size", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        csv_df3 = csv_df3.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)
        csv_df3.rename(columns={
            "Customer Size": "Customer / Asset Size",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)
        csv3 = csv_df3.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv3,
            file_name="Customer Size.csv",
            mime="text/csv",
            help="Click here to download CSV file"
        )

st.subheader(f"Loan Portfolio by Major Industry  - CY {formatted_year_string}")
industry_opb = filtered_df_cutoff.groupby("Major Industry")["Sum of Sum of Loan Portfolio"].sum()
industry_opb_percent = (industry_opb / industry_opb.sum()) * 100
industry_opb_percent = industry_opb_percent.sort_values(ascending=True).round(2)

# Create a DataFrame for plotting
plot_df = industry_opb_percent.reset_index()
plot_df.columns = ['Major Industry', 'OPB Share (%)']


fig2 = px.bar(
    plot_df,
    x='OPB Share (%)',
    y='Major Industry',
    color='OPB Share (%)',
    color_continuous_scale='Cividis',
    orientation='h',
    text=plot_df['OPB Share (%)'].astype(str) + '%',
)

fig2.update_traces(textposition='outside')
fig2.update_layout(coloraxis_showscale=False)
st.plotly_chart(fig2, use_container_width=True)

with st.expander("Loan Portfolio by Major Industry"):
    lgroup4 = filtered_df_cutoff.groupby(by="Major Industry", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
    lgroup4 = lgroup4.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)

    lgroup4.rename(columns={
        "Major Industry": "Major Industry",
        "BORROWER_COUNT": "No. of Borrowers",
        "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
    }, inplace=True)

    lgroup4["Total Loan Portfolio (₱)"] = lgroup4["Total Loan Portfolio (₱)"].apply(lambda x: f"₱{x:,.2f}")
    st.table(lgroup4)

    csv_df4 = filtered_df_cutoff.groupby(by="Major Industry", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
    csv_df4 = csv_df4.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)
    csv_df4.rename(columns={
        "Major Industry": "Major Industry",
        "BORROWER_COUNT": "No. of Borrowers",
        "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
    }, inplace=True)
    csv4 = csv_df4.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Data",
        data=csv4,
        file_name="Major Industry.csv",
        mime="text/csv",
        help="Click here to download CSV file"
    )

#import plotly.figure_factory as ff
st.subheader("Loan Portfolio Summary")
with st.expander("Summary Table",expanded=True):
    st.markdown(f"Monthly Loan Portfolio per Lending Unit- CY {formatted_year_string}")
    filtered_df["CUTOFF_DATE"] = pd.to_datetime(filtered_df["CUTOFF_DATE"], format="%b-%Y")
    sub_category_year = pd.pivot_table(data = filtered_df, values = "Sum of Sum of Loan Portfolio", index = ["LG","LENDING UNIT"], columns = "CUTOFF_DATE", aggfunc = "sum", sort = True)
    sub_category_year = sub_category_year[sorted(sub_category_year.columns)]
    sub_category_year.columns = sub_category_year.columns.strftime("%b-%Y")
    styled_table = sub_category_year.style \
        .format("₱{:,.2f}") \
        .background_gradient(cmap="Blues")
    st.write(styled_table)


    st.markdown(f"Top 20 Borrowers with the Highest OPB - CY {formatted_year_string}")
    filtered_df_cutoff.columns = filtered_df_cutoff.columns.str.strip()
    df_filtered = filtered_df_cutoff[filtered_df_cutoff['MONTH_ID'] == 12].copy()
    unique_df = df_filtered.drop_duplicates(subset=[
        'YEAR', 'BORROWER_CODE_NAME', 'LENDING UNIT', 'LG', 'Major Industry',
        'Account/Loan Type', 'Location', 'Type of Facility', 'Collateral Type',
        'Loan Status', 'Area Code', 'Sum of Sum of Loan Portfolio'])
    unique_df['TempRank'] = unique_df.groupby('YEAR')['Sum of Sum of Loan Portfolio']\
                                     .rank(method='first', ascending=False)
    top20 = unique_df[unique_df['TempRank'] <= 20].copy()
    top20['LoanPortfolioNumeric'] = top20['Sum of Sum of Loan Portfolio']
    top20 = top20.sort_values(['YEAR', 'LoanPortfolioNumeric'], ascending=False)
    top20['Rank'] = top20.groupby('YEAR')['LoanPortfolioNumeric'].rank(method='first', ascending=False).astype(int)
    top20['Sum of Sum of Loan Portfolio'] = top20['LoanPortfolioNumeric'].apply(lambda x: f"₱{x:,.2f}")
    final_df = top20[[
        'Rank', 'BORROWER_CODE_NAME', 'Sum of Sum of Loan Portfolio', 'LENDING UNIT', 'LG', 'Major Industry',
        'Account/Loan Type', 'Location', 'Type of Facility', 'Collateral Type',
        'Loan Status', 'Area Code']]
    final_df.rename(columns={
        "BORROWER_CODE_NAME": "Name of the Borrower",
        "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)",
        "LENDING UNIT": "Lending Unit"
    }, inplace=True)
    st.write(final_df)

col5, col6 = st.columns((2))

with col5:
    st.subheader(f"Loan Portfolio by Government/Private - CY {formatted_year_string}")
    fig4 = px.pie(filtered_df_cutoff, values="Sum of Sum of Loan Portfolio", names="Govt Priv", hole=0.5)
    fig4.update_traces(text=filtered_df_cutoff["Govt Priv"], textposition="outside")
    st.plotly_chart(fig4, use_container_width=True, height=200)

with col6:
    st.subheader(f"Loan Portfolio by Funding - CY {formatted_year_string}")
    fig5 = px.pie(filtered_df_cutoff, values="Sum of Sum of Loan Portfolio", names="Source", hole=0.5)
    fig5.update_traces(text=filtered_df_cutoff["Source"], textposition="outside")
    st.plotly_chart(fig5, use_container_width=True, height=200)

cl5,cl6 = st.columns((2))

with cl5:
    with st.expander("Loan Portfolio by Government/Private", expanded=True):
        lgroup5 = filtered_df_cutoff.groupby(by="Govt Priv", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        lgroup5 = lgroup5.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)

        lgroup5.rename(columns={
            "Govt Priv": "Classification",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)

        lgroup5["Total Loan Portfolio (₱)"] = lgroup5["Total Loan Portfolio (₱)"].apply(lambda x: f"₱{x:,.2f}")
        st.table(lgroup5)

        csv_df5 = filtered_df_cutoff.groupby(by="Govt Priv", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        csv_df5 = csv_df5.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)
        csv_df5.rename(columns={
            "Govt Priv": "Classification",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)
        csv5 = csv_df5.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv5,
            file_name="Govt Private.csv",
            mime="text/csv",
            help="Click here to download CSV file"
        )

with cl6:
    with st.expander("Loan Portfolio by Fund Source", expanded=True):
        lgroup6 = filtered_df_cutoff.groupby(by="Source", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        lgroup6 = lgroup6.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)

        lgroup6.rename(columns={
            "Source": "Fund Source",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)

        lgroup6["Total Loan Portfolio (₱)"] = lgroup6["Total Loan Portfolio (₱)"].apply(lambda x: f"₱{x:,.2f}")
        st.table(lgroup6)

        csv_df6 = filtered_df_cutoff.groupby(by="Source", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        csv_df6 = csv_df6.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)
        csv_df6.rename(columns={
            "Source": "Fund Source",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)
        csv6 = csv_df6.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv6,
            file_name="Fund Source.csv",
            mime="text/csv",
            help="Click here to download CSV file"
        )


chart3, chart4 = st.columns((2))

with chart3:
    st.subheader(f"Loan Portfolio by Interest Rate Type  - CY {formatted_year_string}")
    fig = px.pie(filtered_df_cutoff, values = "Sum of Sum of Loan Portfolio", names = "Interest Type", template = "seaborn")
    fig.update_traces(
        text=filtered_df_cutoff.apply(
            lambda row: f"{row['Interest Type']}", axis=1
        ),
        textposition="outside",
        textfont=dict(size=16)
    )
    st.plotly_chart(fig, use_container_width=True)

with chart4:
    st.subheader(f"Loan Portfolio by Interest Rate  - CY {formatted_year_string}")
    interest_opb = filtered_df_cutoff.groupby("Interest Rate Range")["Sum of Sum of Loan Portfolio"].sum()

    interest_opb_percent = (interest_opb / interest_opb.sum()) * 100
    interest_opb_percent = interest_opb_percent.sort_values(ascending=True).round(2)

    plot_df2 = interest_opb_percent.reset_index()
    plot_df2.columns = ['Interest Rate Range', 'OPB Share (%)']

    fig7 = px.bar(
        plot_df2,
        x='OPB Share (%)',
        y='Interest Rate Range',
        color='OPB Share (%)',
        color_continuous_scale='Cividis',
        orientation='h',
        text=plot_df2['OPB Share (%)'].astype(str) + '%')

    fig7.update_traces(textposition='outside')
    fig7.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig7, use_container_width=True)


with st.expander("Loan Portfolio by Interest Rate"):
    lgroup8 = filtered_df_cutoff.groupby(by=["Interest Type","Interest Rate Range"], as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
    lgroup8 = lgroup8.sort_values(by=["Interest Type","Sum of Sum of Loan Portfolio"], ascending=False)

    lgroup8.rename(columns={
        "Interest Type": "Interest Type",
        "Interest Rate Range": "Interest Rate Range",
        "BORROWER_COUNT": "No. of Borrowers",
        "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
    }, inplace=True)

    lgroup8["Total Loan Portfolio (₱)"] = lgroup8["Total Loan Portfolio (₱)"].apply(lambda x: f"₱{x:,.2f}")
    st.table(lgroup8)
    csv_df8 = filtered_df_cutoff.groupby(by=["Interest Type", "Interest Rate Range"], as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
    csv_df8 = csv_df8.sort_values(by=["Interest Type","Sum of Sum of Loan Portfolio"], ascending=False)
    csv_df8.rename(columns={
        "Interest Type": "Interest Type",
        "Interest Rate Range": "Interest Rate Range",
        "BORROWER_COUNT": "No. of Borrowers",
        "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
    }, inplace=True)
    csv8 = csv_df8.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Data",
        data=csv8,
        file_name="Interest Rate.csv",
        mime="text/csv",
        help="Click here to download CSV file"
    )

cl7, cl8 = st.columns((2))
with cl7:
    st.subheader(f"Loan Portfolio by Facility/Product - CY {formatted_year_string}")
    filtered_df_cutoff["Formatted Value"] = filtered_df_cutoff["Sum of Sum of Loan Portfolio"].apply(lambda x: f"₱{x:,.0f}")
    filtered_df_cutoff["Custom Text"] = filtered_df_cutoff["Type of Facility"] + "<br>" + filtered_df_cutoff["Formatted Value"]

    fig7 = px.treemap(
        filtered_df_cutoff,
        path=["YEAR", "Type of Facility"],
        values="Sum of Sum of Loan Portfolio",
        hover_data={"Sum of Sum of Loan Portfolio": ":,.0f"},
        color="Type of Facility",
        color_discrete_sequence=px.colors.qualitative.D3
    )

    fig7.update_traces(
        textinfo="label+value+percent parent",
        texttemplate="%{label}<br>₱%{value:,.0f}<br>%{percentParent:.2%}",
        hovertemplate="<b>%{label}</b><br>Amount: ₱%{value:,.0f}<br>Parent Share: %{percentParent:.2%}<extra></extra>",
        textfont=dict(size=16)
    )
    st.plotly_chart(fig7, use_container_width=True)

with cl8:
    st.subheader(f"Loan Portfolio by Loan Term - CY {formatted_year_string}")
    filtered_df_cutoff["Formatted Value"] = filtered_df_cutoff["Sum of Sum of Loan Portfolio"].apply(lambda x: f"₱{x:,.0f}")
    filtered_df_cutoff["Custom Text"] = filtered_df_cutoff["Loan Term"] + "<br>" + filtered_df_cutoff["Formatted Value"]

    fig8 = px.treemap(
        filtered_df_cutoff,
        path=["YEAR", "Loan Term"],
        values="Sum of Sum of Loan Portfolio",
        hover_data={"Sum of Sum of Loan Portfolio": ":,.0f"},
        color="Loan Term",
        color_discrete_sequence=px.colors.qualitative.Set3    )

    fig8.update_traces(
        textinfo="label+value+percent parent",
        texttemplate="%{label}<br>₱%{value:,.0f}<br>%{percentParent:.2%}",
        hovertemplate="<b>%{label}</b><br>Amount: ₱%{value:,.0f}<br>Parent Share: %{percentParent:.2%}<extra></extra>",
        textfont=dict(size=16)
    )
    st.plotly_chart(fig8, use_container_width=True)


cl9, cl10 = st.columns((2))

with cl9:
    with st.expander("Loan Portfolio by Facility", expanded=True):
        lgroup9 = filtered_df_cutoff.groupby(by="Type of Facility", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        lgroup9 = lgroup9.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)

        lgroup9.rename(columns={
            "Type of Facility": "Type of Facility",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)

        lgroup9["Total Loan Portfolio (₱)"] = lgroup9["Total Loan Portfolio (₱)"].apply(lambda x: f"₱{x:,.2f}")
        #st.table(lgroup6.style.background_gradient(cmap="Oranges"))
        st.table(lgroup9)

        csv_df9 = filtered_df_cutoff.groupby(by="Type of Facility", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        csv_df9 = csv_df9.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)
        csv_df9.rename(columns={
            "Type of Facility": "Type of Facility",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)
        csv9 = csv_df9.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv9,
            file_name="Facility.csv",
            mime="text/csv",
            help="Click here to download CSV file"
        )

with cl10:
    with st.expander("Loan Portfolio by Loan Term", expanded=True):
        lgroup10 = filtered_df_cutoff.groupby(by="Loan Term", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        lgroup10 = lgroup10.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)

        lgroup10.rename(columns={
            "Loan Term": "Loan Term",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)

        lgroup10["Total Loan Portfolio (₱)"] = lgroup10["Total Loan Portfolio (₱)"].apply(lambda x: f"₱{x:,.2f}")
        st.table(lgroup10)

        csv_df10 = filtered_df_cutoff.groupby(by="Loan Term", as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        csv_df10 = csv_df10.sort_values(by="Sum of Sum of Loan Portfolio", ascending=False)
        csv_df10.rename(columns={
            "Loan Term": "Loan Term",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)
        csv10 = csv_df10.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv10,
            file_name="Funding.csv",
            mime="text/csv",
            help="Click here to download CSV file"
        )

chart11, chart12 = st.columns((2))

with chart11:
    st.subheader(f"Loan Portfolio by Collateral Type  - CY {formatted_year_string}")
    fig11 = px.pie(filtered_df_cutoff, values = "Sum of Sum of Loan Portfolio", names = "Collateral Type", template = "seaborn")
    fig11.update_traces(
        text=filtered_df_cutoff.apply(
            lambda row: f"{row['Collateral Type']}", axis=1
        ),
        textposition="outside",
        textfont=dict(size=16)
    )
    st.plotly_chart(fig11, use_container_width=True)

with chart12:
    st.subheader(f"Loan Portfolio by Collateral Type Description  - CY {formatted_year_string}")

    values_to_drop = ["(blank)","OTHERS COLLATERAL","OTHERS/UNSECURED"]
    filtered_df_cutoff_clean = filtered_df_cutoff[~filtered_df_cutoff["Collateral Type Description"].isin(values_to_drop)]
    collateral_opb = filtered_df_cutoff_clean.groupby("Collateral Type Description")["Sum of Sum of Loan Portfolio"].sum()
    collateral_opb_percent = (collateral_opb / collateral_opb.sum()) * 100
    collateral_opb_percent = collateral_opb_percent.sort_values(ascending=True).round(2)

    plot_df12 = collateral_opb_percent.reset_index()
    plot_df12.columns = ['Collateral Type Description', 'OPB Share (%)']

    fig12 = px.bar(
        plot_df12,
        x='OPB Share (%)',
        y='Collateral Type Description',
        color='OPB Share (%)',
        color_continuous_scale='Cividis',
        orientation='h',
        text=plot_df12['OPB Share (%)'].astype(str) + '%')

    fig12.update_traces(textposition='outside')
    fig12.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig12, use_container_width=True)


cl11, cl12 = st.columns((2))

with cl11:
    with st.expander("Loan Portfolio by Collateral Type"):
        lgroup11 = filtered_df_cutoff.groupby(by=["Collateral Type"], as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        lgroup11 = lgroup11.sort_values(by=["Sum of Sum of Loan Portfolio"], ascending=False)

        lgroup11.rename(columns={
            "Collateral Type" : "Collateral Type",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)

        lgroup11["Total Loan Portfolio (₱)"] = lgroup11["Total Loan Portfolio (₱)"].apply(lambda x: f"₱{x:,.2f}")
        st.table(lgroup11)

        csv_df11 = filtered_df_cutoff.groupby(by=["Collateral Type"], as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        csv_df11 = csv_df11.sort_values(by=["Sum of Sum of Loan Portfolio"], ascending=False)
        csv_df11.rename(columns={
            "Collateral Type": "Collateral Type",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)
        csv11 = csv_df11.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv11,
            file_name="Collateral Type.csv",
            mime="text/csv",
            help="Click here to download CSV file"
        )

with cl12:
    with st.expander("Loan Portfolio by Collateral Type Description"):
        values_to_drop2 = ["(blank)", "OTHERS COLLATERAL", "OTHERS/UNSECURED"]
        filtered_df_cutoff_clean2 = filtered_df_cutoff[
            ~filtered_df_cutoff["Collateral Type Description"].isin(values_to_drop2)]

        lgroup11 = filtered_df_cutoff_clean2.groupby(by=["Collateral Type Description"], as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        lgroup11 = lgroup11.sort_values(by=["Sum of Sum of Loan Portfolio"], ascending=False)

        lgroup11.rename(columns={
            "Collateral Type" : "Collateral Type",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)

        lgroup11["Total Loan Portfolio (₱)"] = lgroup11["Total Loan Portfolio (₱)"].apply(lambda x: f"₱{x:,.2f}")
        st.table(lgroup11)

        csv_df11 = filtered_df_cutoff.groupby(by=["Collateral Type"], as_index=False)[["Sum of Sum of Loan Portfolio","BORROWER_COUNT"]].sum()
        csv_df11 = csv_df11.sort_values(by=["Sum of Sum of Loan Portfolio"], ascending=False)
        csv_df11.rename(columns={
            "Collateral Type": "Collateral Type",
            "BORROWER_COUNT": "No. of Borrowers",
            "Sum of Sum of Loan Portfolio": "Total Loan Portfolio (₱)"
        }, inplace=True)
        csv11 = csv_df11.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv11,
            file_name="Collateral Type Desc.csv",
            mime="text/csv",
            help="Click here to download CSV file"
        )

########################### GeogrSpatial



st.subheader("Geospatial distribution of Borrowers")

data_grouped = filtered_df_cutoff.groupby(['Latitude', 'Longitude','Location'], as_index=False)['BORROWER_COUNT'].sum()

map_center = [12.8797, 121.7740]
m = folium.Map(location=map_center, zoom_start=6, tiles="OpenStreetMap")
marker_cluster = MarkerCluster().add_to(m)
colormap = linear.YlGnBu_09.scale(min(data_grouped['BORROWER_COUNT']), max(data_grouped['BORROWER_COUNT']))

for index, row in data_grouped.iterrows():
    latitude = row['Latitude']
    longitude = row['Longitude']
    loc_map = row['Location']
    borrower_count = row['BORROWER_COUNT']

    color = colormap(borrower_count)
    radius = borrower_count * 2

    folium.CircleMarker(
        location=[latitude, longitude],
        popup=f"Location: {loc_map}<br>No. of Borrowers: {borrower_count}",
        tooltip=f"Location: {loc_map}<br>No. of Borrowers: {borrower_count}",
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.6
    ).add_to(marker_cluster)

map_html = m._repr_html_()
st.components.v1.html(map_html, width=1400, height=900)

################## NON-PERFORMING LOANS

st.divider()
st.markdown("## **NON-PERFORMING LOANS (NPL)**")

col11, col12 = st.columns((2))

with col11:
    st.subheader(f"NPL by Lending Group - CY {formatted_year_string}")
    fig11 = px.pie(filtered_df_cutoff, values="NPA", names="LG", hole = 0.5)
    fig11.update_traces(text = filtered_df_cutoff["LG"], textposition="outside")
    st.plotly_chart(fig11, use_container_width=True, height=200)

with col12:
    st.subheader(f"NPL by Account Type - CY {formatted_year_string}")
    fig12 = px.pie(filtered_df_cutoff, values="NPA", names="Account/Loan Type", hole = 0.5)
    fig12.update_traces(text = filtered_df_cutoff["Account/Loan Type"], textposition="outside")
    st.plotly_chart(fig12, use_container_width=True, height=200)

cl11, cl12 = st.columns(2)

with cl11:
    with st.expander("NPL by Lending Group"):
        npa_count = filtered_df_cutoff[filtered_df_cutoff["Area Code"] == "NPA"].groupby(by=["LG"], as_index=False)["Area Code"].count()
        npa_sum = filtered_df_cutoff.groupby(by=["LG"], as_index=False)["NPA"].sum()

        lgroup11 = pd.merge(npa_count, npa_sum, on="LG", how="left")
        lgroup11.rename(columns={
            "LG": "Lending Group",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        lgroup11["Total NPL (₱)"] = lgroup11["Total NPL (₱)"].replace({'₱': '', ',': ''}, regex=True).astype(float)
        lgroup11 = lgroup11.sort_values(by="Total NPL (₱)", ascending=False)
        lgroup11["Total NPL (₱)"] = lgroup11["Total NPL (₱)"].apply(lambda x: f"₱{x:,.2f}")

        st.table(lgroup11)
        csv_df11 = pd.merge(npa_count, npa_sum, on="LG", how="left")

        csv_df11.rename(columns={
            "LG": "Lending Group",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        csv11 = csv_df11.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv11,
            file_name="NPL LG.csv",
            mime="text/csv",
            help="Click here to download the CSV file"
        )

with cl12:
    with st.expander("NPL by Account Type"):
        npa_count2 = filtered_df_cutoff[filtered_df_cutoff["Area Code"] == "NPA"].groupby(by=["Account/Loan Type"], as_index=False)["Area Code"].count()
        npa_sum2 = filtered_df_cutoff.groupby(by=["Account/Loan Type"], as_index=False)["NPA"].sum()

        lgroup12 = pd.merge(npa_count2, npa_sum2, on="Account/Loan Type", how="left")
        lgroup12.rename(columns={
            "Account/Loan Type": "Account Type",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        lgroup12["Total NPL (₱)"] = lgroup12["Total NPL (₱)"].replace({'₱': '', ',': ''}, regex=True).astype(float)
        lgroup12 = lgroup12.sort_values(by="Total NPL (₱)", ascending=False)
        lgroup12["Total NPL (₱)"] = lgroup12["Total NPL (₱)"].apply(lambda x: f"₱{x:,.2f}")

        st.table(lgroup12)
        csv_df12 = pd.merge(npa_count2, npa_sum2, on="Account/Loan Type", how="left")

        csv_df12.rename(columns={
            "Account/Loan Type": "Account Type",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        csv12 = csv_df12.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv12,
            file_name="NPL Account Type.csv",
            mime="text/csv",
            help="Click here to download the CSV file"
        )

st.subheader(f"NPL by Major Industry  - CY {formatted_year_string}")
industry_npl = filtered_df_cutoff.groupby("Major Industry")["NPA"].sum()
industry_npl_percent = (industry_npl / industry_npl.sum()) * 100
industry_npl_percent = industry_npl_percent.sort_values(ascending=True).round(2)

plot_df_np = industry_npl_percent.reset_index()
plot_df_np.columns = ['Major Industry', 'NPL Share (%)']

fig13 = px.bar(
    plot_df_np,
    x='NPL Share (%)',
    y='Major Industry',
    color='NPL Share (%)',
    color_continuous_scale='Cividis',
    orientation='h',
    text=plot_df_np['NPL Share (%)'].astype(str) + '%',

)

# Adjust visuals
fig13.update_traces(textposition='outside')
fig13.update_layout(coloraxis_showscale=False)
st.plotly_chart(fig13, use_container_width=True)

with st.expander("NPL by Major Industry"):
    npa_count3 = filtered_df_cutoff[filtered_df_cutoff["Area Code"] == "NPA"].groupby(by=["Major Industry"], as_index=False)["Area Code"].count()
    npa_sum3 = filtered_df_cutoff.groupby(by=["Major Industry"], as_index=False)["NPA"].sum()

    lgroup13 = pd.merge(npa_count3, npa_sum3, on="Major Industry", how="left")
    lgroup13.rename(columns={
        "Major Industry": "Major Industry",
        "Area Code": "No. of NPA Records",
        "NPA": "Total NPL (₱)",
    }, inplace=True)

    lgroup13["Total NPL (₱)"] = lgroup13["Total NPL (₱)"].replace({'₱': '', ',': ''}, regex=True).astype(float)
    lgroup13 = lgroup13.sort_values(by="Total NPL (₱)", ascending=False)
    lgroup13["Total NPL (₱)"] = lgroup13["Total NPL (₱)"].apply(lambda x: f"₱{x:,.2f}")

    st.table(lgroup13)
    csv_df13 = pd.merge(npa_count3, npa_sum3, on="Major Industry", how="left")

    csv_df13.rename(columns={
        "Major Industry": "Major Industry",
        "Area Code": "No. of NPA Records",
        "NPA": "Total NPL (₱)",
    }, inplace=True)

    csv13 = csv_df13.to_csv(index=False).encode("utf-8")

    st.download_button(
        "Download Data",
        data=csv13,
        file_name="NPL Major Industry.csv",
        mime="text/csv",
        help="Click here to download the CSV file"
    )


chart13, chart14 = st.columns((2))

with chart13:
    st.subheader(f"NPL by Interest Rate Type  - CY {formatted_year_string}")
    fig13 = px.pie(filtered_df_cutoff, values = "NPA", names = "Interest Type", template = "seaborn")
    fig13.update_traces(
        text=filtered_df_cutoff.apply(
            lambda row: f"{row['Interest Type']}", axis=1
        ),
        textposition="outside",
        textfont=dict(size=16)
    )
    st.plotly_chart(fig13, use_container_width=True)

with chart14:
    st.subheader(f"NPA by Interest Rate  - CY {formatted_year_string}")
    interest_npa = filtered_df_cutoff.groupby("Interest Rate Range")["NPA"].sum()

    interest_npa_percent = (interest_npa / interest_opb.sum()) * 100
    interest_npa_percent = interest_npa_percent.sort_values(ascending=True).round(2)

    plot_df14 = interest_npa_percent.reset_index()
    plot_df14.columns = ['Interest Rate Range', 'NPL Share (%)']

    fig14 = px.bar(
        plot_df14,
        x='NPL Share (%)',
        y='Interest Rate Range',
        color='NPL Share (%)',
        color_continuous_scale='Cividis',
        orientation='h',
        text=plot_df14['NPL Share (%)'].astype(str) + '%')

    fig14.update_traces(textposition='outside')
    fig14.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig14, use_container_width=True)

cl13, cl14 = st.columns((2))

with cl13:
    with st.expander("NPL by Interest Type"):
        npa_count4 = filtered_df_cutoff[filtered_df_cutoff["Area Code"] == "NPA"].groupby(by=["Interest Type"], as_index=False)["Area Code"].count()
        npa_sum4 = filtered_df_cutoff.groupby(by=["Interest Type"], as_index=False)["NPA"].sum()

        lgroup13 = pd.merge(npa_count4, npa_sum4, on="Interest Type", how="left")
        lgroup13.rename(columns={
            "Interest Type": "Interest Type",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        lgroup13["Total NPL (₱)"] = lgroup13["Total NPL (₱)"].replace({'₱': '', ',': ''}, regex=True).astype(float)
        lgroup13 = lgroup13.sort_values(by="Total NPL (₱)", ascending=False)
        lgroup13["Total NPL (₱)"] = lgroup13["Total NPL (₱)"].apply(lambda x: f"₱{x:,.2f}")

        st.table(lgroup13)
        csv_df13 = pd.merge(npa_count4, npa_sum4, on="Interest Type", how="left")

        csv_df13.rename(columns={
            "Interest Type": "Interest Type",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        csv13 = csv_df13.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv13,
            file_name="NPL Interest Type.csv",
            mime="text/csv",
            help="Click here to download the CSV file"
        )

with cl14:
    with st.expander("NPL by Interest Rate"):
        npa_count5 = filtered_df_cutoff[filtered_df_cutoff["Area Code"] == "NPA"].groupby(by=["Interest Rate Range"], as_index=False)["Area Code"].count()
        npa_sum5 = filtered_df_cutoff.groupby(by=["Interest Rate Range"], as_index=False)["NPA"].sum()

        lgroup14 = pd.merge(npa_count5, npa_sum5, on="Interest Rate Range", how="left")
        lgroup14.rename(columns={
            "Interest Rate Range": "Interest Rate",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        lgroup14["Total NPL (₱)"] = lgroup14["Total NPL (₱)"].replace({'₱': '', ',': ''}, regex=True).astype(float)
        lgroup14 = lgroup14.sort_values(by="Total NPL (₱)", ascending=False)
        lgroup14["Total NPL (₱)"] = lgroup14["Total NPL (₱)"].apply(lambda x: f"₱{x:,.2f}")

        st.table(lgroup14)
        csv_df14 = pd.merge(npa_count5, npa_sum5, on="Interest Rate Range", how="left")

        csv_df14.rename(columns={
            "Interest Rate Range": "Interest Rate",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        csv14 = csv_df14.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv14,
            file_name="NPL Interest Rate Range.csv",
            mime="text/csv",
            help="Click here to download the CSV file"
        )


chart15, chart16 = st.columns(2)

with chart15:
    st.subheader(f"NPL by Collateral Type  - CY {formatted_year_string}")
    fig15 = px.pie(filtered_df_cutoff, values = "NPA", names = "Collateral Type", template = "seaborn")
    fig15.update_traces(
        text=filtered_df_cutoff.apply(
            lambda row: f"{row['Collateral Type']}", axis=1
        ),
        textposition="outside",
        textfont=dict(size=16)
    )
    st.plotly_chart(fig15, use_container_width=True)

with chart16:
    st.subheader(f"NPA by Collateral Type Description  - CY {formatted_year_string}")

    values_to_drop2 = ["(blank)","OTHERS COLLATERAL","OTHERS/UNSECURED"]
    filtered_df_cutoff_clean2 = filtered_df_cutoff[~filtered_df_cutoff["Collateral Type Description"].isin(values_to_drop2)]
    collateral_opb2 = filtered_df_cutoff_clean2.groupby("Collateral Type Description")["NPA"].sum()
    collateral_opb_percent2 = (collateral_opb2 / collateral_opb2.sum()) * 100
    collateral_opb_percent2 = collateral_opb_percent2.sort_values(ascending=True).round(2)

    plot_df16 = collateral_opb_percent2.reset_index()
    plot_df16.columns = ['Collateral Type Description', 'NPL Share (%)']

    fig16 = px.bar(
        plot_df16,
        x='NPL Share (%)',
        y='Collateral Type Description',
        color='NPL Share (%)',
        color_continuous_scale='Cividis',
        orientation='h',
        text=plot_df16['NPL Share (%)'].astype(str) + '%')

    fig16.update_traces(textposition='outside')
    fig16.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig16, use_container_width=True)


cl15, cl16 = st.columns((2))

with cl15:
    with st.expander("NPL by Collateral Type"):
        npa_count6 = filtered_df_cutoff[filtered_df_cutoff["Area Code"] == "NPA"].groupby(by=["Collateral Type"], as_index=False)["Area Code"].count()
        npa_sum6 = filtered_df_cutoff.groupby(by=["Collateral Type"], as_index=False)["NPA"].sum()

        lgroup15 = pd.merge(npa_count6, npa_sum6, on="Collateral Type", how="left")
        lgroup15.rename(columns={
            "Collateral Type": "Collateral Type",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        lgroup15["Total NPL (₱)"] = lgroup15["Total NPL (₱)"].replace({'₱': '', ',': ''}, regex=True).astype(float)
        lgroup15 = lgroup15.sort_values(by="Total NPL (₱)", ascending=False)
        lgroup15["Total NPL (₱)"] = lgroup15["Total NPL (₱)"].apply(lambda x: f"₱{x:,.2f}")

        st.table(lgroup15)
        csv_df15 = pd.merge(npa_count6, npa_sum6, on="Collateral Type", how="left")

        csv_df15.rename(columns={
            "Collateral Type": "Collateral Type",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        csv15 = csv_df15.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv15,
            file_name="NPL Collateral Type.csv",
            mime="text/csv",
            help="Click here to download the CSV file"
        )

with cl16:
    with st.expander("NPL by Collateral Type Description"):
        values_to_drop4 = ["(blank)", "OTHERS COLLATERAL", "OTHERS/UNSECURED"]
        filtered_df_cutoff_clean4 = filtered_df_cutoff[~filtered_df_cutoff["Collateral Type Description"].isin(values_to_drop4)]


        npa_count7 = filtered_df_cutoff_clean4[filtered_df_cutoff["Area Code"] == "NPA"].groupby(by=["Collateral Type Description"], as_index=False)["Area Code"].count()
        npa_sum7 = filtered_df_cutoff.groupby(by=["Collateral Type Description"], as_index=False)["NPA"].sum()

        lgroup16 = pd.merge(npa_count7, npa_sum7, on="Collateral Type Description", how="left")
        lgroup16.rename(columns={
            "Collateral Type Description": "Collateral Type Description",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        lgroup16["Total NPL (₱)"] = lgroup16["Total NPL (₱)"].replace({'₱': '', ',': ''}, regex=True).astype(float)
        lgroup16 = lgroup16.sort_values(by="Total NPL (₱)", ascending=False)
        lgroup16["Total NPL (₱)"] = lgroup16["Total NPL (₱)"].apply(lambda x: f"₱{x:,.2f}")

        st.table(lgroup16)
        csv_df16 = pd.merge(npa_count7, npa_sum7, on="Collateral Type Description", how="left")

        csv_df16.rename(columns={
            "Collateral Type Description": "Collateral Type Description",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        csv16 = csv_df16.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv16,
            file_name="NPL Collateral Type Desc.csv",
            mime="text/csv",
            help="Click here to download the CSV file"
        )


st.subheader(f"Hierarchical view of NPL per Region - CY {formatted_year_string}")
filtered_df_cutoff["Formatted Value_NP"] = filtered_df_cutoff["NPA"].apply(lambda x: f"₱{x:,.0f}")
filtered_df_cutoff["Custom Text"] = filtered_df_cutoff["Region"] + "<br>" + filtered_df_cutoff["Formatted Value_NP"]

fig17 = px.treemap(
    filtered_df_cutoff,
    path=["YEAR", "Region"],
    values="NPA",
    hover_data={"NPA": ":,.0f"},
    color="Region",
)

fig17.update_traces(
    textinfo="label+value+percent parent",
    texttemplate="%{label}<br>₱%{value:,.0f}<br>%{percentParent:.2%}",
    hovertemplate="<b>%{label}</b><br>Amount: ₱%{value:,.0f}<br>Parent Share: %{percentParent:.2%}<extra></extra>",
    textfont=dict(size=16)
)
st.plotly_chart(fig17, use_container_width=True)

c19, c20 = st.columns((2))

with c19:
    st.subheader(f"NPL by Facility/Product - CY {formatted_year_string}")
    filtered_df_cutoff["Formatted Value_NP19"] = filtered_df_cutoff["NPA"].apply(lambda x: f"₱{x:,.0f}")
    filtered_df_cutoff["Custom Text_NP19"] = filtered_df_cutoff["Type of Facility"] + "<br>" + filtered_df_cutoff["Formatted Value_NP19"]

    fig19 = px.treemap(
        filtered_df_cutoff,
        path=["YEAR", "Type of Facility"],
        values="NPA",
        hover_data={"NPA": ":,.0f"},
        color="Type of Facility",
        color_discrete_sequence=px.colors.qualitative.D3
    )

    fig19.update_traces(
        textinfo="label+value+percent parent",
        texttemplate="%{label}<br>₱%{value:,.0f}<br>%{percentParent:.2%}",
        hovertemplate="<b>%{label}</b><br>Amount: ₱%{value:,.0f}<br>Parent Share: %{percentParent:.2%}<extra></extra>",
        textfont=dict(size=16)
    )
    st.plotly_chart(fig19, use_container_width=True)

with c20:
    st.subheader(f"Loan Portfolio by Account Class - CY {formatted_year_string}")
    filtered_df_cutoff["Formatted Value_NP20"] = filtered_df_cutoff["NPA"].apply(lambda x: f"₱{x:,.0f}")
    filtered_df_cutoff["Custom Text_NP20"] = filtered_df_cutoff["Account Class"] + "<br>" + filtered_df_cutoff["Formatted Value_NP20"]

    fig20 = px.treemap(
        filtered_df_cutoff,
        path=["YEAR", "Account Class"],
        values="NPA",
        hover_data={"NPA": ":,.0f"},
        color="Account Class",
        color_discrete_sequence=px.colors.qualitative.Set3    )

    fig20.update_traces(
        textinfo="label+value+percent parent",
        texttemplate="%{label}<br>₱%{value:,.0f}<br>%{percentParent:.2%}",
        hovertemplate="<b>%{label}</b><br>Amount: ₱%{value:,.0f}<br>Parent Share: %{percentParent:.2%}<extra></extra>",
        textfont=dict(size=16)
    )
    st.plotly_chart(fig20, use_container_width=True)


cl21, cl22 = st.columns((2))

with cl21:
    with st.expander("NPL by Facility"):
        npa_count9 = filtered_df_cutoff[filtered_df_cutoff["Area Code"] == "NPA"].groupby(by=["Type of Facility"], as_index=False)["Area Code"].count()
        npa_sum9 = filtered_df_cutoff.groupby(by=["Type of Facility"], as_index=False)["NPA"].sum()

        lgroup21 = pd.merge(npa_count9, npa_sum9, on="Type of Facility", how="left")
        lgroup21.rename(columns={
            "Type of Facility": "Type of Facility",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        lgroup21["Total NPL (₱)"] = lgroup21["Total NPL (₱)"].replace({'₱': '', ',': ''}, regex=True).astype(float)
        lgroup21 = lgroup21.sort_values(by="Total NPL (₱)", ascending=False)
        lgroup21["Total NPL (₱)"] = lgroup21["Total NPL (₱)"].apply(lambda x: f"₱{x:,.2f}")

        st.table(lgroup21)
        csv_df21 = pd.merge(npa_count9, npa_sum9, on="Type of Facility", how="left")

        csv_df21.rename(columns={
            "Type of Facility": "Type of Facility",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        csv21 = csv_df21.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv21,
            file_name="NPL Facility.csv",
            mime="text/csv",
            help="Click here to download the CSV file"
        )

with cl22:
    with st.expander("NPL by Account Class"):
        npa_count10 = filtered_df_cutoff[filtered_df_cutoff["Area Code"] == "NPA"].groupby(by=["Account Class"], as_index=False)["Area Code"].count()
        npa_sum10 = filtered_df_cutoff.groupby(by=["Account Class"], as_index=False)["NPA"].sum()

        lgroup22 = pd.merge(npa_count10, npa_sum10, on="Account Class", how="left")
        lgroup22.rename(columns={
            "Account Class": "Account Class",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        lgroup22["Total NPL (₱)"] = lgroup22["Total NPL (₱)"].replace({'₱': '', ',': ''}, regex=True).astype(float)
        lgroup22 = lgroup22.sort_values(by="Total NPL (₱)", ascending=False)
        lgroup22["Total NPL (₱)"] = lgroup22["Total NPL (₱)"].apply(lambda x: f"₱{x:,.2f}")

        st.table(lgroup22)
        csv_df22 = pd.merge(npa_count10, npa_sum10, on="Account Class", how="left")

        csv_df22.rename(columns={
            "Account Class": "Account Classification (BRR)",
            "Area Code": "No. of NPA Records",
            "NPA": "Total NPL (₱)",
        }, inplace=True)

        csv22 = csv_df22.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Data",
            data=csv22,
            file_name="NPL Account Class.csv",
            mime="text/csv",
            help="Click here to download the CSV file"
        )


