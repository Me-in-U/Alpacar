<template>
	<div class="callback">
		<p>로그인 처리 중… 잠시만 기다려 주세요.</p>
	</div>
</template>

<script lang="ts">
import { defineComponent, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { API_BASE } from "@/utils/api";

export default defineComponent({
	setup() {
		const router = useRouter();
		const route = useRoute();

		onMounted(async () => {
			const code = route.query.code as string;
			if (!code) {
				alert("인증 코드가 없습니다.");
				return router.replace("/login");
			}

			try {
				// ➊ 백엔드에 code 전달 → 토큰 받기
				const res = await fetch(`${API_BASE}/auth/social/google/callback/?code=${encodeURIComponent(code)}`);
				const data = await res.json();
				if (!res.ok || !data.access) {
					alert("소셜 로그인에 실패했습니다.");
					return router.replace("/login");
				}

				// ➋ 받은 토큰 저장
				localStorage.setItem("access_token", data.access);
				localStorage.setItem("refresh_token", data.refresh);

				// ➌ 메인 페이지로 이동
				router.replace("/main");
			} catch (err) {
				console.error(err);
				alert("네트워크 오류가 발생했습니다.");
				router.replace("/login");
			}
		});
	},
});
</script>
