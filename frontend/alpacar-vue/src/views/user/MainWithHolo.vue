<template>
	<div class="cards-page">
		<h1>내 차량 카드 데모</h1>
		<div class="cards-container">
			<!-- 홀로그램 카드 컴포넌트 -->
			<HoloCard name="홍길동" number="123 가 4567" />
		</div>
	</div>
</template>

<script setup lang="ts">
import HoloCard from "@/components/HoloCard.vue";
</script>

<style scoped>
.cards-page {
	padding: 20px;
	text-align: center;
}
.cards-container {
	display: flex;
	justify-content: center;
	gap: 40px;
	flex-wrap: wrap;
}
</style>
