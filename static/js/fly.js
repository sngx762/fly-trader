/**
 * Procedural 3D Fly (Drosophila) with dynamic SNN-driven animations (wings, eyes, head tilt, reactions).
 */

import * as THREE from 'three';
import { scene, getElapsedTime } from './scene.js';

export const flyGroup = new THREE.Group();
flyGroup.position.set(0, 0.45, 0.35);
scene.add(flyGroup);

// Materials
const bodyMat = new THREE.MeshStandardMaterial({ color: 0x2a1a0a, roughness: 0.6, metalness: 0.3 });
const stripeMat = new THREE.MeshStandardMaterial({ color: 0x111111, roughness: 0.8 });
const headMat = new THREE.MeshStandardMaterial({ color: 0x3d2314, roughness: 0.5 });
const eyeMat = new THREE.MeshStandardMaterial({
    color: 0xff1100,
    emissive: 0xff2200,
    emissiveIntensity: 1.5,
    roughness: 0.1
});
const legMat = new THREE.MeshStandardMaterial({ color: 0x1a1005, roughness: 0.9 });

const wingMat = new THREE.MeshPhysicalMaterial({
    color: 0xffffff,
    transmission: 0.9,
    opacity: 0.4,
    transparent: true,
    roughness: 0.1,
    side: THREE.DoubleSide
});

// Fly Body Segments (Thorax & Abdomen)
const thoraxGeo = new THREE.SphereGeometry(0.12, 16, 16);
thoraxGeo.scale(1, 0.7, 1.2);
const thorax = new THREE.Mesh(thoraxGeo, bodyMat);
thorax.position.set(0, 0.15, 0);
flyGroup.add(thorax);

const abdomenGeo = new THREE.SphereGeometry(0.14, 16, 16);
abdomenGeo.scale(0.9, 0.7, 1.5);
const abdomen = new THREE.Mesh(abdomenGeo, bodyMat);
abdomen.position.set(0, 0.12, -0.22);
flyGroup.add(abdomen);

// Head
const headGeo = new THREE.SphereGeometry(0.09, 16, 16);
const head = new THREE.Mesh(headGeo, headMat);
head.position.set(0, 0.18, 0.18);
flyGroup.add(head);

// Compound Eyes
const eyeGeo = new THREE.SphereGeometry(0.04, 12, 12);
const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
leftEye.position.set(0.07, 0.20, 0.20);
flyGroup.add(leftEye);

const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
rightEye.position.set(-0.07, 0.20, 0.20);
flyGroup.add(rightEye);

// Wings
const wingGeo = new THREE.PlaneGeometry(0.4, 0.18);
wingGeo.translate(0.2, 0, 0); // pivot at base

const leftWing = new THREE.Mesh(wingGeo, wingMat);
leftWing.position.set(0.05, 0.26, 0.05);
leftWing.rotation.x = -Math.PI / 6;
flyGroup.add(leftWing);

const rightWing = new THREE.Mesh(wingGeo, wingMat);
rightWing.position.set(-0.05, 0.26, 0.05);
rightWing.rotation.x = -Math.PI / 6;
rightWing.rotation.y = Math.PI;
flyGroup.add(rightWing);

// 6 Legs
const legGeo = new THREE.CylinderGeometry(0.008, 0.004, 0.3, 6);
for (let i = 0; i < 6; i++) {
    const leg = new THREE.Mesh(legGeo, legMat);
    const side = i % 2 === 0 ? 1 : -1;
    const zOffset = (Math.floor(i / 2) - 1) * 0.08;
    leg.position.set(side * 0.12, 0.05, zOffset);
    leg.rotation.z = side * -0.6;
    leg.rotation.x = (i % 3) * 0.2;
    flyGroup.add(leg);
}

// State for animations
let currentDopamine = 0.2;
let targetHeadTilt = 0;
let actionReactionTimer = 0;
let currentAction = 'HOLD';

export function updateFlyState(data) {
    if (data.dopamine !== undefined) currentDopamine = data.dopamine;
    if (data.rpe !== undefined) {
        targetHeadTilt = data.rpe * 0.2;
    }
    if (data.action && data.action !== currentAction) {
        currentAction = data.action;
        actionReactionTimer = 1.0; // trigger animation burst
    }
}

export function animateFly() {
    const t = getElapsedTime();

    // Wing flapping (speed proportional to dopamine/activity)
    const flapSpeed = 25 + currentDopamine * 40;
    const flapAngle = Math.sin(t * flapSpeed) * 0.7;
    leftWing.rotation.z = flapAngle;
    rightWing.rotation.z = -flapAngle;

    // Body bobbing
    thorax.position.y = 0.15 + Math.sin(t * 8) * 0.004;
    head.position.y = 0.18 + Math.sin(t * 8) * 0.004;

    // Head tilt based on RPE
    head.rotation.x = THREE.MathUtils.lerp(head.rotation.x, targetHeadTilt, 0.1);

    // Action reaction animations
    if (actionReactionTimer > 0) {
        actionReactionTimer -= 0.016;
        if (currentAction === 'BUY') {
            flyGroup.position.z = 0.35 + Math.sin(actionReactionTimer * Math.PI * 4) * 0.05;
            leftEye.material.emissiveIntensity = 3.0;
            rightEye.material.emissiveIntensity = 3.0;
        } else if (currentAction === 'SELL') {
            flyGroup.rotation.y = Math.sin(actionReactionTimer * Math.PI * 6) * 0.3;
            leftEye.material.emissiveIntensity = 2.5;
            rightEye.material.emissiveIntensity = 2.5;
        }
    } else {
        flyGroup.position.z = 0.35;
        flyGroup.rotation.y = 0;
        leftEye.material.emissiveIntensity = 1.5;
        rightEye.material.emissiveIntensity = 1.5;
    }
}
