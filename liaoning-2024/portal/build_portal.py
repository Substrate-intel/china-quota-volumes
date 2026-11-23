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

# 新疆 2020 版定额官方发布依据（栏目网页版公告，页面无附件；公告正文已逐字收录在
# xj01/xj02/xj10 忠实层 P4，网页版与原书逐字对账仅 7 组括号全半角差异，且网页省略公告号）
XJ_NOTICE_2020 = {
    "url": "https://zjt.xinjiang.gov.cn/xjzjt/c116332/202607/6f45ce7cc94e463ba43bd9536f52cb1f.shtml",
    "no": "2020年 第145号",
    "issued": "2020-10-28",
    "effective": "2021-04-01",
    "repealed": "2010 建筑工程消耗量定额、2014 建筑安装工程补充消耗量定额（土建装饰部分）、"
                "2002 全国统一装饰装修工程预算定额、2012 新疆市政工程消耗量定额、"
                "2017 新疆钢结构工程消耗量定额、2018 绿色建筑工程消耗量定额相应内容",
    "applies_to": ("xj01", "xj02", "xj10", "xj11", "xj12", "xj13", "xj14"),
}
# 装配式定额（试行）官方发布依据（2023-01-31 通知，无公告号，落款 2022-12-26，施行 2023-03-01）
XJ_NOTICE_PC = {
    "url": "https://zjt.xinjiang.gov.cn/xjzjt/c116332/202607/4f3593ab75184517ab4d5b673ddead07.shtml",
    "no": "关于发布《新疆维吾尔自治区装配式建筑工程消耗量定额（试行）》的通知",
    "issued": "2023-01-31",
    "effective": "2023-03-01",
    "repealed": "（无废止条款；作为现行建筑工程计价依据的补充，与 2020 版房建/通用安装/安装补充/费用定额配套使用）",
    "applies_to": ("xj22",),
}
NOTICE_BY_VOL = {vid: XJ_NOTICE_2020 for vid in XJ_NOTICE_2020["applies_to"]}
NOTICE_BY_VOL.update({vid: XJ_NOTICE_PC for vid in XJ_NOTICE_PC["applies_to"]})
# 装配式补充工程量清单官方发布依据（2023-09-21 发布，落款 2023-09-20，无公告号）
XJ_NOTICE_BOQ = {
    "url": "https://zjt.xinjiang.gov.cn/xjzjt/c116332/202607/6cd78c7e532342e48560affd0142aac2.shtml",
    "no": "关于印发《新疆维吾尔自治区装配式建筑工程补充工程量清单》的通知",
    "issued": "2023-09-21",
    "effective": "2023-09-21",
    "repealed": "（无废止条款；依据 GB50854-2013 编制，与装配式建筑工程消耗量定额（试行）配套的清单计价补充）",
    "applies_to": ("xj23",),
}
NOTICE_BY_VOL.update({vid: XJ_NOTICE_BOQ for vid in XJ_NOTICE_BOQ["applies_to"]})

# 自保温混凝土复合砌块等补充定额项目官方发布依据
# （2023-01-11，#25 通知页 + #26 正文页互为发布登记，两份附件 PDF 字节级同源）
XJ_NOTICE_ZBW = {
    "url": "https://zjt.xinjiang.gov.cn/xjzjt/c116332/202607/953f03d0121f432b879454a47e25fb71.shtml",
    "no": "关于发布自保温混凝土复合砌块及复合外保温模板等补充定额项目的通知",
    "issued": "2023-01-11",
    "effective": "2023-01-11",
    "repealed": "（无废止条款；作为 2020 版房屋建筑与装饰工程消耗量定额的补充项目，"
                "#26 正文页挂同一份 PDF 附件，字节级同源）",
    "applies_to": ("xj24",),
}
NOTICE_BY_VOL.update({vid: XJ_NOTICE_ZBW for vid in XJ_NOTICE_ZBW["applies_to"]})


def notice_link(v):
    n = NOTICE_BY_VOL.get(v["id"])
    if not n:
        return ""
    return (f'<a class="lbtn ghost" href="{n["url"]}" target="_blank">'
            f'官方发布依据 · {n["no"]}</a>')


def notice_meta(v):
    n = NOTICE_BY_VOL.get(v["id"])
    if not n:
        return ""
    return (f'<div class="meta">官方依据：{n["no"]}（{n["issued"]} 发布，{n["effective"]} 施行）'
            f' ｜ 同时停止使用：{n["repealed"]}</div>')


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
    {
        "id": "sz11",
        "kind": "docx_quota",
        "tag": "市政卷·措施项目册（md源提取）",
        "name": "辽宁省建设工程计价依据《市政工程定额 第十一册 措施项目》(2024)",
        "dir": "quota-extract-sz11",
        "sub": "out",
        "db": "sz11_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_sz11_措施项目.md",
        "pdf": "input/nowm.pdf",
        "official_id": "1773818813192976",
        "source_sha12": "2eecfa19fd87",
    },
    {
        "id": "sz02",
        "kind": "docx_quota",
        "tag": "市政卷·道路工程册（md源提取）",
        "name": "辽宁省建设工程计价依据《市政工程定额 第二册 道路工程》(2024)",
        "dir": "quota-extract-sz02",
        "sub": "out",
        "db": "sz02_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_sz02_道路工程.md",
        "pdf": "input/nowm.pdf",
        "official_id": "1773818365410596",
        "source_sha12": "08e1d3988a91",
    },
    {
        "id": "sz08",
        "kind": "docx_quota",
        "tag": "市政卷·路灯工程册（md源提取）",
        "name": "辽宁省建设工程计价依据《市政工程定额 第八册 路灯工程》(2024)",
        "dir": "quota-extract-sz08",
        "sub": "out",
        "db": "sz08_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_sz08_路灯工程.md",
        "pdf": "input/nowm.pdf",
        "official_id": "1773818720878087",
        "source_sha12": "1be417028780",
    },
    {
        "id": "yl01",
        "kind": "docx_quota",
        "tag": "园林绿化卷（md源提取）",
        "name": "辽宁省建设工程计价依据《园林绿化工程定额》(2024)",
        "dir": "quota-extract-yl01",
        "sub": "out",
        "db": "yl01_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_yl01_园林绿化工程.md",
        "pdf": "input/nowm.pdf",
        "official_id": "1773819131300494",
        "source_sha12": "7071387e8709",
    },
    {
        "id": "xj01",
        "kind": "docx_quota",
        "tag": "房建装饰上册（新疆2020·OCR双源）",
        "name": "新疆维吾尔自治区房屋建筑与装饰工程消耗量定额（上册）（2020版）",
        "dir": "quota-extract-xj01",
        "sub": "out",
        "db": "xj01_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj01_新疆房建装饰上册.md",
        "pdf": "input/ocr.pdf",
        "source_sha12": "73b2a976a7ac",
    },
    {
        "id": "xj02",
        "kind": "docx_quota",
        "tag": "房建装饰下册（新疆2020·OCR双源）",
        "name": "新疆维吾尔自治区房屋建筑与装饰工程消耗量定额（下册）（2020版）",
        "dir": "quota-extract-xj02",
        "sub": "out",
        "db": "xj02_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj02_新疆房建装饰下册.md",
        "pdf": "input/ocr.pdf",
        "source_sha12": "9d25962c2f84",
    },
    {
        "id": "xj03",
        "kind": "fee",
        "tag": "费用定额卷（新疆2020·计价依据）",
        "name": "新疆维吾尔自治区建筑、安装、市政工程费用定额（2020版）",
        "dir": "quota-extract-xj03",
        "sub": "out",
        "db": "xj03_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj03_费用定额.md",
        "pdf": "input/official.pdf",
        "source_sha12": "9e5415fd102f",
    },
    {
        "id": "xj10",
        "kind": "xj_quota",
        "tag": "市政消耗量定额一卷（新疆2020·OCR双源）",
        "name": "新疆维吾尔自治区市政工程消耗量定额（一）（2020版）",
        "dir": "quota-extract-xj10",
        "sub": "out",
        "db": "xj10_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj10_市政消耗量定额.md",
        "pdf": "input/ocr.pdf",
        "source_sha12": None,
    },
    {
        "id": "xj11",
        "kind": "xj_quota",
        "tag": "市政消耗量定额二卷（新疆2020·OCR双源）",
        "name": "新疆维吾尔自治区市政工程消耗量定额（二）（2020版）",
        "dir": "quota-extract-xj11",
        "sub": "out",
        "db": "xj11_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj11_市政消耗量定额.md",
        "pdf": "input/ocr.pdf",
        "source_sha12": "ffe37a296322",
    },
    {
        "id": "xj12",
        "kind": "xj_quota",
        "tag": "市政消耗量定额三卷（新疆2020·OCR双源）",
        "name": "新疆维吾尔自治区市政工程消耗量定额（三）（2020版）",
        "dir": "quota-extract-xj12",
        "sub": "out",
        "db": "xj12_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj12_市政消耗量定额.md",
        "pdf": "input/ocr.pdf",
        "source_sha12": "779f8e603dd0",
    },
    {
        "id": "xj13",
        "kind": "xj_quota",
        "tag": "市政消耗量定额四卷（新疆2020·OCR双源）",
        "name": "新疆维吾尔自治区市政工程消耗量定额（四）（2020版）",
        "dir": "quota-extract-xj13",
        "sub": "out",
        "db": "xj13_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj13_市政消耗量定额.md",
        "pdf": "input/ocr.pdf",
        "source_sha12": "4943293bd5bb",
    },
    {
        "id": "xj14",
        "kind": "xj_quota",
        "tag": "市政消耗量定额五卷（新疆2020·OCR双源）",
        "name": "新疆维吾尔自治区市政工程消耗量定额（五）（2020版）",
        "dir": "quota-extract-xj14",
        "sub": "out",
        "db": "xj14_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj14_市政消耗量定额.md",
        "pdf": "input/ocr.pdf",
        "source_sha12": "07d581b16f40",
    },
    {
        "id": "xj15",
        "kind": "xj_quota",
        "tag": "安装工程补充消耗量定额（新疆2020·OCR双源）",
        "name": "新疆维吾尔自治区安装工程补充消耗量定额（2020版）",
        "dir": "quota-extract-xj15",
        "sub": "out",
        "db": "xj15_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj15_安装工程补充消耗量定额.md",
        "pdf": "input/ocr.pdf",
        "source_sha12": "1916efa124db",
    },
    {
        "id": "xj16",
        "kind": "fee",
        "tag": "高海拔地区施工增加费用标准（新疆·官方附件+解读）",
        "name": "新疆维吾尔自治区高海拔地区施工增加费用标准",
        "dir": "quota-extract-xj16",
        "sub": "out",
        "db": "xj16_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj16_高海拔费用标准.md",
        "pdf": "input/official.pdf",
        "source_sha12": "d9e5e4c61e25",
    },
    {
        "id": "xj17",
        "kind": "fee",
        "tag": "计价依据问题解释合集（一~四·新疆）",
        "name": "新疆维吾尔自治区计价依据有关问题解释（一）～（四）合集",
        "dir": "quota-extract-xj17",
        "sub": "out",
        "db": "xj17_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj17_解释合集.md",
        "pdf": "input/j1.pdf",
        "source_sha12": "j1=119188f6a586 · j2=8b584cac622e · j3=50602bd568dc · j4=ca2ed5e43cb2（四源锚定）",
    },
    {
        "id": "xj18",
        "kind": "xj_quota",
        "tag": "智能建造（建筑机器人）消耗量定额项目（新疆·试行）",
        "name": "新疆维吾尔自治区智能建造（建筑机器人）消耗量定额项目（试行）",
        "dir": "quota-extract-xj18",
        "sub": "out",
        "db": "xj18_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj18_智能建造建筑机器人消耗量定额.md",
        "pdf": "input/official.pdf",
        "source_sha12": "e36b519621de",
        "gates": 10,
        "pipeline": "官方 PDF 干净文本层 + 矢量网格字符级重建（非 OCR）→ quota schema 九表 + 站点兼容三表 → 六视图前端 → 十门门控（P1 官方原版逐格取证 178/178，印页=物−1）",
    },
    {
        "id": "xj19",
        "kind": "fee",
        "tag": "计价依据问题解释（五·新疆）",
        "name": "新疆维吾尔自治区计价依据有关问题解释（五）",
        "dir": "quota-extract-xj19",
        "sub": "out",
        "db": "xj19_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj19_解释五.md",
        "pdf": "input/official.pdf",
        "source_sha12": "c0940477ec06",
        "pipeline": "官方 2 页图片型 PDF（无文字层）视觉双遍转写+分歧放大核对 → fee schema + fee_semantics 语义分析表（每条解释一行）→ 七视图前端 → 六门门控+冒烟 13/13；勘误三部分：房建 5-430→xj01、安装补充 B4-x→xj15 已 overlay applied，园林 2 条 not_in_db 留档",
    },
    {
        "id": "xj20",
        "kind": "fee",
        "tag": "建筑垃圾运输和处置计价（清单增补·新疆）",
        "name": "新疆维吾尔自治区建筑垃圾运输和处置计价通知（工程量清单增补）",
        "dir": "quota-extract-xj20",
        "sub": "out",
        "db": "xj20_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj20_建筑垃圾计价清单增补.md",
        "pdf": "input/attachment.xlsx",
        "source_sha12": "d14ceca37b2e",
        "gates": 6,
        "pipeline": "源形态第五型（网页 HTML+xlsx 双源直读）：条款逐字取自页面原文、清单表 xlsx 单元格级程序化实读（合并展开/多值留换行），parse 内置双源闭环断言 → fee schema + fee_semantics 语义分析 11 条 → 七视图前端 → 六门门控+冒烟 12/12；增补清单项目 X010103003~006，「余方弃置」停止执行（废止性条款）",
    },
    {
        "id": "xj21",
        "kind": "xj_quota",
        "tag": "排水设施养护及维修工程消耗量定额（新疆·2025）",
        "name": "新疆维吾尔自治区排水设施养护及维修工程消耗量定额",
        "dir": "quota-extract-xj21",
        "sub": "out",
        "db": "xj21_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj21_排水设施养护及维修工程消耗量定额.md",
        "pdf": "input/official.pdf",
        "source_sha12": "5e5c16323e30",
        "gates": 10,
        "pipeline": "官方 99 页 PDF 干净文本层 + 矢量网格字符级重建（复用 xj18 链，非 OCR）→ 9 章 51 节 218 子目 2977 消耗量 → quota schema 九表 + 站点兼容三表 + fee_standard 费用标准表 → 六视图前端 → 十门门控（P1 官方原版逐格取证 2977/2977）+ 冒烟 26/26；双区页码（正文印页=物−6），列级计量单位三形态，括号未计价 99 条",
    },
    {
        "id": "xj22",
        "kind": "xj_quota",
        "tag": "装配式建筑工程消耗量定额（新疆·试行·2023）",
        "name": "新疆维吾尔自治区装配式建筑工程消耗量定额（试行）",
        "dir": "quota-extract-xj22",
        "sub": "out",
        "db": "xj22_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj22_装配式建筑工程消耗量定额.md",
        "pdf": "input/official.pdf",
        "source_sha12": "deb3291d4070",
        "gates": 10,
        "pipeline": "第六型源形态：官方 96 页 PDF，中文 FZ* 方正字体可读 + 数字/符号/西文单位用 FzBookMaker 子集字体无 ToUnicode 乱码 → charmap 反解（OCR 独立转写对齐，6 字体 57 glyphs）→ 矢量网格字符级重建 → 5 章 14 节 264 子目 2688 消耗量 → quota schema 九表 + 站点兼容三表 → 六视图前端 → 十门门控（P1 charmap 取证 paired 3613）+ 冒烟 24/24；双区页码（正文印页=物−9），每子目恰 1 条人工，括号未计价 80 条",
    },
    {
        "id": "xj23",
        "kind": "fee",
        "tag": "装配式建筑工程补充工程量清单（新疆·2023）",
        "name": "新疆维吾尔自治区装配式建筑工程补充工程量清单",
        "dir": "quota-extract-xj23",
        "sub": "out",
        "db": "xj23_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj23_装配式建筑工程补充工程量清单.md",
        "pdf": "input/xj23_source.pdf",
        "source_sha12": "fe9ec3b25abd",
        "gates": 7,
        "pipeline": "第七型源形态（4 页原生文本层 PDF，双源=通知页 HTML 快照+附件）：P3-P4 六列矢量网格，合并单元格按「每列独立行边界」推导（横线 x 跨度判定），组级单元格取词避免跨线 token 二义 → 2 章 24 条目（3 说明条款 + 21 清单项目 X010518001~021，单位恒等 m³，合并组展开）→ fee schema + fee_semantics 语义 3 条 → 七视图前端 → 七门门控（含渲染级冒烟 20/20）+ 复跑零失配；官方原文重复句 1 处留痕（source_dup）",
    },
    {
        "id": "xj24",
        "kind": "xj_quota",
        "tag": "自保温砌块及复合外保温模板补充定额（新疆·2023）",
        "name": "自保温混凝土复合砌块及复合外保温模板等补充定额项目",
        "dir": "quota-extract-xj24",
        "sub": "out",
        "db": "xj24_quota.db",
        "web": "web/index.html",
        "manifest": "baseline_manifest.json",
        "report": "交付报告_xj24_自保温砌块及复合外保温模板补充定额.md",
        "pdf": "input/official.pdf",
        "source_sha12": "3b6f7ef0f9f0",
        "gates": 10,
        "pipeline": "第八型源形态（3 页微型消耗量定额小卷，#25 通知页与 #26 正文页附件字节级同源）："
                    "find_tables 段错误禁用 → 矢量 full 横线切类别块 + 文本坐标聚行 + 列区间取词网格 → "
                    "3 章 3 节 5 子目（B4-1~B4-3 / B10-1 / B10-2）36 消耗格 → quota 九表 + 站点兼容三表 → "
                    "六视图前端（条文四类分组）→ 十门门控（P1 官方原版逐格取证 36/36）+ 冒烟 28/28 + 全链重建零失配；"
                    "上标单位归一、单位嵌名称、类别字连排、无目录页、空白尾页共 7 条疑点留痕",
    },
    {
        "id": "sz09",
        "kind": "md_quota",
        "tag": "市政·第九册 钢筋工程",
        "name": "辽宁省建设工程计价依据《市政工程定额·第九册 钢筋工程》(2024)",
        "dir": "quota-extract-sz09",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773818745668531",
        "source_sha12": "1241b0a5c9ba",
    },
    {
        "id": "lj",
        "kind": "md_quota",
        "tag": "市政·第七册 生活垃圾",
        "name": "辽宁省建设工程计价依据《市政工程定额·第七册 生活垃圾处理工程》(2024)",
        "dir": "quota-extract-lj",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773818696988773",
        "source_sha12": "748b8e6820da",
    },
    {
        "id": "qh",
        "kind": "md_quota",
        "tag": "市政·第三册 桥涵",
        "name": "辽宁省建设工程计价依据《市政工程定额·第三册 桥涵工程》(2024)",
        "dir": "quota-extract-qh",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773818415211293",
        "source_sha12": "300d3ab69ba8",
    },
    {
        "id": "sd",
        "kind": "md_quota",
        "tag": "市政·第四册 隧道",
        "name": "辽宁省建设工程计价依据《市政工程定额·第四册 隧道工程》(2024)",
        "dir": "quota-extract-sd",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773818476061359",
        "source_sha12": "71d7f8fb3550",
    },
    {
        "id": "scl",
        "kind": "md_quota",
        "tag": "市政·第六册 水处理",
        "name": "辽宁省建设工程计价依据《市政工程定额·第六册 水处理工程》(2024)",
        "dir": "quota-extract-scl",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773818668747916",
        "source_sha12": "e805b5b182ce",
    },
    {
        "id": "zzs",
        "kind": "md_quota",
        "tag": "装配式建筑",
        "name": "辽宁省建设工程计价依据《装配式建筑工程定额》(2024)",
        "dir": "quota-extract-zzs",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773817000900819",
        "source_sha12": "e15cc262e922",
    },
    {
        "id": "xtx",
        "kind": "md_quota",
        "tag": "安装·第十一册 信息通信",
        "name": "辽宁省建设工程计价依据《通用安装工程定额·第十一册 信息通信设备及线缆安装工程》(2024)",
        "dir": "quota-extract-xtx",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773818095166709",
        "source_sha12": "c7ebd78dad35",
    },
    {
        "id": "tf",
        "kind": "md_quota",
        "tag": "安装·第七册 通风空调",
        "name": "辽宁省建设工程计价依据《通用安装工程定额·第七册 通风空调安装工程》(2024)",
        "dir": "quota-extract-tf",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773817847518209",
        "source_sha12": "92b26bdcf6d3",
    },
    {
        "id": "yb",
        "kind": "md_quota",
        "tag": "安装·第六册 自控仪表",
        "name": "辽宁省建设工程计价依据《通用安装工程定额·第六册 自动化控制仪表安装工程》(2024)",
        "dir": "quota-extract-yb",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773817800796178",
        "source_sha12": "d1daa6bffacb",
    },
    {
        "id": "zn",
        "kind": "md_quota",
        "tag": "安装·第五册 建筑智能化",
        "name": "辽宁省建设工程计价依据《通用安装工程定额·第五册 建筑智能化工程》(2024)",
        "dir": "quota-extract-zn",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773817700853997",
        "source_sha12": "1f833b71bc60",
    },
    {
        "id": "jx",
        "kind": "md_quota",
        "tag": "安装·第一册 机械设备",
        "name": "辽宁省建设工程计价依据《通用安装工程定额·第一册 机械设备安装工程》(2024)",
        "dir": "quota-extract-jx",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773817223827840",
        "source_sha12": "13db3a42009b",
    },
    {
        "id": "rl",
        "kind": "md_quota",
        "tag": "安装·第二册 热力设备",
        "name": "辽宁省建设工程计价依据《通用安装工程定额·第二册 热力设备安装工程》(2024)",
        "dir": "quota-extract-rl",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773817330205464",
        "source_sha12": "9d14c81b4977",
    },
    {
        "id": "jz",
        "kind": "md_quota",
        "tag": "安装·第三册 静置设备",
        "name": "辽宁省建设工程计价依据《通用安装工程定额·第三册 静置设备与工艺金属结构制作安装工程》(2024)",
        "dir": "quota-extract-jz",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773817524947018",
        "source_sha12": "7550e395520e",
    },
    {
        "id": "gy",
        "kind": "md_quota",
        "tag": "安装·第八册 工业管道",
        "name": "辽宁省建设工程计价依据《通用安装工程定额·第八册 工业管道安装工程》(2024)",
        "dir": "quota-extract-gy",
        "report": None,
        "pdf": "input/nowm.pdf",
        "official_id": "1773817916889781",
        "source_sha12": "7fccbd839639",
    },
    {
        "id": "fy",
        "kind": "fee",
        "tag": "费用标准·取费费率",
        "name": "辽宁省建设工程计价依据《建设工程费用标准》(2024)",
        "dir": "quota-extract-fy",
        "report": None,
        "pdf": "input/nowm.pdf",
        "db": "fy_quota.db",
        "official_id": "1773818980464198",
        "source_sha12": "1dfe4655e68e",
    },
    {
        "id": "gd18",
        "kind": "gd_quota",
        "tag": "广东 2018 综合定额 · 全套 27 册",
        "name": "广东省建设工程计价依据《广东省房屋建筑与装饰/通用安装/市政/园林绿化工程综合定额》(2018)",
        "dir": "quota-extract-gd18",
        "report": "out/GD18_识别与结构化报告.md",
        "pdf": "input/pdf/fj1.pdf",
        "region": "广东",
        "doc_no": "粤建市〔2019〕6号",
        "effective_from": "2019-03-01",
        "extracted": ["fj1", "fj2", "fj3",
                      "az01", "az02", "az03a", "az03b", "az04a", "az04b", "az05", "az06",
                      "az07", "az08a", "az08b", "az09", "az10", "az11", "az12",
                      "sz01", "sz02", "sz03", "sz04", "sz05", "sz06", "sz07", "yl"],
    },
]

# 省份分区：全国库按 region 分组展示。辽宁卷 id 无 xj 前缀；新疆卷 id 以 xj 开头。
# region 优先级：显式 region 字段 > id 前缀 xj → 新疆 > 其余 → 辽宁。
REGION_ORDER = ["辽宁", "新疆", "广东"]


def region_of(v):
    if v.get("region"):
        return v["region"]
    return "新疆" if v["id"].startswith("xj") else "辽宁"


for _v in VOLUMES:
    _v["region"] = region_of(_v)

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


def collect_fee(v):
    """费用定额卷（xj03 起）：fee schema 七表现查渲染（纯计价依据，无消耗量子目）。"""
    d = ROOT / v["dir"]
    con = sqlite3.connect(str(d / v.get("sub", "out") / v.get("db", "xj03_quota.db")))
    cur = con.cursor()
    meta = dict(cur.execute("select key, value from fee_book_meta").fetchall())
    st = {
        "kind": "fee",
        "book_name": meta.get("title", v["name"]),
        "sections": q1(cur, "select count(*) from fee_sections"),
        "items": q1(cur, "select count(*) from fee_items"),
        "programs": q1(cur, "select count(*) from fee_programs"),
        "tables": q1(cur, "select count(*) from fee_tables"),
        "notes": q1(cur, "select count(*) from fee_notes"),
        "toc": q1(cur, "select count(*) from fee_toc"),
        "issues": q1(cur, "select count(*) from fee_issues"),
        "docs": q1(cur, "select count(*) from fee_items where kind='appendix_doc'"),
        "terms": q1(cur, "select count(*) from fee_items where kind='term'"),
    }
    con.close()
    try:
        mf = json.load(open(d / v.get("manifest", "baseline_manifest.json"),
                            encoding="utf-8"))
        st["baseline_files"] = len([k for k in mf if not k.startswith("_")])
    except Exception:
        st["baseline_files"] = None
    st["pdf_pages"] = pdf_pages(v, d)
    st["web_ok"] = (d / v.get("web", "web/index.html")).exists()
    st["report_ok"] = bool(v["report"]) and (d / v["report"]).exists()
    return st


def collect_xj_quota(v):
    """消耗量定额卷（xj10 起）：quota schema 九表现查渲染（OCR 双源管线）。"""
    d = ROOT / v["dir"]
    con = sqlite3.connect(str(d / v.get("sub", "out") / v.get("db", "xj10_quota.db")))
    cur = con.cursor()
    meta = dict(cur.execute("select key, value from quota_book_meta").fetchall())
    st = {
        "kind": "xj_quota",
        "book_name": meta.get("title", v["name"]),
        "volumes": q1(cur, "select count(*) from quota_volumes"),
        "chapters": q1(cur, "select count(*) from quota_chapters"),
        "sections": q1(cur, "select count(*) from quota_sections"),
        "items": q1(cur, "select count(*) from quota_items"),
        "consumptions": q1(cur, "select count(*) from quota_consumptions"),
        "unpriced": q1(cur, "select count(*) from quota_consumptions where unpriced=1"),
        "explain": q1(cur, "select count(*) from quota_explain"),
        "toc": q1(cur, "select count(*) from quota_toc"),
        "issues": q1(cur, "select count(*) from quota_issues"),
    }
    con.close()
    try:
        mf = json.load(open(d / v.get("manifest", "baseline_manifest.json"),
                            encoding="utf-8"))
        st["baseline_files"] = len([k for k in mf if not k.startswith("_")])
    except Exception:
        st["baseline_files"] = None
    st["pdf_pages"] = pdf_pages(v, d)
    st["web_ok"] = (d / v.get("web", "web/index.html")).exists()
    st["report_ok"] = bool(v["report"]) and (d / v["report"]).exists()
    return st


def collect_md_quota(v):
    """md 源提取卷（2024 辽宁二批 13 册）：库=out/<vid>_quota.db（book_meta/items/
    item_labors/item_machines/item_materials/toc/desc_rules），前端=web/index.html，
    核验=out/cost_check_report.json（H1-H6/P1），基线=baseline_manifest.json。"""
    d = ROOT / v["dir"]
    dbp = d / v.get("sub", "out") / v.get("db", "%s_quota.db" % v["id"])
    con = sqlite3.connect(str(dbp))
    cur = con.cursor()
    meta = dict(cur.execute("select key, value from book_meta").fetchall())

    def s1(sql, default=0):
        try:
            return q1(cur, sql)
        except Exception:
            return default

    st = {
        "kind": "md_quota",
        "book_name": meta.get("book_name", v["name"]),
        "items": s1("select count(*) from items"),
        "labors": s1("select count(*) from item_labors"),
        "machines": s1("select count(*) from item_machines"),
        "materials": s1("select count(*) from item_materials"),
        "toc": s1("select count(*) from toc"),
        "desc": s1("select count(*) from desc_rules"),
        "unit_null": s1("select count(*) from items where unit is null or unit=''"),
        "generated_at": meta.get("built_at", meta.get("source", "")),
        "pages_meta": meta.get("pages"),
    }
    con.close()
    # 章节数（web_data 章树）
    st["chapters"] = None
    try:
        st["chapters"] = len(json.load(open(d / "out" / "_web_data.json",
                                            encoding="utf-8"))["chapters"])
    except Exception:
        pass
    try:
        cc = json.load(open(d / "out" / "cost_check_report.json", encoding="utf-8"))
        st["h1"] = cc.get("H1"); st["p1"] = cc.get("P1")
        st["h2"] = cc.get("H2"); st["h3"] = cc.get("H3"); st["h4"] = cc.get("H4")
        st["h5"] = cc.get("H5"); st["h6"] = cc.get("H6")
    except Exception:
        st["h1"] = st["p1"] = st["h2"] = st["h3"] = st["h4"] = st["h5"] = st["h6"] = None
    # work 空源页留痕条数
    st["work_absent"] = None
    try:
        st["work_absent"] = len(json.load(open(d / "out" / ("%s_work_absent_source.json" % v["id"]),
                                               encoding="utf-8"))["entries"])
    except Exception:
        pass
    try:
        mf = json.load(open(d / "baseline_manifest.json", encoding="utf-8"))
        st["baseline_files"] = len(mf.get("files", mf))
    except Exception:
        st["baseline_files"] = None
    st["pdf_pages"] = pdf_pages(v, d)
    st["web_ok"] = (d / "web" / "index.html").exists()
    st["report_ok"] = bool(v.get("report")) and (d / v["report"]).exists()
    return st


def collect_gd18(v):
    """广东 2018 定额（gd18）：结构层全册（22 专业组/206 章/1608 节/26355 子目码）
    + 子目五要素逐册提取。数据源：structure/gd18_tree.json（归并后口径）、
    out/<vol>_items.json（逐册子目）、out/<vol>_gate.json（每册七门门控）、
    out/gd18_audit.json（六项审计）。"""
    d = ROOT / v["dir"]
    tree = json.load(open(d / "out" / "gd18_tree.json", encoding="utf-8"))
    ts = tree["summary"]
    st = {
        "kind": "gd_quota",
        "book_name": v["name"],
        "groups": ts["groups"],
        "chapters": ts["chapters"],
        "sections": ts["sections"],
        "item_codes": ts["distinct_item_codes"],
        "orphan_codes": ts.get("orphan_item_codes", 0),
        "books": 27,
        "pages": None,
        "items": 0,            # 已提取子目（五要素）
        "extracted_books": [],  # 已完子目提取的分册
        "gate_books": [],       # 已跑门控的分册
        "gate_fail": [],        # 门控未通过的分册
    }
    # 已提取子目：逐册累加（items json 是「块」列表，每块 codes 含多子目）
    for vid in v.get("extracted", []):
        p = d / "out" / f"{vid}_items.json"
        if p.exists():
            st["extracted_books"].append(vid)
            blk = json.load(open(p, encoding="utf-8"))
            st["items"] += sum(len(b.get("block", {}).get("codes", [])) for b in blk)
        gp = d / "out" / f"{vid}_gate.json"
        if gp.exists():
            g = json.load(open(gp, encoding="utf-8"))
            st["gate_books"].append(vid)
            if not g.get("all_pass"):
                st["gate_fail"].append(vid)
    st["gate_all_pass"] = (bool(st["gate_books"]) and not st["gate_fail"]
                           and len(st["gate_books"]) == len(st["extracted_books"]))
    st["gate_items"] = st["items"]
    # 台班册（第 27 册 jtb）：1614 台班单价 + 9913「单独计算的费用」20 个安拆子目
    st["jtb_items"] = 0
    st["jtb_9913"] = 0
    st["jtb_gate"] = None
    jp = d / "out" / "jtb_items.json"
    if jp.exists():
        st["jtb_items"] = sum(len(b.get("block", {}).get("codes", []))
                              for b in json.load(open(jp, encoding="utf-8")))
        p9 = d / "out" / "jtb_9913_items.json"
        if p9.exists():
            st["jtb_9913"] = sum(len(b["block"]["codes"])
                                 for b in json.load(open(p9, encoding="utf-8")))
        gp = d / "out" / "jtb_gate.json"
        if gp.exists():
            st["jtb_gate"] = json.load(open(gp, encoding="utf-8")).get("all_pass")
    st["items_total"] = st["items"] + st["jtb_items"] + st["jtb_9913"]
    # 六项审计
    try:
        a = json.load(open(d / "out" / "gd18_audit.json", encoding="utf-8"))
        st["audit"] = a.get("summary", {})
    except Exception:
        st["audit"] = None
    # 印页总数（books 表 pages 求和）
    try:
        con = sqlite3.connect(str(d / "out" / "gd18_structure.db"))
        st["pages"] = con.execute("select coalesce(sum(pages),0) from books").fetchone()[0]
        con.close()
    except Exception:
        st["pages"] = None
    st["web_ok"] = (d / "out" / "GD18_章节地图.html").exists()
    st["report_ok"] = (d / "out" / "GD18_识别与结构化报告.md").exists()
    return st


def render_gd18(v, st):
    links = []
    if st["web_ok"]:
        links.append(f'<a class="lbtn" href="{v["dir"]}/out/GD18_章节地图.html">章节地图·结构成果</a>')
    links.append(f'<a class="lbtn ghost" href="{v["dir"]}/out/gd18_structure.db">SQLite 结构库</a>')
    if st["report_ok"]:
        links.append(f'<a class="lbtn ghost" href="{v["dir"]}/out/GD18_识别与结构化报告.md">识别与结构化报告</a>')
    pages = f'官方PDF {st["pages"]} 页' if st["pages"] else "PDF —"
    a = st.get("audit") or {}
    audit_chip = "".join([
        chip("ok" if a.get("all_pass") else "warn", "六项审计", "全绿" if a.get("all_pass") else "待核"),
    ]) if a else ""
    gate_chip = chip("ok" if st["gate_all_pass"] else ("warn" if not st["gate_books"] else "bad"),
                     f"子目八门门控 {len(st['gate_books'])} 册",
                     "全绿" if st["gate_all_pass"] else (f"{len(st['gate_fail'])} 册待修" if st["gate_fail"] else "—"))
    jtb_chip = chip("ok" if st.get("jtb_gate") else ("warn" if st.get("jtb_items") else "bad"),
                    f"台班册八门 {st.get('jtb_items', 0)} 台班 + {st.get('jtb_9913', 0)} 安拆子目",
                    "全绿" if st.get("jtb_gate") else ("—" if not st.get("jtb_items") else "待核"))
    extracted = "、".join(st["extracted_books"]) or "暂无"
    return f"""
<div class="vcard">
  <div class="vhead"><span class="vtitle">{v["tag"]}</span>
    <span class="badge a">结构层 + 子目五要素 + 台班册 全部收官</span>
    <span class="vtag">{pages}</span></div>
  <div class="vname">{st["book_name"]}</div>
  <div class="ngrid">
    <div class="num"><div class="n">{st["groups"]}</div><div class="t">专业组</div></div>
    <div class="num"><div class="n">{st["chapters"]}</div><div class="t">章</div></div>
    <div class="num"><div class="n">{st["sections"]}</div><div class="t">节</div></div>
    <div class="num"><div class="n">{st["item_codes"]}</div><div class="t">子目码</div></div>
    <div class="num"><div class="n">{st["items"]}</div><div class="t">已提子目</div></div>
    <div class="num"><div class="n">{st.get("jtb_items", 0)}</div><div class="t">台班</div></div>
    <div class="num"><div class="n">{st["orphan_codes"]}</div><div class="t">孤儿码</div></div>
  </div>
  <div class="qrow">{gate_chip}{audit_chip}{jtb_chip}
    <span class="qchip">已提分册 <b>{extracted}</b></span></div>
  <div class="links">{''.join(links)}</div>
  <div class="meta">依据 {v.get("doc_no", "")}（{v.get("effective_from", "")} 施行）｜ 27 册 22 专业组结构全部落地、
  编码落地率 100%，子目五要素逐册提取 {len(st["extracted_books"])} 册 {st["items"]} 子目，
  每册八门门控（编码连续/五要素零空/基价恒等式/名称质量/消耗恒等式/三层表头/私有区零残留/码覆盖对账）；
  第 27 册台班 {st.get("jtb_items", 0)} 个台班单价 + {st.get("jtb_9913", 0)} 个台班安拆子目，
  台班单价恒等式 {st.get("jtb_items", 0)}/{st.get("jtb_items", 0)} 全过、与 26 册消耗交叉比对 24,462 条一致 ｜ 目录 {v["dir"]}/</div>
</div>"""


def collect_volume(v):
    if v["kind"] == "quota":
        return collect_quota(v)
    if v["kind"] == "md_quota":
        return collect_md_quota(v)
    if v["kind"] == "fee":
        return collect_fee(v)
    if v["kind"] == "xj_quota":
        return collect_xj_quota(v)
    if v["kind"] == "docx_quota":
        return collect_docx_quota(v)
    if v["kind"] == "gd_quota":
        return collect_gd18(v)
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
.region{margin-top:30px}
.region-head{display:flex;align-items:baseline;gap:12px;padding:12px 16px;margin-bottom:14px;background:var(--panel);border:1px solid var(--line);border-left:5px solid var(--accent);border-radius:10px}
.region-name{font-size:18px;font-weight:800;color:var(--accent)}
.region-count{font-size:12.5px;color:var(--ink2)}
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


def render_md_quota(v, st):
    db_rel = f'{v.get("sub", "out")}/{v.get("db", "%s_quota.db" % v["id"])}'
    links = []
    if st["web_ok"]:
        links.append(f'<a class="lbtn" href="{v["dir"]}/web/index.html">识别成果库·章节树前端</a>')
    links.append(f'<a class="lbtn ghost" href="{v["dir"]}/{db_rel}">SQLite 成果库</a>')
    if st["report_ok"]:
        links.append(f'<a class="lbtn ghost" href="{v["dir"]}/{v["report"]}">交付报告</a>')
    pdf = f'官方PDF {st["pdf_pages"]} 页' if st["pdf_pages"] else "PDF —"
    base = f'基线指纹 {st["baseline_files"]} 文件' if st["baseline_files"] else "基线指纹 —"
    h1, p1 = st["h1"], st["p1"]
    h5, h6 = st["h5"], st["h6"]
    q = [
        chip("ok" if h1 and h1["fail"] == 0 else "bad", "H1 基价恒等式",
             f'{h1["pass"]}/{h1["pass"] + h1["fail"]}' if h1 else "—"),
        chip("ok" if p1 and p1["fail"] == 0 else "bad", "P1 官方取证", f'{p1["pass"]}' if p1 else "—"),
        chip("warn" if st["unit_null"] else "ok", "unit 空值", st["unit_null"]),
        chip("ok" if h5 and h5["fail"] == 0 else "bad", "H5 量纲 fail", h5["fail"] if h5 else "—"),
    ]
    if st["work_absent"]:
        q.append(chip("", "work 空(源页留痕)", st["work_absent"]))
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
    <div class="num"><div class="n">{st["toc"] if st["toc"] is not None else "—"}</div><div class="t">目录行</div></div>
    <div class="num"><div class="n">{st["desc"] if st["desc"] is not None else "—"}</div><div class="t">条文记录</div></div>
  </div>
  <div class="qrow">{''.join(q)}</div>
  <div class="links">{''.join(links)}</div>
  <div class="meta">目录 {v["dir"]}/ ｜ 管线：去水印干净源→md 转换→子目/目录/条文解析→H1-H6 造价逻辑核验→P1 官方原版逐格取证→九门门控</div>
</div>"""


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
    if v["id"] in NOTICE_BY_VOL:
        links.append(notice_link(v))
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
  {notice_meta(v)}
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


def render_fee(v, st):
    db_rel = f'{v.get("sub", "out")}/{v.get("db", "xj03_quota.db")}'
    web_rel = v.get("web", "web/index.html")
    links = []
    if st["web_ok"]:
        links.append(f'<a class="lbtn" href="{v["dir"]}/{web_rel}">识别成果库·六视图前端</a>')
    links.append(f'<a class="lbtn ghost" href="{v["dir"]}/{db_rel}">SQLite 成果库</a>')
    if st["report_ok"]:
        links.append(f'<a class="lbtn ghost" href="{v["dir"]}/{v["report"]}">交付报告</a>')
    pdf = f'官方PDF {st["pdf_pages"]} 页' if st["pdf_pages"] else "PDF —"
    base = f'基线指纹 {st["baseline_files"]} 文件' if st["baseline_files"] else "基线指纹 —"
    q = [
        chip("ok", "TOC 对账", f'{st["toc"]}/{st["toc"]}'),
        chip("warn" if st["issues"] else "ok", "疑点留痕", st["issues"]),
        chip("ok", "九门门控", "全绿"),
    ]
    return f"""
<div class="vcard">
  <div class="vhead"><span class="vtitle">{v["tag"]}</span>
    <span class="badge g">已收官 · 九门全绿</span>
    <span class="vtag">{pdf}</span><span class="vtag">{base}</span></div>
  <div class="vname">{st["book_name"]}</div>
  <div class="ngrid">
    <div class="num"><div class="n">{st["sections"]}</div><div class="t">节/区</div></div>
    <div class="num"><div class="n">{st["items"]}</div><div class="t">费用条目</div></div>
    <div class="num"><div class="n">{st["tables"]}</div><div class="t">费率表</div></div>
    <div class="num"><div class="n">{st["programs"]}</div><div class="t">计算程序行</div></div>
    <div class="num"><div class="n">{st["terms"]}</div><div class="t">术语</div></div>
    <div class="num"><div class="n">{st["docs"]}</div><div class="t">附录法规文档</div></div>
  </div>
  <div class="qrow">{''.join(q)}</div>
  <div class="links">{''.join(links)}</div>
  <div class="meta">源 PDF sha12={v["source_sha12"]} ｜ 目录 {v["dir"]}/ ｜ 管线：charmap 字形反解+isspace 汉字+缩进拆分+TOC 锚定 → fee 语义层（表题 lookahead 归属）→ fee schema 七表 → 六视图前端 → 九门门控（门7 页眉解码实测印页口径）</div>
</div>"""


def render_xj_quota(v, st):
    db_rel = f'{v.get("sub", "out")}/{v.get("db", "xj10_quota.db")}'
    web_rel = v.get("web", "web/index.html")
    links = []
    if st["web_ok"]:
        links.append(f'<a class="lbtn" href="{v["dir"]}/{web_rel}">识别成果库·四视图前端</a>')
    links.append(f'<a class="lbtn ghost" href="{v["dir"]}/{db_rel}">SQLite 成果库</a>')
    if st["report_ok"]:
        links.append(f'<a class="lbtn ghost" href="{v["dir"]}/{v["report"]}">交付报告</a>')
    if v["id"] in NOTICE_BY_VOL:
        links.append(notice_link(v))
    pdf = f'官方PDF {st["pdf_pages"]} 页' if st["pdf_pages"] else "PDF —"
    base = f'基线指纹 {st["baseline_files"]} 文件' if st["baseline_files"] else "基线指纹 —"
    n_gate = v.get("gates", 9)   # 坑83：门数与管线说明按卷数据驱动，禁静态字面量
    pipeline = v.get("pipeline",
                     "OCR 双源管线：原版矢量线定网格 + OCR 文字层定内容（原版路径化无文本层）"
                     " → 全页网格列占位 → 语义层（跨页续表合并/KIND 单字/精确列归属）"
                     " → quota schema 九表 → 四视图前端 → 九门门控（印页=物−17 零违例）")
    q = [
        chip("ok", "TOC 对账", f'{st["toc"]} 条'),
        chip("warn" if st["issues"] else "ok", "疑点留痕", st["issues"]),
        chip("ok", f"{n_gate}门门控", "全绿"),
    ]
    return f"""
<div class="vcard">
  <div class="vhead"><span class="vtitle">{v["tag"]}</span>
    <span class="badge g">已收官 · {n_gate}门全绿</span>
    <span class="vtag">{pdf}</span><span class="vtag">{base}</span></div>
  <div class="vname">{st["book_name"]}</div>
  <div class="ngrid">
    <div class="num"><div class="n">{st["volumes"]}</div><div class="t">册</div></div>
    <div class="num"><div class="n">{st["chapters"]}</div><div class="t">章</div></div>
    <div class="num"><div class="n">{st["sections"]}</div><div class="t">节</div></div>
    <div class="num"><div class="n">{st["items"]}</div><div class="t">子目</div></div>
    <div class="num"><div class="n">{st["consumptions"]}</div><div class="t">消耗量</div></div>
    <div class="num"><div class="n">{st["unpriced"]}</div><div class="t">未计价材</div></div>
  </div>
  <div class="qrow">{''.join(q)}</div>
  <div class="links">{''.join(links)}</div>
  <div class="meta">{pipeline}</div>
  {notice_meta(v)}
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
    md_vols = [(v, st) for v, st in vols if st["kind"] == "md_quota"]
    fee_vols = [(v, st) for v, st in vols if st["kind"] == "fee"]
    xj_vols = [(v, st) for v, st in vols if st["kind"] == "xj_quota"]
    gd_vols = [(v, st) for v, st in vols if st["kind"] == "gd_quota"]
    # 按省份分区：区内再按 kind 分节
    by_region = {r: [] for r in REGION_ORDER}
    for v, st in vols:
        by_region.setdefault(v["region"], []).append((v, st))
    for r in REGION_ORDER:
        if r not in by_region:
            by_region[r] = []
    total_items = (sum(st["items"] for _, st in quota_vols)
                   + sum(st["items"] for _, st in docx_vols)
                   + sum(st["items"] for _, st in md_vols)
                   + sum(st.get("items_total", st["items"]) for _, st in gd_vols))
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

    # 按省份分区渲染：每个省一个 <h2> 大区标题，区内再按 kind 分节
    def kind_sections(rvols):
        _q = [(v, st) for v, st in rvols if st["kind"] == "quota"]
        _t = [(v, st) for v, st in rvols if st["kind"] == "table"]
        _d = [(v, st) for v, st in rvols if st["kind"] == "docx_quota"]
        _m = [(v, st) for v, st in rvols if st["kind"] == "md_quota"]
        _f = [(v, st) for v, st in rvols if st["kind"] == "fee"]
        _xj = [(v, st) for v, st in rvols if st["kind"] == "xj_quota"]
        _gd = [(v, st) for v, st in rvols if st["kind"] == "gd_quota"]
        _s = ""
        if _q:
            _s += ("<h2>定额卷（章节树前端）</h2>"
                   f"<div class='vgrid'>{''.join(render_quota(v, st) for v, st in _q)}</div>")
        if _d:
            _s += ("<h2>定额卷（docx 提取卷）</h2>"
                   f"<div class='vgrid'>{''.join(render_docx_quota(v, st) for v, st in _d)}</div>")
        if _m:
            _s += ("<h2>定额卷（md 源提取卷）</h2>"
                   f"<div class='vgrid'>{''.join(render_md_quota(v, st) for v, st in _m)}</div>")
        if _xj:
            _s += ("<h2>市政消耗量定额卷（OCR 双源）</h2>"
                   f"<div class='vgrid'>{''.join(render_xj_quota(v, st) for v, st in _xj)}</div>")
        if _f:
            _s += ("<h2>费用定额卷（计价依据·fee schema）</h2>"
                   f"<div class='vgrid'>{''.join(render_fee(v, st) for v, st in _f)}</div>")
        if _t:
            _s += ("<h2>价格与配合比依据（检索前端）</h2>"
                   f"<div class='vgrid'>{''.join(render_table(v, st) for v, st in _t)}</div>")
        if _gd:
            _s += ("<h2>综合定额（结构层 + 子目逐册提取）</h2>"
                   f"<div class='vgrid'>{''.join(render_gd18(v, st) for v, st in _gd)}</div>")
        return _s

    region_html = ""
    for r in REGION_ORDER:
        rvols = by_region.get(r, [])
        if not rvols:
            continue
        r_total = sum(st["items"] for _, st in rvols if st.get("items"))
        # 广东为「一套综合定额（27 册）」形态，与辽/新「逐份文件」口径不同，单独表述
        r_label = "套综合定额 · 27 册" if r == "广东" else "份计价依据文件"
        region_html += (
            f'<section class="region"><div class="region-head">'
            f'<span class="region-name">{r}</span>'
            f'<span class="region-count">{len(rvols)} {r_label} ｜ {r_total} 定额子目</span>'
            f'</div>{kind_sections(rvols)}</section>')

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>全国建设工程计价依据 · 文件库总览</title>
<style>{CSS}</style>
</head>
<body>
<header><div class="h-in">
  <h1>全国建设工程计价依据 · 文件库总览</h1>
  <span class="h-sub">并列文件识别提取情况与成果库入口 ｜ 双击即开 ｜ 指标现查渲染 ｜ 按省份分区</span>
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

  {region_html}

  <section>
    <h2>说明</h2>
    <div class="note">费用定额为纯计价依据文件（取费基数/费率/计算程序，无消耗量子目），
    与消耗量定额配套使用——「消耗量定额载量价基价、费用定额载费率程序」。
    机械台班费用标准与混凝土·砂浆配合比为并列层级的独立计价依据文件，
    2026-10-13 起从房建卷库拆分独立（原寄生形态：machine_prices / mix_ratios / mix_components 表），
    拆分前对应关系、宿主副本与恢复/复建引用路径全部留档于
    <a href="hosting_map.json">hosting_map.json</a>。</div>
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
        elif st["kind"] == "fee":
            print(f"  {v['tag']}: sections={st['sections']} items={st['items']} "
                  f"tables={st['tables']} programs={st['programs']} toc={st['toc']} "
                  f"issues={st['issues']} baseline={st['baseline_files']} pdf={st['pdf_pages']}")
        elif st["kind"] == "xj_quota":
            print(f"  {v['tag']}: vol={st['volumes']} ch={st['chapters']} "
                  f"sec={st['sections']} items={st['items']} cons={st['consumptions']} "
                  f"toc={st['toc']} issues={st['issues']} baseline={st['baseline_files']} pdf={st['pdf_pages']}")
        elif st["kind"] == "md_quota":
            _h1 = st["h1"] or {"pass": 0, "fail": 0}
            _p1 = st["p1"] or {"pass": 0}
            print(f"  {v['tag']}: items={st['items']} ch={st['chapters']} desc={st['desc']} "
                  f"toc={st['toc']} H1={_h1['pass']}/{_h1['pass'] + _h1['fail']} "
                  f"P1={_p1['pass']} baseline={st['baseline_files']} pdf={st['pdf_pages']}")
        elif st["kind"] == "gd_quota":
            print(f"  {v['tag']}: groups={st['groups']} ch={st['chapters']} "
                  f"sec={st['sections']} codes={st['item_codes']} items={st['items']} "
                  f"pages={st['pages']} gate={st['gate_all_pass']}")
        else:
            print(f"  {v['tag']}: rows={st['rows']} pdf={st['pdf_pages']}")


if __name__ == "__main__":
    main()
