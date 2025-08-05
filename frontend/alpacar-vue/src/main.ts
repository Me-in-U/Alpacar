// main.ts
import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import router from "./router";
import { useUserStore } from "@/stores/user";

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.use(router);

// 앱 시작 시 한 번만 실행
const userStore = useUserStore();
const token = localStorage.getItem("access_token");
if (token) {
	userStore.fetchMe(token).catch(() => {
		// 토큰이 만료됐거나 오류가 나면 로그인 페이지로
		userStore.clearUser();
		router.push("/login");
	});
}

app.mount("#app");

// 서비스 워커 등록
if ("serviceWorker" in navigator) {
	window.addEventListener("load", () => {
		navigator.serviceWorker
			.register("/service-worker.js")
			.then((registration) => {
				console.log("서비스 워커 등록 성공:", registration.scope);
			})
			.catch((err) => {
				console.error("서비스 워커 등록 실패:", err);
			});
	});
}
