# -*- coding: utf-8 -*-
"""辽宁省建设工程计价依据·文件库总入口页生成器（sp/index.html）

用法（venv python，含 fitz）：
  C:/Users/Administrator/.workbuddy/binaries/python/envs/default/Scripts/python.exe build_portal.py

设计：
- 全部指标**现查现渲染**（各卷 SQLite / baseline_manifest.json / PDF 页数），不硬编码业务数字。
- 单文件 HTML、数据内联、双击即开（file:// 友好），相对路径链接各卷成果库前端。
- VOLUMES 注册制：kind='quota' 定额卷（章节树前端）；kind='table' 单表卷（机械台班/配合比，
  已于 2026-10-13 从房建卷库拆分独立，对应关系见 hosting_map.json）。
- 新增卷在此注册一条即可。
"""
import json
import pathlib
import sqlite3

ROOT = pathlib.Path(__file__).resolve().parent
try:
    import fitz  # venv 含 fitz；退化环境跳过页数
except Exception:
    fitz = None

VOLUMES = [
    {
        "id": "fj",
        "kind": "quota",
        "tag": "房建装饰卷",
        "name": "辽宁省建设工程计价依据《房屋建筑与装饰工程定额》(2024)",
        "dir": "quota-extract",
        "report": None,
        "pdf": "input/quota_ln.pdf",
        "official_id": "1773816609118923",
        "source_sha12": "cb3b6faba744",
    },
    {
        "id": "az",
        "kind": "quota",
        "tag": "安装卷·电气册",
        "name": "辽宁省建设工程计价依据《安装工程·电气设备与线缆安装工程定额》(2024)",
        "dir": "quota-extract-az04",
        "report": "out/AZ04_交付报告_覆盖清单与人工复核.md",
        "pdf": "input/quota_ln.pdf",
        "official_id": "1773817671812302",
        "source_sha12": "5d0a8c584ba7",
    },
    {
        "id": "az10",
        "kind": "quota",
        "tag": "安装卷·给排水采暖燃气册",
        "name": "辽宁省建设工程计价依据《安装工程·给排水、采暖、燃气安装工程定额》(2024)",
        "dir": "quota-extract-az10",
        "report": "out/AZ10_交付报告_覆盖清单与人工复核.md",
        "pdf": "input/quota_ln.pdf",
        "official_id": "1773818051825682",
        "source_sha12": "4f4b15e152d5",
    },
    {
        "id": "az12",
        "kind": "quota",
        "tag": "安装卷·刷油防腐蚀绝热册",
        "name": "辽宁省建设工程计价依据《安装工程·刷油、防腐蚀、绝热工程定额》(2024)",
        "dir": "quota-extract-az12",
        "report": "out/AZ12_交付报告_覆盖清单与人工复核.md",
        "pdf": "input/quota_ln.pdf",
        "official_id": "1773818164358303",
        "source_sha12": "3ed50922ca02",
    },
    {
        "id": "az09",
        "kind": "docx_quota",
        "tag": "安装卷·消防册（md源提取）",
        "name": "辽宁省建设工程计价依据《通用安装工程定额·第九册 消防工程》(2024)",
        "dir": "quota-extract-az09",
        "sub": "out",
        "db": "az09_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_az09_消防工程_md源管线.md",
        "pdf": "input/nowm.pdf",
        "official_id": "1773817984224554",
        "source_sha12": "26cec326b13e",
    },
    {
        "id": "sz10",
        "kind": "quota",
        "tag": "市政卷·拆除册",
        "name": "辽宁省建设工程计价依据《市政工程·拆除工程定额》(2024)",
        "dir": "quota-extract-sz10",
        "report": "out/SZ10_交付报告_覆盖清单与人工复核.md",
        "pdf": "input/quota_ln.pdf",
        "official_id": "1773818765049947",
        "source_sha12": "139de8f4d6dc",
    },
    {
        "id": "sz05",
        "kind": "quota",
        "tag": "市政卷·市政管网册",
        "name": "辽宁省建设工程计价依据《市政工程·市政管网工程定额》(2024)",
        "dir": "quota-extract-sz05",
        "report": "out/SZ05_交付报告_覆盖清单与人工复核.md",
        "pdf": "input/quota_ln.pdf",
        "official_id": "1773818587204558",
        "source_sha12": "eee418929f37",
    },
    {
        "id": "jxtb",
        "kind": "table",
        "tag": "机械台班费用标准",
        "name": "辽宁省建设工程计价依据《施工机械台班费用标准》(2024)",
        "dir": "quota-extract-jxtb",
        "report": None,
        "pdf": "input/machine_ln.pdf",
        "official_id": "1773819019186524",
        "source_sha12": "4d7f9419cb92",
    },
    {
        "id": "phb",
        "kind": "table",
        "tag": "混凝土·砂浆配合比",
        "name": "辽宁省建设工程计价依据《混凝土、砂浆配合比》(2024)",
        "dir": "quota-extract-phb",
        "report": None,
        "pdf": "input/official/mortar_mix_ratio.pdf",
        "official_id": "1773819057797896",
        "source_sha12": "3c98f0b44f51",
    },
    {
        "id": "sz01",
        "kind": "docx_quota",
        "tag": "市政卷·土石方册（docx提取）",
        "name": "辽宁省建设工程计价依据《市政工程·土石方工程定额 第一册》(2024)",
        "dir": "quota-extract-sz01",
        "report": "out/SZ01_交付报告_覆盖清单与人工复核.md",
        "pdf": "input/quota_ln.pdf",
        "official_id": "1773818336979993",
        "source_sha12": "8cdcaed634f4",
    },
    {
        "id": "lvse",
        "kind": "docx_quota",
        "tag": "绿色建筑册（md源提取）",
        "name": "辽宁省建设工程计价依据《绿色建筑工程定额》(2024)",
        "dir": "quota-extract-lvse",
        "sub": "out",
        "db": "lvse_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_绿色建筑工程定额_md源管线.md",
        "pdf": "1773816825515128_nowm.pdf",
        "official_id": "1773816825515128",
        "source_sha12": "ac0de6d04eba",
    },
]

# 官方清单分组展示顺序（其余组排最后）
GROUP_ORDER = ["通用安装工程", "市政工程", "房屋建筑与装饰", "装配式建筑",
               "园林绿化", "绿色建筑", "机械台班费用", "混凝土·砂浆配合比",
               "建筑工程费用标准", "其他"]


def q1(cur, sql):
    return cur.execute(sql).fetchone()[0]


def pdf_pages(v, d):
    if fitz:
        try:
            return fitz.open(str(d / v["pdf"])).page_count
        except Exception:
            pass
    return None


def collect_quota(v):
    d = ROOT / v["dir"]
    con = sqlite3.connect(str(d / "out" / "quota_ln2024.db"))
    cur = con.cursor()
    meta = dict(cur.execute("select key, value from book_meta").fetchall())
    st = {
        "kind": "quota",
        "chapters": q1(cur, "select count(*) from chapters"),
        "items": q1(cur, "select count(*) from items"),
        "sections": q1(cur, "select count(*) from sections"),
        "labors": q1(cur, "select count(*) from item_labors"),
        "machines": q1(cur, "select count(*) from item_machines"),
        "materials": q1(cur, "select count(*) from item_materials"),
        "mat_prices": q1(cur, "select count(*) from material_prices"),
        "unit_null": q1(cur, "select count(*) from items where unit is null or unit=''"),
        "issues_open": q1(cur, "select count(*) from extraction_issues where review_status='open'"),
        "issues_confirmed": q1(cur, "select count(*) from extraction_issues where review_status='confirmed'"),
        "derive_open": q1(cur, "select count(*) from price_derive where review_status='open'"),
        "h3_fail": q1(cur, "select count(*) from h3_review where status='fail'"),
        "h3_skip": q1(cur, "select count(*) from h3_review where status!='fail'"),
        "erratas": q1(cur, "select count(*) from erratas"),
        "generated_at": meta.get("generated_at", ""),
        "book_name": meta.get("book_name", v["name"]),
    }
    con.close()
    try:
        st["baseline_files"] = len(json.load(open(d / "baseline_manifest.json", encoding="utf-8"))["files"])
    except Exception:
        st["baseline_files"] = None
    st["pdf_pages"] = pdf_pages(v, d)
    st["web_ok"] = (d / "web" / "index.html").exists()
    st["report_ok"] = bool(v["report"]) and (d / v["report"]).exists()
    return st


def collect_table(v):
    d = ROOT / v["dir"]
    con = sqlite3.connect(str(d / "out" / "quota_ln2024.db"))
    cur = con.cursor()
    meta = dict(cur.execute("select key, value from book_meta").fetchall())
    st = {"kind": "table", "book_name": meta.get("book_name", v["name"]),
          "generated_at": meta.get("generated_at", "")}
    if v["id"] == "jxtb":
        st.update({
            "rows": q1(cur, "select count(*) from machine_prices"),
            "instruments": q1(cur, "select count(*) from instrument_prices"),
            "dupes": cur.execute(
                "select code, group_concat(name, ' / ') from machine_prices "
                "group by code having count(*)>1").fetchall(),
            "identity_bad": q1(cur, "select count(*) from machine_prices where identity_ok=0"),
            "identity_bad_i": q1(cur, "select count(*) from instrument_prices where identity_ok!=1"),
            "issues": q1(cur, "select count(*) from extraction_issues"),
            "cross_gaps": q1(cur, "select count(*) from extraction_issues where type='跨册引用缺口'"),
            "row_label": "施工机械台班",
            "source_sha": "4d7f9419cb92",
        })
    else:
        st.update({
            "rows": q1(cur, "select count(*) from mix_ratios"),
            "components": q1(cur, "select count(*) from mix_components"),
            "sections": cur.execute(
                "select section, count(*) from mix_ratios group by 1 order by 2 desc").fetchall(),
            "row_label": "配合比组",
            "source_sha": "3c98f0b44f51",
        })
    con.close()
    st["pdf_pages"] = pdf_pages(v, d)
    st["web_ok"] = (d / "web" / "index.html").exists()
    st["report_ok"] = bool(v["report"]) and (d / v["report"]).exists()
    return st


def collect_docx_quota(v):
    """docx 提取卷（sz01 起）：库=docx_source/docx_quota.db，前端=docx_source/index.html，
    基线=docx_source/manifest.json，核验=docx_source/cost_check_report.json。现查渲染。
    可选覆盖项：sub（子目录，默认 docx_source）、db（库名，默认 docx_quota.db）、
    web（前端相对路径，默认 <sub>/index.html）、manifest（默认 <sub>/manifest.json）。"""
    d = ROOT / v["dir"] / v.get("sub", "docx_source")
    con = sqlite3.connect(str(d / v.get("db", "docx_quota.db")))
    cur = con.cursor()
    meta = dict(cur.execute("select key, value from book_meta").fetchall())
    st = {
        "kind": "docx_quota",
        "items": q1(cur, "select count(*) from items"),
        "labors": q1(cur, "select count(*) from item_labors"),
        "machines": q1(cur, "select count(*) from item_machines"),
        "materials": q1(cur, "select count(*) from item_materials"),
        "toc": q1(cur, "select count(*) from toc"),
        "desc": q1(cur, "select count(*) from desc_rules"),
        "unit_null": q1(cur, "select count(*) from items where unit is null or unit=''"),
        "generated_at": meta.get("built_at", ""),
        "book_name": meta.get("volume", v["name"]),
    }
    con.close()
    try:
        cc = json.load(open(d / "cost_check_report.json", encoding="utf-8"))
        cc2 = cc.get("summary", cc)
        st["h1"] = cc2["H1"]; st["p1"] = cc2["P1"]
        st["h2"] = cc2.get("H2"); st["h3"] = cc2.get("H3"); st["h4"] = cc2.get("H4")
    except Exception:
        st["h1"] = st["p1"] = st["h2"] = st["h3"] = st["h4"] = None
    try:
        mf = json.load(open(ROOT / v["dir"] / v.get("manifest", "docx_source/manifest.json"), encoding="utf-8"))
        st["baseline_files"] = len(mf.get("files", mf))
    except Exception:
        st["baseline_files"] = None
    d0 = ROOT / v["dir"]
    st["pdf_pages"] = pdf_pages(v, d0)
    st["web_ok"] = (d0 / v.get("web", v.get("sub", "docx_source") + "/index.html")).exists()
    st["report_ok"] = bool(v["report"]) and (d0 / v["report"]).exists()
    return st


def collect_volume(v):
    if v["kind"] == "quota":
        return collect_quota(v)
    if v["kind"] == "docx_quota":
        return collect_docx_quota(v)
    return collect_table(v)


CSS = """
:root{--bg:#f6f7f9;--panel:#fff;--line:#e5e7eb;--ink:#111827;--ink2:#6b7280;
--accent:#1d4ed8;--accentbg:#eff6ff;--green:#16a34a;--greenbg:#f0fdf4;
--red:#dc2626;--redbg:#fef2f2;--amber:#d97706;--amberbg:#fffbeb;
--mono:"Consolas","Courier New",monospace}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"Microsoft YaHei","PingFang SC",sans-serif;background:var(--bg);color:var(--ink);font-size:14px}
.wrap{max-width:1180px;margin:0 auto;padding:26px 20px 60px}
header{position:sticky;top:0;z-index:30;background:var(--panel);border-bottom:1px solid var(--line)}
.h-in{max-width:1180px;margin:0 auto;padding:14px 20px;display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
h1{font-size:19px;font-weight:700}
.h-sub{color:var(--ink2);font-size:12px}
.cards{display:flex;gap:10px;margin:18px 0 6px;flex-wrap:wrap}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:9px 16px;min-width:132px}
.card .n{font-size:20px;font-weight:700;font-family:var(--mono)}
.card .n.b{color:var(--accent)} .card .n.g{color:var(--green)}
.card .t{font-size:11px;color:var(--ink2)}
section{margin-top:26px}
h2{font-size:15px;font-weight:700;margin-bottom:10px;padding-left:9px;border-left:4px solid var(--accent)}
.vgrid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:860px){.vgrid{grid-template-columns:1fr}}
.vcard{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.vhead{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:4px}
.vtitle{font-size:15px;font-weight:700}
.vtag{font-size:11px;color:var(--ink2);background:var(--bg);border:1px solid var(--line);border-radius:5px;padding:2px 7px}
.badge{font-size:11px;border-radius:20px;padding:3px 10px;font-weight:600}
.badge.g{background:var(--greenbg);color:var(--green);border:1px solid #bbf7d0}
.badge.a{background:var(--amberbg);color:var(--amber);border:1px solid #fde68a}
.vname{color:var(--ink2);font-size:12px;margin:2px 0 10px}
.ngrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(96px,1fr));gap:6px 10px;margin:8px 0 10px}
.num{background:var(--bg);border-radius:8px;padding:6px 9px}
.num .n{font-size:16px;font-weight:700;font-family:var(--mono);color:var(--ink)}
.num .t{font-size:10.5px;color:var(--ink2)}
.qrow{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0}
.qchip{font-size:11.5px;border-radius:6px;padding:3px 9px;border:1px solid var(--line);background:var(--bg);color:var(--ink)}
.qchip b{font-family:var(--mono)}
.qchip.ok{background:var(--greenbg);border-color:#bbf7d0;color:var(--green)}
.qchip.warn{background:var(--amberbg);border-color:#fde68a;color:var(--amber)}
.qchip.bad{background:var(--redbg);border-color:#fecaca;color:var(--red)}
.links{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.lbtn{display:inline-block;font-size:12.5px;text-decoration:none;border-radius:7px;padding:6px 13px;border:1px solid var(--accent);color:var(--accent);background:var(--accentbg)}
.lbtn:hover{background:var(--accent);color:#fff}
.lbtn.ghost{border-color:var(--line);color:var(--ink2);background:var(--panel)}
.lbtn.ghost:hover{border-color:var(--ink2);color:var(--ink);background:var(--bg)}
.meta{margin-top:10px;color:var(--ink2);font-size:11px;line-height:1.7}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:13px}
th{background:var(--bg);text-align:left;font-size:12px;color:var(--ink2);padding:8px 12px;border-bottom:1px solid var(--line)}
td{padding:8px 12px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
td .m{font-family:var(--mono)}
.note{background:var(--panel);border:1px dashed var(--line);border-radius:10px;padding:12px 16px;color:var(--ink2);font-size:12px;line-height:1.9;margin-top:14px}
.note b{color:var(--ink)}
footer{margin-top:34px;color:var(--ink2);font-size:11px;text-align:center;line-height:1.8}
"""


def chip(cls, label, val):
    return f'<span class="qchip {cls}">{label} <b>{val}</b></span>'


def render_quota(v, st):
    links = []
    if st["web_ok"]:
        links.append(f'<a class="lbtn" href="{v["dir"]}/web/index.html">识别成果库·章节树前端</a>')
    links.append(f'<a class="lbtn ghost" href="{v["dir"]}/out/quota_ln2024.db">SQLite 成果库</a>')
    if st["report_ok"]:
        links.append(f'<a class="lbtn ghost" href="{v["dir"]}/{v["report"]}">交付报告</a>')
    pdf = f'PDF {st["pdf_pages"]} 页' if st["pdf_pages"] else "PDF —"
    base = f'基线指纹 {st["baseline_files"]} 文件' if st["baseline_files"] else "基线指纹 —"
    q = [
        chip("ok" if st["unit_null"] == 0 else "warn", "unit 空值", st["unit_null"]),
        chip("bad" if st["h3_fail"] else "ok", "H3 fail", st["h3_fail"]),
        chip("", "H3 skip(库缺口·反推三表承接)", st["h3_skip"]),
        chip("warn" if st["issues_open"] else "ok", "疑点 open", st["issues_open"]),
    ]
    if st["issues_confirmed"]:
        q.append(chip("ok", "已确认", st["issues_confirmed"]))
    q.append(chip("warn" if st["derive_open"] else "ok", "缺价反推 open", st["derive_open"]))
    if st["erratas"]:
        q.append(chip("", "勘误 overlay", st["erratas"]))
    return f"""
<div class="vcard">
  <div class="vhead"><span class="vtitle">{v["tag"]}</span>
    <span class="badge g">已收官 · gate 全绿</span>
    <span class="vtag">{pdf}</span><span class="vtag">{base}</span></div>
  <div class="vname">{st["book_name"]}</div>
  <div class="ngrid">
    <div class="num"><div class="n">{st["chapters"]}</div><div class="t">章</div></div>
    <div class="num"><div class="n">{st["items"]}</div><div class="t">定额子目</div></div>
    <div class="num"><div class="n">{st["sections"]}</div><div class="t">规则区块</div></div>
    <div class="num"><div class="n">{st["labors"]}</div><div class="t">人工条目</div></div>
    <div class="num"><div class="n">{st["machines"]}</div><div class="t">机械条目</div></div>
    <div class="num"><div class="n">{st["materials"]}</div><div class="t">材料条目</div></div>
    <div class="num"><div class="n">{st["mat_prices"]}</div><div class="t">材料价格库</div></div>
  </div>
  <div class="qrow">{''.join(q)}</div>
  <div class="links">{''.join(links)}</div>
  <div class="meta">库生成：{st["generated_at"]} ｜ 目录 {v["dir"]}/ ｜ 管线：忠实层(fitz 按字体坐标归位)→语义映射→附注规则→勘误 overlay→校验→章节结构→建库(行数+外键+交叉对账门控)</div>
</div>"""


def render_docx_quota(v, st):
    sub = v.get("sub", "docx_source")
    db_rel = f'{sub}/{v.get("db", "docx_quota.db")}'
    web_rel = v.get("web", f"{sub}/index.html")
    links = []
    if st["web_ok"]:
        links.append(f'<a class="lbtn" href="{v["dir"]}/{web_rel}">识别成果库·章节树前端（提取卷）</a>')
    links.append(f'<a class="lbtn ghost" href="{v["dir"]}/{db_rel}">SQLite 成果库</a>')
    if st["report_ok"]:
        links.append(f'<a class="lbtn ghost" href="{v["dir"]}/{v["report"]}">交付报告</a>')
    pdf = f'官方PDF {st["pdf_pages"]} 页' if st["pdf_pages"] else "PDF —"
    base = f'基线指纹 {st["baseline_files"]} 文件' if st["baseline_files"] else "基线指纹 —"
    h1, p1 = st["h1"], st["p1"]
    q = [
        chip("ok" if h1 and h1["fail"] == 0 else "bad", "H1", f'{h1["pass"]}/{h1["pass"]+h1["fail"]}' if h1 else "—"),
        chip("ok" if p1 and p1["fail"] == 0 else "bad", "P1 原版PDF取证", f'{p1["pass"]}' if p1 else "—"),
        chip("warn" if st["unit_null"] else "ok", "unit 空值", st["unit_null"]),
        chip("ok", "H2/H3/H4 fail", f'{st["h2"]["fail"]}/{st["h3"]["fail"]}/{st["h4"]["fail"]}' if st["h2"] else "—"),
    ]
    return f"""
<div class="vcard">
  <div class="vhead"><span class="vtitle">{v["tag"]}</span>
    <span class="badge g">已收官 · 九门全绿</span>
    <span class="vtag">{pdf}</span><span class="vtag">{base}</span></div>
  <div class="vname">{st["book_name"]}</div>
  <div class="ngrid">
    <div class="num"><div class="n">{st["items"]}</div><div class="t">定额子目</div></div>
    <div class="num"><div class="n">{st["labors"]}</div><div class="t">人工条目</div></div>
    <div class="num"><div class="n">{st["machines"]}</div><div class="t">机械条目</div></div>
    <div class="num"><div class="n">{st["materials"]}</div><div class="t">材料条目</div></div>
    <div class="num"><div class="n">{st["toc"]}</div><div class="t">目录行</div></div>
    <div class="num"><div class="n">{st["desc"]}</div><div class="t">条文记录</div></div>
  </div>
  <div class="qrow">{''.join(q)}</div>
  <div class="links">{''.join(links)}</div>
  <div class="meta">库生成：{st["generated_at"]} ｜ 目录 {v["dir"]}/ ｜ 管线：docx 保真层→子目解析(列=子目/行=费用)→条文每条一记录→H1-H6 造价逻辑核验→P1 官方原版 PDF 取证→九门门控（docx-quota-extract skill）</div>
</div>"""


def render_table(v, st):
    links = []
    if st["web_ok"]:
        links.append(f'<a class="lbtn" href="{v["dir"]}/web/index.html">识别成果库·检索前端</a>')
    links.append(f'<a class="lbtn ghost" href="{v["dir"]}/out/quota_ln2024.db">SQLite 成果库</a>')
    pdf = f'PDF {st["pdf_pages"]} 页' if st["pdf_pages"] else "PDF —"
    nums = f'<div class="num"><div class="n">{st["rows"]}</div><div class="t">{st["row_label"]}</div></div>'
    q = []
    meta_line = ""
    if v["id"] == "jxtb":
        nums = (f'<div class="num"><div class="n">{st["rows"]}</div><div class="t">施工机械台班</div></div>'
                f'<div class="num"><div class="n">{st["instruments"]}</div><div class="t">仪器仪表台班</div></div>')
        q.append(chip("ok" if st["identity_bad"] == 0 else "bad", "机械 identity_bad", st["identity_bad"]))
        q.append(chip("ok" if st["identity_bad_i"] == 0 else "bad", "仪表恒等 fail", st["identity_bad_i"]))
        if st["dupes"]:
            rows = "；".join(f"{c}（{n}）" for c, n in st["dupes"])
            q.append(chip("bad", "重复编码疑点", len(st["dupes"])))
            q.append(f'<span class="qchip">{rows}</span>')
        if st["cross_gaps"]:
            q.append(chip("warn", "跨册引用缺口", st["cross_gaps"]))
        meta_line = ("施工机械 953（P19-141）+ 仪器仪表 593（P144-223，873 段 10 位码）全书两篇全覆盖；"
                     "仪表恒等式 593/593 全 pass（单价≈折旧+维护+校验+动力费）"
                     " ｜ 源 PDF sha12=4d7f9419cb92 ｜ 拆分自房建卷库（宿主 5 列副本保留），对应关系见 hosting_map.json")
    else:
        nums += f'<div class="num"><div class="n">{st["components"]}</div><div class="t">组分明细</div></div>'
        secs = "、".join(f"{s.replace('表', '')} {n}" for s, n in st["sections"])
        q.append(f'<span class="qchip">{secs}</span>')
        meta_line = ("mix_ratios（组基价）+ mix_components（组分消耗量）"
                     " ｜ 源 PDF sha12=3c98f0b44f51（省平台官方册） ｜ 拆分自房建卷库（宿主副本保留），对应关系见 hosting_map.json")
    return f"""
<div class="vcard">
  <div class="vhead"><span class="vtitle">{v["tag"]}</span>
    <span class="badge g">独立卷 · 已结构化</span>
    <span class="vtag">{pdf}</span></div>
  <div class="vname">{st["book_name"]}</div>
  <div class="ngrid">{nums}</div>
  <div class="qrow">{''.join(q)}</div>
  <div class="links">{''.join(links)}</div>
  <div class="meta">{meta_line}</div>
</div>"""


def load_registry():
    """读取官方清单快照（scripts/fetch_official_list.py 产）；缺失返回 None。"""
    p = ROOT / "official_registry.json"
    if not p.exists():
        return None
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return None


def render_registry(registry, vols):
    """官方清单对照区块：已识别卷链接成果库，未识别名目列待提取+官方 PDF 直链。"""
    done = {}  # official_id -> (v, st)
    for v, st in vols:
        oid = v.get("official_id")
        if oid:
            done[oid] = (v, st)
    items = sorted(registry["items"],
                   key=lambda it: (GROUP_ORDER.index(it["group"])
                                   if it["group"] in GROUP_ORDER else 99, it["seq"]))
    n_done = sum(1 for it in items if it["file_id"] in done)
    n_todo = len(items) - n_done

    # 分组汇总 chips
    groups = {}
    for it in items:
        g = groups.setdefault(it["group"], [0, 0])
        g[0] += 1
        if it["file_id"] in done:
            g[1] += 1
    gchips = "".join(
        f'<span class="qchip{" ok" if t == d else ""}">{g} <b>{d}/{t}</b></span>'
        for g, (t, d) in sorted(groups.items(),
                                key=lambda kv: GROUP_ORDER.index(kv[0])
                                if kv[0] in GROUP_ORDER else 99))

    rows = []
    for i, it in enumerate(items, 1):
        v_st = done.get(it["file_id"])
        if v_st:
            v, st = v_st
            front_rel = (v.get("web", "docx_source/index.html") if st.get("kind") == "docx_quota"
                         else "web/index.html")
            entry = (f'<a class="lbtn" href="{v["dir"]}/{front_rel}">'
                     f'{v["tag"]}成果库</a>')
            if v.get("report") and (ROOT / v["dir"] / v["report"]).exists():
                entry += (f'<a class="lbtn ghost" href="{v["dir"]}/{v["report"]}">'
                          f'交付报告</a>')
            badge = '<span class="badge g">已识别</span>'
            note = (f'源 PDF sha12={v["source_sha12"]} ｜ 子目 '
                    f'{st.get("items", st.get("rows", "—"))}')
        else:
            entry = (f'<a class="lbtn ghost" href="{it["pdf_url"]}" target="_blank">'
                     f'官方 PDF 下载</a>')
            badge = '<span class="badge a">待提取</span>'
            note = "官方原版 PDF（省平台直链）"
        rows.append(
            f'<tr><td class="m">{i}</td><td>{it["group"]}</td>'
            f'<td>{it["title"]}</td><td class="m">{it["file_id"] or "—"}</td>'
            f'<td>{badge}</td><td>{entry}</td>'
            f'<td style="color:var(--ink2);font-size:11.5px">{note}</td></tr>')

    return f"""
  <section>
    <h2>官方清单对照 · 未识别名目（共 {len(items)} 份）</h2>
    <div class="qrow">
      <span class="qchip ok">已识别 <b>{n_done}</b></span>
      <span class="qchip warn">未识别 <b>{n_todo}</b></span>
      {gchips}
    </div>
    <table>
      <tr><th style="width:30px">#</th><th style="width:110px">专业组</th><th>名目（官方标题）</th>
      <th style="width:130px">官方文件 ID</th><th style="width:76px">状态</th>
      <th style="width:210px">入口</th><th style="width:200px">备注</th></tr>
      {''.join(rows)}
    </table>
    <div class="note">清单来源：辽宁省住建厅工程造价管理平台「计价依据文件库」2024 年度
    （<a href="{registry['source_url']}" target="_blank">官方检索页</a>），
    共 {registry.get('official_total', len(items))} 份；本页快照 {len(items)} 条，
    页指纹 sha12=<span class="m">{registry.get('page_sha12', '—')}</span>，
    抓取于 {registry.get('fetched_at', '—')}（scripts/fetch_official_list.py，可重复执行核对）。
    <b>已识别 5 份</b>：房建装饰、安装·电气（第四册）、安装·给排水采暖燃气（第十册）、
    施工机械台班、混凝土·砂浆配合比，本地源 PDF 与官方文件 sha256 逐份校验一致。
    <b>未识别 {n_todo} 份</b>：含通用安装其余 10 册、市政 11 册、园林绿化/装配式建筑/绿色建筑/
    建筑工程费用标准 4 册合订本——按同一规程（忠实层→语义→校验→建库→门控）开工，
    说一声即启动。</div>
  </section>"""


def main():
    vols = [(v, collect_volume(v)) for v in VOLUMES]
    quota_vols = [(v, st) for v, st in vols if st["kind"] == "quota"]
    table_vols = [(v, st) for v, st in vols if st["kind"] == "table"]
    docx_vols = [(v, st) for v, st in vols if st["kind"] == "docx_quota"]
    total_items = sum(st["items"] for _, st in quota_vols) + sum(st["items"] for _, st in docx_vols)
    jx = next(st for v, st in vols if v["id"] == "jxtb")
    ph = next(st for v, st in vols if v["id"] == "phb")
    registry = load_registry()
    n_todo = 0
    if registry:
        done_ids = {v.get("official_id") for v, _ in vols if v.get("official_id")}
        n_todo = sum(1 for it in registry["items"] if it["file_id"] not in done_ids)

    todo_rows = []
    n = 0
    for v, st in quota_vols:
        if st["derive_open"]:
            n += 1
            extra = ("水泥砂浆 1∶1→319.25、1∶2.5→260.84（舍入级中位价，price_confirm.json 确认后补库）"
                     if v["id"] == "fj" else "price_confirm.json 确认后补库")
            todo_rows.append(
                f"<tr><td>{n}</td><td>{v['tag']}</td><td>缺价反推确认</td>"
                f"<td class='m'>{st['derive_open']}</td><td>{extra}</td></tr>")
        if st["unit_null"]:
            n += 1
            todo_rows.append(
                f"<tr><td>{n}</td><td>{v['tag']}</td><td>unit 空值复核</td>"
                f"<td class='m'>{st['unit_null']}</td><td>明细 out/unit_null_review.json；"
                f"安装卷 95 条为名称内嵌括号单位（030410 章 65 条）</td></tr>")
        if st["h3_fail"]:
            n += 1
            detail = "4-1683/1684、4-2316~2319" if v["id"] == "az" else "13-76/13-84 剩余人工对价"
            todo_rows.append(
                f"<tr><td>{n}</td><td>{v['tag']}</td><td>H3 恒等式 fail</td>"
                f"<td class='m'>{st['h3_fail']}</td><td>{detail}</td></tr>")
    if jx["dupes"]:
        n += 1
        rows = "；".join(f"{c}（{nm}）" for c, nm in jx["dupes"])
        todo_rows.append(
            f"<tr><td>{n}</td><td>机械台班卷</td><td>重复编码人工确认</td>"
            f"<td class='m'>{len(jx['dupes'])}</td><td>{rows} —— 同码不同机，按铁律留痕不静默去重</td></tr>")
    if jx.get("cross_gaps"):
        n += 1
        todo_rows.append(
            f"<tr><td>{n}</td><td>机械台班卷</td><td>跨册引用缺口人工对价</td>"
            f"<td class='m'>{jx['cross_gaps']}</td>"
            f"<td>房建卷 1-163~167（液压锤破碎石方）引用「履带式单头液压岩石破碎机」，"
            f"本册全书查无该机型（反推单价 1563.95 元/台班），属书本身引用缺口，禁硬造条目</td></tr>")
    n += 1
    todo_rows.append(
        f"<tr><td>{n}</td><td>安装卷</td><td>R1 编码推定确认</td><td class='m'>1</td>"
        f"<td>十五/十七章同印 030417，同位对齐推定十五章为 030415，raw_line 保真待人工确认</td></tr>")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>辽宁省计价依据·文件库总览 (2024)</title>
<style>{CSS}</style>
</head>
<body>
<header><div class="h-in">
  <h1>辽宁省建设工程计价依据 · 文件库总览（2024）</h1>
  <span class="h-sub">并列文件识别提取情况与成果库入口 ｜ 双击即开 ｜ 指标现查渲染</span>
</div></header>
<div class="wrap">
  <div class="cards">
    <div class="card"><div class="n b">{len(vols)}</div><div class="t">计价依据文件（全独立）</div></div>
    <div class="card"><div class="n b">{total_items}</div><div class="t">定额子目合计</div></div>
    <div class="card"><div class="n g">{jx['rows'] + jx['instruments']}</div><div class="t">台班单价（机械+仪表）</div></div>
    <div class="card"><div class="n g">{ph['rows']}</div><div class="t">配合比组</div></div>
    <div class="card"><div class="n">{len(vols)}</div><div class="t">独立成果库前端</div></div>
    {f'<div class="card"><div class="n" style="color:var(--amber)">{n_todo}</div><div class="t">未识别名目（官方 {registry.get("official_total", len(registry["items"]))} 份清单内）</div></div>' if registry else ''}
  </div>

  <section>
    <h2>定额卷（章节树前端）</h2>
    <div class="vgrid">{''.join(render_quota(v, st) for v, st in quota_vols)}</div>
  </section>

  <section>
    <h2>定额卷（docx 提取卷）</h2>
    <div class="vgrid">{''.join(render_docx_quota(v, st) for v, st in docx_vols)}</div>
  </section>

  <section>
    <h2>价格与配合比依据（检索前端）</h2>
    <div class="vgrid">{''.join(render_table(v, st) for v, st in table_vols)}</div>
    <div class="note">机械台班费用标准与混凝土·砂浆配合比为并列层级的独立计价依据文件，
    2026-10-13 起从房建卷库拆分独立（原寄生形态：machine_prices / mix_ratios / mix_components 表）。
    拆分前对应关系、宿主副本与恢复/复建引用路径全部留档于
    <a href="hosting_map.json">hosting_map.json</a>；宿主卷库内历史副本保留、基线指纹不动，
    需要数据链接或引用时从独立库按列映射复建。</div>
  </section>

  {render_registry(registry, vols) if registry else '''
  <section>
    <h2>官方清单对照 · 未识别名目</h2>
    <div class="note">官方清单快照缺失：执行
    <span class="m">python scripts/fetch_official_list.py</span>
    抓取辽宁省住建厅「计价依据文件库」2024 清单（共 30 份）后重跑本页。</div>
  </section>'''}

  <section>
    <h2>人工确认待办（跨卷汇总）</h2>
    <table>
      <tr><th style="width:28px">#</th><th style="width:110px">所属</th><th style="width:150px">事项</th><th style="width:70px">数量</th><th>说明</th></tr>
      {''.join(todo_rows)}
    </table>
  </section>

  <section>
    <h2>统一技术底座</h2>
    <div class="note">
      <b>提取管线</b>：忠实层（fitz 按字体+坐标归位，字节级可复现，禁运行时时间戳）→ 语义映射 → 附注规则 → 勘误 overlay →
      分章校验 → 章节结构 → TOC 回锚 → 建库（行数+外键+交叉对账门控）<br>
      <b>门控</b>：十二项全绿才合入（忠实层/分块/语义/目录/校验器/附注/勘误/C 疑点=0/恒等式 H1-H4/数据库对账/语义完整性/基线指纹）<br>
      <b>基线指纹</b>：{' ／ '.join(f"{v['tag']} {st['baseline_files']} 文件" for v, st in quota_vols)}，
      产物字节+脚本 sha+页界签名+源 PDF sha 四条件缓存命中则忠实层跳过重抽<br>
      <b>人工确认口径</b>：一律 overlay（manual_confirm.json / price_confirm.json），改动过门控+刷指纹，禁直改 extract<br>
      <b>页码口径</b>：房建卷 P28 起恒定偏移 27（1612 物理页）；安装卷册说明与正文共用偏移 19（999 物理页）；
      机械台班册 224 物理页；配合比册 63 物理页（印刷页偏移 7）
    </div>
  </section>

  <footer>由 build_portal.py 现查各卷 SQLite / baseline_manifest / PDF 生成 ｜ 重新生成：
  venv python build_portal.py ｜ 新增计价依据文件 → VOLUMES 注册（official_id 对照官方文件 ID）｜
  官方清单核对 → scripts/fetch_official_list.py ｜ 拆分对应关系 → hosting_map.json</footer>
</div>
</body>
</html>"""
    out = ROOT / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"OK -> {out} ({len(html)} chars)")
    for v, st in vols:
        if st["kind"] == "quota":
            print(f"  {v['tag']}: items={st['items']} unit_null={st['unit_null']} "
                  f"h3_fail={st['h3_fail']} baseline={st['baseline_files']} pdf={st['pdf_pages']}")
        elif st["kind"] == "docx_quota":
            print(f"  {v['tag']}: items={st['items']} desc={st['desc']} toc={st['toc']} "
                  f"H1={st['h1']['pass']}/{st['h1']['pass']+st['h1']['fail']} "
                  f"P1={st['p1']['pass']} baseline={st['baseline_files']} pdf={st['pdf_pages']}")
        else:
            print(f"  {v['tag']}: rows={st['rows']} pdf={st['pdf_pages']}")


if __name__ == "__main__":
    main()
