import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd
import numpy as np 
from dateutil import parser
import os
import isodate
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="YT Calls Dashboard", page_icon=":phone:",layout="wide")

st.title(" :phone: Call Center Call Logs Analysis")
#st.markdown('<style>div.block-container{padding-top:1rem;}</style>',unsafe_allow_html=True)

# Function to read the file and return the DataFrame
def read_file(file):
    if file is not None:
        filename = file.name
        st.write(filename)
        return pd.read_csv(file, encoding="ISO-8859-1")
    else:
        return pd.read_csv("Call log (2023).csv", encoding="ISO-8859-1")

# Sidebar section
with st.sidebar:
    st.title("Please upload the file for analysis")
    fl = st.file_uploader(":file_folder: Upload a file", type=(["csv", "txt", "xlsx", "xls"]))

# Main section

df = read_file(fl)

df['Time'] =  df['Time'].apply(lambda x: parser.parse(x)) 
df['Date'] = df['Time'].dt.date
df["Date"] = pd.to_datetime(df["Date"])

# Assuming 'duration' column contains strings in the format '00:02:27'
df['durationSecs'] = df['Call Duration'].apply(lambda x: datetime.strptime(x, "%H:%M:%S").time())
df['CallonMinutes'] = df['durationSecs'].apply(lambda x: x.minute + x.second / 60)

# Assuming 'duration' column contains strings in the format '00:02:27'
df['TalkonSecs'] = df['Talk Duration'].apply(lambda x: datetime.strptime(x, "%H:%M:%S").time())
df['TalkonMinutes'] = df['TalkonSecs'].apply(lambda x: x.minute + x.second / 60)

#fill none value in 1
df['Caller Name'].fillna(1, inplace=True)
df['Callee Name'].fillna(1, inplace=True)

#create date column
df['DayName'] = df['Time'].apply(lambda x: x.strftime("%A")) 
df['MonthName'] = df['Time'].dt.strftime("%B")

category_mapping = {'Inbound': 'Inbound', 'Internal': 'Internal', 'Outbound': 'Outbound','Transfer':'Inbound'}

# Apply the mapping to the 'Category' column
df['Communication Type'] = df['Communication Type'].map(category_mapping)

# Replace 'to_be_dropped' with the specific value you want to drop
value_to_drop = 'Internal'

# Create a boolean mask for rows where the 'Category' column is not equal to the value to drop
mask = df['Communication Type'] != value_to_drop

# Use the boolean mask to filter the DataFrame and keep only rows where 'Category' is not equal to the value to drop
df = df[mask]

col1, col2 = st.columns((2))
# Getting the min and max date 
startDate = pd.to_datetime(df["Date"]).min()
endDate = pd.to_datetime(df["Date"]).max()

with col1:
    date1 = pd.to_datetime(st.date_input("Start Date", startDate))

with col2:
    date2 = pd.to_datetime(st.date_input("End Date", endDate))

df = df[(df["Date"] >= date1) & (df["Date"] <= date2)].copy()

col1, col2, col3 = st.columns(3)

total_patients = df['Caller Name'].count()
inbound_calls = df[df['Communication Type'] == 'Inbound'].shape[0]
outbound_calls = df[df['Communication Type'] == 'Outbound'].shape[0]

# Assigning colors based on the values (you can customize these colors)
color_total_patients = "blue" if total_patients > 0 else "black"
color_inbound_calls = "green" if inbound_calls > 0 else "black"
color_outbound_calls = "orange" if outbound_calls > 0 else "black"

# Emoji Unicode characters
emoji_patient = "👥"
emoji_inbound = "📥"
emoji_outbound = "📤"

# Display metrics with Markdown for color and emojis
col1.markdown(f"<font color='{color_total_patients}'>**{emoji_patient} Patient:** {total_patients}</font>", unsafe_allow_html=True)
col2.markdown(f"<font color='{color_inbound_calls}'>**{emoji_inbound} Inbound:** {inbound_calls}</font>", unsafe_allow_html=True)
col3.markdown(f"<font color='{color_outbound_calls}'>**{emoji_outbound} Outbound:** {outbound_calls}</font>", unsafe_allow_html=True)


col1, col2 = st.columns((2))
with col1:
    # Assuming df is your DataFrame
    df_all_months = df[df['MonthName'].isin(['January', 'February', 'March', 'April', 'May', 'June', 'July','August','September','October','November','December'])]

    # Set 'DayName' to a categorical type with custom order
    custom_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July','August','September','October','November','December']
    df_all_months['MonthName'] = pd.Categorical(df_all_months['MonthName'], categories=custom_order, ordered=True)

    # Group by 'MonthName' and 'Communication Type', reset index to bring the grouped columns back
    grouped_df = df_all_months.groupby(['MonthName', 'Communication Type'])['Caller Name'].count().reset_index()

    # Create the bar chart with Plotly Express
    fig = px.bar(grouped_df,
                x='MonthName',
                y='Caller Name',
                color='Communication Type',
                labels={'Caller Name': 'Count'},
                title='Communication Type Count by Month',
                )
    st.plotly_chart(fig,use_container_width=True, height = 200)

with col2:
    fig = px.pie(df.groupby('Communication Type')['Caller Name'].count().reset_index(),
             names='Communication Type',
             values='Caller Name',
             title='Inbound & Outbound by Percentage',
             hole = 0.5)
    fig.update_traces(text = df["Communication Type"], textposition = "outside")
    st.plotly_chart(fig,use_container_width=True)

col1, col2 = st.columns((2))
with col1:
    fig = px.bar(df.groupby('Status')['Caller Name'].count().reset_index(),
             x='Status',
             y='Caller Name',
             color='Status',
             title='Call Status'
             )
    st.plotly_chart(fig,use_container_width=True, height = 200)

with col2:
    fig = px.pie(df.groupby('Status')['Caller Name'].count().reset_index(),
             names='Status',
             values='Caller Name',
             title='Status by Percentage',
             hole = 0.5)
    #fig.update_traces(text = df["Status"], textposition = "outside")
    st.plotly_chart(fig,use_container_width=True)

col1, col2 = st.columns((2))
with col1:
    # Assuming df is your DataFrame
    df['Hour'] = df['Time'].dt.hour
    fig = go.Figure()
    fig.add_trace(go.Heatmap(
    x=df['Hour'].value_counts().sort_index().index,
    y=['Count'],
    z=[df['Hour'].value_counts().sort_index().values],
    colorscale='Reds',  # You can choose a different colorscale
    colorbar=dict(title='Count'),
))

    fig.update_layout(title="Call Hours Count",
    xaxis_title="Hour of Day",
    yaxis_title="",
    yaxis=dict(showticklabels=False),  # Hide y-axis labels
)

    # Show the plot
    st.plotly_chart(fig, use_container_width=True)

with col2:
    df_all_days = df[df['DayName'].isin(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])]

    # Set 'DayName' to a categorical type with custom order
    custom_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df_all_days['DayName'] = pd.Categorical(df_all_days['DayName'], categories=custom_order, ordered=True)

    # Create a line chart with Plotly graph_objects
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_all_days['DayName'].value_counts().sort_index().index,
        y=df_all_days['DayName'].value_counts().sort_index().values,
        mode='lines+markers',
        line=dict(color='green'),
        marker=dict(color='green', size=8),
        text=df_all_days['Hour'].value_counts().sort_index().values,
        textposition='top center',  # Adjust text position here
    ))

    fig.update_layout(title="Call Days Count",
        xaxis_title="Day",
        yaxis_title="Count",
        xaxis=dict(tickvals=list(range(7))),
        showlegend=False
    )

    # Show the plot
    st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns((2))
with col1:
    # Assuming df is your DataFrame
    filtered_df = df[df['Communication Type'] == 'Inbound']
    tb = filtered_df.groupby('TalkonMinutes').size().reset_index(name='Count')

    # Create the histogram with Plotly Express
    fig = px.histogram(tb, x="TalkonMinutes", nbins=100, title="Histogram of Inbound Durations")
    fig.update_layout(title_text="Histogram of Inbound Durations")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Assuming df is your DataFrame
    filtered_df = df[df['Communication Type'] == 'Outbound']
    tb = filtered_df.groupby('TalkonMinutes').size().reset_index(name='Count')

    # Create the histogram with Plotly Express
    fig = px.histogram(tb, x="TalkonMinutes", nbins=100, title="Histogram of Outbound Durations")
    fig.update_layout(title_text="Histogram of Outbound Durations")
    st.plotly_chart(fig, use_container_width=True)