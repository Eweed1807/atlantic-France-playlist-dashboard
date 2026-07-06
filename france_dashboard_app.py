import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Atlantic France Playlist Analytics",
    page_icon="🇫🇷",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap');
  html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
  .main-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3rem;
    letter-spacing: 3px;
    background: linear-gradient(135deg, #0055A4, #EF4135);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
  }
  .sub-title { color: #888; font-size: 1rem; font-weight: 300; margin-top: 0; letter-spacing: 1px; text-transform: uppercase; }
  .kpi-card { background: linear-gradient(135deg, #1a1a2e, #16213e); border: 1px solid #0055A4; border-radius: 12px; padding: 20px; text-align: center; color: white; }
  .kpi-value { font-family: 'Bebas Neue', sans-serif; font-size: 2.4rem; color: #0055A4; line-height: 1; }
  .kpi-label { font-size: 0.75rem; color: #aaa; text-transform: uppercase; letter-spacing: 1px; margin-top: 4px; }
  .section-header { font-family: 'Bebas Neue', sans-serif; font-size: 1.6rem; letter-spacing: 2px; color: #0055A4; border-bottom: 2px solid #0055A4; padding-bottom: 6px; margin-top: 2rem; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv(r"C:\Users\Pruthvi\OneDrive\Desktop\w\project\Atlantic France Top 50 Playlist\Atlantic_France.csv")
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df = df.dropna(subset=["date", "song"]).sort_values("date")
    df["duration_min"] = (df["duration_ms"] / 60000).round(2)
    df["dur_bucket"] = pd.cut(df["duration_min"], bins=[0,2,3,4,20],
                              labels=["Short (<2m)","Medium (2-3m)","Long (3-4m)","X-Long (>4m)"])
    df["rank_tier"] = pd.cut(df["position"], bins=[0,10,25,50],
                             labels=["Top 10","Top 25","Top 50"])
    df["track_bin"] = pd.cut(df["total_tracks"], bins=[0,1,5,15,30,1000],
                             labels=["Single(1)","EP(2-5)","Standard(6-15)","Large(16-30)","Mega(30+)"])
    return df

df = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎛️ Filters")
    date_min, date_max = df["date"].min().date(), df["date"].max().date()
    date_range = st.date_input("Date Range", value=(date_min, date_max),
                               min_value=date_min, max_value=date_max)
    rank_tier_filter = st.multiselect("Rank Tier", ["Top 10","Top 25","Top 50"],
                                      default=["Top 10","Top 25","Top 50"])
    explicit_filter = st.radio("Explicit Content", ["All","Explicit only","Clean only"])
    album_type_filter = st.multiselect("Album Type", ["single","album","compilation"],
                                       default=["single","album","compilation"])

if len(date_range) == 2:
    start_d, end_d = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    start_d, end_d = df["date"].min(), df["date"].max()

mask = (
    (df["date"] >= start_d) & (df["date"] <= end_d) &
    (df["rank_tier"].isin(rank_tier_filter)) &
    (df["album_type"].isin(album_type_filter))
)
if explicit_filter == "Explicit only":
    mask &= df["is_explicit"] == True
elif explicit_filter == "Clean only":
    mask &= df["is_explicit"] == False
fdf = df[mask].copy()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🇫🇷 Atlantic France Playlist Analytics</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Audience Sensitivity · Content Compliance · Format Preference</p>', unsafe_allow_html=True)
st.markdown("---")

# ── KPIs ─────────────────────────────────────────────────────────────────────
k1,k2,k3,k4,k5,k6 = st.columns(6)
explicit_share = fdf["is_explicit"].sum()/len(fdf)*100 if len(fdf) > 0 else 0
clean_ratio = 100 - explicit_share
single_share = (fdf["album_type"]=="single").sum()/len(fdf)*100 if len(fdf) > 0 else 0
kpis = [
    (k1, f"{fdf['date'].nunique():,}", "Snapshot Days"),
    (k2, f"{explicit_share:.1f}%", "Explicit Share"),
    (k3, f"{clean_ratio:.1f}%", "Clean Dominance"),
    (k4, f"{single_share:.1f}%", "Singles Share"),
    (k5, f"{fdf['duration_min'].mean():.2f}m", "Avg Duration"),
    (k6, f"{fdf['popularity'].mean():.1f}", "Avg Popularity"),
]
for col, val, label in kpis:
    with col:
        st.markdown(f'<div class="kpi-card"><div class="kpi-value">{val}</div><div class="kpi-label">{label}</div></div>',
                    unsafe_allow_html=True)

st.markdown("")

tabs = st.tabs([
    "🔞 Explicit Content Analysis",
    "💿 Release Format Preference",
    "📏 Song Duration Analysis",
    "📦 Album Structure Impact",
    "🎯 Content Compliance Summary",
])

BLUE = "#0055A4"
RED  = "#EF4135"

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – Explicit Content
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    st.markdown('<p class="section-header">Explicit Content Sensitivity Analysis</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        exp_counts = fdf["is_explicit"].value_counts().reset_index()
        exp_counts.columns = ["is_explicit","count"]
        exp_counts["label"] = exp_counts["is_explicit"].map({True:"Explicit",False:"Clean"})
        fig = px.pie(exp_counts, values="count", names="label",
                     title="Explicit vs Clean Content Share",
                     color_discrete_sequence=[RED, BLUE])
        fig.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        exp_pop = fdf.groupby("is_explicit").agg(
            avg_pop=("popularity","mean"), avg_rank=("position","mean")
        ).reset_index()
        exp_pop["label"] = exp_pop["is_explicit"].map({True:"Explicit",False:"Clean"})
        fig2 = px.bar(exp_pop, x="label", y="avg_pop", color="label",
                      color_discrete_sequence=[RED, BLUE],
                      title="Avg Popularity: Explicit vs Clean",
                      text=exp_pop["avg_pop"].round(1))
        fig2.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a",
                           font_color="white", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Explicit Content Distribution Across Rank Tiers")
    tier_exp = fdf.groupby(["rank_tier","is_explicit"], observed=True).size().reset_index(name="count")
    tier_exp["label"] = tier_exp["is_explicit"].map({True:"Explicit",False:"Clean"})
    fig3 = px.bar(tier_exp, x="rank_tier", y="count", color="label",
                  barmode="group", title="Explicit vs Clean Count by Rank Tier",
                  color_discrete_sequence=[RED, BLUE])
    fig3.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a", font_color="white")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("#### Explicit Popularity by Rank Tier")
    tier_pop = fdf.groupby(["rank_tier","is_explicit"], observed=True)["popularity"].mean().reset_index()
    tier_pop["label"] = tier_pop["is_explicit"].map({True:"Explicit",False:"Clean"})
    fig4 = px.bar(tier_pop, x="rank_tier", y="popularity", color="label",
                  barmode="group", title="Avg Popularity by Tier & Explicit Flag",
                  color_discrete_sequence=[RED, BLUE],
                  text=tier_pop["popularity"].round(1))
    fig4.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a", font_color="white")
    st.plotly_chart(fig4, use_container_width=True)

    st.markdown("#### Explicit Share Over Time")
    exp_time = fdf.groupby("date").apply(
        lambda x: (x["is_explicit"].sum()/len(x))*100, include_groups=False
    ).reset_index()
    exp_time.columns = ["date","explicit_pct"]
    fig5 = px.area(exp_time, x="date", y="explicit_pct",
                   title="Daily Explicit Content Share (%)",
                   color_discrete_sequence=[RED])
    fig5.update_traces(fillcolor="rgba(239,65,53,0.15)")
    fig5.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a",
                       font_color="white", yaxis_title="Explicit Share (%)")
    st.plotly_chart(fig5, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 – Release Format
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<p class="section-header">Release Format Preference Analysis</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        fmt_counts = fdf["album_type"].value_counts().reset_index()
        fmt_counts.columns = ["album_type","count"]
        fig = px.pie(fmt_counts, values="count", names="album_type",
                     title="Single vs Album vs Compilation Share",
                     color_discrete_sequence=[BLUE, RED, "#888888"])
        fig.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fmt_pop = fdf.groupby("album_type").agg(
            avg_pop=("popularity","mean"), avg_rank=("position","mean")
        ).reset_index()
        fig2 = px.bar(fmt_pop, x="album_type", y="avg_pop",
                      color="album_type", color_discrete_sequence=[BLUE, RED, "#888888"],
                      title="Avg Popularity by Format",
                      text=fmt_pop["avg_pop"].round(1))
        fig2.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a",
                           font_color="white", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Format Representation by Rank Tier")
    tier_fmt = fdf.groupby(["rank_tier","album_type"], observed=True).size().reset_index(name="count")
    fig3 = px.bar(tier_fmt, x="rank_tier", y="count", color="album_type",
                  barmode="group", title="Album Type Distribution Across Rank Tiers",
                  color_discrete_sequence=[BLUE, RED, "#888888"])
    fig3.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a", font_color="white")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("#### Avg Rank by Format (lower = better)")
    fig4 = px.bar(fmt_pop, x="album_type", y="avg_rank",
                  color="album_type", color_discrete_sequence=[BLUE, RED, "#888888"],
                  title="Avg Chart Rank by Album Type",
                  text=fmt_pop["avg_rank"].round(1))
    fig4.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a",
                       font_color="white", showlegend=False)
    st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – Duration
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    st.markdown('<p class="section-header">Song Duration Preference Analysis</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.histogram(fdf, x="duration_min", nbins=40,
                           title="Duration Distribution Across Playlist",
                           color_discrete_sequence=[BLUE])
        fig.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a",
                          font_color="white", xaxis_title="Duration (minutes)")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        dur_pop = fdf.groupby("dur_bucket", observed=True).agg(
            avg_pop=("popularity","mean"), avg_rank=("position","mean"),
            count=("song","count")
        ).reset_index()
        fig2 = px.bar(dur_pop, x="dur_bucket", y="avg_pop",
                      color="avg_pop", color_continuous_scale="Blues",
                      title="Avg Popularity by Duration Bucket",
                      text=dur_pop["avg_pop"].round(1))
        fig2.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a",
                           font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        fig3 = px.bar(dur_pop, x="dur_bucket", y="avg_rank",
                      color="avg_rank", color_continuous_scale="Reds_r",
                      title="Avg Rank by Duration Bucket (lower = better)",
                      text=dur_pop["avg_rank"].round(1))
        fig3.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a",
                           font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        fig4 = px.scatter(fdf.sample(min(3000, len(fdf)), random_state=42),
                          x="duration_min", y="popularity",
                          color="rank_tier", opacity=0.5,
                          title="Duration vs Popularity",
                          labels={"duration_min":"Duration (min)"})
        fig4.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a", font_color="white")
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("#### Duration Distribution by Rank Tier")
    fig5 = px.box(fdf, x="rank_tier", y="duration_min",
                  color="rank_tier",
                  color_discrete_sequence=[BLUE, RED, "#888888"],
                  title="Duration Distribution by Rank Tier")
    fig5.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a",
                       font_color="white", showlegend=False)
    st.plotly_chart(fig5, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 – Album Structure
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    st.markdown('<p class="section-header">Album Structure Impact Analysis</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        trk_pop = fdf.groupby("track_bin", observed=True).agg(
            avg_pop=("popularity","mean"), avg_rank=("position","mean"),
            count=("song","count")
        ).reset_index()
        fig = px.bar(trk_pop, x="track_bin", y="avg_pop",
                     color="avg_pop", color_continuous_scale="Blues",
                     title="Avg Popularity by Album Size",
                     text=trk_pop["avg_pop"].round(1))
        fig.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a",
                          font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(trk_pop, x="track_bin", y="avg_rank",
                      color="avg_rank", color_continuous_scale="Reds_r",
                      title="Avg Rank by Album Size (lower = better)",
                      text=trk_pop["avg_rank"].round(1))
        fig2.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a",
                           font_color="white", coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("#### Total Tracks Distribution")
    fig3 = px.histogram(fdf, x="total_tracks", nbins=30,
                        title="Album Size (Total Tracks) Distribution",
                        color_discrete_sequence=[BLUE])
    fig3.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a", font_color="white")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("#### Album Size vs Popularity Scatter")
    fig4 = px.scatter(fdf.sample(min(3000,len(fdf)), random_state=42),
                      x="total_tracks", y="popularity",
                      color="album_type", opacity=0.5,
                      title="Total Tracks vs Popularity",
                      color_discrete_sequence=[BLUE, RED, "#888888"])
    fig4.update_layout(plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a", font_color="white")
    st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 – Content Compliance Summary
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    st.markdown('<p class="section-header">Content Compliance Summary Panel</p>', unsafe_allow_html=True)

    st.markdown("#### Attribute Density Across Rank Tiers")
    attr_data = []
    for tier in ["Top 10","Top 25","Top 50"]:
        tier_df = fdf[fdf["rank_tier"]==tier]
        if len(tier_df) > 0:
            attr_data.append({
                "Rank Tier": tier,
                "Explicit Share (%)": round(tier_df["is_explicit"].mean()*100, 1),
                "Singles Share (%)": round((tier_df["album_type"]=="single").mean()*100, 1),
                "Avg Popularity": round(tier_df["popularity"].mean(), 1),
                "Avg Duration (min)": round(tier_df["duration_min"].mean(), 2),
                "Avg Rank": round(tier_df["position"].mean(), 1),
            })
    attr_df = pd.DataFrame(attr_data)
    st.dataframe(attr_df.set_index("Rank Tier"), use_container_width=True)

    st.markdown("#### KPI Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**🔞 Explicit Content**")
        st.metric("Explicit Share", f"{fdf['is_explicit'].mean()*100:.1f}%")
        st.metric("Clean Avg Popularity", f"{fdf[fdf['is_explicit']==False]['popularity'].mean():.1f}")
        st.metric("Explicit Avg Popularity", f"{fdf[fdf['is_explicit']==True]['popularity'].mean():.1f}")

    with col2:
        st.markdown("**💿 Format Preference**")
        st.metric("Singles Share", f"{(fdf['album_type']=='single').mean()*100:.1f}%")
        st.metric("Singles Avg Popularity", f"{fdf[fdf['album_type']=='single']['popularity'].mean():.1f}")
        st.metric("Albums Avg Popularity", f"{fdf[fdf['album_type']=='album']['popularity'].mean():.1f}")

    with col3:
        st.markdown("**📏 Duration Profile**")
        st.metric("Avg Duration", f"{fdf['duration_min'].mean():.2f} min")
        st.metric("Optimal Bucket", "Long (3-4m)")
        st.metric("Optimal Avg Popularity",
                  f"{fdf[fdf['dur_bucket']=='Long (3-4m)']['popularity'].mean():.1f}")

    st.markdown("#### Content Compliance Radar — Top 10 Profile")
    categories = ["Clean Content","Singles","Optimal Duration","Standard Album","Top 10 Presence"]
    top10_df = fdf[fdf["rank_tier"]=="Top 10"]
    values = [
        round(100 - top10_df["is_explicit"].mean()*100, 1),
        round((top10_df["album_type"]=="single").mean()*100, 1),
        round((top10_df["dur_bucket"]=="Long (3-4m)").mean()*100, 1),
        round((top10_df["track_bin"]=="Standard(6-15)").mean()*100, 1),
        100,
    ]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values, theta=categories, fill="toself",
        name="Top 10 Profile", line_color=BLUE,
        fillcolor="rgba(0,85,164,0.2)"
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,100])),
        plot_bgcolor="#0d0d1a", paper_bgcolor="#0d0d1a",
        font_color="white",
        title="Content Profile of France Top 10 Songs"
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.markdown(
    "<p style='text-align:center;color:#555;font-size:0.8rem;'>"
    "Atlantic Recording Corporation · France Top 50 Playlist Analytics · Unified Mentor Fellowship</p>",
    unsafe_allow_html=True
)
