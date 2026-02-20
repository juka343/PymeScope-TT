// Re-exporta desde config.js para evitar duplicación de inicialización
import { auth, db, storage } from "@/firebase/config";

export { auth, db, storage };
