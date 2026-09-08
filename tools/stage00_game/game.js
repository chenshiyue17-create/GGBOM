// ==========================================================================
// GGBOM: 终末医疗兵 - 9:16 STAGE 00 CALIBRATED PROPORTIONS ENGINE
// Exact 1:1 Scale & Dimensional Matching with Concept Art
// ==========================================================================

const canvas = document.getElementById("game-canvas");
const ctx = canvas.getContext("2d");

const V_WIDTH = 540;
const V_HEIGHT = 960;

// Game State
let isPaused = false;
let isMegaBarrage = false;
let megaSpiralAngle = 0;
let lastFpsTime = performance.now();
let frameCount = 0;
let currentFps = 60;
let killCount = 342;
let gemCount = 1680;
let currentZone = "Z1";
let currentZoneIndex = 0;
const ZONES = ["Z1", "Z2", "Z3", "Z4", "Z5", "BossZone"];

// 1. Player (Calibrated Proportions: Bottom Center)
const player = {
    x: V_WIDTH / 2,
    y: V_HEIGHT - 170,
    speed: 3.5,
    hp: 1200,
    maxHp: 1200,
    lvl: 10,
    exp: 65,
    maxExp: 100,
    radius: 18,
    tacticalRingRadius: 36, // Glowing Blue Foot Ring matching Concept Art
    activeSlot: 1,
    aimX: V_WIDTH / 2,
    aimY: 100,
    fireTimer: 0
};

// 2. Boss (Calibrated Giant Scale: Occupies ~30% road width)
const boss = {
    x: V_WIDTH / 2,
    y: 110,
    hp: 4500,
    maxHp: 4500,
    w: 120, // 240px in 1080w
    h: 110,
    radius: 54,
    slamTimer: 0
};

// Weapons (4 Slots)
const weapons = {
    1: { name: "AUTO RIFLE", damage: 28, rate: 7, ammo: 30, maxAmmo: 30, color: "#ffd700", speed: 15, pellets: 1, spread: 0.04 },
    2: { name: "SHOTGUN", damage: 16, rate: 26, ammo: 6, maxAmmo: 6, color: "#ff9100", speed: 13, pellets: 6, spread: 0.35 },
    3: { name: "ROCKET", damage: 140, rate: 45, ammo: 12, maxAmmo: 12, color: "#ff2a8d", speed: 9, pellets: 1, spread: 0, aoe: 95 },
    4: { name: "TESLA GUN", damage: 45, rate: 16, ammo: 8, maxAmmo: 8, color: "#00f2fe", speed: 16, pellets: 1, spread: 0, chain: 3 }
};

// Tactical Inventory
const tacticalProps = {
    barrier: { count: 8, name: "BARRIER", hp: 450, color: "#4facfe", w: 105, h: 32 },
    explosive_barrel: { count: 6, name: "EXPLOSIVE BARREL", hp: 50, dmg: 220, aoe: 130, color: "#ff2a8d", w: 28, h: 38 },
    toxic_barrel: { count: 5, name: "TOXIC BARREL", hp: 60, dotDps: 20, aoe: 100, color: "#00e676", w: 26, h: 36 },
    land_mine: { count: 7, name: "LAND MINE", hp: 1, dmg: 190, aoe: 85, color: "#ff9100", w: 22, h: 22 },
    healing_station: { count: 4, name: "HEALING STATION", hp: 180, healDps: 35, aoe: 90, color: "#00f2fe", w: 36, h: 42 }
};

// Drag State
let draggingProp = null;
let dragWorldPos = { x: 0, y: 0 };
let isHoveringBattlefield = false;

// Collections
let bullets = [];
let enemies = [];
let placedProps = [];
let particles = [];
let expGems = [];
let shockwaves = [];

// Map Ground Image
let mapImg = new Image();

mapImg.onload = () => { console.log("Map image loaded successfully!"); };
mapImg.onerror = () => { console.warn("Map image load failed, using vector fallback"); };
mapImg.src = "/api/exported-image?file=08_Maps/Stage00_Start/T_Map_Stage00_Start_Ground.png";


// Keyboard Input
const keys = {};
window.addEventListener("keydown", (e) => {
    keys[e.key.toLowerCase()] = true;
    if (["1", "2", "3", "4"].includes(e.key)) {
        switchWeapon(parseInt(e.key));
    }
});
window.addEventListener("keyup", (e) => { keys[e.key.toLowerCase()] = false; });

// ==========================================================================
// 1. INITIALIZATION (Matching Concept Art Proportions Exactly)
// ==========================================================================

function initStage00() {
    // 1. Boss Zone Barricade Gate (Width ~340px right below boss)
    placedProps.push({ type: "barrier", x: V_WIDTH / 2, y: 195, w: 320, h: 34, hp: 800, maxHp: 800, isBossGate: true });

    // 2. Mid-Field Barricades (Dividing Z1 / Z2 / Z3)
    placedProps.push({ type: "barrier", x: 120, y: 490, w: 105, h: 30, hp: 450, maxHp: 450 });
    placedProps.push({ type: "barrier", x: 420, y: 490, w: 105, h: 30, hp: 450, maxHp: 450 });

    // 3. Initial Barrels on Field (Matching Concept positions)
    placedProps.push({ type: "explosive_barrel", x: 270, y: 550, w: 28, h: 38, hp: 50, maxHp: 50 }); // Center Blue Ghost Target Barrel
    placedProps.push({ type: "toxic_barrel", x: 100, y: 640, w: 26, h: 36, hp: 60, maxHp: 60 });
    placedProps.push({ type: "explosive_barrel", x: 440, y: 330, w: 28, h: 38, hp: 50, maxHp: 50 });

    // 4. Initial Enemies exactly matching Concept Art:
    // - Z1-Z2: 2 Acid Spitters flanking center
    spawnEnemy("spitter", 175, 565);
    spawnEnemy("spitter", 365, 565);
    // - Z2-Z3: 2 Mutant Hounds flanking
    spawnEnemy("hound", 130, 420);
    spawnEnemy("hound", 410, 380);
    spawnEnemy("spitter", 310, 410);
    // - Z3-Z4: Giant Purple Mutant Brute
    spawnEnemy("brute", 280, 320);
    // - Z4-Z5: Goblin / Zombie Walkers
    spawnEnemy("walker", 150, 255);
    spawnEnemy("walker", 220, 250);
    spawnEnemy("walker", 390, 255);

    // 5. Initial EXP Gems on Field
    spawnExpGem(140, 650);
    spawnExpGem(370, 630);
    spawnExpGem(180, 460);
    spawnExpGem(390, 440);
    spawnExpGem(125, 310);
    spawnExpGem(435, 320);

    setupDragAndDrop();
    requestAnimationFrame(gameLoop);
}

function spawnEnemy(type, x, y) {
    const e = {
        type: type,
        x: x || Math.random() * (V_WIDTH - 140) + 70,
        y: y || Math.random() * 200 + 200,
        fireTimer: Math.random() * 60
    };

    if (type === "walker") {
        e.hp = 65; e.maxHp = 65; e.speed = 1.0; e.radius = 15; e.color = "#8bc34a"; e.name = "行尸";
    } else if (type === "spitter") {
        e.hp = 95; e.maxHp = 95; e.speed = 0.75; e.radius = 18; e.color = "#76ff03"; e.name = "毒液射手";
    } else if (type === "hound") {
        e.hp = 130; e.maxHp = 130; e.speed = 2.4; e.w = 34; e.h = 22; e.radius = 17; e.color = "#ffb300"; e.name = "变异猎犬";
    } else if (type === "brute") {
        e.hp = 480; e.maxHp = 480; e.speed = 0.55; e.radius = 32; e.color = "#ba68c8"; e.name = "狂暴蛮兽";
    }
    enemies.push(e);
}

function spawnExpGem(x, y) {
    expGems.push({ x: x, y: y, radius: 8 });
}

// ==========================================================================
// 2. DRAG AND DROP TACTICAL PLACEMENT
// ==========================================================================

function setupDragAndDrop() {
    const cards = document.querySelectorAll(".tactical-card");

    cards.forEach(card => {
        card.onmousedown = (e) => {
            const propType = card.dataset.prop;
            if (tacticalProps[propType].count <= 0) return;
            
            draggingProp = { type: propType };
            cards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            e.preventDefault();
        };
    });

    window.addEventListener("mousemove", (e) => {
        if (!draggingProp) return;
        const rect = canvas.getBoundingClientRect();
        const scaleX = V_WIDTH / rect.width;
        const scaleY = V_HEIGHT / rect.height;
        
        dragWorldPos.x = (e.clientX - rect.left) * scaleX;
        dragWorldPos.y = (e.clientY - rect.top) * scaleY;
        isHoveringBattlefield = (dragWorldPos.x >= 40 && dragWorldPos.x <= V_WIDTH - 40 && dragWorldPos.y >= 210 && dragWorldPos.y <= V_HEIGHT - 60);
    });

    window.addEventListener("mouseup", () => {
        if (draggingProp && isHoveringBattlefield) {
            const type = draggingProp.type;
            if (tacticalProps[type].count > 0) {
                tacticalProps[type].count--;
                updateTacticalUI();

                const pCfg = tacticalProps[type];
                placedProps.push({
                    type: type,
                    x: dragWorldPos.x,
                    y: dragWorldPos.y,
                    w: pCfg.w,
                    h: pCfg.h,
                    hp: pCfg.hp || 100,
                    maxHp: pCfg.hp || 100
                });

                shockwaves.push({ x: dragWorldPos.x, y: dragWorldPos.y, r: 10, maxR: 50, color: "#00f2fe" });
            }
        }
        draggingProp = null;
    });

    // 绑定 MEGA 百万量级弹幕模式开关
    const btnMega = document.getElementById("btn-mega-barrage");
    if (btnMega) {
        btnMega.onclick = () => {
            isMegaBarrage = !isMegaBarrage;
            btnMega.textContent = isMegaBarrage ? "⚡ MEGA: ON" : "⚡ MEGA: OFF";
            btnMega.classList.toggle("active", isMegaBarrage);
        };
    }

    document.querySelectorAll(".weapon-slot").forEach(slot => {
        slot.onclick = () => switchWeapon(parseInt(slot.dataset.slot));
    });
}

function updateTacticalUI() {
    document.getElementById("cnt-barrier").textContent = tacticalProps.barrier.count;
    document.getElementById("cnt-exp-barrel").textContent = tacticalProps.explosive_barrel.count;
    document.getElementById("cnt-toxic-barrel").textContent = tacticalProps.toxic_barrel.count;
    document.getElementById("cnt-land-mine").textContent = tacticalProps.land_mine.count;
    document.getElementById("cnt-healing").textContent = tacticalProps.healing_station.count;
}

function switchWeapon(slotId) {
    player.activeSlot = slotId;
    document.querySelectorAll(".weapon-slot").forEach(s => {
        s.classList.toggle("active", parseInt(s.dataset.slot) === slotId);
    });
}

// ==========================================================================
// 3. GAME LOOP & CORE SYSTEMS
// ==========================================================================

function gameLoop() {
    if (!isPaused) {
        update();
    }
    render();
    requestAnimationFrame(gameLoop);
}

function update() {
    // 1. Player Movement
    let dx = 0, dy = 0;
    if (keys["w"] || keys["arrowup"]) dy -= 1;
    if (keys["s"] || keys["arrowdown"]) dy += 1;
    if (keys["a"] || keys["arrowleft"]) dx -= 1;
    if (keys["d"] || keys["arrowright"]) dx += 1;

    if (dx !== 0 && dy !== 0) { dx *= 0.7071; dy *= 0.7071; }
    player.x = Math.max(player.radius + 30, Math.min(V_WIDTH - player.radius - 30, player.x + dx * player.speed));
    player.y = Math.max(V_HEIGHT / 2 + 40, Math.min(V_HEIGHT - player.radius - 80, player.y + dy * player.speed));

    // 2. Auto-Aim Weapon System
    let target = boss;
    let minDist = 9999;
    enemies.forEach(e => {
        const d = Math.hypot(e.x - player.x, e.y - player.y);
        if (d < minDist) {
            minDist = d;
            target = e;
        }
    });

    const angle = Math.atan2(target.y - player.y, target.x - player.x);
    player.aimX = target.x;
    player.aimY = target.y;

    const curWpn = weapons[player.activeSlot];
    player.fireTimer++;
    if (player.fireTimer >= curWpn.rate) {
        player.fireTimer = 0;
        fireWeapon(curWpn, angle);
    }

    // MEGA 弹幕架构：极坐标多臂阿基米德螺旋高并发弹幕发射
    if (isMegaBarrage) {
        megaSpiralAngle += 0.22;
        const ARMS = 8;
        for (let a = 0; a < ARMS; a++) {
            const baseRad = megaSpiralAngle + (a * Math.PI * 2 / ARMS);
            for (let layer = 0; layer < 2; layer++) {
                const spd = 7.0 + layer * 3.0;
                const rad = baseRad + layer * 0.08;
                bullets.push({
                    x: player.x,
                    y: player.y - 12,
                    vx: Math.cos(rad) * spd,
                    vy: Math.sin(rad) * spd,
                    angle: rad,
                    speed: spd,
                    damage: 6,
                    color: (a % 2 === 0) ? "#00f2fe" : "#ff2a8d",
                    isMega: true,
                    life: 0,
                    maxLife: 150
                });
            }
        }
    }

    // 3. 高性能逆向空间判定 (预提取敌人坐标与半径平方，彻底消除 Math.hypot)
    const activeTargets = [];
    if (boss.hp > 0) {
        activeTargets.push({ x: boss.x, y: boss.y, r2: (boss.radius + 14) * (boss.radius + 14), isBoss: true });
    }
    for (let i = 0; i < enemies.length; i++) {
        const e = enemies[i];
        activeTargets.push({ x: e.x, y: e.y, r2: (e.radius + 8) * (e.radius + 8), enemy: e });
    }

    // Update Bullets
    bullets = bullets.filter(b => {
        if (b.vx !== undefined) {
            b.x += b.vx;
            b.y += b.vy;
        } else {
            b.vx = Math.cos(b.angle) * b.speed;
            b.vy = Math.sin(b.angle) * b.speed;
            b.x += b.vx;
            b.y += b.vy;
        }

        // 逆向空间极速检测
        for (let t = 0; t < activeTargets.length; t++) {
            const tgt = activeTargets[t];
            const distSq = (b.x - tgt.x) * (b.x - tgt.x) + (b.y - tgt.y) * (b.y - tgt.y);
            if (distSq < tgt.r2) {
                if (tgt.isBoss) {
                    boss.hp = Math.max(0, boss.hp - b.damage);
                    if (!b.isMega) spawnParticles(b.x, b.y, "#ff2a8d", 4);
                    const ratio = Math.max(0, boss.hp / boss.maxHp);
                    const hpBar = document.getElementById("boss-hp-bar");
                    if (hpBar) hpBar.style.transform = `scaleX(${ratio})`;
                } else if (tgt.enemy) {
                    tgt.enemy.hp -= b.damage;
                    if (!b.isMega) spawnParticles(tgt.enemy.x, tgt.enemy.y, b.color, 3);
                }
                if (b.aoe) triggerExplosion(b.x, b.y, b.aoe, b.damage);
                b.dead = true;
                break;
            }
        }

        b.life = (b.life || 0) + 1;
        if (b.maxLife && b.life > b.maxLife) return false;

        return !b.dead && b.x >= -30 && b.x <= V_WIDTH + 30 && b.y >= -30 && b.y <= V_HEIGHT + 30;
    });

    // 4. Update Enemies
    enemies = enemies.filter(e => {
        const toPlayerAng = Math.atan2(player.y - e.y, player.x - e.x);
        e.x += Math.cos(toPlayerAng) * e.speed;
        e.y += Math.sin(toPlayerAng) * e.speed;

        if (e.type === "spitter") {
            e.fireTimer++;
            if (e.fireTimer >= 75) {
                e.fireTimer = 0;
                // Acid green beam
                bullets.push({
                    x: e.x, y: e.y, angle: toPlayerAng, speed: 6.5, damage: 15, color: "#76ff03", isEnemy: true, isAcidStream: true
                });
            }
        }

        if (e.hp <= 0) {
            killCount++;
            document.getElementById("kill-count").textContent = killCount;
            spawnParticles(e.x, e.y, e.color, 14);
            spawnExpGem(e.x, e.y);
            return false;
        }
        return true;
    });

    // 5. Update Props
    placedProps = placedProps.filter(p => {
        if (p.hp <= 0) {
            if (p.type === "explosive_barrel") {
                triggerExplosion(p.x, p.y, 130, 220);
            } else if (p.type === "toxic_barrel") {
                shockwaves.push({ x: p.x, y: p.y, r: 10, maxR: 110, color: "#00e676" });
            }
            return false;
        }
        if (p.type === "healing_station") {
            if (Math.hypot(player.x - p.x, player.y - p.y) < 100) {
                player.hp = Math.min(player.maxHp, player.hp + 0.35);
                updatePlayerHPUI();
            }
        }
        return true;
    });

    // 6. Update EXP Gems (Magnetize)
    expGems = expGems.filter(g => {
        const dist = Math.hypot(player.x - g.x, player.y - g.y);
        if (dist < 150) {
            const a = Math.atan2(player.y - g.y, player.x - g.x);
            g.x += Math.cos(a) * 9;
            g.y += Math.sin(a) * 9;
        }
        if (dist < 22) {
            gemCount += 10;
            player.exp += 10;
            if (player.exp >= player.maxExp) {
                player.exp = 0;
                player.lvl++;
                triggerLevelUp();
            }
            document.getElementById("gem-count").textContent = (gemCount / 1000).toFixed(2) + "K";
            document.getElementById("player-exp-fill").style.width = `${(player.exp / player.maxExp) * 100}%`;
            document.getElementById("player-lvl").textContent = player.lvl;
            return false;
        }
        return true;
    });

    // 7. Boss Shockwave
    boss.slamTimer++;
    if (boss.slamTimer >= 180) {
        boss.slamTimer = 0;
        shockwaves.push({ x: boss.x, y: boss.y + 35, r: 10, maxR: 260, color: "#ff2a8d" });
    }

    // 8. Wave Progression (Z1 -> Z5 -> Boss)
    if (killCount > 350 && currentZoneIndex < 5) {
        currentZoneIndex = Math.min(5, Math.floor((killCount - 340) / 8));
        currentZone = ZONES[currentZoneIndex];
        document.querySelectorAll(".zone-node").forEach(node => {
            node.classList.toggle("active", node.dataset.zone === currentZone);
        });
    }

    if (enemies.length < 10 && Math.random() < 0.04) {
        const types = ["walker", "spitter", "hound", "brute"];
        spawnEnemy(types[Math.floor(Math.random() * types.length)]);
    }
}

function fireWeapon(wpn, baseAngle) {
    for (let i = 0; i < wpn.pellets; i++) {
        const spreadOffset = (Math.random() - 0.5) * wpn.spread;
        bullets.push({
            x: player.x,
            y: player.y - 14,
            angle: baseAngle + spreadOffset,
            speed: wpn.speed,
            damage: wpn.damage,
            aoe: wpn.aoe,
            color: wpn.color
        });
    }
    spawnParticles(player.x, player.y - 16, wpn.color, 3);
}

function triggerExplosion(x, y, aoe, damage) {
    shockwaves.push({ x: x, y: y, r: 5, maxR: aoe, color: "#ff2a8d" });
    spawnParticles(x, y, "#ff9100", 25);
    enemies.forEach(e => {
        if (Math.hypot(e.x - x, e.y - y) < aoe) e.hp -= damage;
    });
}

function spawnParticles(x, y, color, count) {
    for (let i = 0; i < count; i++) {
        const ang = Math.random() * Math.PI * 2;
        const spd = Math.random() * 4 + 1;
        particles.push({
            x: x, y: y,
            vx: Math.cos(ang) * spd,
            vy: Math.sin(ang) * spd,
            color: color,
            alpha: 1.0
        });
    }
}

function updatePlayerHPUI() {
    document.getElementById("player-hp-curr").textContent = Math.round(player.hp);
    document.getElementById("player-hp-fill").style.width = `${(player.hp / player.maxHp) * 100}%`;
}

function triggerLevelUp() {
    isPaused = true;
    document.getElementById("upgrade-modal").style.display = "flex";
}

function selectUpgrade(id) {
    document.getElementById("upgrade-modal").style.display = "none";
    isPaused = false;
    if (id === 1) { player.maxHp += 250; player.hp += 250; updatePlayerHPUI(); }
    else if (id === 2) { weapons[1].damage += 10; weapons[2].damage += 6; }
    else if (id === 3) { weapons[1].pellets += 1; weapons[1].rate = 5; }
}

// ==========================================================================
// 4. RENDERING PIPELINE (1:1 Concept Art Scale & Detail)
// ==========================================================================

function render() {
    ctx.clearRect(0, 0, V_WIDTH, V_HEIGHT);

    // 1. Render Ground Map
    if (mapImg.complete && mapImg.naturalWidth > 0) {
        ctx.drawImage(mapImg, 0, 0, V_WIDTH, V_HEIGHT);
    } else {
        ctx.fillStyle = "#161b26";
        ctx.fillRect(0, 0, V_WIDTH, V_HEIGHT);
        ctx.strokeStyle = "rgba(255, 255, 255, 0.15)";
        ctx.lineWidth = 4;
        ctx.setLineDash([20, 20]);
        ctx.beginPath();
        ctx.moveTo(V_WIDTH / 2, 0);
        ctx.lineTo(V_WIDTH / 2, V_HEIGHT);
        ctx.stroke();
        ctx.setLineDash([]);
    }

    // 2. Render Placed Tactical Props
    placedProps.forEach(p => {
        ctx.save();
        if (p.type === "barrier") {
            ctx.fillStyle = p.isBossGate ? "#37474f" : "#455a64";
            ctx.strokeStyle = "#90a4ae";
            ctx.lineWidth = 2;
            ctx.fillRect(p.x - p.w / 2, p.y - p.h / 2, p.w, p.h);
            ctx.strokeRect(p.x - p.w / 2, p.y - p.h / 2, p.w, p.h);
            // Hazard Stripes
            ctx.fillStyle = "#ffb300";
            for (let sx = p.x - p.w / 2 + 10; sx < p.x + p.w / 2 - 10; sx += 20) {
                ctx.fillRect(sx, p.y - p.h / 2 + 4, 8, p.h - 8);
            }
        } else if (p.type === "explosive_barrel") {
            // High-detail Red Barrel
            ctx.fillStyle = "#d32f2f";
            ctx.strokeStyle = "#ff5252";
            ctx.lineWidth = 2;
            ctx.shadowColor = "#ff2a8d";
            ctx.shadowBlur = 12;
            ctx.beginPath();
            ctx.rect(p.x - p.w / 2, p.y - p.h / 2, p.w, p.h);
            ctx.fill();
            ctx.stroke();
            ctx.fillStyle = "#ffd700";
            ctx.font = "bold 14px sans-serif";
            ctx.fillText("☣", p.x - 6, p.y + 5);
        } else if (p.type === "toxic_barrel") {
            ctx.fillStyle = "#2e7d32";
            ctx.strokeStyle = "#00e676";
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.rect(p.x - p.w / 2, p.y - p.h / 2, p.w, p.h);
            ctx.fill();
            ctx.stroke();
            ctx.fillStyle = "#fff";
            ctx.font = "bold 12px sans-serif";
            ctx.fillText("☠", p.x - 5, p.y + 4);
        } else if (p.type === "land_mine") {
            ctx.fillStyle = "#e65100";
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.w / 2, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = "#ff1744";
            ctx.beginPath();
            ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
            ctx.fill();
        } else if (p.type === "healing_station") {
            ctx.fillStyle = "#00838f";
            ctx.strokeStyle = "#00f2fe";
            ctx.lineWidth = 2;
            ctx.fillRect(p.x - p.w / 2, p.y - p.h / 2, p.w, p.h);
            ctx.strokeRect(p.x - p.w / 2, p.y - p.h / 2, p.w, p.h);
            ctx.fillStyle = "#00e676";
            ctx.font = "bold 18px sans-serif";
            ctx.fillText("+", p.x - 5, p.y + 6);
        }
        ctx.restore();
    });

    // 3. Render EXP Gems (💎 Blue Diamonds with facets)
    expGems.forEach(g => {
        ctx.save();
        ctx.fillStyle = "#00f2fe";
        ctx.shadowColor = "#00f2fe";
        ctx.shadowBlur = 12;
        ctx.beginPath();
        ctx.moveTo(g.x, g.y - 10);
        ctx.lineTo(g.x + 8, g.y);
        ctx.lineTo(g.x, g.y + 10);
        ctx.lineTo(g.x - 8, g.y);
        ctx.closePath();
        ctx.fill();
        ctx.fillStyle = "#ffffff";
        ctx.font = "bold 7px sans-serif";
        ctx.fillText("EXP", g.x - 7, g.y + 3);
        ctx.restore();
    });

    // 4. Render Shockwaves
    shockwaves = shockwaves.filter(s => {
        s.r += 4;
        ctx.save();
        ctx.strokeStyle = s.color;
        ctx.lineWidth = 3;
        ctx.shadowColor = s.color;
        ctx.shadowBlur = 14;
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();
        return s.r < s.maxR;
    });

    // 5. Render Giant Boss Overlord (Top Center Scale)
    ctx.save();
    // Boss Ground Aura
    ctx.fillStyle = "rgba(255, 42, 141, 0.18)";
    ctx.beginPath();
    ctx.arc(boss.x, boss.y, boss.radius + 16, 0, Math.PI * 2);
    ctx.fill();
    // Boss Giant Body
    ctx.fillStyle = "#4e342e";
    ctx.strokeStyle = "#ff2a8d";
    ctx.lineWidth = 4;
    ctx.shadowColor = "#ff2a8d";
    ctx.shadowBlur = 24;
    ctx.beginPath();
    ctx.arc(boss.x, boss.y, boss.radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    // Boss Armor Spikes & Face
    ctx.fillStyle = "#fff";
    ctx.font = "48px sans-serif";
    ctx.fillText("👹", boss.x - 24, boss.y + 16);
    ctx.restore();

    // Realtime Floating Overhead Boss Health Bar Follow
    const bossHud = document.getElementById("boss-hud");
    if (bossHud) {
        if (boss.hp <= 0) {
            bossHud.style.opacity = "0";
            bossHud.style.pointerEvents = "none";
        } else {
            bossHud.style.opacity = "1";
            bossHud.style.left = `${(boss.x / V_WIDTH) * 100}%`;
            bossHud.style.top = `${((boss.y - boss.radius - 12) / V_HEIGHT) * 100}%`;
            const ratio = Math.max(0, boss.hp / boss.maxHp);
            const hpBar = document.getElementById("boss-hp-bar");
            if (hpBar) hpBar.style.transform = `scaleX(${ratio})`;
        }
    }

    // 6. Render Enemies
    enemies.forEach(e => {
        ctx.save();
        ctx.fillStyle = e.color;
        ctx.shadowColor = e.color;
        ctx.shadowBlur = 10;
        ctx.beginPath();
        ctx.arc(e.x, e.y, e.radius, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = "#fff";
        ctx.font = `${Math.round(e.radius * 1.15)}px sans-serif`;
        const icon = e.type === "hound" ? "🐕" : (e.type === "spitter" ? "🐍" : (e.type === "brute" ? "👿" : "🧟"));
        ctx.fillText(icon, e.x - e.radius / 2, e.y + e.radius / 3);
        ctx.restore();
    });

    // 7. Render Player & Glowing Tactical Foot Ring
    ctx.save();
    // Glowing Blue Tactical Foot Ring (Concept Art Exact Proportion)
    ctx.strokeStyle = "#00f2fe";
    ctx.lineWidth = 3;
    ctx.shadowColor = "#00f2fe";
    ctx.shadowBlur = 20;
    ctx.beginPath();
    ctx.arc(player.x, player.y, player.tacticalRingRadius, 0, Math.PI * 2);
    ctx.stroke();

    // Player Character Body
    ctx.fillStyle = "#1976d2";
    ctx.beginPath();
    ctx.arc(player.x, player.y, player.radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#fff";
    ctx.font = "22px sans-serif";
    ctx.fillText("👨‍⚕️", player.x - 11, player.y + 8);
    ctx.restore();

    // 8. 高性能 Instanced 级批处理渲染子弹 (按颜色合批，消除上万次上下文切换)
    // 更新性能与子弹计数指示器
    frameCount++;
    const now = performance.now();
    if (now - lastFpsTime >= 200) {
        currentFps = Math.round((frameCount * 1000) / (now - lastFpsTime));
        frameCount = 0;
        lastFpsTime = now;
        const fpsEl = document.getElementById("fps-display");
        if (fpsEl) {
            fpsEl.textContent = `${currentFps} FPS`;
            fpsEl.style.color = currentFps >= 50 ? "#00ff88" : (currentFps >= 30 ? "#ffd700" : "#ff2a8d");
        }
        const bCountEl = document.getElementById("bullet-count");
        if (bCountEl) bCountEl.textContent = bullets.length.toLocaleString();
    }

    // 分流批次
    const batchCyan = [];
    const batchPink = [];
    const batchYellow = [];
    const batchOrange = [];
    const acidBeams = [];

    for (let i = 0; i < bullets.length; i++) {
        const b = bullets[i];
        if (b.isAcidStream) {
            acidBeams.push(b);
        } else if (b.color === "#00f2fe") {
            batchCyan.push(b);
        } else if (b.color === "#ff2a8d") {
            batchPink.push(b);
        } else if (b.color === "#ff9100") {
            batchOrange.push(b);
        } else {
            batchYellow.push(b);
        }
    }

    // (1) 绘制青色批次
    if (batchCyan.length > 0) {
        ctx.save();
        ctx.fillStyle = "#00f2fe";
        ctx.shadowColor = "#00f2fe";
        ctx.shadowBlur = 8;
        ctx.beginPath();
        for (let i = 0; i < batchCyan.length; i++) {
            const b = batchCyan[i];
            ctx.moveTo(b.x + 3.5, b.y);
            ctx.arc(b.x, b.y, 3.5, 0, Math.PI * 2);
        }
        ctx.fill();
        ctx.restore();
    }

    // (2) 绘制粉色批次
    if (batchPink.length > 0) {
        ctx.save();
        ctx.fillStyle = "#ff2a8d";
        ctx.shadowColor = "#ff2a8d";
        ctx.shadowBlur = 8;
        ctx.beginPath();
        for (let i = 0; i < batchPink.length; i++) {
            const b = batchPink[i];
            ctx.moveTo(b.x + 4, b.y);
            ctx.arc(b.x, b.y, b.aoe ? 7 : 4, 0, Math.PI * 2);
        }
        ctx.fill();
        ctx.restore();
    }

    // (3) 绘制金黄/橙色批次
    const standardBullets = batchYellow.concat(batchOrange);
    if (standardBullets.length > 0) {
        ctx.save();
        ctx.fillStyle = "#ffd700";
        ctx.shadowColor = "#ff9100";
        ctx.shadowBlur = 8;
        ctx.beginPath();
        for (let i = 0; i < standardBullets.length; i++) {
            const b = standardBullets[i];
            ctx.moveTo(b.x + 4, b.y);
            ctx.arc(b.x, b.y, 4, 0, Math.PI * 2);
        }
        ctx.fill();
        ctx.restore();
    }

    // (4) 绘制酸液光束
    if (acidBeams.length > 0) {
        ctx.save();
        ctx.strokeStyle = "#76ff03";
        ctx.lineWidth = 4;
        ctx.shadowColor = "#76ff03";
        ctx.shadowBlur = 12;
        ctx.beginPath();
        for (let i = 0; i < acidBeams.length; i++) {
            const b = acidBeams[i];
            ctx.moveTo(b.x, b.y);
            ctx.lineTo(b.x - Math.cos(b.angle) * 35, b.y - Math.sin(b.angle) * 35);
        }
        ctx.stroke();
        ctx.restore();
    }

    // 9. Render Particles
    particles = particles.filter(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.alpha -= 0.04;
        ctx.save();
        ctx.fillStyle = p.color;
        ctx.globalAlpha = Math.max(0, p.alpha);
        ctx.fillRect(p.x, p.y, 3.5, 3.5);
        ctx.restore();
        return p.alpha > 0;
    });

    // 10. Render Drag & Drop Hologram Placement (Concept Art 100% Match!)
    if (draggingProp && isHoveringBattlefield) {
        ctx.save();
        // Dotted blue trajectory spline connecting sidebar card to placement position
        ctx.strokeStyle = "#00f2fe";
        ctx.lineWidth = 2.5;
        ctx.setLineDash([6, 6]);
        ctx.beginPath();
        ctx.moveTo(V_WIDTH - 40, 260);
        ctx.quadraticCurveTo(V_WIDTH - 90, (260 + dragWorldPos.y) / 2, dragWorldPos.x, dragWorldPos.y);
        ctx.stroke();
        ctx.setLineDash([]);

        // Holographic Ghost Ring (Cyan glowing grid)
        ctx.strokeStyle = "#00f2fe";
        ctx.fillStyle = "rgba(0, 242, 254, 0.22)";
        ctx.lineWidth = 3;
        ctx.shadowColor = "#00f2fe";
        ctx.shadowBlur = 24;
        ctx.beginPath();
        ctx.arc(dragWorldPos.x, dragWorldPos.y, 38, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();

        // Inner target crosshair & grid
        ctx.strokeStyle = "rgba(0, 242, 254, 0.7)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(dragWorldPos.x, dragWorldPos.y, 22, 0, Math.PI * 2);
        ctx.moveTo(dragWorldPos.x - 38, dragWorldPos.y);
        ctx.lineTo(dragWorldPos.x + 38, dragWorldPos.y);
        ctx.moveTo(dragWorldPos.x, dragWorldPos.y - 38);
        ctx.lineTo(dragWorldPos.x, dragWorldPos.y + 38);
        ctx.stroke();

        ctx.restore();
    }
}

// Start
initStage00();
