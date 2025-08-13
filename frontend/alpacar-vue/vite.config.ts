import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import vueDevTools from "vite-plugin-vue-devtools";
import { VitePWA } from "vite-plugin-pwa";

// https://vite.dev/config/
export default defineConfig({
	server: {
		host: "0.0.0.0",
		port: 5173,
	},
	plugins: [
		vue(),
		vueDevTools(),
		VitePWA({
			strategies: 'injectManifest',
			srcDir: 'public',
			filename: 'service-worker.js',
			injectRegister: false,
			registerType: "prompt",
			devOptions: {
				enabled: true,
				type: "module",
			},
			includeAssets: ["favicon.ico", "alpaca-192.png", "alpaca-512.png", "service-worker.js"],
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
						src: "/alpaca-192.png",
						sizes: "192x192",
						type: "image/png",
						purpose: "any maskable",
					},
					{
						src: "/alpaca-512.png",
						sizes: "512x512",
						type: "image/png",
						purpose: "any maskable",
					},
				],
			},
			workbox: {
				globPatterns: ["**/*.{js,css,html,ico,png,svg}"],
				skipWaiting: true,
				clientsClaim: true,
				runtimeCaching: [
					{
						urlPattern: /^https:\/\/api\./,
						handler: "NetworkFirst",
						options: {
							cacheName: "api-cache",
							networkTimeoutSeconds: 10,
						},
					},
				],
			},
		}),
	],
	resolve: {
		alias: {
			"@": fileURLToPath(new URL("./src", import.meta.url)),
		},
	},
});
