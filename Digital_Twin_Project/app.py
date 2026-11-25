import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh

from monitor import SystemMonitor
from database import (
    init_database, insert_metrics, get_metrics, log_recommendation,
    log_event, get_recommendations, get_events,
)
from analytics import calculate_health, analyze_history, run_controlled_verification

st.set_page_config(page_title="Intelligent OS Digital Twin", page_icon="OS", layout="wide")

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background: #08111f; color: #edf4ff; }
[data-testid="stSidebar"] { background: #101c2e; border-right: 1px solid #22324a; }
[data-testid="stHeader"] { background: transparent; }
.metric-card, .panel { background: #111e31; border: 1px solid #263950; border-radius: 14px; padding: 16px; }
.metric-card h3 { margin: 0; color: #91a3ba; font-size: 14px; }
.metric-card h1 { margin: 5px 0 0; color: #f8fbff; font-size: 34px; }
.health-Healthy { color: #36d399; } .health-Warning { color: #fbbf24; } .health-Critical { color: #fb7185; }
small { color: #91a3ba; }
.stButton > button { border-radius: 8px; border: 1px solid #3867ff; color: #dbe5ff; }
</style>
""", unsafe_allow_html=True)

init_database()

if "monitor" not in st.session_state:
    st.session_state.monitor = SystemMonitor()
if "last_metrics" not in st.session_state:
    st.session_state.last_metrics = None

st.sidebar.title("OS Digital Twin")
st.sidebar.caption("Predictive Performance Analytics")
page = st.sidebar.radio("Navigation", ["Overview", "Module 1: Monitoring", "Module 2: Digital Twin", "Module 3: AI Analytics", "History"])
refresh_seconds = st.sidebar.slider("Refresh interval (seconds)", 2, 30, 5)
auto_refresh = st.sidebar.toggle("Enable live collection", value=True)

st.sidebar.divider()
st.sidebar.caption("SQLite database: digital_twin.db")

if auto_refresh:
    st_autorefresh(interval=refresh_seconds * 1000, key="system_refresh")

metrics = st.session_state.monitor.collect()
records = get_metrics(500)
known_health = records[-1]["health_status"] if records else "Healthy"
health = calculate_health(metrics)

if st.session_state.last_metrics is None or st.session_state.last_metrics["timestamp"] != metrics["timestamp"]:
    insert_metrics(metrics, health)
    if health != known_health:
        log_event("HEALTH_CHANGE", f"System health changed from {known_health} to {health}")
    st.session_state.last_metrics = metrics

records = get_metrics(500)
analysis = analyze_history(records)

def metric_card(title, value, detail=""):
    st.markdown(f'<div class="metric-card"><h3>{title}</h3><h1>{value}</h1><small>{detail}</small></div>', unsafe_allow_html=True)

st.title("Intelligent Self-Healing OS Digital Twin")
st.caption(f"{metrics['hostname']}  |  {metrics['platform']}  |  Live system synchronization")

if page == "Overview":
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: metric_card("CPU Usage", f"{metrics['cpu_percent']}%", "Processor load")
    with c2: metric_card("RAM Usage", f"{metrics['memory_percent']}%", f"{metrics['memory_used_gb']} / {metrics['memory_total_gb']} GB")
    with c3: metric_card("Disk Usage", f"{metrics['disk_percent']}%", f"{metrics['disk_used_gb']} / {metrics['disk_total_gb']} GB")
    with c4: metric_card("Network Received", f"{metrics['network_recv_kbps']} KB/s", "Live receive rate")
    with c5: metric_card("Risk Level", analysis["risk"], f"System health: {health}")

    st.divider()
    left, right = st.columns([2, 1])
    with left:
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        fig = px.line(df, x="timestamp", y=["cpu_percent", "memory_percent", "disk_percent"],
                      labels={"value": "Usage (%)", "timestamp": "Time", "variable": "Resource"},
                      template="plotly_dark", title="Live Resource Performance")
        fig.update_layout(paper_bgcolor="#0b1626", plot_bgcolor="#111e31", legend_title="")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown("### System Health")
        st.markdown(f'<h2 class="health-{health}">{health}</h2>', unsafe_allow_html=True)
        st.progress(min(int(metrics["cpu_percent"]), 100), text=f"CPU {metrics['cpu_percent']}%")
        st.progress(min(int(metrics["memory_percent"]), 100), text=f"Memory {metrics['memory_percent']}%")
        st.progress(min(int(metrics["disk_percent"]), 100), text=f"Disk {metrics['disk_percent']}%")
        st.metric("Running processes", metrics["process_count"])

elif page == "Module 1: Monitoring":
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("CPU", f"{metrics['cpu_percent']}%")
    with c2: metric_card("RAM", f"{metrics['memory_percent']}%")
    with c3: metric_card("Disk", f"{metrics['disk_percent']}%")
    with c4: metric_card("Processes", metrics["process_count"])

    c1, c2 = st.columns(2)
    with c1:
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        fig = px.line(df, x="timestamp", y=["cpu_percent", "memory_percent"], template="plotly_dark", title="CPU and Memory History")
        fig.update_layout(paper_bgcolor="#0b1626", plot_bgcolor="#111e31")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        fig = px.line(df, x="timestamp", y=["network_sent_kbps", "network_recv_kbps"], template="plotly_dark", title="Network Activity (KB/s)")
        fig.update_layout(paper_bgcolor="#0b1626", plot_bgcolor="#111e31")
        st.plotly_chart(fig, use_container_width=True)

    disk_left, disk_right = st.columns(2)
    with disk_left:
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        fig = px.line(df, x="timestamp", y=["disk_read_kbps", "disk_write_kbps"], template="plotly_dark", title="Disk Activity (KB/s)")
        fig.update_layout(paper_bgcolor="#0b1626", plot_bgcolor="#111e31")
        st.plotly_chart(fig, use_container_width=True)
    with disk_right:
        st.markdown("### Disk Capacity")
        st.metric("Used", f"{metrics['disk_used_gb']} GB")
        st.metric("Total", f"{metrics['disk_total_gb']} GB")

    cpu_table, memory_table = st.columns(2)
    with cpu_table:
        st.subheader("Top Processes by CPU")
        st.dataframe(pd.DataFrame(metrics["top_cpu_processes"]), use_container_width=True, hide_index=True)
    with memory_table:
        st.subheader("Top Processes by Memory")
        st.dataframe(pd.DataFrame(metrics["top_memory_processes"]), use_container_width=True, hide_index=True)

elif page == "Module 2: Digital Twin":
    st.subheader("Live Digital Twin Synchronization")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### Twin Processor")
        st.metric("Virtual CPU", f"{metrics['cpu_percent']}%", "Synced with host")
        st.progress(min(int(metrics["cpu_percent"]), 100))
    with c2:
        st.markdown("### Twin Memory")
        st.metric("Virtual RAM", f"{metrics['memory_percent']}%", f"{metrics['memory_used_gb']} GB used")
        st.progress(min(int(metrics["memory_percent"]), 100))
    with c3:
        st.markdown("### Twin Storage")
        st.metric("Virtual Disk", f"{metrics['disk_percent']}%", f"{metrics['disk_used_gb']} GB used")
        st.progress(min(int(metrics["disk_percent"]), 100))

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("### Network State")
        st.write(f"Sent: **{metrics['network_sent_kbps']} KB/s**")
        st.write(f"Received: **{metrics['network_recv_kbps']} KB/s**")
    with c2:
        st.markdown("### Process State")
        st.write(f"Running processes: **{metrics['process_count']}**")
    with c3:
        st.markdown("### Virtual Health")
        st.markdown(f'<h2 class="health-{health}">{health}</h2>', unsafe_allow_html=True)

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    fig = px.scatter(df, x="timestamp", y="cpu_percent", color="health_status", template="plotly_dark",
                     title="System State Changes", labels={"cpu_percent": "CPU Usage (%)"})
    fig.update_layout(paper_bgcolor="#0b1626", plot_bgcolor="#111e31")
    st.plotly_chart(fig, use_container_width=True)

elif page == "Module 3: AI Analytics":
    st.subheader("AI-Based Predictive Analytics Engine")
    c1, c2, c3 = st.columns(3)
    with c1: metric_card("Risk Level", analysis["risk"])
    with c2: metric_card("Anomaly Signals", len(analysis["anomalies"]))
    with c3: metric_card("Isolation Forest", "Active" if len(records) >= 10 else "Collecting")

    if analysis["anomalies"]:
        st.warning("|  ".join(item["message"] for item in analysis["anomalies"]))
    else:
        st.success("No abnormal CPU, memory, disk, or system state detected.")

    left, right = st.columns(2)
    with left:
        st.markdown("### 5-Sample Resource Forecast")
        if analysis["predictions"]:
            forecast_df = pd.DataFrame([
                {"Resource": name, "Predicted Usage (%)": values["value"], "Trend": values["trend"]}
                for name, values in analysis["predictions"].items()
            ])
            st.dataframe(forecast_df, use_container_width=True, hide_index=True)
            fig = px.bar(forecast_df, x="Resource", y="Predicted Usage (%)", color="Trend", template="plotly_dark")
            fig.update_layout(paper_bgcolor="#0b1626", plot_bgcolor="#111e31")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("More historical samples are needed for trend prediction.")

    with right:
        st.markdown("### Intelligent Recommendations")
        for recommendation in analysis["recommendations"]:
            st.write("• " + recommendation)

        if st.button("Acknowledge & verify recommendations"):
            before = records[-2] if len(records) >= 2 else None
            verification = run_controlled_verification(metrics, before)
            for recommendation in analysis["recommendations"]:
                log_recommendation(analysis["risk"], "Multiple", recommendation,
                                   "controlled-review", "acknowledged", verification)
            log_event("RECOMMENDATION_REVIEWED", "Safe recommendations acknowledged; no process was terminated.")
            st.success("Recommendations logged and verified. No process was changed.")

    st.info("Safety policy: this project never terminates processes or changes system settings automatically.")

elif page == "History":
    tab1, tab2, tab3 = st.tabs(["Metrics", "Recommendations", "Events"])
    with tab1:
        df = pd.DataFrame(records)
        if not df.empty:
            st.dataframe(df.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)
    with tab2:
        recs = get_recommendations()
        st.dataframe(pd.DataFrame(recs) if recs else pd.DataFrame(), use_container_width=True, hide_index=True)
    with tab3:
        events = get_events()
        st.dataframe(pd.DataFrame(events) if events else pd.DataFrame(), use_container_width=True, hide_index=True)
