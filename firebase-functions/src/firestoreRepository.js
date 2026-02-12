const { FieldValue } = require("firebase-admin/firestore");

async function updateAnalysisStatus(analysisRef, status) {
  await analysisRef.update({ status, updatedAt: FieldValue.serverTimestamp() });
}

async function saveExtractedData(analysisRef, payload) {
  const ref = analysisRef.collection("extractedData").doc();
  await ref.set({
    ...payload,
    createdAt: FieldValue.serverTimestamp(),
  });
}

async function saveFinancialRatios(analysisRef, ratios) {
  const ref = analysisRef.collection("financialRatios").doc();
  await ref.set({
    ...ratios,
    createdAt: FieldValue.serverTimestamp(),
  });
}

async function saveProjections(analysisRef, scenarios) {
  const ref = analysisRef.collection("projections").doc();
  await ref.set({
    scenarios,
    createdAt: FieldValue.serverTimestamp(),
  });
}

async function saveRecommendations(analysisRef, payload) {
  const ref = analysisRef.collection("recommendations").doc();
  await ref.set({
    ...payload,
    createdAt: FieldValue.serverTimestamp(),
  });
}

async function appendAuditLog(analysisRef, action, metadata = {}) {
  const ref = analysisRef.collection("auditLogs").doc();
  await ref.set({
    action,
    metadata,
    createdAt: FieldValue.serverTimestamp(),
  });
}

module.exports = {
  updateAnalysisStatus,
  saveExtractedData,
  saveFinancialRatios,
  saveProjections,
  saveRecommendations,
  appendAuditLog,
};
