"""
intervals.icu → data.json v2
Korrekte Wochendurchschnitte: heute-Metriken vs. gestern-Metriken getrennt.
"""
import requests, json, os
from datetime import date, timedelta
from collections import defaultdict

ATHLETE = os.environ.get("INTERVALS_ATHLETE", "i415605")
API_KEY  = os.environ["INTERVALS_API_KEY"]
AUTH     = ("API_KEY", API_KEY)
BASE     = f"https://intervals.icu/api/v1/athlete/{ATHLETE}"
START    = "2026-01-01"
TODAY    = date.today()
YEST     = TODAY - timedelta(days=1)
TODAY_S  = TODAY.strftime("%Y-%m-%d")
YEST_S   = YEST.strftime("%Y-%m-%d")

def get(path, params=None):
    r = requests.get(f"{BASE}/{path}", auth=AUTH, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

print(f"Fetching {START} → {TODAY_S}...")
wellness   = get("wellness",   {"oldest": START, "newest": TODAY_S})
activities = get("activities", {"oldest": START, "newest": TODAY_S,
    "fields": "type,moving_time,icu_training_load,start_date_local"})

W = {d["id"]: d for d in wellness}

def sleep_fmt(secs):
    if not secs: return None
    return f"{int(secs//3600)}:{int((secs%3600)//60):02d}"

def sleep_h(s):
    if not s: return None
    h, m = map(int, s.split(":"))
    return h + m/60

# Daily training
daily_train = defaultdict(lambda: {"min": 0, "load": 0})
for a in activities:
    ds = a["start_date_local"][:10]
    daily_train[ds]["min"]  += round((a.get("moving_time") or 0) / 60)
    daily_train[ds]["load"] += round(a.get("icu_training_load") or 0)

# Today snapshot (morning metrics: sleep, weight, rhr)
t = W.get(TODAY_S, {})
today_snap = {
    "date":    TODAY_S,
    "weight":  t.get("weight"),
    "rhr":     t.get("restingHR"),
    "sleep":   sleep_fmt(t.get("sleepSecs")),
    "sleep_score": t.get("sleepScore"),
    "bodyFat": t.get("bodyFat"),
}

# Yesterday snapshot (full-day metrics: steps, kcal, protein)
y = W.get(YEST_S, {})
yest_snap = {
    "date":    YEST_S,
    "steps":   y.get("steps"),
    "kcal":    y.get("kcalConsumed"),
    "protein": y.get("protein"),
    "carbs":   y.get("carbohydrates"),
}

# Weekly aggregates — KEY FIX: separate today vs yesterday metrics
def week_bounds(d):
    mon = d - timedelta(days=d.weekday())
    sun = mon + timedelta(days=6)
    return mon, sun, int(d.strftime("%V"))

all_dates, cur = [], date.fromisoformat(START)
while cur <= TODAY:
    all_dates.append(cur); cur += timedelta(days=1)

weeks_data = defaultdict(lambda: {
    # today-metrics (include today)
    "weights":[], "rhrs":[], "sleeps":[],
    # yesterday-metrics (exclude today)
    "steps":[], "kcals":[], "proteins":[],
    "mins":0, "loads":0,
    "mon":None, "sun":None, "kw":0
})

for d in all_dates:
    ds = d.strftime("%Y-%m-%d")
    mon, sun, kw = week_bounds(d)
    wk = f"{mon.strftime('%Y-%m-%d')}/{sun.strftime('%Y-%m-%d')}"
    wd = weeks_data[wk]
    wd["mon"] = mon; wd["sun"] = sun; wd["kw"] = kw
    w = W.get(ds, {})
    
    # today-metrics: include all days up to and including today
    if w.get("weight"):    wd["weights"].append(w["weight"])
    if w.get("restingHR"): wd["rhrs"].append(w["restingHR"])
    if w.get("sleepSecs"): wd["sleeps"].append(w["sleepSecs"]/3600)
    
    # yesterday-metrics: ONLY include days strictly before today
    if d < TODAY:
        if w.get("steps"):        wd["steps"].append(w["steps"])
        if w.get("kcalConsumed"): wd["kcals"].append(w["kcalConsumed"])
        if w.get("protein"):      wd["proteins"].append(w["protein"])
    
    tr = daily_train.get(ds)
    if tr: wd["mins"] += tr["min"]; wd["loads"] += tr["load"]

def avg(lst, dec=1): return round(sum(lst)/len(lst), dec) if lst else None
def avgi(lst):       return round(sum(lst)/len(lst)) if lst else None
def sleep_avg(lst):
    if not lst: return None
    total = sum(lst)/len(lst)
    return f"{int(total)}:{round((total%1)*60):02d}"

result_weeks = []
for wk_key in sorted(weeks_data.keys()):
    d = weeks_data[wk_key]
    if not d["mon"]: continue
    mon_d, sun_d = d["mon"], d["sun"]
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

cw = result_weeks[-1] if result_weeks else {}
pw = result_weeks[-2] if len(result_weeks) >= 2 else {}

output = {
    "generated": f"{TODAY_S}T{__import__('datetime').datetime.now().strftime('%H:%M')}",
    "today":     today_snap,
    "yesterday": yest_snap,
    "current_week": cw,
    "prev_week":    pw,
    "weeks":        result_weeks,
    "targets": {
        "steps": 10000, "sleep": "7:30", "sleep_h": 7.5,
        "protein": 185, "kcal": 2600,
    }
}

os.makedirs("data", exist_ok=True)
with open("data/data.json","w") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print(f"✓ data.json geschrieben — KW-Ø korrekt (heute-Metriken vs. gestern-Metriken getrennt)")
