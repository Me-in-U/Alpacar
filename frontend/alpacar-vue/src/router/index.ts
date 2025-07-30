import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import SignupLogin from '../views/SignupLogin.vue'
import Login from '../views/Login.vue'
import Signup from '../views/Signup.vue'
import ForgotPassword from '../views/ForgotPassword.vue'
import SocialLoginInfo from '../views/SocialLoginInfo.vue'
import AdminLogin from '@/views/admin/AdminLogin.vue'
import AdminMain from '@/views/admin/AdminMain.vue'
import AdminParkingLogs from '@/views/admin/AdminParkingLogs.vue'
import AdminParkingReassign from '@/views/admin/AdminParkingReassign.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/signup-login',
      name: 'signup-login',
      component: SignupLogin
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
      path: '/admin-login',
      name: 'admin-login',
      component: AdminLogin
    },
    {
      path: '/admin-main',
      name: 'admin-main',
      component: AdminMain
    },
    {
      path: '/admin-parkinglogs',
      name: 'admin-parkinglogs',
      component: AdminParkingLogs
    },
    {
      path: '/admin-parkingreassign',
      name: 'admin-parkingreassign',
      component: AdminParkingReassign
    },

  ]
})

export default router
