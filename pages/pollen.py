import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import date, datetime
import pandas as pd
from utils.pollen_api import (
    get_pollen_data, classify, get_advice,
    POLLEN_TYPES, COLOR_MAP,
)

_LEVEL_ORDER = {'lite': 0, 'moderat': 1, 'kraftig': 2, 'ekstrem': 3}
_NORSKE_DAGER = ['Man', 'Tir', 'Ons', 'Tor', 'Fre', 'Lør', 'Søn']


def _build_df(data):
    hourly = data['hourly']
    n = len(hourly['time'])
    df = pd.DataFrame({'time': pd.to_datetime(hourly['time'])})
    for ptype in POLLEN_TYPES:
        raw = hourly.get(ptype, [None] * n)
        df[ptype] = [float(v) if v is not None else 0.0 for v in raw]
    df['date'] = df['time'].dt.date
    return df


def show():
    st_autorefresh(interval=1800000, key="pollen_refresh")
    st.markdown("## 🌼 Pollen")

    try:
        data = get_pollen_data()
    except Exception as e:
        st.warning(f"Kunne ikke hente pollendata: {e}")
        return

    df = _build_df(data)
    today = date.today()
    today_df = df[df['date'] == today]

    if today_df.empty:
        st.info("Ingen pollendata tilgjengelig for i dag.")
        return

    current_hour = datetime.now().hour
    current_idx = (today_df['time'].dt.hour - current_hour).abs().idxmin()
    current_row = today_df.loc[current_idx]

    active = []
    worst_level = 'lite'
    for ptype, info in POLLEN_TYPES.items():
        val = float(current_row[ptype])
        if val > 0:
            level, emo = classify(val, info['category'])
            active.append((ptype, info, val, level, emo))
            if _LEVEL_ORDER[level] > _LEVEL_ORDER[worst_level]:
                worst_level = level

    # 1. Health advice
    if not active:
        st.info("Ingen aktive pollentyper i sesong akkurat nå.")
        return
    elif worst_level == 'lite':
        st.success("Lavt pollennivå i dag. Nyt friluftsliv! 🌿")
    else:
        color = COLOR_MAP[worst_level]
        tips = get_advice(worst_level)
        tip_html = ''.join(f'<li>{t}</li>' for t in tips)
        st.markdown(
            f"<div style='background:{color};color:white;padding:10px 14px;"
            f"border-radius:8px;margin-bottom:8px'>"
            f"<b>Pollennivå: {worst_level.capitalize()}</b>"
            f"<ul style='margin:4px 0 0 0;padding-left:18px'>{tip_html}</ul></div>",
            unsafe_allow_html=True,
        )

    # 2. Cards per active pollen type (max 3 per row)
    n_cols = min(len(active), 3)
    cols = st.columns(n_cols)
    for i, (ptype, info, val, level, emo) in enumerate(active):
        with cols[i % n_cols]:
            st.metric(label=f"{emo} {info['label']}", value=f"{val:.1f} k/m³")
            st.caption(level.capitalize())

    st.divider()

    # 3. 4-day bar chart: daily max per active type
    st.markdown("**4 dager**")
    ptype_keys = [p for p, *_ in active]
    daily_max = df.groupby('date')[ptype_keys].max()
    daily_max.index = [_NORSKE_DAGER[d.weekday()] for d in daily_max.index]
    daily_max.columns = [POLLEN_TYPES[p]['label'] for p in ptype_keys]
    st.bar_chart(daily_max)

    # 4. Hourly line chart for today (active types only)
    st.markdown("**Time for time i dag**")
    hourly_chart = today_df.set_index('time')[ptype_keys].copy()
    hourly_chart.columns = [POLLEN_TYPES[p]['label'] for p in ptype_keys]
    st.line_chart(hourly_chart)


def render_home_widget():
    try:
        data = get_pollen_data()
        df = _build_df(data)
        today = date.today()
        today_df = df[df['date'] == today]
        if today_df.empty:
            return
        current_hour = datetime.now().hour
        current_idx = (today_df['time'].dt.hour - current_hour).abs().idxmin()
        current_row = today_df.loc[current_idx]

        worst = None
        worst_order = -1
        for ptype, info in POLLEN_TYPES.items():
            val = float(current_row[ptype])
            if val > 0:
                level, emo = classify(val, info['category'])
                if _LEVEL_ORDER[level] > worst_order:
                    worst_order = _LEVEL_ORDER[level]
                    worst = (info['label'], val, level, emo)
        if worst:
            label, val, level, emo = worst
            st.caption(f"🌼 {emo} {label} {val:.0f} k/m³ ({level})")
            if level in ('kraftig', 'ekstrem'):
                tips = get_advice(level)
                if tips:
                    st.caption(f"💊 {tips[0]}")
    except Exception:
        pass
