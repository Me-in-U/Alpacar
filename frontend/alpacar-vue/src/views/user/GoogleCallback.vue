<template>
	<div class="callback">로그인 중… 잠시만 기다려주세요.</div>
</template>

<script lang="ts">
import { defineComponent, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useUserStore } from "@/stores/user";
import { alert, alertSuccess, alertWarning, alertError } from "@/composables/useAlert";
export default defineComponent({
	name: "GoogleCallback",
	setup() {
		const router = useRouter();
		const route = useRoute();
		const userStore = useUserStore();

		onMounted(async () => {
			// async로 변경
			const access = route.query.access as string;
			const refresh = route.query.refresh as string;
			if (access && refresh) {
				// 1) 토큰 저장
				localStorage.setItem("access_token", access);
				localStorage.setItem("refresh_token", refresh);

				// 2) Pinia에서 프로필 조회 및 저장
				try {
					await userStore.fetchMe(access);
					router.replace("/main");
				} catch (e) {
					console.error(e);
					await alertError("프로필 조회 중 오류가 발생했습니다.");
					router.replace("/");
				}
			} else {
				await alertError("구글 로그인에 실패했습니다.");
				router.replace("/");
			}
		});

		return {};
	},
});
</script>

<style scoped>
.callback {
	font-family: "Inter", sans-serif;
	font-size: 16px;
	color: #666;
	margin-top: 200px;
	text-align: center;
}
</style>
