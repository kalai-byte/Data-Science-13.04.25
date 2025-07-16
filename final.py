import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import plotly.express as px

# --- Streamlit page Config ---
st.set_page_config(page_title="SecureCheck: Police Query Dashboard", layout="wide")

# --- Database Configuration  ---
db_link = 'postgresql://kalai_online:zo0qcDMN4PGM84TQMWbAE2aQc6V2S8AA@dpg-d1l43iqdbo4c73aki3g0-a.singapore-postgres.render.com/traffic_stops'
engine = create_engine(db_link)

# --- SQL Connection ---
def run_query(sql: str):
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)

# --- Streamlit Config ---
st.markdown("""
    <h1 style='text-align: center; color: #FF6347;'>🚓 SecureCheck: Police Query Dashboard</h1>
    <hr style='border: 1px solid #aaa;'>
    <p style='text-align: center; font-size:18px;'>Explore insights from traffic stop data using SQL-powered analysis.</p>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st.image("C:/Users/kalai/Downloads/traffic_stops/Police1.jpg", use_container_width=True)

with col2:
    st.image ("C:/Users/kalai/Downloads/traffic_stops/Police3.jpg", use_container_width=True)

st.sidebar.header("🔍 Query Explorer")
query_group = st.sidebar.selectbox("Choose Category", [
    "Vehicle-Based", "Demographic-Based", "Time-Based", "Violation-Based", "Location-Based", "Complex Queries"])

# --- Query Mapping ---
queries = {
    "Vehicle-Based": {
        "Top 10 Drug-Related Vehicles": """
            SELECT vehicle_number, COUNT(*) AS count
            FROM traffic_stops
            WHERE drugs_related_stop = TRUE
            GROUP BY vehicle_number
            ORDER BY count DESC
            LIMIT 10;
        """,
        "Most Frequently Searched Vehicles": """
            SELECT vehicle_number, COUNT(*) AS count
            FROM traffic_stops
            WHERE search_conducted = TRUE
            GROUP BY vehicle_number
            ORDER BY count DESC;
        """
    },
    "Demographic-Based": {
        "Highest Arrest Rate by Age Group": """
            SELECT CASE
                WHEN driver_age < 18 THEN '<18'
                WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
                WHEN driver_age BETWEEN 26 AND 40 THEN '26-40'
                WHEN driver_age BETWEEN 41 AND 60 THEN '41-60'
                ELSE '60+'
            END AS age_group,
            COUNT(*) FILTER (WHERE stop_outcome ILIKE '%arrest%')::float / COUNT(*) AS arrest_rate
            FROM traffic_stops
            GROUP BY age_group
            ORDER BY arrest_rate DESC;
        """,
        "Gender Distribution by Country": """
            SELECT country_name, driver_gender, COUNT(*) AS total_stops
            FROM traffic_stops
            GROUP BY country_name, driver_gender
            ORDER BY country_name;
        """,
        "Highest Search Rate (Race + Gender)": """
            SELECT driver_race, driver_gender,
            COUNT(*) FILTER (WHERE search_conducted = TRUE)::float / COUNT(*) AS search_rate
            FROM traffic_stops
            GROUP BY driver_race, driver_gender
            ORDER BY search_rate DESC
            LIMIT 1;
        """
    },
    "Time-Based": {
        "Time of Day with Most Stops": """
            SELECT CASE
                WHEN EXTRACT(HOUR FROM stop_time::time) BETWEEN 0 AND 5 THEN 'Midnight (12AM-6AM)'
                WHEN EXTRACT(HOUR FROM stop_time::time) BETWEEN 6 AND 11 THEN 'Morning (6AM-12PM)'
                WHEN EXTRACT(HOUR FROM stop_time::time) BETWEEN 12 AND 17 THEN 'Afternoon (12PM-6PM)'
                ELSE 'Evening (6PM-12AM)'
            END AS time_period,
            COUNT(*) AS stop_count
            FROM traffic_stops
            GROUP BY time_period
            ORDER BY stop_count DESC;
        """,
        "Average Stop Duration by Violation": """
            SELECT violation,
            AVG(CASE
                WHEN stop_duration ILIKE '%0-15%' THEN 7.5
                WHEN stop_duration ILIKE '%16-30%' THEN 23
                WHEN stop_duration ILIKE '%30+%' THEN 45
                ELSE NULL
            END) AS avg_duration
            FROM traffic_stops
            GROUP BY violation;
        """,
        "Are Night Stops More Likely Arrests": """
            SELECT CASE
                WHEN EXTRACT(HOUR FROM stop_time::time) BETWEEN 0 AND 5 THEN 'Night'
                ELSE 'Day'
            END AS period,
            COUNT(*) FILTER (WHERE stop_outcome ILIKE '%arrest%')::float / COUNT(*) AS arrest_rate
            FROM traffic_stops
            GROUP BY period;
        """
    },
    "Violation-Based": {
        "Violations Leading to Search or Arrest": """
            SELECT violation,
            COUNT(*) FILTER (WHERE search_conducted = TRUE OR stop_outcome ILIKE '%arrest%') AS flagged,
            COUNT(*) AS total,
            ROUND((COUNT(*) FILTER (WHERE search_conducted = TRUE OR stop_outcome ILIKE '%arrest%')::numeric / COUNT(*)) * 100, 2) AS rate_percent
            FROM traffic_stops
            GROUP BY violation
            ORDER BY rate_percent DESC;
        """,
        "Most Common Violations for Under 25": """
            SELECT violation, COUNT(*) AS total
            FROM traffic_stops
            WHERE driver_age < 25
            GROUP BY violation
            ORDER BY total DESC;
        """,
        "Violations Rarely Leading to Search/Arrest": """
            SELECT violation,
            COUNT(*) FILTER (WHERE search_conducted = TRUE OR stop_outcome ILIKE '%arrest%') AS flagged,
            COUNT(*) AS total,
            ROUND((COUNT(*) FILTER (WHERE search_conducted = TRUE OR stop_outcome ILIKE '%arrest%')::numeric / COUNT(*)) * 100, 2) AS rate_percent
            FROM traffic_stops
            GROUP BY violation
            HAVING COUNT(*) > 5
            ORDER BY rate_percent ASC
            LIMIT 5;
        """
    },
    "Location-Based": {
        "Highest Drug-Related Stop Rate by Country": """
            SELECT country_name,
            COUNT(*) FILTER (WHERE drugs_related_stop = TRUE)::float / COUNT(*) AS drug_rate
            FROM traffic_stops
            GROUP BY country_name
            ORDER BY drug_rate DESC;
        """,
        "Arrest Rate by Country & Violation": """
            SELECT country_name, violation,
            COUNT(*) FILTER (WHERE stop_outcome ILIKE '%arrest%')::float / COUNT(*) AS arrest_rate
            FROM traffic_stops
            GROUP BY country_name, violation
            ORDER BY arrest_rate DESC;
        """,
        "Country with Most Searches Conducted": """
            SELECT country_name, COUNT(*) AS searches
            FROM traffic_stops
            WHERE search_conducted = TRUE
            GROUP BY country_name
            ORDER BY searches DESC
            LIMIT 1;
        """
    },
    "Complex Queries": {
        "Yearly Arrest Trends by Country": """
            SELECT country_name,
            EXTRACT(YEAR FROM stop_date::DATE) AS year,
            COUNT(*) AS total,
            COUNT(*) FILTER (WHERE stop_outcome ILIKE '%arrest%') AS arrests,
            ROUND(100.0 * COUNT(*) FILTER (WHERE stop_outcome ILIKE '%arrest%') / COUNT(*), 2) AS arrest_rate
            FROM traffic_stops
            WHERE stop_date IS NOT NULL
            GROUP BY country_name, year
            ORDER BY year, arrest_rate DESC;
        """,
        "Violation Trends by Age and Race": """
            SELECT driver_age, driver_race, violation, COUNT(*) AS count
            FROM traffic_stops
            WHERE driver_age IS NOT NULL AND driver_race IS NOT NULL
            GROUP BY driver_age, driver_race, violation
            ORDER BY count DESC LIMIT 100;
        """,
        "Time Period Analysis": """
            SELECT 
            EXTRACT(YEAR FROM stop_date::date) AS year,
            TO_CHAR(stop_date::date, 'Month') AS month,
            EXTRACT(HOUR FROM stop_time::time) AS hour_of_day,
            COUNT(*) AS stop_count
            FROM traffic_stops
            WHERE stop_date IS NOT NULL AND stop_time IS NOT NULL
            GROUP BY year, month, hour_of_day
            ORDER BY year, month, hour_of_day;

       """,
        "Violations with search and arrest": """SELECT
            violation,
            COUNT(*) AS total_stops,
            COUNT(*) FILTER (WHERE search_conducted = TRUE) AS total_searches,
            COUNT(*) FILTER (WHERE stop_outcome ILIKE '%arrest%') AS total_arrests,
            ROUND(100.0 * COUNT(*) FILTER (WHERE search_conducted = TRUE) / COUNT(*), 2) AS search_rate_percent,
            ROUND(100.0 * COUNT(*) FILTER (WHERE stop_outcome ILIKE '%arrest%') / COUNT(*), 2) AS arrest_rate_percent,
            RANK() OVER (ORDER BY COUNT(*) FILTER (WHERE search_conducted = TRUE) * 1.0 / NULLIF(COUNT(*), 0) DESC) AS search_rank,
            RANK() OVER (ORDER BY COUNT(*) FILTER (WHERE stop_outcome ILIKE '%arrest%') * 1.0 / NULLIF(COUNT(*), 0) DESC) AS arrest_rank
            FROM traffic_stops
            GROUP BY violation
            HAVING COUNT(*) > 10
            ORDER BY search_rate_percent DESC, arrest_rate_percent DESC;
       """,
        "Driver Demographics": """SELECT
            country_name,
            driver_gender,
            driver_race,
            CASE
            WHEN driver_age < 18 THEN '<18'
            WHEN driver_age BETWEEN 18 AND 25 THEN '18-25'
            WHEN driver_age BETWEEN 26 AND 40 THEN '26-40'
            WHEN driver_age BETWEEN 41 AND 60 THEN '41-60'
            ELSE '60+'
            END AS age_group,
            COUNT(*) AS total_stops
            FROM traffic_stops
            WHERE country_name IS NOT NULL
            AND driver_gender IS NOT NULL
            AND driver_race IS NOT NULL
            AND driver_age IS NOT NULL
            GROUP BY country_name, driver_gender, driver_race, age_group
            ORDER BY country_name, total_stops DESC;
            """,
        "Top 5 Violations with Highest Arrest Rates":"""SELECT
            violation,
            COUNT(*) AS total_stops,
            COUNT(*) FILTER (WHERE stop_outcome ILIKE '%arrest%') AS total_arrests,
            ROUND(
            100.0 * COUNT(*) FILTER (WHERE stop_outcome ILIKE '%arrest%') / NULLIF(COUNT(*), 0), 2) AS arrest_rate_percent
            FROM traffic_stops
            WHERE violation IS NOT NULL AND stop_outcome IS NOT NULL
            GROUP BY violation
            HAVING COUNT(*) > 10  -- to avoid misleading rates on rare violations
            ORDER BY arrest_rate_percent DESC
            LIMIT 5;"""
    }
}

# --- Streamlit Execution ---
selected_query = st.selectbox("Choose Query", list(queries[query_group].keys()))
if st.button("Run Query"):
    
    try:
        sql = queries[query_group][selected_query]
        result = run_query(sql)
        if not result.empty:
            st.success("Query executed successfully!")
            st.dataframe(result, use_container_width=True)
            if 'count' in result.columns or 'total' in result.columns:
               count_col = 'count' if 'count' in result.columns else 'total'
               fig = px.bar(result, x=result.columns[0], y=count_col, color=result.columns[0], title="Query Visualization")
               st.plotly_chart(fig, use_container_width=True)
            csv = result.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download as CSV", csv, "query_results.csv", "text/csv")
        else:
            st.info("No results found for this query.")
    except Exception as e:
        st.error("An error occurred while executing the query.")
        st.code(str(e))


