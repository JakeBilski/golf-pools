import json, sys, datetime

tournament_id = sys.argv[1] if len(sys.argv) > 1 else ''

try:
    with open('/tmp/espn_raw.json') as f:
        data = json.load(f)
except Exception as e:
    result = {"error": str(e), "golfers": [], "tournamentId": tournament_id}
    with open('scores.json', 'w') as f:
        json.dump(result, f)
    sys.exit(0)

events = data.get('events', [])
if not events:
    result = {"error": "No events in ESPN response", "golfers": [], "tournamentId": tournament_id}
    with open('scores.json', 'w') as f:
        json.dump(result, f)
    sys.exit(0)

event = events[0]
comp = event.get('competitions', [{}])[0]
competitors = comp.get('competitors', [])
status_detail = comp.get('status', {}).get('type', {}).get('detail', '')
status_name   = comp.get('status', {}).get('type', {}).get('name', '')
tourn_name    = event.get('name', event.get('shortName', ''))

def detect_round(status):
    s = status.lower()
    if '4' in s or 'final' in s: return 'R4'
    if '3' in s: return 'R3'
    if '2' in s: return 'R2'
    return 'R1'

current_round = detect_round(status_detail + ' ' + status_name)

def parse_par(val):
    if val is None or val == '' or val == '--': return None
    s = str(val).strip().upper()
    if s == 'E': return 0
    if s in ('MC', 'CUT', 'WD', 'DQ'): return 20
    try: return int(s.replace('+', ''))
    except: return None

golfers = []
for c in competitors:
    athlete = c.get('athlete', {})
    stats = c.get('statistics', [])
    linescores = c.get('linescores', [])

    def find_stat(*names):
        for name in names:
            for s in stats:
                if s.get('name') == name or s.get('abbreviation') == name:
                    v = s.get('displayValue') or s.get('value')
                    if v is not None and str(v).strip() not in ('', '--'):
                        return str(v).strip()
        return None

    is_cut = c.get('status', '').lower() in ('cut', 'wd', 'dq')

    # Count how many rounds have actual numeric scores
    scored_rounds = []
    for ls in linescores:
        dv = ls.get('displayValue', ls.get('value'))
        if dv is not None and str(dv).strip() not in ('', '--'):
            scored_rounds.append(ls)
    num_scored = len(scored_rounds)

    thru_raw = find_stat('thru', 'holesPlayed', 'THRU')

    # ── Thru detection (improved) ──
    # Priority 1: Tournament-level final status means everyone is F
    if status_name in ('STATUS_FINAL', 'STATUS_PLAY_COMPLETE'):
        thru = 'F'
    # Priority 2: Explicit thru value from ESPN stats
    elif thru_raw is not None:
        thru_str = str(thru_raw).strip().upper()
        if thru_str == 'F' or thru_str == '18':
            thru = 'F'
        elif thru_str.isdigit() and int(thru_str) > 0:
            thru = thru_str
        else:
            thru = thru_str if thru_str != '--' else '-'
    # Priority 3: Player was cut/WD/DQ — they're done
    elif is_cut:
        thru = 'F'
    # Priority 4: Infer from linescores — if they have scores for the current round, they finished
    else:
        round_num = int(current_round[1]) if current_round and len(current_round) > 1 else 1
        if num_scored >= round_num:
            thru = 'F'
        elif num_scored > 0 and num_scored == round_num - 1:
            # They have previous round scores but not the current one — check tee time
            tee_time = c.get('teeTime', '')
            if tee_time:
                try:
                    from datetime import datetime as dt, timezone, timedelta
                    t_obj = dt.fromisoformat(tee_time.replace('Z', '+00:00'))
                    et = timezone(timedelta(hours=-4))
                    t_et = t_obj.astimezone(et)
                    now_et = dt.now(et)
                    # If tee time is in the past, they should be on the course
                    if t_et < now_et:
                        thru = '-'  # On course but no hole data
                    else:
                        thru = t_et.strftime('%-I:%M %p')
                except:
                    thru = tee_time
            else:
                thru = '-'
        else:
            thru = '-'

    rounds = [parse_par(ls.get('displayValue', ls.get('value'))) for ls in linescores[:4]]
    while len(rounds) < 4:
        rounds.append(None)

    name = athlete.get('displayName', athlete.get('shortName', ''))
    if not name: continue

    pos = c.get('position', {}).get('displayName') or str(len(golfers) + 1)

    golfers.append({
        'pos':   'MC' if is_cut else pos,
        'name':  name,
        'flag':  '',
        'score': parse_par(find_stat('scoreToPar', 'TOT') or c.get('score')),
        'today': parse_par(find_stat('roundScore', 'TODAY', 'RD')),
        'thru':  thru,
        'r':     rounds
    })

active = sorted([g for g in golfers if g['pos'] != 'MC'], key=lambda g: (g['score'] or 99))
cut    = [g for g in golfers if g['pos'] == 'MC']
for i, g in enumerate(active):
    g['pos'] = i + 1

ts = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

result = {
    'tournamentId':   tournament_id,
    'tournamentName': tourn_name,
    'status':         status_detail,
    'round':          current_round,
    'lastUpdated':    ts,
    'golfers':        active + cut
}

with open('scores.json', 'w') as f:
    json.dump(result, f)

print(f"Done: {tourn_name}, {len(active + cut)} golfers, {status_detail}")
