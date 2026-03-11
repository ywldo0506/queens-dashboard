import streamlit as st
import pandas as pd
import requests
import io

SHEET_ID = "1JVG8UlklrMotvMPSkcNTYUydLsVUP82e2dtNpC48uhE"
GID = "2114825691"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

LUNCH_KEYS  = ['l1030','l1100','l1130','l1200','l1230','l1300','l1330','l1400']
DINNER_KEYS = ['d1700','d1730','d1800','d1830','d1900']
TIME_LABELS = {
    'l1030':'10:30','l1100':'11:00','l1130':'11:30','l1200':'12:00',
    'l1230':'12:30','l1300':'13:00','l1330':'13:30','l1400':'14:00',
    'd1700':'17:00','d1730':'17:30','d1800':'18:00','d1830':'18:30','d1900':'19:00'
}

@st.cache_data(ttl=0)
def load_data():
    resp = requests.get(CSV_URL)
    resp.encoding = 'utf-8'
    df_raw = pd.read_csv(io.StringIO(resp.text), header=None, dtype=str).fillna('')
    stores = []
    current_cell = ''
    current_store = ''
    store_obj = None
    def g(row, col):
        try:
            v = str(row.iloc[col]).strip()
            return v if v and v != 'nan' else 'X'
        except:
            return 'X'
    def gn(row, col):
        try:
            v = str(row.iloc[col]).strip()
            return '' if v == 'nan' else v
        except:
            return ''
    for i, row in df_raw.iterrows():
        if i < 3:
            continue
        cell  = gn(row, 1) or current_cell
        store = gn(row, 2) or current_store
        day   = gn(row, 3)
        if not store or day not in ['평일', '주말']:
            continue
        if store != current_store:
            if store_obj:
                stores.append(store_obj)
            current_store = store
            current_cell  = cell
            store_obj = {'cell': cell, 'store': store, '평일': None, '주말': None}
        store_obj[day] = {
            'l1030': g(row,4),  'l1100': g(row,5),  'l1130': g(row,6),
            'l1200': g(row,7),  'l1230': g(row,8),  'l1300': g(row,9),
            'l1330': g(row,10), 'l1400': g(row,11),
            'lBigday': gn(row,12), 'lNote': gn(row,13),
            'd1700': g(row,14), 'd1730': g(row,15), 'd1800': g(row,16),
            'd1830': g(row,17), 'd1900': g(row,18),
            'dBigday': gn(row,19), 'dNote': gn(row,20), 'cellNote': gn(row,21),
        }
    if store_obj:
        stores.append(store_obj)
    for s in stores:
        for d in ['평일', '주말']:
            if not s[d]:
                s[d] = {k: 'X' for k in LUNCH_KEYS + DINNER_KEYS}
                s[d].update({'lBigday':'','lNote':'','dBigday':'','dNote':'','cellNote':''})
    return stores

def badge(v):
    v = str(v).strip()
    if not v or v == 'X':
        return '<span style="color:#ccc">✕</span>'
    try:
        n = int(v)
        if n >= 100: color,bg = '#059669','#d1fae5'
        elif n >= 50: color,bg = '#b45309','#fef3c7'
        else: color,bg = '#2563eb','#dbeafe'
        return f'<span style="background:{bg};color:{color};padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600">{v}</span>'
    except:
        return f'<span style="background:#f3e8ff;color:#7c3aed;padding:2px 6px;border-radius:12px;font-size:11px">{v[:10]}</span>'

st.set_page_config(page_title='퀸즈 예약 현황', layout='wide', page_icon='👑')
st.markdown("""
<style>
.block-container{padding-top:1rem}
header[data-testid="stHeader"]{display:none}
thead th{background:#f1f3f8!important;font-size:12px;text-align:center!important;padding:7px 10px}
tbody td{font-size:12px;text-align:center;vertical-align:middle}
tbody tr:hover td{background:#f8f9fc}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([8,1])
with col1:
    st.markdown("## 👑 퀸즈 예약 현황판")
with col2:
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()

with st.spinner("Google Sheets에서 데이터 불러오는 중..."):
    try:
        DATA = load_data()
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        st.stop()

f1, f2, f3, f4 = st.columns([3,2,2,3])
with f1:
    search = st.text_input("🔍 매장명 검색", placeholder="매장명 입력...")
with f2:
    cells = ['전체 셀'] + sorted(set(d['cell'] for d in DATA))
    cell_filter = st.selectbox("셀 선택", cells)
with f3:
    day_filter = st.radio("평일/주말", ['전체','평일','주말'], horizontal=True)
with f4:
    time_opts = ['전체','런치만','디너만'] + [f"런치 {TIME_LABELS[k]}" for k in LUNCH_KEYS] + [f"디너 {TIME_LABELS[k]}" for k in DINNER_KEYS]
    time_filter = st.selectbox("시간대", time_opts)

st.divider()

filtered = DATA
if search:
    filtered = [d for d in filtered if search.lower() in d['store'].lower()]
if cell_filter != '전체 셀':
    filtered = [d for d in filtered if d['cell'] == cell_filter]

days_to_show = ['평일','주말'] if day_filter == '전체' else [day_filter]

if time_filter == '전체': show_l,show_d = LUNCH_KEYS,DINNER_KEYS
elif time_filter == '런치만': show_l,show_d = LUNCH_KEYS,[]
elif time_filter == '디너만': show_l,show_d = [],DINNER_KEYS
elif time_filter.startswith('런치'):
    t = time_filter.replace('런치 ','')
    show_l = [k for k in LUNCH_KEYS if TIME_LABELS[k]==t]; show_d = []
else:
    t = time_filter.replace('디너 ','')
    show_l = []; show_d = [k for k in DINNER_KEYS if TIME_LABELS[k]==t]

st.markdown(f"**총 {len(filtered)}개 매장**")

for day in days_to_show:
    if day_filter == '전체':
        st.markdown(f"### {'📅 평일' if day=='평일' else '🗓️ 주말'}")
    headers = ['셀','매장명']
    if show_l:
        headers += [f"🍱 {TIME_LABELS[k]}" for k in show_l]
        headers += ['런치 빅데이','런치 특이사항']
    if show_d:
        headers += [f"🍽️ {TIME_LABELS[k]}" for k in show_d]
        headers += ['디너 빅데이','디너 특이사항']
    headers += ['셀 특이사항']
    rows_html = []
    for d in filtered:
        dd = d[day]
        if not dd: continue
        row = [d['cell'], d['store']]
        if show_l:
            row += [badge(dd[k]) for k in show_l]
            row += [dd.get('lBigday','').replace('\n','<br>') or '-',
                    dd.get('lNote','').replace('\n','<br>') or '-']
        if show_d:
            row += [badge(dd[k]) for k in show_d]
            row += [dd.get('dBigday','').replace('\n','<br>') or '-',
                    dd.get('dNote','').replace('\n','<br>') or '-']
        row += [dd.get('cellNote','').replace('\n','<br>') or '-']
        rows_html.append(row)
    th = ''.join(f'<th style="white-space:nowrap">{h}</th>' for h in headers)
    trs = ''
    for row in rows_html:
        tds = ''.join(f'<td style="padding:5px 10px;white-space:nowrap">{c}</td>' for c in row)
        trs += f'<tr>{tds}</tr>'
    st.markdown(f"""
    <div style="overflow-x:auto;border:1px solid #e2e8f0;border-radius:10px;margin-bottom:24px">
    <table style="width:100%;border-collapse:collapse;font-family:sans-serif">
    <thead><tr>{th}</tr></thead><tbody>{trs}</tbody>
    </table></div>
    """, unsafe_allow_html=True)

if not filtered:
    st.info("검색 결과가 없어요 🔍")

