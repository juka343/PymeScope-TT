<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { auth, storage, db } from "@/firebase/config";
import { updateProfile, deleteUser } from "firebase/auth";
import { ref as storageRef, uploadBytes, getDownloadURL } from "firebase/storage";
import { collection, query, where, getDocs, deleteDoc, doc } from "firebase/firestore";
import { useToast } from "@/composables/useToast";
import { useConfirm } from "@/composables/useConfirm";
import { useRouter } from "vue-router";

const props = defineProps({
  isOpen: Boolean
});

const emit = defineEmits(["close", "profile-updated"]);

const { toast } = useToast();
const { confirm } = useConfirm();
const router = useRouter();

const user = computed(() => auth.currentUser);

const displayName = ref("");
const previewUrl = ref("");
const selectedFile = ref(null);
const isSaving = ref(false);
const isDeleting = ref(false);

const userInitials = computed(() => {
  const name = displayName.value?.trim() || user.value?.displayName?.trim();
  if (!name) return "U";
  if (name.includes("@")) return name[0].toUpperCase();
  const parts = name.split(" ").filter(Boolean);
  const initials = parts.slice(0, 2).map((p) => p[0]).join("");
  return (initials || name[0]).toUpperCase();
});

watch(() => props.isOpen, (newVal) => {
  if (newVal && user.value) {
    displayName.value = user.value.displayName || "";
    previewUrl.value = user.value.photoURL || "";
    selectedFile.value = null;
  }
});

function handleFileSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  // Basic validation
  if (!file.type.startsWith("image/")) {
    toast({ message: "Por favor selecciona un archivo de imagen válido.", type: "warning" });
    return;
  }
  if (file.size > 2 * 1024 * 1024) {
    toast({ message: "La imagen es muy grande. El tamaño máximo es 2MB.", type: "warning" });
    return;
  }

  selectedFile.value = file;
  previewUrl.value = URL.createObjectURL(file);
}

function triggerFileInput() {
  document.getElementById("profile-image-input").click();
}

async function handleSave() {
  if (!user.value) return;

  isSaving.value = true;
  let newPhotoURL = user.value.photoURL;

  try {
    if (selectedFile.value) {
      // Upload image to Firebase Storage
      const fileRef = storageRef(storage, `uploads/${user.value.uid}/profile_picture_${Date.now()}`);
      await uploadBytes(fileRef, selectedFile.value);
      newPhotoURL = await getDownloadURL(fileRef);
    }

    await updateProfile(user.value, {
      displayName: displayName.value.trim(),
      photoURL: newPhotoURL,
    });

    toast({ message: "Perfil actualizado correctamente.", type: "success" });
    
    emit("profile-updated", { displayName: displayName.value.trim(), photoURL: newPhotoURL });
    closeModal();
  } catch (error) {
    console.error("Error updating profile:", error);
    
    // Check for specific Firebase errors
    if (error.code === 'storage/unauthorized') {
      toast({ 
        message: "Error de permisos en Firebase. Asegúrate de que las reglas de Storage permitan escritura.", 
        type: "error" 
      });
    } else {
      toast({ message: `Error al actualizar: ${error.message || "desconocido"}`, type: "error" });
    }
  } finally {
    isSaving.value = false;
  }
}

function closeModal() {
  if (isDeleting.value) return;

  // Reset fields if cancelled without saving
  if (!isSaving.value) {
    displayName.value = user.value?.displayName || "";
    previewUrl.value = user.value?.photoURL || "";
    selectedFile.value = null;
  }
  emit("close");
}

async function handleDeleteAccount() {
  const confirmed = await confirm({
    title: "Eliminar cuenta",
    message: "¿Estás seguro que deseas borrar tu cuenta? Esta acción no se puede deshacer.",
    confirmText: "Sí, borrar cuenta",
    cancelText: "Cancelar",
    variant: "danger",
  });
  
  if (!confirmed) return;
  if (!user.value) return;
  
  isDeleting.value = true;
  try {
    const uid = user.value.uid;
    
    // Eliminar documentos/proyectos (prototipo)
    const q = query(collection(db, "proyectos"), where("userId", "==", uid));
    const snapshot = await getDocs(q);
    
    const deletePromises = [];
    snapshot.forEach((docSnap) => {
      deletePromises.push(deleteDoc(docSnap.ref));
    });
    
    deletePromises.push(deleteDoc(doc(db, "user_onboarding", uid)));
    await Promise.all(deletePromises);
    
    // Borrar cuenta
    await deleteUser(user.value);
    
    toast({ message: "Tu cuenta ha sido eliminada.", type: "info" });
    closeModal();
    router.push("/");
  } catch (error) {
    console.error("Error eliminando cuenta:", error);
    if (error.code === 'auth/requires-recent-login') {
      toast({ message: "Por seguridad, cierra sesión y vuelve a entrar antes de borrar tu cuenta.", type: "warning" });
    } else {
      toast({ message: "No se pudo eliminar la cuenta.", type: "error" });
    }
  } finally {
    isDeleting.value = false;
  }
}
</script>

<template>
  <div v-if="isOpen" class="modal-root" role="dialog" aria-modal="true">
    <div class="overlay" @click="closeModal"></div>
    
    <div class="modal-wrap">
      <div class="modal">
        <button class="modal-close" type="button" @click="closeModal" aria-label="Cerrar">
          <span class="material-symbols-outlined">close</span>
        </button>

        <div class="modal-head">
          <div class="modal-icon">
            <span class="material-symbols-outlined">person</span>
          </div>
          <div>
            <h3 id="modal-title">Mi Perfil</h3>
            <p>Actualiza tu nombre y foto de perfil.</p>
          </div>
        </div>

        <div class="form">
          <!-- Profile Picture Section -->
          <div class="profile-pic-section">
            <div class="avatar-preview" :style="previewUrl ? { backgroundImage: `url('${previewUrl}')` } : {}">
              <span v-if="!previewUrl">{{ userInitials }}</span>
              <button type="button" class="edit-pic-btn" @click="triggerFileInput" title="Cambiar foto">
                <span class="material-symbols-outlined">photo_camera</span>
              </button>
            </div>
            
            <input 
              type="file" 
              id="profile-image-input" 
              accept="image/*" 
              class="hidden" 
              @change="handleFileSelect"
            />
            
            <div class="pic-info">
              <button type="button" class="btn-text" @click="triggerFileInput">Subir nueva foto</button>
              <small>Recomendado: 256x256px. Máximo 2MB.</small>
            </div>
          </div>

          <!-- Name Section -->
          <div class="field">
            <label for="display-name">Nombre de usuario</label>
            <input
              id="display-name"
              v-model="displayName"
              type="text"
              placeholder="Tu nombre completo"
            />
          </div>

          <!-- Danger Zone -->
          <div class="danger-zone">
            <h4>Zona de peligro</h4>
            <div class="danger-content">
              <div class="danger-text">
                <strong>Eliminar cuenta</strong>
                <p>Se borrarán tus proyectos y no podrás recuperar el acceso.</p>
              </div>
              <button 
                class="btn-danger" 
                type="button" 
                @click="handleDeleteAccount" 
                :disabled="isDeleting"
              >
                {{ isDeleting ? "Borrando..." : "Borrar cuenta" }}
              </button>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button
            class="btn-primary"
            type="button"
            @click="handleSave"
            :disabled="isSaving"
          >
            {{ isSaving ? "Guardando..." : "Guardar cambios" }}
          </button>
          <button class="btn-secondary" type="button" @click="closeModal" :disabled="isSaving">
            Cancelar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-pic-section {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.avatar-preview {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 999px;
  background: rgba(41, 157, 224, 0.1);
  color: #299de0;
  display: grid;
  place-items: center;
  font-weight: 900;
  font-size: 28px;
  background-size: cover;
  background-position: center;
  flex-shrink: 0;
}

.edit-pic-btn {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: #299de0;
  color: white;
  border: 2px solid white;
  display: grid;
  place-items: center;
  cursor: pointer;
  padding: 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: transform 0.2s;
}

.edit-pic-btn:hover {
  transform: scale(1.1);
}

.edit-pic-btn .material-symbols-outlined {
  font-size: 16px;
}

.hidden {
  display: none;
}

.pic-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.btn-text {
  background: none;
  border: none;
  color: #299de0;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  padding: 0;
  text-align: left;
}

.btn-text:hover {
  text-decoration: underline;
}

/* Base Modal Styles */
.modal-root {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.overlay {
  position: absolute;
  inset: 0;
  background: rgba(14, 22, 27, 0.4);
  backdrop-filter: blur(2px);
}

.modal-wrap {
  position: relative;
  width: 100%;
  max-width: 440px;
  padding: 20px;
}

.modal {
  background: #fff;
  border-radius: 20px;
  padding: 32px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
}

.modal-close {
  position: absolute;
  top: 24px;
  right: 24px;
  width: 32px;
  height: 32px;
  border-radius: 999px;
  border: none;
  background: #f8fafb;
  color: #507c95;
  cursor: pointer;
  display: grid;
  place-items: center;
}

.modal-close:hover {
  background: #e8eff3;
  color: #0e161b;
}

.modal-head {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 28px;
}

.modal-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(41, 157, 224, 0.1);
  color: #299de0;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.modal-icon .material-symbols-outlined {
  font-size: 24px;
}

.modal-head h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #0e161b;
}

.modal-head p {
  margin: 4px 0 0;
  font-size: 14px;
  color: #507c95;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 32px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 13px;
  font-weight: 700;
  color: #0e161b;
}

.field input {
  height: 44px;
  padding: 0 14px;
  border: 1px solid #d1dee6;
  border-radius: 10px;
  background: #f8fafb;
  font-family: inherit;
  font-size: 14px;
  color: #0e161b;
  outline: none;
  transition: all 0.2s;
}

.field input:focus {
  border-color: #299de0;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(41, 157, 224, 0.1);
}

.field small {
  font-size: 12px;
  color: #507c95;
}

.modal-actions {
  display: flex;
  gap: 12px;
}

.btn-primary,
.btn-secondary {
  height: 44px;
  padding: 0 20px;
  border-radius: 10px;
  font-weight: 800;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  flex: 1;
}

.btn-primary {
  background: #299de0;
  color: #fff;
  border: none;
  box-shadow: 0 4px 12px rgba(41, 157, 224, 0.2);
}

.btn-primary:hover:not(:disabled) {
  filter: brightness(0.95);
}

.btn-secondary {
  background: transparent;
  color: #0e161b;
  border: 1px solid #d1dee6;
}

.btn-secondary:hover:not(:disabled) {
  background: #f8fafb;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Danger Zone */
.danger-zone {
  margin-top: 12px;
  padding-top: 24px;
  border-top: 1px solid #fee2e2;
}

.danger-zone h4 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #ef4444;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.danger-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  background: #fef2f2;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid #fecaca;
}

.danger-text strong {
  color: #991b1b;
  font-size: 14px;
  display: block;
  margin-bottom: 4px;
}

.danger-text p {
  margin: 0;
  font-size: 13px;
  color: #b91c1c;
  line-height: 1.4;
}

.btn-danger {
  height: 38px;
  padding: 0 16px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 700;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.2s;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.btn-danger:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .danger-content {
    flex-direction: column;
    align-items: flex-start;
  }
  .btn-danger {
    width: 100%;
  }
}
</style>
