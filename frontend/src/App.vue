<script setup>
import ConfirmModal from "@/components/app/ConfirmModal.vue";
import AppToast from "@/components/app/AppToast.vue";
</script>

<template>
  <router-view />
  <ConfirmModal />
  <AppToast />
</template>


<style scoped></style>
