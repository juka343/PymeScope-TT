const axios = require("axios");

function extractNumber(value) {
  if (typeof value === "number") {
    return value;
  }
  if (typeof value === "string") {
    const normalized = value.replace(/[^0-9.-]/g, "");
    return Number(normalized) || 0;
  }
  return 0;
}

async function analyzeDocument(buffer) {
  const endpoint = process.env.AZURE_DOC_INTEL_ENDPOINT;
  const apiKey = process.env.AZURE_DOC_INTEL_KEY;
  const modelId = process.env.AZURE_DOC_INTEL_MODEL || "prebuilt-document";

  if (!endpoint || !apiKey) {
    return { rawResponse: {}, fields: {}, metadata: { provider: "azure", modelId } };
  }

  const submitUrl = `${endpoint}/documentModels/${modelId}:analyze?api-version=2023-07-31`;
  const submitResponse = await axios.post(submitUrl, buffer, {
    headers: {
      "Ocp-Apim-Subscription-Key": apiKey,
      "Content-Type": "application/octet-stream",
    },
  });

  const operationLocation = submitResponse.headers["operation-location"];
  if (!operationLocation) {
    throw new Error("Azure OCR did not return operation-location header.");
  }

  let status = "running";
  let resultData = null;
  while (status === "running" || status === "notStarted") {
    const pollResponse = await axios.get(operationLocation, {
      headers: { "Ocp-Apim-Subscription-Key": apiKey },
    });
    status = pollResponse.data.status;
    resultData = pollResponse.data;
    if (status === "succeeded" || status === "failed") {
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }

  const fields = resultData?.analyzeResult?.documents?.[0]?.fields || {};
  const mappedFields = {};
  for (const [key, value] of Object.entries(fields)) {
    mappedFields[key] = extractNumber(value?.value || value?.content);
  }

  return {
    rawResponse: resultData,
    fields: mappedFields,
    metadata: { provider: "azure", modelId },
  };
}

module.exports = { analyzeDocument };
