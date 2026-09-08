#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
validate_data_tables.py
GGBOM 纯数据驱动体系毫秒级离线校验工具
无需拉起 Unreal 引擎，毫秒级静态校验 JSON 数据表的一致性、合法性与完整性
================================================================================
"""
import os
import sys
import json
import socket
from pathlib import Path

ROOT = Path("/Users/cc/Desktop/GGBOM")
DATA_DIR = ROOT / "xxxx" / "Content" / "Data"

def probe_editor_ports():
    print("🔌 探测 Live Unreal Editor 端口...")
    for port in [30010, 9998, 9999, 6766, 8558]:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.3)
        res = s.connect_ex(('127.0.0.1', port))
        s.close()
        if res == 0:
            print(f"  🟢 端口 {port} 开放中 (已连接)！")

    # UDP Multicast probe
    print("📡 发送 UE Python Remote Execution 组播探测 (239.0.0.1:6766)...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        sock.settimeout(1.0)
        msg = json.dumps({"version": 1, "magic": "ue_py", "type": "open_connection"}).encode('utf-8')
        sock.sendto(msg, ("239.0.0.1", 6766))
        try:
            data, addr = sock.recvfrom(4096)
            resp = json.loads(data.decode('utf-8'))
            print(f"  🎉 收到 Live Editor 回应: {addr} -> {resp}")
        except socket.timeout:
            print("  ⏳ 多播应答超时 (组播可能未绑定)")
        sock.close()
    except Exception as e:
        print(f"  ⚠️ 多播异常: {e}")

def load_json(name):
    path = DATA_DIR / name
    if not path.exists():
        print(f"❌ 数据表缺失: {path}")
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ JSON 语法错误 in {name}: {e}")
        return None

def validate_enemies(data):
    print("🔍 [1/3] 校验敌人数据表 (DT_Enemies.json)...")
    required_fields = ["DisplayName", "MaxHealth", "MoveSpeed", "ContactDamage", "ExpGemValue", "Scale", "BlueprintClass"]
    for eid, info in data.items():
        for rf in required_fields:
            if rf not in info:
                print(f"  ❌ 敌人 [{eid}] 缺失必填字段: {rf}")
                return False
        if info["MaxHealth"] <= 0:
            print(f"  ❌ 敌人 [{eid}] MaxHealth 必须大于 0 (当前: {info['MaxHealth']})")
            return False
        if info["MoveSpeed"] <= 0:
            print(f"  ❌ 敌人 [{eid}] MoveSpeed 必须大于 0 (当前: {info['MoveSpeed']})")
            return False
        print(f"  ✅ 敌人 [{eid}]: {info['DisplayName']} (HP={info['MaxHealth']}, Spd={info['MoveSpeed']}, Scale={info['Scale']})")
    return True

def validate_weapons(data):
    print("🔍 [2/3] 校验武器数据表 (DT_Weapons.json)...")
    required_fields = ["DisplayName", "Damage", "FireRate", "PelletCount", "ProjectileSpeed", "LifeSpan"]
    for wid, info in data.items():
        for rf in required_fields:
            if rf not in info:
                print(f"  ❌ 武器 [{wid}] 缺失必填字段: {rf}")
                return False
        if info["Damage"] <= 0 or info["FireRate"] <= 0 or info["ProjectileSpeed"] <= 0:
            print(f"  ❌ 武器 [{wid}] 数值非法 (Damage, FireRate, ProjectileSpeed 均需大于 0)")
            return False
        print(f"  ✅ 武器 [{wid}]: {info['DisplayName']} (Dmg={info['Damage']}, Rate={info['FireRate']}s, Spd={info['ProjectileSpeed']})")
    return True

def validate_waves(data, enemies_data):
    print("🔍 [3/3] 校验40秒关卡波次推进表 (DT_WaveProgression.json)...")
    for stage_id, stage in data.items():
        total_duration = stage.get("TotalDuration", 40)
        lanes = stage.get("SpawnLanesX", [])
        waves = stage.get("Waves", [])
        print(f"  关卡 [{stage_id}]: 总时长={total_duration}s, 刷怪车道数={len(lanes)}, 波次组数={len(waves)}")
        
        last_time = -1
        for idx, w in enumerate(waves):
            t = w.get("TimeOffset", 0)
            lane_idx = w.get("LaneIndex", 0)
            etype = w.get("EnemyType", "")
            count = w.get("Count", 1)
            
            if t < last_time:
                print(f"  ❌ 波次 #{idx} 时间轴乱序 (当前={t}s, 上一次={last_time}s)")
                return False
            last_time = t
            
            if lane_idx < 0 or lane_idx >= len(lanes):
                print(f"  ❌ 波次 #{idx} 车道索引越界: {lane_idx} (可用车道数: {len(lanes)})")
                return False
                
            if enemies_data and etype not in enemies_data:
                print(f"  ❌ 波次 #{idx} 引用的敌人类型未在 DT_Enemies 中定义: {etype}")
                return False
                
            lane_x = lanes[lane_idx]
            print(f"    - [{t:2d}s] 车道{lane_idx} (X={lane_x:4d}): 刷新 {etype} x{count} 只")
    return True

def main():
    probe_editor_ports()
    print("================================================================")
    print("🚀 开始执行 GGBOM 数据表离线合法性验证...")
    print(f"📁 数据目录: {DATA_DIR}")
    print("================================================================")
    
    enemies = load_json("DT_Enemies.json")
    weapons = load_json("DT_Weapons.json")
    waves = load_json("DT_WaveProgression.json")
    
    if not enemies or not weapons or not waves:
        print("❌ 存在无法加载的数据表，验证失败！")
        sys.exit(1)
        
    ok = validate_enemies(enemies) and validate_weapons(weapons) and validate_waves(waves, enemies)
    
    print("================================================================")
    if ok:
        print("🎉 全部数据表校验通过 (100% PASS)！数据结构高度一致合规！")
        sys.exit(0)
    else:
        print("❌ 数据表校验存在错误，请排查！")
        sys.exit(1)

if __name__ == "__main__":
    main()
