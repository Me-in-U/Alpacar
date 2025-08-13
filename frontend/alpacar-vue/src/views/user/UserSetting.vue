<template>
  <div class="user-setting">
    <!-- Header -->
    <Header />

    <!-- Content -->
    <div class="user-setting__content">
      <!-- 프로필 섹션: 닉네임 / 전화번호 / 비밀번호 (행 + 우측 꺾쇠) -->
      <div class="profile-card">
        <!-- 닉네임 행 -->
        <button
          class="setting-row"
          type="button"
          @click="openNicknameModal"
        >
          <div class="setting-row__text">
            <div class="setting-row__label">
              닉네임
            </div>
            <div class="setting-row__value">
              {{ userInfo?.nickname || '-' }}
            </div>
          </div>
          <span class="chevron" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
        </button>

        <div class="divider"></div>

        <!-- 전화번호 행 -->
        <button
          class="setting-row"
          type="button"
          @click="openPhoneModal"
        >
          <div class="setting-row__text">
            <div class="setting-row__label">
              전화번호
            </div>
            <div class="setting-row__value">
              {{ formatPhoneNumber(userInfo?.phone) || '-' }}
            </div>
          </div>
          <span class="chevron" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
        </button>

        <div class="divider"></div>

        <!-- 비밀번호 행 -->
        <button
          class="setting-row"
          type="button"
          @click="openPasswordModal"
        >
          <div class="setting-row__text">
            <div class="setting-row__label">
              비밀번호
            </div>
            <div class="setting-row__value setting-row__value--placeholder">
              변경하기
            </div>
          </div>
          <span class="chevron" aria-hidden="true">
            <svg viewBox="0 0 24 24">
              <path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
        </button>
      </div>

      <!-- 알림 설정 -->
      <div class="section-title">
        알림 설정
      </div>

      <div class="notification-settings">
        <div class="notification-item">
          <div class="notification-item__content">
            <div class="notification-item__label">
              푸시 알림
            </div>
            <div class="notification-item__desc">
              주차 입출차 및 중요 알림 수신
            </div>
          </div>
          <div class="notification-item__toggle">
            <button
              class="toggle-button"
              :class="{ 'toggle-button--active': isNotificationEnabled }"
              @click="toggleNotifications"
            >
              {{ isNotificationEnabled ? '켜짐' : '꺼짐' }}
            </button>
          </div>
        </div>


        <div class="notification-item">
          <div class="notification-item__content">
            <div class="notification-item__label">
              앱 설치하기
            </div>
            <div class="notification-item__desc">
              앱처럼 사용하기
            </div>
          </div>
          <div class="notification-item__toggle">
            <button
              class="install-button"
              @click="installPWA"
              :disabled="!canInstallPWA"
            >
              {{ canInstallPWA ? '설치' : '설치됨' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Navigation -->
    <BottomNavigation />

    <!-- 닉네임 수정 모달 -->
    <div
      v-if="showNicknameModal"
      class="modal-overlay"
      @click="showNicknameModal = false"
    >
      <div
        class="modal modal--nickname"
        @click.stop
      >
        <h3 class="modal__title">
          수정할 닉네임을 입력하세요
        </h3>

        <div class="modal__input-field">
          <input
            v-model="newNickname"
            @input="handleNicknameInput"
            @beforeinput="preventNicknameLengthExceed"
            @compositionstart="onNicknameCompositionStart"
            @compositionupdate="onNicknameCompositionUpdate"
            @compositionend="onNicknameCompositionEnd"
            @keypress="preventInvalidNicknameChars"
            type="text"
            placeholder="예: 주차하는알파카"
            class="modal__input"
            maxlength="18"
          />
        </div>

        <div
          v-if="newNickname && !isNicknameValid"
          class="error-message"
        >
          닉네임은 한글, 영문, 숫자만 사용 가능 (2-18자)
        </div>

        <button
          class="modal__button"
          @click="updateNickname"
          :disabled="!isNicknameValid"
        >
          설정 완료
        </button>
      </div>
    </div>

    <!-- 전화번호 변경 모달 -->
    <div
      v-if="showPhoneModal"
      class="modal-overlay"
      @click="closePhoneModal"
    >
      <div
        class="modal modal--phone"
        @click.stop
      >
        <h3 class="modal__title">
          새 전화번호 입력
        </h3>

        <form
          autocomplete="off"
          @submit.prevent
        >
          <!-- 브라우저 자동완성 방해용 더미 -->
          <input type="text" style="display:none" />
          <input type="password" style="display:none" />
          <input type="email" style="display:none" />

          <div class="modal__input-field">
            <input
              :id="'phone-' + uniqueId"
              v-model="phoneDisplay"
              @input="handlePhoneInput"
              @keypress="preventInvalidPhoneChars"
              @focus="onPhoneFocus"
              type="text"
              :placeholder="phonePlaceholder"
              class="modal__input"
              maxlength="13"
              autocomplete="off"
              autocorrect="off"
              autocapitalize="off"
              spellcheck="false"
              :name="'phone-field-' + uniqueId"
              inputmode="numeric"
              data-form-type="other"
              data-lpignore="true"
              readonly
              onfocus="this.removeAttribute('readonly');"
            />
          </div>
        </form>

        <div
          v-if="newPhoneNumber && !isPhoneValid"
          class="error-message"
        >
          올바른 전화번호 형식으로 입력해주세요 (숫자 11자리)
        </div>

        <button
          class="modal__button"
          @click="requestPhoneChange"
        >
          변경하기
        </button>
      </div>
    </div>

    <!-- 비밀번호 변경 모달 -->
    <div
      v-if="showPasswordModal"
      class="modal-overlay"
      @click="showPasswordModal = false"
    >
      <div
        class="modal modal--password"
        @click.stop
      >
        <h3 class="modal__title">
          비밀번호 변경
        </h3>

        <div class="section-subtitle">
          현재 비밀번호 입력
        </div>
        <div class="modal__input-field">
          <input
            v-model="currentPassword"
            type="password"
            placeholder="현재 비밀번호를 입력하세요"
            class="modal__input"
            maxlength="20"
          />
        </div>

        <div class="section-subtitle">
          새 비밀번호 입력
        </div>
        <div class="modal__input-field">
          <input
            v-model="newPassword"
            type="password"
            placeholder="새 비밀번호를 입력하세요"
            class="modal__input"
            maxlength="20"
          />
        </div>

        <ul
          v-if="newPassword && !isPasswordValid"
          class="password-rules"
        >
          <li :class="passwordLengthValid ? 'valid' : 'invalid'">8~20자</li>
          <li :class="passwordLetterValid ? 'valid' : 'invalid'">문자 포함</li>
          <li :class="passwordNumberValid ? 'valid' : 'invalid'">숫자 포함</li>
          <li :class="passwordSpecialValid ? 'valid' : 'invalid'">특수문자 포함</li>
          <li :class="passwordNoTripleValid ? 'valid' : 'invalid'">동일문자 3연속 불가</li>
          <li :class="passwordNoSeqValid ? 'valid' : 'invalid'">연속문자 3연속 불가</li>
        </ul>

        <div class="section-subtitle">
          새 비밀번호 확인
        </div>
        <div class="modal__input-field">
          <input
            v-model="confirmPassword"
            type="password"
            placeholder="새 비밀번호를 다시 입력하세요"
            class="modal__input"
            maxlength="20"
          />
        </div>

        <div
          v-if="confirmPassword && !isPasswordConfirmValid"
          class="error-message"
        >
          비밀번호가 일치하지 않습니다
        </div>

        <button
          class="modal__button"
          @click="requestPasswordChange"
        >
          변경하기
        </button>
      </div>
    </div>

    <!-- 이메일 인증(전화/비번 공용) -->
    <div
      v-if="showEmailVerificationModal"
      class="modal-overlay"
      @click="showEmailVerificationModal = false"
    >
      <div
        class="modal modal--email-verify"
        @click.stop
      >
        <h3 class="modal__title">
          {{ verificationTarget === 'phone' ? '전화번호 변경' : '비밀번호 변경' }} 인증
        </h3>

        <div class="email-info">
          <span>{{ userInfo?.email }}로 인증번호를 발송합니다.</span>
        </div>

        <div class="verification-step">
          <button
            class="modal__button"
            @click="sendEmailVerification"
            :disabled="emailSent"
          >
            {{ emailSent ? '인증번호 발송됨' : '인증번호 발송' }}
          </button>
        </div>

        <div
          v-if="emailSent"
          class="verification-input"
        >
          <div class="modal__input-field">
            <input
              v-model="verificationCode"
              type="text"
              placeholder="인증번호를 입력하세요"
              class="modal__input"
              maxlength="6"
            />
          </div>

          <button
            class="modal__button"
            @click="verifyEmailCode"
            :disabled="!verificationCode || emailVerified"
          >
            {{ emailVerified ? '인증완료' : '인증확인' }}
          </button>
        </div>

        <div
          v-if="emailVerified"
          class="verification-complete"
        >
          <button
            class="modal__button modal__button--success"
            @click="verificationTarget === 'phone' ? executePhoneChange() : confirmPasswordChange()"
          >
            {{ verificationTarget === 'phone' ? '전화번호 변경' : '비밀번호 변경' }} 완료
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import Header from "@/components/Header.vue";
import BottomNavigation from "@/components/BottomNavigation.vue";
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";
import { BACKEND_BASE_URL } from "@/utils/api";
import {
  subscribeToPushNotifications,
  unsubscribeFromPushNotifications,
  getSubscriptionStatus,
  showLocalNotification
} from "@/utils/pwa";

/* ====== 스토어 ====== */
const router = useRouter();
const userStore = useUserStore();
const userInfo = computed(() => userStore.me);

// 소셜 로그인 유저 여부 확인
const isSocialUser = computed(() => {
	// 백엔드에서 제공하는 is_social_user 필드 사용
	return userInfo.value?.is_social_user || false;
});

/* ====== 행(꺾쇠) 클릭 핸들러 ====== */
const openNicknameModal = () => {
  showNicknameModal.value = true;
};
const openPhoneModal = () => {
  showPhoneModal.value = true;
  // 입력창 자동완성 방지용 readonly 제거 타이밍 보정
  setTimeout(() => {
    const el = document.querySelector(`#phone-${uniqueId.value}`) as HTMLInputElement | null;
    if (el) el.removeAttribute("readonly");
  }, 100);
};
const closePhoneModal = () => {
  showPhoneModal.value = false;
};
const openPasswordModal = () => {
  showPasswordModal.value = true;
};

/* ====== 닉네임 ====== */
const showNicknameModal = ref(false);
const newNickname = ref("");
const isNicknameComposing = ref(false);
const isNicknameValid = computed(() => {
  const noSpecialChars = /^[a-zA-Z가-힣0-9]+$/.test(newNickname.value);
  const lengthValid = newNickname.value.length >= 2 && newNickname.value.length <= 18;
  return noSpecialChars && lengthValid;
});

const onNicknameCompositionStart = () => { isNicknameComposing.value = true; };
const onNicknameCompositionUpdate = (e: CompositionEvent) => {
  const input = e.target as HTMLInputElement;
  if (input.value.length > 18) {
    const truncated = input.value.slice(0, 18);
    input.value = truncated;
    newNickname.value = truncated;
  }
};
const onNicknameCompositionEnd = (e: Event) => {
  isNicknameComposing.value = false;
  const input = e.target as HTMLInputElement;
  const cleaned = input.value.replace(/[^a-zA-Z가-힣0-9]/g, "").slice(0, 18);
  if (input.value !== cleaned) {
    newNickname.value = cleaned;
    setTimeout(() => { input.value = cleaned; }, 0);
  }
};
const handleNicknameInput = (e: Event) => {
  const input = e.target as HTMLInputElement;
  if (input.value.length > 18) {
    const truncated = input.value.slice(0, 18);
    newNickname.value = truncated;
    input.value = truncated;
    return;
  }
  if (isNicknameComposing.value) return;
  const cleaned = input.value.replace(/[^a-zA-Z가-힣0-9]/g, "").slice(0, 18);
  if (input.value !== cleaned) {
    newNickname.value = cleaned;
    setTimeout(() => { if (input.value !== cleaned) input.value = cleaned; }, 0);
  }
};
const preventNicknameLengthExceed = (e: Event) => {
  const input = e.target as HTMLInputElement;
  const ev = e as InputEvent;
  const len = input.value.length;
  if (ev.inputType && (ev.inputType.includes("insert") || ev.inputType.includes("replace") || ev.inputType === "insertText" || ev.inputType === "insertCompositionText")) {
    if (len >= 18) { e.preventDefault(); return; }
    const data = ev.data || "";
    if (len + data.length > 18) { e.preventDefault(); return; }
  }
};
const preventInvalidNicknameChars = (e: KeyboardEvent) => {
  if (isNicknameComposing.value) return;
  const char = e.key;
  const input = e.target as HTMLInputElement;
  if (["Backspace","Delete","ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Tab","Enter","Escape"].includes(char)) return;
  if (e.isComposing || char === "Process") return;
  if (input.value.length >= 18) { e.preventDefault(); return; }
  if (!/[a-zA-Z가-힣0-9]/.test(char)) e.preventDefault();
};

const updateNickname = async () => {
  const nick = newNickname.value.trim();
  if (!nick) return alert("닉네임을 입력해주세요.");
  try {
    await userStore.updateProfile({ nickname: nick }); // 서버 의존(테스트 시 주석 가능)
    alert("닉네임이 변경되었습니다.");
    showNicknameModal.value = false;
    newNickname.value = "";
  } catch (err: any) {
    console.error(err);
    alert("변경 실패: " + err.message);
  }
};

/* ====== 전화번호 ====== */
const phonePlaceholder = ref("ex) 010-1234-5678");
const uniqueId = ref(Date.now());
const phoneDisplay = ref("");
const newPhoneNumber = ref("");
const showPhoneModal = ref(false);

const isPhoneValid = computed(() => /^[0-9]{11}$/.test(newPhoneNumber.value));

const handlePhoneInput = (e: Event) => {
  let digits = (e.target as HTMLInputElement).value.replace(/[^0-9]/g, "");
  if (digits.length > 11) digits = digits.slice(0, 11);
  const p1 = digits.slice(0, 3);
  const p2 = digits.length >= 4 ? digits.slice(3, 7) : "";
  const p3 = digits.length >= 8 ? digits.slice(7) : "";
  phoneDisplay.value = [p1, p2, p3].filter(Boolean).join("-");
  newPhoneNumber.value = digits;
};
const preventInvalidPhoneChars = (e: KeyboardEvent) => {
  const char = e.key;
  if (!/[0-9]/.test(char) && !["Backspace","Delete","ArrowLeft","ArrowRight","Tab"].includes(char)) e.preventDefault();
};
const onPhoneFocus = (e: FocusEvent) => {
  const target = e.target as HTMLInputElement;
  if (target.hasAttribute("readonly")) target.removeAttribute("readonly");
  target.setAttribute("autocomplete","off");
  uniqueId.value = Date.now();
};

const showEmailVerificationModal = ref(false);
const emailSent = ref(false);
const emailVerified = ref(false);
const verificationCode = ref("");
const verificationTarget = ref<'phone' | 'password'>('phone');

const requestPhoneChange = () => {
  if (!newPhoneNumber.value.trim()) {
    alert("새 전화번호를 입력해주세요.");
    return;
  }
  verificationTarget.value = "phone";
  emailSent.value = false;
  emailVerified.value = false;
  verificationCode.value = "";
  showEmailVerificationModal.value = true;
};

const executePhoneChange = async () => {
  if (!emailVerified.value) { alert("이메일 인증을 먼저 완료해주세요."); return; }
  if (!newPhoneNumber.value || !isPhoneValid.value) { alert("올바른 전화번호를 입력해주세요."); return; }

  try {
    const response = await fetch(`${BACKEND_BASE_URL}/users/me/`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json"
        // "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({
        phone: newPhoneNumber.value,
        nickname: userInfo.value?.nickname,
        name: userInfo.value?.name
      })
    });

    if (response.ok) {
      alert("전화번호가 성공적으로 변경되었습니다. (테스트)");
      showEmailVerificationModal.value = false;
      showPhoneModal.value = false;
      newPhoneNumber.value = "";
      phoneDisplay.value = "";
      emailSent.value = false;
      emailVerified.value = false;
      verificationCode.value = "";
      // await userStore.fetchMe(token!)
    } else {
      const errorData = await response.json();
      alert("전화번호 변경 실패: " + (errorData.detail || errorData.message || "서버 오류"));
    }
  } catch (e) {
    console.error(e);
    alert("전화번호 변경 중 오류가 발생했습니다. (테스트 모드)");
  }
};

/* ====== 비밀번호 ====== */
const showPasswordModal = ref(false);
const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");

const passwordLengthValid = computed(() => newPassword.value.length >= 8 && newPassword.value.length <= 20);
const passwordLetterValid = computed(() => /[a-zA-Z]/.test(newPassword.value));
const passwordNumberValid = computed(() => /\d/.test(newPassword.value));
const passwordSpecialValid = computed(() => /[$@!%*#?&/]/.test(newPassword.value));
const passwordNoTripleValid = computed(() => !/(\w)\1\1/.test(newPassword.value));
const passwordNoSeqValid = computed(() => {
  for (let i = 0; i < newPassword.value.length - 2; i++) {
    const a = newPassword.value.charCodeAt(i);
    const b = newPassword.value.charCodeAt(i + 1);
    const c = newPassword.value.charCodeAt(i + 2);
    if ((b === a + 1 && c === b + 1) || (b === a - 1 && c === b - 1)) return false;
  }
  return true;
});
const isPasswordValid = computed(() =>
  [passwordLengthValid, passwordLetterValid, passwordNumberValid, passwordSpecialValid, passwordNoTripleValid, passwordNoSeqValid].every(v => v.value)
);
const isPasswordConfirmValid = computed(() => confirmPassword.value === newPassword.value && confirmPassword.value.length > 0);

const showPasswordConfirmModal = ref(false);

const requestPasswordChange = () => {
  verificationTarget.value = "password";
  emailSent.value = false;
  emailVerified.value = false;
  verificationCode.value = "";
  showEmailVerificationModal.value = true;
};

const confirmPasswordChange = async () => {
  if (!emailVerified.value) { alert("이메일 인증을 먼저 완료해주세요."); return; }
  if (!currentPassword.value || !newPassword.value || !confirmPassword.value) {
    return alert("모든 비밀번호 필드를 입력해주세요.");
  }
  if (newPassword.value !== confirmPassword.value) {
    return alert("새 비밀번호가 일치하지 않습니다.");
  }

  try {
    await userStore.changePassword(currentPassword.value, newPassword.value); // 서버 의존(테스트 시 주석 가능)
    alert("비밀번호가 성공적으로 변경되었습니다. (테스트)");
    showEmailVerificationModal.value = false;
    showPasswordModal.value = false;
  } catch (e: any) {
    console.error(e);
    alert("변경 실패: " + e.message);
  } finally {
    showPasswordConfirmModal.value = false;
    currentPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";
  }
};

/* ====== 이메일 인증 공통 ====== */
const sendEmailVerification = async () => {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/auth/email-verify/request/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
        // "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ email: userInfo.value?.email })
    });
    if (response.ok) {
      emailSent.value = true;
      alert("인증번호를 발송했습니다. (테스트)");
    } else {
      alert("인증번호 발송 실패");
    }
  } catch {
    alert("인증번호 발송 실패 (테스트 모드)");
  }
};

const verifyEmailCode = async () => {
  try {
    const response = await fetch(`${BACKEND_BASE_URL}/auth/email-verify/verify/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: userInfo.value?.email, code: verificationCode.value })
    });
    if (response.ok) {
      emailVerified.value = true;
      alert("이메일 인증이 완료되었습니다. (테스트)");
    } else {
      const error = await response.json();
      alert(error.detail || "인증 실패");
    }
  } catch {
    alert("인증 실패 (테스트 모드)");
  }
};

/* ====== 알림(PWA) ====== */
const isNotificationEnabled = ref(false);
const canInstallPWA = ref(false);
let deferredPrompt: any = null;

const toggleNotifications = async () => {
  try {
    if (isNotificationEnabled.value) {
      await unsubscribeFromPushNotifications();
      isNotificationEnabled.value = false;
      alert("푸시 알림이 해제되었습니다.");
    } else {
      if (!("Notification" in window)) { alert("이 브라우저는 알림을 지원하지 않습니다."); return; }
      if (!("serviceWorker" in navigator)) { alert("이 브라우저는 푸시 알림을 지원하지 않습니다."); return; }
      let permission = Notification.permission;
      if (permission === "default") permission = await Notification.requestPermission();
      if (permission !== "granted") { alert("알림 권한이 필요합니다. 브라우저 설정에서 알림을 허용해주세요."); return; }
      const subscription = await subscribeToPushNotifications();
      if (subscription) {
        isNotificationEnabled.value = true;
        alert("푸시 알림이 활성화되었습니다.");
        setTimeout(() => {
          showLocalNotification({ type: "general", title: "🎉 알림 설정 완료", body: "이제 주차 알림을 받을 수 있습니다!" });
        }, 1000);
      }
    }
  } catch (e) {
    console.error(e);
    alert("알림 설정 변경 중 오류가 발생했습니다.");
  }
};

const installPWA = async () => {
  if (deferredPrompt) {
    try {
      deferredPrompt.prompt();
      const choiceResult = await deferredPrompt.userChoice;
      if (choiceResult.outcome === "accepted") { canInstallPWA.value = false; }
      deferredPrompt = null;
    } catch (e) {
      console.error(e);
      alert("PWA 설치 중 오류가 발생했습니다.");
    }
  } else if (window.matchMedia("(display-mode: standalone)").matches) {
    alert("이미 PWA로 설치되어 실행 중입니다.");
  } else {
    const ua = navigator.userAgent.toLowerCase();
    if (ua.includes("android")) alert('Chrome 메뉴 → "홈 화면에 추가"를 선택하세요.');
    else if (ua.includes("iphone") || ua.includes("ipad")) alert('Safari 공유 버튼 → "홈 화면에 추가"를 선택하세요.');
    else alert('브라우저 메뉴에서 "앱 설치" 또는 "홈 화면에 추가"를 선택하세요.');
  }
};

const checkNotificationStatus = async () => {
  try {
    const hasPermission = Notification.permission === "granted";
    const subscription = await getSubscriptionStatus();
    isNotificationEnabled.value = hasPermission && !!subscription;
    const isStandalone = window.matchMedia("(display-mode: standalone)").matches;
    const isInWebAppiOS = (window.navigator as any).standalone === true;
    const isInstalled = isStandalone || isInWebAppiOS;
    canInstallPWA.value = !isInstalled && (!!deferredPrompt || "serviceWorker" in navigator);
  } catch (e) {
    console.error(e);
  }
};

const setupPWAListeners = () => {
  window.addEventListener("beforeinstallprompt", (e) => {
    (e as Event).preventDefault?.();
    deferredPrompt = e;
    canInstallPWA.value = true;
  });
  window.addEventListener("appinstalled", () => {
    canInstallPWA.value = false;
    deferredPrompt = null;
  });
};

/* ====== 보안 검증 ====== */
const checkAuthenticationStatus = () => {
	// 1. 소셜 로그인 유저인 경우 접근 차단
	if (isSocialUser.value) {
		alert('소셜 로그인 사용자는 이 페이지에 접근할 수 없습니다.');
		router.push('/user-profile');
		return false;
	}
	
	// 2. 일회용 토큰이 여전히 남아있다면 삭제
	// Router Guard에서 이미 삭제했지만, 혹시 모를 경우를 대비
	const remainingToken = sessionStorage.getItem('user-setting-one-time-auth');
	if (remainingToken) {
		sessionStorage.removeItem('user-setting-one-time-auth');
		console.log('[UserSetting] 남은 일회용 토큰 삭제');
	}
	
	// 3. 이 페이지는 Router Guard를 통과했으므로 정상 접근으로 간주
	console.log('[UserSetting] 정상적인 인증 절차를 통한 접근');
	return true;
};

/* ====== 마운트(테스트용) ====== */
onMounted(async () => {
  // 페이지 접근 시 보안 검증 수행
  if (!checkAuthenticationStatus()) {
  	return; // 검증 실패 시 라우터에서 리다이렉트됨
  }
  
  // 페이지 이탈 시 남은 토큰 정리
  const cleanupTokens = () => {
  	sessionStorage.removeItem('user-setting-one-time-auth');
  	console.log('[UserSetting] 페이지 이탈 시 토큰 정리');
  };
  
  // 브라우저 이벤트 리스너 등록
  window.addEventListener('beforeunload', cleanupTokens);
  window.addEventListener('pagehide', cleanupTokens);
  
  // const token = localStorage.getItem("access_token");
  // if (token) {
  //   await userStore.fetchMe(token);
  // }
  setupPWAListeners();
  await checkNotificationStatus();
  
  // 컴포넌트 언마운트 시 정리
  return () => {
  	window.removeEventListener('beforeunload', cleanupTokens);
  	window.removeEventListener('pagehide', cleanupTokens);
  	cleanupTokens();
  };
});

/* ====== 유틸 ====== */
const formatPhoneNumber = (phone: string | undefined | null) => {
  if (!phone) return null;
  const digits = phone.replace(/\D/g, "");
  if (digits.length !== 11) return phone;
  return digits.replace(/(\d{3})(\d{4})(\d{4})/, "$1-$2-$3");
};
</script>

<style scoped>
/* ── 전체 레이아웃 ── */
.user-setting {
  width: 440px;
  height: 956px;
  position: relative;
  background: #f3edea;
  overflow: hidden;
  margin: 0 auto;
}

.user-setting__content {
  position: relative;
  padding-top: 80px;
  height: calc(100% - 160px);
  overflow-y: auto;
  padding-left: 20px;
  padding-right: 20px;
}

/* ── 프로필 카드(행 리스트) ── */
.profile-card {
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(119, 107, 93, 0.1);
}

.setting-row {
  width: 100%;
  display: flex;
  align-items: center;
  padding: 16px 16px;
  background: transparent;
  border: none;
  cursor: pointer;
  text-align: left;
}

.setting-row:hover {
  background: rgba(119, 107, 93, 0.04);
}

.setting-row__text {
  flex: 1 1 auto;
  min-width: 0;
}

.setting-row__label {
  font-size: 18px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 4px;
}

.setting-row__value {
  font-size: 15px;
  color: #7a7a7a;
  word-break: break-all;
}

.setting-row__value--placeholder {
  color: #9a9a9a;
}

.chevron {
  flex: 0 0 24px;
  width: 24px;
  height: 24px;
  color: #8a837a;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.chevron svg {
  width: 20px;
  height: 20px;
}

.divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.08);
  margin-left: 16px;
  margin-right: 16px;
}

/* ── 알림 카드 ── */
.section-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 10px;
}

.notification-settings {
  background: #ffffff;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(119, 107, 93, 0.1);
}

.notification-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0;
  border-bottom: 1px solid rgba(119, 107, 93, 0.1);
}

.notification-item:last-child {
  border-bottom: none;
}

.notification-item__content {
  flex: 1;
}

.notification-item__label {
  font-size: 16px;
  font-weight: 600;
  color: #333333;
  margin-bottom: 4px;
}

.notification-item__desc {
  font-size: 14px;
  color: #776b5d;
}

.notification-item__toggle {
  margin-left: 16px;
}

.toggle-button {
  padding: 8px 16px;
  border: 2px solid #776b5d;
  border-radius: 20px;
  background: #ffffff;
  color: #776b5d;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 60px;
}

.toggle-button:hover {
  background: rgba(119, 107, 93, 0.1);
}

.toggle-button--active {
  background: #776b5d;
  color: #ffffff;
}

.install-button {
  padding: 8px 16px;
  border: 2px solid #4caf50;
  border-radius: 20px;
  background: #ffffff;
  color: #4caf50;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 60px;
}

.install-button:hover:not(:disabled) {
  background: rgba(76, 175, 80, 0.1);
}

.install-button:disabled {
  border-color: #cccccc;
  color: #cccccc;
  cursor: not-allowed;
}

.test-button {
  padding: 8px 16px;
  border: 2px solid #2196f3;
  border-radius: 20px;
  background: #ffffff;
  color: #2196f3;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  min-width: 60px;
}

.test-button:hover {
  background: rgba(33, 150, 243, 0.1);
}

/* ── 모달 공통 ── */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #f3eeea;
  width: 90%;
  max-width: 360px;
  padding: 27px 24px 32px;
  border-radius: 10px;
}

.modal__title {
  font-size: 18px;
  font-weight: 600;
  text-align: center;
  margin-bottom: 20px;
}

.modal__input-field {
  width: 100%;
  background: #ffffff;
  border: 1px solid #ccc;
  margin-bottom: 16px;
  padding: 10px 12px;
  box-sizing: border-box;
  border-radius: 8px;
}

.modal__input {
  width: 100%;
  border: none;
  outline: none;
  font-size: 16px;
  padding: 0;
  box-sizing: border-box;
  background: transparent;
}

.modal__button {
  width: 100%;
  height: 48px;
  background: #776b5d;
  color: #ffffff;
  border: none;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
}

.modal__button--success {
  background: #4caf50;
}


/* 비밀번호 유효성 안내 */
.password-rules {
  list-style: none;
  padding: 0;
  margin: 5px 0 15px 0;
  font-size: 12px;
}

.password-rules li {
  padding: 2px 0;
  color: #999999;
}

.password-rules li.valid {
  color: #4caf50;
}

.password-rules li.valid::before {
  content: "✓ ";
}

.password-rules li.invalid {
  color: #f44336;
}

.password-rules li.invalid::before {
  content: "✗ ";
}

/* 메시지 */
.error-message {
  color: #f44336;
  font-size: 14px;
  margin-bottom: 12px;
}

.email-info {
  text-align: center;
  margin-bottom: 16px;
  font-size: 14px;
  color: #666666;
}

.verification-step {
  margin-bottom: 16px;
}

.verification-input {
  margin-bottom: 16px;
}

.verification-complete {
  margin-top: 10px;
}

/* Responsive */
@media (max-width: 440px) {
  .user-setting {
    width: 100vw;
    height: 100vh;
  }

  .user-setting__content {
    padding-left: 15px;
    padding-right: 15px;
  }

  .setting-row__label {
    font-size: 17px;
  }

  .setting-row__value {
    font-size: 14px;
  }
}

@media (min-width: 441px) {
  .user-setting {
    width: 440px;
    height: auto;
    min-height: 100vh;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
  }

  .user-setting__content {
    flex: 1;
    height: auto;
    min-height: calc(100vh - 160px);
    padding-bottom: 20px;
  }
}
</style>
