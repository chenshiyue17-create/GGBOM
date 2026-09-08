# -*- coding: utf-8 -*-
import json
import urllib.request
from pathlib import Path

def inspect_rc():
    url = "http://127.0.0.1:30010/remote/info"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        
    routes = []
    for r in data.get("HttpRoutes", []):
        routes.append(f"{r.get('Verb')} {r.get('Path')}")
        
    out = Path("/Users/cc/Desktop/GGBOM/xxxx/output/rc_routes.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(routes), encoding="utf-8")
    print(f"✅ 获取到 {len(routes)} 条 Remote Control 路由，已写入 {out}")

if __name__ == "__main__":
    inspect_rc()
