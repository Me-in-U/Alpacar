<template>
	<div class="modal-overlay">
		<div class="modal-container">
			<!-- X Close Button -->
			<button class="modal-close-btn" @click="onClose" aria-label="닫기">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<line x1="18" y1="6" x2="6" y2="18"></line>
					<line x1="6" y1="6" x2="18" y2="18"></line>
				</svg>
			</button>

			<p class="modal-title">관리자만 접근 가능합니다</p>
			<button class="back-button" @click="onClose">돌아가기</button>
		</div>
	</div>
</template>

<script setup lang="ts">
const emit = defineEmits(["close"]);

function onClose() {
	emit("close");
}
</script>

<style scoped>
.modal-overlay {
	position: fixed;
	top: 0;
	left: 0;
	width: 100vw;
	height: 100vh;
	background-color: rgba(0, 0, 0, 0.4);
	z-index: 9999;
	display: flex;
	justify-content: center;
	align-items: center;
}

.modal-container {
	background-color: #f9f5ec;
	border: 1px solid #000;
	border-radius: 12px;
	padding: 48px 32px;
	width: 480px;
	box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25);
	text-align: center;
	position: relative;
}

.modal-title {
	font-size: 24px;
	font-weight: 700;
	font-family: Inter, sans-serif;
	margin-bottom: 40px; /* ✅ 여기 간격 조절 */
}

.back-button {
	background-color: #4b3d34;
	color: #fff;
	font-size: 20px;
	font-weight: 600;
	padding: 14px 32px;
	border: none;
	border-radius: 8px;
	cursor: pointer;
}

/* Modal Close Button */
.modal-close-btn {
	position: absolute;
	top: 16px;
	right: 16px;
	width: 32px;
	height: 32px;
	background: transparent;
	border: none;
	cursor: pointer;
	display: flex;
	align-items: center;
	justify-content: center;
	border-radius: 4px;
	color: #666;
	transition: all 0.2s ease;
}

.modal-close-btn:hover {
	background-color: rgba(0, 0, 0, 0.1);
	color: #333;
}

.modal-close-btn svg {
	width: 20px;
	height: 20px;
}
</style>
