import { createRouter, createWebHistory } from 'vue-router'
import EntryPage from '../views/user/EntryPage.vue'
import Login from '../views/user/Login.vue'
import Signup from '../views/user/Signup.vue'
import ForgotPassword from '../views/user/ForgotPassword.vue'
import SocialLoginInfo from '../views/user/SocialLoginInfo.vue'
import MainPage from '../views/user/MainPage.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'entry-page',
      component: EntryPage
    },
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/signup',
      name: 'signup',
      component: Signup
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: ForgotPassword
    },
    {
      path: '/social-login-info',
      name: 'social-login-info',
      component: SocialLoginInfo
    },
    {
      path: '/main',
      name: 'main',
      component: MainPage
    }
  ]
})

export default router
