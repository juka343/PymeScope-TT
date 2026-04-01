import { createRouter, createWebHistory } from "vue-router";
import LandingView from "../views/LandingView.vue";

import DashboardLayout from "@/layouts/DashboardLayout.vue";
import DashboardLayoutMulti from "@/layouts/DashboardLayoutMulti.vue"; // <-- crea este archivo

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

    {
      path: "/misProyectos",
      name: "misProyectos",
      component: () => import("../views/MisProyectosView.vue"),
    },

    //PANTALLAS DE TEORIA
        {
          path: "/teoriaRentabilidad",
          name: "teoriaRentabilidad",
          component: () => import("../views/TeoriaRentabilidadView.vue"), 
        },

    // DASHBOARD MONOPERIODO
    {
      path: "/proyecto/:id_proyecto/dashboard",
      component: DashboardLayout,
      children: [
        { path: "", redirect: { name: "resumen" } }, // default

        {
          path: "resumen",
          name: "resumen",
          component: () => import("../views/ResumenGeneralMonoView.vue"),
        },
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
        {
          path: "endeudamiento",
          name: "endeudamiento",
          component: () => import("../views/EndeudamientoView.vue"),
        },
        {
          path: "rotacion",
          name: "rotacion",
          component: () => import("../views/RotacionDeActivosView.vue"),
        },
        {
          path: "estructura",
          name: "estructura",
          component: () => import("../views/EstructuraView.vue"),
        },
        {
          path: "proyecciones",
          name: "proyecciones",
          component: () => import("../views/ProyeccionesView.vue"),
        },
        {
          path: "FormularioEstadoDeResultados",
          name: "FormularioEstadoDeResultados",
          component: () => import("../views/FormularioEstadoDeResultadosView.vue"),
        },
        {
          path: "ProyeccionProformaEdo",
          name: "ProyeccionProformaEdo",
          component: () => import("../views/ProyeccionProformaEdoView.vue"),
        },
        {
          path: "FormularioBalanceGeneral",
          name: "FormularioBalanceGeneral",
          component: () => import("../views/FormularioBalanceGeneralView.vue"),
        },
        {
          path: "ProyeccionProformaBalanceGeneral",
          name: "ProyeccionProformaBalanceGeneral",
          component: () => import("../views/ProyeccionProformaBalanceGeneralView.vue"),
        },
      ],
    },

    // DASHBOARD MULTIPERIODO
    {
      path: "/proyecto/:id_proyecto/dashboard-multi",
      component: DashboardLayoutMulti,
      children: [
        { path: "", redirect: { name: "rentabilidadMulti" } }, // default

        // {
        //   path: "resumen",
        //   name: "resumenMulti",
        //   component: () => import("../views/ResumenGeneralMultiView.vue"),
        // },
        {
          path: "rentabilidad",
          name: "rentabilidadMulti",
          component: () => import("../views/RentabilidadMultiperiodoView.vue"), 
        },
        {
          path: "liquidez",
          name: "liquidezMulti",
          component: () => import("../views/LiquidezMultiperiodoView.vue"), 
        },
        {
          path: "endeudamiento",
          name: "endeudamientoMulti",
          component: () => import("../views/EndeudamientoMultiperiodoView.vue"), 
        },
        {
          path: "rotacion",
          name: "rotacionMulti",
          component: () => import("../views/RotacionDeActivosMultiView.vue"), 
        },
        {
          path: "estructura",
          name: "estructuraMulti",
          component: () => import("../views/EstructuraMultiView.vue"), 
        },
        // {
        //   path: "proyecciones",
        //   name: "proyeccionesMulti",
        //   component: () => import("../views/ProyeccionesMultiView.vue"), 
        // },
      ],
    },

    // fallback opcional
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
});

export default router;