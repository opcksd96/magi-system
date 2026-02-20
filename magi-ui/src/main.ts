import { initI18n, translateUI, i18next } from './i18n';

// --- ATOMIC INITIALIZATION STATE ---
let terminal: HTMLDivElement;
let input: HTMLTextAreaElement;
let submitBtn: HTMLButtonElement;
let fileInput: HTMLInputElement;
let sysStatusEl: HTMLElement;
let telemetryBox: HTMLElement;
let resultModal: HTMLElement;
let modalVerdict: HTMLElement;
let closeModalBtn: HTMLButtonElement;
let mainMagiStamp: HTMLElement;

const magiHistory: string[] = JSON.parse(localStorage.getItem("magi_history") || "[]");
let magiHistoryIndex = magiHistory.length;
// --- SYSTEM STATE PROTOCOL ---
enum MagiState {
    IDLE = "IDLE",
    JUDGING = "JUDGING",
    RESULT_READY = "RESULT_READY", // Calculated but maybe not yet viewed (if on Projection)
    RESOLVED = "RESOLVED",        // Displayed on Command view
    ERROR = "ERROR"
}

// --- SYSTEM STATE ---
let isBusy = false; 

const advisors = {
    melchior: { cmd: "#melchior", proj: "#p-melchior", name: "MELCHIOR" },
    balthasar: { cmd: "#balthasar", proj: "#p-balthasar", name: "BALTHASAR" },
    casper: { cmd: "#casper", proj: "#p-casper", name: "CASPER" },
};

const API_URL = "http://localhost:8001";

// --- DIRTY STATE PERSISTENCE ---
// A "dirty" result is one that arrived but was never explicitly saved/cleared.
// If the page is closed while dirty, the next session will detect and restore it.
const DIRTY_KEY = "magi_dirty_result";

const setDirty = (data: any, query: string) => {
    try {
        localStorage.setItem(DIRTY_KEY, JSON.stringify({
            is_dirty: true,
            savedAt: new Date().toISOString(),
            data,
            query,
        }));
    } catch (e) {
        console.warn("[MAGI] Could not persist dirty state", e);
    }
};

const clearDirty = () => {
    localStorage.removeItem(DIRTY_KEY);
};

const loadDirty = (): { is_dirty: boolean; data: any; query: string; savedAt: string } | null => {
    try {
        const raw = localStorage.getItem(DIRTY_KEY);
        if (!raw) return null;
        const parsed = JSON.parse(raw);
        return parsed?.is_dirty ? parsed : null;
    } catch {
        return null;
    }
};

// --- CORE UTILITIES ---
const log = (msg: string, type: "info" | "error" | "magi" = "info") => {
    if (!terminal) return;
    const line = document.createElement("div");
    line.className = `line ${type} log-entry ${type}`;
    line.textContent = `> ${msg}`;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
    
    try {
        localStorage.setItem("magi_logs", terminal.innerHTML);
        localStorage.setItem("magi_history", JSON.stringify(magiHistory));
    } catch (e) {
        console.warn("Storage quota exceeded", e);
    }
};

const showToast = (msg: string, type: "info" | "success" = "info") => {
    let container = document.querySelector(".toast-container");
    if (!container) {
        container = document.createElement("div");
        container.className = "toast-container";
        document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>[SYSTEM_NOTIFY]</span> ${msg}`;
    container.appendChild(toast);
    
    setTimeout(() => toast.classList.add("show"), 10);
    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 4000);
};

const updateAdvisorStatus = (name: string, active: boolean, ruling: string = "") => {
    const configs = (advisors as any)[name];
    if (!configs) return;

    const cmdEl = document.querySelector(configs.cmd) as HTMLDivElement;
    const projEl = document.querySelector(configs.proj) as HTMLDivElement;
    const status = (ruling || "").toUpperCase();
    
    // Robust detection for Approval / Denial (handles EN and JP)
    const isDenied = status.includes("DENY") || status.includes("REJECT") || status.includes("FAIL") || status.includes("否決") || status.includes("否");
    const isPassed = status.includes("APPROVE") || status.includes("PASS") || status.includes("可決") || status.includes("可");

    if (cmdEl) {
        cmdEl.classList.remove("cmd-active", "cmd-passed", "cmd-rejected", "blink-user-error", "blink-system-error", "blink-app-error");
        if (active) cmdEl.classList.add("cmd-active");
        if (isPassed) {
            cmdEl.classList.add("cmd-passed");
            log(`COMMAND: ${configs.name} APPROVED`, "magi");
        }
        else if (isDenied) {
            cmdEl.classList.add("cmd-rejected");
            log(`COMMAND: ${configs.name} REJECTED`, "magi");
        }
    }

    if (projEl) {
        const stampEl = projEl.querySelector('.p-stamp') as HTMLElement;
        
        // Remove all state classes first
        projEl.classList.remove("proj-active", "proj-deny", "proj-passed");

        // Re-inject ID as class for higher specificity
        const idClass = projEl.id;
        if (!projEl.classList.contains(idClass)) projEl.classList.add(idClass);
        
        if (stampEl) {
            stampEl.classList.add('hidden');
            stampEl.className = 'p-stamp hidden';
        }
        
        if (isDenied) {
            projEl.classList.add("proj-deny");
            if (stampEl) {
                stampEl.classList.remove('hidden');
                stampEl.classList.add('status-rejected');
                stampEl.innerHTML = '<span>否決</span>';
            }
        } else if (isPassed) {
            projEl.classList.add("proj-passed");
            if (stampEl) {
                stampEl.classList.remove('hidden');
                stampEl.classList.add('status-passed');
                stampEl.innerHTML = '<span>可決</span>';
            }
        } else if (active) {
            projEl.classList.add("proj-active");
            if (stampEl) {
                stampEl.classList.remove('hidden');
                stampEl.classList.add('status-judging');
                stampEl.innerHTML = '<span>審議中</span>';
            }
        }
    }
};

const triggerErrorBlink = (type: 'user' | 'system' | 'app') => {
    const classMap = { user: 'blink-user-error', system: 'blink-system-error', app: 'blink-app-error' };
    const className = classMap[type];
    Object.values(advisors).forEach(cfg => {
        const el = document.querySelector(cfg.cmd) as HTMLElement;
        if (el) {
            el.classList.add(className);
            if (type !== 'app') setTimeout(() => el.classList.remove(className), 3000);
        }
    });
};

const resetProjection = () => {
    if (mainMagiStamp) {
        mainMagiStamp.classList.add('hidden');
        mainMagiStamp.innerHTML = "";
    }
    ["melchior", "balthasar", "casper"].forEach(n => updateAdvisorStatus(n, false));
    
    // 全てのパネルスタンプを確実に隠す
    document.querySelectorAll('.p-stamp').forEach(el => el.classList.add('hidden'));
    updateBridges("idle");
};

const updateBridges = (state: "idle" | "online" | "divergence" | "critique" | "convergence") => {
    const bridges = document.querySelectorAll(".connector");
    bridges.forEach(b => {
        // Reset all state/active classes
        b.classList.remove("state-divergence", "state-critique", "state-convergence", "active");
        
        if (state === "online") {
            // System ready: orange glow, slow pulse only (no phase flicker)
            b.classList.add("active");
        } else if (state !== "idle") {
            // Query phase: full phase color + animation
            b.classList.add("active", `state-${state}`);
        }
        // idle: no classes, border color only
    });
};

// --- REFACTORED OBSERVER (VIEW) ---
let maybeShowResult: () => void;
let hideResultPanel: () => void;
let pollingInterval: number | null = null;

// --- STICKY STATE TRACKING ---
let lastMagiState: MagiState | null = null;

/**
 * Derives the true system status from Ground-Truth (M) and updates the UI (V).
 * Transition-guarded to prevent flickers and "particle dust" data loss.
 */
const syncView = async (activeJob?: any) => {
    const dirty = loadDirty();
    const isJudging = activeJob && activeJob.status === "judging";
    const hasUnsavedResult = !!(dirty && dirty.data && dirty.data.ruling);
    const isLocalJudging = !!(dirty && dirty.data && dirty.data.status === "judging");

    // Determine the 'Ground-Truth State'
    // Priority: JUDGING (Server) > JUDGING (Local Hack) > RESOLVED (Dirty) > IDLE
    let currentState = MagiState.IDLE;
    if (isJudging || isLocalJudging) currentState = MagiState.JUDGING;
    else if (hasUnsavedResult) currentState = MagiState.RESOLVED;

    isBusy = (currentState === MagiState.JUDGING);

    // --- TRANSITION GUARD ---
    const isTransition = (currentState !== lastMagiState);
    if (isTransition) {
        console.log(`[STATE_TRANSITION] ${lastMagiState} -> ${currentState}`);
        if (currentState === MagiState.IDLE || currentState === MagiState.JUDGING) {
            resetProjection(); // Clean slate only on major state entries
        }
        lastMagiState = currentState;
    }

    // 0. DOM Elements for Overlays
    const busyOverlay = document.getElementById("busy-overlay");
    const busyPhaseText = document.getElementById("busy-phase-text");

    // 1. Input/Button Locking (Idempotent)

    // 1. Input/Button Locking
    if (input) input.disabled = isBusy;
    if (submitBtn) {
        submitBtn.disabled = isBusy;
        submitBtn.textContent = i18next.t("execute").toUpperCase();
    }
    if (fileInput) fileInput.disabled = isBusy;

    // 2. Status Terminal Text
    if (sysStatusEl) {
        sysStatusEl.textContent = i18next.t(isBusy ? "processing" : "online");
        sysStatusEl.className = isBusy ? "busy" : "online";
        if (!isBusy) input?.focus();
    }

    // 3. Overlays / Polling
    if (busyOverlay) busyOverlay.classList.toggle("hidden", currentState !== MagiState.JUDGING);
    
    if (currentState === MagiState.JUDGING) {
        // Bridges and Stamps: Only explicitly re-sync if they aren't already active
        updateBridges("divergence"); 
        
        if (mainMagiStamp) {
            mainMagiStamp.classList.remove('hidden');
            mainMagiStamp.style.visibility = "visible";
            mainMagiStamp.style.opacity = "1";
            mainMagiStamp.style.display = "flex"; // Force layout
            mainMagiStamp.className = "magi-stamp status-judging";
            mainMagiStamp.innerHTML = `<span>審議中</span>`;
        }

        if (busyPhaseText) busyPhaseText.textContent = `PHASE: ${activeJob?.phase || "INITIALIZING..."}`;
        
        ["melchior", "balthasar", "casper"].forEach(n => updateAdvisorStatus(n, true));
        
        // Start Polling if not already
        if (!pollingInterval) {
            pollingInterval = window.setInterval(async () => {
                try {
                    const res = await fetch(`${API_URL}/active-job`);
                    if (res.ok) {
                        const job = await res.json();
                        if (job && job.status === "judging") {
                            syncView(job);
                        } else {
                            // Job finished! Clear polling and sync with result
                            clearInterval(pollingInterval!);
                            pollingInterval = null;
                            syncView(); 
                        }
                    }
                } catch (e) { console.error("Poll fail", e); }
            }, 800);
        }
    } else {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            pollingInterval = null;
        }
    }

    // 4. Result Population (RESOLVED)
    if (currentState === MagiState.RESOLVED && dirty) {
        const { data, query, savedAt } = dirty;
        const ruling = data.ruling || "DENY";
        const isApproved = ruling.toUpperCase().includes("APPROVE");
        const now = savedAt ? new Date(savedAt) : new Date();

        // Populate Document Panel
        const caseNum = String(now.getTime()).slice(-6);
        if (document.getElementById("report-case-num")) document.getElementById("report-case-num")!.textContent = caseNum;
        if (document.getElementById("report-timestamp")) document.getElementById("report-timestamp")!.textContent = now.toISOString().replace('T', ' ').substring(0, 19);
        
        if (modalVerdict) {
            modalVerdict.textContent = isApproved ? "申立認容" : "申立棄却";
            modalVerdict.className = "result-verdict " + (isApproved ? "cmd-approve" : "cmd-deny");
        }
        if (document.getElementById("j-shumon")) document.getElementById("j-shumon")!.textContent = isApproved
            ? "本件申立を認める。\nMAGI三機体の多数決により可決とする。"
            : "本件申立を棄却する。\nMAGI三機体の検討の結果、申立に理由なしと認める。";
        if (document.getElementById("j-query")) document.getElementById("j-query")!.textContent = query || "—";
        if (document.getElementById("j-reason")) document.getElementById("j-reason")!.textContent = data.reasoning || data.report_markdown || "（理由記録なし）";
        
        const advisorEl = document.getElementById("j-advisors");
        if (advisorEl) {
            const advisorData = data.advisors || [];
            if (advisorData.length > 0) {
                advisorEl.innerHTML = advisorData.map((a: any) => {
                    const voteLabel = (a.vote || "").toUpperCase().includes("APPROVE") ? "【可】" : "【否】";
                    return `<strong>${a.name || '審議官'} ${voteLabel}</strong>\n${a.opinion || a.content || '（意見テキスト未収録）'}`;
                }).join('\n\n');
            } else {
                advisorEl.textContent = `メルキオール1号機・バルタザール2号機・カスパール3号機\n各機体の詳細意見は別紙記録による。`;
            }
        }
        if (document.getElementById("modal-stats")) {
            document.getElementById("modal-stats")!.innerHTML = `<span>TOKENS: ${data.telemetry?.total_tokens || 0}</span><span>TIME: ${data.telemetry?.total_time?.toFixed(2) || "?"}s</span><span>AES-256</span><span>CASE: MAGI-S-${caseNum}</span>`;
        }

        // Population Projection
        if (mainMagiStamp) {
            const stampClass = isApproved ? "status-passed" : "status-rejected";
            const stampText = isApproved ? "可決" : "否決";
            mainMagiStamp.classList.remove('hidden');
            mainMagiStamp.style.visibility = "visible";
            mainMagiStamp.style.opacity = "1";
            mainMagiStamp.style.display = "flex";
            mainMagiStamp.className = `magi-stamp ${stampClass}`;
            mainMagiStamp.innerHTML = `<span>${stampText}</span>`;
        }

        // Sync advisor cells
        const nameMap: Record<string, string> = {
            melchior: "melchior", balthasar: "balthasar", casper: "casper",
            magi1: "melchior", magi2: "balthasar", magi3: "casper",
            "melchior-1": "melchior", "balthasar-2": "balthasar", "casper-3": "casper"
        };
        ["melchior", "balthasar", "casper"].forEach(n => updateAdvisorStatus(n, false, ruling.toUpperCase()));
        (data.advisors || []).forEach((a: any) => {
            const rawName = (a.name || "").toLowerCase().trim();
            const cleanName = rawName.replace(/[^a-z0-9-]/g, "");
            const magiKey = nameMap[cleanName] || nameMap[cleanName.replace("-", "")] || Object.keys(nameMap).find(k => cleanName.includes(k)) || null;
            if (magiKey) updateAdvisorStatus(magiKey, false, (a.vote || ruling).toUpperCase());
        });
        updateBridges("online");

        if (maybeShowResult) maybeShowResult();
    }

    // 5. Clean Reset (IDLE)
    if (currentState === MagiState.IDLE) {
        // resetProjection was already called in the transition block above
        updateBridges("online"); // Ensure orange glow is visible
        if (hideResultPanel) hideResultPanel();
    }
};

// --- REFACTORED COMMAND EXECUTION ---
const executeQuery = async () => {
    const query = input.value.trim();
    if (!query || isBusy) return;
    magiHistory.push(query);
    magiHistoryIndex = magiHistory.length;
    log(`INPUT DATA: ${query.toUpperCase()}`);
    input.value = "";
  
    try {
        updateBridges("divergence");
        // transitionTo handles mainMagiStamp and overlays
        log("STATUS: PROMPT RECEIVED. INITIALIZING DATA MATCHING...", "magi");
        ["melchior", "balthasar", "casper"].forEach(n => updateAdvisorStatus(n, true));
        log("STATUS: COMMENCING DIVERGENCE PHASE [PHASE 1/3]...", "magi");
        // No mock phase transitions - bridges stay on divergence until real response

        const response = await fetch(`${API_URL}/judge`, {
            method: "POST", 
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: query })
        });

        // Register as dirty immediately so if we reload during deliberation, 
        // the bootstrap re-attaches to the active job
        setDirty({ status: "judging" }, query);
        localStorage.setItem("magi_history", JSON.stringify(magiHistory));

        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        const data = await response.json();
        
        if (data.telemetry && telemetryBox) {
            telemetryBox.innerHTML = `<span>MODEL: ${data.telemetry.model || "?"}</span><span>TOKENS: ${data.telemetry.total_tokens || 0}</span><span>TIME: ${data.telemetry.total_time?.toFixed(2) || "?"}s</span>`;
        }
        
        // Detect ruling for local feedback (DOM updates are handled in transitionTo)
        const ruling = data.ruling || "DENY";
        const isApproved = ruling.toUpperCase().includes("APPROVE");

        // Persist and Sync View
        setDirty(data, query);
        syncView();
        
        showToast(`MAGI ADJUDICATION COMPLETE — ${isApproved ? "可決" : "否決"}`, isApproved ? "success" : "info");
    } catch (err: any) {
        log(`FATAL ERROR: ${err}`, "error");
        triggerErrorBlink('system');
        clearDirty(); // Clean up on fatal error
        syncView();
        updateBridges("online"); 
    }
};

// Active jobs are now handled implicitly by calling syncView(job)

// --- BOOTSTRAPPER ---
async function bootstrap() {
    // 1. Resolve DOM elements
    terminal = document.querySelector("#terminal") as HTMLDivElement;
    input = document.querySelector("#magi-input") as HTMLTextAreaElement;
    submitBtn = document.querySelector("#submit-btn") as HTMLButtonElement;
    fileInput = document.getElementById("menu-load-file") as HTMLInputElement;
    sysStatusEl = document.getElementById("sys-status") as HTMLElement;
    telemetryBox = document.getElementById("telemetry-box") as HTMLElement;
    resultModal = document.getElementById("result-dialog") as HTMLElement;
    modalVerdict = document.getElementById("modal-verdict") as HTMLElement;
    closeModalBtn = document.getElementById("close-modal") as HTMLButtonElement;
    mainMagiStamp = document.getElementById("magi-stamp") as HTMLElement;

    // 2. Initial UI Sync (Non-Translating)
    if (sysStatusEl) {
        sysStatusEl.textContent = "BOOTING...";
        sysStatusEl.className = "busy";
    }

    // 3. i18n is ALREADY initialized by the gateway
    translateUI(); 
    resetProjection(); // CLEAN STATE
    // setBusy(true); // 不要な審議中表示を防ぐ

    try {
        log("MAGI システム初期化中...");
        log("国際化サブシステム準備完了。", "info");

        // 4. Load Backend Configuration
        try {
            const resp = await fetch(`${API_URL}/config`);
            if (resp.ok) {
                const cfg = await resp.json();
                const setLang = document.getElementById("set-lang") as HTMLSelectElement;
                if (setLang) setLang.value = cfg.system?.language || "en";
                log("構成設定を取得しました。", "magi");
            }
        } catch (e) {
            log("サーバー設定の取得に失敗しました（ローカルの既定値を使用）。", "info");
        }

        if (closeModalBtn) closeModalBtn.onclick = () => {
            clearDirty(); // REMOVE DATA MODEL -> TRIGGER IDLE TRANSITION
            syncView();
        };

        const btnSaveMd  = document.getElementById("btn-save-md");
        const btnPdf     = document.getElementById("btn-export-pdf");
        const btnCopy    = document.getElementById("btn-copy-clip");
        const btnPrompt  = document.getElementById("btn-to-prompt");
        const btnRetry   = document.getElementById("btn-retry");

        const getLastResult = () => (window as any).__magiLastResult;

        if (btnSaveMd) btnSaveMd.onclick = () => {
            const r = getLastResult();
            if (!r) return;
            const md = r.data.report_markdown || r.data.reasoning || r.data.ruling || "";
            const blob = new Blob([md], { type: "text/markdown" });
            const a = document.createElement("a");
            a.href = URL.createObjectURL(blob);
            a.download = `magi_report_${Date.now()}.md`;
            a.click();
            clearDirty(); // DATA CONSUMED -> CLEAR MODEL
            syncView();    // TRIGGER IDLE
            showToast("SAVED AS MARKDOWN", "success");
        };

        if (btnPdf) btnPdf.onclick = () => {
            showToast("OPENING PRINT DIALOG", "success");
            window.print();
        };

        if (btnCopy) btnCopy.onclick = async () => {
            const r = getLastResult();
            if (!r) return;
            const text = `[MAGI RULING: ${r.data.ruling}]\n\n${r.data.reasoning || r.data.report_markdown || ""}`;
            await navigator.clipboard.writeText(text);
            showToast("COPIED TO CLIPBOARD", "success");
        };

        if (btnPrompt) btnPrompt.onclick = () => {
            const r = getLastResult();
            if (!r) return;
            if (input) {
                input.value = r.query;
                input.dispatchEvent(new Event('input'));
                resultModal.classList.add("hidden");
                input.focus();
            }
        };

        if (btnRetry) btnRetry.onclick = () => {
            const r = getLastResult();
            if (!r) return;
            if (input) {
                input.value = r.query;
                resultModal.classList.add("hidden");
                executeQuery();
            }
        };

        if (submitBtn) submitBtn.addEventListener("click", executeQuery);
        if (input) {
            input.addEventListener("keydown", (e) => {
                // Enter only submits, Shift+Enter allows newline
                if (e.key === "Enter" && !e.shiftKey) { 
                    e.preventDefault(); 
                    executeQuery(); 
                }
                
                // History Navigation (Arrow Keys)
                if (e.key === "ArrowUp") {
                    if (magiHistoryIndex > 0) {
                        e.preventDefault();
                        magiHistoryIndex--;
                        input.value = magiHistory[magiHistoryIndex];
                        input.dispatchEvent(new Event('input')); 
                    }
                } else if (e.key === "ArrowDown") {
                    if (magiHistoryIndex < magiHistory.length) {
                        e.preventDefault();
                        magiHistoryIndex++;
                        input.value = magiHistoryIndex < magiHistory.length ? magiHistory[magiHistoryIndex] : "";
                        input.dispatchEvent(new Event('input'));
                    }
                }
            });
            // Auto-resize textarea
            input.addEventListener("input", () => {
                input.style.height = "auto";
                input.style.height = (input.scrollHeight) + "px";
            });
        }

        // Bind Tab Switching — with deferred result display logic
        (window as any).__currentView = document.querySelector(".tab-btn.active")?.getAttribute("data-view") || "command-view";
        (window as any).__pendingResultReady = false;   // set when result arrives while on projection

        (window as any).__showResultPanel = () => {
            if (resultModal) {
                resultModal.classList.remove("hidden");
                // Force scroll to top
                const body = document.getElementById("judgment-body");
                if (body) body.scrollTop = 0;
            }
        };
        hideResultPanel = () => {
            if (resultModal) resultModal.classList.add("hidden");
        };

        // Intercept result panel visibility: only show on command-view if result is active and final
        maybeShowResult = () => {
            const currentView = (window as any).__currentView;
            const dirty = loadDirty();
            // A "final" result has a ruling. If it's just "judging", don't show the panel yet.
            const hasFinalResult = dirty && dirty.data && dirty.data.ruling;
            const isPending = (window as any).__pendingResultReady;
            
            if (currentView === "command-view" && (isPending || hasFinalResult)) {
                (window as any).__pendingResultReady = false;
                (window as any).__showResultPanel();
            }
        };

        const tabBtns = document.querySelectorAll(".tab-btn");
        const views = document.querySelectorAll(".view-container");
        tabBtns.forEach(btn => {
            btn.addEventListener("click", () => {
                const targetView = (btn as HTMLElement).dataset.view || "command-view";
                tabBtns.forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                views.forEach(v => {
                    if (v.id === targetView) v.classList.remove("hidden");
                    else v.classList.add("hidden");
                });
                (window as any).__currentView = targetView;

                if ((window as any).__currentView === "command-view") {
                    // Reveal deferred result if any
                    maybeShowResult();
                } else {
                    // Hide result panel — projection screen is Eva-only, no UI chrome
                    hideResultPanel();
                }
            });
        });

        // Patch resultModal.classList.remove("hidden") to respect current view
        // We override the result display calls in executeQuery / resumeActiveJob
        (window as any).__showResultWhenReady = () => {
            (window as any).__pendingResultReady = true;
            maybeShowResult(); // only actually shows if on command-view
        };

        // beforeunload: warn if there's an unprocessed result and user is on projection
        window.addEventListener("beforeunload", (e) => {
            if ((window as any).__pendingResultReady || ((window as any).__currentView !== "command-view" && (window as any).__magiLastResult)) {
                const msg = "MAGI ADJUDICATION DATA NOT SAVED. SAVE BEFORE EXIT?";
                e.preventDefault();
                e.returnValue = msg;
                return msg;
            }
        });
        
        // Result panel sync
        maybeShowResult();


        // 6. Persistence Loading (Local + Server)

        // 6a. Dirty State Restore — if previous session closed with unsaved results
        const dirtyRestored = (() => {
            const dirty = loadDirty();
            if (dirty && dirty.data && dirty.data.ruling) {
                const { data, query, savedAt } = dirty;
                const isApproved = (data.ruling || "").toUpperCase().includes("APPROVE");
                const rulingLabel = isApproved ? "申立認容" : "申立棄却";

                log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`, "magi");
                log(`[復元] 未保存の決議データを検出しました。`, "magi");
                log(`保存日時: ${savedAt} | 決議: ${isApproved ? "✅ 可決" : "❌ 否決"}`, "info");
                log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`, "magi");

                // Store for action buttons
                (window as any).__magiLastResult = { data, query };
                showToast(`[RESTORE] 前回セッションを復元しました — ${rulingLabel}`, isApproved ? "success" : "info");
                return true;
            }
            return false;
        })();

        if (dirtyRestored) {
            log("セッションの復元が完了しました。前回セッションの審議データを再読込しました。", "magi");
        }

        // 6b. Restore log terminal from localStorage
        const savedLogs = localStorage.getItem("magi_logs");
        if (savedLogs && terminal) {
            terminal.innerHTML = savedLogs;
            terminal.scrollTop = terminal.scrollHeight;
            log("ローカルセッションのログおよび履歴を再構築しました。", "magi");
        }

        // Sync with server history
        try {
            const historyResp = await fetch(`${API_URL}/recent`);
            if (historyResp.ok) {
                const history = await historyResp.json();
                if (history && history.length > 0) {
                    log(`解析アーカイブから ${history.length} 件のエントリを同期中...`, "info");
                    // history is [newest...oldest], so reverse to get [oldest...newest]
                    history.reverse().forEach((item: any) => {
                        const timeStr = item.timestamp?.split('.')[0].replace('T', ' ') || "UNKNOWN";
                        log(`[${timeStr}] PREVIOUS_INPUT: ${item.prompt}`, "info");
                        log(`RULING: ${item.result?.ruling || "UNRESOLVED"}`, "magi");
                        
                        // Populate internal history (Oldest first, Newest at end)
                        if (item.prompt && !magiHistory.includes(item.prompt)) {
                             magiHistory.push(item.prompt);
                        }
                    });
                    magiHistoryIndex = magiHistory.length;
                }
            }
        } catch (e) {
            log("サーバーアーカイブの同期に失敗しました。", "error");
        }

        // 7. Health Check
        try {
            const resp = await fetch(`${API_URL}/health`);
            if (resp.ok) {
                log("MAGI クラスター接続状況... [正常]");
                
                // 7a. Ping each advisor model for connectivity (4s timeout)
                try {
                    const pingAbort = new AbortController();
                    const pingTimer = setTimeout(() => pingAbort.abort(), 4000);
                    const pingResp = await fetch(`${API_URL}/ping`, { signal: pingAbort.signal });
                    clearTimeout(pingTimer);
                    if (pingResp.ok) {
                        const pingData = await pingResp.json();
                        if (pingData.status === "online") {
                            log("審議官モデルリンク... [確立]", "magi");
                            // Activate only the bridges (NO advisor stamps at this stage)
                            updateBridges("online");
                        } else {
                            log("審議官モデルリンク... [機能低下]", "error");
                        }
                    }
                } catch (e) {
                    log("モデルの疎通確認に失敗しました。審議官はオフラインです。", "error");
                }

                // 7b. Check for Active Jobs (Resume Logic)
                try {
                    const activeResp = await fetch(`${API_URL}/active-job`);
                    if (activeResp.ok) {
                        const job = await activeResp.json();
                        if (job && job.status === "judging") {
                            log(`[復元] 進行中の審議プロセスを検出しました...`);
                            syncView(job); // Active job takes precedence immediately & enters polling
                            return; 
                        }
                    }
                } catch (e) {
                    console.warn("Could not check for active jobs", e);
                }
            }
        } catch (err) {
            log("バックエンドがオフラインです。スタンドアロンモードで動作中。", "error");
        }
        
        // --- FINAL AUTHORITATIVE SYNC ---
        // At this point, all data (LocalStorage + Health + Jobs) has been audited.
        syncView();

    } catch (err: any) {
        console.error("FATAL BOOTSTRAP FAILURE", err);
        syncView(); // Emergency fallback
    }
}

// --- GATEWAY ---
(async function initSystem() {
    try {
        // A. Priority 1: Localization Setup (BEFORE anything else)
        await initI18n();
        
        // B. Priority 2: Wait for DOM readiness if not yet ready
        if (document.readyState === "loading") {
            window.addEventListener("DOMContentLoaded", bootstrap);
        } else {
            bootstrap();
        }
    } catch (criticalError) {
        console.error("GATEWAY FAILURE: i18n subsystem could not start.", criticalError);
    }
})();
