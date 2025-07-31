// static/service-worker.js
self.addEventListener("push", (event) => {
	let data = {};
	if (event.data) {
		data = event.data.json();
	}
	event.waitUntil(
		self.registration.showNotification(data.title || "OCR 알림", {
			body: data.body || "",
			icon: "/static/icons/favicon.ico",
		})
	);
});
