<template>
	<div class="alert-test-container">
		<h1>Alert System Test</h1>

		<div class="test-section">
			<h2>Alert Types</h2>
			<div class="button-grid">
				<button @click="testInfo" class="test-btn info">Info Alert</button>
				<button @click="testSuccess" class="test-btn success">Success Alert</button>
				<button @click="testWarning" class="test-btn warning">Warning Alert</button>
				<button @click="testError" class="test-btn error">Error Alert</button>
				<button @click="testConfirm" class="test-btn confirm">Confirm Dialog</button>
			</div>
		</div>

		<div class="test-section">
			<h2>Auto-Close Test</h2>
			<div class="button-grid">
				<button @click="testAutoClose" class="test-btn auto">Auto-Close Success (3s)</button>
			</div>
		</div>

		<div class="test-section">
			<h2>Multiple Alerts</h2>
			<div class="button-grid">
				<button @click="testMultiple" class="test-btn multiple">Show Multiple Alerts</button>
			</div>
		</div>

		<div class="result" v-if="lastResult">
			<h3>Last Result:</h3>
			<p>{{ lastResult }}</p>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { alert, alertSuccess, alertWarning, alertError, confirm } from "@/composables/useAlert";

const lastResult = ref("");

const testInfo = async () => {
	const result = await alert("이것은 정보 알림입니다. 기본 색상과 아이콘이 표시됩니다.", "정보 알림");
	lastResult.value = `Info alert result: ${result}`;
};

const testSuccess = async () => {
	const result = await alertSuccess("작업이 성공적으로 완료되었습니다!", "성공");
	lastResult.value = `Success alert result: ${result}`;
};

const testWarning = async () => {
	const result = await alertWarning("주의가 필요한 상황입니다. 계속 진행하시겠습니까?", "주의");
	lastResult.value = `Warning alert result: ${result}`;
};

const testError = async () => {
	const result = await alertError("오류가 발생했습니다. 다시 시도해주세요.", "오류");
	lastResult.value = `Error alert result: ${result}`;
};

const testConfirm = async () => {
	const result = await confirm("정말로 삭제하시겠습니까?", "삭제 확인", "삭제", "취소");
	lastResult.value = `Confirm result: ${result ? "Confirmed" : "Cancelled"}`;
};

const testAutoClose = async () => {
	const result = await alertSuccess("이 메시지는 3초 후에 자동으로 닫힙니다.", "자동 닫기 테스트");
	lastResult.value = `Auto-close result: ${result}`;
};

const testMultiple = async () => {
	// 여러 알림을 순차적으로 표시
	await alert("첫 번째 알림입니다.");
	await alertWarning("두 번째 경고 알림입니다.");
	await alertSuccess("모든 테스트가 완료되었습니다!");
	lastResult.value = "Multiple alerts completed";
};
</script>

<style scoped>
.alert-test-container {
	max-width: 800px;
	margin: 0 auto;
	padding: 20px;
	font-family: "Inter", sans-serif;
}

h1 {
	text-align: center;
	color: #4b3d34;
	margin-bottom: 30px;
}

.test-section {
	margin-bottom: 30px;
	padding: 20px;
	border: 1px solid #e5e7eb;
	border-radius: 8px;
	background: #f9fafb;
}

h2 {
	color: #374151;
	margin-bottom: 15px;
}

.button-grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
	gap: 12px;
}

.test-btn {
	padding: 12px 20px;
	border: none;
	border-radius: 8px;
	font-family: "Inter", sans-serif;
	font-weight: 500;
	cursor: pointer;
	transition: all 0.2s ease;
}

.test-btn:hover {
	transform: translateY(-2px);
	box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.test-btn.info {
	background: #4b3d34;
	color: white;
}

.test-btn.success {
	background: #10b981;
	color: white;
}

.test-btn.warning {
	background: #f59e0b;
	color: white;
}

.test-btn.error {
	background: #ef4444;
	color: white;
}

.test-btn.confirm {
	background: #6366f1;
	color: white;
}

.test-btn.auto {
	background: #10b981;
	color: white;
}

.test-btn.multiple {
	background: #8b5cf6;
	color: white;
}

.result {
	margin-top: 20px;
	padding: 15px;
	background: #f0f9ff;
	border: 1px solid #0ea5e9;
	border-radius: 8px;
}

.result h3 {
	margin: 0 0 8px 0;
	color: #0369a1;
}

.result p {
	margin: 0;
	color: #075985;
}
</style>
