// vite.config.ts
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import vueDevTools from "vite-plugin-vue-devtools";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
	server: {
		host: "0.0.0.0",
		port: 5173,
	},
	plugins: [
		vue(),
		vueDevTools(),
		VitePWA({
			strategies: "injectManifest", // ★ 커스텀 SW 주입 방식
			srcDir: "public", // SW 파일 위치
			filename: "service-worker.js", // public에 있는 파일 이름
			registerType: "autoUpdate", // 새 SW 있으면 자동 업데이트
			devOptions: {
				enabled: true,
				type: "module",
			},
			manifest: {
				name: "Alpacar - 스마트 주차 서비스",
				short_name: "Alpacar",
				description: "알파카와 함께하는 스마트 주차 관리 서비스",
				theme_color: "#776B5D",
				background_color: "#f3edea",
				display: "standalone",
				start_url: "/",
				scope: "/",
				orientation: "portrait",
				lang: "ko",
				categories: ["transportation", "utilities"],
				icons: [
					{
						src: "/alpaca-logo-small.png",
						sizes: "192x192",
						type: "image/png",
						purpose: "any maskable",
					},
					{
						src: "/alpaca-logo-small.png",
						sizes: "512x512",
						type: "image/png",
						purpose: "any maskable",
					},
				],
			},
			workbox: {
				cleanupOutdatedCaches: true, // 오래된 캐시 자동 제거
				globPatterns: ["**/*.{js,css,html,ico,png,svg}"],
				// runtimeCaching은 public/service-worker.js 내부 fetch 이벤트에서 처리
			},
		}),
	],
	resolve: {
		alias: {
			"@": fileURLToPath(new URL("./src", import.meta.url)),
		},
	},
});

// import { fileURLToPath, URL } from 'node:url'

// import { defineConfig } from 'vite'
// import vue from '@vitejs/plugin-vue'
// import vueDevTools from 'vite-plugin-vue-devtools'
// import { VitePWA } from 'vite-plugin-pwa'

// // https://vite.dev/config/
// export default defineConfig({
//   server: {
//     host: '0.0.0.0',
//     port: 5173
//   },
//   plugins: [
//     vue(),
//     vueDevTools(),
//     VitePWA({
//       registerType: 'prompt',
//       devOptions: {
//         enabled: true,
//         type: 'module'
//       },
//       includeAssets: ['favicon.ico', 'alpaca-logo-small.png', 'service-worker.js'],
//       manifest: {
//         name: 'Alpacar - 스마트 주차 서비스',
//         short_name: 'Alpacar',
//         description: '알파카와 함께하는 스마트 주차 관리 서비스',
//         theme_color: '#776B5D',
//         background_color: '#f3edea',
//         display: 'standalone',
//         start_url: '/',
//         scope: '/',
//         orientation: 'portrait',
//         lang: 'ko',
//         categories: ['transportation', 'utilities'],
//         icons: [
//           {
//             src: '/alpaca-logo-small.png',
//             sizes: '192x192',
//             type: 'image/png',
//             purpose: 'any maskable'
//           },
//           {
//             src: '/alpaca-logo-small.png',
//             sizes: '512x512',
//             type: 'image/png',
//             purpose: 'any maskable'
//           }
//         ]
//       },
//       workbox: {
//         globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
//         runtimeCaching: [
//           {
//             urlPattern: /^https:\/\/api\./,
//             handler: 'NetworkFirst',
//             options: {
//               cacheName: 'api-cache',
//               networkTimeoutSeconds: 10
//             }
//           }
//         ]
//       }
//     })
//   ],
//   resolve: {
//     alias: {
//       '@': fileURLToPath(new URL('./src', import.meta.url))
//     },
//   },
// })
