# ==========================================================
# SALES OFFICER DASHBOARD — DATA PROCESSING
# All business-logic / number-crunching lives here, kept
# separate from the Streamlit UI so it can be tested on its
# own and re-used if the UI ever changes.
#
# NOTE: This version matches the workbook that has THREE
# sheets: "Outlet Targt + Memo", "SO Activity", "Attendance".
# (An earlier version of this file supported a 2-sheet
# workbook without an official target sheet — that format is
# no longer used.)
# ==========================================================
import numpy as np
import pandas as pd

# ------------------------------------------------------------
# CONFIG / ASSUMPTIONS
# ------------------------------------------------------------
# Outlet Target / Memo Target for the WHOLE workbook period come
# straight from the "Outlet Targt + Memo" sheet (they're fixed
# per-SO totals set by the business, e.g. 260 = 20/day x 13 days).
# The per-day numbers below are only used to compute each SO's
# own "Avg Outlets/Day" and "Avg Memo/Day" for the Top/Bottom
# performer lists, exactly as requested:
#   - Good performer: avg >= 20 outlets/day
#   - Bad performer:  avg < 15 outlets/day
GOOD_PERFORMER_MIN_AVG_VISITS = 20
BAD_PERFORMER_MAX_AVG_VISITS = 15
MEMO_TARGET_PER_DAY = 8
RED_FLAG_BELOW_PCT = 60      # "60% er niche red mark"

REQUIRED_TARGET_COLUMNS = [
    "Staff ID", "Sr Name", "Total Outlet Target", "Total Outlet Visit",
    "Percentage Of Visit", "Total Shop Memo Target", "Total Shop Memo Count", "Memo %",
]
REQUIRED_ACTIVITY_COLUMNS = [
    "Sub Business", "Zone Name", "RSM", "AGM/SM/RSM", "Base Name",
    "Staff ID", "Sr Name", "Route Id", "Route Name", "Route Day Name",
    "Market Id", "Market Name", "Number Of Outlet Visit",
    "Number Of Ordered Shop", "Visit Date",
]
REQUIRED_ATTENDANCE_COLUMNS = [
    "Employee Name", "Staff Id", "Group Name", "Zone Name", "Base Name",
    "Attendance Date", "Day Name", "Attendance Status", "In Time Only",
]
# These are optional — if present, the Market Stay / Idle Time tab
# is computed; if not (as in the current export), it's skipped
# with a friendly message instead of crashing.
OPTIONAL_MARKET_STAY_COLUMNS = ["Check Out Status", "Out Time Only", "Total Hours"]


class DashboardDataError(Exception):
    """Raised when the uploaded workbook doesn't look like an
    SO Activity / SO Attendance / Outlet Target export."""
    pass


# ------------------------------------------------------------
# LOAD & CLEAN
# ------------------------------------------------------------
def load_workbook(file_or_path):
    """
    Read the uploaded Excel file. Expects three sheets:
      - one with "target" or "memo" in its name  -> outlet/memo targets
      - one with "activity" in its name          -> SO Activity
      - one with "attendance" in its name        -> Attendance
    Returns (activity_df, attendance_df, target_df).
    """
    xl = pd.ExcelFile(file_or_path)
    sheet_map = {s.strip().lower(): s for s in xl.sheet_names}

    activity_key = next((v for k, v in sheet_map.items() if "activity" in k), None)
    attendance_key = next((v for k, v in sheet_map.items() if "attendance" in k), None)
    target_key = next((v for k, v in sheet_map.items() if "target" in k or "memo" in k), None)

    missing_sheets = []
    if activity_key is None:
        missing_sheets.append("SO Activity")
    if attendance_key is None:
        missing_sheets.append("Attendance")
    if target_key is None:
        missing_sheets.append("Outlet Target + Memo")
    if missing_sheets:
        raise DashboardDataError(
            f"Couldn't find these sheet(s): {missing_sheets}. "
            f"Sheets found in file: {xl.sheet_names}"
        )

    act = xl.parse(activity_key)
    att = xl.parse(attendance_key)
    tgt = xl.parse(target_key)

    # Excel exports often carry stray leading/trailing spaces in
    # header names (e.g. "Office Attendance ") — strip them all.
    act.columns = [str(c).strip() for c in act.columns]
    att.columns = [str(c).strip() for c in att.columns]
    tgt.columns = [str(c).strip() for c in tgt.columns]

    missing_act = [c for c in REQUIRED_ACTIVITY_COLUMNS if c not in act.columns]
    missing_att = [c for c in REQUIRED_ATTENDANCE_COLUMNS if c not in att.columns]
    missing_tgt = [c for c in REQUIRED_TARGET_COLUMNS if c not in tgt.columns]
    if missing_act:
        raise DashboardDataError(f"'SO Activity' sheet is missing columns: {missing_act}")
    if missing_att:
        raise DashboardDataError(f"'Attendance' sheet is missing columns: {missing_att}")
    if missing_tgt:
        raise DashboardDataError(f"'Outlet Target + Memo' sheet is missing columns: {missing_tgt}")

    act = _clean_activity(act)
    att = _clean_attendance(att)
    tgt = _clean_target(tgt)
    return act, att, tgt


def _clean_activity(act):
    act = act.copy()
    act["Staff ID"] = act["Staff ID"].astype(str).str.strip()
    act["Sr Name"] = act["Sr Name"].astype(str).str.strip()
    act["Route Name"] = act["Route Name"].astype(str).str.strip()
    act["Market Name"] = act["Market Name"].astype(str).str.strip()
    act["Zone Name"] = act["Zone Name"].astype(str).str.strip()
    act["Sub Business"] = act["Sub Business"].astype(str).str.strip()
    act["Visit Date"] = pd.to_datetime(act["Visit Date"]).dt.normalize()

    # RSM column is sometimes fully blank in older exports; the UI
    # falls back to Zone Name for "RSM-wise" views when that happens.
    act["_RSM_available"] = act["RSM"].notna().any() or act["AGM/SM/RSM"].notna().any()
    return act


def _clean_attendance(att):
    att = att.copy()
    att["Staff Id"] = att["Staff Id"].astype(str).str.strip()
    att["Employee Name"] = att["Employee Name"].astype(str).str.strip()
    att["Group Name"] = att["Group Name"].astype(str).str.strip()
    att["Zone Name"] = att["Zone Name"].astype(str).str.strip()
    att["Attendance Date"] = pd.to_datetime(att["Attendance Date"]).dt.normalize()
    att["Attendance Status"] = att["Attendance Status"].astype(str).str.strip()
    if "Late Status" in att.columns:
        att["Late Status"] = att["Late Status"].astype(str).str.strip()
    return att


def _clean_target(tgt):
    tgt = tgt.copy()
    tgt["Staff ID"] = tgt["Staff ID"].astype(str).str.strip()
    tgt["Sr Name"] = tgt["Sr Name"].astype(str).str.strip()
    # "Percentage Of Visit" / "Memo %" come in as fractions (0.79 = 79%).
    tgt["Outlet Visit %"] = (tgt["Percentage Of Visit"] * 100).round().astype("Int64")
    tgt["Memo Performance %"] = (tgt["Memo %"] * 100).round().astype("Int64")
    return tgt


def has_market_stay_data(att):
    return all(c in att.columns for c in OPTIONAL_MARKET_STAY_COLUMNS)


def has_rsm_data(act):
    return bool(act["_RSM_available"].iloc[0]) if len(act) else False


def rsm_or_zone_column(act):
    """Which column to group by for 'RSM-wise' views."""
    return "RSM" if has_rsm_data(act) else "Zone Name"


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def _time_to_minutes(t):
    """'08:13:25' -> minutes since midnight. Returns NaN if unparsable."""
    if pd.isna(t):
        return np.nan
    try:
        parts = str(t).split(":")
        h, m = int(parts[0]), int(parts[1])
        return h * 60 + m
    except Exception:
        return np.nan


def _minutes_to_hhmm(mins):
    if pd.isna(mins):
        return "N/A"
    mins = int(round(mins))
    return f"{mins // 60:02d}:{mins % 60:02d}"


def _pct(numerator, denominator):
    if denominator in (0, None) or pd.isna(denominator):
        return np.nan
    return round(100 * numerator / denominator)


def build_so_master(act, att):
    """One row per Sales Officer with identifying info, pulled
    from whichever sheet has it (prefers Attendance for name/group
    since it's the more 'HR-accurate' source)."""
    act_ids = act[["Staff ID", "Sr Name", "Sub Business", "Zone Name", "Base Name",
                   "RSM", "AGM/SM/RSM"]].drop_duplicates("Staff ID")
    act_ids = act_ids.rename(columns={"Staff ID": "Staff Id", "Sr Name": "Name",
                                       "Sub Business": "Group", "Base Name": "Base"})

    att_ids = att[["Staff Id", "Employee Name", "Group Name", "Zone Name", "Base Name"]].drop_duplicates("Staff Id")
    att_ids = att_ids.rename(columns={"Employee Name": "Name", "Group Name": "Group", "Base Name": "Base"})

    master = pd.merge(att_ids, act_ids, on="Staff Id", how="outer", suffixes=("", "_act"))
    master["Name"] = master["Name"].fillna(master["Name_act"])
    master["Group"] = master["Group"].fillna(master["Group_act"])
    master["Zone Name"] = master["Zone Name"].fillna(master["Zone Name_act"])
    master["Base"] = master["Base"].fillna(master["Base_act"])
    master = master[["Staff Id", "Name", "Group", "Zone Name", "Base", "RSM", "AGM/SM/RSM"]].drop_duplicates("Staff Id")
    return master.reset_index(drop=True)


# ------------------------------------------------------------
# 1 & 2 & 14. ATTENDANCE: daily status, late %, present %
#    New export's "Attendance Status" is only Present/Absent;
#    "Late Status" (On Time / Late / Absent) carries lateness.
# ------------------------------------------------------------
def attendance_daily_pivot(att):
    """SO (rows) x Date (columns) -> Attendance Status.
    This answers 'je koidin ache she koidin hoi late na hoi present'."""
    pivot = att.pivot_table(
        index="Staff Id", columns="Attendance Date",
        values="Attendance Status", aggfunc="first"
    )
    pivot.columns = [c.strftime("%d-%b") for c in pivot.columns]
    return pivot


def attendance_summary(att):
    """Per-SO: total days recorded, present/late/absent counts,
    Late % and Present % (both integers, both against total days)."""
    has_late_status = "Late Status" in att.columns
    grp = att.groupby("Staff Id")
    total_days = grp["Attendance Date"].nunique()
    present_days = grp.apply(lambda d: (d["Attendance Status"] == "Present").sum())
    absent_days = grp.apply(lambda d: (d["Attendance Status"] == "Absent").sum())
    if has_late_status:
        late_days = grp.apply(lambda d: (d["Late Status"] == "Late").sum())
    else:
        late_days = pd.Series(0, index=total_days.index)

    out = pd.DataFrame({
        "Total Days": total_days,
        "Present Days": present_days,
        "Late Days": late_days,
        "Absent Days": absent_days,
    })
    out["Present %"] = out.apply(lambda r: _pct(r["Present Days"], r["Total Days"]), axis=1)
    out["Late %"] = out.apply(lambda r: _pct(r["Late Days"], r["Total Days"]), axis=1)
    out = out.reset_index()
    return out


# ------------------------------------------------------------
# 3. FIRST VISIT (approximated as daily check-in time — the
#    workbook has no per-outlet visit timestamp, only a date)
# ------------------------------------------------------------
def first_visit_summary(att):
    att = att.copy()
    att["_in_min"] = att["In Time Only"].apply(_time_to_minutes)
    daily = att[["Staff Id", "Attendance Date", "In Time Only", "_in_min"]].dropna(subset=["_in_min"])
    daily = daily.rename(columns={"In Time Only": "First Visit (Check-in)"})

    avg = daily.groupby("Staff Id")["_in_min"].mean().reset_index()
    avg["Avg First Visit Time"] = avg["_in_min"].apply(_minutes_to_hhmm)
    avg = avg.drop(columns="_in_min")

    daily_table = daily.pivot_table(
        index="Staff Id", columns="Attendance Date",
        values="First Visit (Check-in)", aggfunc="first"
    )
    daily_table.columns = [c.strftime("%d-%b") for c in daily_table.columns]
    return avg, daily_table.reset_index()


# ------------------------------------------------------------
# 4. MARKET STAY / IDLE TIME
#    Only available if the Attendance sheet has checkout columns.
#    The current export doesn't record check-out time at all, so
#    this returns None and the UI shows a friendly note instead.
# ------------------------------------------------------------
def market_stay_summary(att):
    if not has_market_stay_data(att):
        return None

    from re import match as _rematch

    def _hours_str_to_minutes(s):
        if pd.isna(s):
            return np.nan
        m = _rematch(r"(\d+)h\s*(\d+)m", str(s).strip())
        if not m:
            return np.nan
        return int(m.group(1)) * 60 + int(m.group(2))

    att = att.copy()
    att["_has_checkout"] = att["Check Out Status"].notna()
    att["_stay_min"] = att["Total Hours"].apply(_hours_str_to_minutes)
    att.loc[~att["_has_checkout"], "_stay_min"] = np.nan

    grp = att.groupby("Staff Id")
    out = pd.DataFrame({
        "Days With Checkout": grp["_has_checkout"].sum(),
        "Days Without Checkout": grp["_has_checkout"].apply(lambda s: (~s).sum()),
        "Avg Market Stay (min)": grp["_stay_min"].mean(),
    }).reset_index()
    out["Avg Market Stay"] = out["Avg Market Stay (min)"].apply(_minutes_to_hhmm)
    out["Avg Market Stay (min)"] = out["Avg Market Stay (min)"].round().astype("Int64")
    return out


# ------------------------------------------------------------
# 5. MEMO COUNT vs TARGET
#    "Memo" = Number Of Ordered Shop (order placed = a sales
#    memo). Official Memo % / period target come from the
#    "Outlet Targt + Memo" sheet; Avg Memo/Day is computed here
#    from actual active days for the per-day view.
# ------------------------------------------------------------
def memo_performance(act, tgt, target_per_day=MEMO_TARGET_PER_DAY):
    daily = act.groupby(["Staff ID", "Visit Date"])["Number Of Ordered Shop"].sum().reset_index()
    summary = daily.groupby("Staff ID").agg(
        Active_Days=("Visit Date", "nunique"),
        Total_Memo=("Number Of Ordered Shop", "sum"),
    ).reset_index()
    summary["Avg Memo/Day"] = (summary["Total_Memo"] / summary["Active_Days"]).round().astype("Int64")
    summary["Memo Target/Day"] = target_per_day
    summary = summary.rename(columns={"Staff ID": "Staff Id",
                                       "Active_Days": "Active Days",
                                       "Total_Memo": "Total Memo"})
    # Official target/percentage straight from the target sheet.
    summary = summary.merge(
        tgt[["Staff ID", "Total Shop Memo Target", "Total Shop Memo Count", "Memo Performance %"]]
        .rename(columns={"Staff ID": "Staff Id"}),
        on="Staff Id", how="left")
    return summary


# ------------------------------------------------------------
# 6, 7, 12, 13. OUTLET VISIT PERFORMANCE, TOP/BOTTOM PERFORMERS
#    Each SO Activity row is one market visited that day, and
#    "Number Of Outlet Visit" is how many outlets were covered
#    at that market — so totals must SUM that column, not count
#    rows. (Verified against the official target sheet totals.)
# ------------------------------------------------------------
def outlet_visit_performance(act, tgt):
    daily = act.groupby(["Staff ID", "Visit Date"])["Number Of Outlet Visit"].sum().reset_index()
    summary = daily.groupby("Staff ID").agg(
        Active_Days=("Visit Date", "nunique"),
        Total_Outlet_Visits=("Number Of Outlet Visit", "sum"),
    ).reset_index()
    summary["Avg Outlets/Day"] = (summary["Total_Outlet_Visits"] / summary["Active_Days"]).round().astype("Int64")
    summary = summary.rename(columns={"Staff ID": "Staff Id",
                                       "Active_Days": "Active Days",
                                       "Total_Outlet_Visits": "Total Outlet Visits"})
    # Official target/percentage straight from the target sheet.
    summary = summary.merge(
        tgt[["Staff ID", "Total Outlet Target", "Outlet Visit %"]]
        .rename(columns={"Staff ID": "Staff Id"}),
        on="Staff Id", how="left")
    return summary


def top_bottom_performers(outlet_perf, master, top_n=10,
                           good_min=GOOD_PERFORMER_MIN_AVG_VISITS,
                           bad_max=BAD_PERFORMER_MAX_AVG_VISITS):
    merged = outlet_perf.merge(master, on="Staff Id", how="left")
    good = merged[merged["Avg Outlets/Day"] >= good_min].sort_values(
        "Avg Outlets/Day", ascending=False).head(top_n)
    bad = merged[merged["Avg Outlets/Day"] < bad_max].sort_values(
        "Avg Outlets/Day", ascending=True).head(top_n)
    cols = ["Staff Id", "Name", "Group", "Zone Name", "Active Days",
            "Total Outlet Visits", "Avg Outlets/Day", "Outlet Visit %"]
    cols = [c for c in cols if c in merged.columns]
    return good[cols].reset_index(drop=True), bad[cols].reset_index(drop=True)


# ------------------------------------------------------------
# 8. GROUP-WISE (Sub Business / Group Name)
# ------------------------------------------------------------
def group_wise_summary(outlet_perf, master):
    merged = outlet_perf.merge(master, on="Staff Id", how="left")
    grp = merged.groupby("Group").agg(
        SO_Count=("Staff Id", "nunique"),
        Avg_Outlets_Per_Day=("Avg Outlets/Day", "mean"),
        Avg_Outlet_Visit_Pct=("Outlet Visit %", "mean"),
    ).reset_index()
    grp["Avg_Outlets_Per_Day"] = grp["Avg_Outlets_Per_Day"].round().astype("Int64")
    grp["Avg_Outlet_Visit_Pct"] = grp["Avg_Outlet_Visit_Pct"].round().astype("Int64")
    grp = grp.rename(columns={"SO_Count": "SO Count",
                               "Avg_Outlets_Per_Day": "Avg Outlets/Day",
                               "Avg_Outlet_Visit_Pct": "Avg Outlet Visit %"})
    return grp


# ------------------------------------------------------------
# 9. RSM-WISE (falls back to Zone Name if RSM column is empty)
# ------------------------------------------------------------
def rsm_wise_top_bottom(outlet_perf, master, group_col):
    merged = outlet_perf.merge(master, on="Staff Id", how="left")
    if group_col not in merged.columns:
        return pd.DataFrame(), pd.DataFrame()

    idx_top = merged.groupby(group_col)["Avg Outlets/Day"].idxmax().dropna()
    idx_bottom = merged.groupby(group_col)["Avg Outlets/Day"].idxmin().dropna()

    cols = [group_col, "Name", "Staff Id", "Avg Outlets/Day", "Outlet Visit %"]
    cols = [c for c in cols if c in merged.columns]
    top = merged.loc[idx_top, cols].sort_values("Avg Outlets/Day", ascending=False).reset_index(drop=True)
    bottom = merged.loc[idx_bottom, cols].sort_values("Avg Outlets/Day", ascending=True).reset_index(drop=True)
    return top, bottom


# ------------------------------------------------------------
# 10. DAY-WISE: which route did each SO visit most
# ------------------------------------------------------------
def most_visited_route(act):
    route_counts = act.groupby(["Staff ID", "Route Name"]).size().reset_index(name="Visits")
    idx = route_counts.groupby("Staff ID")["Visits"].idxmax()
    top_route = route_counts.loc[idx].rename(
        columns={"Staff ID": "Staff Id", "Route Name": "Most Visited Route", "Visits": "Visit Count"})
    return top_route.reset_index(drop=True)


# ------------------------------------------------------------
# 11. REPEAT MARKET VISITS — same outlet visited on multiple
#     different dates within the uploaded period
# ------------------------------------------------------------
def repeat_market_visits(act):
    per_market = act.groupby(["Staff ID", "Market Id", "Market Name"])["Visit Date"].nunique().reset_index()
    per_market = per_market.rename(columns={"Visit Date": "Distinct Days Visited"})
    repeats = per_market[per_market["Distinct Days Visited"] > 1].copy()
    repeats = repeats.rename(columns={"Staff ID": "Staff Id"})

    summary = repeats.groupby("Staff Id").agg(
        Repeated_Markets=("Market Id", "nunique"),
        Max_Repeat_Visits=("Distinct Days Visited", "max"),
    ).reset_index().rename(columns={"Repeated_Markets": "Repeated Markets",
                                     "Max_Repeat_Visits": "Max Times Same Market Visited"})
    return summary, repeats.sort_values("Distinct Days Visited", ascending=False).reset_index(drop=True)


# ------------------------------------------------------------
# MASTER BUILD — runs everything once, used by the UI
# ------------------------------------------------------------
def build_all(act, att, tgt):
    master = build_so_master(act, att)
    group_col = rsm_or_zone_column(act)

    outlet_perf = outlet_visit_performance(act, tgt)

    results = {
        "master": master,
        "group_col": group_col,
        "attendance_summary": attendance_summary(att),
        "attendance_daily_pivot": attendance_daily_pivot(att),
        "first_visit_avg": None,
        "first_visit_daily": None,
        "market_stay": market_stay_summary(att),
        "has_market_stay_data": has_market_stay_data(att),
        "memo_perf": memo_performance(act, tgt),
        "outlet_perf": outlet_perf,
        "route_wise": most_visited_route(act),
    }
    fv_avg, fv_daily = first_visit_summary(att)
    results["first_visit_avg"] = fv_avg
    results["first_visit_daily"] = fv_daily

    good, bad = top_bottom_performers(outlet_perf, master)
    results["top_performers"] = good
    results["bottom_performers"] = bad

    results["group_wise"] = group_wise_summary(outlet_perf, master)

    rsm_top, rsm_bottom = rsm_wise_top_bottom(outlet_perf, master, group_col)
    results["rsm_top"] = rsm_top
    results["rsm_bottom"] = rsm_bottom

    rpt_summary, rpt_detail = repeat_market_visits(act)
    results["repeat_summary"] = rpt_summary
    results["repeat_detail"] = rpt_detail

    return results
