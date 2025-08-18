<template>
	<div class="main-page-container">
		<Header />

		<div class="main-content">
			<div class="center-content">
				<img src="@/assets/alert_black.png" width="67" height="67" alt="경고" />
				<h2 class="title">주차완료</h2>
				<p class="body">주차완료</p>
			</div>
		</div>

		<BottomNavigation />
	</div>
</template>

<script setup lang="ts">
import Header from "@/components/Header.vue";
import BottomNavigation from "@/components/BottomNavigation.vue";
</script>

<style scoped>
/* 모바일 컨테이너 */
.main-page-container {
	width: 100vw;
	max-width: 440px;
	min-height: 100vh;
	background: #F9F5EC;
	margin: 0 auto;
	display: flex;
	flex-direction: column;
}
.main-content {
	flex: 1;
	padding-top: 80px;
	padding-bottom: 80px;
	min-height: calc(100vh - 160px);
	overflow-y: auto;
}

/* 상태 화면 */
.unrecognized-container,
.loading-container {
	width: 100%;
	min-height: calc(100vh - 160px);
	display: flex;
	flex-direction: column;
	justify-content: center;
	align-items: center;
	text-align: center;
	padding: 0 16px;
}
.center-content .title {
	font-size: 20px;
	font-weight: 600;
	color: #464038;
	margin: 16px 0 12px;
}
.center-content .body {
	font-size: 16px;
	color: #666;
	line-height: 1.4;
}
.car-animation-wrapper {
	position: relative;
	width: 100%;
	max-width: 400px;
	height: 100px;
	overflow: hidden;
}
.car-animation {
	position: absolute;
	bottom: 0;
	left: -100px;
	width: 100px;
	height: auto;
	animation: moveCar 4s linear infinite;
}
@keyframes moveCar {
	0% {
		transform: translateX(0);
		opacity: 0;
	}
	10% {
		opacity: 1;
	}
	90% {
		opacity: 1;
	}
	100% {
		transform: translateX(600px);
		opacity: 0;
	}
}
.loading-text {
	margin-top: 16px;
	font-size: 16px;
	color: #666;
}

/* 추천 결과 */
.recommend-header {
	display: flex;
	flex-direction: column;
	align-items: center;
	margin-bottom: 24px;
	text-align: center;
}
.title {
	font-size: 28px;
	font-weight: 700;
	color: #333;
	padding-top: 24px;
}
.info-box {
	width: 60%;
	background: #fff;
	border-radius: 8px;
	padding: 16px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
	margin-bottom: 24px;
}
.info-title {
	font-size: 18px;
	font-weight: 700;
	margin-bottom: 6px;
}
.info-detail {
	font-size: 14px;
	color: #666;
	margin: 2px 0;
}

/* 지도 */
.map-section {
	text-align: center;
}
.map-wrapper {
	--map-w: 400px;
	--map-h: 354px;
	--slot-w: 52px;
	--slot-h: 98px;
	--slot-gap: 6px;
	position: relative;
	width: 100%;
	max-width: var(--map-w);
	height: var(--map-h);
	background: #444;
	border-radius: 8px;
	margin: 0 auto;
}
.overlay {
	position: absolute;
	top: 0;
	left: 0;
	pointer-events: none;
	z-index: 2;
}
.row {
	display: flex;
	justify-content: center;
	gap: var(--slot-gap);
	position: absolute;
	left: 50%;
	transform: translateX(-50%);
}
.row-1 {
	top: 10px;
}
.row-2 {
	bottom: 10px;
}
.aisle {
	width: 24px;
}
.divider {
	position: absolute;
	top: 50%;
	width: 100%;
	border-top: 3px dashed #fff;
	transform: translateY(-50%);
}

.spot {
	width: var(--slot-w);
	height: var(--slot-h);
	border: 2px solid #fff;
	color: #fff;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 14px;
}
.spot--placeholder {
	visibility: hidden;
	border: 0;
	background: transparent;
}
.spot.empty {
	background: #999;
}
.spot.occupied {
	background: #fe5454;
}
.spot.reserved {
	background: #f5dd29;
	color: #333;
	font-weight: 700;
}
.spot.recommended {
	outline: 3px solid #8fcd2b;
	box-shadow: inset 0 0 0 2px #fff;
}

.pin {
	position: absolute;
	width: 24px;
	height: 24px;
	z-index: 3;
}
.car {
	position: absolute;
	top: calc(50% + 16px);
	left: 10px;
	width: 56px;
	height: 32px;
}

.legend {
	display: flex;
	justify-content: center;
	gap: 16px;
	margin: 16px 0 32px;
}
.legend-item {
	display: flex;
	align-items: center;
	gap: 6px;
	font-size: 12px;
	color: #444;
}
.box {
	width: 14px;
	height: 14px;
	border-radius: 4px;
}
.recommended.box {
	background: #8fcd2b;
}
.occupied.box {
	background: #fe5454;
}
.empty.box {
	background: #999;
}
.reserved.box {
	background: #f5dd29;
}

/* 데스크톱에서 440px 고정 */
@media (min-width: 441px) {
	.main-page-container {
		width: 440px;
	}
	.main-content {
		min-height: calc(100vh - 160px);
		padding-bottom: 20px;
	}
}
</style>
