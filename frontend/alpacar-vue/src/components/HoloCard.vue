<template>
	<div class="holo-wrapper">
		<!-- .card: tilt 전용 -->
		<div ref="card" class="card" @mousemove="onMove" @touchmove.passive.prevent="onMove" @mouseleave="onLeave" @touchend="onLeave" @click="toggleFlip">
			<div class="card-inner" :class="{ flipped: isFlipped }">
				<!-- 앞면 -->
				<div class="face front">
					<span class="label name">{{ name }}</span>
					<span class="label number">{{ number }}</span>
				</div>
				<!-- 뒷면 -->
				<div class="face back"></div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, defineProps } from "vue";

const card = ref<HTMLElement | null>(null);
let ticking = false;
const isFlipped = ref(false);

const { name, number } = defineProps<{
	name: string;
	number: string;
}>();

function toggleFlip() {
	isFlipped.value = !isFlipped.value;
}

function onMove(e: MouseEvent | TouchEvent) {
	if (!card.value) return;
	e.preventDefault();

	if (!ticking) {
		window.requestAnimationFrame(() => {
			const el = card.value!;
			const rect = el.getBoundingClientRect();
			let x: number, y: number;
			if ("touches" in e) {
				x = e.touches[0].clientX - rect.left;
				y = e.touches[0].clientY - rect.top;
			} else {
				x = (e as MouseEvent).offsetX;
				y = (e as MouseEvent).offsetY;
			}
			const w = rect.width,
				h = rect.height;
			const px = Math.abs((100 / w) * x - 100);
			const py = Math.abs((100 / h) * y - 100);
			const pa = 50 - px + (50 - py);

			// 변수 계산
			const lp = 50 + (px - 50) / 1.5;
			const tp = 50 + (py - 50) / 1.5;
			const pxs = 50 + (px - 50) / 7;
			const pys = 50 + (py - 50) / 7;
			const opc = (20 + Math.abs(pa) * 1.5) / 100;
			const rotX = ((tp - 50) / 2) * -1;
			const rotY = ((lp - 50) / 1.5) * 0.5;

			// CSS 변수 업데이트
			el.style.setProperty("--lp", `${lp}%`);
			el.style.setProperty("--tp", `${tp}%`);
			el.style.setProperty("--px_s", `${pxs}%`);
			el.style.setProperty("--py_s", `${pys}%`);
			el.style.setProperty("--opc", `${opc}`);
			// Tilt 적용
			el.style.transform = `rotateX(${rotX}deg) rotateY(${rotY}deg)`;

			ticking = false;
		});
		ticking = true;
	}
}

function onLeave() {
	const el = card.value!;
	if (!card.value) return;
	// 바로 원위치 & 변수 리셋 (CSS transition 이 자동으로 애니메이트)
	el.style.transform = "rotateX(0deg) rotateY(0deg)";
	el.style.setProperty("--lp", "50%");
	el.style.setProperty("--tp", "50%");
	el.style.setProperty("--px_s", "50%");
	el.style.setProperty("--py_s", "50%");
	el.style.setProperty("--opc", "0.75");
}

onMounted(() => {
	const el = card.value!;
	el.addEventListener("mousemove", onMove);
	el.addEventListener("touchmove", onMove, { passive: false });
	el.addEventListener("mouseleave", onLeave);
	el.addEventListener("touchend", onLeave);
});

onUnmounted(() => {
	const el = card.value;
	if (!el) return;
	el.removeEventListener("mousemove", onMove);
	el.removeEventListener("touchmove", onMove);
	el.removeEventListener("mouseleave", onLeave);
	el.removeEventListener("touchend", onLeave);
});
</script>

<style scoped>
.holo-wrapper {
	--c1: rgb(134, 243, 255);
	--c2: rgb(255, 145, 244);
	--front: url("@/assets/test-card.png");
	--back: url("@/assets/test-card-back.png");
	perspective: 800px;
	display: inline-block;
}

.card {
	width: 200px;
	height: 280px;
	box-shadow: -5px -5px 5px -5px var(--c1), 5px 5px 5px -5px var(--c2), 0 55px 35px -20px rgba(0, 0, 0, 0.5);
	background: var(--front) center/cover no-repeat;
	position: relative;
	isolation: isolate;
	transform-style: preserve-3d;
	touch-action: none;

	/* 언제나 부드러운 복귀를 위한 transition */
	transition: transform 0.3s ease-out;

	/* 초기 홀로그램 변수 */
	--lp: 50%;
	--tp: 50%;
	--px_s: 50%;
	--py_s: 50%;
	--opc: 0.75;
}

.card::before,
.card::after {
	content: "";
	position: absolute;
	inset: 0;
	pointer-events: none;
	mix-blend-mode: color-dodge;
}

.card::before {
	background: linear-gradient(115deg, transparent 0%, var(--c1) 25%, transparent 47%, transparent 53%, var(--c2) 75%, transparent 100%) no-repeat;
	background-size: 300% 300%;
	background-position: var(--lp) var(--tp);
	opacity: 0.5;
	filter: brightness(0.5);
}

.card::after {
	background: url("https://assets.codepen.io/13471/sparkles.gif"), url("https://assets.codepen.io/13471/holo.png"),
		linear-gradient(125deg, #ff008450 15%, #fca40040 30%, #ffff0030 40%, #00ff8a20 60%, #00cfff40 70%, #cc4cfa50 85%);
	background-size: 160%;
	background-position: var(--px_s) var(--py_s);
	background-blend-mode: overlay;
	opacity: var(--opc);
	filter: brightness(1) contrast(1);
}

.card:hover {
	box-shadow: -20px -20px 30px -25px var(--c1), 20px 20px 30px -25px var(--c2), 0 55px 35px -20px rgba(0, 0, 0, 0.5);
}

/* 카드 위에 표시할 텍스트 */
.label {
	position: absolute;
	transform: translateX(-50%);
	color: rgb(233, 233, 233);
	text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
	font-family: "Inter", sans-serif;
	pointer-events: none;
}

.label.name {
	bottom: 31%;
	left: 63%;
	font-size: 1.1rem;
	font-weight: 600;
}

.label.number {
	bottom: 17%;
	left: 55%;
	font-size: 0.9rem;
	font-weight: 500;
}
</style>
