"""
intervals.icu → data.json
Läuft mehrfach täglich. Holt immer die aktuellsten Daten.
"""
import requests, json, os
from datetime import date, timedelta
from collections import defaultdict

ATHLETE = os.environ.get("INTERVALS_ATHLETE", "i415605")
API_KEY  = os.environ["INTERVALS_API_KEY"]
AUTH     = ("API_KEY", API_KEY)
BASE     = f"https://intervals.icu/api/v1/athlete/{ATHLETE}"
START    = "2026-01-01"
TODAY    = date.today().strftime("%Y-%m-%d")
YEST     = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

def get(path, params=None):
    r = requests.get(f"{BASE}/{path}", auth=AUTH, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

print(f"Fetching {START} → {TODAY}...")
wellness   = get("wellness",   {"oldest": START, "newest": TODAY})
activities = get("activities", {"oldest": START, "newest": TODAY,
    "fields": "type,moving_time,icu_training_load,start_date_local"})

W = {d["id"]: d for d in wellness}

def sleep_fmt(secs):
    if not secs: return None
    h = int(secs // 3600)
    m = int((secs % 3600) // 60)
    return f"{h}:{m:02d}"

# Daily training
daily_train = defaultdict(lambda: {"min": 0, "load": 0})
for a in activities:
    ds = a["start_date_local"][:10]
    daily_train[ds]["min"]  += round((a.get("moving_time") or 0) / 60)
    daily_train[ds]["load"] += round(a.get("icu_training_load") or 0)

# Today snapshot (sleep + weight — morning data)
t = W.get(TODAY, {})
today_snap = {
    "date":    TODAY,
    "weight":  t.get("weight"),
    "rhr":     t.get("restingHR"),
    "sleep":   sleep_fmt(t.get("sleepSecs")),
    "sleep_score": t.get("sleepScore"),
    "bodyFat": t.get("bodyFat"),
}

# Yesterday snapshot (full-day data: steps, kcal, protein)
y = W.get(YEST, {})
yest_snap = {
    "date":    YEST,
    "steps":   y.get("steps"),
    "kcal":    y.get("kcalConsumed"),
    "protein": y.get("protein"),
    "carbs":   y.get("carbohydrates"),
}

# Weekly aggregates
def week_key(date_str):
    d = date.fromisoformat(date_str)
    mon = d - timedelta(days=d.weekday())
    sun = mon + timedelta(days=6)
    return mon.strftime("%Y-%m-%d"), sun.strftime("%Y-%m-%d"), int(d.strftime("%V"))

all_dates, cur, end_d = [], date.fromisoformat(START), date.today()
while cur <= end_d:
    all_dates.append(cur.strftime("%Y-%m-%d")); cur += timedelta(days=1)

weeks_data = defaultdict(lambda: {
    "weights":[], "rhrs":[], "sleeps":[], "steps":[],
    "kcals":[], "proteins":[], "mins":0, "loads":0,
    "mon":"", "sun":"", "kw":0
})

for ds in all_dates:
    mon, sun, kw = week_key(ds)
    wk = f"{mon}/{sun}"
    weeks_data[wk].update({"mon": mon, "sun": sun, "kw": kw})
    w = W.get(ds, {})
    if w.get("weight"):       weeks_data[wk]["weights"].append(w["weight"])
    if w.get("restingHR"):    weeks_data[wk]["rhrs"].append(w["restingHR"])
    if w.get("sleepSecs"):    weeks_data[wk]["sleeps"].append(w["sleepSecs"]/3600)
    if w.get("steps"):        weeks_data[wk]["steps"].append(w["steps"])
    if w.get("kcalConsumed"): weeks_data[wk]["kcals"].append(w["kcalConsumed"])
    if w.get("protein"):      weeks_data[wk]["proteins"].append(w["protein"])
    t = daily_train.get(ds)
    if t: weeks_data[wk]["mins"] += t["min"]; weeks_data[wk]["loads"] += t["load"]

def avg(lst, dec=1): return round(sum(lst)/len(lst), dec) if lst else None
def avgi(lst):       return round(sum(lst)/len(lst)) if lst else None
def sleep_avg(lst):
    if not lst: return None
    h = int(sum(lst)/len(lst)); m = round((sum(lst)/len(lst) - h)*60)
    return f"{h}:{m:02d}"

result_weeks = []
for wk_key in sorted(weeks_data.keys()):
    d = weeks_data[wk_key]
    if not d["mon"]: continue
    mon_d = date.fromisoformat(d["mon"]); sun_d = date.fromisoformat(d["sun"])
    result_weeks.append({
        "key":      wk_key,
        "kw":       f"KW {d['kw']}",
        "period":   f"{mon_d.strftime('%-d. %b')}–{sun_d.strftime('%-d. %b')}",
        "weight":   avg(d["weights"]),
        "rhr":      avgi(d["rhrs"]),
        "sleep":    sleep_avg(d["sleeps"]),
        "steps":    avgi(d["steps"]),
        "kcal":     avgi(d["kcals"]),
        "protein":  avgi(d["proteins"]),
        "train_min": d["mins"] or None,
        "load":     d["loads"] or None,
    })

# Current week averages for widget
cur_week_key = None
for wk_key in sorted(weeks_data.keys(), reverse=True):
    if weeks_data[wk_key]["mon"]:
        cur_week_key = wk_key; break

cw = next((w for w in result_weeks if w["key"] == cur_week_key), {})
pw = result_weeks[-2] if len(result_weeks) >= 2 else {}

output = {
    "generated":  f"{TODAY}T{__import__('datetime').datetime.now().strftime('%H:%M')}",
    "today":      today_snap,
    "yesterday":  yest_snap,
    "current_week": cw,
    "prev_week":    pw,
    "weeks":        result_weeks,
    "targets": {
        "steps":   10000,
        "sleep":   "7:30",
        "sleep_h": 7.5,
        "protein": 185,
        "kcal":    2600,
    }
}

os.makedirs("data", exist_ok=True)
with open("data/data.json","w") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"✓ {len(result_weeks)} Wochen → data/data.json ({TODAY})")
