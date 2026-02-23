import { createRouter, createWebHistory } from "vue-router";
import LandingView from "../views/LandingView.vue";
import DashboardLayout from "@/layouts/DashboardLayout.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", name: "landing", component: LandingView },

    { path: "/login", name: "login", component: () => import("../views/LoginView.vue") },
    { path: "/registro", name: "registro", component: () => import("../views/RegistroView.vue") },

    {
      path: "/proyecto/:id_proyecto/cargar",
      name: "cargaDeDocumentos",
      component: () => import("../views/CargaDeDocumentosView.vue"),
    },

    { path: "/misProyectos", name: "misProyectos", component: () => import("../views/MisProyectosView.vue") },

    // RUTAS CON LAYOUT
    // RUTAS CON LAYOUT
    {
      path: "/proyecto/:id_proyecto/dashboard", 
      component: DashboardLayout,
      children: [
        {
          path: "rentabilidad",
          name: "rentabilidad",
          component: () => import("../views/RentabilidadView.vue"),
        },
        {
          path: "liquidez",
          name: "liquidez",
          component: () => import("../views/LiquidezView.vue"),
        },
      ],
    },
  ],
});

export default router;
