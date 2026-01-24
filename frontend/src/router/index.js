import { createRouter, createWebHistory } from 'vue-router'
import HomeView from "../views/HomeView.vue"
import DashboardView from "../views/DashboardView.vue"
import FamilyView from "../views/FamilyView.vue";
import AdminView from "../views/AdminView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
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
      component: FamilyView
    },
    {
      path: "/admin",
      name: "admin",
      component: AdminView
    }
  ],
})

export default router
