# ==========================================================
# SALES OFFICER PERFORMANCE DASHBOARD
# Streamlit app — no login, no upload button. The dashboard
# simply reads the Excel file sitting in data/latest_report.xlsx.
# To refresh: replace that file locally, commit, push to GitHub —
# Streamlit Cloud redeploys and Boss's link shows the new data.
# ==========================================================
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

import data_processing as dp

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------
st.set_page_config(page_title="Sales Officer Dashboard", page_icon="📊", layout="wide")

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
LATEST_FILE = DATA_DIR / "latest_report.xlsx"

RED_FLAG_BELOW_PCT = dp.RED_FLAG_BELOW_PCT


# ------------------------------------------------------------
# STYLE HELPERS
# ------------------------------------------------------------
def highlight_pct_below(val, threshold=RED_FLAG_BELOW_PCT):
    try:
        if pd.isna(val):
            return ""
        if float(val) < threshold:
            return "background-color:#ffcccc;color:#7a0000;font-weight:600;"
    except (TypeError, ValueError):
        return ""
    return ""


def style_pct_columns(df, pct_cols):
    pct_cols = [c for c in pct_cols if c in df.columns]
    styler = df.style
    for c in pct_cols:
        styler = styler.map(highlight_pct_below, subset=[c])
    # Force integer display everywhere (no decimals), per requirement.
    fmt = {c: "{:.0f}" for c in df.select_dtypes(include="number").columns}
    styler = styler.format(fmt, na_rep="N/A")
    return styler


def kpi_card(col, label, value, suffix=""):
    col.metric(label, f"{value}{suffix}" if value is not None else "N/A")


# ------------------------------------------------------------
# LOAD DATA (from the file committed in data/latest_report.xlsx)
# ------------------------------------------------------------
st.title("📊 Sales Officer Performance Dashboard")

if LATEST_FILE.exists():
    mtime = pd.Timestamp.fromtimestamp(LATEST_FILE.stat().st_mtime)
    st.caption(f"📅 Last updated: {mtime.strftime('%d %b %Y, %I:%M %p')}")
else:
    st.warning(
        "কোনো রিপোর্ট পাওয়া যায়নি। `data/latest_report.xlsx` ফাইলটা রিপ্লেস করে "
        "GitHub-এ push করে নতুন করে deploy করুন।"
    )
    st.stop()

try:
    act, att, tgt = dp.load_workbook(LATEST_FILE)
    results = dp.build_all(act, att, tgt)
except dp.DashboardDataError as e:
    st.error(f"The saved report has a problem: {e}")
    st.stop()

if not dp.has_rsm_data(act):
    st.info(
        "ℹ️ The 'RSM' column is empty in this file, so RSM-wise views below are "
        "grouped by **Zone** instead. If your export starts including RSM names, "
        "this dashboard will automatically switch to grouping by RSM.",
        icon="ℹ️",
    )

master = results["master"]
group_col = results["group_col"]


# ------------------------------------------------------------
# SIDEBAR — FILTERS
# ------------------------------------------------------------
with st.sidebar:
    st.header("🔍 Filters")
    groups = sorted(master["Group"].dropna().unique().tolist())
    sel_groups = st.multiselect("Group / Sub Business", groups, default=groups)

    zones = sorted(master["Zone Name"].dropna().unique().tolist())
    sel_zones = st.multiselect("Zone", zones, default=[])

    so_search = st.text_input("Search Sales Officer name")

filtered_master = master[master["Group"].isin(sel_groups)] if sel_groups else master
if sel_zones:
    filtered_master = filtered_master[filtered_master["Zone Name"].isin(sel_zones)]
if so_search:
    filtered_master = filtered_master[
        filtered_master["Name"].str.contains(so_search, case=False, na=False)]

allowed_ids = set(filtered_master["Staff Id"])


def flt(df, id_col="Staff Id"):
    """Apply the sidebar SO filter to any per-SO dataframe."""
    if id_col not in df.columns or df.empty:
        return df
    return df[df[id_col].isin(allowed_ids)]


# ------------------------------------------------------------
# TOP-LEVEL KPIs
# ------------------------------------------------------------
outlet_perf = flt(results["outlet_perf"])
memo_perf = flt(results["memo_perf"])
att_summary = flt(results["attendance_summary"])

c1, c2, c3, c4, c5 = st.columns(5)
kpi_card(c1, "Total Sales Officers", len(filtered_master))
kpi_card(c2, "Avg Outlet Visit %",
         int(outlet_perf["Outlet Visit %"].mean()) if len(outlet_perf) else None, "%")
kpi_card(c3, "Avg Memo Performance",
         int(memo_perf["Memo Performance %"].mean()) if len(memo_perf) else None, "%")
kpi_card(c4, "Avg Present %",
         int(att_summary["Present %"].mean()) if len(att_summary) else None, "%")
kpi_card(c5, "Avg Late %",
         int(att_summary["Late %"].mean()) if len(att_summary) else None, "%")

st.divider()

tabs = st.tabs([
    "🏆 Performance & Leaderboard",
    "🗓️ Attendance & Punctuality",
    "🏪 Market Coverage",
    "🧭 Route & Repeat Visits",
    "📁 Raw Tables",
])


# ============================================================
# TAB 1 — PERFORMANCE & LEADERBOARD
# ============================================================
with tabs[0]:
    st.subheader("Group-wise Performance")
    group_wise = dp.group_wise_summary(outlet_perf, filtered_master)
    colA, colB = st.columns([1, 1])
    with colA:
        st.dataframe(style_pct_columns(group_wise, ["Avg Outlet Visit %"]),
                     width='stretch', hide_index=True)
    with colB:
        if len(group_wise):
            fig = px.bar(group_wise, x="Group", y="Avg Outlets/Day", color="Group",
                         title="Avg Outlets Visited / Day by Group", text="Avg Outlets/Day")
            st.plotly_chart(fig, width='stretch')

    st.subheader(f"🏆 Top 10 Good Performers (avg ≥ {dp.GOOD_PERFORMER_MIN_AVG_VISITS} outlets/day)")
    top10, bottom10 = dp.top_bottom_performers(outlet_perf, filtered_master)
    st.dataframe(style_pct_columns(top10, ["Outlet Visit %"]), width='stretch', hide_index=True)
    if len(top10):
        fig = px.bar(top10, x="Name", y="Avg Outlets/Day", color="Group",
                     title="Top Performers", text="Avg Outlets/Day")
        st.plotly_chart(fig, width='stretch')

    st.subheader(f"⚠️ Top 10 Bad Performers (avg < {dp.BAD_PERFORMER_MAX_AVG_VISITS} outlets/day)")
    st.dataframe(style_pct_columns(bottom10, ["Outlet Visit %"]), width='stretch', hide_index=True)
    if len(bottom10):
        fig = px.bar(bottom10, x="Name", y="Avg Outlets/Day", color="Group",
                     title="Bad Performers", text="Avg Outlets/Day",
                     color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig, width='stretch')

    st.subheader(f"🧭 {group_col}-wise Top & Least Performer")
    rsm_top, rsm_bottom = dp.rsm_wise_top_bottom(outlet_perf, filtered_master, group_col)
    colC, colD = st.columns(2)
    with colC:
        st.caption("Top performer per " + group_col)
        st.dataframe(style_pct_columns(rsm_top, ["Outlet Visit %"]), width='stretch', hide_index=True)
        if len(rsm_top):
            fig = px.bar(rsm_top, x=group_col, y="Avg Outlets/Day", title=f"Top SO by {group_col}")
            st.plotly_chart(fig, width='stretch')
    with colD:
        st.caption("Least performer per " + group_col)
        st.dataframe(style_pct_columns(rsm_bottom, ["Outlet Visit %"]), width='stretch', hide_index=True)
        if len(rsm_bottom):
            fig = px.bar(rsm_bottom, x=group_col, y="Avg Outlets/Day", title=f"Least Performer by {group_col}",
                         color_discrete_sequence=["indianred"])
            st.plotly_chart(fig, width='stretch')


# ============================================================
# TAB 2 — ATTENDANCE & PUNCTUALITY
# ============================================================
with tabs[1]:
    st.subheader("Late Count & Attendance Summary")
    att_display = att_summary.merge(filtered_master[["Staff Id", "Name", "Group", "Zone Name"]],
                                     on="Staff Id", how="left")
    att_display = att_display.sort_values("Late %", ascending=False)
    show_cols = ["Staff Id", "Name", "Group", "Zone Name", "Total Days",
                 "Present Days", "Late Days", "Absent Days", "Leave Days", "Present %", "Late %"]
    show_cols = [c for c in show_cols if c in att_display.columns]
    st.dataframe(style_pct_columns(att_display[show_cols], ["Present %"]),
                 width='stretch', hide_index=True)
    st.caption("Present % below the threshold is highlighted red. Late % is shown for reference.")

    with st.expander("📅 Day-by-day attendance status per SO"):
        daily_pivot = flt(results["attendance_daily_pivot"].reset_index()).set_index("Staff Id")
        st.dataframe(daily_pivot, width='stretch')

    st.subheader("🕗 First Visit (Check-in) Time")
    fv_avg = flt(results["first_visit_avg"]).merge(
        filtered_master[["Staff Id", "Name"]], on="Staff Id", how="left")
    st.dataframe(fv_avg[["Staff Id", "Name", "Avg First Visit Time"]],
                 width='stretch', hide_index=True)

    with st.expander("📅 Day-by-day first visit time per SO"):
        fv_daily = flt(results["first_visit_daily"])
        st.dataframe(fv_daily, width='stretch', hide_index=True)


# ============================================================
# TAB 3 — MARKET COVERAGE (outlet visits, memo, stay time)
# ============================================================
with tabs[2]:
    st.subheader("Outlet Visit Performance")
    st.caption(
        "Outlet Target / Visit % is the official figure from the 'Outlet Targt + Memo' "
        "sheet (Total Outlet Visit ÷ Total Outlet Target). "
        f"Below {RED_FLAG_BELOW_PCT}% is flagged red."
    )
    op_display = outlet_perf.merge(filtered_master[["Staff Id", "Name", "Group", "Zone Name"]],
                                    on="Staff Id", how="left").sort_values("Outlet Visit %", ascending=False)
    show_cols = ["Staff Id", "Name", "Group", "Zone Name", "Active Days",
                 "Total Outlet Visits", "Avg Outlets/Day", "Total Outlet Target", "Outlet Visit %"]
    show_cols = [c for c in show_cols if c in op_display.columns]
    st.dataframe(style_pct_columns(op_display[show_cols], ["Outlet Visit %"]),
                 width='stretch', hide_index=True)

    st.subheader(f"🧾 Memo Performance (target {dp.MEMO_TARGET_PER_DAY}/day)")
    mp_display = memo_perf.merge(filtered_master[["Staff Id", "Name", "Group"]],
                                  on="Staff Id", how="left").sort_values("Memo Performance %", ascending=False)
    show_cols = ["Staff Id", "Name", "Group", "Active Days", "Total Memo",
                 "Avg Memo/Day", "Memo Target/Day", "Total Shop Memo Target",
                 "Total Shop Memo Count", "Memo Performance %"]
    show_cols = [c for c in show_cols if c in mp_display.columns]
    st.dataframe(style_pct_columns(mp_display[show_cols], ["Memo Performance %"]),
                 width='stretch', hide_index=True)

    st.subheader("⏱️ Market Stay / Idle Time")
    if not results.get("has_market_stay_data"):
        st.info(
            "ℹ️ এই Excel export-এ check-out time রেকর্ড করা নেই (শুধু check-in সময় আছে), "
            "তাই Market Stay / Idle Time হিসাব করা সম্ভব হচ্ছে না। ভবিষ্যতে export-এ "
            "check-out time যোগ হলে এই সেকশন automatically চালু হয়ে যাবে।",
            icon="ℹ️",
        )
    else:
        st.caption(
            "Based on check-in → check-out time. Only days with a recorded checkout "
            "are used — many rows only have a check-in, so 'Days Without Checkout' "
            "shows how many days couldn't be measured."
        )
        ms_display = flt(results["market_stay"]).merge(
            filtered_master[["Staff Id", "Name"]], on="Staff Id", how="left")
        show_cols = ["Staff Id", "Name", "Days With Checkout", "Days Without Checkout", "Avg Market Stay"]
        show_cols = [c for c in show_cols if c in ms_display.columns]
        st.dataframe(ms_display[show_cols], width='stretch', hide_index=True)


# ============================================================
# TAB 4 — ROUTE & REPEAT VISITS
# ============================================================
with tabs[3]:
    st.subheader("Most Visited Route per Sales Officer")
    rw_display = flt(results["route_wise"], id_col="Staff Id").merge(
        filtered_master[["Staff Id", "Name", "Group"]], on="Staff Id", how="left")
    st.dataframe(rw_display[["Staff Id", "Name", "Group", "Most Visited Route", "Visit Count"]],
                 width='stretch', hide_index=True)

    st.subheader("🔁 Repeat Market Visits (same outlet visited more than once)")
    rpt_summary = flt(results["repeat_summary"]).merge(
        filtered_master[["Staff Id", "Name"]], on="Staff Id", how="left"
    ).sort_values("Max Times Same Market Visited", ascending=False)
    st.dataframe(rpt_summary[["Staff Id", "Name", "Repeated Markets", "Max Times Same Market Visited"]],
                 width='stretch', hide_index=True)

    with st.expander("See exact repeated markets"):
        rpt_detail = flt(results["repeat_detail"], id_col="Staff Id")
        st.dataframe(rpt_detail, width='stretch', hide_index=True)


# ============================================================
# TAB 5 — RAW TABLES (for spot-checking)
# ============================================================
with tabs[4]:
    st.subheader("SO Master List")
    st.dataframe(filtered_master, width='stretch', hide_index=True)
    st.subheader("Raw SO Activity (filtered rows shown are NOT filtered here — full data)")
    st.dataframe(act.head(500), width='stretch', hide_index=True)
    st.subheader("Raw SO Attendance")
    st.dataframe(att.head(500), width='stretch', hide_index=True)
