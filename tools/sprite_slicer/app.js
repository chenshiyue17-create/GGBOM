// ==========================================================================
// GGBOM SPRITE STUDIO - SMART CONTOUR & ANTI-COLLISION ENGINE
// ==========================================================================

const API_BASE = "";

// State
let rawTreeData = [];
let currentFileObj = null; // { id, filename, rel_path, default_cat, default_sub, default_base, default_align }
let imageElement = new Image();
let imageWidth = 0;
let imageHeight = 0;

let zoom = 1.0;
let panX = 0;
let panY = 0;
let isPanning = false;
let startPanX = 0;
let startPanY = 0;

let currentTool = "select"; // "select", "draw", "wand"
let boxes = []; // Array of { id, x, y, w, h, label, contour: [[x, y], ...] }
let selectedBoxId = null;

let isContourEnabled = true;
let alphaThreshold = 15;

// Drawing state
let isDrawing = false;
let drawStartX = 0;
let drawStartY = 0;

// Dragging / Resizing state
let isDraggingBox = false;
let isResizingHandle = false;
let activeHandle = null;
let dragStartX = 0;
let dragStartY = 0;
let originalBox = null;

// Animation Player
let isPlaying = false;
let animTimer = null;
let currentAnimFrame = 0;
let fps = 8;

// DOM Elements
const canvasStage = document.getElementById("canvas-stage");
const mainCanvas = document.getElementById("main-canvas");
const mainCtx = mainCanvas.getContext("2d");
const contoursSvg = document.getElementById("contours-svg");
const boxesOverlay = document.getElementById("boxes-overlay");
const canvasViewport = document.getElementById("canvas-viewport");

const assetTreeEl = document.getElementById("asset-tree");
const assetSearchEl = document.getElementById("asset-search");
const boxCountEl = document.getElementById("box-count");
const framesStripEl = document.getElementById("frames-strip");

const animCanvas = document.getElementById("anim-canvas");
const animCtx = animCanvas.getContext("2d");
const btnPlayAnim = document.getElementById("btn-play-anim");
const fpsSlider = document.getElementById("fps-slider");
const fpsValEl = document.getElementById("fps-val");

const propX = document.getElementById("prop-x");
const propY = document.getElementById("prop-y");
const propW = document.getElementById("prop-w");
const propH = document.getElementById("prop-h");
const propLabel = document.getElementById("prop-label");
const selectedBoxIdEl = document.getElementById("selected-box-id");
const contourPtsCount = document.getElementById("contour-pts-count");
const btnRecomputeContour = document.getElementById("btn-recompute-contour");

const exportCategoryEl = document.getElementById("export-category");
const exportSubfolderEl = document.getElementById("export-subfolder");
const exportBasenameEl = document.getElementById("export-basename");
const exportCollisionModeEl = document.getElementById("export-collision-mode");
const folderStatusBadge = document.getElementById("folder-status-badge");
const padSlider = document.getElementById("pad-slider");
const padValEl = document.getElementById("pad-val");
const chkSmartMask = document.getElementById("chk-smart-mask");
const btnExport = document.getElementById("btn-export");
const statusResult = document.getElementById("status-result");
const btnRefreshTree = document.getElementById("btn-refresh-tree");

const btnToggleContour = document.getElementById("btn-toggle-contour");
const inputThresh = document.getElementById("input-thresh");

// Modal Elements
const exportModal = document.getElementById("export-modal");
const btnCloseModal = document.getElementById("btn-close-modal");
const modalSavedPath = document.getElementById("modal-saved-path");
const modalSavedSpecs = document.getElementById("modal-saved-specs");
const modalFileCount = document.getElementById("modal-file-count");
const modalGalleryGrid = document.getElementById("modal-gallery-grid");
const modalBtnOpenFinder = document.getElementById("modal-btn-open-finder");
const modalBtnCopyPath = document.getElementById("modal-btn-copy-path");
let lastExportData = null;

// Folder Switching & Live Preview Elements
const currentFolderBadge = document.getElementById("current-folder-badge");
const btnFolderToggle = document.getElementById("btn-folder-toggle");
const folderDrawer = document.getElementById("folder-drawer");
const inputCustomFolder = document.getElementById("input-custom-folder");
const btnBrowseFolder = document.getElementById("btn-browse-folder");
const btnLoadCustomFolder = document.getElementById("btn-load-custom-folder");
const livePathPreviewEl = document.getElementById("live-path-preview");

// Cut Lines State (自由控制横竖切线)
let hCutLines = []; // Array of { id, y }
let vCutLines = []; // Array of { id, x }
let isDraggingCutLine = false;
let activeCutLine = null; // { type: 'h'|'v', id }

// Cut Lines DOM Elements
const cutlinesOverlay = document.getElementById("cutlines-overlay");
const toolCutlinesBtn = document.getElementById("tool-cutlines");
const btnAddHLine = document.getElementById("btn-add-hline");
const btnAddVLine = document.getElementById("btn-add-vline");
const btnSliceByCutlines = document.getElementById("btn-slice-by-cutlines");
const btnClearCutlines = document.getElementById("btn-clear-cutlines");
const cutlineCountBadge = document.getElementById("cutline-count-badge");
const btnGridPreset2x4 = document.getElementById("btn-grid-preset-2x4");
const btnGridPreset1x8 = document.getElementById("btn-grid-preset-1x8");
const btnGridPreset1x4 = document.getElementById("btn-grid-preset-1x4");
const btnGridPreset3x3 = document.getElementById("btn-grid-preset-3x3");

// ==========================================================================
// 0. PROGRESS PERSISTENCE SYSTEM (进度永久化引擎 - 本地/服务双重备份)
// ==========================================================================

const LOCAL_STORAGE_PROGRESS_KEY = "ggbom_slicer_progress";
let projectProgress = {
    active_folder: "",
    last_selected_rel_path: "",
    files_progress: {}
};
let autoSaveTimer = null;
let isRestoringProgress = false;

const saveStatusBadge = document.getElementById("save-status-badge");
const saveStatusText = document.getElementById("save-status-text");
const btnSaveProgress = document.getElementById("btn-save-progress");
const btnResetCurrentProgress = document.getElementById("btn-reset-current-progress");

async function loadProjectProgress() {
    // 1. 先读本地 localStorage，保障即时离线可用
    try {
        const local = localStorage.getItem(LOCAL_STORAGE_PROGRESS_KEY);
        if (local) {
            const parsed = JSON.parse(local);
            if (parsed && typeof parsed === "object") {
                projectProgress = parsed;
                if (!projectProgress.files_progress) projectProgress.files_progress = {};
            }
        }
    } catch (e) {
        console.warn("localStorage load failed:", e);
    }

    // 2. 再从服务端 /api/slicer/progress 获取持久化存储做深度合并
    try {
        const res = await fetch(API_BASE + "/api/slicer/progress");
        if (res.ok) {
            const serverData = await res.json();
            if (serverData && typeof serverData === "object") {
                if (serverData.active_folder) projectProgress.active_folder = serverData.active_folder;
                if (serverData.last_selected_rel_path) projectProgress.last_selected_rel_path = serverData.last_selected_rel_path;
                if (serverData.files_progress && typeof serverData.files_progress === "object") {
                    if (!projectProgress.files_progress) projectProgress.files_progress = {};
                    for (const [relPath, fileProg] of Object.entries(serverData.files_progress)) {
                        const localItem = projectProgress.files_progress[relPath];
                        if (!localItem || (fileProg.lastSaved && fileProg.lastSaved >= (localItem.lastSaved || 0))) {
                            projectProgress.files_progress[relPath] = fileProg;
                        }
                    }
                }
            }
        }
    } catch (e) {
        console.warn("Server progress fetch failed, using local cache:", e);
    }
}

function saveCurrentFileProgress(forceSync = false) {
    if (!currentFileObj) return;

    let alignMode = "bottom_center";
    const checkedRadio = document.querySelector('input[name="align-mode"]:checked');
    if (checkedRadio) alignMode = checkedRadio.value;

    const fileProg = {
        boxes: JSON.parse(JSON.stringify(boxes || [])),
        hCutLines: JSON.parse(JSON.stringify(hCutLines || [])),
        vCutLines: JSON.parse(JSON.stringify(vCutLines || [])),
        selectedBoxId: selectedBoxId,
        exportCategory: exportCategoryEl ? exportCategoryEl.value : "01_Player",
        exportSubfolder: exportSubfolderEl ? exportSubfolderEl.value.trim() : "",
        exportBasename: exportBasenameEl ? exportBasenameEl.value.trim() : "",
        alignMode: alignMode,
        padding: padSlider ? parseInt(padSlider.value) : 10,
        fps: fpsSlider ? parseInt(fpsSlider.value) : 8,
        isContourEnabled: isContourEnabled,
        alphaThreshold: alphaThreshold,
        exportSheet: document.getElementById("chk-generate-sheet") ? document.getElementById("chk-generate-sheet").checked : true,
        smartMask: chkSmartMask ? chkSmartMask.checked : true,
        lastSaved: Date.now()
    };

    if (!projectProgress.files_progress) projectProgress.files_progress = {};
    projectProgress.files_progress[currentFileObj.rel_path] = fileProg;
    projectProgress.last_selected_rel_path = currentFileObj.rel_path;

    try {
        localStorage.setItem(LOCAL_STORAGE_PROGRESS_KEY, JSON.stringify(projectProgress));
    } catch (e) {
        console.warn("localStorage save failed:", e);
    }

    updateSaveStatusUI("saved");

    if (forceSync) {
        syncProgressToServer();
    } else {
        debounceAutoSave();
    }
}

function debounceAutoSave() {
    if (autoSaveTimer) clearTimeout(autoSaveTimer);
    updateSaveStatusUI("saving");
    autoSaveTimer = setTimeout(() => {
        syncProgressToServer();
    }, 400);
}

async function syncProgressToServer() {
    try {
        const payload = {
            active_folder: projectProgress.active_folder,
            last_selected_rel_path: projectProgress.last_selected_rel_path,
            files_progress: projectProgress.files_progress
        };
        const res = await fetch(API_BASE + "/api/slicer/save-progress", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            updateSaveStatusUI("saved");
        }
    } catch (e) {
        console.warn("Sync progress to server failed:", e);
    }
}

function updateSaveStatusUI(state) {
    if (!saveStatusBadge || !saveStatusText) return;
    const now = new Date();
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
    if (state === "saving") {
        saveStatusBadge.className = "save-badge saving";
        saveStatusText.textContent = "💾 正在自动保存...";
    } else {
        saveStatusBadge.className = "save-badge saved";
        saveStatusText.textContent = `💾 进度已保存 (${timeStr})`;
    }
}

async function resetCurrentFileProgress() {
    if (!currentFileObj) return;
    if (!confirm(`确定要重置当前图片【${currentFileObj.filename}】的所有切片选区与切线进度吗？`)) return;

    if (projectProgress.files_progress && projectProgress.files_progress[currentFileObj.rel_path]) {
        delete projectProgress.files_progress[currentFileObj.rel_path];
    }
    try {
        localStorage.setItem(LOCAL_STORAGE_PROGRESS_KEY, JSON.stringify(projectProgress));
        await fetch(API_BASE + "/api/slicer/reset-progress", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rel_path: currentFileObj.rel_path })
        });
    } catch (e) {}

    clearCutLines();
    boxes = [];
    selectedBoxId = null;
    renderBoxesAndContours();
    updatePreviewStrip();
    autoDetectInitial();
    showStatus(`↺ 已重置素材【${currentFileObj.filename}】的进度，并重新智能推荐`, true);
}

// ==========================================================================
// 1. INITIALIZATION & ASSET LOADING
// ==========================================================================

async function init() {
    setupEventListeners();
    await loadProjectProgress();
    await loadCurrentFolderInfo();
    await loadAssetTree();
}

async function loadCurrentFolderInfo() {
    try {
        const res = await fetch(API_BASE + "/api/current-folder");
        if (res.ok) {
            const data = await res.json();
            if (currentFolderBadge && data.display_name) {
                currentFolderBadge.textContent = data.display_name + " ▾";
                currentFolderBadge.title = data.current_folder;
            }
            if (inputCustomFolder && data.current_folder) {
                inputCustomFolder.value = data.current_folder;
            }
        }
    } catch (e) {
        console.warn("Could not fetch current folder info:", e);
    }
}

function extractTreeList(input) {
    if (Array.isArray(input)) return input;
    if (input && Array.isArray(input.tree)) return input.tree;
    if (input && Array.isArray(input.data)) return input.data;
    if (input && input.data && Array.isArray(input.data.tree)) return input.data.tree;
    return [];
}

async function switchRawFolder(newPath) {
    if (!newPath || !newPath.trim()) return;
    if (assetTreeEl) {
        assetTreeEl.innerHTML = `<div class="loading-spinner" style="padding:15px;color:var(--primary);">正在扫描指定文件夹: ${newPath.trim()}...</div>`;
    }
    try {
        const res = await fetch(API_BASE + "/api/set-raw-folder", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ folder: newPath.trim() })
        });
        const data = await res.json();
        if (data.success) {
            if (currentFolderBadge) {
                currentFolderBadge.textContent = (data.display_name || newPath.trim().split('/').pop() || newPath.trim()) + " ▾";
                currentFolderBadge.title = data.active_folder || newPath.trim();
            }
            if (inputCustomFolder) inputCustomFolder.value = data.active_folder || newPath.trim();
            if (folderDrawer) folderDrawer.style.display = "none";
            rawTreeData = extractTreeList(data.data || data);
            renderAssetTree(rawTreeData);
        } else {
            alert("⚠️ 打开文件夹失败: " + (data.error || "路径不存在或无法访问"));
            await loadAssetTree();
        }
    } catch (e) {
        alert("⚠️ 文件夹切换请求异常: " + e.message);
        await loadAssetTree();
    }
}

async function browseFolderDialog() {
    if (btnBrowseFolder) btnBrowseFolder.textContent = "⏳...";
    try {
        const res = await fetch(API_BASE + "/api/select-folder-dialog", { method: 'POST' });
        const data = await res.json();
        if (data.success && data.folder) {
            if (currentFolderBadge) {
                currentFolderBadge.textContent = (data.display_name || data.folder.split('/').pop() || data.folder) + " ▾";
                currentFolderBadge.title = data.folder;
            }
            if (inputCustomFolder) inputCustomFolder.value = data.folder;
            if (folderDrawer) folderDrawer.style.display = "none";
            rawTreeData = extractTreeList(data.data || data);
            renderAssetTree(rawTreeData);
        }
    } catch (e) {
        console.error("Browse dialog error:", e);
    } finally {
        if (btnBrowseFolder) btnBrowseFolder.textContent = "浏览...";
    }
}

function toggleFolderDrawer() {
    if (!folderDrawer) return;
    const isHidden = folderDrawer.style.display === "none" || !folderDrawer.style.display;
    folderDrawer.style.display = isHidden ? "flex" : "none";
    if (isHidden && inputCustomFolder) {
        inputCustomFolder.focus();
    }
}

function updateLivePathPreview() {
    if (!livePathPreviewEl) return;
    const cat = exportCategoryEl ? exportCategoryEl.value : "03_Weapons";
    const sub = exportSubfolderEl ? exportSubfolderEl.value.trim() || "SubFolder" : "SubFolder";
    const base = exportBasenameEl ? exportBasenameEl.value.trim() || "T_Sprite" : "T_Sprite";
    
    const b = boxes.find(bx => bx.id === selectedBoxId) || (boxes.length > 0 ? boxes[0] : null);
    const frameTag = b && b.label ? b.label : "01";
    
    livePathPreviewEl.textContent = `Content/美术/Art/${cat}/${sub}/${base}_${frameTag}.png`;
}

async function loadAssetTree() {
    assetTreeEl.innerHTML = `<div class="loading-spinner" style="padding:15px;color:var(--primary);">正在连接美术素材库...</div>`;
    try {
        const res = await fetch(API_BASE + "/api/raw-tree");
        if (!res.ok) throw new Error("HTTP " + res.status);
        const json = await res.json();
        rawTreeData = extractTreeList(json);
        renderAssetTree(rawTreeData);
    } catch (e) {
        assetTreeEl.innerHTML = `<div class="error" style="color:var(--danger);padding:10px;">❌ 加载素材库失败: ${e.message}</div>`;
    }
}

function renderAssetTree(inputData, filterQuery = "") {
    assetTreeEl.innerHTML = "";
    const tree = extractTreeList(inputData);
    let totalRendered = 0;
    let firstFileObj = null;
    let firstFileElement = null;

    if (!Array.isArray(tree) || tree.length === 0) {
        assetTreeEl.innerHTML = `<div style="padding:15px;color:var(--text-dim);font-size:12px;">当前文件夹内未发现图片素材</div>`;
        return;
    }

    tree.forEach(group => {
        const matchingFiles = group.files.filter(fObj => {
            if (!filterQuery) return true;
            const q = filterQuery.toLowerCase();
            return fObj.filename.toLowerCase().includes(q) || group.folder.toLowerCase().includes(q);
        });

        if (matchingFiles.length === 0) return;

        const grpEl = document.createElement("div");
        grpEl.className = "folder-group";
        
        const titleEl = document.createElement("div");
        titleEl.className = "folder-title";
        titleEl.innerHTML = `<span>📂</span> <span>${group.folder}</span> <span style="font-size:10px;color:var(--text-dim);">(${matchingFiles.length})</span>`;
        
        const listEl = document.createElement("div");
        listEl.className = "file-list";
        
        matchingFiles.forEach(fObj => {
            const fileItem = document.createElement("div");
            fileItem.className = `file-item ${currentFileObj && currentFileObj.id === fObj.id ? 'active' : ''}`;
            fileItem.textContent = fObj.filename;
            fileItem.title = fObj.rel_path;
            
            fileItem.onclick = () => selectRawFile(fObj, fileItem);
            listEl.appendChild(fileItem);

            // 优先匹配上次最后编辑的素材
            if (projectProgress && projectProgress.last_selected_rel_path === fObj.rel_path) {
                targetFileObj = fObj;
                targetFileElement = fileItem;
            }

            if (!firstFileObj) {
                firstFileObj = fObj;
                firstFileElement = fileItem;
            }
            totalRendered++;
        });

        titleEl.onclick = () => {
            listEl.style.display = listEl.style.display === "none" ? "flex" : "none";
        };

        grpEl.appendChild(titleEl);
        grpEl.appendChild(listEl);
        assetTreeEl.appendChild(grpEl);
    });

    if (totalRendered === 0) {
        assetTreeEl.innerHTML = `<div style="padding:15px;color:var(--text-dim);font-size:12px;">未搜索到匹配的素材</div>`;
        return;
    }

    if (targetFileObj && targetFileElement) {
        selectRawFile(targetFileObj, targetFileElement);
    } else if (!currentFileObj && firstFileObj) {
        selectRawFile(firstFileObj, firstFileElement);
    }
}

let targetFileObj = null;
let targetFileElement = null;

function selectRawFile(fObj, el) {
    // 切换离开前，先保存上一张图片的编辑进度（强制同步）
    if (currentFileObj && currentFileObj.rel_path !== fObj.rel_path) {
        saveCurrentFileProgress(true);
    }

    document.querySelectorAll(".file-item").forEach(i => i.classList.remove("active"));
    if (el) el.classList.add("active");
    
    currentFileObj = fObj;
    projectProgress.last_selected_rel_path = fObj.rel_path;
    
    // Auto-populate unique non-colliding destination configs!
    if (fObj.default_cat) exportCategoryEl.value = fObj.default_cat;
    if (fObj.default_sub) exportSubfolderEl.value = fObj.default_sub;
    if (fObj.default_base) exportBasenameEl.value = fObj.default_base;
    if (fObj.default_align) {
        const r = document.querySelector(`input[name="align-mode"][value="${fObj.default_align}"]`);
        if (r) r.checked = true;
    }

    checkTargetFolderStatus();
    updateLivePathPreview();
    
    imageElement = new Image();
    imageElement.crossOrigin = "anonymous";
    imageElement.onload = () => {
        imageWidth = imageElement.naturalWidth || imageElement.width;
        imageHeight = imageElement.naturalHeight || imageElement.height;
        
        mainCanvas.width = imageWidth;
        mainCanvas.height = imageHeight;
        
        contoursSvg.setAttribute("width", imageWidth);
        contoursSvg.setAttribute("height", imageHeight);
        contoursSvg.setAttribute("viewBox", `0 0 ${imageWidth} ${imageHeight}`);

        boxesOverlay.style.width = imageWidth + "px";
        boxesOverlay.style.height = imageHeight + "px";
        
        mainCtx.clearRect(0, 0, imageWidth, imageHeight);
        mainCtx.drawImage(imageElement, 0, 0);
        
        fitToScreen();

        // 检查该素材是否已有永久化保存的进度
        const hist = projectProgress.files_progress && projectProgress.files_progress[fObj.rel_path];
        if (hist && Array.isArray(hist.boxes) && hist.boxes.length > 0) {
            isRestoringProgress = true;
            boxes = JSON.parse(JSON.stringify(hist.boxes || []));
            hCutLines = JSON.parse(JSON.stringify(hist.hCutLines || []));
            vCutLines = JSON.parse(JSON.stringify(hist.vCutLines || []));
            selectedBoxId = hist.selectedBoxId || (boxes.length > 0 ? boxes[0].id : null);

            // 恢复各项配置与属性
            if (hist.exportCategory && exportCategoryEl) exportCategoryEl.value = hist.exportCategory;
            if (hist.exportSubfolder && exportSubfolderEl) exportSubfolderEl.value = hist.exportSubfolder;
            if (hist.exportBasename && exportBasenameEl) exportBasenameEl.value = hist.exportBasename;
            if (hist.alignMode) {
                const r = document.querySelector(`input[name="align-mode"][value="${hist.alignMode}"]`);
                if (r) r.checked = true;
            }
            if (hist.padding !== undefined && padSlider) {
                padSlider.value = hist.padding;
                if (padValEl) padValEl.textContent = `${hist.padding} px`;
            }
            if (hist.fps !== undefined && fpsSlider) {
                fps = hist.fps;
                fpsSlider.value = hist.fps;
                if (fpsValEl) fpsValEl.textContent = `${hist.fps} FPS`;
            }
            if (hist.isContourEnabled !== undefined) {
                isContourEnabled = hist.isContourEnabled;
                if (btnToggleContour) {
                    if (isContourEnabled) btnToggleContour.classList.add("active");
                    else btnToggleContour.classList.remove("active");
                }
            }
            if (hist.alphaThreshold !== undefined && inputThresh) {
                alphaThreshold = hist.alphaThreshold;
                inputThresh.value = hist.alphaThreshold;
            }

            renderCutLines();
            renderBoxesAndContours();
            updatePreviewStrip();

            if (selectedBoxId) {
                const b = boxes.find(bx => bx.id === selectedBoxId);
                if (b) updatePropPanel(b);
            }
            checkTargetFolderStatus();
            updateLivePathPreview();

            if (!isPlaying && boxes.length > 0) {
                togglePlayAnim();
            }

            showStatus(`💾 已自动恢复【${fObj.filename}】上次保存的进度（${boxes.length} 个选区，${hCutLines.length + vCutLines.length} 条切线）`, true);
            isRestoringProgress = false;
        } else {
            // 新素材：清空切线并运行初始推荐
            clearCutLines();
            boxes = [];
            selectedBoxId = null;
            autoDetectInitial();
        }
    };
    imageElement.onerror = (err) => {
        console.error("Image load error:", err);
        showStatus("❌ 加载图片失败: " + fObj.filename, false);
    };
    
    imageElement.src = API_BASE + "/api/raw-image?id=" + fObj.id;
}

async function checkTargetFolderStatus() {
    if (!folderStatusBadge) return;
    const cat = exportCategoryEl.value;
    const sub = exportSubfolderEl.value.trim();
    if (!sub) return;

    try {
        const res = await fetch(`${API_BASE}/api/check-folder?cat=${encodeURIComponent(cat)}&sub=${encodeURIComponent(sub)}`);
        const data = await res.json();
        if (data.exists && data.count > 0) {
            folderStatusBadge.className = "folder-badge existing";
            folderStatusBadge.textContent = `⚠️ 已有 ${data.count} 个切片`;
            folderStatusBadge.title = `目标路径已有 ${data.count} 个文件，将依据覆盖保护策略处理`;
        } else {
            folderStatusBadge.className = "folder-badge safe";
            folderStatusBadge.textContent = `● 新目录 (无冲突)`;
            folderStatusBadge.title = `全新独立目录，无覆盖风险`;
        }
    } catch (e) {
        console.error("Check folder error:", e);
    }
}

// ==========================================================================
// 2. CANVAS TRANSFORM & ZOOM / PAN
// ==========================================================================

function updateTransform() {
    canvasStage.style.transform = `translate(${panX}px, ${panY}px) scale(${zoom})`;
    const zoomLevelEl = document.getElementById("zoom-level");
    if (zoomLevelEl) zoomLevelEl.textContent = `${Math.round(zoom * 100)}%`;
}

function fitToScreen() {
    if (!imageWidth || !imageHeight) return;
    const vpW = canvasViewport.clientWidth - 80;
    const vpH = canvasViewport.clientHeight - 80;
    const scaleX = vpW / imageWidth;
    const scaleY = vpH / imageHeight;
    zoom = Math.min(1.0, Math.min(scaleX, scaleY));
    panX = 0;
    panY = 0;
    updateTransform();
}

// ==========================================================================
// 3. BOXES & SMART CONTOURS RENDERING
// ==========================================================================

function renderBoxesAndContours() {
    boxesOverlay.innerHTML = "";
    contoursSvg.innerHTML = "";
    
    boxes.forEach((b, idx) => {
        // 1. Render SVG Smart Outline Path
        if (isContourEnabled && b.contour && b.contour.length >= 3) {
            let pathD = "M " + b.contour.map(p => `${p[0]} ${p[1]}`).join(" L ") + " Z";
            const pathEl = document.createElementNS("http://www.w3.org/2000/svg", "path");
            pathEl.setAttribute("d", pathD);
            pathEl.setAttribute("class", `contour-path ${b.id === selectedBoxId ? "selected" : ""}`);
            contoursSvg.appendChild(pathEl);
        }

        // 2. Render Box Handles
        const boxEl = document.createElement("div");
        boxEl.className = `crop-box ${b.id === selectedBoxId ? "selected" : ""}`;
        boxEl.style.left = `${b.x}px`;
        boxEl.style.top = `${b.y}px`;
        boxEl.style.width = `${b.w}px`;
        boxEl.style.height = `${b.h}px`;
        boxEl.dataset.id = b.id;

        const badge = document.createElement("div");
        badge.className = "box-badge";
        badge.textContent = b.label || String(idx + 1).padStart(2, '0');
        boxEl.appendChild(badge);

        const dims = document.createElement("div");
        dims.className = "box-dims";
        dims.textContent = `${Math.round(b.w)} × ${Math.round(b.h)}`;
        boxEl.appendChild(dims);

        if (b.id === selectedBoxId) {
            ["nw", "ne", "sw", "se", "n", "s", "w", "e"].forEach(dir => {
                const handle = document.createElement("div");
                handle.className = `handle handle-${dir}`;
                handle.dataset.handle = dir;
                boxEl.appendChild(handle);
            });
        }

        boxesOverlay.appendChild(boxEl);
    });

    if (boxCountEl) boxCountEl.textContent = boxes.length;
    updatePreviewStrip();
    updatePropsPanel();
}

function selectBox(id) {
    selectedBoxId = id;
    renderBoxesAndContours();
}

function updatePropsPanel() {
    const b = boxes.find(bx => bx.id === selectedBoxId);
    if (b) {
        if (selectedBoxIdEl) selectedBoxIdEl.textContent = b.label || b.id;
        if (propX) propX.value = Math.round(b.x);
        if (propY) propY.value = Math.round(b.y);
        if (propW) propW.value = Math.round(b.w);
        if (propH) propH.value = Math.round(b.h);
        if (propLabel) propLabel.value = b.label || "";
        if (contourPtsCount) contourPtsCount.textContent = `${b.contour ? b.contour.length : 0} 描边点`;
    } else {
        if (selectedBoxIdEl) selectedBoxIdEl.textContent = "无";
        if (propX) propX.value = "";
        if (propY) propY.value = "";
        if (propW) propW.value = "";
        if (propH) propH.value = "";
        if (propLabel) propLabel.value = "";
        if (contourPtsCount) contourPtsCount.textContent = "0 点";
    }
    updateLivePathPreview();
}

async function recomputeContourForBox(b) {
    if (!currentFileObj || !b) return;
    try {
        const res = await fetch(API_BASE + "/api/compute-contour", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                id: currentFileObj.id,
                box: { x: b.x, y: b.y, w: b.w, h: b.h },
                threshold: alphaThreshold
            })
        });
        const data = await res.json();
        if (data.contour) {
            b.contour = data.contour;
            renderBoxesAndContours();
        }
    } catch (e) {
        console.error("Contour recompute failed", e);
    }
}

function screenToCanvasCoords(clientX, clientY) {
    const rect = canvasStage.getBoundingClientRect();
    const x = (clientX - rect.left) / zoom;
    const y = (clientY - rect.top) / zoom;
    return {
        x: Math.max(0, Math.min(imageWidth, x)),
        y: Math.max(0, Math.min(imageHeight, y))
    };
}

// ==========================================================================
// 4. DETECTION PRESETS
// ==========================================================================

async function autoDetect(mode = 'auto') {
    if (!currentFileObj) return;
    try {
        const res = await fetch(API_BASE + "/api/detect", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: currentFileObj.id, mode: mode, threshold: alphaThreshold })
        });
        const data = await res.json();
        if (data.boxes) {
            boxes = data.boxes.map((b, idx) => ({
                id: "box_" + Date.now() + "_" + idx,
                x: b.x,
                y: b.y,
                w: b.w,
                h: b.h,
                label: b.label || String(idx + 1).padStart(2, '0'),
                contour: b.contour || []
            }));
            selectedBoxId = boxes.length > 0 ? boxes[0].id : null;
            renderBoxesAndContours();
            setTool("select");
            if (!isPlaying && boxes.length > 0) {
                togglePlayAnim();
            }
            if (!isRestoringProgress) {
                saveCurrentFileProgress(true);
            }
        }
    } catch (e) {
        console.error("Auto detect failed", e);
    }
}

function autoDetectInitial() {
    if (!currentFileObj) return;
    const rel = currentFileObj.rel_path;
    if (rel.includes("子弹")) {
        autoDetect("horizontal_4");
    } else if (rel.includes("可破坏道具")) {
        autoDetect("horizontal_3");
    } else if (rel.includes("医疗兵") || rel.includes("敌人")) {
        autoDetect("grid_2x4");
    } else {
        autoDetect("auto");
    }
}

// ==========================================================================
// 4.5. CUT LINES ENGINE (可自由控制的横竖切线系统)
// ==========================================================================

function renderCutLines() {
    if (!cutlinesOverlay) return;
    cutlinesOverlay.style.width = imageWidth + "px";
    cutlinesOverlay.style.height = imageHeight + "px";
    cutlinesOverlay.innerHTML = "";

    // 1. 渲染横切线 (Horizontal Cut Lines)
    hCutLines.forEach(line => {
        const el = document.createElement("div");
        el.className = `cutline cutline-h ${activeCutLine && activeCutLine.id === line.id ? "active" : ""}`;
        el.style.top = `${line.y}px`;
        el.dataset.id = line.id;

        const badge = document.createElement("div");
        badge.className = "cutline-badge";
        badge.innerHTML = `<span>Y: ${Math.round(line.y)}</span><span class="badge-del" title="删除横切线">✕</span>`;

        const delBtn = badge.querySelector(".badge-del");
        if (delBtn) {
            delBtn.onmousedown = (e) => e.stopPropagation();
            delBtn.onclick = (e) => {
                e.stopPropagation();
                hCutLines = hCutLines.filter(l => l.id !== line.id);
                renderCutLines();
                if (!isRestoringProgress) saveCurrentFileProgress(false);
                showStatus(`已删除横切线 (Y: ${Math.round(line.y)})`, true);
            };
        }

        el.onmousedown = (e) => {
            if (e.target.classList.contains("badge-del")) return;
            isDraggingCutLine = true;
            activeCutLine = { type: 'h', id: line.id };
            renderCutLines();
            e.stopPropagation();
        };

        el.appendChild(badge);
        cutlinesOverlay.appendChild(el);
    });

    // 2. 渲染竖切线 (Vertical Cut Lines)
    vCutLines.forEach(line => {
        const el = document.createElement("div");
        el.className = `cutline cutline-v ${activeCutLine && activeCutLine.id === line.id ? "active" : ""}`;
        el.style.left = `${line.x}px`;
        el.dataset.id = line.id;

        const badge = document.createElement("div");
        badge.className = "cutline-badge";
        badge.innerHTML = `<span>X: ${Math.round(line.x)}</span><span class="badge-del" title="删除竖切线">✕</span>`;

        const delBtn = badge.querySelector(".badge-del");
        if (delBtn) {
            delBtn.onmousedown = (e) => e.stopPropagation();
            delBtn.onclick = (e) => {
                e.stopPropagation();
                vCutLines = vCutLines.filter(l => l.id !== line.id);
                renderCutLines();
                if (!isRestoringProgress) saveCurrentFileProgress(false);
                showStatus(`已删除竖切线 (X: ${Math.round(line.x)})`, true);
            };
        }

        el.onmousedown = (e) => {
            if (e.target.classList.contains("badge-del")) return;
            isDraggingCutLine = true;
            activeCutLine = { type: 'v', id: line.id };
            renderCutLines();
            e.stopPropagation();
        };

        el.appendChild(badge);
        cutlinesOverlay.appendChild(el);
    });

    if (cutlineCountBadge) {
        cutlineCountBadge.textContent = `${hCutLines.length} 横 / ${vCutLines.length} 竖`;
    }
}

function addHorizontalCutLine(y = null) {
    if (!imageHeight) {
        showStatus("请先选择一张原画素材！", false);
        return;
    }
    const targetY = y !== null ? y : Math.round(imageHeight / 2);
    const id = "hline_" + Date.now() + "_" + Math.random().toString(36).substr(2, 4);
    hCutLines.push({ id, y: targetY });
    renderCutLines();
    if (!isRestoringProgress) saveCurrentFileProgress(false);
    showStatus(`➕ 已添加横切线 (Y: ${targetY}px，可自由上下拖拽)`, true);
}

function addVerticalCutLine(x = null) {
    if (!imageWidth) {
        showStatus("请先选择一张原画素材！", false);
        return;
    }
    const targetX = x !== null ? x : Math.round(imageWidth / 2);
    const id = "vline_" + Date.now() + "_" + Math.random().toString(36).substr(2, 4);
    vCutLines.push({ id, x: targetX });
    renderCutLines();
    if (!isRestoringProgress) saveCurrentFileProgress(false);
    showStatus(`➕ 已添加竖切线 (X: ${targetX}px，可自由左右拖拽)`, true);
}

function clearCutLines() {
    hCutLines = [];
    vCutLines = [];
    renderCutLines();
    if (!isRestoringProgress) saveCurrentFileProgress(false);
    showStatus("🗑️ 已清空全部横竖切线", true);
}

function generateCutLinesGrid(rows, cols) {
    if (!imageWidth || !imageHeight) {
        showStatus("请先选择一张原画素材！", false);
        return;
    }
    hCutLines = [];
    vCutLines = [];

    // 生成横切线
    for (let r = 1; r < rows; r++) {
        hCutLines.push({
            id: "hline_grid_" + r + "_" + Date.now(),
            y: Math.round((imageHeight / rows) * r)
        });
    }

    // 生成竖切线
    for (let c = 1; c < cols; c++) {
        vCutLines.push({
            id: "vline_grid_" + c + "_" + Date.now(),
            x: Math.round((imageWidth / cols) * c)
        });
    }

    renderCutLines();
    if (!isRestoringProgress) saveCurrentFileProgress(false);
    showStatus(`📐 已生成 ${rows}行 × ${cols}列 切线网格（${hCutLines.length}横 / ${vCutLines.length}竖，鼠标可自由拖拽微调）`, true);
}

async function sliceByCutLines() {
    if (!imageWidth || !imageHeight) {
        showStatus("请先加载原画素材！", false);
        return;
    }
    if (hCutLines.length === 0 && vCutLines.length === 0) {
        showStatus("⚠️ 请先添加至少一条横切线或竖切线！", false);
        return;
    }

    // 收集横坐标与纵坐标切割点并去重排序
    const hPoints = Array.from(new Set([0, ...hCutLines.map(l => Math.round(l.y)).filter(y => y > 0 && y < imageHeight), imageHeight])).sort((a, b) => a - b);
    const vPoints = Array.from(new Set([0, ...vCutLines.map(l => Math.round(l.x)).filter(x => x > 0 && x < imageWidth), imageWidth])).sort((a, b) => a - b);

    const newBoxes = [];
    let idx = 1;
    for (let r = 0; r < hPoints.length - 1; r++) {
        const y1 = hPoints[r];
        const y2 = hPoints[r + 1];
        const h = y2 - y1;
        if (h < 5) continue;

        for (let c = 0; c < vPoints.length - 1; c++) {
            const x1 = vPoints[c];
            const x2 = vPoints[c + 1];
            const w = x2 - x1;
            if (w < 5) continue;

            newBoxes.push({
                id: "box_cut_" + Date.now() + "_" + idx,
                x: x1,
                y: y1,
                w: w,
                h: h,
                label: String(idx).padStart(2, '0'),
                contour: []
            });
            idx++;
        }
    }

    if (newBoxes.length === 0) {
        showStatus("⚠️ 切线分割未生成有效切片框", false);
        return;
    }

    boxes = newBoxes;
    selectedBoxId = boxes[0].id;
    renderBoxesAndContours();
    setTool("select");

    // 并发计算描边
    boxes.forEach(b => recomputeContourForBox(b));

    // 自动播放动画
    if (!isPlaying) {
        togglePlayAnim();
    }

    showStatus(`✂️ 成功根据横竖切线分割出 ${boxes.length} 个切片选区！`, true);
    if (!isRestoringProgress) saveCurrentFileProgress(true);
}

// ==========================================================================
// 5. PREVIEW STRIP & ANIMATION PLAYER
// ==========================================================================

function updatePreviewStrip() {
    if (!framesStripEl) return;
    framesStripEl.innerHTML = "";
    if (boxes.length === 0) {
        framesStripEl.innerHTML = `<div class="empty-hint">当前无选区框，点击工具栏绘制或使用预设</div>`;
        return;
    }

    boxes.forEach((b, idx) => {
        const card = document.createElement("div");
        card.className = `frame-thumb-card ${b.id === selectedBoxId ? "active" : ""}`;
        card.onclick = () => selectBox(b.id);

        const canvasBox = document.createElement("div");
        canvasBox.className = "thumb-canvas-box";

        const thumbCanvas = document.createElement("canvas");
        thumbCanvas.width = Math.max(1, b.w);
        thumbCanvas.height = Math.max(1, b.h);
        const tctx = thumbCanvas.getContext("2d");
        if (imageElement.complete) {
            if (b.contour && b.contour.length >= 3 && chkSmartMask.checked) {
                tctx.save();
                tctx.beginPath();
                b.contour.forEach((p, pi) => {
                    const lx = p[0] - b.x;
                    const ly = p[1] - b.y;
                    if (pi === 0) tctx.moveTo(lx, ly);
                    else tctx.lineTo(lx, ly);
                });
                tctx.closePath();
                tctx.clip();
                tctx.drawImage(imageElement, b.x, b.y, b.w, b.h, 0, 0, b.w, b.h);
                tctx.restore();
            } else {
                tctx.drawImage(imageElement, b.x, b.y, b.w, b.h, 0, 0, b.w, b.h);
            }
        }

        canvasBox.appendChild(thumbCanvas);
        card.appendChild(canvasBox);

        const info = document.createElement("div");
        info.className = "thumb-info";
        info.innerHTML = `<strong>#${idx + 1}</strong> ${Math.round(b.w)}×${Math.round(b.h)}`;
        card.appendChild(info);

        framesStripEl.appendChild(card);
    });

    renderAnimFrame(0);
}

function renderAnimFrame(frameIdx) {
    if (boxes.length === 0 || !imageElement.complete) return;
    const b = boxes[frameIdx % boxes.length];
    
    animCtx.clearRect(0, 0, animCanvas.width, animCanvas.height);
    
    const maxDim = Math.max(b.w, b.h);
    const scale = Math.min(130 / maxDim, 1.0);
    const dw = b.w * scale;
    const dh = b.h * scale;
    const dx = (animCanvas.width - dw) / 2;
    const dy = (animCanvas.height - dh) / 2;
    
    animCtx.drawImage(imageElement, b.x, b.y, b.w, b.h, dx, dy, dw, dh);
}

function togglePlayAnim() {
    isPlaying = !isPlaying;
    btnPlayAnim.textContent = isPlaying ? "⏸ 暂停动画" : "▶ 播放动画";
    btnPlayAnim.style.background = isPlaying ? "var(--accent-gradient)" : "var(--primary-gradient)";

    if (isPlaying) {
        startAnimLoop();
    } else {
        clearInterval(animTimer);
    }
}

function startAnimLoop() {
    clearInterval(animTimer);
    animTimer = setInterval(() => {
        if (boxes.length > 0) {
            currentAnimFrame = (currentAnimFrame + 1) % boxes.length;
            renderAnimFrame(currentAnimFrame);
        }
    }, 1000 / fps);
}

// ==========================================================================
// 6. EXPORT ACTION & MODAL POPUP
// ==========================================================================

async function exportArt() {
    if (!currentFileObj || boxes.length === 0) {
        showStatus("请先选择原画并添加裁切框！", false);
        return;
    }

    btnExport.disabled = true;
    btnExport.innerHTML = `<span class="btn-icon">⏳</span> 正在高精度智能抠图与对齐...`;

    try {
        const alignRadio = document.querySelector('input[name="align-mode"]:checked');
        const payload = {
            id: currentFileObj.id,
            category: exportCategoryEl.value,
            subfolder: exportSubfolderEl.value.trim(),
            base_name: exportBasenameEl.value.trim(),
            overwrite_mode: exportCollisionModeEl.value,
            align: alignRadio ? alignRadio.value : "center",
            pad: parseInt(padSlider.value),
            smart_mask: chkSmartMask.checked,
            generate_sheet: document.getElementById("chk-generate-sheet").checked,
            boxes: boxes.map((b, idx) => ({
                x: Math.round(b.x),
                y: Math.round(b.y),
                w: Math.round(b.w),
                h: Math.round(b.h),
                label: b.label || String(idx + 1).padStart(2, '0'),
                contour: b.contour || []
            }))
        };

        const res = await fetch(API_BASE + "/api/export", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.success) {
            showStatus(`✅ 导出成功！保存至 [${data.saved_dir}]`, true);
            showExportModal(data);
            checkTargetFolderStatus();
        } else {
            showStatus("❌ 导出失败: " + data.error, false);
        }
    } catch (e) {
        showStatus("❌ 导出异常: " + e.message, false);
    } finally {
        btnExport.disabled = false;
        btnExport.innerHTML = `<span class="btn-icon">🚀</span> <span class="btn-text">一键精准导出至工程</span>`;
    }
}

function showExportModal(data) {
    lastExportData = data;
    modalSavedPath.textContent = data.full_path || data.saved_dir;
    modalSavedSpecs.textContent = `单帧规范尺寸: ${data.frame_size[0]} × ${data.frame_size[1]} px (${data.saved_files.length} 个文件)`;
    modalFileCount.textContent = data.saved_files.length;
    
    modalGalleryGrid.innerHTML = "";
    data.saved_files.forEach(fn => {
        const card = document.createElement("div");
        card.className = "modal-gallery-card";
        
        const img = document.createElement("img");
        const relUrl = data.rel_folder ? `${data.rel_folder}/${fn}` : `${exportCategoryEl.value}/${exportSubfolderEl.value}/${fn}`;
        img.src = `${API_BASE}/api/exported-image?file=${encodeURIComponent(relUrl)}&t=${Date.now()}`;
        img.title = fn;
        
        const name = document.createElement("div");
        name.className = "modal-gallery-name";
        name.textContent = fn;
        
        card.appendChild(img);
        card.appendChild(name);
        modalGalleryGrid.appendChild(card);
    });

    exportModal.style.display = "flex";
}

function showStatus(msg, isSuccess) {
    if (!statusResult) return;
    statusResult.style.display = "block";
    statusResult.className = `status-result ${isSuccess ? "success" : "error"}`;
    statusResult.textContent = msg;
}

// ==========================================================================
// 7. EVENT LISTENERS & INTERACTION ENGINE
// ==========================================================================

function setupEventListeners() {
    // Toolbar Tools
    const toolSelectBtn = document.getElementById("tool-select");
    const toolDrawBtn = document.getElementById("tool-draw");
    const toolWandBtn = document.getElementById("tool-wand");

    if (toolSelectBtn) toolSelectBtn.onclick = () => setTool("select");
    if (toolDrawBtn) toolDrawBtn.onclick = () => setTool("draw");
    if (toolWandBtn) toolWandBtn.onclick = () => setTool("wand");
    if (toolCutlinesBtn) toolCutlinesBtn.onclick = () => setTool("cutlines");

    // Cut Lines Buttons
    if (btnAddHLine) btnAddHLine.onclick = () => addHorizontalCutLine();
    if (btnAddVLine) btnAddVLine.onclick = () => addVerticalCutLine();
    if (btnSliceByCutlines) btnSliceByCutlines.onclick = sliceByCutLines;
    if (btnClearCutlines) btnClearCutlines.onclick = clearCutLines;

    // Cut Lines Quick Grid Presets
    if (btnGridPreset2x4) btnGridPreset2x4.onclick = () => generateCutLinesGrid(2, 4);
    if (btnGridPreset1x8) btnGridPreset1x8.onclick = () => generateCutLinesGrid(1, 8);
    if (btnGridPreset1x4) btnGridPreset1x4.onclick = () => generateCutLinesGrid(1, 4);
    if (btnGridPreset3x3) btnGridPreset3x3.onclick = () => generateCutLinesGrid(3, 3);

    // Progress Persistence Buttons
    if (btnSaveProgress) {
        btnSaveProgress.onclick = () => {
            saveCurrentFileProgress(true);
            showStatus("💾 进度已永久保存到本地与服务！(退出/刷新不丢失，不同步到 UE)", true);
        };
    }
    if (btnResetCurrentProgress) {
        btnResetCurrentProgress.onclick = resetCurrentFileProgress;
    }

    // Folder Switcher Events
    if (btnFolderToggle) btnFolderToggle.onclick = toggleFolderDrawer;
    if (currentFolderBadge) currentFolderBadge.onclick = toggleFolderDrawer;
    if (btnBrowseFolder) btnBrowseFolder.onclick = browseFolderDialog;
    if (btnLoadCustomFolder) {
        btnLoadCustomFolder.onclick = () => {
            if (inputCustomFolder) switchRawFolder(inputCustomFolder.value);
        };
    }
    if (inputCustomFolder) {
        inputCustomFolder.onkeydown = (e) => {
            if (e.key === "Enter") switchRawFolder(inputCustomFolder.value);
        };
    }
    document.querySelectorAll(".preset-chip").forEach(chip => {
        chip.onclick = () => {
            const p = chip.dataset.path;
            if (p) switchRawFolder(p);
        };
    });

    // Prevent default drag & drop navigation across entire page (no more accidental tab redirect)
    window.addEventListener("dragover", (e) => { e.preventDefault(); }, false);
    window.addEventListener("drop", (e) => { e.preventDefault(); }, false);

    // Sidebar drop folder/image support
    const sidebarLeft = document.getElementById("sidebar-left");
    if (sidebarLeft) {
        sidebarLeft.ondragover = (e) => {
            e.preventDefault();
            sidebarLeft.style.borderColor = "var(--primary)";
        };
        sidebarLeft.ondragleave = () => {
            sidebarLeft.style.borderColor = "";
        };
        sidebarLeft.ondrop = async (e) => {
            e.preventDefault();
            sidebarLeft.style.borderColor = "";
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                const first = files[0];
                if (first.path) {
                    switchRawFolder(first.path);
                }
            }
        };
    }

    // Dynamic folder status check & live path update on inputs
    if (exportCategoryEl) {
        exportCategoryEl.onchange = () => {
            checkTargetFolderStatus();
            updateLivePathPreview();
            if (!isRestoringProgress) saveCurrentFileProgress(false);
        };
    }
    if (exportSubfolderEl) {
        exportSubfolderEl.oninput = () => {
            checkTargetFolderStatus();
            updateLivePathPreview();
            if (!isRestoringProgress) saveCurrentFileProgress(false);
        };
    }
    if (exportBasenameEl) {
        exportBasenameEl.oninput = () => {
            updateLivePathPreview();
            if (!isRestoringProgress) saveCurrentFileProgress(false);
        };
    }
    document.querySelectorAll('input[name="align-mode"]').forEach(r => {
        r.onchange = () => {
            if (!isRestoringProgress) saveCurrentFileProgress(false);
        };
    });

    // Smart Contour Toggle
    if (btnToggleContour) {
        btnToggleContour.onclick = () => {
            isContourEnabled = !isContourEnabled;
            btnToggleContour.classList.toggle("active", isContourEnabled);
            renderBoxesAndContours();
            if (!isRestoringProgress) saveCurrentFileProgress(false);
        };
    }

    // Alpha threshold
    if (inputThresh) {
        inputThresh.onchange = () => {
            alphaThreshold = parseInt(inputThresh.value) || 15;
            if (selectedBoxId) {
                const b = boxes.find(bx => bx.id === selectedBoxId);
                if (b) recomputeContourForBox(b);
            }
            if (!isRestoringProgress) saveCurrentFileProgress(false);
        };
    }

    if (btnRecomputeContour) {
        btnRecomputeContour.onclick = () => {
            const b = boxes.find(bx => bx.id === selectedBoxId);
            if (b) recomputeContourForBox(b);
            if (!isRestoringProgress) saveCurrentFileProgress(false);
        };
    }

    // Search filter
    if (assetSearchEl) {
        assetSearchEl.oninput = () => {
            renderAssetTree(rawTreeData, assetSearchEl.value.trim());
        };
    }

    if (btnRefreshTree) {
        btnRefreshTree.onclick = () => loadAssetTree();
    }

    // Modal Events
    if (btnCloseModal) {
        btnCloseModal.onclick = () => { exportModal.style.display = "none"; };
    }
    if (modalBtnOpenFinder) {
        modalBtnOpenFinder.onclick = async () => {
            if (lastExportData && lastExportData.rel_folder) {
                await fetch(API_BASE + "/api/open-folder", {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ folder: lastExportData.rel_folder })
                });
            }
        };
    }
    if (modalBtnCopyPath) {
        modalBtnCopyPath.onclick = () => {
            if (lastExportData) {
                navigator.clipboard.writeText(lastExportData.full_path || lastExportData.saved_dir);
                modalBtnCopyPath.textContent = "✅ 已复制到剪贴板！";
                setTimeout(() => { modalBtnCopyPath.textContent = "📋 复制绝对路径"; }, 2000);
            }
        };
    }

    // Presets
    const pAuto = document.getElementById("preset-auto");
    const pH4 = document.getElementById("preset-h4");
    const pH3 = document.getElementById("preset-h3");
    const pGrid = document.getElementById("preset-grid24");
    const pClear = document.getElementById("btn-clear-boxes");

    if (pAuto) pAuto.onclick = () => autoDetect("auto");
    if (pH4) pH4.onclick = () => autoDetect("horizontal_4");
    if (pH3) pH3.onclick = () => autoDetect("horizontal_3");
    if (pGrid) pGrid.onclick = () => autoDetect("grid_2x4");
    if (pClear) pClear.onclick = () => {
        boxes = [];
        selectedBoxId = null;
        renderBoxesAndContours();
        if (!isRestoringProgress) saveCurrentFileProgress(false);
    };

    // Zoom Controls
    const btnZIn = document.getElementById("btn-zoom-in");
    const btnZOut = document.getElementById("btn-zoom-out");
    const btnZFit = document.getElementById("btn-zoom-fit");

    if (btnZIn) btnZIn.onclick = () => { zoom = Math.min(zoom * 1.25, 5.0); updateTransform(); };
    if (btnZOut) btnZOut.onclick = () => { zoom = Math.max(zoom / 1.25, 0.1); updateTransform(); };
    if (btnZFit) btnZFit.onclick = fitToScreen;

    // Viewport Wheel Zoom
    if (canvasViewport) {
        canvasViewport.onwheel = (e) => {
            e.preventDefault();
            const delta = e.deltaY < 0 ? 1.15 : 0.85;
            zoom = Math.max(0.1, Math.min(5.0, zoom * delta));
            updateTransform();
        };

        canvasViewport.onmousedown = (e) => {
            if (e.button === 1 || e.spaceKey || (e.button === 0 && e.target === canvasViewport)) {
                isPanning = true;
                startPanX = e.clientX - panX;
                startPanY = e.clientY - panY;
                canvasViewport.style.cursor = "grabbing";
            }
        };
    }

    window.addEventListener("mousemove", (e) => {
        if (isPanning) {
            panX = e.clientX - startPanX;
            panY = e.clientY - startPanY;
            updateTransform();
            return;
        }

        if (isDraggingCutLine && activeCutLine) {
            const coords = screenToCanvasCoords(e.clientX, e.clientY);
            if (activeCutLine.type === 'h') {
                const line = hCutLines.find(l => l.id === activeCutLine.id);
                if (line) {
                    line.y = Math.max(0, Math.min(imageHeight, Math.round(coords.y)));
                    renderCutLines();
                }
            } else if (activeCutLine.type === 'v') {
                const line = vCutLines.find(l => l.id === activeCutLine.id);
                if (line) {
                    line.x = Math.max(0, Math.min(imageWidth, Math.round(coords.x)));
                    renderCutLines();
                }
            }
            return;
        }

        if (isDrawing) {
            const coords = screenToCanvasCoords(e.clientX, e.clientY);
            const x = Math.min(drawStartX, coords.x);
            const y = Math.min(drawStartY, coords.y);
            const w = Math.abs(coords.x - drawStartX);
            const h = Math.abs(coords.y - drawStartY);
            
            let tempBox = boxes.find(b => b.id === "temp_draw_box");
            if (!tempBox) {
                tempBox = { id: "temp_draw_box", x, y, w, h, label: String(boxes.length + 1).padStart(2, '0'), contour: [] };
                boxes.push(tempBox);
            } else {
                tempBox.x = x;
                tempBox.y = y;
                tempBox.w = w;
                tempBox.h = h;
            }
            renderBoxesAndContours();
            return;
        }

        if (isDraggingBox && selectedBoxId) {
            const coords = screenToCanvasCoords(e.clientX, e.clientY);
            const dx = coords.x - dragStartX;
            const dy = coords.y - dragStartY;
            const b = boxes.find(bx => bx.id === selectedBoxId);
            if (b && originalBox) {
                const oldX = b.x;
                const oldY = b.y;
                b.x = Math.max(0, Math.min(imageWidth - b.w, originalBox.x + dx));
                b.y = Math.max(0, Math.min(imageHeight - b.h, originalBox.y + dy));
                
                const shiftX = b.x - oldX;
                const shiftY = b.y - oldY;
                if (b.contour) {
                    b.contour = b.contour.map(p => [p[0] + shiftX, p[1] + shiftY]);
                }
                renderBoxesAndContours();
            }
            return;
        }

        if (isResizingHandle && selectedBoxId && activeHandle) {
            const coords = screenToCanvasCoords(e.clientX, e.clientY);
            const b = boxes.find(bx => bx.id === selectedBoxId);
            if (b && originalBox) {
                if (activeHandle.includes("e")) b.w = Math.max(10, coords.x - originalBox.x);
                if (activeHandle.includes("s")) b.h = Math.max(10, coords.y - originalBox.y);
                if (activeHandle.includes("w")) {
                    const newW = originalBox.x + originalBox.w - coords.x;
                    if (newW >= 10) { b.x = coords.x; b.w = newW; }
                }
                if (activeHandle.includes("n")) {
                    const newH = originalBox.y + originalBox.h - coords.y;
                    if (newH >= 10) { b.y = coords.y; b.h = newH; }
                }
                renderBoxesAndContours();
            }
            return;
        }
    });

    window.addEventListener("mouseup", async () => {
        isPanning = false;
        if (canvasViewport) canvasViewport.style.cursor = "default";

        if (isDrawing) {
            isDrawing = false;
            const tempBox = boxes.find(b => b.id === "temp_draw_box");
            if (tempBox) {
                if (tempBox.w < 15 || tempBox.h < 15) {
                    boxes = boxes.filter(b => b.id !== "temp_draw_box");
                } else {
                    tempBox.id = "box_" + Date.now();
                    selectedBoxId = tempBox.id;
                    setTool("select");
                    await recomputeContourForBox(tempBox);
                }
                renderBoxesAndContours();
            }
        }

        if (isResizingHandle && selectedBoxId) {
            const b = boxes.find(bx => bx.id === selectedBoxId);
            if (b) await recomputeContourForBox(b);
        }

        const hadInteraction = isDraggingBox || isResizingHandle || isDraggingCutLine || isDrawing;
        isDraggingBox = false;
        isResizingHandle = false;
        isDraggingCutLine = false;
        activeCutLine = null;
        activeHandle = null;
        originalBox = null;

        if (hadInteraction && !isRestoringProgress) {
            saveCurrentFileProgress(false);
        }
    });

    // Box Overlay Interaction
    if (boxesOverlay) {
        boxesOverlay.onmousedown = (e) => {
            const handle = e.target.closest(".handle");
            if (handle) {
                isResizingHandle = true;
                activeHandle = handle.dataset.handle;
                const coords = screenToCanvasCoords(e.clientX, e.clientY);
                dragStartX = coords.x;
                dragStartY = coords.y;
                const b = boxes.find(bx => bx.id === selectedBoxId);
                if (b) originalBox = { ...b };
                e.stopPropagation();
                return;
            }

            const boxEl = e.target.closest(".crop-box");
            if (boxEl) {
                const id = boxEl.dataset.id;
                selectBox(id);
                setTool("select");
                isDraggingBox = true;
                const coords = screenToCanvasCoords(e.clientX, e.clientY);
                dragStartX = coords.x;
                dragStartY = coords.y;
                const b = boxes.find(bx => bx.id === id);
                if (b) originalBox = { ...b };
                e.stopPropagation();
                return;
            }

            if (currentTool === "cutlines") {
                const coords = screenToCanvasCoords(e.clientX, e.clientY);
                if (e.shiftKey) {
                    addVerticalCutLine(coords.x);
                } else {
                    addHorizontalCutLine(coords.y);
                }
                e.stopPropagation();
                return;
            }

            if (currentTool === "draw" || currentTool === "wand") {
                isDrawing = true;
                const coords = screenToCanvasCoords(e.clientX, e.clientY);
                drawStartX = coords.x;
                drawStartY = coords.y;
                e.stopPropagation();
            }
        };
    }

    // Props inputs
    [propX, propY, propW, propH, propLabel].forEach(input => {
        if (input) {
            input.oninput = () => {
                const b = boxes.find(bx => bx.id === selectedBoxId);
                if (b) {
                    b.x = parseFloat(propX.value) || 0;
                    b.y = parseFloat(propY.value) || 0;
                    b.w = parseFloat(propW.value) || 10;
                    b.h = parseFloat(propH.value) || 10;
                    b.label = propLabel.value.trim();
                    renderBoxesAndContours();
                    if (!isRestoringProgress) saveCurrentFileProgress(false);
                }
            };
        }
    });

    if (padSlider) {
        padSlider.oninput = () => {
            if (padValEl) padValEl.textContent = `${padSlider.value} px`;
            if (!isRestoringProgress) saveCurrentFileProgress(false);
        };
    }

    if (fpsSlider) {
        fpsSlider.oninput = () => {
            fps = parseInt(fpsSlider.value);
            if (fpsValEl) fpsValEl.textContent = fps;
            if (isPlaying) startAnimLoop();
            if (!isRestoringProgress) saveCurrentFileProgress(false);
        };
    }
    if (btnPlayAnim) btnPlayAnim.onclick = togglePlayAnim;

    const chkGenSheet = document.getElementById("chk-generate-sheet");
    if (chkGenSheet) {
        chkGenSheet.onchange = () => {
            if (!isRestoringProgress) saveCurrentFileProgress(false);
        };
    }
    if (chkSmartMask) {
        chkSmartMask.onchange = () => {
            if (!isRestoringProgress) saveCurrentFileProgress(false);
        };
    }

    if (btnExport) btnExport.onclick = exportArt;

    // Keyboard Shortcuts
    window.addEventListener("keydown", (e) => {
        if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;

        if (e.key === "Delete" || e.key === "Backspace") {
            if (selectedBoxId) {
                boxes = boxes.filter(b => b.id !== selectedBoxId);
                selectedBoxId = boxes.length > 0 ? boxes[0].id : null;
                renderBoxesAndContours();
                if (!isRestoringProgress) saveCurrentFileProgress(false);
            }
        }

        if (["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(e.key) && selectedBoxId) {
            e.preventDefault();
            const step = e.shiftKey ? 10 : 1;
            const b = boxes.find(bx => bx.id === selectedBoxId);
            if (b) {
                const oldX = b.x;
                const oldY = b.y;
                if (e.key === "ArrowUp") b.y = Math.max(0, b.y - step);
                if (e.key === "ArrowDown") b.y = Math.min(imageHeight - b.h, b.y + step);
                if (e.key === "ArrowLeft") b.x = Math.max(0, b.x - step);
                if (e.key === "ArrowRight") b.x = Math.min(imageWidth - b.w, b.x + step);
                const shiftX = b.x - oldX;
                const shiftY = b.y - oldY;
                if (b.contour) b.contour = b.contour.map(p => [p[0] + shiftX, p[1] + shiftY]);
                renderBoxesAndContours();
                if (!isRestoringProgress) saveCurrentFileProgress(false);
            }
        }

        if (e.key === "v" || e.key === "V") setTool("select");
        if (e.key === "b" || e.key === "B") setTool("draw");
        if (e.key === "w" || e.key === "W") setTool("wand");
        if (e.key === "c" || e.key === "C") setTool("cutlines");
    });

    // 页面刷新或退出前强制保存进度
    window.addEventListener("beforeunload", () => {
        saveCurrentFileProgress(true);
    });
}

function setTool(tool) {
    currentTool = tool;
    const toolSelectBtn = document.getElementById("tool-select");
    const toolDrawBtn = document.getElementById("tool-draw");
    const toolWandBtn = document.getElementById("tool-wand");
    const toolCutlinesBtn = document.getElementById("tool-cutlines");
    if (toolSelectBtn) toolSelectBtn.classList.toggle("active", tool === "select");
    if (toolDrawBtn) toolDrawBtn.classList.toggle("active", tool === "draw");
    if (toolWandBtn) toolWandBtn.classList.toggle("active", tool === "wand");
    if (toolCutlinesBtn) toolCutlinesBtn.classList.toggle("active", tool === "cutlines");
    if (canvasStage) canvasStage.style.cursor = tool === "select" ? "default" : "crosshair";
}

// Start
init();
