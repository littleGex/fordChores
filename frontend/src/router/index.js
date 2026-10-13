import { createRouter, createWebHistory } from 'vue-router'
import HomeView from "../views/HomeView.vue"
import DashboardView from "../views/DashboardView.vue"
import FamilyView from "../views/FamilyView.vue";
import AdminView from "../views/AdminView.vue";
import LoginView from "../views/LoginView.vue";
import { isLoggedIn, isParent } from "../auth";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/login",
      name: "login",
      component: LoginView,
      meta: { public: true }
    },
    {
      path: "/",
      name: "home",
      component: HomeView
    },
    {
      path: "/dashboard",
      name: "dashboard",
      component: DashboardView
    },
    {
      path: "/family",
      name: "family",
      component: FamilyView,
      meta: { requiresParent: true }
    },
    {
      path: "/admin",
      name: "admin",
      component: AdminView,
      meta: { requiresParent: true }
    }
  ],
})

// Everything except the login screen needs a family login; the family
// and admin pages are for parents
router.beforeEach((to) => {
  if (to.meta.public) {
    return isLoggedIn.value ? '/dashboard' : true
  }
  if (!isLoggedIn.value) {
    return '/login'
  }
  if (to.meta.requiresParent && !isParent.value) {
    return '/dashboard'
  }
  return true
})

export default router
