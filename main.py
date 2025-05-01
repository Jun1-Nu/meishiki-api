from fastapi import FastAPI
from datetime import datetime
import ephem
from typing import Optional

app = FastAPI()

# 干支定義
tenkan = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
chishi = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

# 十二運対応表
juuniun = {
    '甲': ['死','墓','絶','胎','養','長生','沐浴','冠帯','建禄','帝旺','衰','病'],
    '乙': ['病','死','墓','絶','胎','養','長生','沐浴','冠帯','建禄','帝旺','衰'],
    '丙': ['衰','病','死','墓','絶','胎','養','長生','沐浴','冠帯','建禄','帝旺'],
    '丁': ['帝旺','衰','病','死','墓','絶','胎','養','長生','沐浴','冠帯','建禄'],
    '戊': ['建禄','帝旺','衰','病','死','墓','絶','胎','養','長生','沐浴','冠帯'],
    '己': ['冠帯','建禄','帝旺','衰','病','死','墓','絶','胎','養','長生','沐浴'],
    '庚': ['沐浴','冠帯','建禄','帝旺','衰','病','死','墓','絶','胎','養','長生'],
    '辛': ['長生','沐浴','冠帯','建禄','帝旺','衰','病','死','墓','絶','胎','養'],
    '壬': ['養','長生','沐浴','冠帯','建禄','帝旺','衰','病','死','墓','絶','胎'],
    '癸': ['胎','養','長生','沐浴','冠帯','建禄','帝旺','衰','病','死','墓','絶']
}

def get_juuniun(day_stem, branch):
    return juuniun[day_stem][chishi.index(branch)]

def get_eto(year):
    eto_index = (year - 1984) % 60
    stem = tenkan[eto_index % 10]
    branch = chishi[eto_index % 12]
    return stem, branch

zokan = {
    '子': ['癸'],
    '丑': ['己', '癸', '辛'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '庚', '戊'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲']
}

gogyou = {
    '甲': '木', '乙': '木',
    '丙': '火', '丁': '火',
    '戊': '土', '己': '土',
    '庚': '金', '辛': '金',
    '壬': '水', '癸': '水'
}

relations = {
    ('同','陽'): '比肩', ('同','陰'): '劫財',
    ('生','陽'): '偏印', ('生','陰'): '印綬',
    ('剋','陽'): '偏官', ('剋','陰'): '正官',
    ('被剋','陽'): '偏財', ('被剋','陰'): '正財',
    ('泄','陽'): '傷官', ('泄','陰'): '食神'
}

def get_relation(base, target):
    base_elm, target_elm = gogyou[base], gogyou[target]
    base_yin, target_yin = tenkan.index(base) % 2, tenkan.index(target) % 2
    yin_relation = '陽' if target_yin == 0 else '陰'

    if base_elm == target_elm:
        return relations[('同', yin_relation)]
    elif (base_elm, target_elm) in [('木','火'),('火','土'),('土','金'),('金','水'),('水','木')]:
        return relations[('泄', yin_relation)]
    elif (target_elm, base_elm) in [('木','火'),('火','土'),('土','金'),('金','水'),('水','木')]:
        return relations[('生', yin_relation)]
    elif (base_elm, target_elm) in [('木','土'),('火','金'),('土','水'),('金','木'),('水','火')]:
        return relations[('剋', yin_relation)]
    elif (target_elm, base_elm) in [('木','土'),('火','金'),('土','水'),('金','木'),('水','火')]:
        return relations[('被剋', yin_relation)]
    else:
        return '不明'

def get_zokan_relations(branch, base_stem):
    return [(stem, get_relation(base_stem, stem)) for stem in zokan.get(branch, [])]

def get_month_eto(year, month, day):
    birth = datetime(year, month, day)
    setsurei = get_setsurei_date(year, month)
    if birth < setsurei:
        month -= 1
        if month == 0:
            year -= 1
            month = 12
    month_branch = chishi[(month + 1) % 12]
    year_stem_index = (year - 1984) % 10
    month_stem_index = (year_stem_index * 2 + month) % 10
    month_stem = tenkan[month_stem_index]
    return month_stem, month_branch

def get_day_eto(target_date):
    base_date = datetime(1900, 1, 31)
    delta_days = (target_date - base_date).days
    stem = tenkan[delta_days % 10]
    branch = chishi[delta_days % 12]
    return stem, branch

def get_hour_eto(day_stem, hour):
    index = hour // 2 % 12
    branch = chishi[index]
    stem_index = (tenkan.index(day_stem) * 2 + index) % 10
    stem = tenkan[stem_index]
    return stem, branch

def get_setsurei_date(year, month):
    solar_terms = {
        1: (2, 4), 2: (3, 6), 3: (4, 5), 4: (5, 5),
        5: (6, 6), 6: (7, 7), 7: (8, 7), 8: (9, 7),
        9: (10, 8), 10: (11, 7), 11: (12, 7), 12: (1, 6)
    }
    m, d = solar_terms[month]
    return datetime(year if month != 12 else year + 1, m, d)

@app.get("/get_bazi")
def get_bazi(year: int, month: int, day: int, hour: int, gender: str, target_year: Optional[int] = None):
    birth_date = datetime(year, month, day)
    year_stem, year_branch = get_eto(year)
    month_stem, month_branch = get_month_eto(year, month, day)
    day_stem, day_branch = get_day_eto(birth_date)
    hour_stem, hour_branch = get_hour_eto(day_stem, hour)

    year_rel = get_relation(day_stem, year_stem)
    month_rel = get_relation(day_stem, month_stem)
    hour_rel = get_relation(day_stem, hour_stem)

    year_zokan = get_zokan_relations(year_branch, day_stem)
    month_zokan = get_zokan_relations(month_branch, day_stem)
    day_zokan = get_zokan_relations(day_branch, day_stem)
    hour_zokan = get_zokan_relations(hour_branch, day_stem)

    year_un = get_juuniun(day_stem, year_branch)
    month_un = get_juuniun(day_stem, month_branch)
    day_un = get_juuniun(day_stem, day_branch)
    hour_un = get_juuniun(day_stem, hour_branch)

    # 大運（仮実装：出生年＋10年ごとに8期）
    base_index = (tenkan.index(month_stem) + 1) % 10
    daiyun = []
    for i in range(8):
        stem = tenkan[(base_index + i) % 10]
        branch = chishi[(chishi.index(month_branch) + i) % 12]
        relation = get_relation(day_stem, stem)
        daiyun.append({
            "start_age": i * 10,
            "stem": stem,
            "branch": branch,
            "relation": relation
        })

    ming_data = {
        "birth": birth_date.strftime("%Y-%m-%d"),
        "gender": gender,
        "year_pillar": f"{year_stem}{year_branch}",
        "year_relation": year_rel,
        "year_zokan": year_zokan,
        "year_un": year_un,
        "month_pillar": f"{month_stem}{month_branch}",
        "month_relation": month_rel,
        "month_zokan": month_zokan,
        "month_un": month_un,
        "day_pillar": f"{day_stem}{day_branch}",
        "day_zokan": day_zokan,
        "day_un": day_un,
        "hour_pillar": f"{hour_stem}{hour_branch}",
        "hour_relation": hour_rel,
        "hour_zokan": hour_zokan,
        "hour_un": hour_un,
        "daiun": daiyun,
        "message": "四柱＋通変星＋蔵干＋十二運＋大運を算出しました"
    }

    if target_year:
        stem = tenkan[(target_year - 1984) % 10]
        branch = chishi[(target_year - 1984) % 12]
        relation = get_relation(day_stem, stem)
        ming_data["target_year"] = {
            "year": target_year,
            "stem": stem,
            "branch": branch,
            "relation": relation
        }

    return ming_data

@app.get("/get_ryunen")
def get_ryunen(start_year: int, span: int, day_stem: str):
    result = []
    for i in range(span):
        year = start_year + i
        stem = tenkan[(year - 1984) % 10]
        branch = chishi[(year - 1984) % 12]
        relation = get_relation(day_stem, stem)
        result.append({
            "year": year,
            "stem": stem,
            "branch": branch,
            "relation": relation
        })
    return result

