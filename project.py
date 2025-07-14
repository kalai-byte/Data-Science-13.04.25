import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine, text

# --- Database Configuration ---
db_con = 'postgresql://kalai_online:zo0qcDMN4PGM84TQMWbAE2aQc6V2S8AA@dpg-d1l43iqdbo4c73aki3g0-a.singapore-postgres.render.com/traffic_stops'
db_engine = create_engine(db_con )

# --- Utility Functions ---
def fetch_data(query, params=None):
    with db_engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params) if params else pd.read_sql(text(query), conn)

def fetch_scalar(query, params=None):
    with db_engine.connect() as conn:
        return conn.execute(text(query), params).scalar() if params else conn.execute(text(query)).scalar()

# --- Page Setup ---
st.set_page_config(page_title="Traffic Dashboard", layout="wide")
st.markdown("""
<h1 style='text-align: center; color: #B22222;'>🚦 Police Traffic Dashboard 🚓</h1>
""", unsafe_allow_html=True)

# --- Header Images ---
#columns = st.columns(3)
#for idx, img in enumerate(["STOP1.JPEG", "STOP2.JPEG", "STOP3.JPEG"]):
   # with columns[idx]:
      # st.image(f"C:/Users/kalai/Downloads/traffic_stops/{img}", use_container_width=True)


# --- Sidebar ---
view_option = st.sidebar.selectbox("Choose View", ["Vehicle Data", "Violation Summary", "Insights"])

# --- Section: Vehicle Data ---
if view_option == "Vehicle Data":
    st.subheader("Vehicle Logs")
    search_term = st.text_input("Enter Vehicle Number")
    vehicle_query = "SELECT * FROM traffic_stops WHERE vehicle_number ILIKE :term LIMIT 66000" if search_term else "SELECT * FROM traffic_stops LIMIT 66000"
    parameters = {"term": f"%{search_term}%"} if search_term else None
    st.dataframe(fetch_data(vehicle_query, parameters))

# --- Section: Violation Summary ---
elif view_option == "Violation Summary":
    st.subheader("Violation Breakdown")
    summary_query = "SELECT violation, COUNT(*) AS count FROM traffic_stops GROUP BY violation ORDER BY count DESC LIMIT 100"
    st.dataframe(fetch_data(summary_query))

# --- Section: Insights ---
elif view_option == "Insights":
    st.subheader("Trends & Demographics")
    insights_query = "SELECT violation, driver_gender FROM traffic_stops LIMIT 100"
    insights_data = fetch_data(insights_query)

    tab1, tab2 = st.tabs(["Violation Types", "Gender Distribution"])

    with tab1:
        if not insights_data.empty:
            v_data = insights_data['violation'].value_counts().reset_index(name='count')
            st.plotly_chart(px.bar(v_data, x='index', y='count', title='Violation Type Distribution'), use_container_width=True)

    with tab2:
        if not insights_data.empty:
            g_data = insights_data['driver_gender'].value_counts().reset_index(name='count')
            st.plotly_chart(px.bar(g_data, x='index', y='count', title='Gender Representation'), use_container_width=True)

# --- Overview Metrics ---
st.markdown("### Key Enforcement Stats")
metrics = st.columns(4)
try:
    metrics[0].metric("Total Stops", fetch_scalar("SELECT COUNT(*) FROM traffic_stops"))
    metrics[1].metric("Arrests", fetch_scalar("SELECT COUNT(*) FROM traffic_stops WHERE stop_outcome ILIKE '%arrest%'"))
    metrics[2].metric("Warnings", fetch_scalar("SELECT COUNT(*) FROM traffic_stops WHERE stop_outcome ILIKE '%warning%'"))
    metrics[3].metric("Drug Related", fetch_scalar("SELECT COUNT(*) FROM traffic_stops WHERE drugs_related_stop = TRUE"))
except Exception as err:
    st.error("Failed to load metrics")
    st.code(str(err))

# --- Intelligence Queries ---
st.markdown("### Traffic Intelligence Reports")
query_option = st.selectbox("Choose Query", [
    "Total Stops", "Violation Types", "Arrests vs Warnings", "Average Age",
    "Top Search Types", "Gender Distribution", "Top Violations for Arrests"
])
intelligence_queries = {
    "Total Stops": "SELECT COUNT(*) AS total FROM traffic_stops",
    "Violation Types": "SELECT violation, COUNT(*) FROM traffic_stops GROUP BY violation ORDER BY COUNT(*) DESC",
    "Arrests vs Warnings": "SELECT stop_outcome, COUNT(*) FROM traffic_stops GROUP BY stop_outcome",
    "Average Age": "SELECT AVG(driver_age) FROM traffic_stops",
    "Top Search Types": "SELECT search_type, COUNT(*) FROM traffic_stops WHERE search_type != '' GROUP BY search_type ORDER BY COUNT(*) DESC LIMIT 5",
    "Gender Distribution": "SELECT driver_gender, COUNT(*) FROM traffic_stops GROUP BY driver_gender",
    "Top Violations for Arrests": "SELECT violation, COUNT(*) FROM traffic_stops WHERE stop_outcome ILIKE '%arrest%' GROUP BY violation ORDER BY COUNT(*) DESC LIMIT 10"
}
if st.button("Execute Query"):
    st.dataframe(fetch_data(intelligence_queries[query_option]))
