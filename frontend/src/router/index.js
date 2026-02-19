import { createRouter, createWebHistory } from "vue-router";
import LandingView from "../views/LandingView.vue";
import LoginView from "../views/LoginView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", name: "landing", component: LandingView },
    {path: "/login", name: "login", component: () => import("../views/LoginView.vue"),},
    {path: "/registro", name: "registro", component: () => import("../views/RegistroView.vue"),},
    {path: "/proyecto/:id_proyecto/cargar", name: "cargaDeDocumentos", component: () => import("../views/CargaDeDocumentosView.vue"),},
    {path: "/misProyectos", name: "misProyectos", component: () => import("../views/MisProyectosView.vue"),},



  ],
});

export default router;
