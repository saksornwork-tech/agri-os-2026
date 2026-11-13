#!/usr/bin/env python3
"""Agri-OS: transparent, fail-closed weather ingestion and agricultural decision support."""
import argparse, datetime as dt, html, json, os, pathlib, urllib.parse, urllib.request
from zoneinfo import ZoneInfo
TZ=ZoneInfo('Asia/Bangkok')
ROOT=pathlib.Path(__file__).resolve().parent
POINTS={'ชุมพร (จุดอ้างอิง)':(10.493,99.180),'ท่าแซะ (แปลงตัวอย่าง)':(10.8397289,99.1181340)}
FIELDS=['temperature_2m','apparent_temperature','precipitation','cloud_cover','wind_speed_10m','wind_direction_10m','wind_gusts_10m','pressure_msl','cape','relative_humidity_2m','relative_humidity_850hPa','wind_speed_850hPa','wind_direction_850hPa']
THAI='https://api-v3.thaiwater.net/api/v1/thaiwater30/public/'
def get_json(url):
    req=urllib.request.Request(url,headers={'Accept':'application/json','User-Agent':'AgriOS-2026/0.1'})
    with urllib.request.urlopen(req,timeout=22) as r:
        if r.status!=200: raise ValueError('HTTP '+str(r.status))
        return json.load(r)
def ecmwf(lat,lon):
    q=urllib.parse.urlencode({'latitude':lat,'longitude':lon,'hourly':','.join(FIELDS),'timezone':'Asia/Bangkok','forecast_days':10})
    return get_json('https://api.open-meteo.com/v1/ecmwf?'+q)
def parse_hour(s):return dt.datetime.fromisoformat(s).replace(tzinfo=TZ)
def number(v):return isinstance(v,(int,float)) and not isinstance(v,bool)
def wind(deg):
    if not number(deg):return 'ไม่มีข้อมูล'
    return ['N','NE','E','SE','S','SW','W','NW'][round(deg/45)%8]
def summarize(data,start,stop):
    if not isinstance(data,dict) or not isinstance(data.get('hourly'),dict):return None
    h=data['hourly']; times=h.get('time',[])
    ids=[i for i,t in enumerate(times) if start<parse_hour(t)<=stop]
    if not ids:return None
    rain=h.get('precipitation',[])
    if any(i>=len(rain) or not number(rain[i]) for i in ids):total=None
    else:total=round(sum(rain[i] for i in ids),1)
    def avg(k):
        vals=[h.get(k,[])[i] for i in ids if i<len(h.get(k,[])) and number(h[k][i])]
        return round(sum(vals)/len(vals),1) if len(vals)==len(ids) else None
    return {'rain_mm':total,'wind_surface':wind(avg('wind_direction_10m')),'wind_850':wind(avg('wind_direction_850hPa')),'gust_kmh':avg('wind_gusts_10m'),'rh_pct':avg('relative_humidity_2m'),'pressure_hpa':avg('pressure_msl'),'hours':len(ids)}
def thaiwater():
    out={}
    for name,endpoint in [('rain_24h','rain_24h'),('waterlevel','waterlevel_load')]:
        try:
            raw=get_json(THAI+endpoint)
            rows=raw.get('data') if isinstance(raw,dict) else None
            out[name]={'status':'received' if rows else 'empty_or_unknown','record_count':len(rows) if isinstance(rows,list) else None,'raw_file':f'{name}_raw.json'}
            (ROOT/f'{name}_raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2),encoding='utf-8')
        except Exception as ex:out[name]={'status':'unavailable','reason':str(ex)}
    return out
def advice(rows):
    vals=[r['metrics']['rain_mm'] for r in rows if r['metrics'] and number(r['metrics']['rain_mm'])]
    peak=max(vals) if vals else None
    return ['ตรวจร่องระบายน้ำและความชื้นดินจริงก่อนใส่ปุ๋ยหรือทำงานในสวน','หลีกเลี่ยงพ่นสารเมื่อใบเปียก ฝนใกล้เข้ามา หรือลมแรง และปฏิบัติตามฉลาก','ตรวจหน้ากรีดยางและความปลอดภัยของแปลงก่อนกรีด','ฝนสะสมช่วง 6 ชั่วโมงสูงสุดในข้อมูลที่มี: '+(str(peak)+' มม.' if peak is not None else 'ไม่มีข้อมูล')+'; ไม่ใช้เกณฑ์ 90 มม. เพื่อรับรองความปลอดภัย']
def render(report):
    css='body{font-family:system-ui,"Noto Sans Thai",sans-serif;max-width:1100px;margin:auto;padding:24px;line-height:1.6;background:#f8fafc;color:#16283a}h1,h2{color:#123b52}table{border-collapse:collapse;width:100%;background:white}td,th{padding:10px;border:1px solid #cbd5e1;text-align:left}th{background:#dcecf4}.warn{color:#a04010}.muted{color:#536579}li{margin:8px 0}'
    def table(rows):
        s='<table><tr><th>ช่วงเวลา</th><th>ลมผิวพื้น / 850 hPa</th><th>ฝน (มม.) / สถานะ</th><th>พื้นที่</th></tr>'
        for r in rows:
            m=r['metrics']; rain='ไม่มีข้อมูล' if m is None or m['rain_mm'] is None else str(m['rain_mm'])+' มม.'
            if m and number(m['rain_mm']) and m['rain_mm']>=90:rain+=' | ถึงเกณฑ์แจ้งเตือนที่ตั้งไว้'
            s+='<tr><td>'+html.escape(r['period'])+'</td><td>'+html.escape((m['wind_surface']+' / '+m['wind_850']) if m else 'ไม่มีข้อมูล')+'</td><td>'+html.escape(rain)+'</td><td>'+html.escape(r['area'])+'</td></tr>'
        return s+'</table>'
    n=report['nowcast']; rows=report['forecast'];
    return '<!doctype html><html lang="th"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Agri-OS 2026</title><style>'+css+'</style><h1>Agri-OS 2026 | รายงานต้นแบบ</h1><p>เวลาประมวลผล '+html.escape(report['generated_at'])+' (Asia/Bangkok)</p><p class="warn">คำเตือน: ช่วง 0–6 ชม. เป็นการนำผล ECMWF รายชั่วโมงมาสรุป ไม่ใช่ radar nowcast; ยังไม่รองรับการระบุตำบลเสี่ยงจริงหรือการแจ้งเตือนอัตโนมัติ</p><h2>หัวข้อที่ 1: พยากรณ์ 24 ชั่วโมงและแนวโน้ม 4 ระยะ</h2><p>ระยะ 0–6 ชม. / 1–3 วัน / 4–10 วัน: ECMWF เมื่อ API ใช้งานได้; 15 วัน–9 เดือน: ยังไม่เชื่อม ensemble และดัชนีภูมิอากาศ</p>'+table(rows)+'<h3>แนวทางปฏิบัติสำหรับเกษตรกร</h3><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in report['advice'])+'</ul><h2>หัวข้อที่ 2: ระยะประชิด 0–6 ชั่วโมง</h2>'+table(n)+'<p class="muted">ค่าที่ไม่มีข้อมูลไม่ใช่ศูนย์ มิลลิเมตร | ไม่แสดงสถานะปลอดภัยจากฝนต่ำกว่า 90 มม.</p><h3>สถานะต้นทาง</h3><pre>'+html.escape(json.dumps(report['sources'],ensure_ascii=False,indent=2))+'</pre></html>'
def main():
    p=argparse.ArgumentParser();p.add_argument('--offline',action='store_true',help='generate safe missing-data report without API');a=p.parse_args()
    now=dt.datetime.now(TZ).replace(minute=0,second=0,microsecond=0)
    sources={};datasets={}
    for name,(lat,lon) in POINTS.items():
        try:
            if a.offline:raise RuntimeError('offline mode')
            datasets[name]=ecmwf(lat,lon);sources[name]='received'
        except Exception as ex:sources[name]='unavailable: '+str(ex)
    sources['thaiwater']=({'status':'skipped_offline'} if a.offline else thaiwater())
    area='ชุมพร (จุดอ้างอิง; ไม่ใช่ค่ารายอำเภอ/ตำบล)'; dataset=datasets.get('ชุมพร (จุดอ้างอิง)')
    def make(period_hours,steps):
        result=[]
        for i in range(steps):
            a1=now+dt.timedelta(hours=i*period_hours);b1=a1+dt.timedelta(hours=period_hours)
            result.append({'period':a1.strftime('%d/%m %H:%M')+' – '+b1.strftime('%d/%m %H:%M'),'area':area,'metrics':summarize(dataset,a1,b1)})
        return result
    forecast=make(6,12);nowcast=make(1,6)
    report={'generated_at':dt.datetime.now(TZ).isoformat(timespec='seconds'),'sources':sources,'forecast':forecast,'nowcast':nowcast,'advice':advice(forecast),'limitations':['No radar motion tracking','No verified 77-province grid','No ML calibration','No soil-water balance without measured soil inputs','ECMWF 0-6h is not a radar nowcast']}
    (ROOT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (ROOT/'report.html').write_text(render(report),encoding='utf-8')
    print('Wrote',ROOT/'report.html','and report.json')
if __name__=='__main__':main()
