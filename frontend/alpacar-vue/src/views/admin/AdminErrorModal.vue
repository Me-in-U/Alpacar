<template>
	<div class="container">
		<!-- 빨강 경고 아이콘 -->
		<img class="icon" src="@/assets/alert_red.png" alt="Error" />

		<!-- 안내 문구 -->
		<p class="message1">주차 공간 배정 시스템에 문제가 생겼습니다.</p>
		<p class="message2">수동 배정 페이지로 이동합니다.</p>

		<!-- 확인 버튼 -->
		<button class="confirm-btn" @click="onConfirm">확인</button>
	</div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";

const router = useRouter();

function onConfirm() {
	router.push("/admin-parkingreassign");
}
</script>

<style scoped>
.container {
	position: fixed;
	top: 50%;
	left: 50%;
	transform: translate(-50%, -50%);
	width: 50vw;
	max-width: 500px;
	background-color: #ebe3d5;
	border: 3px solid #000;
	box-shadow: 0px 6px 4px rgba(0, 0, 0, 0.25);
	box-sizing: border-box;
	padding-top: 20px;
	padding-bottom: 40px;
	text-align: center;
	font-family: Inter, sans-serif;
	color: #000;
}

/* 아이콘 위치 */
.icon {
	width: 75px;
	height: 75px;
	margin: 0 auto;
	display: block;
}

/* 첫 번째 메시지: 아이콘 바로 아래 */
.message1 {
	margin-top: 16px;
	font-size: 24px;
	font-weight: 600;
	line-height: 1.4;
	padding: 0 16px;
}

/* 두 번째 메시지: 첫 번째 메시지 바로 아래 */
.message2 {
	margin-top: 16px;
	font-size: 24px;
	font-weight: 600;
	line-height: 1.4;
	padding: 0 16px;
}

/* 확인 버튼: 메시지 아래로 충분히 띄워서 배치 */
.confirm-btn {
	margin-top: 32px;
	width: 170px;
	height: 50px;
	background-color: #4d4d4d;
	color: #fff;
	border: none;
	cursor: pointer;
	font-weight: 600;
	font-size: 24px;
	line-height: 50px;
	text-align: center;
	border-radius: 4px;
}

.confirm-btn:hover {
	background-color: #383838;
}
</style>
