import streamlit as st
import pandas as pd
from plotly.subplots import make_subplots
import numpy as np
import helper as h 
from dotenv import load_dotenv

load_dotenv()

# Parameters
# ----------

st.set_page_config(layout="wide")
# st.set_page_config(layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
        .stApp {
            background-color: #0e1117;
            color: #fafafa;
        }
        .stMarkdown, .stDataFrame {
            color: #fafafa;
        }
    </style>
""", unsafe_allow_html=True)



TZ = 'Europe/Berlin' # 'America/Los_Angeles'
TARGET_DELTA_FASTING = 4
TARGET_DELTA_FIRST_MEAL = 1
TARGET_DELTA_LAST_MEAL = 3
TARGET_DELTA_SLEEP = 7
DT_DEEP_FAST_IN_HOURS = 12 # this is the time after which the deep fasting state starts
MIN_GAP_BETWEEN_SESSIONS_IN_MINUTES = DT_DEEP_FAST_IN_HOURS*60

# Functions
# ---------

@st.cache_data
def load_data():

    # load sleep data
    df_sleep = h.load_sleep_data_from_supabase()
    df_sleep_sessions = h.identify_sessions(df_sleep, min_gap_between_sessions_in_minutes=30, min_duration_of_session_in_minutes=60, add_sleep_duration_in_hours=True)

    # load food data
    df_eat = h.load_eat_data_from_supabase()
    df_eat_sessions = h.identify_sessions(df_eat, min_gap_between_sessions_in_minutes=MIN_GAP_BETWEEN_SESSIONS_IN_MINUTES, min_duration_of_session_in_minutes=0)

    # evaluate deep fasting sessions
    df_deep_fast_sessions = h.evaluate_deep_fast_sessions(df_eat_sessions, DT_DEEP_FAST_IN_HOURS)

    # evaluate delta to first and last meal
    df_first_and_last_meal = h.evaluate_delta_to_first_and_last_meal(df_sleep_sessions, df_eat)

    # evaluate data for visualization
    df_sleep_sessions_viz = h.process_for_visualization(df_sleep_sessions, TZ)
    df_eat_viz = h.process_for_visualization(df_eat, TZ)
    df_eat_sessions_viz = h.process_for_visualization(df_eat_sessions, TZ)
    df_deep_fast_sessions_viz = h.process_for_visualization(df_deep_fast_sessions, TZ)

    df_deep_fast_viz = h.process_deep_fast_sessions_for_viz(df_deep_fast_sessions, timezone=TZ)
    df_first_meal_viz, df_last_meal_viz = h.process_first_and_last_meal_data_for_viz(df_first_and_last_meal, timezone=TZ)
    df_sleep_duration_viz = h.process_sleep_sessions_for_viz(df_sleep_sessions, TZ)

    # calculate score
    df_score = h.calculate_score(
        df_deep_fast_viz, 
        df_first_meal_viz, 
        df_last_meal_viz, 
        df_sleep_duration_viz,
        target_delta_fasting = TARGET_DELTA_FASTING,
        target_delta_first_meal = TARGET_DELTA_FIRST_MEAL,
        target_delta_last_meal = TARGET_DELTA_LAST_MEAL,
        target_delta_sleep = TARGET_DELTA_SLEEP,
    )

    return {
        "df_sleep": df_sleep,
        "df_sleep_sessions": df_sleep_sessions,
        "df_eat": df_eat,
        "df_eat_sessions": df_eat_sessions,
        "df_deep_fast_sessions": df_deep_fast_sessions,
        "df_first_and_last_meal": df_first_and_last_meal,
        "df_sleep_sessions_viz": df_sleep_sessions_viz,
        "df_eat_viz": df_eat_viz,
        "df_eat_sessions_viz": df_eat_sessions_viz,
        "df_deep_fast_sessions_viz": df_deep_fast_sessions_viz,
        "df_deep_fast_viz": df_deep_fast_viz,
        "df_first_meal_viz": df_first_meal_viz,
        "df_last_meal_viz": df_last_meal_viz,
        "df_sleep_duration_viz": df_sleep_duration_viz,
        "df_score": df_score,
    }


def _get_current_scores(df_score):
    ret = {}
    cols =["score_fasting", "score_first_meal", "score_last_meal", "score_sleep"]
    for c in cols:
        ser_tmp = df_score[c].dropna()
        if len(ser_tmp) > 0:
            ret[c] = ser_tmp.iloc[-1]
        else:
            ret[c] = np.nan
    ret["score"] = np.mean(list(ret.values()))
    return ret


def _get_current_and_last_score(df_score):    
    
    score_current = _get_current_scores(df_score)["score"]
    ts_current = df_score.date.dropna().iloc[-1]
    
    # Last valid
    row = df_score.dropna().iloc[-1]
    score_last = row.score
    ts_last = row.date
    
    return score_current, ts_current, score_last, ts_last


def visualize_data(
    df_sleep_sessions_viz=None, 
    df_eat_viz=None, 
    df_eat_sessions_viz=None, 
    df_deep_fast_sessions_viz=None, 
    df_deep_fast_viz=None, 
    df_first_meal_viz=None, 
    df_last_meal_viz=None, 
    df_sleep_duration_viz=None, 
    df_score=None, 
    **kwargs
):
    
    fig = make_subplots(rows=6, cols=1, shared_xaxes=True, vertical_spacing=0.025)

    # Sleep sessions
    fig.add_bar(x=pd.to_datetime(df_sleep_sessions_viz.date),
        y=df_sleep_sessions_viz.dh,
        base=df_sleep_sessions_viz.h1,
        opacity=0.8,
        marker_color='gray',
        hovertemplate=df_sleep_sessions_viz.info_html,
        name="Asleep",
        row=1, col=1
    )

    # East Sessions
    fig.add_bar(x=pd.to_datetime(df_eat_sessions_viz.date),
        y=df_eat_sessions_viz.dh,
        base=df_eat_sessions_viz.h1,
        opacity=0.2,
        marker_color='darkgreen',
        hovertemplate=df_eat_sessions_viz.info_html,
        name="Feeding Windows",
        row=1, col=1
    )

    fig.add_bar(x=pd.to_datetime(df_eat_viz.date),
        y=df_eat_viz.dh,
        base=df_eat_viz.h1,
        opacity=1.0,
        marker_color='darkgreen',
        hovertemplate=df_eat_viz.info_html,
        name="Meals",
        row=1, col=1
    )

    # Fast windows
    fig.add_bar(x=pd.to_datetime(df_deep_fast_sessions_viz.date),
        y=df_deep_fast_sessions_viz.dh,
        base=df_deep_fast_sessions_viz.h1,
        opacity=0.5,
        marker_color='aqua',
        hovertemplate=df_deep_fast_sessions_viz.info_html,
        name="Deep Fast",
        row=1, col=1
    )

    fig.add_hline(
        y=7,
        line_dash="dot",
        line_color="white",
        row=5, col=1
    )

    for df, name, color, row in zip(
        [df_deep_fast_viz, df_first_meal_viz, df_last_meal_viz, df_sleep_duration_viz], 
        ["Deep Fasting Duration", "First Meal After Sleep", "Last Meal Before Sleep", "Sleep Duration"],
        ["aqua", "orange", "yellow", "white"],
        [2, 3, 4, 5]
    ):
            
        fig.add_scatter(
            x=df.date,
            y=df.delta_in_hours,
            mode='lines+markers',
            name=name,
            opacity=0.2,
            marker_color=color,
            row=row, col=1
        )

        fig.add_scatter(
            x=df.date,
            y=df.mean_delta_in_hours,
            mode='lines',
            name=name + (" Weekly Average"),
            marker_color=color,
            row=row, col=1
        )
        
        
        

    for y, row in zip([TARGET_DELTA_FASTING, TARGET_DELTA_FIRST_MEAL, TARGET_DELTA_LAST_MEAL, TARGET_DELTA_SLEEP], [2, 3, 4, 5]):
        fig.add_hline(
            y=y,
            line_dash="dot",
            line_color="white",
            line_width=1,
            row=row, col=1
        )

    fig.add_scatter(
        x=df_score.date,
        y=df_score.score,
        mode='lines',
        name="Score",
        opacity=1,
        marker_color="red",
        row=6, col=1
    )

    score_current, ts_current, score_last, ts_last = _get_current_and_last_score(df_score)

    fig.add_scatter(
        x=[ts_last,ts_current],
        y=[score_last, score_current],
        mode='lines',
        line=dict(color='red', dash='dot'),
        row=6, col=1,
        showlegend=False
    )

    fig.add_scatter(
        x=[ts_current],
        y=[score_current],
        mode='markers',
        name="Current Score",
        marker=dict(color='red', size=6),
        row=6, col=1
    )


    fig.update_xaxes(showline=True, mirror=True, showgrid=True, range=[pd.Timestamp('2024-10-15'), pd.Timestamp.now()])

    fig.update_yaxes(showline=True, mirror=True, showgrid=False, range=[0, 24], row=1, col=1)
    for row in [2,3,4]:
        fig.update_yaxes(showline=True, mirror=True, showgrid=False, range=[0, 8], row=row, col=1)
    fig.update_yaxes(showline=True, mirror=True, showgrid=False, range=[4, 10], row=5, col=1)
    fig.update_yaxes(showline=True, mirror=True, showgrid=True, range=[0, 1], tickformat=',.0%', row=6, col=1)

    # Example for adding annotations to each subplot using the layout annotations list
    fig.update_layout(
        annotations=[
            dict(
                text="Deep Fast",
                x=0, y=1,
                xref="x2 domain",
                yref="y2 domain",
                showarrow=False,
                font=dict(color="aqua", size=12)
            ),
            dict(
                text="First Meal After Sleep",
                x=0, y=1,
                xref="x3 domain", 
                yref="y3 domain",
                showarrow=False,
                font=dict(color="orange", size=12)
            ),
            dict(
                text="Last Meal Before Sleep",
                x=0, y=1,
                xref="x4 domain",
                yref="y4 domain",
                showarrow=False,
                font=dict(color="yellow", size=12)
            ),
            dict(
                text="Sleep Duration",
                x=0, y=1,
                xref="x5 domain",
                yref="y5 domain",
                showarrow=False,
                font=dict(color="white", size=12)
            ),
        ]
    )
    
    fig.update_layout(
        margin=dict(l=0, r=10, t=10, b=10),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.05,
            xanchor="left",
            x=0.0
        )
    )
    
     # Layout
    fig.update_layout(
        barmode='overlay',
        template='plotly_dark',
        bargap=0.05,
        width=1000,
        height=1000,
    )

    return fig
    

# Main
# ----
    
st.title("Sleep, Eat, Repeat")

ret = load_data()
scores_current = _get_current_scores(ret["df_score"])



c1, c2, _ = st.columns([1, 4, 5])
with c1: 
    st.metric(label="Overall Score", value=f"{scores_current['score']:.1%}", border=True)
with c2: 
    k =["score_fasting", "score_first_meal", "score_last_meal", "score_sleep"]
    n = ["Fasting", "First Meal", "Last Meal", "Sleep"]
    v = [scores_current[k] for k in k]
    c = st.columns(len(k))
    for i, (k, v, n) in enumerate(zip(k, v, n)):
        with c[i]:
            st.metric(label=n, value=f"{v:.1%}", border=True)
    
fig = visualize_data(**ret)
st.plotly_chart(fig)

c1, _ = st.columns([1, 9])
with c1:
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()
