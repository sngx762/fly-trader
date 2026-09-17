/**
 * HUD & Equity Chart overlay controller + event-driven visual effects (flash, camera shake, notifications).
 */

import { camera } from './scene.js';

const stepCounter = document.querySelector('#step-counter');
const runStatus = document.querySelector('#run-status');
const modeBadge = document.querySelector('#mode-badge');
const assetBadge = document.querySelector('#asset-badge');
const metricBalance = document.querySelector('#metric-balance');
const metricPnl = document.querySelector('#metric-pnl');
const metricPosition = document.querySelector('#metric-position');
const metricPrice = document.querySelector('#metric-price');
const metricRpe = document.querySelector('#metric-rpe');
const metricDopa = document.querySelector('#metric-dopa');
const metricConf = document.querySelector('#metric-conf');
const metricAction = document.querySelector('#metric-action');
const dopaBar = document.querySelector('#dopa-bar');
const tradesContainer = document.querySelector('#trades-container');
const eventTicker = document.querySelector('#event-ticker');
const flashOverlay = document.querySelector('#flash-overlay');

const equityCanvas = document.querySelector('#equity-canvas');
const equityCtx = equityCanvas.getContext('2d');

let equityHistory = [];

export function initHUD() {
    equityCanvas.width = equityCanvas.clientWidth * window.devicePixelRatio;
    equityCanvas.height = equityCanvas.clientHeight * window.devicePixelRatio;
}

export function updateHUD(data) {
    if (data.step !== undefined && data.total_steps !== undefined) {
        stepCounter.textContent = `${data.step} / ${data.total_steps}`;
    }
    if (data.running !== undefined) {
        runStatus.textContent = data.running ? 'RUNNING' : 'FINISHED';
        runStatus.className = data.running ? 'text-[#00ff88] font-bold animate-pulse' : 'text-[#ff3355] font-bold';
    }
    if (data.fly_mode !== undefined || data.mode !== undefined) {
        const m = data.fly_mode || data.mode;
        modeBadge.textContent = `MODE: FLY ${m}`;
    }
    if (data.asset !== undefined && assetBadge) {
        assetBadge.textContent = `ASSET: ${data.asset}`;
    }
    if (data.balance !== undefined) {
        metricBalance.textContent = `$${data.balance.toFixed(2)}`;
    }
    if (data.equity !== undefined) {
        equityHistory.push(data.equity);
        if (equityHistory.length > 100) equityHistory.shift();
        drawEquityChart();
    }
    if (data.pnl_pct !== undefined) {
        metricPnl.textContent = `${data.pnl_pct >= 0 ? '+' : ''}${data.pnl_pct.toFixed(2)}%`;
        metricPnl.className = `font-bold ${data.pnl_pct >= 0 ? 'text-[#00ff88]' : 'text-[#ff3355]'}`;
    }
    if (data.position !== undefined) {
        metricPosition.textContent = `${data.position.toFixed(4)} BTC`;
    }
    if (data.price !== undefined) {
        metricPrice.textContent = `$${data.price.toFixed(2)}`;
    }
    if (data.dopamine !== undefined) {
        metricDopa.textContent = data.dopamine.toFixed(2);
        const pct = Math.min(100, Math.max(0, (data.dopamine / 3.0) * 100));
        dopaBar.style.width = `${pct}%`;
    }
    if (data.rpe !== undefined) {
        metricRpe.textContent = `${data.rpe >= 0 ? '+' : ''}${data.rpe.toFixed(3)}`;
        metricRpe.className = data.rpe >= 0 ? 'text-[#00ff88] font-bold' : 'text-[#ff3355] font-bold';
    }
    if (data.confidence !== undefined) {
        metricConf.textContent = `${(data.confidence * 100).toFixed(1)}%`;
    }
    if (data.action !== undefined) {
        metricAction.textContent = data.action;
        if (data.action === 'BUY') {
            metricAction.className = 'px-3 py-1 rounded-lg bg-[#00ff88]/20 font-mono font-bold text-sm text-[#00ff88] border border-[#00ff88]/40';
        } else if (data.action === 'SELL') {
            metricAction.className = 'px-3 py-1 rounded-lg bg-[#ff3355]/20 font-mono font-bold text-sm text-[#ff3355] border border-[#ff3355]/40';
        } else {
            metricAction.className = 'px-3 py-1 rounded-lg bg-[#1a1a2e] font-mono font-bold text-sm text-[#667788] border border-white/10';
        }
    }

    if (data.events && data.events.length > 0) {
        const latestEvt = data.events[data.events.length - 1];
        handleEventEffect(latestEvt);
    }
}

export function updateTradesList(trades) {
    if (!trades || trades.length === 0) return;
    tradesContainer.innerHTML = '';
    const recent = trades.slice(-15).reverse();
    recent.forEach(t => {
        const row = document.createElement('div');
        row.className = 'flex justify-between items-center text-xs font-mono p-2 rounded-lg bg-[#1a1a2e]/60 border border-white/5';
        const isBuy = t.action === 'BUY';
        const pnlColor = t.pnl >= 0 ? 'text-[#00ff88]' : 'text-[#ff3355]';
        row.innerHTML = `
            <span class="text-[#667788]">#${t.time}</span>
            <span class="font-bold ${isBuy ? 'text-[#00ff88]' : 'text-[#ff3355]'}">${t.action}</span>
            <span class="text-white">$${t.price.toFixed(2)}</span>
            <span class="${pnlColor}">${t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}</span>
        `;
        tradesContainer.appendChild(row);
    });
}

function handleEventEffect(evt) {
    if (evt.type === 'dopamine_burst') {
        eventTicker.textContent = `⚡ DOPAMINE BURST (Intensity: ${evt.data.intensity.toFixed(2)})`;
        flashOverlay.className = 'fixed inset-0 pointer-events-none z-50 transition-opacity duration-300 opacity-100 dopamine-flash';
        setTimeout(() => {
            flashOverlay.className = 'fixed inset-0 pointer-events-none z-50 transition-opacity duration-300 opacity-0';
        }, 300);
    } else if (evt.type === 'punishment') {
        eventTicker.textContent = `⚠️ PUNISHMENT SIGNAL (Intensity: ${evt.data.intensity.toFixed(2)})`;
        flashOverlay.className = 'fixed inset-0 pointer-events-none z-50 transition-opacity duration-300 opacity-100 punishment-flash';
        // Camera shake
        camera.position.x += (Math.random() - 0.5) * 0.1;
        setTimeout(() => {
            flashOverlay.className = 'fixed inset-0 pointer-events-none z-50 transition-opacity duration-300 opacity-0';
        }, 200);
    }
}

function drawEquityChart() {
    const w = equityCanvas.width;
    const h = equityCanvas.height;
    equityCtx.clearRect(0, 0, w, h);

    if (equityHistory.length < 2) return;

    const minEq = Math.min(...equityHistory);
    const maxEq = Math.max(...equityHistory);
    const range = (maxEq - minEq) || 1;

    equityCtx.strokeStyle = '#00ff88';
    equityCtx.lineWidth = 2;
    equityCtx.beginPath();

    equityHistory.forEach((eq, i) => {
        const x = (i / (equityHistory.length - 1)) * w;
        const y = h - ((eq - minEq) / range) * (h - 10) - 5;
        if (i === 0) equityCtx.moveTo(x, y);
        else equityCtx.lineTo(x, y);
    });
    equityCtx.stroke();
}
