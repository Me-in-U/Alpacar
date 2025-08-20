<template>
	<div class="callback">로그인 중… 잠시만 기다려주세요.</div>
</template>

<script lang="ts">
import { defineComponent, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useUserStore } from "@/stores/user";
import { alertError } from "@/composables/useAlert";
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
				// 1) 보안 토큰 저장 (SecureTokenManager 사용)
				const { SecureTokenManager } = await import("@/utils/security");
				SecureTokenManager.setSecureToken("access_token", access, true); // 세션 저장
				SecureTokenManager.setSecureToken("refresh_token", refresh, true);

				// ✅ 토큰이 URL에 남지 않게 먼저 쿼리 제거(리퍼러 안전)
				window.history.replaceState(null, "", "/auth/social/google/callback");

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
