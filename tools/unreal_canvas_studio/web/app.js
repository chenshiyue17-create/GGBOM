/**
 * 《GGBOM: 终末医疗兵》全实体与蓝图配置工作台核心交互系统
 * - 主角全属性、多动作状态、方向罗盘与特效叠加实时放映
 * - 敌人蓝图 CDO 属性检查器与 4 帧轻量怪放映室
 * - DT_Enemies 全量数据表格 (DataTable Grid) 批量修改
 * - 军备武库与卡牌系统联动
 * - 变更 Diff 审计、直接原子保存与 UE5 热同步
 */

let state = {
  original: null,
  current: null,
  blueprintSchema: [],
  availableFlipbooks: [],
  playerAnimations: {},
  vfxCatalog: [],
  
  // 主角交互状态
  selectedPlayerId: "Player_Medic",
  playerAction: "Idle",
  playerDirection: "Dir_01_Down",
  playerFPS: 5.0,
  playerAnimInterval: null,
  playerFrameIdx: 0,
  vfxInterval: null,
  vfxFrameIdx: 0,

  // 敌人交互状态
  selectedEnemyId: "Enemy_Zombie_Walker",
  enemyAnimInterval: null,
  enemyFrameIdx: 0,
  enemyFPS: 4.0,
  enemySearchFilter: "",

  // 土地地块交互状态
  selectedTileId: "Tile_Stage01_Z1",

  // 战斗特效交互状态 (DT_HitEffects)
  selectedEffectId: "FX_Hit_Sparks",
  effectFPS: 12.0,
  effectScale: 0.45,
  effectAnimInterval: null,
  effectFrameIdx: 0,
  effectFrames: [],
  effectIsHitStopping: false
};

document.addEventListener("DOMContentLoaded", () => {
  // 核心安全防线：全局阻断浏览器默认的文件拖放打开/跳转行为，杜绝任何外部拖入图片时浏览器跳转为网页预览！
  ["dragenter", "dragover", "dragleave", "drop"].forEach(name => {
    window.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
    }, false);
    document.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
    }, false);
  });

  initTabs();
  loadAllData();
  setupEventListeners();
  initPipelineStudioDragAndDrop();
  initHudStudioDragAndDrop();
});

function initTabs() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(btn => {
    btn.addEventListener("click", () => {
      navItems.forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
      
      btn.classList.add("active");
      const tabId = btn.getAttribute("data-tab");
      const pane = document.getElementById(tabId);
      if (pane) pane.classList.add("active");

      if (tabId === "tab-weapons") {
        renderWeaponsGrid();
      } else if (tabId === "tab-effects") {
        renderEffectsStudio();
      } else if (tabId === "tab-tiles") {
        renderTilesStudio();
      } else if (tabId === "tab-datatable") {
        renderDataTable();
      } else if (tabId === "tab-commits") {
        loadCommits();
      }
    });
  });
}

async function loadAllData() {
  try {
    const res = await fetch("/api/data");
    const data = await res.json();
    if (data.status === "success") {
      state.original = JSON.parse(JSON.stringify(data));
      state.current = JSON.parse(JSON.stringify(data));
      state.blueprintSchema = data.blueprint_schema || [];
      state.availableFlipbooks = data.available_flipbooks || [];
      state.playerAnimations = data.player_animations || {};
      state.vfxCatalog = data.vfx_catalog || [];

      renderAllViews();
      showToast("🎮 全实体数据、动作与特效资产已就绪！");
    }
  } catch (err) {
    console.error("加载数据失败:", err);
    showToast("⚠️ 加载后端数据失败，请检查服务", 4000);
  }
}

function renderAllViews() {
  renderPlayerStudio();
  renderEnemyList();
  renderEnemyDetail();
  renderTilesStudio();
  renderEffectsStudio();
  renderDataTable();
  renderWeaponsGrid();
  renderCardsGrid();
  renderWaveTimeline();
  updateDiffState();
}

// ==============================================================================
// 1. 主角全属性与多方向动作/特效工作台 (Player Studio)
// ==============================================================================
function renderPlayerStudio() {
  const charData = state.current.characters ? state.current.characters[state.selectedPlayerId] : null;
  if (!charData) return;

  // 1. 顶部基础信息与角色选择下拉框
  document.getElementById("playerStageName").textContent = `${charData.DisplayName} (${state.selectedPlayerId})`;
  document.getElementById("playerStageMeta").textContent = `${state.playerAction} | ${state.playerDirection}`;

  const playerSelect = document.getElementById("playerSelectDropdown");
  if (playerSelect) {
    const chars = state.current.characters || {};
    playerSelect.innerHTML = Object.entries(chars).map(([cid, c]) => `
      <option value="${cid}" ${cid === state.selectedPlayerId ? "selected" : ""}>${c.DisplayName || cid} (${cid})</option>
    `).join("");
  }
  
  const avatarImg = document.getElementById("playerAvatarImg");
  if (charData.Avatar) {
    avatarImg.src = `/art/${charData.Avatar}`;
  }

  // 渲染新探测到的候选头像立绘快捷切换栏
  renderCandidateAvatars(charData);

  // 2. 启动动作与方向动画
  startPlayerAnimation();

  // 3. 渲染主角全能属性 Details 面板
  renderPlayerPropertyTree(charData);

  // 4. 渲染全动作与全朝向资产槽位矩阵
  renderActionSlotsMatrix();
}

function renderCandidateAvatars(charData) {
  const wrap = document.getElementById("candidateAvatarsWrap");
  if (!wrap) return;
  wrap.innerHTML = "";

  const candidates = charData.CandidateAvatars || (state.current.candidate_avatars || []);
  if (!candidates || candidates.length === 0) return;

  const select = document.createElement("select");
  select.style.background = "rgba(15,23,42,0.85)";
  select.style.color = "#38bdf8";
  select.style.border = "1px solid rgba(56,189,248,0.5)";
  select.style.borderRadius = "4px";
  select.style.fontSize = "11px";
  select.style.padding = "2px 8px";
  select.style.cursor = "pointer";
  select.title = "系统自动探测到的 01_Player 下所有图片（包括用户拖入的头像立绘）";
  
  select.innerHTML = `
    <option value="" disabled selected>🖼️ 选用新发现头像 (${candidates.length}个发现)</option>
    ${candidates.map(c => `<option value="${c.path}" ${c.path === charData.Avatar ? "selected" : ""}>${c.is_priority ? "★ " : ""}${c.name} (${c.folder})</option>`).join("")}
  `;

  select.onchange = (e) => {
    const chosen = e.target.value;
    if (!chosen) return;
    charData.Avatar = chosen;
    document.getElementById("playerAvatarImg").src = `/art/${chosen}`;
    renderPlayerPropertyTree(charData);
    updateDiffState();
    showToast(`👁️ 已选用头像: ${chosen}（草稿预览中，点击保存后生效）`);
  };

  wrap.appendChild(select);
}

function switchPlayerCharacter(cid) {
  state.selectedPlayerId = cid;
  renderPlayerStudio();
}

function switchPlayerAction(action) {
  state.playerAction = action;
  document.querySelectorAll(".btn-action").forEach(b => {
    if (b.getAttribute("data-action") === action) b.classList.add("active");
    else b.classList.remove("active");
  });

  const actionLabels = {
    "Idle": "待机中 (IDLE)",
    "Run": "移动疾跑 (RUN)",
    "Attack": "普通攻击/射击 (ATTACK)",
    "Hurt": "受击震动 (HURT)",
    "Skill": "战术技能 (SKILL)",
    "Death": "战死倒地 (DEATH)"
  };
  document.getElementById("playerActionBadge").textContent = actionLabels[action] || action;
  document.getElementById("playerStageMeta").textContent = `${state.playerAction} | ${state.playerDirection}`;
  
  startPlayerAnimation();
}

function switchPlayerDirection(dirKey) {
  state.playerDirection = dirKey;
  document.querySelectorAll(".btn-dir").forEach(b => {
    if (b.getAttribute("data-dir") === dirKey) b.classList.add("active");
    else b.classList.remove("active");
  });

  const dirLabels = {
    "Dir_01_Down": "正下 (Dir_01_Down)",
    "Dir_02_DownLeft": "左下 (Dir_02_DownLeft)",
    "Dir_03_Left": "正侧 (Dir_03_Left)",
    "Dir_04_UpLeft": "左上 (Dir_04_UpLeft)",
    "Dir_05_Up": "正上 (Dir_05_Up)"
  };
  document.getElementById("playerDirIndicator").textContent = `朝向: ${dirLabels[dirKey] || dirKey}`;
  document.getElementById("playerStageMeta").textContent = `${state.playerAction} | ${state.playerDirection}`;
  
  startPlayerAnimation();
}

function startPlayerAnimation() {
  if (state.playerAnimInterval) {
    clearInterval(state.playerAnimInterval);
    state.playerAnimInterval = null;
  }
  state.playerFrameIdx = 0;

  const charData = state.current.characters ? state.current.characters[state.selectedPlayerId] : null;
  let frames = [];
  let currentPath = "";
  let isFlip = false;

  // 1. 优先读取 charData.Animations 中的自定义配置
  if (charData && charData.Animations && charData.Animations[state.playerAction]) {
    const actMap = charData.Animations[state.playerAction];
    const slot = actMap[state.playerDirection] || actMap["Default"];
    if (slot) {
      currentPath = slot.path || "";
      isFlip = !!slot.flipX;
      if (slot.customFrames && slot.customFrames.length > 0) {
        frames = [...slot.customFrames];
      }
    }
  }

  // 2. 若无自定义切片，读取 playerAnimations 缓存
  if (frames.length === 0) {
    const actData = state.playerAnimations[state.playerAction] || {};
    let dirInfo = actData[state.playerDirection];
    if (!dirInfo) {
      const availableDirs = Object.keys(actData);
      if (availableDirs.length > 0) {
        dirInfo = actData[availableDirs[0]];
      }
    }
    if (dirInfo) {
      frames = dirInfo.frames ? [...dirInfo.frames] : [];
      if (!currentPath) currentPath = dirInfo.path || "";
    }
  }

  const imgEl = document.getElementById("playerSpriteImg");
  const indicatorEl = document.getElementById("playerFrameIndicator");
  const slicesBox = document.getElementById("playerFrameSlices");
  const slotPathEl = document.getElementById("currentSlotPath");

  if (slotPathEl) {
    slotPathEl.textContent = currentPath || "未绑定本地素材";
  }

  // 镜像翻转控制
  if (isFlip) {
    imgEl.style.transform = "scaleX(-1)";
  } else {
    imgEl.style.transform = "scaleX(1)";
  }

  slicesBox.innerHTML = "";
  if (!frames || frames.length === 0) {
    imgEl.src = "";
    indicatorEl.textContent = "无切片帧";
    return;
  }

  // 渲染切片条（支持点击单张单独替换）
  frames.forEach((f, idx) => {
    const b = document.createElement("div");
    b.className = `frame-slice-box ${idx === 0 ? "current" : ""}`;
    b.id = `pSlice_${idx}`;
    b.title = "点击从素材库替换此帧贴图";
    b.innerHTML = `<img src="/art/${f}" alt="F${idx+1}" /><span class="label">F${idx+1}</span>`;
    b.onclick = () => {
      openAssetBrowser({
        title: `替换【${state.playerAction}-${state.playerDirection}】第 ${idx+1} 帧切片`,
        currentVal: f,
        filterDir: currentPath,
        mode: "file",
        onSelect: (newF) => {
          frames[idx] = newF;
          if (charData) {
            if (!charData.Animations) charData.Animations = {};
            if (!charData.Animations[state.playerAction]) charData.Animations[state.playerAction] = {};
            if (!charData.Animations[state.playerAction][state.playerDirection]) {
              charData.Animations[state.playerAction][state.playerDirection] = { path: currentPath, fps: state.playerFPS, customFrames: [...frames] };
            } else {
              charData.Animations[state.playerAction][state.playerDirection].customFrames = [...frames];
            }
          }
          startPlayerAnimation();
          renderActionSlotsMatrix();
          updateDiffState();
          showToast(`✅ 已更换第 ${idx+1} 帧`);
        }
      });
    };
    slicesBox.appendChild(b);
  });

  state.playerFrameIdx = 0;
  const step = () => {
    if (!frames || frames.length === 0) return;
    imgEl.src = `/art/${frames[state.playerFrameIdx]}`;
    indicatorEl.textContent = `FRAME: ${state.playerFrameIdx + 1}/${frames.length}`;

    document.querySelectorAll("#playerFrameSlices .frame-slice-box").forEach((b, i) => {
      if (i === state.playerFrameIdx) b.classList.add("current");
      else b.classList.remove("current");
    });

    state.playerFrameIdx = (state.playerFrameIdx + 1) % frames.length;
  };

  step();
  const ms = Math.max(40, 1000 / (state.playerFPS || 5.0));
  state.playerAnimInterval = setInterval(step, ms);
}

// 1.1 从素材库挑选更换角色头像 (Avatar)
function openAssetPickerForAvatar() {
  const charData = state.current.characters[state.selectedPlayerId];
  openAssetBrowser({
    title: `为【${charData.DisplayName}】挑选头像贴图 (Avatar)`,
    currentVal: charData.Avatar || "",
    filterDir: "01_Player",
    mode: "file",
    onSelect: (selectedPath) => {
      charData.Avatar = selectedPath;
      document.getElementById("playerAvatarImg").src = `/art/${selectedPath}`;
      renderPlayerPropertyTree(charData);
      updateDiffState();
      showToast("👁️ 角色头像已切换（仅本地预览，点击右上角【保存修改】后生效）");
    }
  });
}

// 1.2 从素材库为当前动作与方向挑选替换素材 (整套序列或单帧)
function openAssetPickerForCurrentAction(type = 'folder') {
  const charData = state.current.characters[state.selectedPlayerId];
  if (!charData.Animations) charData.Animations = {};
  if (!charData.Animations[state.playerAction]) charData.Animations[state.playerAction] = {};

  const currentSlot = charData.Animations[state.playerAction][state.playerDirection] || {};
  let currentPath = currentSlot.path || "";
  if (!currentPath) {
    if (state.playerAction === "Attack" || state.playerAction === "Hurt") {
      currentPath = `01_Player/02_Attack_Hurt/${state.playerDirection}/${state.playerAction}`;
    } else if (state.playerAction === "Death") {
      currentPath = `01_Player/03_Death_Revive/Death_Collapse`;
    } else {
      currentPath = `01_Player/01_Idle_Run/${state.playerDirection}/${state.playerAction}`;
    }
  }

  if (type === 'folder') {
    openAssetBrowser({
      title: `为【${state.playerAction} - ${state.playerDirection}】挑选动作切片目录`,
      currentVal: currentPath,
      filterDir: currentPath,
      mode: "folder",
      onSelect: async (selectedDirOrFile) => {
        let dirPath = selectedDirOrFile;
        if (selectedDirOrFile.endsWith(".png") || selectedDirOrFile.endsWith(".jpg")) {
          dirPath = selectedDirOrFile.substring(0, selectedDirOrFile.lastIndexOf("/"));
        }

        try {
          const res = await fetch(`/api/dir-frames?dir=${encodeURIComponent(dirPath)}&action=${encodeURIComponent(state.playerAction)}`);
          const d = await res.json();
          const frames = d.frames || [];
          const actualDir = d.dir || dirPath;

          if (frames.length === 0) {
            showToast("⚠️ 该目录未找到有效 PNG 序列帧，请选择具体包含帧切片的子目录！");
            return;
          }

          // 1. 更新当前角色数据结构中的动作方向槽位
          charData.Animations[state.playerAction][state.playerDirection] = {
            path: actualDir,
            fps: state.playerFPS,
            customFrames: [...frames]
          };

          // 2. 同步更新放映台内存缓存，保证即时播放
          if (!state.playerAnimations[state.playerAction]) state.playerAnimations[state.playerAction] = {};
          state.playerAnimations[state.playerAction][state.playerDirection] = {
            path: actualDir,
            frames: [...frames]
          };

          // 3. 强制重置帧索引并停止旧定时器
          state.playerFrameIdx = 0;
          if (state.playerAnimInterval) {
            clearInterval(state.playerAnimInterval);
            state.playerAnimInterval = null;
          }

          document.getElementById("currentSlotPath").textContent = actualDir;
          startPlayerAnimation();
          renderActionSlotsMatrix();
          updateDiffState();
          showToast(`👁️ 动作序列已更新 (${frames.length} 帧)！当前为调试预览草稿，点击右上角【保存修改】后生效`);
        } catch (err) {
          console.error(err);
          showToast("⚠️ 获取序列帧失败");
        }
      }
    });
  } else {
    // 选单帧追加
    openAssetBrowser({
      title: `为【${state.playerAction} - ${state.playerDirection}】挑选单张切片`,
      currentVal: currentPath,
      filterDir: currentPath,
      mode: "file",
      onSelect: (filePath) => {
        const slot = charData.Animations[state.playerAction][state.playerDirection] || { path: currentPath, fps: state.playerFPS, customFrames: [] };
        if (!slot.customFrames || slot.customFrames.length === 0) {
          const actData = state.playerAnimations[state.playerAction] || {};
          const dirInfo = actData[state.playerDirection];
          slot.customFrames = dirInfo ? [...dirInfo.frames] : [];
        }
        slot.customFrames.push(filePath);
        charData.Animations[state.playerAction][state.playerDirection] = slot;

        startPlayerAnimation();
        renderActionSlotsMatrix();
        updateDiffState();
        showToast("👁️ 已追加切片帧（仅视口预览，点击右上角【保存修改】后生效）");
      }
    });
  }
}

// 1.3 恢复当前动作方向切片为默认
function resetCurrentActionToDefault() {
  const charData = state.current.characters[state.selectedPlayerId];
  if (charData && charData.Animations && charData.Animations[state.playerAction]) {
    delete charData.Animations[state.playerAction][state.playerDirection];
  }
  startPlayerAnimation();
  renderActionSlotsMatrix();
  updateDiffState();
  showToast("👁️ 动作槽位已恢复默认切片（草稿状态，点击右上角【保存修改】后生效）");
}

// 1.4 全动作全朝向资产槽位总览矩阵
function renderActionSlotsMatrix() {
  const container = document.getElementById("actionSlotsMatrixContainer");
  if (!container) return;
  const charData = state.current.characters ? state.current.characters[state.selectedPlayerId] : null;
  if (!charData) return;

  const actions = ["Idle", "Run", "Attack", "Hurt", "Skill", "Death"];
  const dirs = [
    { key: "Dir_01_Down", label: "↓ 正下" },
    { key: "Dir_02_DownLeft", label: "↙ 左下" },
    { key: "Dir_03_Left", label: "← 正侧" },
    { key: "Dir_04_UpLeft", label: "↖ 左上" },
    { key: "Dir_05_Up", label: "↑ 正上" }
  ];

  let html = `<table class="action-matrix-table"><thead><tr><th>动作状态</th>`;
  dirs.forEach(d => {
    html += `<th>${d.label}</th>`;
  });
  html += `</tr></thead><tbody>`;

  actions.forEach(act => {
    html += `<tr><td><strong>${act}</strong></td>`;
    dirs.forEach(d => {
      let slotPath = "";
      let isCustom = false;
      if (charData.Animations && charData.Animations[act] && charData.Animations[act][d.key]) {
        slotPath = charData.Animations[act][d.key].path || "";
        isCustom = true;
      } else if (state.playerAnimations[act] && state.playerAnimations[act][d.key]) {
        slotPath = state.playerAnimations[act][d.key].path || "";
      } else if (charData.Animations && charData.Animations[act] && charData.Animations[act]["Default"]) {
        slotPath = charData.Animations[act]["Default"].path || "";
      }

      const shortName = slotPath ? slotPath.split("/").slice(-2).join("/") : "未绑定";
      html += `<td>
        <span class="matrix-slot-tag" title="点击从素材库替换: ${slotPath}" onclick="selectMatrixSlotAndPick('${act}', '${d.key}')">
          ${isCustom ? '⭐ ' : ''}${shortName}
        </span>
      </td>`;
    });
    html += `</tr>`;
  });

  html += `</tbody></table>`;
  container.innerHTML = html;
}

function selectMatrixSlotAndPick(act, dirKey) {
  state.playerAction = act;
  state.playerDirection = dirKey;
  switchPlayerAction(act);
  switchPlayerDirection(dirKey);
  openAssetPickerForCurrentAction('folder');
}

// 模拟播放特效 (VFX Overlay)
function triggerTestVFX(vfxType) {
  const charData = state.current.characters[state.selectedPlayerId];
  const vfxPath = (charData.VFX && charData.VFX[vfxType]) ? charData.VFX[vfxType] : "05_VFX/09_Nanite_Heal";
  const matchedVfx = state.vfxCatalog.find(v => v.path === vfxPath || v.id === vfxPath.split('/').pop());

  const overlayImg = document.getElementById("vfxOverlayImg");
  const vfxBadge = document.getElementById("vfxActiveIndicator");

  if (!matchedVfx || !matchedVfx.frames || matchedVfx.frames.length === 0) {
    showToast(`⚠️ 未找到特效切片: ${vfxPath}`);
    return;
  }

  if (state.vfxInterval) clearInterval(state.vfxInterval);
  overlayImg.style.display = "block";
  vfxBadge.style.display = "inline-block";
  vfxBadge.textContent = `特效: ${matchedVfx.name}`;

  let vIdx = 0;
  const vFrames = matchedVfx.frames;
  state.vfxInterval = setInterval(() => {
    overlayImg.src = `/art/${vFrames[vIdx]}`;
    vIdx++;
    if (vIdx >= vFrames.length) {
      clearInterval(state.vfxInterval);
      setTimeout(() => {
        overlayImg.style.display = "none";
        vfxBadge.style.display = "none";
      }, 200);
    }
  }, 100);
}

// ==============================================================================
// 特效与武器元数据映射与富可视化辅助系统 (Visual Asset Meta & Helpers)
// ==============================================================================
const VFX_CHINESE_MAP = {
  "01_Explosion_Fire": "高爆烈焰解体爆裂",
  "02_Inferno_Shock": "炼狱冲击波",
  "03_Spark_Flare": "火花耀斑",
  "04_Blood_Gore": "变异血肉飞溅",
  "05_Smoke_Dust": "烟尘弥漫",
  "06_Toxic_Splatter": "毒液喷溅",
  "07_Acid_Cloud": "酸蚀持续毒雾",
  "09_Nanite_Heal": "纳米急救光环",
  "10_Plasma_Shield": "等离子防护屏障",
  "11_Hit_Kinetic": "金属动能跳弹火花",
  "12_Hit_Acid": "腐蚀强酸飞溅",
  "13_Muzzle_Flash": "突击步枪枪口火光",
  "14_Spark_Tiny": "微弱火花",
  "15_Freeze_Crack": "极寒冰霜碎裂",
  "16_EMP_Pulse": "等离子电弧脉冲",
  "17_Dash_Ghost": "疾行战术冲刺残影",
  "18_LevelUp_Beam": "升级强化光束"
};

function getVfxMeta(pathOrId) {
  if (!pathOrId) {
    return { name: "未配置特效", folder: "无", frames: [], firstFrame: "", frameCount: 0 };
  }
  const clean = pathOrId.replace(/^05_VFX\//, "").replace(/\/$/, "");
  const matchedCat = (state.vfxCatalog || []).find(v => v.path === pathOrId || v.id === clean || v.path.endsWith(clean));
  
  let frames = matchedCat ? matchedCat.frames : [];
  let name = VFX_CHINESE_MAP[clean] || (matchedCat ? matchedCat.name : clean);
  let firstFrame = frames.length > 0 ? `/art/${frames[0]}` : "";

  return {
    name,
    folder: pathOrId,
    id: clean,
    frames,
    firstFrame,
    frameCount: frames.length
  };
}

function getWeaponMeta(weaponId) {
  const defaultRes = {
    id: weaponId || "无",
    name: weaponId || "未指定武器",
    icon: "",
    damage: 0,
    fireRate: 0,
    bulletSpeed: 0
  };
  if (!weaponId || !state.current || !state.current.weapons) return defaultRes;
  const w = state.current.weapons[weaponId];
  if (!w) return defaultRes;

  let icon = "";
  if (w.ArtInfo) {
    if (w.ArtInfo.bullet) icon = `/art/${w.ArtInfo.bullet}`;
    else if (w.ArtInfo.muzzle) icon = `/art/${w.ArtInfo.muzzle}`;
    else if (w.ArtInfo.sheet) icon = `/art/${w.ArtInfo.sheet}`;
  }

  return {
    id: weaponId,
    name: w.DisplayName || weaponId,
    icon: icon,
    damage: w.BaseDamage || 10,
    fireRate: w.FireRate || 1,
    bulletSpeed: w.BulletSpeed || 1000
  };
}

/**
 * 全生命周期外部素材直接拖入摄取、自动备份与解耦引擎 (Universal Drag & Drop Ingestion)
 * 核心功能：
 * 1. 允许从操作系统外部（桌面、Finder、下载等任何文件夹）直接拖拽图片文件进入槽位；
 * 2. 自动在工程 Content/美术/Art/.source_backup/{category}/ 下建立带时间戳和指纹的生肉原图备份，永不怕素材丢失；
 * 3. 自动存入工程规范的内部相对路径并输出 UE 资产引用路径，完全解耦原始路径与素材依赖；
 * 4. 摄取成功后即时触发回调并刷新界面所有缩略图与动效。
 */
function setupUniversalImageDrop(element, config = {}) {
  if (!element) return;

  const {
    category = "general",
    entityId = "",
    targetDir = null,
    autoRemoveBlack = false,
    autoTrim = false,
    label = "素材",
    onSuccess = null
  } = config;

  ["dragenter", "dragover", "dragleave", "drop"].forEach(name => {
    element.addEventListener(name, (e) => {
      e.preventDefault();
      e.stopPropagation();
    }, false);
  });

  ["dragenter", "dragover"].forEach(name => {
    element.addEventListener(name, () => {
      element.classList.add("universal-drop-target-active");
    }, false);
  });

  ["dragleave", "drop"].forEach(name => {
    element.addEventListener(name, () => {
      element.classList.remove("universal-drop-target-active");
    }, false);
  });

  element.addEventListener("drop", async (e) => {
    const dt = e.dataTransfer;
    if (!dt || !dt.files || dt.files.length === 0) return;

    const file = dt.files[0];
    const isImage = file.type.startsWith("image/") || /\.(png|jpg|jpeg|webp|tga|bmp)$/i.test(file.name);
    if (!isImage) {
      showToast(`⚠️ [${file.name}] 不是支持的图像文件格式 (PNG/JPG/WEBP/TGA)`);
      return;
    }

    const catVal = typeof category === "function" ? category() : category;
    const entVal = typeof entityId === "function" ? entityId() : entityId;
    const tgtDir = typeof targetDir === "function" ? targetDir() : targetDir;

    showToast(`📥 正在摄取 [${file.name}] 并创建安全备份...`);

    const reader = new FileReader();
    reader.onload = async (event) => {
      const base64Data = event.target.result;
      try {
        const payload = {
          file_base64: base64Data,
          filename: file.name,
          category: catVal,
          entity_id: entVal,
          target_dir: tgtDir,
          auto_remove_black: autoRemoveBlack,
          auto_trim: autoTrim
        };

        const res = await fetch("/api/asset/ingest", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await res.json();

        if (data.status === "success") {
          showToast(`🎉 [${label}] 已安全归档入项目内部！\n📁 相对路径: ${data.project_rel_path}\n🛡️ 原图备份: ${data.backup_rel_path}`);
          if (typeof onSuccess === "function") {
            await onSuccess(data);
          }
          if (typeof refreshAssetCatalog === "function") {
            refreshAssetCatalog(false);
          }
        } else {
          showToast(`❌ 素材摄取失败: ${data.error || data.message || "未知错误"}`);
        }
      } catch (err) {
        console.error("素材摄取网络异常:", err);
        showToast(`❌ 网络请求失败: ${err.message}`);
      }
    };
    reader.readAsDataURL(file);
  }, false);
}

function createWeaponVisualSlotRow(key, label, currentVal, origVal, onUpdate) {
  const row = document.createElement("div");
  row.className = "prop-row visual-slot-row";
  const isModified = currentVal !== origVal;
  const meta = getWeaponMeta(currentVal);

  row.innerHTML = `
    <div class="prop-label-col">
      <div class="prop-meta-line">
        <span class="type-pill Weapon" style="background: rgba(139,92,246,0.2); color: #a78bfa; border: 1px solid rgba(139,92,246,0.4);">REF</span>
        <span class="prop-var-name">${key}</span>
      </div>
      <div class="prop-desc">${label}</div>
    </div>
    <div class="prop-input-col" style="flex: 1;">
      <div class="visual-asset-slot-card" id="weaponSlotCard_${key}" title="点击更换武器，或直接从外部拖入图片素材">
        <div class="slot-thumb-box">
          ${meta.icon ? `<img class="slot-thumb-img" src="${meta.icon}" alt="${meta.name}" />` : `<span style="font-size: 20px;">🔫</span>`}
        </div>
        <div class="slot-info-box">
          <div class="slot-title">
            <span>${meta.name}</span>
            <span class="slot-code">${currentVal}</span>
          </div>
          <div class="slot-badges">
            <span class="badge-mini cyan">💥 伤害: ${meta.damage}</span>
            <span class="badge-mini green">⚡ 射速: ${meta.fireRate}/s</span>
            <span class="badge-mini gray">🚀 弹速: ${meta.bulletSpeed}</span>
          </div>
        </div>
        <div class="slot-btn-group">
          <button class="btn btn-secondary btn-xs glow-cyan" type="button">🔄 更换</button>
        </div>
      </div>
    </div>
    <div class="prop-action-col">
      ${isModified ? '<span class="mod-dot" title="已修改"></span>' : ''}
    </div>
  `;

  const card = row.querySelector(".visual-asset-slot-card");
  card.onclick = (e) => {
    openVisualWeaponPalette(currentVal, (newWeaponId) => {
      onUpdate(newWeaponId);
      renderPlayerPropertyTree(state.current.characters[state.selectedPlayerId]);
    });
  };

  // 支持从外部直接拖入武器切片或图标
  setupUniversalImageDrop(card, {
    category: "weapon",
    entityId: () => currentVal || "Custom_Weapons",
    label: `${label} (武器素材)`,
    onSuccess: (data) => {
      const wId = currentVal;
      if (state.current.weapons && state.current.weapons[wId]) {
        state.current.weapons[wId].Icon = data.project_rel_path;
        updateDiffState();
      }
      renderPlayerPropertyTree(state.current.characters[state.selectedPlayerId]);
    }
  });

  return row;
}

function openVisualWeaponPalette(currentWeaponId, onSelect) {
  let modal = document.getElementById("visualWeaponPaletteModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "visualWeaponPaletteModal";
    modal.className = "visual-palette-modal";
    document.body.appendChild(modal);
  }

  const weapons = state.current.weapons || {};
  modal.innerHTML = `
    <div class="visual-palette-box">
      <div class="visual-palette-header">
        <h3><span>🔫</span> 可视化军备枪械库选择</h3>
        <button class="btn-close" onclick="document.getElementById('visualWeaponPaletteModal').remove()">&times;</button>
      </div>
      <div class="visual-palette-grid">
        ${Object.keys(weapons).map(wId => {
          const wMeta = getWeaponMeta(wId);
          const isActive = wId === currentWeaponId;
          return `
            <div class="visual-palette-card ${isActive ? 'active' : ''}" onclick="selectWeaponFromPalette('${wId}')">
              <div class="card-preview-thumb">
                ${wMeta.icon ? `<img src="${wMeta.icon}" alt="${wMeta.name}" />` : `<span style="font-size: 20px;">🔫</span>`}
              </div>
              <div style="flex: 1; overflow: hidden;">
                <div style="font-size: 13px; font-weight: bold; color: #f8fafc;">${wMeta.name}</div>
                <div style="font-size: 10px; color: #94a3b8; font-family: monospace;">${wId}</div>
                <div style="display: flex; gap: 4px; margin-top: 4px;">
                  <span class="badge-mini cyan">${wMeta.damage} 伤</span>
                  <span class="badge-mini green">${wMeta.fireRate}/s</span>
                </div>
              </div>
              ${isActive ? '<span style="color: #10b981; font-size: 16px;">✓</span>' : ''}
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `;

  window.selectWeaponFromPalette = (chosenId) => {
    onSelect(chosenId);
    showToast(`🔫 已装备武器：${weapons[chosenId] ? weapons[chosenId].DisplayName : chosenId}`);
    modal.remove();
  };

  modal.onclick = (e) => {
    if (e.target === modal) modal.remove();
  };
}

function createVfxVisualSlotRow(key, label, currentVal, origVal, onUpdate) {
  const row = document.createElement("div");
  row.className = "prop-row visual-slot-row";
  const isModified = currentVal !== origVal;
  const meta = getVfxMeta(currentVal);

  row.innerHTML = `
    <div class="prop-label-col">
      <div class="prop-meta-line">
        <span class="type-pill VFX" style="background: rgba(236,72,153,0.2); color: #f472b6; border: 1px solid rgba(236,72,153,0.4);">REF</span>
        <span class="prop-var-name">${key}</span>
      </div>
      <div class="prop-desc">${label}</div>
    </div>
    <div class="prop-input-col" style="flex: 1;">
      <div class="visual-asset-slot-card vfx-card" id="vfxSlotCard_${key}" title="鼠标悬停放映动效，点击更换特效，或直接从外部拖入图片素材">
        <div class="slot-thumb-box vfx-live-box" title="鼠标悬停连续放映特效帧">
          <img class="slot-thumb-img vfx-live-img" src="${meta.firstFrame || ''}" alt="${meta.name}" />
          <span class="vfx-live-badge">${meta.frameCount}F</span>
        </div>
        <div class="slot-info-box">
          <div class="slot-title">
            <span>✨ ${meta.name}</span>
          </div>
          <div class="slot-badges">
            <span class="badge-mini cyan">🎬 ${meta.frameCount} 帧动效</span>
            <span class="badge-mini gray" title="${meta.folder}">${meta.folder}</span>
          </div>
        </div>
        <div class="slot-btn-group">
          <button class="btn btn-secondary btn-xs glow-cyan" type="button" title="从可视化特效库挑选">📁 更换</button>
        </div>
      </div>
    </div>
    <div class="prop-action-col">
      ${isModified ? '<span class="mod-dot" title="已修改"></span>' : ''}
    </div>
  `;

  // 1. 鼠标悬停逐帧放映微缩动效
  const thumbBox = row.querySelector(".slot-thumb-box");
  const thumbImg = row.querySelector(".vfx-live-img");
  let hoverTimer = null;
  let hoverFrameIdx = 0;

  thumbBox.addEventListener("mouseenter", () => {
    const curMeta = getVfxMeta(row.dataset.currentVal || currentVal);
    if (!curMeta.frames || curMeta.frames.length <= 1) return;
    hoverFrameIdx = 0;
    hoverTimer = setInterval(() => {
      hoverFrameIdx = (hoverFrameIdx + 1) % curMeta.frames.length;
      thumbImg.src = `/art/${curMeta.frames[hoverFrameIdx]}`;
    }, 110);
  });

  thumbBox.addEventListener("mouseleave", () => {
    if (hoverTimer) clearInterval(hoverTimer);
    hoverTimer = null;
    const curMeta = getVfxMeta(row.dataset.currentVal || currentVal);
    if (curMeta.firstFrame) thumbImg.src = curMeta.firstFrame;
  });

  // 2. 点击卡片或按钮打开可视化特效画廊
  const card = row.querySelector(".visual-asset-slot-card");
  card.onclick = () => {
    openVisualVfxPalette(row.dataset.currentVal || currentVal, (newVfxPath) => {
      row.dataset.currentVal = newVfxPath;
      onUpdate(newVfxPath);
      renderPlayerPropertyTree(state.current.characters[state.selectedPlayerId]);
    });
  };

  // 3. 支持从操作系统外部直接拖入技能特效帧（自动执行去黑底预处理）
  setupUniversalImageDrop(card, {
    category: "vfx",
    entityId: () => {
      const cleanKey = key.replace(/[^a-zA-Z0-9_]/g, "");
      return `${state.selectedPlayerId}_${cleanKey}`;
    },
    autoRemoveBlack: true,
    label: `${label} (技能特效切片)`,
    onSuccess: (data) => {
      row.dataset.currentVal = data.project_rel_path;
      onUpdate(data.project_rel_path);
      renderPlayerPropertyTree(state.current.characters[state.selectedPlayerId]);
    }
  });

  return row;
}

function openVisualVfxPalette(currentVfxPath, onSelect) {
  let modal = document.getElementById("visualVfxPaletteModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "visualVfxPaletteModal";
    modal.className = "visual-palette-modal";
    document.body.appendChild(modal);
  }

  const catalog = state.vfxCatalog || [];
  modal.innerHTML = `
    <div class="visual-palette-box" style="max-width: 780px;">
      <div class="visual-palette-header">
        <h3><span>✨</span> 可视化战斗特效画廊 (共 ${catalog.length} 款特效动效)</h3>
        <button class="btn-close" onclick="document.getElementById('visualVfxPaletteModal').remove()">&times;</button>
      </div>
      <div class="visual-palette-grid">
        ${catalog.map(v => {
          const vMeta = getVfxMeta(v.path);
          const isActive = v.path === currentVfxPath || v.id === currentVfxPath;
          return `
            <div class="visual-palette-card ${isActive ? 'active' : ''}" 
                 data-vfx-path="${v.path}"
                 onclick="selectVfxFromPalette('${v.path}')">
              <div class="card-preview-thumb vfx-palette-thumb" data-frames='${JSON.stringify(v.frames)}'>
                ${vMeta.firstFrame ? `<img src="${vMeta.firstFrame}" alt="${vMeta.name}" />` : `<span>✨</span>`}
              </div>
              <div style="flex: 1; overflow: hidden;">
                <div style="font-size: 13px; font-weight: bold; color: #f8fafc;">${vMeta.name}</div>
                <div style="font-size: 10px; color: #94a3b8; font-family: monospace;">${v.id}</div>
                <div style="display: flex; gap: 4px; margin-top: 4px;">
                  <span class="badge-mini cyan">${v.frames.length} 帧切片</span>
                </div>
              </div>
              ${isActive ? '<span style="color: #10b981; font-size: 16px;">✓</span>' : ''}
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `;

  modal.querySelectorAll(".visual-palette-card").forEach(c => {
    const thumbImg = c.querySelector("img");
    const thumbBox = c.querySelector(".vfx-palette-thumb");
    const framesData = JSON.parse(thumbBox.dataset.frames || "[]");
    let timer = null;
    let idx = 0;
    if (framesData.length > 1 && thumbImg) {
      c.addEventListener("mouseenter", () => {
        idx = 0;
        timer = setInterval(() => {
          idx = (idx + 1) % framesData.length;
          thumbImg.src = `/art/${framesData[idx]}`;
        }, 110);
      });
      c.addEventListener("mouseleave", () => {
        if (timer) clearInterval(timer);
        timer = null;
        thumbImg.src = `/art/${framesData[0]}`;
      });
    }
  });

  window.selectVfxFromPalette = (chosenPath) => {
    onSelect(chosenPath);
    const meta = getVfxMeta(chosenPath);
    showToast(`✨ 已绑定特效：${meta.name}`);
    modal.remove();
  };

  modal.onclick = (e) => {
    if (e.target === modal) modal.remove();
  };
}

function openVisualFlipbookPalette(currentPath, onSelect) {
  let modal = document.getElementById("visualFlipbookPaletteModal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "visualFlipbookPaletteModal";
    modal.className = "visual-palette-modal";
    document.body.appendChild(modal);
  }

  const flipbooks = state.availableFlipbooks || [];
  modal.innerHTML = `
    <div class="visual-palette-box" style="max-width: 780px;">
      <div class="visual-palette-header">
        <h3><span>🎬</span> 可视化怪物 Flipbook 资产画廊</h3>
        <button class="btn-close" onclick="document.getElementById('visualFlipbookPaletteModal').remove()">&times;</button>
      </div>
      <div class="visual-palette-grid">
        ${flipbooks.map(fb => {
          const isActive = fb.path === currentPath;
          let thumb = "";
          let frames = [];
          if (fb.enemy_key && state.current.enemies[fb.enemy_key]) {
            const art = state.current.enemies[fb.enemy_key].ArtInfo;
            if (art && art.frames) {
              thumb = `/art/${art.frames[0]}`;
              frames = art.frames;
            }
          }
          return `
            <div class="visual-palette-card ${isActive ? 'active' : ''}" onclick="selectFlipbookFromPalette('${fb.path}')">
              <div class="card-preview-thumb fb-palette-thumb" data-frames='${JSON.stringify(frames)}'>
                ${thumb ? `<img src="${thumb}" alt="${fb.name}" />` : `<span>🎬</span>`}
              </div>
              <div style="flex: 1; overflow: hidden;">
                <div style="font-size: 13px; font-weight: bold; color: #f8fafc;">${fb.name}</div>
                <div style="font-size: 10px; color: #94a3b8; font-family: monospace; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${fb.path}">${fb.path.split('/').pop()}</div>
                <div style="display: flex; gap: 4px; margin-top: 4px;">
                  <span class="badge-mini cyan">4 帧单向</span>
                </div>
              </div>
              ${isActive ? '<span style="color: #10b981; font-size: 16px;">✓</span>' : ''}
            </div>
          `;
        }).join("")}
      </div>
    </div>
  `;

  // 悬停动态逐帧放映
  modal.querySelectorAll(".visual-palette-card").forEach(c => {
    const thumbImg = c.querySelector("img");
    const thumbBox = c.querySelector(".fb-palette-thumb");
    const framesData = JSON.parse(thumbBox.dataset.frames || "[]");
    let timer = null;
    let idx = 0;
    if (framesData.length > 1 && thumbImg) {
      c.addEventListener("mouseenter", () => {
        idx = 0;
        timer = setInterval(() => {
          idx = (idx + 1) % framesData.length;
          thumbImg.src = `/art/${framesData[idx]}`;
        }, 120);
      });
      c.addEventListener("mouseleave", () => {
        if (timer) clearInterval(timer);
        timer = null;
        thumbImg.src = `/art/${framesData[0]}`;
      });
    }
  });

  window.selectFlipbookFromPalette = (chosenPath) => {
    onSelect(chosenPath);
    const matched = flipbooks.find(f => f.path === chosenPath);
    showToast(`🎬 已选定 Flipbook：${matched ? matched.name : chosenPath}`);
    modal.remove();
  };

  modal.onclick = (e) => {
    if (e.target === modal) modal.remove();
  };
}

function createAssetVisualSlotRow(key, label, currentVal, origVal, onUpdate) {
  const row = document.createElement("div");
  row.className = "prop-row visual-slot-row";
  const isModified = currentVal !== origVal;
  const imgUrl = currentVal ? `/art/${currentVal}` : "";
  const fileName = currentVal ? currentVal.split("/").pop() : "未选择";
  const folder = currentVal && currentVal.includes("/") ? currentVal.substring(0, currentVal.lastIndexOf("/")) : "01_Player";

  row.innerHTML = `
    <div class="prop-label-col">
      <div class="prop-meta-line">
        <span class="type-pill AssetReference" style="background: rgba(16,185,129,0.2); color: #34d399; border: 1px solid rgba(16,185,129,0.4);">Avatar</span>
        <span class="prop-var-name">${key}</span>
      </div>
      <div class="prop-desc">${label}</div>
    </div>
    <div class="prop-input-col" style="flex: 1;">
      <div class="visual-asset-slot-card avatar-slot-card" title="点击放大预览，支持直接拖入外部图片更换">
        <div class="slot-thumb-box" id="avatarSlotThumbBox">
          ${imgUrl ? `<img class="slot-thumb-img" src="${imgUrl}" alt="头像" />` : `<span style="font-size: 20px;">👤</span>`}
        </div>
        <div class="slot-info-box">
          <div class="slot-title">
            <span>${fileName}</span>
          </div>
          <div class="slot-badges">
            <span class="badge-mini cyan">🖼️ 角色头像</span>
            <span class="badge-mini gray" title="${folder}">${folder}</span>
          </div>
        </div>
        <div class="slot-btn-group">
          <button class="btn btn-secondary btn-xs glow-cyan btn-browse-avatar" type="button" title="打开素材库挑选">📁 浏览</button>
        </div>
      </div>
    </div>
    <div class="prop-action-col">
      ${isModified ? '<span class="mod-dot" title="已修改"></span>' : ''}
    </div>
  `;

  const card = row.querySelector(".visual-asset-slot-card");
  card.onclick = (e) => {
    openAssetPickerForAvatar();
  };

  // 支持从外部直接拖入图片替换头像，自动持久化备份原图并规范存入工程内部，彻底解耦外部路径！
  setupUniversalImageDrop(card, {
    category: "avatar",
    entityId: () => state.selectedPlayerId || "Player",
    label: "角色头像切片",
    onSuccess: (data) => {
      onUpdate(data.project_rel_path);
      const avatarImg = document.getElementById("playerAvatarImg");
      if (avatarImg) avatarImg.src = data.web_url;
      renderPlayerPropertyTree(state.current.characters[state.selectedPlayerId]);
    }
  });

  return row;
}

// 渲染主角全属性 Details 面板
function renderPlayerPropertyTree(charData) {
  const container = document.getElementById("playerPropsTree");
  container.innerHTML = "";

  const origChar = state.original && state.original.characters ? state.original.characters[state.selectedPlayerId] : {};

  // 1. 基础身份与头像
  const cat1 = createPropCategory("🏷️ 身份标识与外观头像 (Identity & Avatar)");
  cat1.list.appendChild(createPropRow("DisplayName", "角色称谓 (DisplayName)", "String", charData.DisplayName, origChar.DisplayName, (val) => {
    charData.DisplayName = val;
    document.getElementById("playerStageName").textContent = `${val} (${state.selectedPlayerId})`;
    updateDiffState();
  }));

  cat1.list.appendChild(createAssetVisualSlotRow("Avatar", "角色头像切片 (Avatar Path)", charData.Avatar, origChar.Avatar, (val) => {
    charData.Avatar = val;
    document.getElementById("playerAvatarImg").src = `/art/${val}`;
    updateDiffState();
  }));
  container.appendChild(cat1.group);

  // 2. 初始军备与战术技能
  const cat2 = createPropCategory("🔫 初始军备与战术技能 (Weapons & Tactical)");
  cat2.list.appendChild(createWeaponVisualSlotRow("DefaultWeaponID", "主武器 (Primary Weapon)", charData.DefaultWeaponID, origChar.DefaultWeaponID, (val) => {
    charData.DefaultWeaponID = val;
    updateDiffState();
  }));

  cat2.list.appendChild(createWeaponVisualSlotRow("SecondaryWeaponID", "副武器 (Secondary Weapon)", charData.SecondaryWeaponID || "WPN_Shotgun_Heavy", origChar.SecondaryWeaponID, (val) => {
    charData.SecondaryWeaponID = val;
    updateDiffState();
  }));

  cat2.list.appendChild(createNumberPropRow("TacticalCooldown", "技能冷却秒数 (Cooldown)", charData.TacticalCooldown, origChar.TacticalCooldown, 1.0, 1.0, 30.0, (val) => {
    charData.TacticalCooldown = val;
    updateDiffState();
  }));
  container.appendChild(cat2.group);

  // 3. 战斗数值与抗性
  const cat3 = createPropCategory("🛡️ 战斗数值、机动与生存 (Combat & Survival)");
  cat3.list.appendChild(createNumberPropRow("MaxHealth", "最大生命值 (MaxHealth)", charData.MaxHealth, origChar.MaxHealth, 50, 100, 5000, (val) => {
    charData.MaxHealth = val;
    updateDiffState();
  }));
  cat3.list.appendChild(createNumberPropRow("Armor", "基础护甲值 (Armor)", charData.Armor || 15, origChar.Armor, 1, 0, 100, (val) => {
    charData.Armor = val;
    updateDiffState();
  }));
  cat3.list.appendChild(createNumberPropRow("MoveSpeed", "基础移速 (MoveSpeed)", charData.MoveSpeed, origChar.MoveSpeed, 10, 100, 800, (val) => {
    charData.MoveSpeed = val;
    updateDiffState();
  }));
  cat3.list.appendChild(createNumberPropRow("CritChance", "基础暴击率 (CritChance)", charData.CritChance || 0.15, origChar.CritChance, 0.01, 0.0, 1.0, (val) => {
    charData.CritChance = val;
    updateDiffState();
  }));
  cat3.list.appendChild(createNumberPropRow("CritMultiplier", "暴击倍率 (CritMultiplier)", charData.CritMultiplier || 1.5, origChar.CritMultiplier, 0.1, 1.0, 5.0, (val) => {
    charData.CritMultiplier = val;
    updateDiffState();
  }));
  cat3.list.appendChild(createNumberPropRow("PickupRadius", "水晶拾取范围 (PickupRadius)", charData.PickupRadius || 120, origChar.PickupRadius, 10, 50, 500, (val) => {
    charData.PickupRadius = val;
    updateDiffState();
  }));
  container.appendChild(cat3.group);

  // 4. 特效绑定挂载 (VFX)
  const cat4 = createPropCategory("✨ 角色特效挂载 (VFX Attachments)");
  const curVFX = charData.VFX || {};

  cat4.list.appendChild(createVfxVisualSlotRow("HitVFX", "受击反馈特效 (HitVFX)", curVFX.HitVFX || "05_VFX/11_Hit_Kinetic", (origChar.VFX || {}).HitVFX, (val) => {
    if (!charData.VFX) charData.VFX = {};
    charData.VFX.HitVFX = val;
    updateDiffState();
  }));

  cat4.list.appendChild(createVfxVisualSlotRow("SkillVFX", "战术技能特效 (SkillVFX)", curVFX.SkillVFX || "05_VFX/09_Nanite_Heal", (origChar.VFX || {}).SkillVFX, (val) => {
    if (!charData.VFX) charData.VFX = {};
    charData.VFX.SkillVFX = val;
    updateDiffState();
  }));

  cat4.list.appendChild(createVfxVisualSlotRow("MuzzleVFX", "枪口火光特效 (MuzzleVFX)", curVFX.MuzzleVFX || "05_VFX/13_Muzzle_Flash", (origChar.VFX || {}).MuzzleVFX, (val) => {
    if (!charData.VFX) charData.VFX = {};
    charData.VFX.MuzzleVFX = val;
    updateDiffState();
  }));

  cat4.list.appendChild(createVfxVisualSlotRow("DashVFX", "冲刺残影特效 (DashVFX)", curVFX.DashVFX || "05_VFX/17_Dash_Ghost", (origChar.VFX || {}).DashVFX, (val) => {
    if (!charData.VFX) charData.VFX = {};
    charData.VFX.DashVFX = val;
    updateDiffState();
  }));
  container.appendChild(cat4.group);
}

// 辅助：创建分组
function createPropCategory(title) {
  const group = document.createElement("div");
  group.className = "prop-category-group";
  const header = document.createElement("div");
  header.className = "category-header";
  header.innerHTML = `<span class="category-arrow">▼</span><span>${title}</span>`;
  header.addEventListener("click", () => group.classList.toggle("collapsed"));
  const list = document.createElement("div");
  list.className = "category-props-list";
  group.appendChild(header);
  group.appendChild(list);
  return { group, list };
}

// 辅助：创建通用单行属性 (支持普通文本与AssetReference素材库浏览)
function createPropRow(key, name, type, val, origVal, onUpdate) {
  const row = document.createElement("div");
  row.className = "prop-row";
  const isModified = val !== origVal;
  const isAsset = type === "AssetReference";

  row.innerHTML = `
    <div class="prop-label-col">
      <div class="prop-meta-line">
        <span class="type-pill ${type}">${type}</span>
        <span class="prop-var-name">${key}</span>
      </div>
      <div class="prop-desc">${name}</div>
    </div>
    <div class="prop-input-col" style="${isAsset ? 'display: flex; gap: 6px; align-items: center;' : ''}">
      <input type="text" class="input-text" value="${val || ''}" style="flex: 1;" />
      ${isAsset ? `<button class="btn btn-secondary btn-sm glow-cyan" title="从素材库挑选" style="padding: 4px 8px; font-size: 11px; white-space: nowrap;">📁 浏览</button>` : ''}
    </div>
    <div class="prop-action-col">
      ${isModified ? '<span class="mod-dot" title="已修改"></span>' : ''}
    </div>
  `;

  const input = row.querySelector("input");
  input.addEventListener("input", (e) => onUpdate(e.target.value));

  if (isAsset) {
    const btnBrowse = row.querySelector("button");
    btnBrowse.addEventListener("click", () => {
      openAssetBrowser({
        title: `为【${key} (${name})】挑选美术资产`,
        currentVal: input.value,
        filterDir: input.value || "",
        mode: "file",
        onSelect: (selectedPath) => {
          input.value = selectedPath;
          onUpdate(selectedPath);
        }
      });
    });
  }

  return row;
}

// 辅助：创建数字+滑块单行属性
function createNumberPropRow(key, name, val, origVal, step, min, max, onUpdate) {
  const row = document.createElement("div");
  row.className = "prop-row";
  const isModified = val !== origVal;

  row.innerHTML = `
    <div class="prop-label-col">
      <div class="prop-meta-line">
        <span class="type-pill Float">Float</span>
        <span class="prop-var-name">${key}</span>
      </div>
      <div class="prop-desc">${name}</div>
    </div>
    <div class="prop-input-col">
      <input type="number" class="prop-input-number" value="${val}" step="${step}" min="${min}" max="${max}" />
      <input type="range" class="prop-slider" value="${val}" step="${step}" min="${min}" max="${max}" />
    </div>
    <div class="prop-action-col">
      ${isModified ? '<span class="mod-dot" title="已修改"></span>' : ''}
    </div>
  `;

  const numInput = row.querySelector("input[type='number']");
  const slider = row.querySelector("input[type='range']");

  const sync = (nval) => {
    numInput.value = nval;
    slider.value = nval;
    onUpdate(nval);
  };

  numInput.addEventListener("input", (e) => sync(parseFloat(e.target.value) || 0));
  slider.addEventListener("input", (e) => sync(parseFloat(e.target.value) || 0));
  return row;
}

// 辅助：创建下拉选择单行属性
function createSelectPropRow(key, name, val, origVal, options, onUpdate) {
  const row = document.createElement("div");
  row.className = "prop-row";
  const isModified = val !== origVal;

  const select = document.createElement("select");
  select.className = "prop-asset-select";
  options.forEach(opt => {
    const o = document.createElement("option");
    o.value = opt.value;
    o.textContent = opt.label;
    if (opt.value === val) o.selected = true;
    select.appendChild(o);
  });
  select.addEventListener("change", (e) => onUpdate(e.target.value));

  row.innerHTML = `
    <div class="prop-label-col">
      <div class="prop-meta-line">
        <span class="type-pill AssetReference">Ref</span>
        <span class="prop-var-name">${key}</span>
      </div>
      <div class="prop-desc">${name}</div>
    </div>
    <div class="prop-input-col"></div>
    <div class="prop-action-col">
      ${isModified ? '<span class="mod-dot" title="已修改"></span>' : ''}
    </div>
  `;

  row.querySelector(".prop-input-col").appendChild(select);
  return row;
}

// ==============================================================================
// 2. 敌人蓝图属性配置 Inspector & 4 帧放映室
// ==============================================================================
function renderEnemyList() {
  const container = document.getElementById("enemyList");
  container.innerHTML = "";

  const enemies = state.current.enemies || {};
  const eids = Object.keys(enemies);
  document.getElementById("enemyCountBadge").textContent = `${eids.length} 类`;

  eids.forEach(eid => {
    const item = enemies[eid];
    const el = document.createElement("div");
    el.className = `enemy-item-card ${eid === state.selectedEnemyId ? "active" : ""}`;
    
    let thumbSrc = "";
    if (item.ArtInfo && item.ArtInfo.frames && item.ArtInfo.frames.length > 0) {
      thumbSrc = `/art/${item.ArtInfo.frames[0]}`;
    }

    el.innerHTML = `
      <div class="enemy-thumb-wrap">
        <img class="enemy-thumb" src="${thumbSrc}" alt="${item.DisplayName}" />
      </div>
      <div class="enemy-info">
        <div class="name">${item.DisplayName}</div>
        <div class="meta">HP: ${item.MaxHealth} | SPD: ${item.MoveSpeed}</div>
      </div>
    `;

    el.addEventListener("click", () => {
      state.selectedEnemyId = eid;
      document.querySelectorAll(".enemy-item-card").forEach(c => c.classList.remove("active"));
      el.classList.add("active");
      renderEnemyDetail();
    });

    container.appendChild(el);
  });
}

function renderEnemyDetail() {
  const enemy = state.current.enemies[state.selectedEnemyId];
  if (!enemy) return;

  document.getElementById("currentBpTitle").textContent = `${state.selectedEnemyId} (${enemy.DisplayName})`;
  document.getElementById("currentBpClassPath").textContent = enemy.BlueprintClass || `/Game/Blueprints/Characters/Enemies/BP_${state.selectedEnemyId}`;

  startEnemySpriteAnimation(enemy);
  renderEnemyBlueprintPropertyTree(enemy);
}

function startEnemySpriteAnimation(enemy) {
  if (state.enemyAnimInterval) {
    clearInterval(state.enemyAnimInterval);
  }

  const frames = enemy.ArtInfo ? enemy.ArtInfo.frames : [];
  if (!frames || frames.length === 0) return;

  state.enemyFrameIdx = 0;
  const imgEl = document.getElementById("spriteLiveImage");
  const indicatorEl = document.getElementById("frameIndicator");
  const scaleIndicator = document.getElementById("scaleIndicator");
  const slicesContainer = document.getElementById("frameSlices");

  const curScale = enemy.Scale !== undefined ? enemy.Scale : 0.45;
  scaleIndicator.textContent = `SCALE: ${curScale}x`;
  imgEl.style.transform = `scale(${curScale / 0.45})`;

  slicesContainer.innerHTML = "";
  frames.forEach((f, idx) => {
    const box = document.createElement("div");
    box.className = `frame-slice-box ${idx === 0 ? "current" : ""}`;
    box.innerHTML = `<img src="/art/${f}" alt="F${idx+1}" /><span class="label">F${idx+1}</span>`;
    slicesContainer.appendChild(box);
  });

  const step = () => {
    if (frames.length === 0) return;
    imgEl.src = `/art/${frames[state.enemyFrameIdx]}`;
    indicatorEl.textContent = `FRAME: ${state.enemyFrameIdx + 1}/${frames.length}`;

    document.querySelectorAll("#frameSlices .frame-slice-box").forEach((b, i) => {
      if (i === state.enemyFrameIdx) b.classList.add("current");
      else b.classList.remove("current");
    });

    state.enemyFrameIdx = (state.enemyFrameIdx + 1) % frames.length;
  };

  step();
  const ms = Math.max(50, 1000 / state.enemyFPS);
  state.enemyAnimInterval = setInterval(step, ms);
}

function renderEnemyBlueprintPropertyTree(enemy) {
  const container = document.getElementById("blueprintPropsTree");
  container.innerHTML = "";

  const origEnemy = state.original && state.original.enemies ? state.original.enemies[state.selectedEnemyId] : {};
  const filter = state.enemySearchFilter.toLowerCase().trim();

  state.blueprintSchema.forEach(cat => {
    const matchedProps = cat.props.filter(p => {
      if (!filter) return true;
      return p.key.toLowerCase().includes(filter) || p.name.toLowerCase().includes(filter);
    });

    if (matchedProps.length === 0) return;

    const groupEl = document.createElement("div");
    groupEl.className = "prop-category-group";
    const headerEl = document.createElement("div");
    headerEl.className = "category-header";
    headerEl.innerHTML = `<span class="category-arrow">▼</span><span>${cat.category}</span>`;
    headerEl.addEventListener("click", () => groupEl.classList.toggle("collapsed"));
    groupEl.appendChild(headerEl);

    const listEl = document.createElement("div");
    listEl.className = "category-props-list";

    matchedProps.forEach(p => {
      const rowEl = document.createElement("div");
      rowEl.className = "prop-row";

      const val = enemy[p.key] !== undefined ? enemy[p.key] : (p.default !== undefined ? p.default : "");
      const origVal = origEnemy[p.key] !== undefined ? origEnemy[p.key] : (p.default !== undefined ? p.default : "");
      const isModified = val !== origVal;

      const labelCol = document.createElement("div");
      labelCol.className = "prop-label-col";
      labelCol.innerHTML = `
        <div class="prop-meta-line">
          <span class="type-pill ${p.type}">${p.type}</span>
          <span class="prop-var-name">${p.key}</span>
        </div>
        <div class="prop-desc">${p.name}</div>
      `;

      const inputCol = document.createElement("div");
      inputCol.className = "prop-input-col";

      if (p.readonly) {
        inputCol.innerHTML = `<input type="text" class="input-text" value="${val}" readonly style="width: 100%; opacity: 0.7; font-size: 11px;" />`;
      } else if (p.type === "Boolean") {
        inputCol.innerHTML = `
          <label class="switch-box">
            <input type="checkbox" ${val ? "checked" : ""} />
            <span style="font-family: var(--font-mono); font-size: 11px; color: ${val ? '#10b981' : '#94a3b8'};">
              ${val ? "True (锁定生效)" : "False"}
            </span>
          </label>
        `;
        inputCol.querySelector("input").addEventListener("change", (e) => {
          enemy[p.key] = e.target.checked;
          renderEnemyBlueprintPropertyTree(enemy);
          renderDataTable();
          updateDiffState();
        });
      } else if (p.type === "AssetReference") {
        const matchedFb = state.availableFlipbooks.find(f => f.path === val);
        const fbName = matchedFb ? matchedFb.name : (val ? val.split('.').pop() : "未绑定 Flipbook");
        let fbThumb = "";
        let fbFrames = [];
        if (matchedFb && matchedFb.enemy_key && state.current.enemies[matchedFb.enemy_key]) {
          const art = state.current.enemies[matchedFb.enemy_key].ArtInfo;
          if (art && art.frames && art.frames.length > 0) {
            fbThumb = `/art/${art.frames[0]}`;
            fbFrames = art.frames;
          }
        } else if (enemy.ArtInfo && enemy.ArtInfo.frames && enemy.ArtInfo.frames.length > 0) {
          fbThumb = `/art/${enemy.ArtInfo.frames[0]}`;
          fbFrames = enemy.ArtInfo.frames;
        }

        const fbCard = document.createElement("div");
        fbCard.className = "visual-asset-slot-card";
        fbCard.style.cursor = "pointer";
        fbCard.title = "鼠标悬停预览4帧动作，点击可视化更换Flipbook";
        fbCard.innerHTML = `
          <div class="slot-thumb-box enemy-fb-thumb" style="width:40px; height:40px; min-width:40px;">
            ${fbThumb ? `<img class="slot-thumb-img" src="${fbThumb}" alt="${fbName}" />` : `<span>🎬</span>`}
            <span class="vfx-live-badge">${fbFrames.length || 4}F</span>
          </div>
          <div class="slot-info-box">
            <div class="slot-title">
              <span>${fbName}</span>
            </div>
            <div class="slot-badges">
              <span class="badge-mini cyan">🎬 PaperFlipbook</span>
              <span class="badge-mini gray" title="${val}" style="max-width: 140px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${val ? val.split('/').pop() : ''}</span>
            </div>
          </div>
          <div class="slot-btn-group">
            <button class="btn btn-secondary btn-xs glow-cyan" type="button">🔄 更换</button>
          </div>
        `;

        // 悬停动态放映
        const thumbImg = fbCard.querySelector(".slot-thumb-img");
        let timer = null;
        let idx = 0;
        if (thumbImg && fbFrames.length > 1) {
          fbCard.addEventListener("mouseenter", () => {
            idx = 0;
            timer = setInterval(() => {
              idx = (idx + 1) % fbFrames.length;
              thumbImg.src = `/art/${fbFrames[idx]}`;
            }, 120);
          });
          fbCard.addEventListener("mouseleave", () => {
            if (timer) clearInterval(timer);
            timer = null;
            thumbImg.src = fbThumb;
          });
        }

        fbCard.onclick = () => {
          openVisualFlipbookPalette(val, (newPath) => {
            enemy[p.key] = newPath;
            const newMatched = state.availableFlipbooks.find(f => f.path === newPath);
            if (newMatched && newMatched.enemy_key && state.current.enemies[newMatched.enemy_key]) {
              const targetArt = state.current.enemies[newMatched.enemy_key].ArtInfo;
              if (targetArt) {
                enemy.ArtInfo = targetArt;
                startEnemySpriteAnimation(enemy);
              }
            }
            renderEnemyBlueprintPropertyTree(enemy);
            renderDataTable();
            updateDiffState();
          });
        };

        // 支持直接从操作系统外部拖入怪物贴图/动作切片图片，自动备份并解耦
        setupUniversalImageDrop(fbCard, {
          category: "enemy",
          entityId: () => state.selectedEnemyId || "Custom_Enemy",
          label: `${p.name} (怪物美术切片)`,
          onSuccess: (data) => {
            enemy[p.key] = data.game_path;
            if (!enemy.ArtInfo) enemy.ArtInfo = {};
            if (!enemy.ArtInfo.frames) enemy.ArtInfo.frames = [];
            enemy.ArtInfo.frames.unshift(data.project_rel_path);
            renderEnemyBlueprintPropertyTree(enemy);
            renderDataTable();
            updateDiffState();
          }
        });

        inputCol.appendChild(fbCard);
      } else {
        const numInput = document.createElement("input");
        numInput.type = "number";
        numInput.className = "prop-input-number";
        numInput.value = val;
        numInput.step = p.step || 1;

        const slider = document.createElement("input");
        slider.type = "range";
        slider.className = "prop-slider";
        slider.value = val;
        slider.step = p.step || 1;

        let baseMax = p.max !== undefined ? p.max : (val > 100 ? val * 2.5 : 200);
        if (p.key === "MaxHealth") baseMax = enemy.MaxHealth > 1000 ? 6000 : 800;
        if (p.key === "Scale") baseMax = 1.5;
        slider.min = p.min || 0;
        slider.max = baseMax;

        const sync = (nval) => {
          enemy[p.key] = nval;
          numInput.value = nval;
          slider.value = nval;
          if (p.key === "Scale") {
            document.getElementById("scaleIndicator").textContent = `SCALE: ${nval}x`;
            document.getElementById("spriteLiveImage").style.transform = `scale(${nval / 0.45})`;
          }
          renderDataTable();
          updateDiffState();
        };

        numInput.addEventListener("input", (e) => sync(parseFloat(e.target.value) || 0));
        slider.addEventListener("input", (e) => sync(parseFloat(e.target.value) || 0));

        inputCol.appendChild(numInput);
        inputCol.appendChild(slider);
      }

      const actionCol = document.createElement("div");
      actionCol.className = "prop-action-col";
      if (isModified) {
        actionCol.innerHTML = `<span class="mod-dot" title="属性已修改"></span>`;
      }

      rowEl.appendChild(labelCol);
      rowEl.appendChild(inputCol);
      rowEl.appendChild(actionCol);
      listEl.appendChild(rowEl);
    });

    groupEl.appendChild(listEl);
    container.appendChild(groupEl);
  });
}

// ==============================================================================
// 3. 全量 UE5 DataTable 网格系统 (Universal DataTable Grid Inspector)
// ==============================================================================
let currentGridTableName = "DT_Enemies";

function switchGridTable(tableName) {
  currentGridTableName = tableName;
  document.querySelectorAll(".dt-selector-bar .btn-chip").forEach(btn => {
    if (btn.getAttribute("onclick") && btn.getAttribute("onclick").includes(tableName)) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });
  renderDataTable();
}

function renderDataTable() {
  const table = document.getElementById("universalDataTable");
  if (!table) return;
  const thead = table.querySelector("thead");
  const tbody = table.querySelector("tbody");
  thead.innerHTML = "";
  tbody.innerHTML = "";

  let dataMap = {};
  if (currentGridTableName === "DT_Characters") dataMap = state.current.characters || {};
  else if (currentGridTableName === "DT_Weapons") dataMap = state.current.weapons || {};
  else if (currentGridTableName === "DT_HitEffects") dataMap = state.current.hit_effects || {};
  else if (currentGridTableName === "DT_Enemies") dataMap = state.current.enemies || {};
  else if (currentGridTableName === "DT_TacticalCards") dataMap = state.current.cards || {};
  else if (currentGridTableName === "DT_MapTiles") dataMap = state.current.tiles || {};

  const rowKeys = Object.keys(dataMap);
  if (rowKeys.length === 0) {
    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:20px;color:#64748b;">该数据表格为空</td></tr>';
    return;
  }

  // 提取所有列字段
  const firstItem = dataMap[rowKeys[0]];
  const cols = ["RowKey", "DisplayName", ...Object.keys(firstItem).filter(k => k !== "DisplayName" && k !== "ArtInfo" && k !== "Animations" && k !== "VFX")];

  // 生成表头
  const trHead = document.createElement("tr");
  cols.forEach(c => {
    const th = document.createElement("th");
    th.textContent = c;
    trHead.appendChild(th);
  });
  thead.appendChild(trHead);

  // 生成行数据
  rowKeys.forEach(rk => {
    const item = dataMap[rk];
    const tr = document.createElement("tr");

    cols.forEach(col => {
      const td = document.createElement("td");
      if (col === "RowKey") {
        td.innerHTML = `<strong>${rk}</strong>`;
      } else {
        const val = item[col] !== undefined ? item[col] : "";
        const isNum = typeof val === "number";
        const input = document.createElement("input");
        input.className = "dt-editable-cell";
        input.type = isNum ? "number" : "text";
        input.value = val;
        if (isNum) input.step = "any";

        input.onchange = (e) => {
          const nval = isNum ? (parseFloat(e.target.value) || 0) : e.target.value;
          item[col] = nval;
          updateDiffState();
          if (currentGridTableName === "DT_Enemies" && rk === state.selectedEnemyId) renderEnemyDetail();
          if (currentGridTableName === "DT_Weapons") renderWeaponsGrid();
          if (currentGridTableName === "DT_Characters") renderPlayerStudio();
          if (currentGridTableName === "DT_MapTiles") renderTilesStudio();
          if (currentGridTableName === "DT_HitEffects") renderEffectsStudio();
        };

        td.appendChild(input);
      }
      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  });
}

// ==============================================================================
// 4. 军备武库与卡牌
// ==============================================================================
// ==============================================================================
// 4. DT_Weapons 武器与子弹全属性配置 (外观图标/飞行贴图/弹道物理/爆炸载荷/特效装配)
// ==============================================================================
function renderWeaponsGrid() {
  const container = document.getElementById("weaponsGrid");
  if (!container) return;
  container.innerHTML = "";

  const weapons = state.current.weapons || {};
  const hitEffects = state.current.hit_effects || {};

  // 动态更新军械库战力 HUD 概览条 (填补空白，直观呈现战力)
  const weaponList = Object.values(weapons);
  const totalWeapons = weaponList.length;
  let totalDps = 0;
  weaponList.forEach(w => {
    totalDps += Math.round((w.Damage || 0) * (1 / (w.FireRate || 0.1)) * (w.PelletCount || 1));
  });
  const avgDps = totalWeapons > 0 ? Math.round(totalDps / totalWeapons) : 0;

  const hudCountEl = document.getElementById("hudWeaponCount");
  const hudDpsEl = document.getElementById("hudAvgDps");
  if (hudCountEl) hudCountEl.textContent = `${totalWeapons} 门主力武器已就绪`;
  if (hudDpsEl) hudDpsEl.textContent = `${avgDps} DPS`;

  Object.entries(weapons).forEach(([wid, w]) => {
    const dps = Math.round((w.Damage || 0) * (1 / (w.FireRate || 0.1)) * (w.PelletCount || 1));
    const card = document.createElement("div");
    card.className = "weapon-card-enhanced";

    const iconSrc = w.Icon ? `/art/${w.Icon}` : `/art/06_Cards/04_WeaponModCards/T_Card_WeaponMod_01.png`;
    const bulletSrc = w.BulletImage ? `/art/${w.BulletImage}` : "";
    const bulletScale = w.BulletScale !== undefined ? w.BulletScale : 0.35;
    const muzzleSrc = w.MuzzleFX ? `/art/${w.MuzzleFX}` : "";
    const impactSrc = w.ImpactFX ? `/art/${w.ImpactFX}` : "";
    const trailText = w.TrailFX || "None";

    // 构造特效下拉选项
    const effectOptions = Object.entries(hitEffects).map(([fxId, fx]) => `
      <option value="${fxId}" ${w.HitEffectID === fxId ? "selected" : ""}>${fx.DisplayName || fxId} (${fxId})</option>
    `).join("");

    card.innerHTML = `
      <!-- 武器卡片头部 -->
      <div class="weapon-card-header-flex">
        <div class="weapon-icon-box" title="点击从素材库更换武器卡面图标 (Icon)" onclick="openWeaponIconPicker('${wid}')">
          <img src="${iconSrc}" alt="${w.DisplayName}" />
          <div class="weapon-icon-overlay">更换图标</div>
        </div>
        <div class="weapon-title-group">
          <div style="display: flex; align-items: center; gap: 8px;">
            <input type="text" class="weapon-name-input" value="${w.DisplayName || wid}" onchange="updateWeaponParam('${wid}', 'DisplayName', this.value)" />
            <span class="weapon-id-badge">${wid}</span>
          </div>
          <div style="display: flex; gap: 8px; align-items: center; margin-top: 5px;">
            <span class="weapon-dps-badge">理论 DPS: ${dps}</span>
            <button class="btn btn-secondary btn-sm glow-cyan" style="padding: 2px 8px; font-size: 11px;" onclick="openWeaponIconPicker('${wid}')">
              🖼️ 换卡牌图标
            </button>
          </div>
        </div>
        <div class="weapon-header-actions" style="display: flex; flex-direction: column; gap: 4px;">
          <button class="btn btn-secondary btn-sm" title="克隆当前武器为新武器行" onclick="cloneWeapon('${wid}')">
            📋 复制武器
          </button>
          <button class="btn btn-secondary btn-sm" style="color: #f43f5e;" title="删除此武器" onclick="deleteWeapon('${wid}')">
            🗑️ 删除
          </button>
        </div>
      </div>

      <!-- 模块一：武器击发机制 (Firearm Specs) -->
      <div class="weapon-section-title">
        <span>🔫 武器击发机制 (Firearm Specs)</span>
      </div>
      <div class="weapon-params-grid">
        <div class="weapon-param-item">
          <label>单发伤害 (Damage)</label>
          <input type="number" class="input-text" value="${w.Damage}" step="2" onchange="updateWeaponParam('${wid}', 'Damage', parseFloat(this.value)||0)" />
        </div>
        <div class="weapon-param-item">
          <label>射频间隔 (FireRate s)</label>
          <input type="number" class="input-text" value="${w.FireRate}" step="0.02" onchange="updateWeaponParam('${wid}', 'FireRate', parseFloat(this.value)||0)" />
        </div>
        <div class="weapon-param-item">
          <label>弹片数量 (PelletCount)</label>
          <input type="number" class="input-text" value="${w.PelletCount}" step="1" onchange="updateWeaponParam('${wid}', 'PelletCount', parseInt(this.value)||1)" />
        </div>
        <div class="weapon-param-item">
          <label>散布角度 (SpreadAngle °)</label>
          <input type="number" class="input-text" value="${w.SpreadAngle}" step="2" onchange="updateWeaponParam('${wid}', 'SpreadAngle', parseFloat(this.value)||0)" />
        </div>
      </div>

      <!-- 模块二：子弹物理与弹道参数 (Bullet & Ballistics) -->
      <div class="weapon-section-title">
        <span>🚀 子弹飞行贴图与弹道物理 (Bullet & Ballistics)</span>
      </div>

      <div class="weapon-bullet-preview-box">
        <div class="weapon-bullet-thumb-wrap" title="点击从素材库挑选子弹飞行切片" onclick="openWeaponBulletPicker('${wid}')">
          ${bulletSrc ? `<img src="${bulletSrc}" alt="子弹" style="transform: scale(${bulletScale * 2.2});" />` : '<span style="font-size:10px;color:#64748b;">无贴图</span>'}
          <div class="overlay-text">改切片</div>
        </div>
        <div class="weapon-bullet-meta">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="font-size: 11px; font-weight: 600; color: #f1f5f9;">飞行切片 (BulletImage)</span>
            <button class="btn btn-secondary btn-sm glow-cyan" style="padding: 2px 7px; font-size: 10px;" onclick="openWeaponBulletPicker('${wid}')">
              📁 挑选子弹
            </button>
          </div>
          <div class="weapon-bullet-path">${w.BulletImage || '未配置子弹贴图'}</div>
          <div class="weapon-bullet-scale-row" style="display: flex; align-items: center; gap: 8px; margin-top: 3px;">
            <span style="color: #94a3b8; font-size: 11px;">缩放 (Scale):</span>
            <input type="number" class="input-text" style="width: 64px; text-align: center;" value="${bulletScale}" step="0.05" min="0.1" max="2.0" onchange="updateWeaponParam('${wid}', 'BulletScale', parseFloat(this.value)||0.35)" />
            <span style="color: #38bdf8; font-family: var(--font-mono); font-weight: 700; font-size: 11px;">${Math.round(bulletScale * 100)}% 尺寸</span>
          </div>
        </div>
      </div>

      <div class="weapon-params-grid">
        <div class="weapon-param-item">
          <label>初速 (ProjectileSpeed)</label>
          <input type="number" class="input-text" value="${w.ProjectileSpeed !== undefined ? w.ProjectileSpeed : 950}" step="50" onchange="updateWeaponParam('${wid}', 'ProjectileSpeed', parseFloat(this.value)||0)" />
        </div>
        <div class="weapon-param-item">
          <label>贯穿怪数 (PierceCount)</label>
          <input type="number" class="input-text" value="${w.PierceCount !== undefined ? w.PierceCount : 1}" step="1" onchange="updateWeaponParam('${wid}', 'PierceCount', parseInt(this.value)||0)" />
        </div>
        <div class="weapon-param-item">
          <label>存活寿命 (LifeSpan s)</label>
          <input type="number" class="input-text" value="${w.LifeSpan !== undefined ? w.LifeSpan : 2.0}" step="0.2" onchange="updateWeaponParam('${wid}', 'LifeSpan', parseFloat(this.value)||1.0)" />
        </div>
        <div class="weapon-param-item">
          <label>碰撞半径 (Radius px)</label>
          <input type="number" class="input-text" value="${w.CollisionRadius !== undefined ? w.CollisionRadius : 12.0}" step="1" onchange="updateWeaponParam('${wid}', 'CollisionRadius', parseFloat(this.value)||12.0)" />
        </div>
        <div class="weapon-param-item" style="grid-column: 1 / -1;">
          <label>碰撞胶囊高度 (CollisionHeight px)</label>
          <input type="number" class="input-text" value="${w.CollisionHeight !== undefined ? w.CollisionHeight : 24.0}" step="1" onchange="updateWeaponParam('${wid}', 'CollisionHeight', parseFloat(this.value)||24.0)" />
        </div>
      </div>

      <!-- 模块三：范围爆炸载荷 (Explosion Payload) -->
      <div class="weapon-section-title">
        <span>💥 范围爆炸载荷 (Explosion Payload)</span>
      </div>
      <div class="weapon-params-grid">
        <div class="weapon-param-item">
          <label>溅射半径 (ExplosionRadius px)</label>
          <input type="number" class="input-text" value="${w.ExplosionRadius !== undefined ? w.ExplosionRadius : 0.0}" step="10" onchange="updateWeaponParam('${wid}', 'ExplosionRadius', parseFloat(this.value)||0)" />
        </div>
        <div class="weapon-param-item">
          <label>爆炸伤害 (ExplosionDamage)</label>
          <input type="number" class="input-text" value="${w.ExplosionDamage !== undefined ? w.ExplosionDamage : 0.0}" step="5" onchange="updateWeaponParam('${wid}', 'ExplosionDamage', parseFloat(this.value)||0)" />
        </div>
      </div>

      <!-- 模块四：战斗特效与状态装配 (VFX & Debuffs) -->
      <div class="weapon-section-title">
        <span>✨ 战斗特效与状态装配 (VFX & Debuffs)</span>
      </div>

      <div class="weapon-art-slots-bar">
        <div class="art-slot-item" title="点击从素材库挑选枪口火光贴图" onclick="openWeaponArtPicker('${wid}', 'MuzzleFX', '03_Weapons')">
          <span class="art-slot-label">枪口火光 (Muzzle)</span>
          <div class="art-slot-thumb">
            ${muzzleSrc ? `<img src="${muzzleSrc}" alt="火光" />` : '<span style="font-size:10px;color:#64748b;">无</span>'}
          </div>
          <span class="art-slot-change-btn">更 换</span>
        </div>

        <div class="art-slot-item" title="点击从素材库挑选命中火花贴图" onclick="openWeaponArtPicker('${wid}', 'ImpactFX', '03_Weapons')">
          <span class="art-slot-label">受击命中 (Impact)</span>
          <div class="art-slot-thumb">
            ${impactSrc ? `<img src="${impactSrc}" alt="命中" />` : '<span style="font-size:10px;color:#64748b;">无</span>'}
          </div>
          <span class="art-slot-change-btn">更 换</span>
        </div>

        <div class="art-slot-item" title="点击从素材库挑选拖尾特效目录" onclick="openWeaponTrailPicker('${wid}')">
          <span class="art-slot-label">子弹拖尾 (TrailFX)</span>
          <div class="art-slot-thumb" style="padding: 2px;">
            <span style="font-size:9px; color:#38bdf8; word-break:break-all; text-align:center;">${trailText.split('/').pop()}</span>
          </div>
          <span class="art-slot-change-btn">更 换</span>
        </div>
      </div>

      <div class="weapon-params-grid">
        <div class="weapon-param-item">
          <label>关联命中特效 (HitEffectID - 驱动DT_HitEffects)</label>
          <select class="prop-asset-select" style="font-size: 11px; padding: 4px;" onchange="updateWeaponParam('${wid}', 'HitEffectID', this.value)">
            ${effectOptions}
          </select>
        </div>
        <div class="weapon-param-item">
          <label>附加减益状态 (InflictDebuffID)</label>
          <input type="text" class="input-text" style="font-size: 12px; padding: 4px;" value="${w.InflictDebuffID || 'None'}" onchange="updateWeaponParam('${wid}', 'InflictDebuffID', this.value)" />
        </div>
      </div>
    `;

    container.appendChild(card);
  });
}

function openWeaponIconPicker(wid) {
  const w = state.current.weapons[wid];
  openAssetBrowser({
    title: `为武器【${w.DisplayName}】挑选专属卡面大图标 (Icon)`,
    currentVal: w.Icon || "",
    filterDir: "06_Cards/04_WeaponModCards",
    mode: "file",
    onSelect: (selectedPath) => {
      w.Icon = selectedPath;
      renderWeaponsGrid();
      updateDiffState();
      showToast(`👁️ 武器卡面图标已更换为: ${selectedPath.split('/').pop()}（草稿预览中，点击右上角【保存修改】后生效）`);
    }
  });
}

function openWeaponBulletPicker(wid) {
  const w = state.current.weapons[wid];
  openAssetBrowser({
    title: `为武器【${w.DisplayName}】挑选飞行子弹切片贴图 (BulletImage)`,
    currentVal: w.BulletImage || "",
    filterDir: "03_Weapons",
    mode: "file",
    onSelect: (selectedPath) => {
      w.BulletImage = selectedPath;
      renderWeaponsGrid();
      updateDiffState();
      showToast(`👁️ 子弹飞行贴图已更新: ${selectedPath.split('/').pop()}（草稿预览中，点击右上角【保存修改】后生效）`);
    }
  });
}

function openWeaponTrailPicker(wid) {
  const w = state.current.weapons[wid];
  openAssetBrowser({
    title: `为武器【${w.DisplayName}】挑选子弹飞行拖尾特效 (TrailFX)`,
    currentVal: w.TrailFX || "",
    filterDir: "05_VFX",
    mode: "folder",
    onSelect: (selectedPath) => {
      w.TrailFX = selectedPath;
      renderWeaponsGrid();
      updateDiffState();
      showToast(`👁️ 子弹拖尾特效已更新: ${selectedPath.split('/').pop()}（草稿预览中，点击右上角【保存修改】后生效）`);
    }
  });
}

function openWeaponArtPicker(wid, fieldKey, defaultDir) {
  const w = state.current.weapons[wid];
  const fieldNames = {
    "BulletImage": "子弹飞行切片",
    "MuzzleFX": "枪口火光贴图",
    "ImpactFX": "受击命中特效",
    "TrailFX": "飞行拖尾特效"
  };
  openAssetBrowser({
    title: `为武器【${w.DisplayName}】挑选${fieldNames[fieldKey] || fieldKey}`,
    currentVal: w[fieldKey] || "",
    filterDir: defaultDir,
    mode: "file",
    onSelect: (selectedPath) => {
      w[fieldKey] = selectedPath;
      renderWeaponsGrid();
      updateDiffState();
      showToast(`👁️ 武器${fieldNames[fieldKey] || fieldKey}已更新（草稿预览中，点击右上角【保存修改】后生效）`);
    }
  });
}

function updateWeaponParam(wid, key, val) {
  const w = state.current.weapons[wid];
  if (w) {
    w[key] = val;
    renderWeaponsGrid();
    updateDiffState();
  }
}

function cloneWeapon(wid) {
  const w = state.current.weapons[wid];
  if (!w) return;
  const newWid = `${wid}_Copy_${Math.floor(Math.random() * 899 + 100)}`;
  state.current.weapons[newWid] = JSON.parse(JSON.stringify(w));
  state.current.weapons[newWid].DisplayName = `${w.DisplayName || wid} (副本)`;
  renderWeaponsGrid();
  renderDataTable();
  updateDiffState();
  showToast(`🎉 成功克隆武器: ${newWid} 并加入 DT_Weapons！`);
}

function deleteWeapon(wid) {
  if (confirm(`确定要从武器数据表 (DT_Weapons) 中删除【${wid}】吗？`)) {
    delete state.current.weapons[wid];
    renderWeaponsGrid();
    renderDataTable();
    updateDiffState();
    showToast(`🗑️ 已删除武器: ${wid}`);
  }
}

// ==============================================================================
// 4.5 DT_HitEffects 战斗特效工作台 (VFX Live Studio & HitStop & CameraShake)
// ==============================================================================
function renderEffectsStudio() {
  const hitEffects = state.current.hit_effects || {};
  const effectKeys = Object.keys(hitEffects);
  if (effectKeys.length === 0) return;

  if (!state.selectedEffectId || !hitEffects[state.selectedEffectId]) {
    state.selectedEffectId = effectKeys[0];
  }

  const fxData = hitEffects[state.selectedEffectId];
  if (!fxData) return;

  // 1. 渲染左侧特效选择列表
  renderEffectList();

  // 2. 更新中间放映台元数据
  const titleEl = document.getElementById("currentEffectTitle");
  const folderEl = document.getElementById("currentEffectFolder");
  const typeBadgeEl = document.getElementById("effectTypeBadge");
  const typeIconEl = document.getElementById("effectTypeIcon");

  if (titleEl) titleEl.textContent = `${fxData.DisplayName || state.selectedEffectId} (${state.selectedEffectId})`;
  if (folderEl) folderEl.textContent = fxData.VFXFolder || "未配置素材目录";
  if (typeBadgeEl) typeBadgeEl.textContent = fxData.EffectType || "HitImpact";

  const typeIcons = {
    "MuzzleFlash": "🔥",
    "HitImpact": "💥",
    "DeathExplosion": "💣",
    "AreaField": "☣️",
    "TrailFX": "✨"
  };
  if (typeIconEl) typeIconEl.textContent = typeIcons[fxData.EffectType] || "✨";

  // 3. 同步滑块初始值
  state.effectFPS = fxData.FPS !== undefined ? fxData.FPS : 12.0;
  state.effectScale = fxData.Scale !== undefined ? fxData.Scale : 0.45;

  const fpsSlider = document.getElementById("effectFpsSlider");
  const fpsDisplay = document.getElementById("effectFpsDisplay");
  if (fpsSlider) fpsSlider.value = state.effectFPS;
  if (fpsDisplay) fpsDisplay.textContent = `${state.effectFPS.toFixed(1)} FPS`;

  const scaleSlider = document.getElementById("effectScaleSlider");
  const scaleDisplay = document.getElementById("effectScaleDisplay");
  if (scaleSlider) scaleSlider.value = state.effectScale;
  if (scaleDisplay) scaleDisplay.textContent = `${state.effectScale.toFixed(2)}x`;

  // 4. 异步加载当前特效切片目录下的帧序列并启动动画
  if (fxData.VFXFolder) {
    loadEffectFrames(fxData.VFXFolder);
  }

  // 5. 渲染右侧属性检查器
  renderEffectPropertyTree(fxData);
}

function renderEffectList() {
  const container = document.getElementById("effectList");
  const countBadge = document.getElementById("effectCountBadge");
  if (!container) return;
  container.innerHTML = "";

  const hitEffects = state.current.hit_effects || {};
  const effectEntries = Object.entries(hitEffects);
  if (countBadge) countBadge.textContent = `${effectEntries.length} 个特效`;

  const typeIcons = {
    "MuzzleFlash": "🔥",
    "HitImpact": "💥",
    "DeathExplosion": "💣",
    "AreaField": "☣️",
    "TrailFX": "✨"
  };

  effectEntries.forEach(([fxId, fx]) => {
    const item = document.createElement("div");
    item.className = `effect-item ${fxId === state.selectedEffectId ? 'active' : ''}`;
    const icon = typeIcons[fx.EffectType] || "✨";

    item.innerHTML = `
      <div class="effect-item-icon">${icon}</div>
      <div class="effect-item-info">
        <div class="effect-item-name">${fx.DisplayName || fxId}</div>
        <div class="effect-item-id">${fxId} | ${fx.EffectType || 'FX'}</div>
      </div>
      <button class="btn btn-secondary btn-sm" style="padding: 2px 6px; font-size: 10px; color: #f43f5e;" title="删除此特效" onclick="event.stopPropagation(); deleteEffect('${fxId}')">
        &times;
      </button>
    `;

    item.onclick = () => {
      switchSelectedEffect(fxId);
    };

    container.appendChild(item);
  });
}

function switchSelectedEffect(fxId) {
  state.selectedEffectId = fxId;
  state.effectFrameIdx = 0;
  renderEffectsStudio();
}

async function loadEffectFrames(folder) {
  try {
    const res = await fetch(`/api/vfx-frames?folder=${encodeURIComponent(folder)}`);
    const data = await res.json();
    if (data.status === "success" && data.frames) {
      state.effectFrames = data.frames;
      const countEl = document.getElementById("effectFramesCountBadge");
      if (countEl) countEl.textContent = `${data.frames.length} 帧序列`;

      renderEffectFilmstrip();
      startEffectAnimation();
    }
  } catch (err) {
    console.error("加载特效帧序列失败:", err);
  }
}

function startEffectAnimation() {
  if (state.effectAnimInterval) {
    clearInterval(state.effectAnimInterval);
    state.effectAnimInterval = null;
  }

  const spriteEl = document.getElementById("effectLiveSprite");
  const frameIndicator = document.getElementById("effectFrameIndicator");
  const scaleIndicator = document.getElementById("effectScaleIndicator");
  const fpsIndicator = document.getElementById("effectFpsIndicator");
  const spriteWrap = document.getElementById("effectSpriteWrap");

  if (!spriteEl || !state.effectFrames || state.effectFrames.length === 0) return;

  if (spriteWrap) {
    spriteWrap.style.transform = `scale(${state.effectScale})`;
  }
  if (scaleIndicator) scaleIndicator.textContent = `SCALE: ${state.effectScale.toFixed(2)}x`;
  if (fpsIndicator) fpsIndicator.textContent = `${state.effectFPS.toFixed(1)} FPS`;

  const intervalMs = Math.max(30, 1000 / (state.effectFPS || 12.0));

  const updateFrame = () => {
    if (state.effectIsHitStopping) return; // 顿帧期间跳过换帧

    const currentFrame = state.effectFrames[state.effectFrameIdx];
    if (currentFrame) {
      spriteEl.src = `/art/${currentFrame}`;
    }

    if (frameIndicator) {
      frameIndicator.textContent = `FRAME: ${state.effectFrameIdx + 1}/${state.effectFrames.length}`;
    }

    // 胶卷帧高亮
    document.querySelectorAll(".filmstrip-item").forEach((fEl, idx) => {
      if (idx === state.effectFrameIdx) fEl.classList.add("active");
      else fEl.classList.remove("active");
    });

    state.effectFrameIdx = (state.effectFrameIdx + 1) % state.effectFrames.length;
  };

  updateFrame();
  state.effectAnimInterval = setInterval(updateFrame, intervalMs);
}

function renderEffectFilmstrip() {
  const container = document.getElementById("effectFilmstrip");
  if (!container) return;
  container.innerHTML = "";

  (state.effectFrames || []).forEach((framePath, idx) => {
    const item = document.createElement("div");
    item.className = `filmstrip-item ${idx === state.effectFrameIdx ? 'active' : ''}`;
    item.innerHTML = `
      <img src="/art/${framePath}" alt="帧${idx + 1}" />
      <span class="frame-num">${idx + 1}</span>
    `;

    item.onclick = () => {
      state.effectFrameIdx = idx;
      const spriteEl = document.getElementById("effectLiveSprite");
      if (spriteEl) spriteEl.src = `/art/${framePath}`;
      const frameIndicator = document.getElementById("effectFrameIndicator");
      if (frameIndicator) frameIndicator.textContent = `FRAME: ${idx + 1}/${state.effectFrames.length}`;
    };

    container.appendChild(item);
  });
}

function handleEffectFpsSlider(val) {
  const fps = parseFloat(val) || 12.0;
  state.effectFPS = fps;
  document.getElementById("effectFpsDisplay").textContent = `${fps.toFixed(1)} FPS`;
  updateEffectParam(state.selectedEffectId, "FPS", fps);
  startEffectAnimation();
}

function handleEffectScaleSlider(val) {
  const scale = parseFloat(val) || 0.45;
  state.effectScale = scale;
  document.getElementById("effectScaleDisplay").textContent = `${scale.toFixed(2)}x`;
  const spriteWrap = document.getElementById("effectSpriteWrap");
  if (spriteWrap) spriteWrap.style.transform = `scale(${scale})`;
  const scaleIndicator = document.getElementById("effectScaleIndicator");
  if (scaleIndicator) scaleIndicator.textContent = `SCALE: ${scale.toFixed(2)}x`;
  updateEffectParam(state.selectedEffectId, "Scale", scale);
}

// 核心功能：模拟打击感测试 (顿帧 HitStop 与 摄像机震屏 CameraShake 物理响应)
function triggerHitImpactTest() {
  const fx = state.current.hit_effects ? state.current.hit_effects[state.selectedEffectId] : null;
  if (!fx) return;

  const hitStopMs = fx.HitStopDurationMs !== undefined ? fx.HitStopDurationMs : 30;
  const shakeIntensity = fx.CameraShakeIntensity !== undefined ? fx.CameraShakeIntensity : 0.25;

  const viewport = document.getElementById("effectViewport");
  const hitStopBadge = document.getElementById("effectHitStopIndicator");

  // 1. 触发顿帧打击感暂停
  state.effectIsHitStopping = true;
  if (viewport) {
    viewport.classList.add("hit-stopping");
  }
  if (hitStopBadge) {
    hitStopBadge.style.display = "inline-block";
  }

  setTimeout(() => {
    // 2. 顿帧结束，恢复动画换帧
    state.effectIsHitStopping = false;
    if (viewport) viewport.classList.remove("hit-stopping");
    if (hitStopBadge) hitStopBadge.style.display = "none";

    // 3. 触发真实摄像机震屏 (根据 CameraShakeIntensity 动态调整震幅)
    if (viewport) {
      viewport.classList.remove("shaking");
      void viewport.offsetWidth; // 触发重绘
      viewport.classList.add("shaking");
      viewport.style.animationDuration = `${Math.min(0.6, Math.max(0.2, shakeIntensity * 1.5))}s`;

      setTimeout(() => {
        viewport.classList.remove("shaking");
      }, 500);
    }

    showToast(`💥 打击感触发: 顿帧 ${hitStopMs}ms | 震屏幅度 ${shakeIntensity.toFixed(2)}x (模拟UE5战斗反馈)`);
  }, Math.max(20, hitStopMs));
}

function renderEffectPropertyTree(fxData) {
  const container = document.getElementById("effectPropsTree");
  if (!container) return;
  container.innerHTML = "";

  const effectTypes = ["HitImpact", "MuzzleFlash", "DeathExplosion", "AreaField", "TrailFX"];
  const typeOptions = effectTypes.map(t => `<option value="${t}" ${fxData.EffectType === t ? 'selected' : ''}>${t}</option>`).join("");

  const props = [
    {
      key: "DisplayName",
      label: "特效显示名称 (DisplayName)",
      type: "string",
      value: fxData.DisplayName || "",
      desc: "战斗界面与编辑器中呈现的中文名称"
    },
    {
      key: "EffectType",
      label: "特效类型分类 (EffectType)",
      type: "select",
      options: typeOptions,
      value: fxData.EffectType || "HitImpact",
      desc: "枪火/击中/死亡爆炸/区域毒雾/拖尾"
    },
    {
      key: "VFXFolder",
      label: "美术切片资源目录 (VFXFolder)",
      type: "asset_folder",
      value: fxData.VFXFolder || "",
      desc: "对应 Content/美术/Art/05_VFX/ 下的切片序列目录"
    },
    {
      key: "FPS",
      label: "动画步频播放帧率 (FPS)",
      type: "number",
      step: 1,
      value: fxData.FPS !== undefined ? fxData.FPS : 12.0,
      desc: "每秒播放帧数，控制特效绽放与消失快慢"
    },
    {
      key: "Scale",
      label: "视口放映与游戏内缩放 (Scale)",
      type: "number",
      step: 0.05,
      value: fxData.Scale !== undefined ? fxData.Scale : 0.45,
      desc: "在 9:16 正交视口下的体型大小倍率"
    },
    {
      key: "LifeDuration",
      label: "生命周期秒数 (LifeDuration s)",
      type: "number",
      step: 0.05,
      value: fxData.LifeDuration !== undefined ? fxData.LifeDuration : 0.35,
      desc: "特效 Actor 生成后在关卡中存活的最长时间"
    },
    {
      key: "HitStopDurationMs",
      label: "动作打击顿帧时间 (HitStop ms)",
      type: "number",
      step: 5,
      value: fxData.HitStopDurationMs !== undefined ? fxData.HitStopDurationMs : 30,
      desc: "命中敌人瞬间画面定格时间，制造沉重刀刀到肉感 (0~100ms)"
    },
    {
      key: "CameraShakeIntensity",
      label: "摄像机震屏幅度 (CameraShakeIntensity)",
      type: "number",
      step: 0.05,
      value: fxData.CameraShakeIntensity !== undefined ? fxData.CameraShakeIntensity : 0.25,
      desc: "触发时对正交相机的剧烈抖动幅度 (0.0~1.0)"
    }
  ];

  props.forEach(p => {
    const row = document.createElement("div");
    row.className = "prop-row";

    let inputHtml = "";
    if (p.type === "select") {
      inputHtml = `
        <select class="prop-asset-select" onchange="updateEffectParam('${state.selectedEffectId}', '${p.key}', this.value)">
          ${p.options}
        </select>
      `;
    } else if (p.type === "asset_folder") {
      inputHtml = `
        <div style="display: flex; gap: 6px; width: 100%;">
          <input type="text" class="input-text" style="flex: 1;" value="${p.value}" onchange="updateEffectParam('${state.selectedEffectId}', '${p.key}', this.value); loadEffectFrames(this.value);" />
          <button class="btn btn-secondary btn-sm glow-cyan" onclick="openAssetPickerForCurrentEffectFolder()">
            📁 挑目录
          </button>
        </div>
      `;
    } else {
      const isNum = p.type === "number";
      inputHtml = `
        <input type="${isNum ? 'number' : 'text'}" class="input-text" value="${p.value}" ${isNum ? `step="${p.step || 'any'}"` : ''} onchange="updateEffectParam('${state.selectedEffectId}', '${p.key}', ${isNum ? 'parseFloat(this.value)||0' : 'this.value'})" />
      `;
    }

    row.innerHTML = `
      <div class="prop-label-group">
        <span class="prop-label">${p.label}</span>
        <span class="prop-desc">${p.desc}</span>
      </div>
      <div class="prop-input-wrap">
        ${inputHtml}
      </div>
    `;

    container.appendChild(row);
  });
}

function updateEffectParam(fxId, key, val) {
  const fx = state.current.hit_effects ? state.current.hit_effects[fxId] : null;
  if (!fx) return;

  fx[key] = val;
  updateDiffState();

  if (key === "DisplayName") {
    const titleEl = document.getElementById("currentEffectTitle");
    if (titleEl) titleEl.textContent = `${val} (${fxId})`;
    renderEffectList();
  } else if (key === "EffectType") {
    const typeBadgeEl = document.getElementById("effectTypeBadge");
    if (typeBadgeEl) typeBadgeEl.textContent = val;
    renderEffectList();
  }
}

function openAssetPickerForCurrentEffectFolder() {
  const fx = state.current.hit_effects ? state.current.hit_effects[state.selectedEffectId] : null;
  if (!fx) return;

  openAssetBrowser({
    title: `为特效【${fx.DisplayName}】挑选切片目录 (05_VFX)`,
    currentVal: fx.VFXFolder || "",
    filterDir: "05_VFX",
    mode: "folder",
    onSelect: (selectedFolder) => {
      fx.VFXFolder = selectedFolder;
      updateEffectParam(state.selectedEffectId, "VFXFolder", selectedFolder);
      loadEffectFrames(selectedFolder);
      renderEffectsStudio();
      showToast(`👁️ 特效切片目录已切换为: ${selectedFolder}（草稿预览中，点击右上角【保存修改】后生效）`);
    }
  });
}

function deleteEffect(fxId) {
  if (confirm(`确定要从战斗特效表 (DT_HitEffects) 中删除【${fxId}】吗？`)) {
    delete state.current.hit_effects[fxId];
    renderEffectsStudio();
    renderDataTable();
    updateDiffState();
    showToast(`🗑️ 已删除战斗特效: ${fxId}`);
  }
}

function renderCardsGrid() {
  const container = document.getElementById("cardsGrid");
  container.innerHTML = "";

  const cards = state.current.cards || {};
  Object.entries(cards).forEach(([cid, c]) => {
    const item = document.createElement("div");
    item.className = "tactical-card-item";

    let cardImg = "";
    if (c.ArtInfo && c.ArtInfo.card_image) {
      cardImg = `<img src="/art/${c.ArtInfo.card_image}" alt="${c.DisplayName}" />`;
    }

    item.innerHTML = `
      <div class="card-art-box">${cardImg}</div>
      <div class="card-content">
        <span class="card-rarity ${c.Rarity}">${c.Rarity}</span>
        <h4 style="color: #fff; font-size: 13px;">${c.DisplayName}</h4>
        <p style="font-size: 11px; color: #94a3b8; margin: 3px 0;">${c.Description}</p>
        <div style="font-size: 11px; color: #10b981; font-family: var(--font-mono);">
          增益倍率: x${c.Value} (${c.TargetStat})
        </div>
      </div>
    `;

    container.appendChild(item);
  });
}

// ==============================================================================
// 5. 关卡波次推进
// ==============================================================================
function renderWaveTimeline() {
  const body = document.getElementById("waveTimelineBody");
  const tableBody = document.getElementById("waveDataTable").querySelector("tbody");
  body.innerHTML = "";
  tableBody.innerHTML = "";

  const waveData = state.current.waves && state.current.waves.Stage_01_Main ? state.current.waves.Stage_01_Main.Waves : [];
  const totalDuration = 40.0;

  for (let t = 0; t <= totalDuration; t += 5) {
    const leftPct = (t / totalDuration) * 100;
    const tick = document.createElement("div");
    tick.className = "timeline-tick-line";
    tick.style.left = `${leftPct}%`;
    body.appendChild(tick);

    const lbl = document.createElement("div");
    lbl.className = "timeline-tick-label";
    lbl.style.left = `${leftPct}%`;
    lbl.textContent = `${t}s`;
    body.appendChild(lbl);
  }

  const laneColors = ["#38bdf8", "#10b981", "#f59e0b", "#ef4444"];
  waveData.forEach((w) => {
    const leftPct = (w.TimeOffset / totalDuration) * 100;
    const topPos = 16 + w.LaneIndex * 24;
    const pill = document.createElement("div");
    pill.className = "wave-event-pill";
    pill.style.left = `${leftPct}%`;
    pill.style.top = `${topPos}px`;
    pill.style.backgroundColor = laneColors[w.LaneIndex % 4];

    let enemyName = w.EnemyType.replace("Enemy_", "").replace("Boss_", "👑 ");
    pill.innerHTML = `<span>${w.Count}x ${enemyName}</span>`;
    body.appendChild(pill);

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${w.TimeOffset}s</td>
      <td><span class="lane-dot l${w.LaneIndex}"></span>Lane ${w.LaneIndex}</td>
      <td><strong>${w.EnemyType}</strong></td>
      <td>${w.Count} 只</td>
      <td>${w.Interval}s</td>
      <td>${w.DangerAlert ? '<span style="color:#ef4444; font-weight:bold;">⚠️ 警报</span>' : '常规'}</td>
    `;
    tableBody.appendChild(tr);
  });
}

// ==============================================================================
// 6. 快捷平衡批处理
// ==============================================================================
function batchScaleEnemyHP(multiplier) {
  const enemies = state.current.enemies || {};
  Object.values(enemies).forEach(e => {
    e.MaxHealth = Math.round(e.MaxHealth * multiplier);
  });
  renderEnemyDetail();
  renderDataTable();
  updateDiffState();
  showToast(`⚡ 全体怪物生命值已调整 x${multiplier}！`);
}

function batchScaleEnemySpeed(multiplier) {
  const enemies = state.current.enemies || {};
  Object.values(enemies).forEach(e => {
    e.MoveSpeed = Math.round(e.MoveSpeed * multiplier);
  });
  renderEnemyDetail();
  renderDataTable();
  updateDiffState();
  showToast(`⚡ 全体怪物移动速度已调整 x${multiplier}！`);
}

function boostPlayerStats() {
  const p = state.current.characters[state.selectedPlayerId];
  if (p) {
    p.MaxHealth = (p.MaxHealth || 1200) + 300;
    p.Armor = (p.Armor || 15) + 10;
    p.MoveSpeed = (p.MoveSpeed || 350) + 30;
    renderPlayerStudio();
    updateDiffState();
    showToast("⚡ 主角基础体魄与机动已全面增强！");
  }
}

function resetCurrentConfig() {
  if (!state.original) return;
  state.current = JSON.parse(JSON.stringify(state.original));
  renderAllViews();
  showToast("🔄 已恢复未保存的原始数据");
}

// ==============================================================================
// 7. 属性 Diff 与直接提交
// ==============================================================================
function getDiffSummary() {
  const diffs = [];
  if (!state.original || !state.current) return diffs;

  // 1. 比较主角
  const origChars = state.original.characters || {};
  const currChars = state.current.characters || {};
  Object.keys(currChars).forEach(cId => {
    const cc = currChars[cId];
    const oc = origChars[cId] || {};
    ["DisplayName", "Avatar", "MaxHealth", "MoveSpeed", "Armor", "CritChance", "CritMultiplier", "PickupRadius", "DefaultWeaponID", "SecondaryWeaponID", "TacticalCooldown"].forEach(prop => {
      if (cc[prop] !== oc[prop]) {
        diffs.push({
          category: "主角角色属性",
          target: cc.DisplayName || cId,
          property: prop,
          oldVal: oc[prop],
          newVal: cc[prop]
        });
      }
    });
    // 特效比较
    const cVFX = cc.VFX || {};
    const oVFX = oc.VFX || {};
    ["HitVFX", "SkillVFX", "MuzzleVFX", "DashVFX"].forEach(vp => {
      if (cVFX[vp] !== oVFX[vp]) {
        diffs.push({
          category: "主角特效配置",
          target: cc.DisplayName || cId,
          property: vp,
          oldVal: oVFX[vp],
          newVal: cVFX[vp]
        });
      }
    });
  });

  // 2. 比较敌人
  const origE = state.original.enemies || {};
  const currE = state.current.enemies || {};
  Object.keys(currE).forEach(eid => {
    const ce = currE[eid];
    const oe = origE[eid] || {};
    Object.keys(ce).forEach(prop => {
      if (prop !== "ArtInfo" && ce[prop] !== oe[prop]) {
        diffs.push({
          category: "敌人蓝图属性",
          target: ce.DisplayName || eid,
          property: prop,
          oldVal: oe[prop],
          newVal: ce[prop]
        });
      }
    });
  });

  // 3. 比较武器与子弹全属性
  const origW = state.original.weapons || {};
  const currW = state.current.weapons || {};
  Object.keys(currW).forEach(wid => {
    const cw = currW[wid];
    const ow = origW[wid] || {};
    Object.keys(cw).forEach(prop => {
      if (prop !== "ArtInfo" && cw[prop] !== ow[prop]) {
        diffs.push({
          category: "武器与子弹属性",
          target: cw.DisplayName || wid,
          property: prop,
          oldVal: ow[prop] !== undefined ? ow[prop] : "未配置",
          newVal: cw[prop]
        });
      }
    });
  });

  // 4. 比较土地地块
  const origT = state.original.tiles || {};
  const currT = state.current.tiles || {};
  Object.keys(currT).forEach(tid => {
    const ct = currT[tid];
    const ot = origT[tid] || {};
    Object.keys(ct).forEach(prop => {
      if (ct[prop] !== ot[prop]) {
        diffs.push({
          category: "土地地块属性",
          target: ct.DisplayName || tid,
          property: prop,
          oldVal: ot[prop] !== undefined ? ot[prop] : "未配置",
          newVal: ct[prop]
        });
      }
    });
  });

  // 5. 比较战斗特效 (DT_HitEffects)
  const origFX = state.original.hit_effects || {};
  const currFX = state.current.hit_effects || {};
  Object.keys(currFX).forEach(fxId => {
    const cfx = currFX[fxId];
    const ofx = origFX[fxId] || {};
    Object.keys(cfx).forEach(prop => {
      if (cfx[prop] !== ofx[prop]) {
        diffs.push({
          category: "战斗特效配置",
          target: cfx.DisplayName || fxId,
          property: prop,
          oldVal: ofx[prop] !== undefined ? ofx[prop] : "未配置",
          newVal: cfx[prop]
        });
      }
    });
  });

  return diffs;
}

function updateDiffState() {
  const diffs = getDiffSummary();
  const syncBox = document.getElementById("syncStatusBox");
  const syncText = document.getElementById("syncStatusText");
  const btnDiscard = document.getElementById("btnDiscardAllChanges");
  const btnCommitText = document.getElementById("btnCommitText");

  if (diffs.length > 0) {
    if (syncBox) {
      syncBox.className = "sync-status-box is-draft";
      syncText.innerHTML = `🟡 <strong>调试草稿预览中</strong>（${diffs.length} 项未保存改动 · 仅视口预览，未写入磁盘）`;
    }
    if (btnDiscard) btnDiscard.style.display = "inline-flex";
    if (btnCommitText) btnCommitText.textContent = `保存修改并生效 (${diffs.length})`;
  } else {
    if (syncBox) {
      syncBox.className = "sync-status-box is-synced";
      syncText.innerHTML = `🟢 <strong>磁盘数据已就绪</strong>（当前配置已生效）`;
    }
    if (btnDiscard) btnDiscard.style.display = "none";
    if (btnCommitText) btnCommitText.textContent = `保存修改并生效`;
  }
}

// 7.1 全局放弃所有未保存修改 (还原磁盘原始数据)
function discardAllChanges() {
  const diffs = getDiffSummary();
  if (diffs.length === 0) {
    showToast("当前无任何未保存的草稿修改");
    return;
  }
  if (confirm(`确定要放弃当前 ${diffs.length} 项调试改动，完全还原为本地磁盘原始数据吗？\n\n注意：所有未保存的视口预览调整将全部重置回磁盘已有配置。`)) {
    state.current = JSON.parse(JSON.stringify(state.original));
    renderAllViews();
    showToast("🔄 已放弃全部未保存草稿，成功还原为本地磁盘原始数据！");
  }
}

// 7.2 仅放弃主角角色的未保存草稿
function discardPlayerChanges() {
  if (!state.original || !state.original.characters) return;
  if (confirm("确定要放弃当前角色的所有调试草稿，完全还原为磁盘原始数据吗？")) {
    state.current.characters = JSON.parse(JSON.stringify(state.original.characters));
    renderPlayerStudio();
    renderActionSlotsMatrix();
    updateDiffState();
    showToast("🔄 已将角色数据完全还原为磁盘生效配置！");
  }
}

// 7.3 仅放弃武器与子弹的未保存草稿
function discardWeaponsChanges() {
  if (!state.original || !state.original.weapons) return;
  if (confirm("确定要放弃武器与子弹物理的所有调试草稿，完全还原为磁盘原始数据吗？")) {
    state.current.weapons = JSON.parse(JSON.stringify(state.original.weapons));
    renderWeaponsGrid();
    updateDiffState();
    showToast("🔄 已将武器与子弹数据完全还原为磁盘生效配置！");
  }
}

// 7.4 仅放弃战斗特效的未保存草稿
function discardEffectsChanges() {
  if (!state.original || !state.original.hit_effects) return;
  if (confirm("确定要放弃战斗特效的所有调试草稿，完全还原为磁盘原始数据吗？")) {
    state.current.hit_effects = JSON.parse(JSON.stringify(state.original.hit_effects));
    renderEffectsStudio();
    updateDiffState();
    showToast("🔄 已将战斗特效数据完全还原为磁盘生效配置！");
  }
}

// 7.5 仅放弃怪物敌人的未保存草稿
function discardEnemiesChanges() {
  if (!state.original || !state.original.enemies) return;
  if (confirm("确定要放弃敌人的所有调试草稿，完全还原为磁盘原始数据吗？")) {
    state.current.enemies = JSON.parse(JSON.stringify(state.original.enemies));
    renderEnemyList();
    renderEnemyDetail();
    updateDiffState();
    showToast("🔄 已将怪物敌人数据完全还原为磁盘生效配置！");
  }
}

function openCommitModal() {
  const diffs = getDiffSummary();
  const modal = document.getElementById("commitModal");
  const listEl = document.getElementById("modalDiffList");

  if (diffs.length === 0) {
    listEl.innerHTML = '<div style="color: #94a3b8;">未检测到任何改动。您仍可强制提交重新保存。</div>';
  } else {
    listEl.innerHTML = diffs.map(d => `
      <div class="diff-entry">
        [${d.category}] <span class="key">${d.target}.${d.property}:</span> 
        <span class="old">${d.oldVal}</span> &rarr; <span class="new">${d.newVal}</span>
      </div>
    `).join("");
  }

  modal.classList.add("open");
}

function closeCommitModal() {
  document.getElementById("commitModal").classList.remove("open");
}

async function handleConfirmCommit() {
  const author = document.getElementById("commitAuthorInput").value.trim() || "策划/开发者";
  const comment = document.getElementById("commitNoteInput").value.trim() || "通过全实体配置中心微调提交";
  const diffs = getDiffSummary();

  const payload = {
    author,
    comment,
    raw_diff: diffs,
    characters: state.current.characters,
    enemies: state.current.enemies,
    weapons: state.current.weapons,
    cards: state.current.cards,
    waves: state.current.waves,
    tiles: state.current.tiles,
    hit_effects: state.current.hit_effects
  };

  try {
    const res = await fetch("/api/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (result.status === "success") {
      state.original = JSON.parse(JSON.stringify(state.current));
      updateDiffState();
      closeCommitModal();
      showToast("🎉 全实体属性与特效已成功原子化保存至工程！");
      loadCommits();
      renderPlayerStudio();
      renderEnemyDetail();
      renderTilesStudio();
      renderWeaponsGrid();
      renderEffectsStudio();
    } else {
      showToast(`❌ 保存失败: ${result.message}`, 4000);
    }
  } catch (err) {
    showToast(`❌ 网络请求异常: ${err}`, 4000);
  }
}

// ==============================================================================
// 8. 历史审计与一键 UE5 热部署
// ==============================================================================
async function loadCommits() {
  try {
    const res = await fetch("/api/commits");
    const data = await res.json();
    const listEl = document.getElementById("commitList");
    
    if (data.status === "success" && data.commits && data.commits.length > 0) {
      listEl.innerHTML = data.commits.map(c => `
        <div class="commit-item">
          <div class="commit-item-header">
            <strong>${c.author}</strong>
            <span style="color: #64748b;">${c.timestamp}</span>
          </div>
          <div class="commit-comment">${c.comment}</div>
          <div class="commit-tables">${(c.diff_summary || []).join(" | ")}</div>
        </div>
      `).join("");
    } else {
      listEl.innerHTML = '<div class="empty-hint">暂无提交记录</div>';
    }
  } catch (e) {
    console.error(e);
  }
}

async function handleDeployToUE5() {
  const btn = document.getElementById("btnDeployUE5");
  const statusText = document.getElementById("deployStatusText");
  const logBox = document.getElementById("deployLogBox");

  btn.disabled = true;
  statusText.textContent = "正在调用 UnrealEditor-Cmd 部署...";
  logBox.textContent = "启动 UE5 命令行引擎任务...\n";

  try {
    const res = await fetch("/api/deploy", { method: "POST" });
    const result = await res.json();
    
    statusText.textContent = result.message;
    logBox.textContent = result.output || result.message;
    if (result.status === "success") {
      showToast("🚀 UE5 关卡蓝图与实例部署成功！");
    } else {
      showToast("⚠️ UE5 部署已完成，请检查日志", 3000);
    }
  } catch (err) {
    statusText.textContent = "部署失败";
    logBox.textContent = `执行错误: ${err}`;
  } finally {
    btn.disabled = false;
  }
}

// ==============================================================================
// 9. 事件监听与辅助
// ==============================================================================
function setupEventListeners() {
  document.getElementById("btnCommitChanges").addEventListener("click", openCommitModal);
  document.getElementById("btnConfirmCommit").addEventListener("click", handleConfirmCommit);
  document.getElementById("btnDeployUE5").addEventListener("click", handleDeployToUE5);

  // 全局模态框防卡死交互：点击外部遮罩背景关闭 / 按 ESC 键关闭
  document.querySelectorAll(".modal-backdrop").forEach(backdrop => {
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove("open");
      }
    });
  });

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      document.querySelectorAll(".modal-backdrop.open").forEach(modal => {
        modal.classList.remove("open");
      });
    }
  });

  const playerFpsSlider = document.getElementById("playerFpsSlider");
  if (playerFpsSlider) {
    playerFpsSlider.addEventListener("input", (e) => {
      state.playerFPS = parseFloat(e.target.value);
      document.getElementById("playerFpsVal").textContent = `${state.playerFPS.toFixed(1)} FPS`;
      startPlayerAnimation();
    });
  }

  const fpsSlider = document.getElementById("fpsSlider");
  if (fpsSlider) {
    fpsSlider.addEventListener("input", (e) => {
      state.enemyFPS = parseFloat(e.target.value);
      document.getElementById("fpsValue").textContent = `${state.enemyFPS.toFixed(1)} FPS`;
      const enemy = state.current.enemies[state.selectedEnemyId];
      if (enemy) startEnemySpriteAnimation(enemy);
    });
  }

  const searchInput = document.getElementById("propSearchInput");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      state.enemySearchFilter = e.target.value;
      const enemy = state.current.enemies[state.selectedEnemyId];
      if (enemy) renderEnemyBlueprintPropertyTree(enemy);
    });
  }

  // 素材库搜索与确定绑定
  const assetSearchInput = document.getElementById("assetSearchInput");
  if (assetSearchInput) {
    assetSearchInput.addEventListener("input", (e) => handleAssetSearch(e.target.value));
  }

  const btnApply = document.getElementById("btnApplySelectedAsset");
  if (btnApply) {
    btnApply.addEventListener("click", applySelectedAsset);
  }

  // 1. 主角头像框直接拖入图片监听 (Universal Drag & Drop to Avatar)
  const avatarBox = document.getElementById("avatarBoxTrigger");
  if (avatarBox) {
    setupUniversalImageDrop(avatarBox, {
      category: "avatar",
      entityId: () => state.selectedPlayerId || "Player",
      label: "主角头像",
      onSuccess: (data) => {
        const charData = state.current.characters[state.selectedPlayerId];
        if (charData) {
          charData.Avatar = data.project_rel_path;
          const imgEl = document.getElementById("playerAvatarImg");
          if (imgEl) imgEl.src = data.web_url;
          renderPlayerPropertyTree(charData);
          updateDiffState();
        }
      }
    });
  }

  // 2. 素材库浏览器网格拖入文件监听 (Universal Drag & Drop to Asset Grid)
  const dropZone = document.getElementById("assetDropZone");
  if (dropZone) {
    setupUniversalImageDrop(dropZone, {
      category: () => {
        if (currentBrowserNode && currentBrowserNode.path) {
          const p = currentBrowserNode.path;
          if (p.includes("01_Player")) return "avatar";
          if (p.includes("03_Weapons")) return "weapon";
          if (p.includes("05_VFX")) return "vfx";
          if (p.includes("02_Enemies")) return "enemy";
          if (p.includes("07_UI")) return "ui";
        }
        return "general";
      },
      targetDir: () => currentBrowserNode ? currentBrowserNode.path : null,
      label: "素材库文件",
      onSuccess: async (data) => {
        await refreshAssetCatalog(false);
        if (typeof selectAssetInBrowser === "function") {
          selectAssetInBrowser(data.project_rel_path);
        }
      }
    });
  }

  // 3. 启动本地素材库热监听变动感知器
  startAssetWatcher();
}

let lastArtSystemMtime = 0;
function startAssetWatcher() {
  setInterval(async () => {
    try {
      const res = await fetch("/api/asset/watch-status");
      const json = await res.json();
      if (json.status === "success" && json.data) {
        const mtime = json.data.mtime;
        if (lastArtSystemMtime !== 0 && mtime > lastArtSystemMtime) {
          lastArtSystemMtime = mtime;
          const latestName = json.data.latest && json.data.latest.length > 0 ? json.data.latest[0] : "";
          showToast(`🎨 感知到本地文件夹有新素材拖入/变动 [${latestName}]，已自动同步！`, 3500);
          await refreshAssetCatalog(false);

          // 重新拉取数据以刷新候选头像
          const dataRes = await fetch("/api/data");
          const data = await dataRes.json();
          if (data.status === "success" && data.candidate_avatars) {
            state.current.candidate_avatars = data.candidate_avatars;
            if (state.current.characters && state.current.characters[state.selectedPlayerId]) {
              state.current.characters[state.selectedPlayerId].CandidateAvatars = data.candidate_avatars;
              renderCandidateAvatars(state.current.characters[state.selectedPlayerId]);
            }
          }
        } else {
          lastArtSystemMtime = mtime;
        }
      }
    } catch (e) {
      // 忽略后台轮询错误
    }
  }, 5000);
}

// ==============================================================================
// 10. 本地美术素材库浏览器核心系统 (Asset Browser Controller)
// ==============================================================================
let artCatalogCache = null;
let currentBrowserNode = null;
let selectedAssetForQuickAction = null;
let assetPickerConfig = {
  active: false,
  title: "",
  currentVal: "",
  filterDir: "",
  mode: "file", // "file" | "folder"
  onSelect: null,
  selectedItem: null
};

async function fetchAssetCatalog(force = false) {
  if (artCatalogCache && !force) return artCatalogCache;
  try {
    const url = force ? "/api/asset/refresh" : "/api/art-tree";
    const res = await fetch(url);
    const data = await res.json();
    if (data.status === "success") {
      artCatalogCache = data;
      return artCatalogCache;
    }
  } catch (e) {
    console.error("加载素材库失败:", e);
    showToast("⚠️ 加载素材库失败");
  }
  return null;
}

async function refreshAssetCatalog(showToastNotice = true) {
  const data = await fetchAssetCatalog(true);
  if (!data) return;
  if (assetPickerConfig && assetPickerConfig.active) {
    renderAssetTree(data.tree, assetPickerConfig.filterDir);
    if (currentBrowserNode) {
      const refreshedNode = findTreeNodeByPath(data.tree, currentBrowserNode.path) || currentBrowserNode;
      currentBrowserNode = refreshedNode;
      renderAssetGrid(refreshedNode.files || [], refreshedNode.path, refreshedNode);
    } else if (data.tree && data.tree.length > 0) {
      renderAssetGrid(data.tree[0].files || [], data.tree[0].path, data.tree[0]);
    }
  }
  if (showToastNotice) {
    showToast(`🔄 素材库已刷新！共感知到 ${data.total || data.total_count} 项切片资产`);
  }
}

async function quickSetAsAvatar() {
  const path = selectedAssetForQuickAction || (assetPickerConfig ? assetPickerConfig.selectedItem : null);
  if (!path) {
    showToast("⚠️ 请先在网格中点击选中一张切片图片！");
    return;
  }
  try {
    showToast("⏳ 正在设为主角头像并规范化落盘...");
    const res = await fetch("/api/asset/auto-process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "set_avatar",
        path: path,
        normalize: true
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      const charData = state.current.characters[state.selectedPlayerId];
      if (charData) {
        charData.Avatar = data.avatar_path;
        document.getElementById("playerAvatarImg").src = data.avatar_url;
        renderPlayerPropertyTree(charData);
        updateDiffState();
      }
      showToast(`🎉 头像已一键更新为：${data.avatar_path}！`);
      closeAssetBrowser();
    } else {
      showToast(`❌ 处理失败: ${data.error || "未知错误"}`);
    }
  } catch (e) {
    showToast(`❌ 请求异常: ${e}`);
  }
}

async function quickRemoveBlack() {
  const path = selectedAssetForQuickAction || (assetPickerConfig ? assetPickerConfig.selectedItem : null);
  if (!path) {
    showToast("⚠️ 请先在网格中点击选中一张切片图片！");
    return;
  }
  try {
    showToast("⏳ 正在去除黑底并生成透明通道...");
    const res = await fetch("/api/asset/auto-process", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "remove_black",
        path: path,
        threshold: 25
      })
    });
    const data = await res.json();
    if (data.status === "success") {
      showToast("🪄 去黑底成功，已生成透明PNG并刷新素材库！");
      await refreshAssetCatalog(false);
    } else {
      showToast(`❌ 去黑底失败: ${data.error || "未知错误"}`);
    }
  } catch (e) {
    showToast(`❌ 请求异常: ${e}`);
  }
}

function quickSendToSlicePipeline() {
  const path = selectedAssetForQuickAction || (assetPickerConfig ? assetPickerConfig.selectedItem : null);
  if (!path) {
    showToast("⚠️ 请先在网格中点击选中一张切片图片！");
    return;
  }
  closeAssetBrowser();
  const tabBtn = document.querySelector('.tab-btn[data-tab="tab-asset-pipeline"]');
  if (tabBtn) tabBtn.click();
  const input = document.getElementById("sliceImgPath");
  if (input) {
    input.value = path;
    if (typeof loadSlicePreview === "function") loadSlicePreview();
  }
  showToast(`✂️ 已载入素材 [${path}] 至切片工坊！`);
}

function triggerAssetFileUpload() {
  const fileInput = document.getElementById("assetBrowserFileInput");
  if (fileInput) fileInput.click();
}

async function handleAssetFileSelected(event) {
  const files = event.target.files;
  if (!files || files.length === 0) return;
  const file = files[0];
  const targetDir = currentBrowserNode ? currentBrowserNode.path : "01_Player/touxiang";
  await uploadAndProcessFile(file, targetDir);
  event.target.value = "";
}

async function uploadAndProcessFile(file, targetDir, autoProcess = "") {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64Data = e.target.result;
      try {
        showToast(`📤 正在上传 [${file.name}] 到 ${targetDir}...`);
        const res = await fetch("/api/asset/upload", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            target_dir: targetDir,
            filename: file.name,
            file_base64: base64Data,
            auto_process: autoProcess
          })
        });
        const data = await res.json();
        if (data.status === "success") {
          showToast(`✅ [${file.name}] 存入成功并自动感知！`);
          await refreshAssetCatalog(false);
          resolve(data);
        } else {
          showToast(`❌ 上传失败: ${data.error || "未知错误"}`);
          reject(data);
        }
      } catch (err) {
        showToast(`❌ 网络请求失败: ${err}`);
        reject(err);
      }
    };
    reader.readAsDataURL(file);
  });
}

async function openAssetBrowser({ title = "选择本地美术资产", currentVal = "", filterDir = "", mode = "file", onSelect = null }) {
  let initSelected = currentVal || "";
  if (mode === "folder" && initSelected && (initSelected.endsWith(".png") || initSelected.endsWith(".jpg"))) {
    initSelected = initSelected.substring(0, initSelected.lastIndexOf("/"));
  }

  selectedAssetForQuickAction = null;
  const quickToolbar = document.getElementById("assetQuickActionToolbar");
  if (quickToolbar) quickToolbar.style.display = "none";

  assetPickerConfig = {
    active: true,
    title,
    currentVal: initSelected,
    filterDir: filterDir || initSelected,
    mode,
    onSelect,
    selectedItem: initSelected
  };

  const modal = document.getElementById("assetBrowserModal");
  document.getElementById("assetBrowserTargetDesc").textContent = title;
  
  const displayEl = document.getElementById("selectedAssetPathDisplay");
  if (displayEl) {
    if (mode === "folder" && initSelected) {
      displayEl.innerHTML = `<span style="color:#38bdf8; font-weight:bold;">📁 [已选目录]</span> ${initSelected}`;
    } else {
      displayEl.textContent = initSelected || "未选择";
    }
  }

  document.getElementById("assetSearchInput").value = "";
  modal.classList.add("open");

  // 每次打开优先从后端刷新获取最新素材（确保手动拖入的文件瞬间被展示）
  const catalog = await fetchAssetCatalog(true);
  if (!catalog) return;

  // 渲染分类树
  renderAssetTree(artCatalogCache.tree, assetPickerConfig.filterDir);

  // 定位与渲染资产网格
  let targetNode = null;
  const searchDir = assetPickerConfig.filterDir;
  if (searchDir) {
    targetNode = findTreeNodeByPath(artCatalogCache.tree, searchDir);
    if (!targetNode) {
      // 尝试取父级路径
      const pDir = searchDir.substring(0, searchDir.lastIndexOf("/"));
      if (pDir) targetNode = findTreeNodeByPath(artCatalogCache.tree, pDir);
    }
  }

  if (!targetNode && artCatalogCache.tree && artCatalogCache.tree.length > 0) {
    targetNode = artCatalogCache.tree[0];
  }

  if (targetNode) {
    currentBrowserNode = targetNode;
    // 如果初始未设置 selectedItem，默认给当前定位目录
    if (mode === "folder" && !assetPickerConfig.selectedItem) {
      assetPickerConfig.selectedItem = targetNode.path;
      if (displayEl) {
        displayEl.innerHTML = `<span style="color:#38bdf8; font-weight:bold;">📁 [已选目录]</span> ${targetNode.path} <span style="color:#94a3b8; font-size:11px;">(${targetNode.files ? targetNode.files.length : 0} 帧)</span>`;
      }
    }
    renderAssetGrid(targetNode.files || [], targetNode.path, targetNode);
  } else if (artCatalogCache.all_files) {
    renderAssetGrid(artCatalogCache.all_files.slice(0, 100), "全部素材 (前100项)", null);
  }
}

function closeAssetBrowser() {
  const modal = document.getElementById("assetBrowserModal");
  modal.classList.remove("open");
  assetPickerConfig.active = false;
  // 隐藏横幅
  const banner = document.getElementById("currentFolderActionBanner");
  if (banner) banner.style.display = "none";
}

function findTreeNodeByPath(tree, path) {
  if (!tree || !path) return null;
  for (const node of tree) {
    if (node.path === path) return node;
    if (path.startsWith(node.path + "/")) {
      const found = findTreeNodeByPath(node.dirs || [], path);
      if (found) return found;
      return node;
    }
  }
  return null;
}

function renderAssetTree(tree, activePath) {
  const container = document.getElementById("assetTreeList");
  container.innerHTML = "";

  function buildTreeDOM(nodes, level = 0) {
    const listWrap = document.createElement("div");
    listWrap.className = level === 0 ? "" : "tree-children";

    nodes.forEach(node => {
      const row = document.createElement("div");
      const hasChildren = node.dirs && node.dirs.length > 0;
      const fileCount = node.files ? node.files.length : 0;
      const isCurrentSelected = assetPickerConfig.selectedItem === node.path;
      const isActive = activePath && (activePath === node.path || activePath.startsWith(node.path + "/"));

      row.className = `tree-node ${isActive ? "active" : ""} ${isCurrentSelected ? "selected-folder" : ""}`;
      row.style.paddingLeft = `${level * 14 + 8}px`;

      const icon = hasChildren ? "📂" : "📁";
      row.innerHTML = `
        <span class="tree-node-icon">${icon}</span>
        <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${node.path}">${node.name}</span>
        ${fileCount > 0 ? `<span class="tree-node-badge">${fileCount}</span>` : ''}
        ${assetPickerConfig.mode === "folder" ? `<button class="tree-node-select-btn" type="button" title="点击立即选定并绑定此目录">选目录</button>` : ''}
      `;

      row.onclick = (e) => {
        if (e.target.tagName === "BUTTON") {
          assetPickerConfig.selectedItem = node.path;
          applySelectedAsset();
          return;
        }

        document.querySelectorAll(".tree-node").forEach(n => n.classList.remove("active", "selected-folder"));
        row.classList.add("active");
        currentBrowserNode = node;

        // 若处于选目录模式，点击整行直接识别为当前选中的目录！
        if (assetPickerConfig.mode === "folder") {
          row.classList.add("selected-folder");
          assetPickerConfig.selectedItem = node.path;
          const displayEl = document.getElementById("selectedAssetPathDisplay");
          if (displayEl) {
            displayEl.innerHTML = `<span style="color:#38bdf8; font-weight:bold;">📁 [已选目录]</span> ${node.path} <span style="color:#94a3b8; font-size:11px;">(${fileCount} 帧切片)</span>`;
          }
        }

        renderAssetGrid(node.files || [], node.path, node);
      };

      listWrap.appendChild(row);

      if (hasChildren) {
        const childDOM = buildTreeDOM(node.dirs, level + 1);
        listWrap.appendChild(childDOM);
      }
    });

    return listWrap;
  }

  container.appendChild(buildTreeDOM(tree));
}

function renderAssetGrid(files, breadcrumb, node) {
  const grid = document.getElementById("assetGrid");
  const breadcrumbEl = document.getElementById("currentFolderBreadcrumb");
  const countEl = document.getElementById("assetMatchCount");

  breadcrumbEl.textContent = `Content/美术/Art/${breadcrumb || ''}`;
  countEl.textContent = `${files.length} 项素材`;
  grid.innerHTML = "";

  // 选目录模式特权：在网格顶部渲染醒目的大号一键确认横幅操作栏
  const parentPanel = grid.parentElement;
  let bannerEl = document.getElementById("currentFolderActionBanner");
  if (assetPickerConfig.mode === "folder" && breadcrumb && !breadcrumb.startsWith("搜索结果")) {
    if (!bannerEl) {
      bannerEl = document.createElement("div");
      bannerEl.id = "currentFolderActionBanner";
      parentPanel.insertBefore(bannerEl, grid);
    }
    bannerEl.className = "folder-action-banner";
    bannerEl.style.display = "flex";
    bannerEl.innerHTML = `
      <div class="banner-info">
        <span class="banner-icon">📁</span>
        <div>
          <div class="banner-title">当前目录：<strong>${breadcrumb}</strong></div>
          <div class="banner-sub">包含 <strong>${files.length}</strong> 张序列帧切片</div>
        </div>
      </div>
      <button class="btn btn-primary btn-sm glow-cyan" type="button" id="btnQuickConfirmFolder" style="font-weight: 600; padding: 6px 14px;">
        ✅ 立即绑定此目录 (${files.length} 帧)
      </button>
    `;

    document.getElementById("btnQuickConfirmFolder").onclick = () => {
      assetPickerConfig.selectedItem = breadcrumb;
      applySelectedAsset();
    };
  } else if (bannerEl) {
    bannerEl.style.display = "none";
  }

  if (files.length === 0) {
    grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 40px; color: #64748b; font-size: 13px;">该目录下暂无直接图片素材（可展开左侧子目录浏览）</div>';
    return;
  }

  files.forEach(f => {
    const card = document.createElement("div");
    const isSelected = assetPickerConfig.selectedItem === f.path || (assetPickerConfig.mode === "folder" && assetPickerConfig.selectedItem === breadcrumb);
    card.className = `asset-card ${isSelected ? "selected" : ""}`;
    card.title = `${f.name}\n路径: ${f.path}`;

    card.innerHTML = `
      <div class="asset-card-thumb">
        <img src="/art/${f.path}" alt="${f.name}" loading="lazy" />
      </div>
      <span class="asset-card-name">${f.name}</span>
    `;

    // 单击选中高亮
    card.onclick = () => {
      document.querySelectorAll(".asset-card").forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");

      selectedAssetForQuickAction = f.path;
      const quickToolbar = document.getElementById("assetQuickActionToolbar");
      if (quickToolbar) {
        quickToolbar.style.display = "flex";
        const nameEl = document.getElementById("quickActionTargetName");
        if (nameEl) nameEl.textContent = `🎯 已选素材: ${f.name} (${f.path})`;
      }

      if (assetPickerConfig.mode === "folder") {
        const folderPath = breadcrumb || (f.path.includes("/") ? f.path.substring(0, f.path.lastIndexOf("/")) : f.path);
        assetPickerConfig.selectedItem = folderPath;
        const displayEl = document.getElementById("selectedAssetPathDisplay");
        if (displayEl) {
          displayEl.innerHTML = `<span style="color:#38bdf8; font-weight:bold;">📁 [已选目录]</span> ${folderPath} <span style="color:#94a3b8; font-size:11px;">(参考切片: ${f.name})</span>`;
        }
      } else {
        assetPickerConfig.selectedItem = f.path;
        const displayEl = document.getElementById("selectedAssetPathDisplay");
        if (displayEl) displayEl.textContent = f.path;
      }
    };

    // 双击直接应用
    card.ondblclick = () => {
      if (assetPickerConfig.mode === "folder") {
        assetPickerConfig.selectedItem = breadcrumb || (f.path.includes("/") ? f.path.substring(0, f.path.lastIndexOf("/")) : f.path);
      } else {
        assetPickerConfig.selectedItem = f.path;
      }
      applySelectedAsset();
    };

    grid.appendChild(card);
  });
}

function handleAssetSearch(query) {
  if (!artCatalogCache || !artCatalogCache.all_files) return;
  const q = query.trim().toLowerCase();
  if (!q) {
    if (currentBrowserNode) {
      renderAssetGrid(currentBrowserNode.files || [], currentBrowserNode.path, currentBrowserNode);
    }
    return;
  }

  const matched = artCatalogCache.all_files.filter(f => f.name.toLowerCase().includes(q) || f.path.toLowerCase().includes(q));
  renderAssetGrid(matched, `搜索结果: "${query}"`, null);
}

function applySelectedAsset() {
  let target = assetPickerConfig.selectedItem;

  // 选目录模式智能容错兜底：若尚未点击具体文件或目录行，但当前正处于某个目录视图中，自动应用当前浏览目录！
  if (assetPickerConfig.mode === "folder") {
    if (!target && currentBrowserNode && currentBrowserNode.path) {
      target = currentBrowserNode.path;
    }
    if (target && (target.endsWith(".png") || target.endsWith(".jpg"))) {
      target = target.substring(0, target.lastIndexOf("/"));
    }
  }

  if (!target) {
    showToast("⚠️ 请先在素材库中点击选择一个素材或目录！");
    return;
  }

  if (assetPickerConfig.onSelect) {
    assetPickerConfig.onSelect(target);
  }
  closeAssetBrowser();
}

function showToast(msg, duration = 2500) {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, duration);
}

// ==============================================================================
// 11. DT_MapTiles 土地地块工作台系统 (Landscape & Tiles Studio)
// ==============================================================================
function renderTilesStudio() {
  const container = document.getElementById("tileList");
  if (!container) return;
  container.innerHTML = "";

  const tiles = state.current.tiles || {};
  const tileIds = Object.keys(tiles);
  const countBadge = document.getElementById("tileCountBadge");
  if (countBadge) countBadge.textContent = `${tileIds.length} 块`;

  if (tileIds.length === 0) return;
  if (!tiles[state.selectedTileId]) {
    state.selectedTileId = tileIds[0];
  }

  tileIds.forEach(tid => {
    const t = tiles[tid];
    const isAct = tid === state.selectedTileId;
    const card = document.createElement("div");
    card.className = `tile-item-card ${isAct ? "active" : ""}`;

    const thumbSrc = t.GroundTexture ? `/art/${t.GroundTexture}` : "";

    card.innerHTML = `
      <div class="tile-item-thumb">
        ${thumbSrc ? `<img src="${thumbSrc}" alt="${t.DisplayName}" />` : '<span style="font-size:10px;color:#64748b;">无图</span>'}
      </div>
      <div class="tile-item-info">
        <span class="tile-item-name">${t.DisplayName || tid}</span>
        <span class="tile-item-id">${tid}</span>
      </div>
      <div style="display:flex; flex-direction:column; gap:4px; align-items:flex-end;">
        <span class="tile-badge-fric">阻力: ${t.FrictionMultiplier || 1.0}x</span>
        ${(t.DamagePerSecond && t.DamagePerSecond > 0) ? `<span class="tile-badge-dmg">${t.DamagePerSecond} DPS</span>` : ''}
      </div>
    `;

    card.onclick = () => {
      state.selectedTileId = tid;
      renderTilesStudio();
    };

    container.appendChild(card);
  });

  // 渲染当前地块预览视口与属性
  const curTile = tiles[state.selectedTileId];
  if (!curTile) return;

  const liveImg = document.getElementById("tileLiveImg");
  const specBadge = document.getElementById("tileSpecBadge");
  if (liveImg && curTile.GroundTexture) {
    liveImg.src = `/art/${curTile.GroundTexture}`;
  }
  if (specBadge) {
    specBadge.textContent = `地面阻力: ${curTile.FrictionMultiplier || 1.0}x | 环境伤害: ${curTile.DamagePerSecond || 0} DPS | ${curTile.SurfaceType || 'Default'}`;
  }

  // 渲染 Details 属性检查器
  renderTilePropertyTree(curTile);
}

function renderTilePropertyTree(tileData) {
  const container = document.getElementById("tilePropsTree");
  if (!container) return;
  container.innerHTML = "";

  const origTiles = state.original && state.original.tiles ? state.original.tiles : {};
  const origTile = origTiles[state.selectedTileId] || {};

  // 1. 基础信息与地表材质
  const cat1 = createPropCategory("🗺️ 土地地块材质与层级 (Textures & Visuals)");
  cat1.list.appendChild(createPropRow("DisplayName", "地块称谓 (DisplayName)", "String", tileData.DisplayName, origTile.DisplayName, (val) => {
    tileData.DisplayName = val;
    renderTilesStudio();
    updateDiffState();
  }));

  cat1.list.appendChild(createPropRow("GroundTexture", "地表材质贴图 (GroundTexture)", "AssetReference", tileData.GroundTexture, origTile.GroundTexture, (val) => {
    tileData.GroundTexture = val;
    renderTilesStudio();
    updateDiffState();
  }));

  cat1.list.appendChild(createPropRow("OverheadTexture", "高空遮罩层贴图 (OverheadTexture)", "AssetReference", tileData.OverheadTexture, origTile.OverheadTexture, (val) => {
    tileData.OverheadTexture = val;
    updateDiffState();
  }));
  container.appendChild(cat1.group);

  // 2. 物理阻力与环境伤害
  const cat2 = createPropCategory("⚡ 物理特性与环境机制 (Physics & Environmental)");
  cat2.list.appendChild(createNumberPropRow("FrictionMultiplier", "地面摩擦阻力倍率 (Friction)", tileData.FrictionMultiplier || 1.0, origTile.FrictionMultiplier, 0.05, 0.2, 2.0, (val) => {
    tileData.FrictionMultiplier = val;
    renderTilesStudio();
    updateDiffState();
  }));

  cat2.list.appendChild(createNumberPropRow("DamagePerSecond", "环境每秒持续伤害 (DPS)", tileData.DamagePerSecond || 0.0, origTile.DamagePerSecond, 1.0, 0.0, 100.0, (val) => {
    tileData.DamagePerSecond = val;
    renderTilesStudio();
    updateDiffState();
  }));

  cat2.list.appendChild(createNumberPropRow("SpawnWeight", "怪物刷出权重 (SpawnWeight)", tileData.SpawnWeight || 1.0, origTile.SpawnWeight, 0.1, 0.0, 10.0, (val) => {
    tileData.SpawnWeight = val;
    updateDiffState();
  }));

  cat2.list.appendChild(createPropRow("SurfaceType", "物理材质类型 (SurfaceType)", "String", tileData.SurfaceType || "Surface_Default", origTile.SurfaceType, (val) => {
    tileData.SurfaceType = val;
    updateDiffState();
  }));
  container.appendChild(cat2.group);
}

function openAssetPickerForCurrentTile() {
  const curTile = state.current.tiles ? state.current.tiles[state.selectedTileId] : null;
  if (!curTile) return;

  openAssetBrowser({
    title: `为土地【${curTile.DisplayName}】挑选地表材质贴图`,
    currentVal: curTile.GroundTexture || "",
    filterDir: "08_Maps",
    mode: "file",
    onSelect: (selectedPath) => {
      curTile.GroundTexture = selectedPath;
      renderTilesStudio();
      updateDiffState();
      showToast("✅ 土地地表材质贴图已更换！");
    }
  });
}

// ==============================================================================
// 12. UE5 行结构体搭配与全实体新增系统 (RowStruct Entity Creation)
// ==============================================================================
const STRUCT_TEMPLATES = {
  character: {
    structName: "FCharacterRow",
    tableName: "DT_Characters",
    title: "新增角色数据表行 (FCharacterRow)",
    defaultKeyPrefix: "Player_",
    fields: [
      { key: "DisplayName", name: "角色称谓 (DisplayName)", type: "String", default: "特勤突击兵" },
      { key: "Avatar", name: "头像切片贴图 (Avatar)", type: "AssetReference", default: "01_Player/01_Idle_Run/Dir_01_Down/Idle/T_Player_Medic_Idle_Dir_01_Down_01.png", filterDir: "01_Player" },
      { key: "MaxHealth", name: "最大生命值 (MaxHealth)", type: "Float", default: 1200.0, step: 50 },
      { key: "MoveSpeed", name: "基础移速 (MoveSpeed)", type: "Float", default: 390.0, step: 10 },
      { key: "Armor", name: "基础护甲 (Armor)", type: "Float", default: 15.0, step: 1 },
      { key: "CritChance", name: "基础暴击率 (CritChance)", type: "Float", default: 0.20, step: 0.01 },
      { key: "CritMultiplier", name: "暴击伤害倍率 (CritMultiplier)", type: "Float", default: 1.8, step: 0.1 },
      { key: "PickupRadius", name: "水晶拾取半径 (PickupRadius)", type: "Float", default: 140.0, step: 10 },
      { key: "DefaultWeaponID", name: "主武器 ID (DefaultWeaponID)", type: "String", default: "WPN_Rifle_Standard" },
      { key: "SecondaryWeaponID", name: "副武器 ID (SecondaryWeaponID)", type: "String", default: "WPN_Shotgun_Heavy" },
      { key: "TacticalCooldown", name: "战术技能冷却秒数 (TacticalCooldown)", type: "Float", default: 8.0, step: 0.5 }
    ]
  },
  weapon: {
    structName: "FWeaponRow",
    tableName: "DT_Weapons",
    title: "新增武器数据表行 (FWeaponRow)",
    defaultKeyPrefix: "WPN_",
    fields: [
      { key: "DisplayName", name: "武器名称 (DisplayName)", type: "String", default: "等离子聚焦激光" },
      { key: "Icon", name: "武器卡面大图标 (Icon)", type: "AssetReference", default: "06_Cards/04_WeaponModCards/T_Card_WeaponMod_05.png", filterDir: "06_Cards/04_WeaponModCards" },
      { key: "Damage", name: "单发基础伤害 (Damage)", type: "Float", default: 55.0, step: 5 },
      { key: "FireRate", name: "射击间隔秒数 (FireRate s)", type: "Float", default: 0.16, step: 0.02 },
      { key: "PelletCount", name: "单次射击弹片数 (PelletCount)", type: "Integer", default: 1, step: 1 },
      { key: "SpreadAngle", name: "弹片散布角度 (SpreadAngle °)", type: "Float", default: 0.0, step: 2 },
      { key: "BulletImage", name: "子弹飞行贴图 (BulletImage)", type: "AssetReference", default: "03_Weapons/02_AssaultRifle/T_Bullet_AssaultRifle_02_Flight.png", filterDir: "03_Weapons" },
      { key: "BulletScale", name: "子弹尺寸缩放 (BulletScale)", type: "Float", default: 0.35, step: 0.05 },
      { key: "ProjectileSpeed", name: "弹道初速 (ProjectileSpeed uu/s)", type: "Float", default: 950.0, step: 50 },
      { key: "PierceCount", name: "穿透怪物数 (PierceCount 次)", type: "Integer", default: 2, step: 1 },
      { key: "LifeSpan", name: "存活寿命秒数 (LifeSpan s)", type: "Float", default: 2.0, step: 0.2 },
      { key: "CollisionRadius", name: "碰撞胶囊半径 (CollisionRadius px)", type: "Float", default: 12.0, step: 1 },
      { key: "CollisionHeight", name: "碰撞胶囊高度 (CollisionHeight px)", type: "Float", default: 24.0, step: 1 },
      { key: "ExplosionRadius", name: "爆炸溅射半径 (ExplosionRadius px)", type: "Float", default: 0.0, step: 10 },
      { key: "ExplosionDamage", name: "爆炸溅射伤害 (ExplosionDamage)", type: "Float", default: 0.0, step: 5 },
      { key: "MuzzleFX", name: "枪口开火贴图 (MuzzleFX)", type: "AssetReference", default: "03_Weapons/02_AssaultRifle/T_Bullet_AssaultRifle_01_Muzzle.png", filterDir: "03_Weapons" },
      { key: "ImpactFX", name: "命中受击贴图 (ImpactFX)", type: "AssetReference", default: "03_Weapons/02_AssaultRifle/T_Bullet_AssaultRifle_03_Impact.png", filterDir: "03_Weapons" },
      { key: "TrailFX", name: "飞行拖尾粒子/切片 (TrailFX)", type: "AssetReference", default: "05_VFX/14_Spark_Tiny", filterDir: "05_VFX" },
      { key: "HitEffectID", name: "关联命中特效 ID (HitEffectID)", type: "String", default: "FX_Hit_Sparks" },
      { key: "InflictDebuffID", name: "附加减益状态 (InflictDebuffID)", type: "String", default: "None" }
    ]
  },
  effect: {
    structName: "FHitEffectRow",
    tableName: "DT_HitEffects",
    title: "新增战斗特效数据表行 (FHitEffectRow)",
    defaultKeyPrefix: "FX_",
    fields: [
      { key: "DisplayName", name: "特效名称 (DisplayName)", type: "String", default: "等离子电弧爆裂" },
      { key: "EffectType", name: "特效类型 (EffectType)", type: "String", default: "HitImpact" },
      { key: "VFXFolder", name: "切片目录 (VFXFolder)", type: "AssetReference", default: "05_VFX/16_EMP_Pulse", filterDir: "05_VFX" },
      { key: "Scale", name: "放映尺寸缩放 (Scale)", type: "Float", default: 0.60, step: 0.05 },
      { key: "FPS", name: "动画播放步频 (FPS)", type: "Float", default: 12.0, step: 1 },
      { key: "LifeDuration", name: "存活生命秒数 (LifeDuration s)", type: "Float", default: 0.35, step: 0.05 },
      { key: "HitStopDurationMs", name: "打击顿帧时间 (HitStop ms)", type: "Integer", default: 35, step: 5 },
      { key: "CameraShakeIntensity", name: "摄像机震屏幅度 (CameraShake)", type: "Float", default: 0.25, step: 0.05 }
    ]
  },
  enemy: {
    structName: "FEnemyRow",
    tableName: "DT_Enemies",
    title: "新增怪物数据表行 (FEnemyRow)",
    defaultKeyPrefix: "Enemy_",
    fields: [
      { key: "DisplayName", name: "怪物名称 (DisplayName)", type: "String", default: "生化剧毒喷吐者" },
      { key: "MaxHealth", name: "基础生命上限 (MaxHealth)", type: "Float", default: 200.0, step: 10 },
      { key: "MoveSpeed", name: "移动速度 (MoveSpeed)", type: "Float", default: 130.0, step: 10 },
      { key: "ContactDamage", name: "碰撞肉搏伤害 (ContactDamage)", type: "Float", default: 20.0, step: 2 },
      { key: "ScoreReward", name: "消灭得分奖励 (ScoreReward)", type: "Integer", default: 30, step: 5 },
      { key: "ExpGemValue", name: "经验水晶点数 (ExpGemValue)", type: "Integer", default: 20, step: 5 },
      { key: "Scale", name: "体型缩放 (Scale)", type: "Float", default: 0.45, step: 0.05 },
      { key: "Flipbook", name: "PaperFlipbook 资产路径", type: "String", default: "/Game/P01/Imported/Content/Asset/Art/02_Enemies/01_ZombieWalker/Flipbooks/PF_Enemy_ZombieWalker.PF_Enemy_ZombieWalker" }
    ]
  },
  tile: {
    structName: "FTileRow",
    tableName: "DT_MapTiles",
    title: "新增土地地块数据表行 (FTileRow)",
    defaultKeyPrefix: "Tile_",
    fields: [
      { key: "DisplayName", name: "土地地块名称 (DisplayName)", type: "String", default: "战术辐射污染荒土" },
      { key: "GroundTexture", name: "地表贴图 (GroundTexture)", type: "AssetReference", default: "08_Maps/Stage02_Z2/T_Map_Stage02_Z2_Ground.png", filterDir: "08_Maps" },
      { key: "OverheadTexture", name: "高空遮罩层贴图 (OverheadTexture)", type: "AssetReference", default: "", filterDir: "08_Maps" },
      { key: "FrictionMultiplier", name: "地面阻力系数 (1.0标准, <1减速)", type: "Float", default: 0.70, step: 0.05 },
      { key: "DamagePerSecond", name: "环境每秒伤害 (DPS)", type: "Float", default: 10.0, step: 2 },
      { key: "NavWalkable", name: "可导航通行 (NavWalkable)", type: "Boolean", default: true },
      { key: "SpawnWeight", name: "刷怪生成权重 (SpawnWeight)", type: "Float", default: 1.5, step: 0.2 },
      { key: "SurfaceType", name: "地面物理材质类型 (SurfaceType)", type: "String", default: "Surface_Toxic_Acid" }
    ]
  }
};

let currentAddingEntityType = "character";

function openAddNewRowModal(entityType) {
  currentAddingEntityType = entityType;
  const tmpl = STRUCT_TEMPLATES[entityType];
  if (!tmpl) return;

  const modal = document.getElementById("addEntityModal");
  document.getElementById("newEntityStructBadge").textContent = `UE5 USTRUCT: ${tmpl.structName} (驱动数据表: ${tmpl.tableName})`;
  document.getElementById("newEntityModalTitle").textContent = tmpl.title;
  
  const randSuffix = Math.floor(Math.random() * 899 + 100);
  document.getElementById("newEntityRowKey").value = `${tmpl.defaultKeyPrefix}${randSuffix}`;

  const container = document.getElementById("newEntityFormFields");
  container.innerHTML = "";

  tmpl.fields.forEach(f => {
    const row = document.createElement("div");
    const isAsset = f.type === "AssetReference";
    const isNum = f.type === "Float" || f.type === "Integer";
    const isSpanFull = isAsset || f.key === "DisplayName" || f.key === "Flipbook" || f.key === "DefaultWeaponID" || f.key === "SecondaryWeaponID" || f.key === "HitEffectID";

    row.className = `struct-form-row ${isSpanFull ? 'span-full' : ''}`;

    row.innerHTML = `
      <div class="struct-form-meta">
        <span class="struct-form-name">${f.name}</span>
        <span class="type-pill ${f.type}">${f.type}</span>
      </div>
      <div class="struct-form-input-wrap">
        <input type="${isNum ? 'number' : 'text'}" class="input-text" id="addField_${f.key}" value="${f.default !== undefined ? f.default : ''}" ${isNum ? `step="${f.step || 'any'}"` : ''} style="flex: 1;" />
        ${isAsset ? `<button class="btn btn-secondary btn-sm glow-cyan" type="button" onclick="openAssetBrowserForNewEntityField('${f.key}', '${f.filterDir || ''}')">📁 挑选素材</button>` : ''}
      </div>
    `;
    container.appendChild(row);
  });

  modal.classList.add("open");
}

function openAssetBrowserForNewEntityField(fieldKey, filterDir) {
  const input = document.getElementById(`addField_${fieldKey}`);
  openAssetBrowser({
    title: `为新实体挑选【${fieldKey}】素材`,
    currentVal: input ? input.value : "",
    filterDir: filterDir || "",
    mode: "file",
    onSelect: (selectedPath) => {
      if (input) input.value = selectedPath;
    }
  });
}

function closeAddNewRowModal() {
  document.getElementById("addEntityModal").classList.remove("open");
}

function handleConfirmAddNewRow() {
  const rowKey = document.getElementById("newEntityRowKey").value.trim();
  if (!rowKey) {
    showToast("⚠️ 请输入合法的数据表行键名 (RowKey)！");
    return;
  }

  const tmpl = STRUCT_TEMPLATES[currentAddingEntityType];
  const tableDataKey = currentAddingEntityType === "character" ? "characters" :
                       currentAddingEntityType === "weapon" ? "weapons" :
                       currentAddingEntityType === "effect" ? "hit_effects" :
                       currentAddingEntityType === "enemy" ? "enemies" : "tiles";

  if (!state.current[tableDataKey]) state.current[tableDataKey] = {};
  if (state.current[tableDataKey][rowKey]) {
    showToast(`⚠️ 该行键名 [${rowKey}] 已存在于 ${tmpl.tableName} 中，请修改！`);
    return;
  }

  const newObj = {};
  tmpl.fields.forEach(f => {
    const input = document.getElementById(`addField_${f.key}`);
    let val = input ? input.value : f.default;
    if (f.type === "Float") val = parseFloat(val) || 0.0;
    else if (f.type === "Integer") val = parseInt(val) || 0;
    else if (f.type === "Boolean") val = val === "true" || val === true;
    newObj[f.key] = val;
  });

  // 针对角色的特殊初始化（自动配置默认 6 方向动作结构与特效映射）
  if (currentAddingEntityType === "character") {
    newObj.CollisionRadius = 24.0;
    newObj.CollisionHeight = 48.0;
    newObj.SortPriority = 2000;
    newObj.VFX = {
      HitVFX: "05_VFX/11_Hit_Kinetic",
      SkillVFX: "05_VFX/09_Nanite_Heal",
      MuzzleVFX: "05_VFX/13_Muzzle_Flash",
      DashVFX: "05_VFX/17_Dash_Ghost"
    };
    newObj.Animations = JSON.parse(JSON.stringify(state.current.characters.Player_Medic.Animations || {}));
    state.selectedPlayerId = rowKey;
  } else if (currentAddingEntityType === "weapon") {
    newObj.PelletCount = newObj.PelletCount || 1;
  } else if (currentAddingEntityType === "effect") {
    state.selectedEffectId = rowKey;
  } else if (currentAddingEntityType === "enemy") {
    newObj.Scale = newObj.Scale || 0.45;
    state.selectedEnemyId = rowKey;
  } else if (currentAddingEntityType === "tile") {
    newObj.TileSize = 1024;
    state.selectedTileId = rowKey;
  }

  state.current[tableDataKey][rowKey] = newObj;

  closeAddNewRowModal();
  updateDiffState();

  // 刷新对应视图
  if (currentAddingEntityType === "character") {
    renderPlayerStudio();
  } else if (currentAddingEntityType === "weapon") {
    renderWeaponsGrid();
  } else if (currentAddingEntityType === "effect") {
    renderEffectsStudio();
  } else if (currentAddingEntityType === "enemy") {
    renderEnemyList();
    renderEnemyDetail();
  } else if (currentAddingEntityType === "tile") {
    renderTilesStudio();
  }
  renderDataTable();

  showToast(`🎉 成功新增 ${tmpl.structName} 行: ${rowKey} 并加入 ${tmpl.tableName}！`);
}

function openAddNewRowModalFromCurrentGrid() {
  if (currentGridTableName === "DT_Characters") openAddNewRowModal("character");
  else if (currentGridTableName === "DT_Weapons") openAddNewRowModal("weapon");
  else if (currentGridTableName === "DT_HitEffects") openAddNewRowModal("effect");
  else if (currentGridTableName === "DT_Enemies") openAddNewRowModal("enemy");
  else if (currentGridTableName === "DT_MapTiles") openAddNewRowModal("tile");
  else openAddNewRowModal("enemy");
}

// 页面离开防误触拦截：若有未保存的草稿改动，提示用户
window.addEventListener("beforeunload", (e) => {
  if (typeof getDiffSummary === "function") {
    const diffs = getDiffSummary();
    if (diffs && diffs.length > 0) {
      e.preventDefault();
      e.returnValue = "您有尚未保存的配置调试草稿，确定要离开吗？";
      return e.returnValue;
    }
  }
});

/* ==============================================================================
   1. 工程管理与新工程自愈脚手架 (Scaffold & Project Switcher)
   ============================================================================== */
function checkScaffoldNotice(projectInfo) {
  const banner = document.getElementById("scaffoldBanner");
  const textEl = document.getElementById("scaffoldNoticeText");
  const nameEl = document.getElementById("headerProjectName");
  const pathEl = document.getElementById("headerProjectPath");

  if (nameEl && projectInfo.projectName) nameEl.textContent = projectInfo.projectName;
  if (pathEl && projectInfo.projectPath) pathEl.textContent = `挂载: ${projectInfo.projectPath}`;

  if (projectInfo.missingStandardTables && projectInfo.missingStandardTables.length > 0) {
    if (banner && textEl) {
      textEl.textContent = `检测到新工程缺少 ${projectInfo.missingStandardTables.length} 个标准表: ${projectInfo.missingStandardTables.slice(0, 2).join(", ")}等`;
      banner.style.display = "inline-flex";
    }
  } else {
    if (banner) banner.style.display = "none";
  }
}

async function scaffoldMissingTables() {
  try {
    const resp = await fetch("/api/project/scaffold-tables", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({})
    });
    const res = await resp.json();
    if (res.success) {
      showToast(`🎉 成功自愈生成 ${res.createdTables.length} 个标准核心数据表！`);
      setTimeout(() => window.location.reload(), 800);
    } else {
      showToast("❌ 自愈生成失败: " + (res.error || "未知错误"));
    }
  } catch (err) {
    showToast("❌ 请求失败: " + err.message);
  }
}

function promptSwitchProject() {
  const modal = document.getElementById("switchProjectModal");
  if (modal) modal.classList.add("active");
}

function closeSwitchProjectModal() {
  const modal = document.getElementById("switchProjectModal");
  if (modal) modal.classList.remove("active");
}

async function handleConfirmSwitchProject() {
  const input = document.getElementById("newProjectPathInput");
  const path = input ? input.value.trim() : "";
  if (!path) {
    showToast("⚠️ 请输入有效的工程路径");
    return;
  }
  try {
    const resp = await fetch("/api/project/switch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path })
    });
    const res = await resp.json();
    if (res.success) {
      showToast(`🎉 成功挂载工程: ${res.project.projectName}！正在重载...`);
      closeSwitchProjectModal();
      setTimeout(() => window.location.reload(), 1000);
    } else {
      showToast("❌ 挂载失败: " + (res.error || "路径无法解析"));
    }
  } catch (err) {
    showToast("❌ 挂载失败: " + err.message);
  }
}


// 通用素材选择适配器 (兼容 openAssetPicker("folder" | "image", callback))
function openAssetPicker(mode = "image", onSelect) {
  const isFolder = mode === "folder";
  openAssetBrowser({
    title: isFolder ? "选择目标工程标准目录" : "挑选美术源图资产",
    mode: isFolder ? "folder" : "file",
    onSelect: (selectedPath) => {
      if (typeof onSelect === "function") {
        const filename = selectedPath ? selectedPath.split("/").pop() : "";
        const fileObj = {
          absPath: selectedPath,
          project_rel_path: selectedPath,
          name: filename,
          url: "/art/" + selectedPath
        };
        onSelect(selectedPath, fileObj);
      }
    }
  });
}

/* ==============================================================================
   2. 🎨 美术素材全流水线工坊 (Asset Pipeline Studio)
   ============================================================================== */
let currentPipelineSourcePath = null;
let pipelineState = {
  sourcePath: null,
  sourceFilename: "",
  imageNaturalWidth: 0,
  imageNaturalHeight: 0,
  currentMode: "smart", // "smart" | "grid" | "tools"
  smartBoxes: [],       // 智能提取的外接矩形 [{x, y, w, h}]
  customHLines: [],     // 水平裁切线绝对像素坐标 [y1, y2, ...]
  customVLines: [],     // 垂直裁切线绝对像素坐标 [x1, x2, ...]
  currentSlices: [],    // 当前生成的全部切片清单
  // 多动作分行状态
  exportMode: "multi",  // "multi" | "single"
  actionGroups: [],     // [{ id, name, subDir, prefix, startIndex, slices, boxes }]
  // 动作循环放映机
  flipbookTimer: null,
  flipbookPlaying: true,
  flipbookFps: 8,
  flipbookIndex: 0,
  flipbookActiveGroup: null, // null 为全播，字符串为特定动作名
  flipbookActiveSlices: []
};

function initPipelineStudioDragAndDrop() {
  const pipelineBox = document.getElementById("pipelineSrcImageBox");
  const stage = document.getElementById("pipelinePreviewStage") || document.querySelector(".pipeline-preview-stage");
  const ctrlCard = document.querySelector(".pipeline-ctrl-card");
  const tabPipeline = document.getElementById("tab-asset-pipeline");

  // 绑定流水线源图框、预览舞台与控制面板，完全支持任意外部图片拖入并安全持久化
  [pipelineBox, stage, ctrlCard, tabPipeline].forEach(targetEl => {
    if (!targetEl) return;
    setupUniversalImageDrop(targetEl, {
      category: "pipeline",
      entityId: "Pipeline_Source",
      label: "流水线源图",
      autoRemoveBlack: false,
      autoTrim: false,
      onSuccess: (data) => {
        loadPipelineSource(data.abs_path || data.project_rel_path, data.web_url, data.filename, data.size ? data.size[0] : 0, data.size ? data.size[1] : 0);
        showToast(`🎉 外部图片 [${data.filename}] 已成功载入流水线工坊并创建生肉备份，现可自由移动切线或一键智能提取！`);
      }
    });
  });

  // 窗口改变大小时自适应重绘切线
  window.addEventListener("resize", () => {
    if (pipelineState.sourcePath) {
      renderSliceOverlay();
    }
  });

  // 加载项目中实际存在的所有已有美术子目录供自动联想
  loadProjectFoldersList();
}

// 动态拉取项目内已有文件夹列表
async function loadProjectFoldersList() {
  try {
    const resp = await fetch("/api/asset/folders");
    const data = await resp.json();
    if (data.folders && data.folders.length > 0) {
      const datalist = document.getElementById("projectFoldersList");
      if (datalist) {
        datalist.innerHTML = "";
        data.folders.forEach(f => {
          const opt = document.createElement("option");
          opt.value = f;
          datalist.appendChild(opt);
        });
      }
    }
  } catch (err) {
    console.warn("加载项目文件夹列表失败:", err);
  }
}

// 📁 打开项目素材库窗口，让用户自由点选已有项目目录
function browseProjectFolderForExport() {
  openAssetPicker("folder", (selectedDir) => {
    const inputEl = document.getElementById("exportCategoryInput");
    if (inputEl) {
      inputEl.value = selectedDir;
      onExportCategoryInputChange();
      showToast(`📁 已选择目标工程目录: [${selectedDir}]`);
    }
  });
}

function onExportCategoryInputChange() {
  updateExportNamePreview();
}

function openAssetPickerForPipeline() {
  openAssetPicker("image", (selectedPath, fileObj) => {
    const absPath = fileObj ? fileObj.absPath : selectedPath;
    const filename = fileObj ? fileObj.name : selectedPath.split("/").pop();
    const webUrl = fileObj ? fileObj.url : `/asset-view?path=${encodeURIComponent(absPath)}`;
    loadPipelineSource(absPath, webUrl, filename, 0, 0);
    showToast("✅ 已成功加载源图到流水线工坊！");
  });
}

function loadPipelineSource(absPath, webUrl, filename, naturalW, naturalH) {
  currentPipelineSourcePath = absPath;
  pipelineState.sourcePath = absPath;
  pipelineState.sourceFilename = filename;
  pipelineState.smartBoxes = [];
  pipelineState.actionGroups = [];

  const titleEl = document.getElementById("pipelineSrcTitle");
  const metaEl = document.getElementById("pipelineSrcMeta");
  const boxEl = document.getElementById("pipelineSrcImageBox");

  if (titleEl) titleEl.textContent = `当前源图: ${filename}`;
  if (metaEl) {
    metaEl.textContent = naturalW && naturalH ? `已就绪 (${naturalW}x${naturalH})` : "已就绪";
    metaEl.className = "badge green";
  }

  // 载入大图并监听真实像素尺寸
  if (boxEl) {
    boxEl.innerHTML = `<img id="pipelineSrcImgEl" src="${webUrl}?t=${Date.now()}" alt="${filename}" style="max-width: 100%; max-height: 380px; object-fit: contain; display: block; margin: 0 auto;" />`;
    const imgEl = document.getElementById("pipelineSrcImgEl");
    imgEl.onload = () => {
      pipelineState.imageNaturalWidth = imgEl.naturalWidth;
      pipelineState.imageNaturalHeight = imgEl.naturalHeight;
      if (metaEl) {
        metaEl.textContent = `已就绪 (${imgEl.naturalWidth}x${imgEl.naturalHeight})`;
      }
      initDefaultGridLines();
      renderSliceOverlay();
      autoSuggestExportNaming(filename);
    };
  }
}

function initDefaultGridLines() {
  const rows = parseInt(document.getElementById("sliceRowsInput")?.value) || 2;
  const cols = parseInt(document.getElementById("sliceColsInput")?.value) || 4;
  recalculateGridLines(rows, cols);
}

function recalculateGridLines(rows, cols) {
  const w = pipelineState.imageNaturalWidth || 1000;
  const h = pipelineState.imageNaturalHeight || 1000;
  
  pipelineState.customHLines = [];
  for (let r = 1; r < rows; r++) {
    pipelineState.customHLines.push(Math.round((h / rows) * r));
  }
  pipelineState.customVLines = [];
  for (let c = 1; c < cols; c++) {
    pipelineState.customVLines.push(Math.round((w / cols) * c));
  }
}

function onGridParamsChange() {
  const rows = parseInt(document.getElementById("sliceRowsInput")?.value) || 2;
  const cols = parseInt(document.getElementById("sliceColsInput")?.value) || 4;
  recalculateGridLines(rows, cols);
  renderSliceOverlay();
}

function resetGridLinesEvenly() {
  onGridParamsChange();
  showToast("🔄 网格切线已按行数列数均匀重置！可在图上自由拖动。");
}

function switchPipelineMode(mode) {
  pipelineState.currentMode = mode;
  document.querySelectorAll(".pipeline-mode-tab").forEach(tab => {
    tab.classList.toggle("active", tab.dataset.mode === mode);
  });

  const panelSmart = document.getElementById("panelSmartExtract");
  const panelGrid = document.getElementById("panelGridSlice");
  const panelTools = document.getElementById("panelHelperTools");

  if (panelSmart) panelSmart.style.display = mode === "smart" ? "block" : "none";
  if (panelGrid) panelGrid.style.display = mode === "grid" ? "block" : "none";
  if (panelTools) panelTools.style.display = mode === "tools" ? "block" : "none";

  renderSliceOverlay();
}

// 绘制交互式切线与识别外框
function renderSliceOverlay() {
  const overlay = document.getElementById("sliceOverlayLayer");
  const imgEl = document.getElementById("pipelineSrcImgEl");
  const stage = document.getElementById("pipelinePreviewStage");
  if (!overlay || !imgEl || !pipelineState.sourcePath) {
    if (overlay) overlay.style.display = "none";
    return;
  }

  const imgRect = imgEl.getBoundingClientRect();
  const stageRect = stage.getBoundingClientRect();

  if (imgRect.width === 0 || imgRect.height === 0) return;

  overlay.style.display = "block";
  overlay.style.left = `${imgRect.left - stageRect.left}px`;
  overlay.style.top = `${imgRect.top - stageRect.top}px`;
  overlay.style.width = `${imgRect.width}px`;
  overlay.style.height = `${imgRect.height}px`;
  overlay.innerHTML = "";

  const scaleX = imgRect.width / pipelineState.imageNaturalWidth;
  const scaleY = imgRect.height / pipelineState.imageNaturalHeight;

  // 1. 智能精灵识别模式：渲染外接矩形框
  if (pipelineState.currentMode === "smart") {
    if (pipelineState.smartBoxes && pipelineState.smartBoxes.length > 0) {
      pipelineState.smartBoxes.forEach((b, idx) => {
        const rectEl = document.createElement("div");
        rectEl.className = "smart-sprite-rect";
        rectEl.style.left = `${Math.round(b.x * scaleX)}px`;
        rectEl.style.top = `${Math.round(b.y * scaleY)}px`;
        rectEl.style.width = `${Math.round(b.w * scaleX)}px`;
        rectEl.style.height = `${Math.round(b.h * scaleY)}px`;
        rectEl.innerHTML = `<span class="sprite-rect-label">#${idx + 1} (${b.w}x${b.h})</span>`;
        overlay.appendChild(rectEl);
      });
    }
    return;
  }

  // 2. 自由网格线切片模式：渲染支持鼠标拖动的水平线与垂直线
  if (pipelineState.currentMode === "grid") {
    // 水平裁切线
    pipelineState.customHLines.forEach((lineY, idx) => {
      const lineEl = document.createElement("div");
      lineEl.className = "slice-line-h";
      lineEl.style.top = `${Math.round(lineY * scaleY)}px`;
      lineEl.innerHTML = `
        <div class="line-handle-h" title="按住可上下拖动裁切线 (当前 Y: ${lineY}px)">
          <span>↕ ${lineY}px</span>
        </div>
      `;
      setupDraggableLineH(lineEl, idx, scaleY);
      overlay.appendChild(lineEl);
    });

    // 垂直裁切线
    pipelineState.customVLines.forEach((lineX, idx) => {
      const lineEl = document.createElement("div");
      lineEl.className = "slice-line-v";
      lineEl.style.left = `${Math.round(lineX * scaleX)}px`;
      lineEl.innerHTML = `
        <div class="line-handle-v" title="按住可左右拖动裁切线 (当前 X: ${lineX}px)">
          <span>↔ ${lineX}px</span>
        </div>
      `;
      setupDraggableLineV(lineEl, idx, scaleX);
      overlay.appendChild(lineEl);
    });
  }
}

// 绑定水平切线拖拽控制器 (线本身和手柄均可拖动)
function setupDraggableLineH(lineEl, lineIndex, scaleY) {
  const onMouseDown = (e) => {
    e.preventDefault();
    e.stopPropagation();
    lineEl.classList.add("dragging");

    const overlay = document.getElementById("sliceOverlayLayer");
    const overlayRect = overlay.getBoundingClientRect();

    const onMouseMove = (ev) => {
      ev.preventDefault();
      const clientY = ev.clientY;
      const relY = clientY - overlayRect.top;
      let naturalY = Math.round(relY / scaleY);
      naturalY = Math.max(10, Math.min(pipelineState.imageNaturalHeight - 10, naturalY));

      pipelineState.customHLines[lineIndex] = naturalY;
      lineEl.style.top = `${Math.round(naturalY * scaleY)}px`;
      const handle = lineEl.querySelector(".line-handle-h");
      if (handle) handle.innerHTML = `<span>↕ ${naturalY}px</span>`;
    };

    const onMouseUp = () => {
      lineEl.classList.remove("dragging");
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      pipelineState.customHLines.sort((a, b) => a - b);
      renderSliceOverlay();
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  };

  lineEl.addEventListener("mousedown", onMouseDown);
}

// 绑定垂直切线拖拽控制器 (线本身、宽热区和手柄均可拖动)
function setupDraggableLineV(lineEl, lineIndex, scaleX) {
  const onMouseDown = (e) => {
    e.preventDefault();
    e.stopPropagation();
    lineEl.classList.add("dragging");

    const overlay = document.getElementById("sliceOverlayLayer");
    const overlayRect = overlay.getBoundingClientRect();

    const onMouseMove = (ev) => {
      ev.preventDefault();
      const clientX = ev.clientX;
      const relX = clientX - overlayRect.left;
      let naturalX = Math.round(relX / scaleX);
      naturalX = Math.max(10, Math.min(pipelineState.imageNaturalWidth - 10, naturalX));

      pipelineState.customVLines[lineIndex] = naturalX;
      lineEl.style.left = `${Math.round(naturalX * scaleX)}px`;
      const handle = lineEl.querySelector(".line-handle-v");
      if (handle) handle.innerHTML = `<span>↔ ${naturalX}px</span>`;
    };

    const onMouseUp = () => {
      lineEl.classList.remove("dragging");
      document.removeEventListener("mousemove", onMouseMove);
      document.removeEventListener("mouseup", onMouseUp);
      pipelineState.customVLines.sort((a, b) => a - b);
      renderSliceOverlay();
    };

    document.addEventListener("mousemove", onMouseMove);
    document.addEventListener("mouseup", onMouseUp);
  };

  lineEl.addEventListener("mousedown", onMouseDown);
}

// 🧠 1. 智能识别精灵岛屿
async function executeSmartDetect() {
  if (!currentPipelineSourcePath) {
    showToast("⚠️ 请先从素材库挑选或拖入待切片源图！");
    return;
  }
  const minArea = parseInt(document.getElementById("smartMinAreaInput")?.value) || 3000;
  const padding = parseInt(document.getElementById("smartPaddingInput")?.value) || 4;

  try {
    showToast("⏳ 正在进行 OpenCV 轮廓分析与形态学精灵提取...");
    const resp = await fetch("/api/asset/smart-detect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: currentPipelineSourcePath,
        min_area: minArea,
        padding: padding
      })
    });
    const res = await resp.json();
    const boxes = res.boxes || res.sprites || [];
    const count = res.count || res.totalDetected || boxes.length;
    if (boxes.length > 0) {
      pipelineState.smartBoxes = boxes;
      renderSliceOverlay();
      showToast(`🧠 成功精准识别出 ${count} 个独立精灵岛屿！可直接点击【按识别框执行裁切】。`);
    } else {
      showToast("⚠️ 未识别到有效精灵岛屿，请尝试调小【最小像素面积】或检查 Alpha 通道。");
    }
  } catch (err) {
    showToast("❌ 智能识别失败: " + err.message);
  }
}

// ✂️ 2. 执行智能识别框裁切
async function executeSliceDetectedSprites() {
  if (!currentPipelineSourcePath) {
    showToast("⚠️ 请先选择源图！");
    return;
  }
  if (!pipelineState.smartBoxes || pipelineState.smartBoxes.length === 0) {
    showToast("⚠️ 尚未进行智能识别，正在自动执行识别...");
    await executeSmartDetect();
    if (!pipelineState.smartBoxes || pipelineState.smartBoxes.length === 0) return;
  }

  try {
    showToast("⏳ 正在按智能识别框执行精确无留白裁切...");
    const resp = await fetch("/api/asset/slice-custom", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: currentPipelineSourcePath,
        boxes: pipelineState.smartBoxes
      })
    });
    const res = await resp.json();
    if (res.slices) {
      handleSliceSuccess(res.slices);
    } else {
      showToast("❌ 裁切失败: " + (res.error || "未知异常"));
    }
  } catch (err) {
    showToast("❌ 裁切请求失败: " + err.message);
  }
}

// ✂️ 3. 执行自由网格线裁切 (包含用户拖动后的切线坐标)
async function executeCustomGridSlice() {
  if (!currentPipelineSourcePath) {
    showToast("⚠️ 请先选择源图！");
    return;
  }

  try {
    showToast("⏳ 正在按拖动后的自定义网格切线执行裁切...");
    const resp = await fetch("/api/asset/slice-custom", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: currentPipelineSourcePath,
        h_lines: pipelineState.customHLines,
        v_lines: pipelineState.customVLines
      })
    });
    const res = await resp.json();
    if (res.slices) {
      handleSliceSuccess(res.slices);
    } else {
      showToast("❌ 网格裁切失败: " + (res.error || "未知异常"));
    }
  } catch (err) {
    showToast("❌ 网格裁切请求失败: " + err.message);
  }
}

// 切片生成成功后的统一处理：分析动作组、渲染展台、开启放映机、激活导出面板
function handleSliceSuccess(slices) {
  pipelineState.currentSlices = slices;
  renderPipelineSlices(slices);

  // 智能划分动作组 (根据切片行数或聚类拆分多动作)
  buildActionGroupsFromSlices(slices);

  // 默认试播第 1 个动作组或全部切片
  if (pipelineState.actionGroups.length > 0) {
    playActionGroupFlipbook(0);
  } else {
    startPipelineFlipbook(slices, "全部切片");
  }

  // 展开项目导出面板
  const exportPanel = document.getElementById("exportProjectPanel");
  if (exportPanel) {
    exportPanel.style.display = "block";
    renderMultiActionConfigRows();
    updateExportNamePreview();
  }

  showToast(`🎉 成功生成 ${slices.length} 帧切片！已智能拆分为 ${pipelineState.actionGroups.length} 个动作组，可独立命名与试播。`);
}

// 🔀 智能将切片列表按行拆分成独立动作组 (如第1行动作 Attack，第2行动作 Run)
function buildActionGroupsFromSlices(slices) {
  if (!slices || slices.length === 0) {
    pipelineState.actionGroups = [];
    return;
  }

  // 1. 自动从文件名中提取潜在的动作名称列表 (如 T_01_S_Attack_Run_A -> ['Attack', 'Run'])
  const guessedActionNames = extractActionKeywords(pipelineState.sourceFilename);

  // 2. 判断切片的分行归属 (按 row 字段或 Y 坐标聚类)
  const rowsMap = new Map();
  const hasExplicitRow = slices[0].row !== undefined;

  if (hasExplicitRow) {
    slices.forEach(s => {
      const r = s.row || 0;
      if (!rowsMap.has(r)) rowsMap.set(r, []);
      rowsMap.get(r).push(s);
    });
  } else {
    // 根据切片框的 Y 坐标聚类分行 (平均高度的 45% 作为分行容差)
    const avgH = slices.reduce((acc, s) => acc + s.size[1], 0) / slices.length;
    slices.forEach(s => {
      const cy = s.box ? s.box[1] : 0;
      let matchedRow = null;
      for (const [rKey, grp] of rowsMap.entries()) {
        const refY = grp[0].box ? grp[0].box[1] : 0;
        if (Math.abs(cy - refY) < avgH * 0.5) {
          matchedRow = rKey;
          break;
        }
      }
      if (matchedRow !== null) {
        rowsMap.get(matchedRow).push(s);
      } else {
        rowsMap.set(rowsMap.size, [s]);
      }
    });
  }

  const rowKeys = Array.from(rowsMap.keys()).sort((a, b) => a - b);
  const actionGroups = [];

  rowKeys.forEach((rk, rIdx) => {
    const rowSlices = rowsMap.get(rk);
    // 动作名称推断
    let actName = guessedActionNames[rIdx] || (rowKeys.length === 1 ? "Action" : `Action_${rIdx + 1}`);
    let prefix = `T_Player_${actName}`;

    actionGroups.push({
      id: `action_row_${rIdx}`,
      rowIndex: rIdx,
      name: actName,
      subDir: actName,
      prefix: prefix,
      startIndex: 1,
      slices: rowSlices,
      boxes: rowSlices.map(s => ({
        x: s.box[0],
        y: s.box[1],
        w: s.box[2],
        h: s.box[3]
      }))
    });
  });

  pipelineState.actionGroups = actionGroups;

  // 如果包含多行，默认开启多动作分行模式
  if (actionGroups.length > 1) {
    setExportActionMode("multi");
  } else {
    setExportActionMode("single");
  }
}

// 从文件名中智能提取动作关键词
function extractActionKeywords(filename) {
  if (!filename) return ["Action_01", "Action_02"];
  const stem = filename.replace(/\.[^/.]+$/, "");
  const KNOWN_ACTIONS = [
    "Attack", "Run", "Idle", "Walk", "Hurt", "Hit", "Die", "Death",
    "Skill", "Jump", "Shoot", "Fire", "Dash", "Defense", "Reload"
  ];
  const matched = [];
  KNOWN_ACTIONS.forEach(act => {
    const reg = new RegExp(`\\b${act}\\b|_?${act}_?`, "i");
    if (reg.test(stem)) {
      matched.push(act);
    }
  });

  if (matched.length > 0) {
    return matched;
  }

  // 尝试以下划线分割猜测
  const parts = stem.split("_").filter(p => p.length > 2 && !/^(T|S|A|B|C|01|02|03|04)$/i.test(p));
  return parts.length > 0 ? parts : ["Action_01", "Action_02"];
}

function autoDetectActionNamesFromFilename() {
  if (pipelineState.currentSlices.length > 0) {
    buildActionGroupsFromSlices(pipelineState.currentSlices);
    renderMultiActionConfigRows();
    updateExportNamePreview();
    showToast("🪄 已重新根据源图文件名推断动作名称与前缀！");
  }
}

// 切换单动作 vs 多动作分行模式
function setExportActionMode(mode) {
  pipelineState.exportMode = mode;
  const btnMulti = document.getElementById("btnModeMultiAction");
  const btnSingle = document.getElementById("btnModeSingleAction");
  const secMulti = document.getElementById("multiActionConfigSection");
  const secSingle = document.getElementById("singleActionConfigSection");

  if (btnMulti) btnMulti.className = `btn btn-xs ${mode === "multi" ? "btn-primary active" : "btn-secondary"}`;
  if (btnSingle) btnSingle.className = `btn btn-xs ${mode === "single" ? "btn-primary active" : "btn-secondary"}`;

  if (secMulti) secMulti.style.display = mode === "multi" ? "block" : "none";
  if (secSingle) secSingle.style.display = mode === "single" ? "grid" : "none";

  updateExportNamePreview();
}

// 渲染多动作分行配置列表
function renderMultiActionConfigRows() {
  const container = document.getElementById("multiActionRowsList");
  if (!container) return;
  container.innerHTML = "";

  if (!pipelineState.actionGroups || pipelineState.actionGroups.length === 0) {
    container.innerHTML = `<div class="empty-hint" style="padding:10px;">暂无分行动作数据</div>`;
    return;
  }

  pipelineState.actionGroups.forEach((grp, idx) => {
    const rowCard = document.createElement("div");
    rowCard.className = "action-row-item";
    rowCard.id = `action_row_card_${idx}`;

    const isCurrentPlaying = pipelineState.flipbookActiveGroup === grp.name;

    rowCard.innerHTML = `
      <div class="action-row-header">
        <span class="badge-action-name">🏷️ 动作 #${idx + 1} (第 ${grp.rowIndex + 1} 行 · ${grp.slices.length} 帧)</span>
        <div style="display: flex; gap: 6px; align-items: center;">
          <button class="btn btn-secondary btn-xs ${isCurrentPlaying ? 'glow-cyan' : ''}" onclick="playActionGroupFlipbook(${idx})">
            ${isCurrentPlaying ? '🎬 正在试播' : '▶️ 试播此动作'}
          </button>
          <span style="font-size: 10px; color: #94a3b8;">${grp.slices[0].size[0]}x${grp.slices[0].size[1]}px</span>
        </div>
      </div>
      <div class="action-row-inputs">
        <div class="form-mini-item">
          <label>动作名:</label>
          <input type="text" class="input-text-mini" value="${grp.name}" style="width: 80px;" oninput="onActionGroupChange(${idx}, 'name', this.value)" />
        </div>
        <div class="form-mini-item">
          <label>存放子目录:</label>
          <input type="text" class="input-text-mini" value="${grp.subDir}" style="width: 100px;" oninput="onActionGroupChange(${idx}, 'subDir', this.value)" />
        </div>
        <div class="form-mini-item">
          <label>前缀:</label>
          <input type="text" class="input-text-mini" value="${grp.prefix}" style="width: 140px;" oninput="onActionGroupChange(${idx}, 'prefix', this.value)" />
        </div>
        <div class="form-mini-item">
          <label>起始号:</label>
          <input type="number" class="input-text-mini" value="${grp.startIndex}" min="0" max="99" style="width: 45px;" oninput="onActionGroupChange(${idx}, 'startIndex', this.value)" />
        </div>
      </div>
      <div style="font-size: 10px; color: #10b981; margin-top: 4px; font-family: var(--font-mono);">
        📁 预览: ${grp.subDir}/${grp.prefix}_${String(grp.startIndex).padStart(2, '0')}.png ~ _${String(grp.startIndex + grp.slices.length - 1).padStart(2, '0')}.png (共 ${grp.slices.length} 帧)
      </div>
    `;
    container.appendChild(rowCard);
  });
}

function onActionGroupChange(groupIndex, field, value) {
  const grp = pipelineState.actionGroups[groupIndex];
  if (!grp) return;

  if (field === "name") {
    grp.name = value.trim();
    grp.subDir = value.trim();
    const baseCat = document.getElementById("exportCategoryInput")?.value || "01_Player/Actions";
    const entityPrefix = baseCat.includes("Player") ? "T_Player_" : (baseCat.includes("Enemies") ? "T_Enemy_" : "T_");
    grp.prefix = `${entityPrefix}${value.trim()}`;
  } else if (field === "subDir") {
    grp.subDir = value.trim();
  } else if (field === "prefix") {
    grp.prefix = value.trim();
  } else if (field === "startIndex") {
    grp.startIndex = parseInt(value) || 1;
  }

  // 重新渲染当前行的预览与全局预览
  renderMultiActionConfigRows();
  updateExportNamePreview();
}

// 独占循环试播指定的动作组 (例如只播第 1 行的开火，或只播第 2 行的奔跑)
function playActionGroupFlipbook(groupIndex) {
  const grp = pipelineState.actionGroups[groupIndex];
  if (!grp) return;

  pipelineState.flipbookActiveGroup = grp.name;
  startPipelineFlipbook(grp.slices, `动作: ${grp.name}`);
  renderMultiActionConfigRows();
}

// 渲染切片成果展台
function renderPipelineSlices(slices) {
  const container = document.getElementById("pipelineSlicesContainer");
  const countEl = document.getElementById("pipelineSliceCount");
  if (countEl) countEl.textContent = `${slices.length} 帧`;
  if (!container) return;

  container.innerHTML = "";
  slices.forEach((s) => {
    const card = document.createElement("div");
    card.className = "pipeline-slice-thumb";
    const imgUrl = s.url || `/asset-view?path=${encodeURIComponent(s.path)}`;
    card.innerHTML = `
      <img src="${imgUrl}" alt="${s.filename}" />
      <span title="${s.filename}">#${s.frameIndex + 1} ${s.size[0]}x${s.size[1]}</span>
    `;
    container.appendChild(card);
  });
}

// 🎬 连续动作放映机控制器
function startPipelineFlipbook(slices, titleLabel) {
  const playerBox = document.getElementById("pipelineFlipbookPlayerBox");
  if (!playerBox || !slices || slices.length === 0) return;

  pipelineState.flipbookActiveSlices = slices;
  playerBox.style.display = "block";
  pipelineState.flipbookIndex = 0;
  pipelineState.flipbookPlaying = true;
  updateFlipbookFrame(titleLabel);

  if (pipelineState.flipbookTimer) clearInterval(pipelineState.flipbookTimer);
  pipelineState.flipbookTimer = setInterval(() => {
    if (!pipelineState.flipbookPlaying || !pipelineState.flipbookActiveSlices.length) return;
    pipelineState.flipbookIndex = (pipelineState.flipbookIndex + 1) % pipelineState.flipbookActiveSlices.length;
    updateFlipbookFrame(titleLabel);
  }, Math.round(1000 / pipelineState.flipbookFps));
}

function updateFlipbookFrame(titleLabel) {
  const slices = pipelineState.flipbookActiveSlices;
  if (!slices || !slices.length) return;
  const frame = slices[pipelineState.flipbookIndex];
  const previewImg = document.getElementById("flipbookPreviewImg");
  const badge = document.getElementById("flipbookFrameBadge");

  if (previewImg && frame) {
    previewImg.src = frame.url || `/asset-view?path=${encodeURIComponent(frame.path)}`;
  }
  if (badge) {
    const label = titleLabel ? `[${titleLabel}] ` : "";
    badge.textContent = `${label}${pipelineState.flipbookIndex + 1}/${slices.length}F`;
  }
}

function togglePipelineFlipbook() {
  pipelineState.flipbookPlaying = !pipelineState.flipbookPlaying;
  const btn = document.getElementById("btnFlipbookPlay");
  if (btn) {
    btn.textContent = pipelineState.flipbookPlaying ? "⏸️ 暂停" : "▶️ 播放";
  }
}

function changePipelineFps(val) {
  pipelineState.flipbookFps = parseInt(val) || 8;
  const textEl = document.getElementById("pipelineFpsText");
  if (textEl) textEl.textContent = `${pipelineState.flipbookFps} FPS`;

  if (pipelineState.flipbookTimer) {
    clearInterval(pipelineState.flipbookTimer);
    pipelineState.flipbookTimer = setInterval(() => {
      if (!pipelineState.flipbookPlaying || !pipelineState.flipbookActiveSlices.length) return;
      pipelineState.flipbookIndex = (pipelineState.flipbookIndex + 1) % pipelineState.flipbookActiveSlices.length;
      updateFlipbookFrame();
    }, Math.round(1000 / pipelineState.flipbookFps));
  }
}

// 💾 项目目录分类选择与自动命名规范
function autoSuggestExportNaming(filename) {
  let stem = filename.replace(/\.[^/.]+$/, "");
  let defaultCategory = "01_Player/Actions";
  let defaultSubDir = "";

  if (stem.includes("Player") || stem.includes("Attack") || stem.includes("Run") || stem.includes("Idle")) {
    defaultCategory = "01_Player/Actions";
    defaultSubDir = stem.replace(/^T_/, "").replace(/_A$|_B$|_C$/, "");
  } else if (stem.includes("Enemy") || stem.includes("Zombie") || stem.includes("Monster")) {
    defaultCategory = "02_Enemies";
    defaultSubDir = stem.replace(/^T_/, "");
  } else if (stem.includes("Weapon") || stem.includes("Gun") || stem.includes("Bullet")) {
    defaultCategory = "03_Weapons";
    defaultSubDir = stem.replace(/^T_/, "");
  } else if (stem.includes("FX") || stem.includes("Hit") || stem.includes("Explode")) {
    defaultCategory = "05_VFX";
    defaultSubDir = stem.replace(/^T_/, "");
  } else if (stem.includes("UI") || stem.includes("Icon") || stem.includes("Btn")) {
    defaultCategory = "07_UI";
    defaultSubDir = stem.replace(/^T_/, "");
  }

  let prefix = stem.startsWith("T_") ? stem : `T_${stem}`;
  prefix = prefix.replace(/_[A-Z]$/, "");

  const catInp = document.getElementById("exportCategoryInput");
  const subInp = document.getElementById("exportSubDirInput");
  const preInp = document.getElementById("exportPrefixInput");

  if (catInp) catInp.value = defaultCategory;
  if (subInp) subInp.value = defaultSubDir;
  if (preInp) preInp.value = prefix;

  updateExportNamePreview();
}

function updateExportNamePreview() {
  const baseCategory = document.getElementById("exportCategoryInput")?.value.trim() || "01_Player/Actions";
  const pathPreviewEl = document.getElementById("exportPathPreview");
  const filenamePreviewEl = document.getElementById("exportFilenamePreview");

  if (pipelineState.exportMode === "multi" && pipelineState.actionGroups.length > 0) {
    if (pathPreviewEl) {
      pathPreviewEl.textContent = `Content/美术/Art/${baseCategory}/[各动作独立子目录]/`;
    }
    if (filenamePreviewEl) {
      const summaryList = pipelineState.actionGroups.map(g => {
        const pad = (num) => String(num).padStart(2, "0");
        return `【${g.name}】${g.prefix}_${pad(g.startIndex)}.png ~ _${pad(g.startIndex + g.slices.length - 1)}.png`;
      });
      filenamePreviewEl.innerHTML = summaryList.join("<br/>");
    }
  } else {
    const subDir = document.getElementById("exportSubDirInput")?.value.trim() || "";
    let prefix = document.getElementById("exportPrefixInput")?.value.trim() || "T_Sprite";
    if (!prefix.startsWith("T_")) prefix = `T_${prefix}`;
    const startIdx = parseInt(document.getElementById("exportStartIndexInput")?.value) || 1;
    const count = pipelineState.currentSlices.length || 8;

    const targetPath = subDir ? `Content/美术/Art/${baseCategory}/${subDir}/` : `Content/美术/Art/${baseCategory}/`;
    const pad = (num) => String(num).padStart(2, "0");
    const filenamePreview = `${prefix}_${pad(startIdx)}.png ~ ${prefix}_${pad(startIdx + count - 1)}.png (共 ${count} 帧)`;

    if (pathPreviewEl) pathPreviewEl.textContent = targetPath;
    if (filenamePreviewEl) filenamePreviewEl.textContent = filenamePreview;
  }
}

// 🚀 统一执行导出方案 (自适应单动作与多动作模式)
async function executeCurrentExportPlan() {
  if (pipelineState.exportMode === "multi" && pipelineState.actionGroups.length > 0) {
    await executeMultiActionExport();
  } else {
    await executeSingleActionExport();
  }
}

// 🔀 批量将多动作独立分类输出到项目各自子目录并持久化备份
async function executeMultiActionExport() {
  if (!currentPipelineSourcePath) {
    showToast("⚠️ 无可用源图！");
    return;
  }
  if (!pipelineState.actionGroups || pipelineState.actionGroups.length === 0) {
    showToast("⚠️ 暂无动作组，请先执行切片！");
    return;
  }

  const baseCategory = document.getElementById("exportCategoryInput")?.value.trim() || "01_Player/Actions";
  const autoTrim = document.getElementById("chkExportAutoTrim")?.checked || true;
  const autoRemoveBlack = document.getElementById("chkExportAutoRemoveBlack")?.checked || false;

  const actionPayload = pipelineState.actionGroups.map(grp => ({
    name: grp.name,
    category: baseCategory,
    sub_dir: grp.subDir,
    prefix: grp.prefix,
    start_index: grp.startIndex,
    boxes: grp.boxes
  }));

  try {
    showToast("🚀 正在将多个动作独立规范存入各自目录并备份生肉原图...");
    const resp = await fetch("/api/asset/export-multi-actions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: currentPipelineSourcePath,
        action_groups: actionPayload,
        base_category: baseCategory,
        auto_trim: autoTrim,
        auto_remove_black: autoRemoveBlack
      })
    });
    const res = await resp.json();
    if (res.status === "success") {
      const summary = res.actionSummaries ? res.actionSummaries.join(" | ") : "";
      showToast(`🎉 成功批量导出 ${res.totalActions} 个动作 (${res.totalExported} 帧切片)！${summary}`);
      if (typeof refreshAssetLibrary === "function") {
        refreshAssetLibrary();
      }
      loadProjectFoldersList();
    } else {
      showToast("❌ 批量导出失败: " + (res.error || "未知异常"));
    }
  } catch (err) {
    showToast("❌ 导出请求失败: " + err.message);
  }
}

// 📋 单动作整组导出
async function executeSingleActionExport() {
  if (!currentPipelineSourcePath) {
    showToast("⚠️ 无可用源图！");
    return;
  }
  if (!pipelineState.currentSlices || pipelineState.currentSlices.length === 0) {
    showToast("⚠️ 请先切片后再导出！");
    return;
  }

  const category = document.getElementById("exportCategoryInput")?.value.trim() || "01_Player/Actions";
  const subDir = document.getElementById("exportSubDirInput")?.value.trim() || "";
  const prefix = document.getElementById("exportPrefixInput")?.value.trim() || "T_Sprite";
  const startIdx = parseInt(document.getElementById("exportStartIndexInput")?.value) || 1;
  const autoTrim = document.getElementById("chkExportAutoTrim")?.checked || true;
  const autoRemoveBlack = document.getElementById("chkExportAutoRemoveBlack")?.checked || false;

  const boxes = pipelineState.currentSlices.map(s => ({
    x: s.box[0],
    y: s.box[1],
    w: s.box[2],
    h: s.box[3]
  }));

  try {
    showToast("🚀 正在将切片批量存入项目目录并归档生肉原图...");
    const resp = await fetch("/api/asset/export-slices", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path: currentPipelineSourcePath,
        boxes: boxes,
        category: category,
        sub_dir: subDir,
        prefix: prefix,
        start_index: startIdx,
        auto_trim: autoTrim,
        auto_remove_black: autoRemoveBlack
      })
    });
    const res = await resp.json();
    const isSuccess = res.status === "success" || res.success;
    if (isSuccess) {
      const count = res.totalExported || res.count || (res.exportedFiles ? res.exportedFiles.length : 0);
      const folder = res.targetDir || res.project_folder || "";
      showToast(`🎉 成功将 ${count} 个切片导出至工程：[${folder}]！已自动在 .source_backup 备份生肉原图。`);
      if (typeof refreshAssetLibrary === "function") {
        refreshAssetLibrary();
      }
      loadProjectFoldersList();
    } else {
      showToast("❌ 导出失败: " + (res.error || "未知异常"));
    }
  } catch (err) {
    showToast("❌ 导出请求失败: " + err.message);
  }
}
/* ==============================================================================
   3. 📱 可视化 HUD / UI 画布拖拽交互工坊 (Canvas HUD Studio)
   ============================================================================== */
let hudLayoutState = {
  widgetName: "WBP_CombatHUD",
  canvasResolution: [360, 640],
  widgets: []
};
let selectedHudWidgetId = null;
let isHudPlayMode = false;
let hudSimulatedHP = 100;
let hudSimulatedCoins = 250;

async function initHudStudio() {
  try {
    const resp = await fetch("/api/hud/layout");
    const data = await resp.json();
    if (data && data.widgets) {
      hudLayoutState = data;
    }
    renderHudCanvas();
  } catch (e) {
    console.error("加载 HUD 布局失败:", e);
  }
}

function renderHudCanvas() {
  const canvas = document.getElementById("hudScreenCanvas");
  if (!canvas) return;
  canvas.innerHTML = "";

  hudLayoutState.widgets.forEach((w) => {
    const el = document.createElement("div");
    el.className = `hud-widget-instance ${selectedHudWidgetId === w.id ? "selected" : ""}`;
    el.id = `widget_${w.id}`;
    
    // 支持整体 Scale 缩放
    const scale = w.scale || 1.0;
    const curW = Math.round(w.size[0] * scale);
    const curH = Math.round(w.size[1] * scale);

    el.style.left = `${w.position[0]}px`;
    el.style.top = `${w.position[1]}px`;
    el.style.width = `${curW}px`;
    el.style.height = `${curH}px`;

    // 内部组件渲染 + 8向控制手柄
    el.innerHTML = `
      <span class="widget-label">${w.name} [${w.prefabType}] (${curW}x${curH})</span>
      ${getWidgetPreviewHTML(w)}
      <div class="resize-handle nw" data-handle="nw"></div>
      <div class="resize-handle n"  data-handle="n"></div>
      <div class="resize-handle ne" data-handle="ne"></div>
      <div class="resize-handle e"  data-handle="e"></div>
      <div class="resize-handle se" data-handle="se"></div>
      <div class="resize-handle s"  data-handle="s"></div>
      <div class="resize-handle sw" data-handle="sw"></div>
      <div class="resize-handle w"  data-handle="w"></div>
    `;

    // 点击选中
    el.onclick = (e) => {
      e.stopPropagation();
      selectHudWidget(w.id);
    };

    // 拖拽移动与手柄拉伸缩放支持 (仅非试玩模式)
    if (!isHudPlayMode) {
      enableWidgetDragging(el, w);
      enableWidgetResizing(el, w);
    }

    canvas.appendChild(el);
  });
}

function getWidgetPreviewHTML(w) {
  const slots = w.artSlots || {};
  
  if (w.prefabType === "HealthBar") {
    const hpPct = Math.max(0, Math.min(100, (hudSimulatedHP / 100) * 100));
    // 如果有自定义底板与填充贴图
    const bgImg = slots.bgImage ? `/asset-view?path=${encodeURIComponent(slots.bgImage)}` : "";
    const fillImg = slots.fillImage ? `/asset-view?path=${encodeURIComponent(slots.fillImage)}` : "";

    return `
      <div style="width: 100%; height: 100%; background: ${bgImg ? `url('${bgImg}') center/100% 100% no-repeat` : 'rgba(0,0,0,0.6)'}; border-radius: 4px; overflow: hidden; position: relative; border: 1px solid #10b981;">
        <div style="width: ${hpPct}%; height: 100%; background: ${fillImg ? `url('${fillImg}') left center/100% 100% repeat-x` : 'linear-gradient(90deg, #059669, #10b981)'}; transition: width 0.25s ease;"></div>
        <div style="position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-family: var(--font-mono); font-size: 10px; font-weight: 700; color: #fff; text-shadow: 0 1px 2px #000;">
          ${Math.round(hudSimulatedHP)} / 100 HP
        </div>
      </div>
    `;
  } else if (w.prefabType === "WeaponSlot") {
    const iconImg = slots.iconImage ? `/asset-view?path=${encodeURIComponent(slots.iconImage)}` : "";
    const frameImg = slots.frameImage ? `/asset-view?path=${encodeURIComponent(slots.frameImage)}` : "";

    return `
      <div style="width: 100%; height: 100%; background: ${frameImg ? `url('${frameImg}') center/cover no-repeat` : '#0b1329'}; border: 1px solid #06b6d4; border-radius: 8px; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; overflow: hidden;">
        ${iconImg ? `<img src="${iconImg}" style="max-width: 80%; max-height: 80%; object-fit: contain;" />` : `<span style="font-size: 24px;">🔫</span>`}
        <span style="font-family: var(--font-mono); font-size: 9px; color: #38bdf8; position: absolute; bottom: 2px; text-shadow: 0 1px 2px #000;">30 / 120</span>
        <div id="hudReloadMask" style="position: absolute; inset: 0; background: rgba(0,0,0,0.75); display: none; align-items: center; justify-content: center; color: #f59e0b; font-size: 9px; font-family: var(--font-mono);">换弹中...</div>
      </div>
    `;
  } else if (w.prefabType === "EconomyBadge") {
    const coinImg = slots.coinIcon ? `/asset-view?path=${encodeURIComponent(slots.coinIcon)}` : "";
    return `
      <div style="width: 100%; height: 100%; background: rgba(0,0,0,0.5); border: 1px solid #f59e0b; border-radius: 12px; display: flex; align-items: center; gap: 6px; padding: 0 8px;">
        ${coinImg ? `<img src="${coinImg}" style="width: 16px; height: 16px; object-fit: contain;" />` : `<span style="font-size: 14px;">🪙</span>`}
        <span id="hudCoinsText" style="font-family: var(--font-mono); font-size: 11px; font-weight: 700; color: #fbbf24;">${hudSimulatedCoins}</span>
      </div>
    `;
  } else if (w.prefabType === "TouchJoystick") {
    const baseImg = slots.baseImage ? `/asset-view?path=${encodeURIComponent(slots.baseImage)}` : "";
    const thumbImg = slots.thumbImage ? `/asset-view?path=${encodeURIComponent(slots.thumbImage)}` : "";
    return `
      <div style="width: 100%; height: 100%; border-radius: 50%; border: ${baseImg ? 'none' : '2px dashed rgba(255,255,255,0.3)'}; background: ${baseImg ? `url('${baseImg}') center/cover no-repeat` : 'rgba(255,255,255,0.05)'}; display: flex; align-items: center; justify-content: center;">
        <div style="width: 36%; height: 36%; border-radius: 50%; background: ${thumbImg ? `url('${thumbImg}') center/cover no-repeat` : 'rgba(56, 189, 248, 0.5)'}; border: ${thumbImg ? 'none' : '1px solid #38bdf8'};"></div>
      </div>
    `;
  } else if (w.prefabType === "AvatarFrame") {
    const avatarImg = slots.avatarImage ? `/asset-view?path=${encodeURIComponent(slots.avatarImage)}` : "";
    return `
      <div style="width: 100%; height: 100%; border-radius: 50%; border: 2px solid #38bdf8; background: #080d1a; overflow: hidden; display: flex; align-items: center; justify-content: center;">
        ${avatarImg ? `<img src="${avatarImg}" style="width: 100%; height: 100%; object-fit: cover;" />` : `<span style="font-size: 24px;">👤</span>`}
      </div>
    `;
  } else if (w.prefabType === "CustomImage") {
    const mainImg = slots.mainImage ? `/art/${slots.mainImage}` : "";
    return `
      <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; overflow: hidden;">
        ${mainImg ? `<img src="${mainImg}" style="width: 100%; height: 100%; object-fit: contain;" />` : `<span style="font-size: 24px;">🖼️</span>`}
      </div>
    `;
  } else {
    return `
      <div style="width: 100%; height: 100%; background: rgba(15, 23, 42, 0.6); display: flex; align-items: center; justify-content: center; font-family: var(--font-mono); font-size: 10px; color: #94a3b8;">
        ${w.name}
      </div>
    `;
  }
}

// 8向缩放手柄拉伸逻辑 (零误差缩放)
function enableWidgetResizing(el, widgetData) {
  const handles = el.querySelectorAll(".resize-handle");
  handles.forEach((handle) => {
    handle.onmousedown = (e) => {
      e.stopPropagation();
      const dir = handle.getAttribute("data-handle");
      const startX = e.clientX;
      const startY = e.clientY;
      const origW = widgetData.size[0];
      const origH = widgetData.size[1];
      const origPosX = widgetData.position[0];
      const origPosY = widgetData.position[1];
      const origRatio = origW / origH;
      const isLocked = widgetData.lockAspectRatio !== false;

      const onMouseMove = (moveEv) => {
        const dx = moveEv.clientX - startX;
        const dy = moveEv.clientY - startY;

        let newW = origW;
        let newH = origH;
        let newPosX = origPosX;
        let newPosY = origPosY;

        if (dir.includes("e")) newW = Math.max(20, origW + dx);
        if (dir.includes("s")) newH = Math.max(20, origH + dy);
        if (dir.includes("w")) {
          newW = Math.max(20, origW - dx);
          newPosX = origPosX + (origW - newW);
        }
        if (dir.includes("n")) {
          newH = Math.max(20, origH - dy);
          newPosY = origPosY + (origH - newH);
        }

        // 保持宽高比锁定
        if (isLocked) {
          if (dir.includes("e") || dir.includes("w")) {
            newH = Math.round(newW / origRatio);
          } else {
            newW = Math.round(newH * origRatio);
          }
        }

        widgetData.size[0] = Math.round(newW);
        widgetData.size[1] = Math.round(newH);
        widgetData.position[0] = Math.round(newPosX);
        widgetData.position[1] = Math.round(newPosY);

        el.style.width = `${widgetData.size[0]}px`;
        el.style.height = `${widgetData.size[1]}px`;
        el.style.left = `${widgetData.position[0]}px`;
        el.style.top = `${widgetData.position[1]}px`;

        updateInspectorValues(widgetData);
      };

      const onMouseUp = () => {
        window.removeEventListener("mousemove", onMouseMove);
        window.removeEventListener("mouseup", onMouseUp);
        renderHudCanvas();
      };

      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup", onMouseUp);
    };
  });
}

function enableWidgetDragging(el, widgetData) {
  let isDragging = false;
  let startX, startY, origX, origY;

  el.onmousedown = (e) => {
    if (isHudPlayMode || e.target.classList.contains("resize-handle")) return;
    isDragging = true;
    startX = e.clientX;
    startY = e.clientY;
    origX = widgetData.position[0];
    origY = widgetData.position[1];

    const onMouseMove = (moveEv) => {
      if (!isDragging) return;
      const dx = moveEv.clientX - startX;
      const dy = moveEv.clientY - startY;
      widgetData.position[0] = Math.round(origX + dx);
      widgetData.position[1] = Math.round(origY + dy);
      el.style.left = `${widgetData.position[0]}px`;
      el.style.top = `${widgetData.position[1]}px`;
      updateInspectorValues(widgetData);
    };

    const onMouseUp = () => {
      isDragging = false;
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };

    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
  };
}

function onPrefabDragStart(e, prefabType) {
  e.dataTransfer.setData("text/plain", prefabType);
}

function onCanvasDragOver(e) {
  e.preventDefault();
  e.stopPropagation();
}

function initHudStudioDragAndDrop() {
  const container = document.querySelector(".hud-canvas-container");
  const bezel = document.querySelector(".device-notch-bezel");
  const canvas = document.getElementById("hudScreenCanvas");

  const targets = [container, bezel, canvas].filter(Boolean);
  targets.forEach(el => {
    ["dragenter", "dragover"].forEach(name => {
      el.addEventListener(name, (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (bezel) bezel.classList.add("universal-drop-target-active");
        if (canvas) canvas.classList.add("universal-drop-target-active");
      }, false);
    });

    ["dragleave"].forEach(name => {
      el.addEventListener(name, (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (container && (!e.relatedTarget || !container.contains(e.relatedTarget))) {
          if (bezel) bezel.classList.remove("universal-drop-target-active");
          if (canvas) canvas.classList.remove("universal-drop-target-active");
        }
      }, false);
    });

    el.addEventListener("drop", (e) => {
      e.preventDefault();
      e.stopPropagation();
      if (bezel) bezel.classList.remove("universal-drop-target-active");
      if (canvas) canvas.classList.remove("universal-drop-target-active");
      onCanvasDrop(e);
    }, false);
  });
}

function onCanvasDrop(e) {
  e.preventDefault();
  e.stopPropagation();

  const canvasEl = document.getElementById("hudScreenCanvas");
  let dropX = 20;
  let dropY = 40;
  if (canvasEl) {
    const rect = canvasEl.getBoundingClientRect();
    dropX = Math.round(e.clientX - rect.left);
    dropY = Math.round(e.clientY - rect.top);
    // 安全边界限制：防止落在手机黑边或外壳导致坐标负数或飞出屏幕
    dropX = Math.max(16, Math.min(rect.width - 90, dropX));
    dropY = Math.max(16, Math.min(rect.height - 90, dropY));
  }

  // 1. 检查是否直接从操作系统外部（Finder/桌面）拖入了图片文件！
  if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
    const file = e.dataTransfer.files[0];
    const isImage = file.type.startsWith("image/") || /\.(png|jpg|jpeg|webp|tga|bmp)$/i.test(file.name);
    if (isImage) {
      showToast(`📥 正在将外部 UI 素材 [${file.name}] 导入画布并自动备份...`);
      const reader = new FileReader();
      reader.onload = async (event) => {
        const base64Data = event.target.result;
        try {
          const res = await fetch("/api/asset/ingest", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              file_base64: base64Data,
              filename: file.name,
              category: "ui",
              entity_id: "Custom_UI"
            })
          });
          const data = await res.json();
          if (data.status === "success") {
            const newId = `ui_${Date.now().toString(36)}`;
            const newWidget = {
              id: newId,
              prefabType: "CustomImage",
              name: file.name.replace(/\.[^/.]+$/, ""),
              anchor: "TopLeft",
              position: [Math.max(10, dropX - 32), Math.max(10, dropY - 32)],
              size: [64, 64],
              scale: 1.0,
              lockAspectRatio: true,
              binding: "",
              artSlots: {
                mainImage: data.project_rel_path
              }
            };
            hudLayoutState.widgets.push(newWidget);
            selectHudWidget(newId);
            renderHudCanvas();
            showToast(`🎉 外部图片已成功转存项目并生成 UI 控件！\n📁 路径: ${data.project_rel_path}\n🛡️ 原图备份: ${data.backup_rel_path}`);
            refreshAssetCatalog(false);
          } else {
            showToast(`❌ 导入失败: ${data.error || "未知错误"}`);
          }
        } catch (err) {
          showToast(`❌ 网络异常: ${err.message}`);
        }
      };
      reader.readAsDataURL(file);
      return;
    }
  }

  // 2. 内部控件模板拖放
  const prefabType = e.dataTransfer.getData("text/plain");
  if (!prefabType) return;

  const newId = `ui_${Date.now().toString(36)}`;
  const defaultSizes = {
    HealthBar: [180, 24],
    WeaponSlot: [72, 72],
    BuffTray: [180, 36],
    EconomyBadge: [96, 26],
    AvatarFrame: [64, 64],
    TouchJoystick: [110, 110]
  };

  const newWidget = {
    id: newId,
    prefabType: prefabType,
    name: `新${prefabType}`,
    anchor: "TopLeft",
    position: [dropX - 40, dropY - 20],
    size: defaultSizes[prefabType] || [100, 40],
    scale: 1.0,
    lockAspectRatio: prefabType !== "HealthBar",
    binding: `Player.${prefabType}`,
    artSlots: {}
  };

  hudLayoutState.widgets.push(newWidget);
  selectHudWidget(newId);
  renderHudCanvas();
  showToast(`🎉 成功将 ${newWidget.name} 拖入手机画布！`);
}

function selectHudWidget(widgetId) {
  selectedHudWidgetId = widgetId;
  renderHudCanvas();
  const widget = hudLayoutState.widgets.find((w) => w.id === widgetId);
  renderInspector(widget);
}

// 检查器渲染：包含尺寸、缩放、等比锁定、锚点、数据源绑定与【自定义美术贴图槽位】
function renderInspector(widget) {
  const form = document.getElementById("inspectorForm");
  const titleEl = document.getElementById("inspectorWidgetTitle");
  const delBtn = document.getElementById("btnDeleteWidget");

  if (!widget) {
    if (form) form.innerHTML = `<div class="empty-hint">未选中任何 UI 控件</div>`;
    if (titleEl) titleEl.textContent = "UI 控件属性检查器";
    if (delBtn) delBtn.style.display = "none";
    return;
  }

  if (titleEl) titleEl.textContent = `${widget.name} (${widget.prefabType})`;
  if (delBtn) delBtn.style.display = "block";

  if (!widget.artSlots) widget.artSlots = {};
  if (widget.scale === undefined) widget.scale = 1.0;
  if (widget.lockAspectRatio === undefined) widget.lockAspectRatio = true;

  // 获取该预置件的美术槽位列表
  const prefabArtConfig = {
    CustomImage: [
      { key: "mainImage", label: "自定义图片贴图 (Image Texture)" }
    ],
    HealthBar: [
      { key: "bgImage", label: "底板背景贴图 (Background)" },
      { key: "fillImage", label: "生命填充条贴图 (Fill Bar)" }
    ],
    WeaponSlot: [
      { key: "frameImage", label: "武器品质框贴图 (Frame)" },
      { key: "iconImage", label: "武器枪械大图标 (Weapon Icon)" }
    ],
    EconomyBadge: [
      { key: "coinIcon", label: "货币/矿石图标 (Coin Icon)" }
    ],
    TouchJoystick: [
      { key: "baseImage", label: "摇杆固定底座 (Base)" },
      { key: "thumbImage", label: "触控滑动球 (Thumb)" }
    ],
    AvatarFrame: [
      { key: "avatarImage", label: "角色头像立绘 (Avatar)" }
    ]
  };

  const currentSlots = prefabArtConfig[widget.prefabType] || [{ key: "bgImage", label: "默认贴图" }];

  let artSlotsHTML = currentSlots.map((slot) => {
    const curPath = widget.artSlots[slot.key] || "";
    const shortName = curPath ? curPath.split("/").pop() : "未绑定贴图 (支持直接拖入图片)";
    const imgUrl = curPath ? (curPath.startsWith("/") ? curPath : `/art/${curPath}`) : "";

    return `
      <div class="art-slot-item" id="artSlotItem_${widget.id}_${slot.key}" title="支持直接从外部拖入图片替换贴图">
        <div class="art-slot-thumb" onclick="pickArtForWidgetSlot('${widget.id}', '${slot.key}')" title="点击挑选素材">
          ${imgUrl ? `<img src="${imgUrl}" alt="${slot.label}" />` : `<span class="empty-slot-icon">🖼️</span>`}
        </div>
        <div class="art-slot-meta">
          <span class="slot-label">${slot.label}</span>
          <span class="slot-path" title="${curPath}">${shortName}</span>
        </div>
        <button class="btn btn-secondary btn-xs" onclick="pickArtForWidgetSlot('${widget.id}', '${slot.key}')">挑素材</button>
      </div>
    `;
  }).join("");

  form.innerHTML = `
    <div class="form-group">
      <label>控件名称:</label>
      <input type="text" class="input-text" value="${widget.name}" onchange="updateWidgetField('${widget.id}', 'name', this.value)" />
    </div>

    <!-- 🎨 自定义美术资产槽位 -->
    <div class="form-group">
      <label style="color:#38bdf8; font-weight:700;">🎨 自定义美术贴图 (Art Assets):</label>
      <div class="art-slots-group">
        ${artSlotsHTML}
      </div>
    </div>
  `;

  // 为每个贴图槽位绑定直接拖拽摄取
  currentSlots.forEach((slot) => {
    const slotEl = form.querySelector(`#artSlotItem_${widget.id}_${slot.key}`);
    if (slotEl) {
      setupUniversalImageDrop(slotEl, {
        category: "ui",
        entityId: () => widget.id,
        label: `${widget.name} - ${slot.label}`,
        onSuccess: (data) => {
          widget.artSlots[slot.key] = data.project_rel_path;
          renderHudCanvas();
          renderInspector(widget);
        }
      });
    }
  });

  form.innerHTML += `

    <!-- 尺寸与等比锁定 -->
    <div class="form-group">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
        <label style="margin: 0;">尺寸 W × H (px):</label>
        <button class="aspect-lock-btn ${widget.lockAspectRatio ? 'locked' : ''}" onclick="toggleAspectRatioLock('${widget.id}')" title="锁定宽高比">
          ${widget.lockAspectRatio ? '🔗 已锁定等比' : '🔓 自由拉伸'}
        </button>
      </div>
      <div style="display: flex; gap: 8px;">
        <input type="number" id="inp_size_w" class="input-text" value="${widget.size[0]}" onchange="updateWidgetSize('${widget.id}', 0, this.value)" />
        <input type="number" id="inp_size_h" class="input-text" value="${widget.size[1]}" onchange="updateWidgetSize('${widget.id}', 1, this.value)" />
      </div>
    </div>

    <!-- 缩放倍率滑块 -->
    <div class="form-group">
      <label>缩放倍率 (Scale: <span id="scaleDisplayVal">${widget.scale}x</span>):</label>
      <input type="range" min="0.2" max="3.0" step="0.05" value="${widget.scale}" style="width: 100%; cursor: pointer;" oninput="updateWidgetScale('${widget.id}', this.value)" />
    </div>

    <!-- 坐标位置 -->
    <div class="form-group">
      <label>坐标 X / Y (UE5 UMG Slot Position):</label>
      <div style="display: flex; gap: 8px;">
        <input type="number" id="inp_pos_x" class="input-text" value="${widget.position[0]}" onchange="updateWidgetPos('${widget.id}', 0, this.value)" />
        <input type="number" id="inp_pos_y" class="input-text" value="${widget.position[1]}" onchange="updateWidgetPos('${widget.id}', 1, this.value)" />
      </div>
      <span style="font-size: 9px; color: #64748b;">支持鼠标在画布边缘手柄拖拽缩放或直接拖拽移动</span>
    </div>

    <!-- UE5 锚点与对齐预设 -->
    <div class="form-group">
      <label>UE5 UMG 锚点与对齐预设 (Anchors & Alignment):</label>
      <select class="input-text" onchange="applyAnchorPreset('${widget.id}', this.value)">
        <option value="TopLeft" ${widget.anchor === "TopLeft" ? "selected" : ""}>左上 (TopLeft: 0,0 | Align 0,0)</option>
        <option value="TopCenter" ${widget.anchor === "TopCenter" ? "selected" : ""}>顶部居中 (TopCenter: 0.5,0 | Align 0.5,0)</option>
        <option value="TopRight" ${widget.anchor === "TopRight" ? "selected" : ""}>右上 (TopRight: 1,0 | Align 1,0)</option>
        <option value="BottomLeft" ${widget.anchor === "BottomLeft" ? "selected" : ""}>左下 (BottomLeft: 0,1 | Align 0,1)</option>
        <option value="BottomCenter" ${widget.anchor === "BottomCenter" ? "selected" : ""}>底部居中 (BottomCenter: 0.5,1 | Align 0.5,1)</option>
        <option value="BottomRight" ${widget.anchor === "BottomRight" ? "selected" : ""}>右下 (BottomRight: 1,1 | Align 1,1)</option>
        <option value="Center" ${widget.anchor === "Center" ? "selected" : ""}>正中 (Center: 0.5,0.5 | Align 0.5,0.5)</option>
      </select>
      <span style="font-size: 9px; color: #10b981;">自动适配对齐，杜绝进 UE5 坐标飞出或错位！</span>
    </div>

    <!-- 数据源绑定 -->
    <div class="form-group">
      <label>🔗 数据源绑定 (Data Binding):</label>
      <input type="text" class="input-text" value="${widget.binding || ''}" placeholder="例如: Player.CurrentHP" onchange="updateWidgetField('${widget.id}', 'binding', this.value)" />
      <span style="font-size: 10px; color: #64748b;">绑定至 UE5 蓝图变量或 DataTable 行属性</span>
    </div>
  `;
}

// 挑选美术素材槽位贴图
function pickArtForWidgetSlot(widgetId, slotKey) {
  openAssetPicker("image", (selectedPath, fileObj) => {
    const w = hudLayoutState.widgets.find((x) => x.id === widgetId);
    if (!w) return;
    if (!w.artSlots) w.artSlots = {};

    const rawPath = fileObj ? fileObj.absPath : selectedPath;
    w.artSlots[slotKey] = rawPath;

    // 智能获取贴图分辨率并提示按比例重置
    const img = new Image();
    img.onload = function() {
      showToast(`🎨 已绑定素材: ${fileObj ? fileObj.name : rawPath.split('/').pop()} (${img.naturalWidth}x${img.naturalHeight})`);
    };
    img.src = `/asset-view?path=${encodeURIComponent(rawPath)}`;

    renderHudCanvas();
    renderInspector(w);
  });
}

function toggleAspectRatioLock(widgetId) {
  const w = hudLayoutState.widgets.find((x) => x.id === widgetId);
  if (w) {
    w.lockAspectRatio = !w.lockAspectRatio;
    renderInspector(w);
    showToast(w.lockAspectRatio ? "🔗 已锁定等比缩放" : "🔓 已解除等比锁定");
  }
}

function updateWidgetScale(widgetId, val) {
  const w = hudLayoutState.widgets.find((x) => x.id === widgetId);
  if (w) {
    w.scale = parseFloat(val) || 1.0;
    const disp = document.getElementById("scaleDisplayVal");
    if (disp) disp.textContent = `${w.scale.toFixed(2)}x`;
    renderHudCanvas();
  }
}

function applyAnchorPreset(widgetId, anchorPreset) {
  const w = hudLayoutState.widgets.find((x) => x.id === widgetId);
  if (w) {
    w.anchor = anchorPreset;
    renderHudCanvas();
    renderInspector(w);
    showToast(`🎯 已应用 UE5 锚点对齐: ${anchorPreset}，进引擎 100% 贴合！`);
  }
}

function updateInspectorValues(widget) {
  const px = document.getElementById("inp_pos_x");
  const py = document.getElementById("inp_pos_y");
  if (px) px.value = widget.position[0];
  if (py) py.value = widget.position[1];
}

function updateWidgetField(id, field, val) {
  const w = hudLayoutState.widgets.find((x) => x.id === id);
  if (w) {
    w[field] = val;
    renderHudCanvas();
  }
}

function updateWidgetPos(id, axis, val) {
  const w = hudLayoutState.widgets.find((x) => x.id === id);
  if (w) {
    w.position[axis] = parseInt(val) || 0;
    renderHudCanvas();
  }
}

function updateWidgetSize(id, axis, val) {
  const w = hudLayoutState.widgets.find((x) => x.id === id);
  if (w) {
    w.size[axis] = Math.max(10, parseInt(val) || 10);
    renderHudCanvas();
  }
}

function deleteSelectedWidget() {
  if (!selectedHudWidgetId) return;
  hudLayoutState.widgets = hudLayoutState.widgets.filter((w) => w.id !== selectedHudWidgetId);
  selectedHudWidgetId = null;
  renderHudCanvas();
  renderInspector(null);
  showToast("🗑️ 控件已从画布中删除");
}

async function saveHudLayout() {
  try {
    const resp = await fetch("/api/hud/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ layout: hudLayoutState })
    });
    const res = await resp.json();
    if (res.success) {
      showToast("💾 HUD 画布布局已成功保存至项目！");
    }
  } catch (err) {
    showToast("❌ 保存 HUD 失败: " + err.message);
  }
}

function toggleHudPlayMode() {
  isHudPlayMode = !isHudPlayMode;
  const btn = document.getElementById("btnToggleHudPlay");
  const icon = document.getElementById("hudPlayIcon");
  const text = document.getElementById("hudPlayText");
  const consoleEl = document.getElementById("hudSandboxConsole");

  if (isHudPlayMode) {
    if (btn) btn.className = "btn btn-primary btn-sm glow";
    if (icon) icon.textContent = "⏹️";
    if (text) text.textContent = "退出试玩测试";
    if (consoleEl) consoleEl.style.display = "block";
    showToast("🎮 已进入 HUD 试玩沙盒模式！可直接点击按键与扣血模拟！");
  } else {
    if (btn) btn.className = "btn btn-emerald btn-sm";
    if (icon) icon.textContent = "▶️";
    if (text) text.textContent = "进入交互试玩模式";
    if (consoleEl) consoleEl.style.display = "none";
    showToast("⏸️ 已退出试玩模式，恢复编辑排布状态。");
  }
  renderHudCanvas();
}

function simulateHudDamage(amount) {
  hudSimulatedHP = Math.max(0, hudSimulatedHP - amount);
  renderHudCanvas();
  showToast(`💥 模拟受到攻击！扣除 ${amount} HP！`);
}

function simulateHudHeal(amount) {
  hudSimulatedHP = Math.min(100, hudSimulatedHP + amount);
  renderHudCanvas();
  showToast(`💚 模拟治愈！恢复 ${amount} HP！`);
}

function simulateHudCoins(amount) {
  hudSimulatedCoins += amount;
  renderHudCanvas();
  showToast(`🪙 获得 +${amount} 生化金币！`);
}

function simulateHudReload() {
  const mask = document.getElementById("hudReloadMask");
  if (mask) {
    mask.style.display = "flex";
    setTimeout(() => {
      mask.style.display = "none";
      showToast("✅ 武器换弹完毕！弹夹已装满！");
    }, 1200);
  }
}

async function exportUE5UMGScript() {
  try {
    const resp = await fetch("/api/hud/export-umg", { method: "POST" });
    const res = await resp.json();
    if (res.pythonScript) {
      alert("✅ 已生成 UE5 原生 UMG 蓝图 Python 自动化脚本！\n可在 UE5 编辑器中一键运行生成 WBP_CombatHUD.uasset。\n\n" + res.pythonScript);
    }
  } catch (err) {
    showToast("❌ 导出失败: " + err.message);
  }
}

/* ==============================================================================
   4. 🧬 动态自定义属性扩展系统 (Custom Properties Engine)
   ============================================================================== */
let currentCustomPropTargetTable = "DT_Characters";

function openCustomPropModal(tableName) {
  currentCustomPropTargetTable = tableName || "DT_Characters";
  const hiddenInp = document.getElementById("customPropTargetTable");
  const titleEl = document.getElementById("customPropModalTitle");
  const modal = document.getElementById("customPropModal");

  if (hiddenInp) hiddenInp.value = currentCustomPropTargetTable;
  if (titleEl) titleEl.textContent = `➕ 为 ${currentCustomPropTargetTable} 添加自定义属性`;
  if (modal) modal.classList.add("active");
}

function closeCustomPropModal() {
  const modal = document.getElementById("customPropModal");
  if (modal) modal.classList.remove("active");
}

function onCustomPropTypeChanged(val) {
  // 根据类型给默认值提示
  const defInp = document.getElementById("customPropDefault");
  if (!defInp) return;
  if (val === "float") defInp.placeholder = "例如: 1.5";
  else if (val === "int") defInp.placeholder = "例如: 3";
  else if (val === "percent") defInp.placeholder = "例如: 0.25 (25%)";
  else if (val === "bool") defInp.placeholder = "true 或 false";
  else if (val === "color") defInp.placeholder = "#ff0055";
  else defInp.placeholder = "留空则按类型默认值填充";
}

async function handleConfirmAddCustomProp() {
  const keyInp = document.getElementById("customPropKey");
  const nameInp = document.getElementById("customPropName");
  const typeInp = document.getElementById("customPropType");
  const defInp = document.getElementById("customPropDefault");
  const scopeInp = document.getElementById("customPropScopeTable");

  const key = keyInp ? keyInp.value.trim() : "";
  const name = nameInp ? nameInp.value.trim() : "";
  const propType = typeInp ? typeInp.value : "float";
  const defaultVal = defInp ? defInp.value.trim() : "";
  const isTableScope = scopeInp ? scopeInp.checked : true;

  if (!key) {
    showToast("⚠️ 请输入属性英文标识 (Key)！");
    return;
  }

  const propDef = {
    displayName: name || key,
    type: propType,
    defaultValue: defaultVal || undefined,
    scope: isTableScope ? "table" : "instance"
  };

  try {
    const resp = await fetch("/api/custom-props/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        table: currentCustomPropTargetTable,
        key: key,
        definition: propDef
      })
    });
    const res = await resp.json();
    if (res.success) {
      showToast(`🎉 成功为 ${currentCustomPropTargetTable} 注入自定义属性 [${key}: ${name}]！`);
      closeCustomPropModal();
      // 若是全表推广，向当前表草稿的所有行批量注入该属性默认值
      if (isTableScope && state.current) {
        const tableKey = currentCustomPropTargetTable === "DT_Characters" ? "characters" : (currentCustomPropTargetTable === "DT_Weapons" ? "weapons" : "enemies");
        if (state.current[tableKey]) {
          Object.values(state.current[tableKey]).forEach((row) => {
            if (row[key] === undefined) {
              row[key] = defaultVal || 0;
            }
          });
          updateDiffState();
        }
      }
    } else {
      showToast("❌ 添加属性失败: " + (res.error || "未知异常"));
    }
  } catch (err) {
    showToast("❌ 请求失败: " + err.message);
  }
}

// 扩展初始化钩子：在主程序启动时顺带初始化 HUD 画布并检查脚手架横幅
const origInitApp = typeof initApp === "function" ? initApp : null;
initApp = async function() {
  if (origInitApp) await origInitApp();
  if (state && state.project) {
    checkScaffoldNotice(state.project);
  }
  initHudStudio();
};
