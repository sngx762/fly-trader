/**
 * API client (SSE for real-time streaming state, fetch for candles and trades) + Animation loop coordinator.
 */

import { renderScene } from './scene.js';
import { updateFlyState, animateFly } from './fly.js';
import { updateCandles } from './monitor.js';
import { initHUD, updateHUD, updateTradesList } from './hud.js';

initHUD();

// Fetch initial candles & trades
async function fetchStaticData() {
    try {
        const [candlesRes, tradesRes] = await Promise.all([
            fetch('/api/candles'),
            fetch('/api/trades')
        ]);
        if (candlesRes.ok) {
            const candles = await candlesRes.json();
            updateCandles(candles);
        }
        if (tradesRes.ok) {
            const trades = await tradesRes.json();
            updateTradesList(trades);
        }
    } catch (e) {
        console.error("Error fetching static dashboard data:", e);
    }
}

fetchStaticData();

// Periodic fetch for trades update
setInterval(async () => {
    try {
        const res = await fetch('/api/trades');
        if (res.ok) {
            const trades = await res.json();
            updateTradesList(trades);
        }
        const candlesRes = await fetch('/api/candles');
        if (candlesRes.ok) {
            const candles = await candlesRes.json();
            updateCandles(candles);
        }
    } catch (e) {
        // ignore polling errors during simulation restart
    }
}, 1000);

// SSE connection for real-time streaming state
function connectSSE() {
    const es = new EventSource('/api/stream');

    es.onmessage = (e) => {
        try {
            const data = JSON.parse(e.data);
            updateHUD(data);
            updateFlyState(data);
        } catch (err) {
            console.error("Failed to parse SSE message:", err);
        }
    };

    es.onerror = (err) => {
        console.warn("SSE connection lost, reconnecting...", err);
        es.close();
        setTimeout(connectSSE, 2000);
    };
}

connectSSE();

// Main Animation Loop
function animate() {
    requestAnimationFrame(animate);
    animateFly();
    renderScene();
}

animate();
