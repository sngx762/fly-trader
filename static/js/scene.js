/**
 * 3D Scene Setup (Three.js r160+): Camera, lights, fog, floor, particles, and post-processing bloom.
 */

import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';

// Canvas & Renderer
const canvas = document.querySelector('#webgl-canvas');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;

// Scene & Fog
export const scene = new THREE.Scene();
scene.background = new THREE.Color(0x050508);
scene.fog = new THREE.FogExp2(0x050508, 0.12);

// Camera
export const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 100);
camera.position.set(0, 1.4, 4.2);
camera.lookAt(0, 0.8, 0);

// Lights
const ambientLight = new THREE.AmbientLight(0x223344, 0.5);
scene.add(ambientLight);

const dirLight = new THREE.DirectionalLight(0xffe0a0, 1.5);
dirLight.position.set(3, 5, 2);
scene.add(dirLight);

const bluePointLight = new THREE.PointLight(0x00aaff, 1.0, 10);
bluePointLight.position.set(-3, 2, -2);
scene.add(bluePointLight);

// Monitor Glow Light (will be near monitor)
export const monitorLight = new THREE.PointLight(0x33ccff, 2.5, 5);
monitorLight.position.set(0, 0.9, 0.6);
scene.add(monitorLight);

// Post-processing Bloom (with try/catch fallback for Safari/mobile)
export let composer = null;
try {
    const renderPass = new RenderPass(scene, camera);
    const bloomPass = new UnrealBloomPass(
        new THREE.Vector2(window.innerWidth, window.innerHeight),
        0.7,  // strength
        0.5,  // radius
        0.7   // threshold
    );
    composer = new EffectComposer(renderer);
    composer.addPass(renderPass);
    composer.addPass(bloomPass);
} catch (e) {
    console.warn("UnrealBloomPass failed to initialize, falling back to standard renderer:", e);
    composer = null;
}

// Floor
const floorGeo = new THREE.PlaneGeometry(20, 20);
const floorMat = new THREE.MeshStandardMaterial({
    color: 0x0a0a12,
    roughness: 0.15,
    metalness: 0.85
});
const floor = new THREE.Mesh(floorGeo, floorMat);
floor.rotation.x = -Math.PI / 2;
floor.position.y = 0;
scene.add(floor);

// Atmospheric Particle Field (200 particles)
const particleGeo = new THREE.BufferGeometry();
const particleCount = 200;
const posArray = new Float32Array(particleCount * 3);

for (let i = 0; i < particleCount * 3; i += 3) {
    posArray[i] = (Math.random() - 0.5) * 10;
    posArray[i + 1] = Math.random() * 4;
    posArray[i + 2] = (Math.random() - 0.5) * 10;
}
particleGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
const particleMat = new THREE.PointsMaterial({
    size: 0.03,
    color: 0x33ccff,
    transparent: true,
    opacity: 0.6,
    blending: THREE.AdditiveBlending
});
const particles = new THREE.Points(particleGeo, particleMat);
scene.add(particles);

// Window Resize Handler
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
    if (composer) composer.setSize(window.innerWidth, window.innerHeight);
});

// Animation Loop Clock
const clock = new THREE.Clock();

export function getElapsedTime() {
    return clock.getElapsedTime();
}

export function renderScene() {
    const t = clock.getElapsedTime();
    
    // Camera breathing effect
    camera.position.y = 1.4 + Math.sin(t * 0.4) * 0.03;
    
    // Slowly drift particles
    const positions = particleGeo.attributes.position.array;
    for (let i = 1; i < particleCount * 3; i += 3) {
        positions[i] -= 0.001;
        if (positions[i] < 0) positions[i] = 4;
    }
    particleGeo.attributes.position.needsUpdate = true;

    if (composer) {
        composer.render();
    } else {
        renderer.render(scene, camera);
    }
}
