/**
 * 3D Desk & Monitor displaying real-time BTC candlestick chart rendered on a CanvasTexture.
 */

import * as THREE from 'three';
import { scene } from './scene.js';

// Desk
const deskGeo = new THREE.BoxGeometry(2.6, 0.06, 1.4);
const deskMat = new THREE.MeshStandardMaterial({ color: 0x12121c, roughness: 0.3, metalness: 0.8 });
const desk = new THREE.Mesh(deskGeo, deskMat);
desk.position.set(0, 0.15, 0.5);
scene.add(desk);

// Monitor Frame
const frameGeo = new THREE.BoxGeometry(1.6, 1.0, 0.06);
const frameMat = new THREE.MeshStandardMaterial({ color: 0x0a0a0f, roughness: 0.2, metalness: 0.9 });
const monitorFrame = new THREE.Mesh(frameGeo, frameMat);
monitorFrame.position.set(0, 0.85, 0.1);
scene.add(monitorFrame);

// Screen Canvas Texture Setup
const canvas2d = document.createElement('canvas');
canvas2d.width = 1024;
canvas2d.height = 640;
const ctx = canvas2d.getContext('2d');

const screenTexture = new THREE.CanvasTexture(canvas2d);
screenTexture.generateMipmaps = true;
screenTexture.minFilter = THREE.LinearMipmapLinearFilter;

const screenGeo = new THREE.PlaneGeometry(1.5, 0.9);
const screenMat = new THREE.MeshBasicMaterial({
    map: screenTexture,
    side: THREE.FrontSide
});
const monitorScreen = new THREE.Mesh(screenGeo, screenMat);
monitorScreen.position.set(0, 0.85, 0.132);
scene.add(monitorScreen);

// Stand legs
const standGeo = new THREE.CylinderGeometry(0.04, 0.06, 0.7, 16);
const standMat = new THREE.MeshStandardMaterial({ color: 0x222233, metalness: 0.9, roughness: 0.2 });
const stand = new THREE.Mesh(standGeo, standMat);
stand.position.set(0, 0.5, 0.3);
stand.rotation.x = Math.PI / 12;
scene.add(stand);

let cachedCandles = [];

export function updateCandles(candles) {
    if (candles && candles.length > 0) {
        cachedCandles = candles;
        drawChart();
    }
}

function drawChart() {
    const w = canvas2d.width;
    const h = canvas2d.height;

    // Background
    ctx.fillStyle = '#050508';
    ctx.fillRect(0, 0, w, h);

    // Grid lines
    ctx.strokeStyle = '#121222';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 64) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, h);
        ctx.stroke();
    }
    for (let y = 0; y < h; y += 64) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
    }

    if (cachedCandles.length === 0) {
        ctx.fillStyle = '#33ccff';
        ctx.font = '24px JetBrains Mono';
        ctx.textAlign = 'center';
        ctx.fillText('LOADING BTC OHLCV STREAM...', w / 2, h / 2);
        screenTexture.needsUpdate = true;
        return;
    }

    const candles = cachedCandles.slice(-80); // show last 80 candles
    const prices = candles.map(c => [c.l, c.h]).flat();
    const minPrice = Math.min(...prices);
    const maxPrice = Math.max(...prices);
    const priceRange = (maxPrice - minPrice) || 1;

    const padding = 60;
    const chartW = w - padding * 2;
    const chartH = h - padding * 2;
    const candleW = Math.max(2, chartW / candles.length - 3);

    candles.forEach((c, i) => {
        const x = padding + i * (chartW / candles.length) + candleW / 2;
        const yHigh = padding + chartH - ((c.h - minPrice) / priceRange) * chartH;
        const yLow = padding + chartH - ((c.l - minPrice) / priceRange) * chartH;
        const yOpen = padding + chartH - ((c.o - minPrice) / priceRange) * chartH;
        const yClose = padding + chartH - ((c.c - minPrice) / priceRange) * chartH;

        const isGreen = c.c >= c.o;
        const color = isGreen ? '#00ff88' : '#ff3355';

        // Wick
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(x, yHigh);
        ctx.lineTo(x, yLow);
        ctx.stroke();

        // Body
        ctx.fillStyle = color;
        const bodyY = Math.min(yOpen, yClose);
        const bodyH = Math.max(2, Math.abs(yClose - yOpen));
        ctx.fillRect(x - candleW / 2, bodyY, candleW, bodyH);
    });

    // Price label on right
    const lastC = candles[candles.length - 1];
    if (lastC) {
        ctx.fillStyle = '#33ccff';
        ctx.font = 'bold 20px JetBrains Mono';
        ctx.textAlign = 'left';
        ctx.fillText(`BTC/USDT  $${lastC.c.toFixed(2)}`, padding, 40);
    }

    screenTexture.needsUpdate = true;
}
