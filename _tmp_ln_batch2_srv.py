# -*- coding: utf-8 -*-
"""辽宁第二批 md 源定额卷灌库 SQL 生成器（服务器版）。

在服务器 /opt/metal/sp-quota/liaoning-2024 下执行，db 路径：
  quota-extract-<vol>/db_pdf/<vol>_quota.db

输出：/opt/metal/sp-quota/ln_batch2_import.sql
"""
import gzip
import json
import os
import sqlite3
import uuid

BASE = "/opt/metal/sp-quota/liaoning-2024"
OUT_SQL = "/opt/metal/sp-quota/ln_batch2_import.sql"

REGION = "21"
ORG = "辽宁省住房和城乡建设厅"
YEAR = 2024
PARENT_LIB = "a1b2c3d4-0021-2024-0000-000000000021"
LIB_INSTALL = "c36b6741-fc02-3245-4863-84f42572f0aa"
LIB_MUNICIPAL = "0a9d9de3-f7ec-a2e9-c195-fe4bd36df9a2"
LIB_ZZS_NAME = "辽宁省装配式建筑工程定额（2024）"
LIB_ZZS = str(uuid.uuid5(uuid.NAMESPACE_URL, "costing://" + LIB_ZZS_NAME))

VOLS_INSTALL = ["jx", "rl", "jz", "tf", "yb", "zn", "xtx", "gy"]
VOLS_MUNICIPAL = ["sz09", "lj", "qh", "sd", "scl"]


def q(s):
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def db_path(vol):
    return os.path.join(BASE, "quota-extract-%s" % vol, "db_pdf",
                        "%s_quota.db" % vol)


def vol_prefix(vol):
    db = sqlite3.connect(db_path(vol))
    code = db.execute("SELECT item_code FROM items LIMIT 1").fetchone()[0]
    db.close()
    return code.split("-")[0]


def load_chapters(vol):
    import re
    db = sqlite3.connect(db_path(vol))
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT chapter_code, title FROM toc WHERE level='章行' "
        "AND chapter_code IS NOT NULL ORDER BY seq").fetchall()
    if rows:
        chs = []
        for i, r in enumerate(rows, 1):
            name = (r["title"] or "").split("(")[0].strip()
            name = re.sub(r"^第[一二三四五六七八九十]+章\s*", "", name).strip()
            chs.append((r["chapter_code"], i, name))
        db.close()
        return chs
    codes = [r[0] for r in db.execute(
        "SELECT DISTINCT chapter_code FROM items "
        "WHERE chapter_code IS NOT NULL ORDER BY chapter_code")]
    chs = []
    for i, c in enumerate(codes, 1):
        nm = db.execute("SELECT title FROM toc WHERE title LIKE ? LIMIT 1",
                        ("%" + c + "%",)).fetchone()
        name = nm[0].split("(")[0].strip() if nm else c
        name = re.sub(r"^第[一二三四五六七八九十]+章\s*", "", name).strip()
        chs.append((c, i, name))
    db.close()
    return chs


def emit_vol(w, stats, vol, lib_id, specialty, new_lib):
    db = sqlite3.connect(db_path(vol))
    db.row_factory = sqlite3.Row
    prefix = vol_prefix(vol)
    chs = load_chapters(vol)

    if new_lib:
        w("DELETE FROM quota_library_item_labors WHERE library_item_id IN "
          "(SELECT id FROM quota_library_items WHERE library_id = %s);" % q(lib_id))
        w("DELETE FROM quota_library_item_materials WHERE library_item_id IN "
          "(SELECT id FROM quota_library_items WHERE library_id = %s);" % q(lib_id))
        w("DELETE FROM quota_library_item_machines WHERE library_item_id IN "
          "(SELECT id FROM quota_library_items WHERE library_id = %s);" % q(lib_id))
        w("DELETE FROM quota_library_items WHERE library_id = %s;" % q(lib_id))
        w("DELETE FROM quota_chapters WHERE library_id = %s;" % q(lib_id))
        w("DELETE FROM libraries WHERE id = %s;" % q(lib_id))
        w("INSERT INTO libraries (id, owner_type, owner_id, library_type, name, "
          "description, version_no, published, created_at, updated_at, parent_id) "
          "VALUES (%s, 'SYSTEM', '00000000-0000-0000-0000-000000000000', "
          "'QUOTA', %s, %s, '2024', true, now(), now(), %s);" % (
              q(lib_id), q(LIB_ZZS_NAME),
              q("【专业子库，父级：辽宁省建设工程计价依据（2024）】"
                "装配式建筑 zzs 单列，251 子目，md 源定额站点清洗数据"),
              q(PARENT_LIB)))
    else:
        like_code = q(prefix + "-%")
        w("DELETE FROM quota_library_item_labors WHERE library_item_id IN "
          "(SELECT id FROM quota_library_items WHERE library_id = %s "
          "AND quota_code LIKE %s);" % (q(lib_id), like_code))
        w("DELETE FROM quota_library_item_materials WHERE library_item_id IN "
          "(SELECT id FROM quota_library_items WHERE library_id = %s "
          "AND quota_code LIKE %s);" % (q(lib_id), like_code))
        w("DELETE FROM quota_library_item_machines WHERE library_item_id IN "
          "(SELECT id FROM quota_library_items WHERE library_id = %s "
          "AND quota_code LIKE %s);" % (q(lib_id), like_code))
        w("DELETE FROM quota_library_items WHERE library_id = %s "
          "AND quota_code LIKE %s;" % (q(lib_id), like_code))
        for cc, _chno, _name in chs:
            w("DELETE FROM quota_chapters WHERE library_id = %s "
              "AND chapter_code = %s;" % (q(lib_id), q(cc)))

    sort_base = {"sz09": 100, "lj": 110, "qh": 120, "sd": 130, "scl": 140,
                 "jx": 100, "rl": 110, "jz": 120, "tf": 130, "yb": 140,
                 "zn": 150, "xtx": 160, "gy": 170}.get(vol, 0)
    for i, (cc, chno, name) in enumerate(chs):
        w("INSERT INTO quota_chapters (id, library_id, chapter_code, "
          "chapter_no, name, sort_order, created_at) VALUES "
          "(gen_random_uuid(), %s, %s, %d, %s, %d, now());" % (
              q(lib_id), q(cc), chno, q(name), sort_base + i))
        stats["chapters"] += 1

    items = db.execute("SELECT * FROM items ORDER BY item_code").fetchall()
    for it in items:
        item_id = str(uuid.uuid5(uuid.NAMESPACE_URL,
                                 "costing://%s/%s" % (lib_id, it["item_code"])))
        rc = []
        for tbl, typ in (("item_labors", "labor"),
                         ("item_materials", "material"),
                         ("item_machines", "machine")):
            for c in db.execute(
                    "SELECT * FROM %s WHERE item_code=? ORDER BY seq"
                    % tbl, (it["item_code"],)).fetchall():
                e = {"name": c["name"], "type": typ, "unit": c["unit"],
                     "consumption": c["qty"]}
                if c["unpriced"]:
                    e["unpriced"] = True
                rc.append(e)
                stats[{"labor": "labors", "material": "materials",
                       "machine": "machines"}[typ]] += 1
        bl = it["labor_fee"] or 0
        bm = it["material_fee"] or 0
        bma = it["machine_fee"] or 0
        bmg = it["combined_fee"] or 0
        w("INSERT INTO quota_library_items (id, library_id, region_code, "
          "specialty_code, quota_code, quota_name, unit, "
          "resource_composition, tags, work_content, base_price_labor, "
          "base_price_material, base_price_machine, base_price_management, "
          "effective_year, published_org) VALUES (%s, %s, %s, %s, "
          "%s, %s, %s, %s::jsonb, '[]'::jsonb, %s, %s, %s, %s, %s, %d, %s);" % (
              q(item_id), q(lib_id), q(REGION), q(specialty),
              q(it["item_code"]), q(it["name"]), q(it["unit"]),
              q(json.dumps(rc, ensure_ascii=False)),
              q(it["work_content"]), bl, bm, bma, bmg, YEAR, q(ORG)))
        stats["items"] += 1
    db.close()


def gen():
    stats = {"items": 0, "labors": 0, "materials": 0, "machines": 0,
             "chapters": 0}
    lines = ["BEGIN;"]
    w = lines.append
    for vol in VOLS_INSTALL:
        emit_vol(w, stats, vol, LIB_INSTALL, "安装", new_lib=False)
    for vol in VOLS_MUNICIPAL:
        emit_vol(w, stats, vol, LIB_MUNICIPAL, "市政", new_lib=False)
    emit_vol(w, stats, "zzs", LIB_ZZS, "装配式", new_lib=True)
    w("COMMIT;")
    return "\n".join(lines), stats


def main():
    sql, stats = gen()
    with open(OUT_SQL, "w", encoding="utf-8", newline="\n") as f:
        f.write(sql)
    print("LIB_ZZS =", LIB_ZZS)
    print("SQL:", OUT_SQL, os.path.getsize(OUT_SQL), "bytes")
    print("stats:", json.dumps(stats, ensure_ascii=False))
    total = stats["labors"] + stats["materials"] + stats["machines"]
    assert stats["items"] == 12668, stats
    assert total == 169297, stats
    print("守恒断言通过：items=12668 cons=169297")


if __name__ == "__main__":
    main()
