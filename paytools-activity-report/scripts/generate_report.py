#!/usr/bin/env python3
"""
Paytools Team Activity Report Generator
Usage: python3 generate_report.py --input <audit_log.json> --output <report.html>
"""

import argparse, json, os, sys
from datetime import datetime, timezone, timedelta, date
from collections import defaultdict, Counter

AEDT = timezone(timedelta(hours=11))

def to_aedt(dt_str):
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    return dt.astimezone(AEDT)

def fmt_time(dt): return dt.strftime('%H:%M') if dt else ''
def fmt_dt(dt): return dt.strftime('%d/%m/%Y %H:%M') if dt else ''
def fmt_span(minutes):
    if minutes < 60: return f"{minutes}m"
    return f"{minutes/60:.1f}h"
def fmt_start(mins):
    return f"{int(mins)//60:02d}:{int(mins)%60:02d}"
def initials(name):
    parts = name.split()
    return (parts[0][0]+parts[-1][0]).upper() if len(parts) >= 2 else name[:2].upper()

def categorize(typ):
    t = typ.lower()
    if t == 'check': return 'Check Tasks'
    if t == 'checklist': return 'Checklist Actions'
    if 'active storage' in t: return 'File Attachments'
    if t == 'comment': return 'Comments'
    if 'calendar event' in t or 'pay group calendar event' in t: return 'Calendar Events'
    if t in ['employee', 'adjustment', 'overpayment', 'underpayment']: return 'Employee Work'
    if t in ['raci stakeholder', 'obligation', 'obligation review', 'issue']: return 'Governance'
    return 'Config / Templates'

ROLE_BADGE_STYLE = {
    'Manager':       'background:#EDE9FE;color:#5B21B6',
    'Officer':       'background:#CCFBF1;color:#0D766E',
    'Specialist':    'background:#FCE7F3;color:#9D174D',
    'Administrator': 'background:#FEF3C7;color:#92400E',
}
AVATAR_BG = {
    'Manager':    ('#5B21B6', '#7C3AED'),
    'Officer':    ('#0D766E', '#0F9E93'),
    'Specialist': ('#9D174D', '#BE185D'),
    'Administrator': ('#92400E', '#B45309'),
}

CONFIG_TYPES = {
    'check definition', 'check definition checklist definition', 'checklist definition',
    'calendar event checklist definition', 'location', 'notification', 'pay group user',
    'freshdesk api key', 'field definition', 'approval definition user', 'pay group calendar event',
    'calendar event', 'calendar event occurrence', 'team user', 'user company', 'user',
}

CONFIG_TYPE_LABELS = {
    'check definition':                        'Check Template',
    'checklist definition':                    'Checklist Template',
    'check definition checklist definition':   'Check → Checklist Assignment',
    'calendar event checklist definition':     'Calendar Event → Checklist',
    'calendar event':                          'Calendar Event',
    'calendar event occurrence':               'Calendar Event Occurrence',
    'pay group calendar event':                'Pay Group → Calendar Event',
    'pay group user':                          'Pay Group Member',
    'approval definition user':                'Approver Assignment',
    'field definition':                        'Custom Field',
    'location':                                'Location',
    'notification':                            'Notification',
    'team user':                               'Team Member',
    'user company':                            'User Organisation',
    'user':                                    'User',
    'freshdesk api key':                       'Freshdesk Integration',
}

CONFIG_ACTION_LABELS = {
    'create':  'Created',
    'update':  'Updated',
    'remove':  'Removed',
    'destroy': 'Deleted',
    'archive': 'Archived',
}

def humanise_config_type(raw):
    return CONFIG_TYPE_LABELS.get(raw.lower(), raw.replace('_', ' ').title())

def humanise_config_action(raw):
    return CONFIG_ACTION_LABELS.get(raw.lower(), raw.title())

def infer_role(name, cats):
    """Infer role from action patterns — check-heavy = Officer, checklist-approver = Manager,
    config-only = Specialist. Falls back gracefully."""
    total = sum(cats.values())
    if total == 0: return ('Unknown', 'Officer')
    check_pct = cats.get('Check Tasks', 0) / total
    checklist_pct = cats.get('Checklist Actions', 0) / total
    config_pct = cats.get('Config / Templates', 0) / total
    if check_pct >= 0.6: return ('Payroll Officer', 'Officer')
    if checklist_pct >= 0.5: return ('Payroll Manager', 'Manager')
    if config_pct >= 0.7: return ('Payroll Specialist', 'Specialist')
    if check_pct >= 0.3 or checklist_pct >= 0.3: return ('Payroll Officer', 'Officer')
    return ('Payroll Specialist', 'Specialist')

def heat_level(n):
    if n == 0: return 'h0'
    if n <= 20: return 'h1'
    if n <= 60: return 'h2'
    if n <= 120: return 'h3'
    return 'h4'

def ordinal(n):
    if 11 <= n % 100 <= 13: return f"{n}th"
    return f"{n}{['th','st','nd','rd','th','th','th','th','th','th'][n%10]}"

def natural_period_name(name):
    """Convert 'Period Ending 17/05/2026' → 'Period Ending 17th May 2026'."""
    try:
        raw = name.replace('Period Ending ', '')
        dt = datetime.strptime(raw, '%d/%m/%Y')
        return f"Period Ending {ordinal(dt.day)} {dt.strftime('%B %Y')}"
    except:
        return name

def extract_pay_group(checklist_def_names):
    """Extract pay group code from checklist definition names, e.g. 'Laminex AU Fortnightly (F4) Friday' → 'F4'."""
    import re
    codes = set()
    for name in checklist_def_names:
        m = re.search(r'\(([^)]+)\)', name)
        if m:
            codes.add(m.group(1))
    if not codes:
        return ''
    # If all codes are the same, return it; otherwise return sorted joined
    return ', '.join(sorted(codes))

def parse_period_date(name):
    try: return datetime.strptime(name.replace('Period Ending ', ''), '%d/%m/%Y')
    except: return datetime.min

def badge(role_key, text):
    s = ROLE_BADGE_STYLE.get(role_key, 'background:#F3F4F6;color:#555769')
    return f'<span class="badge" style="{s}">{text}</span>'

def progress_bar(val, max_val, color='var(--purple)'):
    pct = min(100, int(val / max_val * 100)) if max_val else 0
    return f'<div class="bar-wrap"><div class="bar-fill" style="width:{pct}%;background:{color}"></div></div>'

def wday_dots(wday_active):
    labels = ['M', 'T', 'W', 'T', 'F']
    return ''.join(
        f'<span class="wday-item"><span class="wday-dot {"wday-on" if wday_active[i] else "wday-off"}"></span>'
        f'<span class="wday-lbl">{labels[i]}</span></span>'
        for i in range(5)
    )

def action_dot(act):
    colors = {'create': 'var(--green)', 'update': 'var(--purple)', 'remove': 'var(--red)',
              'destroy': 'var(--red)', 'deactivate': 'var(--amber)'}
    c = colors.get(act, 'var(--grey-400)')
    return f'<span class="action-dot" style="background:{c}"></span>'

# ── CSS ──────────────────────────────────────────────────────────────────────
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --purple:#3339F2;--purple-light:#F4F1FE;--purple-mid:#7B6EF5;--purple-100:#D9D0FC;
  --teal:#14B8A6;--teal-light:#CCFBF1;--amber:#FBC231;--amber-light:#FEF3C7;
  --red:#FB757C;--red-light:#FEE2E4;--green:#58DFB5;
  --grey-50:#F9FAFB;--grey-100:#F3F4F6;--grey-200:#E5E7EB;--grey-400:#9CA3AF;
  --grey-500:#757780;--grey-600:#555769;--grey-700:#374151;--grey-800:#1F2937;
}
body{font-family:'DM Sans',sans-serif;background:var(--grey-100);color:var(--grey-800);font-size:14px}
.header{position:sticky;top:0;z-index:100;background:#fff;border-bottom:1px solid var(--grey-200);padding:12px 32px;display:flex;align-items:center;justify-content:space-between}
.report-name{font-weight:700;font-size:16px}
.report-meta{font-size:12px;color:var(--grey-500);margin-top:2px}
.tabs{background:#fff;border-bottom:1px solid var(--grey-200);padding:0 32px;display:flex;gap:0;overflow-x:auto}
.tab-btn{padding:12px 18px;font-size:13px;font-weight:500;color:var(--grey-500);border:none;border-bottom:2px solid transparent;background:none;cursor:pointer;white-space:nowrap;transition:.15s}
.tab-btn:hover{color:var(--grey-800)}
.tab-btn.active{color:var(--purple);border-bottom-color:var(--purple)}
.content{padding:28px 32px;max-width:1400px;margin:0 auto}
.tab-pane{display:none}.tab-pane.active{display:block}
.stat-cards{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:28px}
.stat-card{background:#fff;border-radius:10px;padding:20px 24px;flex:1;min-width:140px;border:1px solid var(--grey-200)}
.stat-val{font-size:26px;font-weight:700;color:var(--grey-800)}
.stat-sub{font-size:14px;font-weight:500;color:var(--grey-500)}
.stat-lbl{font-size:12px;color:var(--grey-500);margin-top:4px}
.section-title{font-size:15px;font-weight:700;color:var(--grey-800);margin:28px 0 14px}
.section-desc{font-size:13px;color:var(--grey-500);margin-bottom:16px}
.summary-table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;border:1px solid var(--grey-200)}
.summary-table th{background:var(--grey-50);padding:10px 14px;font-size:12px;font-weight:600;color:var(--grey-600);text-align:left;border-bottom:1px solid var(--grey-200)}
.summary-table td{padding:10px 14px;border-bottom:1px solid var(--grey-200);vertical-align:middle}
.summary-table tr:last-child td{border-bottom:none}
.user-cell{display:flex;align-items:center;gap:10px}
.mini-avatar{width:30px;height:30px;border-radius:50%;color:#fff;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.user-name{font-weight:600;font-size:13px}
.user-title{font-size:11px;color:var(--grey-500)}
.badge{font-size:11px;font-weight:600;padding:2px 8px;border-radius:99px;display:inline-block}
.bar-cell{display:flex;align-items:center;gap:8px}
.bar-wrap{flex:1;height:6px;background:var(--grey-200);border-radius:4px;min-width:60px}
.bar-fill{height:6px;border-radius:4px}
.bar-num{font-size:13px;font-weight:600;color:var(--grey-700);min-width:35px}
.wday-item{display:inline-flex;flex-direction:column;align-items:center;gap:2px;margin-right:4px}
.wday-dot{width:8px;height:8px;border-radius:50%}
.wday-on{background:var(--purple)}.wday-off{background:var(--grey-200)}
.wday-lbl{font-size:9px;color:var(--grey-400)}
.time-tag{font-size:12px;font-weight:600;padding:2px 7px;border-radius:6px;background:var(--grey-100);color:var(--grey-700)}
.time-early{background:#DCFCE7;color:#166534}
.time-late{background:var(--amber-light);color:#92400E}
.heatmap-wrap{overflow-x:auto;margin-bottom:8px;background:#fff;border-radius:10px;border:1px solid var(--grey-200);padding:16px}
.heatmap{border-collapse:collapse;font-family:'DM Mono',monospace}
.heatmap th,.heatmap td{padding:4px 6px;text-align:center;font-size:11px}
.heat-user-col,.heat-user{text-align:left;font-weight:600;padding-right:12px;white-space:nowrap;font-family:'DM Sans',sans-serif;font-size:12px;color:var(--grey-700)}
.heat-col{font-size:10px;color:var(--grey-500);white-space:nowrap;font-weight:400}
.heat-cell{width:52px;height:28px;border-radius:4px;font-size:11px;font-weight:500}
.h0{background:var(--grey-100);color:var(--grey-400)}.h1{background:#EDE9FE;color:#5B21B6}
.h2{background:#DDD6FE;color:#4C1D95}.h3{background:#A78BFA;color:#fff}.h4{background:var(--purple);color:#fff}
.heat-legend{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--grey-500);padding:8px 0;flex-wrap:wrap}
.lc{display:inline-flex;align-items:center;justify-content:center;min-width:44px;height:22px;border-radius:4px;font-size:11px}
.cat-grid{background:#fff;border-radius:10px;border:1px solid var(--grey-200);padding:16px;display:grid;grid-template-columns:1fr 1fr;gap:12px}
.cat-row{display:flex;align-items:center;gap:10px}
.cat-name{font-size:13px;color:var(--grey-700);min-width:160px}
.cat-count{font-size:13px;font-weight:600;color:var(--grey-800);min-width:35px;text-align:right}
.profiles-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.profile-card{background:#fff;border-radius:12px;border:1px solid var(--grey-200);overflow:hidden}
.profile-header{padding:20px;color:#fff;display:flex;flex-direction:column;gap:4px;align-items:flex-start}
.profile-avatar{width:40px;height:40px;border-radius:50%;background:rgba(255,255,255,0.3);font-size:16px;font-weight:700;display:flex;align-items:center;justify-content:center;margin-bottom:8px}
.profile-name{font-size:16px;font-weight:700}.profile-role{font-size:12px;opacity:0.85}
.profile-header .badge{margin-top:4px}
.profile-stats{display:flex;border-bottom:1px solid var(--grey-200)}
.pstat{flex:1;text-align:center;padding:14px;border-right:1px solid var(--grey-200)}
.pstat:last-child{border-right:none}
.pstat-val{font-size:20px;font-weight:700;color:var(--grey-800)}
.pstat-lbl{font-size:11px;color:var(--grey-500);margin-top:2px}
.sess-strip{padding:14px;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid var(--grey-200)}
.sess-block{background:var(--purple-light);border-radius:8px;padding:8px 10px;min-width:100px;font-size:11px}
.sess-date{font-weight:700;color:var(--purple);font-size:12px}
.sess-range{color:var(--grey-600);margin:2px 0}.sess-count{color:var(--grey-500)}
.obs-box{padding:14px;font-size:13px;color:var(--grey-700);line-height:1.6}
.pp-block{background:#fff;border-radius:10px;border:1px solid var(--grey-200);margin-bottom:16px;overflow:hidden}
.pp-header{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;border-bottom:1px solid var(--grey-200);background:var(--grey-50)}
.pp-name{font-weight:700;font-size:14px}.pp-meta{display:flex;gap:8px;align-items:center}
.pp-stat{font-size:12px;color:var(--grey-500);font-weight:500}
.pp-late{font-size:11px;font-weight:700;background:var(--red-light);color:var(--red);padding:2px 8px;border-radius:99px}
.bau-table{width:100%;border-collapse:collapse;font-size:13px}
.bau-table th{background:var(--grey-50);padding:8px 14px;font-size:11px;font-weight:600;color:var(--grey-600);text-align:left;border-bottom:1px solid var(--grey-200)}
.bau-table td{padding:8px 14px;border-bottom:1px solid var(--grey-200);vertical-align:middle}
.bau-table tr:last-child td{border-bottom:none}
.late-flag{font-size:11px;font-weight:700;color:var(--red);background:var(--red-light);padding:2px 7px;border-radius:99px}
.config-user-block{background:#fff;border-radius:10px;border:1px solid var(--grey-200);margin-bottom:16px;overflow:hidden}
.config-user-hdr{padding:14px 16px;background:var(--grey-50);border-bottom:1px solid var(--grey-200);display:flex;align-items:center;gap:10px}
.config-count{font-size:12px;color:var(--grey-500)}
.action-dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px;vertical-align:middle}
.alert-card{border-radius:10px;padding:18px 20px;margin-bottom:14px;border-left:4px solid}
.alert-red{background:var(--red-light);border-color:var(--red)}
.alert-amber{background:var(--amber-light);border-color:var(--amber)}
.alert-title{font-weight:700;font-size:14px;margin-bottom:6px}
.alert-card p{font-size:13px;color:var(--grey-700);line-height:1.6;margin-bottom:6px}
.alert-list{padding-left:18px;font-size:13px;color:var(--grey-700);line-height:1.8}
.pos-grid,.rec-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:28px}
.pos-card{background:#F0FDF9;border:1px solid #99F6E4;border-radius:10px;padding:16px 18px}
.pos-title{font-weight:700;font-size:13px;color:#0F766E;margin-bottom:6px}
.pos-card p{font-size:13px;color:var(--grey-700);line-height:1.6}
.rec-card{background:var(--grey-50);border:1px solid var(--grey-200);border-radius:10px;padding:16px 18px}
.rec-title{font-weight:700;font-size:13px;color:var(--grey-800);margin-bottom:6px}
.rec-card p{font-size:13px;color:var(--grey-600);line-height:1.6}
.footer{text-align:center;padding:24px;font-size:11px;color:var(--grey-400);margin-top:40px}
"""

JS = """
function showTab(id,event){
  document.querySelectorAll('.tab-pane').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b=>b.classList.remove('active'));
  document.getElementById('tab-'+id).classList.add('active');
  if(event&&event.target) event.target.classList.add('active');
}
"""

# ── Main analysis ─────────────────────────────────────────────────────────────

def build_report(input_path, output_path):
    with open(input_path) as f:
        raw = json.load(f)
    audits = raw.get('audits', raw) if isinstance(raw, dict) else raw

    for a in audits:
        if a.get('date'):
            a['_dt'] = to_aedt(a['date'])
        a['_cat'] = categorize(a.get('type', ''))

    system_users = {'Paytools', 'System', ''}
    human_audits = [a for a in audits if a.get('user_name', '') not in system_users]
    USERS = sorted(set(a['user_name'] for a in human_audits if a.get('user_name')))
    if not USERS:
        raise ValueError("No human user records found in this audit log.")

    all_dates = sorted(set(a['_dt'].date() for a in human_audits if '_dt' in a))
    if not all_dates:
        raise ValueError("No valid timestamps found.")

    date_range_str = f"{all_dates[0].strftime('%d %b')} – {all_dates[-1].strftime('%d %b %Y')}"
    generated_str = datetime.now(AEDT).strftime('%d/%m/%Y')
    # Determine MonthYear for filename suggestion
    month_year = all_dates[-1].strftime('%b%Y')

    # ── Per-user stats ──────────────────────────────────────────────────────
    user_stats = {}
    for u in USERS:
        ua = [a for a in human_audits if a['user_name'] == u]
        dts = sorted([a['_dt'] for a in ua if '_dt' in a])
        days = sorted(set(d.date() for d in dts))
        sessions = []
        for day in days:
            day_dts = sorted([d for d in dts if d.date() == day])
            span_min = int((day_dts[-1] - day_dts[0]).total_seconds() / 60) if len(day_dts) > 1 else 0
            sessions.append({'date': day, 'first': day_dts[0], 'last': day_dts[-1],
                             'count': len(day_dts), 'span_min': span_min})
        spans = sorted([s['span_min'] for s in sessions])
        med_span_min = spans[len(spans) // 2] if spans else 0
        starts = sorted([s['first'].hour * 60 + s['first'].minute for s in sessions])
        med_start_min = starts[len(starts) // 2] if starts else 540
        ooh = any(d.hour < 7 or d.hour >= 18 for d in dts)
        wdays = Counter(d.date().weekday() for d in dts)
        wday_active = [wdays.get(i, 0) > 0 for i in range(5)]
        cats_ctr = Counter(a['_cat'] for a in ua)
        role_title, role_key = infer_role(u, dict(cats_ctr))
        user_stats[u] = {
            'total': len(ua), 'days': len(days), 'day_list': days,
            'sessions': sessions, 'med_span_min': med_span_min,
            'med_start_min': med_start_min, 'ooh': ooh,
            'wday_active': wday_active, 'cats': dict(cats_ctr),
            'main_cat': cats_ctr.most_common(1)[0][0] if cats_ctr else '',
            'earliest': dts[0] if dts else None,
            'role_title': role_title, 'role_key': role_key,
        }

    # Sort users by activity descending
    USERS = sorted(USERS, key=lambda u: -user_stats[u]['total'])

    total_actions = sum(s['total'] for s in user_stats.values())
    most_active = USERS[0]
    earliest_u = min(USERS, key=lambda u: user_stats[u]['earliest'] or datetime.max.replace(tzinfo=AEDT))
    ooh_count = sum(1 for u in USERS if user_stats[u]['ooh'])
    all_cats_ctr = Counter(a['_cat'] for a in human_audits)

    # ── Heatmap ─────────────────────────────────────────────────────────────
    heatmap = {}
    for u in USERS:
        heatmap[u] = {}
        for a in [x for x in human_audits if x['user_name'] == u and '_dt' in x]:
            d = a['_dt'].date()
            heatmap[u][d] = heatmap[u].get(d, 0) + 1

    # ── Check analysis ──────────────────────────────────────────────────────
    checks = [a for a in audits if a.get('type') == 'check']
    completions = [a for a in checks if a.get('changes', {}).get('status', ['', ''])[1]
                   in ['Completed', 'COMPLETED']]
    reverts = [a for a in checks if a.get('changes', {}).get('status')
               in [['Completed', 'Pending'], ['COMPLETED', 'PENDING']]]
    late_list = []
    for a in completions:
        dd = a.get('due_date')
        if dd and '_dt' in a:
            comp = a['_dt'].date()
            due = datetime.strptime(dd, '%Y-%m-%d').date()
            if comp > due:
                late_list.append({'name': a['name'], 'days': (comp - due).days,
                                  'user': a['user_name']})
    late_by_name = Counter(l['name'] for l in late_list)
    recurring_late = [(n, c) for n, c in late_by_name.most_common(8) if c >= 3]

    # ── BAU ──────────────────────────────────────────────────────────────────
    bau_records = [a for a in audits if a.get('associations', {}).get('pay_period')]
    pay_periods_dict = {}
    for a in bau_records:
        pp = a['associations']['pay_period']
        pid = pp['id']
        if pid not in pay_periods_dict:
            pay_periods_dict[pid] = {'name': pp['name'], 'occurrences': {},
                                     'total_checks': 0, 'late_checks': 0,
                                     'checklist_def_names': set()}
        ppd = pay_periods_dict[pid]
        cd = a.get('associations', {}).get('checklist_definition')
        if cd and cd.get('name'):
            ppd['checklist_def_names'].add(cd['name'])
        occ = a.get('associations', {}).get('calendar_event_occurrence')
        if occ:
            oid = occ['id']
            if oid not in ppd['occurrences']:
                ppd['occurrences'][oid] = {'name': occ['name'], 'done': 0, 'late': 0, 'approved': False}
        if (a.get('type') == 'check' and
                a.get('changes', {}).get('status', ['', ''])[1] in ['Completed', 'COMPLETED']):
            ppd['total_checks'] += 1
            if occ:
                ppd['occurrences'][occ['id']]['done'] += 1
            dd = a.get('due_date')
            if dd and '_dt' in a:
                comp2 = a['_dt'].date()
                due2 = datetime.strptime(dd, '%Y-%m-%d').date()
                if comp2 > due2:
                    ppd['late_checks'] += 1
                    if occ:
                        ppd['occurrences'][occ['id']]['late'] += 1
        if (a.get('type') == 'checklist' and
                a.get('changes', {}).get('status', ['', ''])[1] in ['Approved', 'APPROVED']):
            if occ:
                ppd['occurrences'][occ['id']]['approved'] = True

    active_periods = {pid: ppd for pid, ppd in pay_periods_dict.items()
                      if ppd['total_checks'] > 0}
    sorted_periods = sorted(active_periods.items(),
                            key=lambda x: parse_period_date(x[1]['name']), reverse=True)[:10]

    # ── Config ────────────────────────────────────────────────────────────────
    config_human = [a for a in audits if a.get('type', '').lower() in CONFIG_TYPES
                    and a.get('user_name', '') not in system_users]
    config_by_user = {}
    for u in USERS:
        uc = [a for a in config_human if a['user_name'] == u]
        if uc:
            config_by_user[u] = uc
    config_actions_ctr = Counter(a['action'] for a in config_human)
    top_config_user = max(config_by_user, key=lambda u: len(config_by_user[u])) if config_by_user else ''

    # ── Build observations ────────────────────────────────────────────────────
    # Most active user observation
    most_active_stats = user_stats[most_active]
    observations_per_user = {}
    for u in USERS:
        s = user_stats[u]
        cats = s['cats']
        total = s['total']
        days = s['days']
        sessions = s['sessions']
        ooh = s['ooh']
        main_cat = s['main_cat']
        check_count = cats.get('Check Tasks', 0)
        cl_count = cats.get('Checklist Actions', 0)
        cfg_count = cats.get('Config / Templates', 0)
        attach_count = cats.get('File Attachments', 0)
        rev_count = sum(1 for a in reverts if a['user_name'] == u)
        ooh_sessions = [sess for sess in sessions if sess['first'].hour >= 18 or sess['first'].hour < 7]
        early_sessions = [sess for sess in sessions if sess['first'].hour < 7]
        late_sessions = [sess for sess in sessions if sess['first'].hour >= 18]
        obs = []
        obs.append(f"{u} logged {total:,} actions across {days} active day{'s' if days != 1 else ''}.")
        if check_count > 0 and check_count / total > 0.5:
            obs.append(f"The majority of work ({check_count} actions, {int(check_count/total*100)}%) was check task completions.")
        if cl_count > 0:
            approved = sum(1 for a in audits if a.get('type') == 'checklist'
                           and a['user_name'] == u
                           and a.get('changes', {}).get('status', ['', ''])[1] in ['Approved', 'APPROVED'])
            submitted = sum(1 for a in audits if a.get('type') == 'checklist'
                            and a['user_name'] == u
                            and a.get('changes', {}).get('status', ['', ''])[1] == 'Awaiting Approval')
            if approved > 0:
                obs.append(f"{u} approved {approved} checklist{'s' if approved != 1 else ''} during the period.")
            if submitted > 0:
                obs.append(f"{submitted} checklist{'s' if submitted != 1 else ''} submitted for approval.")
        if cfg_count > 0 and cfg_count / total > 0.4:
            obs.append(f"Work was focused on configuration and template setup ({cfg_count} config actions).")
        if attach_count > 0:
            obs.append(f"{attach_count} file attachment{'s' if attach_count != 1 else ''} recorded, indicating evidence documentation practice.")
        if rev_count > 0:
            obs.append(f"{rev_count} check revert{'s' if rev_count != 1 else ''} recorded — evidence of active self-correction within sessions.")
        if late_sessions:
            obs.append(f"{len(late_sessions)} session{'s' if len(late_sessions) != 1 else ''} started after 18:00 AEDT, including {late_sessions[0]['date'].strftime('%d %b')} at {fmt_time(late_sessions[0]['first'])}.")
        if early_sessions:
            obs.append(f"{len(early_sessions)} session{'s' if len(early_sessions) != 1 else ''} started before 07:00 AEDT.")
        observations_per_user[u] = ' '.join(obs)

    # ── Tab 1: Team Overview ─────────────────────────────────────────────────
    ea = user_stats[earliest_u]['earliest']
    stat_cards_html = f"""<div class="stat-cards">
  <div class="stat-card"><div class="stat-val">{len(USERS)}</div><div class="stat-lbl">Active Users</div></div>
  <div class="stat-card"><div class="stat-val">{total_actions:,}</div><div class="stat-lbl">Total Actions</div></div>
  <div class="stat-card"><div class="stat-val">{most_active.split()[0]}<span class="stat-sub"> {user_stats[most_active]['total']}</span></div><div class="stat-lbl">Most Active User</div></div>
  <div class="stat-card"><div class="stat-val">{ea.strftime('%d %b') if ea else '—'}<span class="stat-sub"> {earliest_u.split()[0]}</span></div><div class="stat-lbl">Earliest Login</div></div>
  <div class="stat-card"><div class="stat-val">{ooh_count}</div><div class="stat-lbl">Out-of-Hours Users</div></div>
</div>"""

    max_total = max(s['total'] for s in user_stats.values())
    summary_rows = ''
    for u in USERS:
        s = user_stats[u]
        rk = s['role_key']
        av_bg = AVATAR_BG.get(rk, ('#3339F2', '#6366F1'))
        start_cls = 'time-early' if s['med_start_min'] < 420 else ('time-late' if s['med_start_min'] > 510 else '')
        summary_rows += f"""<tr>
  <td><div class="user-cell"><div class="mini-avatar" style="background:{av_bg[0]}">{initials(u)}</div>
  <div><div class="user-name">{u}</div><div class="user-title">{s['role_title']}</div></div></div></td>
  <td>{badge(rk, rk)}</td>
  <td><div class="bar-cell">{progress_bar(s['total'], max_total)} <span class="bar-num">{s['total']}</span></div></td>
  <td>{s['days']}</td>
  <td>{wday_dots(s['wday_active'])}</td>
  <td><span class="time-tag {start_cls}">{fmt_start(s['med_start_min'])}</span></td>
  <td>{fmt_span(s['med_span_min'])}</td>
</tr>"""

    summary_table_html = f"""<table class="summary-table">
<thead><tr><th>User</th><th>Role</th><th>Total Actions</th><th>Active Days</th><th>Days Active</th><th>Typical Start</th><th>Avg Session</th></tr></thead>
<tbody>{summary_rows}</tbody>
</table>"""

    # Heatmap
    hm_cols = ''.join(f'<th class="heat-col">{d.strftime("%d %b")}</th>' for d in all_dates)
    hm_rows = ''
    for u in USERS:
        cells = ''
        for d in all_dates:
            n = heatmap[u].get(d, 0)
            hl = heat_level(n)
            label = '—' if n == 0 else str(n)
            cells += f'<td class="heat-cell {hl}">{label}</td>'
        hm_rows += f'<tr><td class="heat-user">{u}</td>{cells}</tr>'
    heatmap_html = f"""<div class="heatmap-wrap">
<table class="heatmap">
<thead><tr><th class="heat-user-col">User</th>{hm_cols}</tr></thead>
<tbody>{hm_rows}</tbody>
</table></div>
<div class="heat-legend">
<span>Activity:</span>
<span class="heat-cell h0 lc">—</span><span> None</span>
<span class="heat-cell h1 lc">1–20</span>
<span class="heat-cell h2 lc">21–60</span>
<span class="heat-cell h3 lc">61–120</span>
<span class="heat-cell h4 lc">121+</span>
</div>"""

    cat_order = ['Check Tasks', 'Checklist Actions', 'Config / Templates', 'File Attachments',
                 'Calendar Events', 'Comments', 'Employee Work', 'Governance']
    max_cat = max(all_cats_ctr.values()) if all_cats_ctr else 1
    cat_rows_html = ''
    for c in cat_order:
        n = all_cats_ctr.get(c, 0)
        if n > 0:
            cat_rows_html += f'<div class="cat-row"><div class="cat-name">{c}</div>{progress_bar(n, max_cat, "var(--purple-mid)")}<div class="cat-count">{n}</div></div>'

    tab1 = f"""{stat_cards_html}
<div class="section-title">Team Activity Summary</div>
{summary_table_html}
<div class="section-title">Daily Action Volume</div>
{heatmap_html}
<div class="section-title">Types of Work</div>
<div class="cat-grid">{cat_rows_html}</div>"""

    # ── Tab 2: User Profiles ─────────────────────────────────────────────────
    profile_cards_html = ''
    for u in USERS:
        s = user_stats[u]
        rk = s['role_key']
        av_bg = AVATAR_BG.get(rk, ('#3339F2', '#6366F1'))
        strip = ''
        for sess in s['sessions']:
            strip += (f'<div class="sess-block"><div class="sess-date">{sess["date"].strftime("%d %b")}</div>'
                      f'<div class="sess-range">{fmt_time(sess["first"])}–{fmt_time(sess["last"])}</div>'
                      f'<div class="sess-count">{sess["count"]} actions</div></div>')
        main_lbl = s['main_cat'][:18] if s['main_cat'] else '—'
        obs_text = observations_per_user.get(u, '')
        profile_cards_html += f"""<div class="profile-card">
  <div class="profile-header" style="background:linear-gradient(135deg,{av_bg[0]},{av_bg[1]})">
    <div class="profile-avatar">{initials(u)}</div>
    <div class="profile-name">{u}</div>
    <div class="profile-role">{s['role_title']}</div>
    {badge(rk, rk)}
  </div>
  <div class="profile-stats">
    <div class="pstat"><div class="pstat-val">{s['total']}</div><div class="pstat-lbl">Total Actions</div></div>
    <div class="pstat"><div class="pstat-val">{s['days']}</div><div class="pstat-lbl">Active Days</div></div>
    <div class="pstat"><div class="pstat-val" style="font-size:13px">{main_lbl}</div><div class="pstat-lbl">Main Work</div></div>
  </div>
  <div class="sess-strip">{strip}</div>
  <div class="obs-box"><p>{obs_text}</p></div>
</div>"""

    tab2 = f'<div class="profiles-grid">{profile_cards_html}</div>'

    # ── Tab 3: BAU Work ───────────────────────────────────────────────────────
    bau_html = ''
    if sorted_periods:
        for pid, ppd in sorted_periods:
            occs = sorted(ppd['occurrences'].values(), key=lambda x: x['name'])
            occ_rows = ''
            for occ in occs:
                approved_mark = '✓' if occ['approved'] else '–'
                late_flag = f'<span class="late-flag">{occ["late"]} late</span>' if occ['late'] > 0 else ''
                occ_rows += f'<tr><td>{occ["name"]}</td><td>{occ["done"]}</td><td>{approved_mark}</td><td>{late_flag}</td></tr>'
            late_pill = f'<span class="pp-late">{ppd["late_checks"]} late</span>' if ppd['late_checks'] else ''
            pay_group_code = extract_pay_group(ppd['checklist_def_names'])
            pay_group_badge = f'<span class="badge" style="background:#EEF2FF;color:#3730A3;margin-left:8px">{pay_group_code}</span>' if pay_group_code else ''
            display_name = natural_period_name(ppd['name'])
            bau_html += f"""<div class="pp-block">
  <div class="pp-header">
    <div class="pp-name">{display_name}{pay_group_badge}</div>
    <div class="pp-meta"><span class="pp-stat">{ppd['total_checks']} checks</span>{late_pill}</div>
  </div>
  <table class="bau-table">
  <thead><tr><th>Event Occurrence</th><th>Checks Done</th><th>Checklist Approved</th><th>Late</th></tr></thead>
  <tbody>{occ_rows}</tbody>
  </table>
</div>"""
    tab3 = f"""<div class="section-title">Pay Period Processing</div>
<p class="section-desc">Active pay periods with check completions, sorted most recent first.</p>
{bau_html if bau_html else '<p class="section-desc">No BAU pay period data found in this log.</p>'}"""

    # ── Tab 4: Config Changes ─────────────────────────────────────────────────
    config_detail_html = ''
    if config_by_user:
        cfg_created = config_actions_ctr.get('create', 0)
        cfg_updated = config_actions_ctr.get('update', 0)
        cfg_removed = config_actions_ctr.get('remove', 0) + config_actions_ctr.get('destroy', 0)
        total_cfg = len(config_human)
        config_stat_html = f"""<div class="stat-cards">
  <div class="stat-card"><div class="stat-val">{top_config_user.split()[0] if top_config_user else '—'}<span class="stat-sub"> {len(config_by_user.get(top_config_user, []))}</span></div><div class="stat-lbl">Most Active Config User</div></div>
  <div class="stat-card"><div class="stat-val">{total_cfg}</div><div class="stat-lbl">Total Config Actions</div></div>
  <div class="stat-card"><div class="stat-val">{cfg_created}</div><div class="stat-lbl">Created</div></div>
  <div class="stat-card"><div class="stat-val">{cfg_updated}</div><div class="stat-lbl">Updated</div></div>
  <div class="stat-card"><div class="stat-val">{cfg_removed}</div><div class="stat-lbl">Removed</div></div>
</div>"""
        for u, recs in sorted(config_by_user.items(), key=lambda x: -len(x[1])):
            rk = user_stats[u]['role_key']
            rows = ''
            for a in sorted(recs, key=lambda x: x.get('date', '')):
                dt = a['_dt'].strftime('%d/%m/%Y %H:%M') if '_dt' in a else ''
                assoc_str = ', '.join(v.get('name', '') for v in a.get('associations', {}).values() if v.get('name'))
                name_str = (a.get('name', '') or assoc_str)[:50]
                rows += f'<tr><td>{action_dot(a["action"])}{humanise_config_action(a["action"])}</td><td>{humanise_config_type(a["type"])}</td><td>{name_str}</td><td>{dt}</td></tr>'
            config_detail_html += f"""<div class="config-user-block">
  <div class="config-user-hdr"><strong>{u}</strong> {badge(rk, rk)} <span class="config-count">{len(recs)} actions</span></div>
  <table class="bau-table"><thead><tr><th>Action</th><th>Type</th><th>Record</th><th>Date (AEDT)</th></tr></thead>
  <tbody>{rows}</tbody></table>
</div>"""
        tab4_content = config_stat_html + '<div class="section-title">Config Activity by User</div>' + config_detail_html
    else:
        tab4_content = '<p class="section-desc">No human config changes found in this log.</p>'

    # ── Tab 5: Observations & Alerts ─────────────────────────────────────────
    alerts_html = ''
    if recurring_late:
        late_items = ''.join(f'<li><strong>{n}</strong> — completed late {c} times</li>' for n, c in recurring_late[:6])
        late_pct = int(len(late_list) / len(completions) * 100) if completions else 0
        alerts_html += f"""<div class="alert-card alert-red">
  <div class="alert-title">Recurring Late Check Completions</div>
  <p>The following checks were completed after their due date on 3 or more occasions. This pattern
  typically indicates that due dates are set earlier than the work can realistically be completed,
  or there is a structural resourcing constraint on those days.</p>
  <ul class="alert-list">{late_items}</ul>
  <p>Total late completions in period: <strong>{len(late_list)}</strong> of {len(completions)} ({late_pct}%).</p>
</div>"""

    if ooh_count > 0:
        ooh_users = [u for u in USERS if user_stats[u]['ooh']]
        ooh_names = ', '.join(ooh_users)
        alerts_html += f"""<div class="alert-card alert-amber">
  <div class="alert-title">Out-of-Hours Activity</div>
  <p>{ooh_count} user{'s' if ooh_count != 1 else ''} recorded actions before 07:00 or after 18:00 AEDT: {ooh_names}.
  Review whether this reflects expected flexible working patterns or indicates time-pressure issues
  in the pay cycle.</p>
</div>"""

    if reverts:
        alerts_html += f"""<div class="alert-card alert-amber">
  <div class="alert-title">Check Reverts ({len(reverts)} total)</div>
  <p>{len(reverts)} checks were reverted from Completed back to Pending during the period. All reverts
  indicate active self-correction. Review whether any recur on the same check across multiple
  periods, which could signal an upstream data or process issue.</p>
</div>"""

    if not alerts_html:
        alerts_html = '<p class="section-desc">No significant alerts detected in this period.</p>'

    # Positives
    positives_list = []
    attach_total = all_cats_ctr.get('File Attachments', 0)
    if attach_total > 0:
        positives_list.append(('File Attachment Practice', f'{attach_total} file attachment{"s" if attach_total != 1 else ""} recorded across the period, supporting evidence trails for audit readiness.'))
    if len(reverts) > 0:
        positives_list.append(('Active Self-Correction', f'{len(reverts)} check revert{"s" if len(reverts) != 1 else ""} recorded, all indicating real-time quality control within active sessions.'))
    approved_total = sum(1 for a in audits if a.get('type') == 'checklist'
                         and a.get('changes', {}).get('status', ['', ''])[1] in ['Approved', 'APPROVED'])
    if approved_total > 0:
        positives_list.append(('Formal Approval Workflow', f'{approved_total} checklist approval{"s" if approved_total != 1 else ""} completed through the full Awaiting Approval → Approved workflow.'))
    if config_by_user:
        positives_list.append(('Active Configuration', f'{len(config_human)} configuration actions recorded by {len(config_by_user)} user{"s" if len(config_by_user) != 1 else ""}, indicating ongoing governance and template investment.'))
    if len(USERS) >= 2:
        positives_list.append(('Role Separation', f'Distinct processing and approval roles are visible in the data: separate users for check completion and checklist approval.'))

    pos_html = ''
    for title, desc in positives_list[:6]:
        pos_html += f'<div class="pos-card"><div class="pos-title">{title}</div><p>{desc}</p></div>'

    # Recommendations
    recs_list = []
    if recurring_late:
        top_n = recurring_late[0][0]
        top_c = recurring_late[0][1]
        recs_list.append(('Review Due Dates for Recurring Late Checks',
                          f'"{top_n}" and {len(recurring_late)-1} other check{"s" if len(recurring_late) > 2 else ""} were completed late {top_c} times each. '
                          f'Audit whether these due dates reflect the actual processing window. Adjusting them eliminates false-positive lateness signals and makes genuine delays visible.'))
    if ooh_count > 0:
        recs_list.append(('Review After-Hours Processing',
                          f'{ooh_count} user{"s have" if ooh_count != 1 else " has"} active sessions outside standard hours. '
                          f'If this is unplanned, review pay cycle scheduling and workload distribution to reduce out-of-hours reliance.'))
    if approved_total > 0:
        recs_list.append(('Set an Approval Turnaround SLA',
                          'Checklist approvals are the final step in each pay run. Define and document a turnaround expectation — '
                          'for example, approval within 2 business days of submission — and consider an automated reminder if a checklist remains in Awaiting Approval beyond that window.'))
    recs_list.append(('Scheduled Governance Review',
                      'Use the Observations tab as a standing agenda item in the team\'s periodic governance review. '
                      'The recurring late check list and approval patterns are most useful when tracked across multiple periods.'))

    rec_html = ''
    for title, desc in recs_list[:5]:
        rec_html += f'<div class="rec-card"><div class="rec-title">{title}</div><p>{desc}</p></div>'

    tab5 = f"""<div class="section-title">Alerts</div>
{alerts_html}
<div class="section-title">Positive Observations</div>
<div class="pos-grid">{pos_html}</div>
<div class="section-title">Recommendations</div>
<div class="rec-grid">{rec_html}</div>"""

    # ── Determine tabs to render ──────────────────────────────────────────────
    show_bau = bool(sorted_periods)
    show_config = bool(config_by_user)

    tabs_html = '<div class="tabs">'
    tabs_html += '<button class="tab-btn active" onclick="showTab(\'overview\',event)">Team Overview</button>'
    tabs_html += '<button class="tab-btn" onclick="showTab(\'profiles\',event)">User Profiles</button>'
    if show_bau:
        tabs_html += '<button class="tab-btn" onclick="showTab(\'bau\',event)">BAU Work</button>'
    if show_config:
        tabs_html += '<button class="tab-btn" onclick="showTab(\'config\',event)">Config Changes</button>'
    tabs_html += '<button class="tab-btn" onclick="showTab(\'obs\',event)">Observations &amp; Alerts</button>'
    tabs_html += '</div>'

    panes_html = f'<div id="tab-overview" class="tab-pane active">{tab1}</div>'
    panes_html += f'<div id="tab-profiles" class="tab-pane">{tab2}</div>'
    if show_bau:
        panes_html += f'<div id="tab-bau" class="tab-pane">{tab3}</div>'
    if show_config:
        panes_html += f'<div id="tab-config" class="tab-pane">{tab4_content}</div>'
    panes_html += f'<div id="tab-obs" class="tab-pane">{tab5}</div>'

    # ── Final HTML ────────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Paytools — Team Activity Report — {date_range_str}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="header">
  <div>
    <div class="report-name">Paytools — Team Activity Report</div>
    <div class="report-meta">{date_range_str} · Generated {generated_str}</div>
  </div>
</div>
{tabs_html}
<div class="content">{panes_html}</div>
<div class="footer">
  <p>Confidential — Internal Use Only · Paytools · Generated {generated_str} · {date_range_str}</p>
</div>
<script>{JS}</script>
</body>
</html>"""

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return {
        'output_path': output_path,
        'date_range': date_range_str,
        'users': len(USERS),
        'total_actions': total_actions,
        'completions': len(completions),
        'late': len(late_list),
        'recurring_late': recurring_late[:3],
        'month_year': month_year,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate Paytools Team Activity Report')
    parser.add_argument('--input', required=True, help='Path to Paytools audit log JSON')
    parser.add_argument('--output', required=True, help='Path for output HTML report')
    args = parser.parse_args()

    try:
        result = build_report(args.input, args.output)
        print(f"Report written: {result['output_path']}")
        print(f"Period: {result['date_range']} | Users: {result['users']} | "
              f"Actions: {result['total_actions']} | "
              f"Completions: {result['completions']} ({result['late']} late)")
        if result['recurring_late']:
            names = ', '.join(f"{n} ({c}x)" for n, c in result['recurring_late'])
            print(f"Top recurring late checks: {names}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
