const { initializeApp } = require("firebase-admin/app");
const { getFirestore, FieldValue } = require("firebase-admin/firestore");
const { getStorage } = require("firebase-admin/storage");
const { onDocumentCreated } = require("firebase-functions/v2/firestore");

const { analyzeDocument } = require("./ocrService");
const { buildFinancialRatios } = require("./financialCalculations");
const { generateProjectionScenarios } = require("./projectionEngine");
const { generateRecommendations } = require("./recommendationService");
const {
  updateAnalysisStatus,
  saveExtractedData,
  saveFinancialRatios,
  saveProjections,
  saveRecommendations,
  appendAuditLog,
} = require("./firestoreRepository");

initializeApp({
  storageBucket: process.env.FIREBASE_STORAGE_BUCKET,
});

const db = getFirestore();
const storage = getStorage();

function mapStatements(fields, period) {
  const incomeStatement = {
    period,
    currency: "MXN",
    ingresos: fields.ingresos || fields.ventas_netas || 0,
    ingresosFijos: fields.ingresos_fijos || 0,
    ingresosVariables: fields.ingresos_variables || 0,
    costos: fields.costos || 0,
    costosFijos: fields.costos_fijos || 0,
    costosVariables: fields.costos_variables || 0,
    costosDirectos: fields.costos_directos || 0,
    costosIndirectos: fields.costos_indirectos || 0,
    gastos: fields.gastos || 0,
    utilidadBruta: fields.utilidad_bruta || 0,
    utilidadOperativa: fields.utilidad_operativa || 0,
    utilidadNeta: fields.utilidad_neta || 0,
  };

  const balanceSheet = {
    period,
    currency: "MXN",
    activos: {
      circulantes: fields.activos_circulantes || fields.activos_totales || 0,
      noCirculantes: fields.activos_no_circulantes || 0,
    },
    pasivos: {
      cortoPlazo: fields.pasivos_corto_plazo || fields.pasivos_totales || 0,
      largoPlazo: fields.pasivos_largo_plazo || 0,
    },
    capitalContable: fields.capital_contable || 0,
  };

  return { incomeStatement, balanceSheet };
}

exports.onFinancialStatementCreated = onDocumentCreated(
  "users/{userId}/companies/{companyId}/analysisSessions/{analysisId}/financialStatements/{statementId}",
  async (event) => {
    const snapshot = event.data;
    if (!snapshot) {
      return;
    }

    const statement = snapshot.data();
    const { userId, companyId, analysisId } = event.params;

    const analysisRef = db
      .collection("users")
      .doc(userId)
      .collection("companies")
      .doc(companyId)
      .collection("analysisSessions")
      .doc(analysisId);

    try {
      await updateAnalysisStatus(analysisRef, "processing");
      await appendAuditLog(analysisRef, "analysis_started", { statementId: snapshot.id });

      const bucketName = statement.storageBucket || process.env.FIREBASE_STORAGE_BUCKET;
      const storagePath = statement.storagePath;
      if (!bucketName || !storagePath) {
        throw new Error("Missing storage bucket or path.");
      }

      const [fileBuffer] = await storage.bucket(bucketName).file(storagePath).download();
      const ocrResult = await analyzeDocument(fileBuffer);

      const period = statement.period || "unknown";
      const mapped = mapStatements(ocrResult.fields, period);

      await saveExtractedData(analysisRef, {
        rawOcr: ocrResult.rawResponse,
        mappedFields: ocrResult.fields,
        ocrMetadata: ocrResult.metadata,
        incomeStatement: mapped.incomeStatement,
        balanceSheet: mapped.balanceSheet,
        processedAt: FieldValue.serverTimestamp(),
      });

      const ratios = buildFinancialRatios(mapped.incomeStatement, mapped.balanceSheet);
      await saveFinancialRatios(analysisRef, ratios);

      const projections = generateProjectionScenarios(mapped.incomeStatement, mapped.balanceSheet, {
        horizonYears: 3,
        baseGrowthRate: 0.05,
      });
      await saveProjections(analysisRef, projections);

      const recommendations = await generateRecommendations(ratios, projections);
      await saveRecommendations(analysisRef, recommendations);

      await updateAnalysisStatus(analysisRef, "completed");
      await appendAuditLog(analysisRef, "analysis_completed", { statementId: snapshot.id });

      await snapshot.ref.update({
        status: "completed",
        updatedAt: FieldValue.serverTimestamp(),
        incomeStatement: mapped.incomeStatement,
        balanceSheet: mapped.balanceSheet,
      });
    } catch (error) {
      await updateAnalysisStatus(analysisRef, "failed");
      await appendAuditLog(analysisRef, "analysis_failed", {
        statementId: snapshot.id,
        error: error instanceof Error ? error.message : String(error),
      });
      await snapshot.ref.update({
        status: "failed",
        updatedAt: FieldValue.serverTimestamp(),
        errorMessage: error instanceof Error ? error.message : String(error),
      });
    }
  }
);
