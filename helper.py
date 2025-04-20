import json
import pandas as pd
import numpy as np
import pytz
from datetime import timedelta, datetime
from supabase import create_client
import os

# Sleep data
# ----------

def load_sleep_data_from_json(fp):
    with open(fp, "r") as f:
        return json.load(f)    
    
def load_sleep_data_from_supabase():
    supabase_client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
    response = supabase_client.table("apple_health_sleep_analysis").select("*").execute()
    df_sleep = pd.DataFrame(response.data)
    df_sleep = df_sleep[df_sleep.value != "Awake"]
    df_sleep["ts_start"] = pd.to_datetime(df_sleep["ts_start"])
    df_sleep["ts_end"] = pd.to_datetime(df_sleep["ts_end"])
    return df_sleep

def process_raw_sleep_data(sleep_data):

    df_sleep = pd.DataFrame(sleep_data)

    # only keep asleep states
    df_sleep = df_sleep[df_sleep.value.isin([1,3,4,5])]

    # convert to datetime
    df_sleep["ts_start"] = pd.to_datetime(df_sleep["start"])
    df_sleep["ts_end"] = pd.to_datetime(df_sleep["end"])
    
    # drop some columns
    df_sleep = df_sleep[["id", "ts_start", "ts_end", "value", "valueDescription"]]
    
    return df_sleep

# Eat data
# -------

def load_eat_data_from_supabase(min_eat_duration_in_min = 15):
    
    supabase_client = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
    response = supabase_client.table("foodlog").select("*").execute()
    df_eat = pd.DataFrame(response.data)
    df_eat["ts_start"] = pd.to_datetime(df_eat["ts_start"])
    df_eat["ts_end"] = pd.to_datetime(df_eat["ts_end"])
    eat_data = df_eat.to_dict("records")

    dt = timedelta(minutes=min_eat_duration_in_min) 
    for e in eat_data:    
        if e["ts_end"] - e["ts_start"] < dt:
            e["ts_end"] = e["ts_start"] + dt
    df_eat = pd.DataFrame(eat_data)
    df_eat["info_dict"] = df_eat.apply(lambda row: {"description": row.description, "id": row.id}, axis=1)
    
    df_eat["value"] = df_eat["description"]
    
    return df_eat

def load_raw_eat_data(fp):
    return pd.read_csv(fp, names=["ts_start", "ts_end", "rating", "description"]).to_dict("records")

def process_raw_eat_data(eat_data, min_eat_duration_in_min = 15):

    df_eat = pd.DataFrame(eat_data)
    
    # TOTO: make this nicer
    df_eat["ts_start"] = pd.to_datetime(df_eat["ts_start"], utc=True)
    df_eat["ts_end"] = pd.to_datetime(df_eat["ts_end"], utc=True)
    eat_data = df_eat.to_dict("records")

    dt = timedelta(minutes=min_eat_duration_in_min) 
    for e in eat_data:    
        if e["ts_end"] - e["ts_start"] < dt:
            e["ts_end"] = e["ts_start"] + dt
    df_eat = pd.DataFrame(eat_data)
    df_eat["info_dict"] = df_eat.apply(lambda row: {"description": row.description, "rating": row.rating}, axis=1)
    return df_eat

# Sleep Durations
# ---------------

def process_sleep_sessions_for_viz(df_sleep_sessions, timezone = "UTC"):
    
    df_sleep_duration_viz = df_sleep_sessions.copy()
    df_sleep_duration_viz["ts_end"] = df_sleep_duration_viz.ts_end.apply(lambda x: x.tz_convert(timezone))
    df_sleep_duration_viz["date"] = df_sleep_duration_viz.ts_end.dt.date
    df_sleep_duration_viz["delta_in_hours"] = df_sleep_duration_viz["sleep_duration_in_hours"]
    df_sleep_duration_viz = fill_missing_dates(df_sleep_duration_viz[["date", "delta_in_hours"]], fill_value=0)
    
    # When there are multiple sessions per day, we sum them up.
    df_sleep_duration_viz = df_sleep_duration_viz.groupby("date").agg("sum").reset_index()
    
    # TODO: When the duration is np.nan (because only in bed) we should keep it maybe at 0
    # df_sleep_duration_viz.loc[df_sleep_duration_viz["delta_in_hours"] == 0, "delta_in_hours"] = np.nan
    
    df_sleep_duration_viz["mean_delta_in_hours"] = df_sleep_duration_viz.delta_in_hours.rolling(7).mean()

    return df_sleep_duration_viz

# Deep fasting
# ------------

def evaluate_deep_fast_sessions(df_eat_sessions, dt_deep_fast_in_hours):
    
    # take as a ts_start the ts_start of the easting session + dt_deep_fast_in_hours
    # take as a ts_end the ts_start of the next easting session
    ser_ts_start = df_eat_sessions.ts_end + timedelta(hours=dt_deep_fast_in_hours)
    ser_ts_end = pd.to_datetime(df_eat_sessions.ts_start.shift(-1).fillna(datetime.now(tz=pytz.timezone("UTC"))))
    df_deep_fast_sessions = pd.DataFrame(data={'ts_start': ser_ts_start, 'ts_end': ser_ts_end})
    
    # check the resulting fasting duration and drop the ones with a negative duration
    df_deep_fast_sessions["delta_in_hours"] = (df_deep_fast_sessions["ts_end"] - df_deep_fast_sessions["ts_start"]).dt.total_seconds() / 60 / 60
    df_deep_fast_sessions = df_deep_fast_sessions[df_deep_fast_sessions["delta_in_hours"] > 0]
    
    # add some infos
    df_deep_fast_sessions["info_dict"] = df_deep_fast_sessions.apply(lambda row: {"delta_in_hours": row.delta_in_hours}, axis=1)
    
    return df_deep_fast_sessions

def process_deep_fast_sessions_for_viz(df_deep_fast_sessions, timezone='UTC'):
    
    # convert to desired timezone
    df_deep_fast_sessions["ts_start"] = df_deep_fast_sessions.ts_start.apply(lambda x: x.tz_convert(timezone))
    df_deep_fast_sessions["ts_end"] = df_deep_fast_sessions.ts_end.apply(lambda x: x.tz_convert(timezone))
    df_deep_fast_sessions["date"] = df_deep_fast_sessions.ts_end.dt.date
    
    df_deep_fast_duration = fill_missing_dates(df_deep_fast_sessions[["date", "delta_in_hours"]], fill_value=0)
    
    # When there are multiple deep fast sessions per date, take the larger one
    df_deep_fast_duration = df_deep_fast_duration.sort_values(by = "delta_in_hours").groupby("date").last().reset_index().sort_values(by="date") 

    df_deep_fast_duration["mean_delta_in_hours"] = df_deep_fast_duration.delta_in_hours.rolling(7).mean()
    
    return df_deep_fast_duration



# Meals before and after sleep sessions
# -------------------------------------

def evaluate_delta_to_first_and_last_meal(df_sleep_sessions, df_eat):

    df = df_sleep_sessions.copy()

    df["ts_start_first_meal_after"] = None
    df["ts_end_last_meal_before"] = None
    
    for idx, row in df.iterrows():
        
        # find the first meal after the sleep session
        ser = df_eat.ts_start - row.ts_end
        ser = ser[ser > timedelta(seconds=0)]
        if len(ser) == 0:
            ts_start_first_meal_after = pd.to_datetime(np.nan)
        else:
            ts_start_first_meal_after = df_eat.loc[ser.idxmin()].ts_start

        # find the last meal before sleep session
        ser = row.ts_start - df_eat.ts_end
        ser = ser[ser > timedelta(seconds=0)]
        if len(ser) == 0:
            ts_end_last_meal_before = pd.to_datetime(np.nan)
        else:
            ts_end_last_meal_before = df_eat.loc[ser.idxmin()].ts_end
        
        # add to dataframe
        df.loc[idx, "ts_start_first_meal_after"] = ts_start_first_meal_after 
        df.loc[idx, "ts_end_last_meal_before"] = ts_end_last_meal_before   
        
        
    for k in ["ts_start_first_meal_after", "ts_end_last_meal_before"]:
        df[k] = pd.to_datetime(df[k])
        
    df["delta_first_meal_after_in_hours"] = (df.ts_start_first_meal_after - df.ts_end).dt.total_seconds() / 60 /60
    df["delta_last_meal_before_in_hours"] = (df.ts_start - df.ts_end_last_meal_before).dt.total_seconds() / 60 /60
    
    return df
    
    
def process_first_and_last_meal_data_for_viz(df, timezone="UTC"):

    # first convert all the timestamps to the desired timezone
    for c in df.columns:
        if c.startswith("ts_"):
            df[c] = df[c].apply(lambda x: x.tz_convert(timezone))

    # as a date we take ts_end_last_meal_before and ts_start_first_meal_after
    df["date_first_meal_after"] = df.ts_start_first_meal_after.dt.date
    df["date_last_meal_before"] = df.ts_end_last_meal_before.dt.date

    # derive individual dataframe from the last and the first meal
    dfs = []
    for k in ["first_meal_after", "last_meal_before"]:
        col = {
            f"date_{k}": "date",
            f"delta_{k}_in_hours": "delta_in_hours"
        }
        df_tmp = df[list(col.keys())].rename(columns=col).dropna(subset=["date"])
        df_tmp = fill_missing_dates(df_tmp) 
        
        # if there were multiple sleep sessions per date, we take the smallest value
        df_tmp = df_tmp.sort_values(by = "delta_in_hours").groupby("date").first().reset_index().sort_values(by="date") 
        df_tmp["mean_delta_in_hours"] = df_tmp.delta_in_hours.rolling(7).mean()
        dfs.append(df_tmp.copy())

    return dfs       


# Score
# -----

def calculate_score(
    df_deep_fast_viz, 
    df_first_meal_viz, 
    df_last_meal_viz, 
    df_sleep_duration_viz,
    target_delta_fasting = 4,
    target_delta_first_meal = 1,
    target_delta_last_meal = 3,
    target_delta_sleep = 7,
    rolling_window_days = 7,
):
    dfs = []

    for name, target, df in zip(
        ["fasting", "first_meal", "last_meal", "sleep"],
        [target_delta_fasting, target_delta_first_meal, target_delta_last_meal, target_delta_sleep],
        [df_deep_fast_viz, df_first_meal_viz, df_last_meal_viz, df_sleep_duration_viz]
    ):
        df_tmp = df[["date", "delta_in_hours"]].copy()
        df_tmp[f"score_{name}"] = (df_tmp.delta_in_hours > target).astype(int).rolling(rolling_window_days).mean()
        df_tmp = df_tmp.drop(columns=["delta_in_hours"])
        dfs.append(df_tmp)

    df = dfs[0].merge(dfs[1], on="date", how="outer").merge(dfs[2], on="date", how="outer").merge(dfs[3], on="date", how="outer").set_index("date")
    
    df["score"] = df.mean(axis=1).where(df.notna().all(axis=1))

    return df.reset_index()


# General Funcs
# -------------

def identify_sessions(df, min_gap_between_sessions_in_minutes=60*12, min_duration_of_session_in_minutes=0, add_sleep_duration_in_hours=False):

    df_agg = df.copy()

    # calculate gap to next sleep period
    df_agg = df_agg.sort_values("ts_start").reset_index(drop=True)
    df_agg["gap_to_next_in_minutes"] = (df_agg["ts_start"].shift(-1) - df_agg["ts_end"]).dt.total_seconds() / 60
    df_agg["sleep_duration_in_hours"] = np.where(
        df_agg["value"] != "InBed",
        (df_agg["ts_end"] - df_agg["ts_start"]).dt.total_seconds() / 60 / 60,
        np.nan
    )
    
    # assign sleep session
    df_agg["session"] = np.nan
    current_session = 0 
    for i in range(len(df_agg)):
        df_agg.loc[i, "session"] = current_session   
        if df_agg.loc[i, "gap_to_next_in_minutes"] > min_gap_between_sessions_in_minutes:
            current_session += 1
    df_agg["session"] = df_agg["session"].astype(int)
    
    # group by sleep-session
    df_agg = df_agg.groupby("session").agg(
        ts_start = ("ts_start", "min"),
        ts_end = ("ts_end", "max"),
        sleep_duration_in_hours = ("sleep_duration_in_hours", lambda x: x.sum() if not x.isna().all() else np.nan),
    ).reset_index().sort_values("ts_start")
    
    # remove sessions that are too short (whatever the threshold is)
    df_agg["duration_in_hours"] = (df_agg["ts_end"] - df_agg["ts_start"]).dt.total_seconds() / 60 / 60
    df_agg = df_agg[df_agg.duration_in_hours >= min_duration_of_session_in_minutes/60]

    if add_sleep_duration_in_hours:
        df_agg["info_dict"] = df_agg.apply(lambda row: {"session": row.session, "duration_in_hours": row.duration_in_hours, "sleep_duration_in_hours": row.sleep_duration_in_hours}, axis=1)
    else:
        df_agg["info_dict"] = df_agg.apply(lambda row: {"session": row.session, "duration_in_hours": row.duration_in_hours}, axis=1)
        df_agg.drop(columns=["sleep_duration_in_hours"], inplace=True)

    return df_agg



def process_for_visualization(df_sleep, tz):

    current_timezone = pytz.timezone(tz)

    data = []

    for _, row in df_sleep.iterrows():    
        
        t1 = row["ts_start"].tz_convert(current_timezone)
        t2 = row["ts_end"].tz_convert(current_timezone)
        assert t1 <= t2, "t1 is larger or equal to t2!!!" # Todo: Ensure a minimum...

        d1 = t1.date()
        h1 = t1.hour + t1.minute / 60
        d2 = t2.date()
        h2 = t2.hour + t2.minute / 60

        if "info_dict" in row:
            info_html = "<br>".join([f"{k}: {v}" for k, v in row.info_dict.items()])
        else:
            info_html = ""
        info_html += f"<br>from: {t1}"
        info_html += f"<br>to: {t2}"

        if d1 != d2:
        
            data.append({
                "date": d1,
                "h1": h1,
                "h2": 24,
                "dh": 24 - h1,
                "info_html": info_html
            })

            for i in range(1, (d2 - d1).days):
                d = d1 + i * timedelta(days=1)
                data.append({
                    "date": d,
                    "h1": 0,
                    "h2": 24,
                    "dh": 24,
                    "info_html": info_html
                })
                
            data.append({
                "date": d2,
                "h1": 0,
                "h2": h2,
                "dh": h2,
                "info_html": info_html
            })
        
        else:
            data.append({
                "date": d1,
                "h1": h1,
                "h2": h2,
                "dh": h2 - h1,
                "info_html": info_html
            })        

    df_sleep_tz = pd.DataFrame(data)

    return df_sleep_tz


def fill_missing_dates(df, date_key = "date", fill_value=0):
    df = df.copy()
    df[date_key] = pd.to_datetime(df[date_key])
    df_tmp = pd.DataFrame(pd.date_range(start=df[date_key].min(), end=df[date_key].max()), columns=[date_key])
    return df.merge(df_tmp, on=date_key, how="outer").fillna(fill_value)