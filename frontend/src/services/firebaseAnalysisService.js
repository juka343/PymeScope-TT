import { auth, db, storage } from "./firebaseClient";
import { ref, uploadBytes } from "firebase/storage";
import { doc, setDoc, serverTimestamp } from "firebase/firestore";

export async function uploadFinancialStatement(
  file,
  companyId,
  period,
  statementType = "general"
) {
  const user = auth.currentUser;
  if (!user) {
    throw new Error("User not authenticated.");
  }

  const analysisId = crypto.randomUUID();
  const statementId = crypto.randomUUID();
  const storagePath = `analyses/${analysisId}/${statementId}/${file.name}`;
  const storageRef = ref(storage, storagePath);

  await uploadBytes(storageRef, file, { contentType: file.type });

  const analysisRef = doc(
    db,
    "users",
    user.uid,
    "companies",
    companyId,
    "analysisSessions",
    analysisId
  );

  await setDoc(analysisRef, {
    ownerId: user.uid,
    companyId,
    period,
    status: "uploaded",
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  });

  const statementRef = doc(analysisRef, "financialStatements", statementId);

  await setDoc(statementRef, {
    analysisId,
    companyId,
    period,
    statementType,
    version: 1,
    storagePath,
    storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
    status: "uploaded",
  });

  return { analysisId, statementId, storagePath };
}
