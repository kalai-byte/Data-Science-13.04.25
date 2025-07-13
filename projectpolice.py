import pandas as pd
import streamlit as st
import psycopg2 as ps
sheet_id='16qEUKckLFy7j1qoSd1bSQURn9QXDb6ffSBAWzRkPsSg'
sheet_name='Sheet1'
url  = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
traffic_df = pd.read_csv(url, low_memory=False)
db_url= 'postgresql://kalai_online:zo0qcDMN4PGM84TQMWbAE2aQc6V2S8AA@dpg-d1l43iqdbo4c73aki3g0-a.singapore-postgres.render.com/traffic_stops'
from sqlalchemy import create_engine,inspect
engine=create_engine(db_url)


try:
    con = ps.connect(
        dbname="kalaidbpro",  
        user="kalai_online",
        password="zo0qcDMN4PGM84TQMWbAE2aQc6V2S8AA",
        port="5432",
        host="dpg-d1l43iqdbo4c73aki3g0-a.singapore-postgres.render.com"
       
    )
    print("Connected successfully")
except Exception as e:
    print("Connection failed:", e)


st.set_page_config(page_title=" Police Dashboard")

#Data Cleaning

traffic_df.dropna(axis=1, how='all', inplace=True)

traffic_df.fillna({
    'driver_age': traffic_df['driver_age'].median(),
    'search_type': 'None',
    'stop_duration':'unknown',
    'violation':'unknown',
    'stop_outcome':'unknown',
}, inplace=True)


traffic_df['timestamp'] = pd.to_datetime(traffic_df['stop_date'] +' '+ traffic_df['stop_time'])
traffic_df['stop_date']= pd.to_datetime(traffic_df['stop_date'], errors='coerce').dt.strftime('%Y-%m-%d')
traffic_df['stop_date']= pd.to_datetime(traffic_df['stop_date'], format='%H:%M:%S', errors='coerce').dt.strftime('H:%M:%S')

st.set_page_config(page_title=" Police Dashboard")


query_list = st.selectbox("Select a Query to Run", [
    "Total Number of  Stops"
    "Count of Stops by Violation Type",
    "Number of Arrests vs Warnings",
    "Average Age of Drivers Stopped",
    "Top 5 Most Frequent Search Types",
    "Count of Stops by Gender",
    "Most Common Violation for Arrests"
])

query_map = {
    "Total Number of  Stops": "SELECT COUNT(*) AS total_stops FROM traffic_stops",
    "Count of Stops by Violation Type": "SELECT violation, COUNT(*) AS count FROM traffic_stops GROUP BY violation ORDER BY count DESC",
    "Number of Arrests vs Warnings": "SELECT stop_outcome, COUNT(*) AS count FROM traffic_stops GROUP BY stop_outcome",
    "Average Age of Drivers Stopped": "SELECT AVG(driver_age) AS average_age FROM traffic_stops",
    "Top 5 Most Frequent Search Types": "SELECT search_type, COUNT(*) FROM traffic_stops WHERE search_type != '' GROUP BY search_type ORDER BY COUNT(*) DESC LIMIT 5",
    "Count of Stops by Gender": "SELECT driver_gender, COUNT(*) AS count FROM traffic_stops GROUP BY driver_gender",
    "Most Common Violation for Arrests": "SELECT violation, COUNT(*) AS count FROM traffic_stops WHERE stop_outcome LIKE '%arrest%' GROUP BY violation ORDER BY count DESC LIMIT 10"
}

if query_list:
    sql_query = query_map[query_list]
    result_df = pd.read_sql(sql_query, engine)
    st.subheader(query_list)
    st.dataframe(result_df)
