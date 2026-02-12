const axios = require("axios");
const crypto = require("crypto");

async function generateRecommendations(ratios, projections) {
  const apiKey = process.env.OPENAI_API_KEY;
  const model = process.env.OPENAI_MODEL || "gpt-4o-mini";

  const promptUsed = [
    "Eres un analista financiero senior.",
    "Devuelve JSON con: texto_analisis (string) y sugerencias (array).",
    `Ratios: ${JSON.stringify(ratios)}`,
    `Proyecciones: ${JSON.stringify(projections)}`,
  ].join("\n");

  const promptHash = crypto.createHash("sha256").update(promptUsed).digest("hex");

  if (!apiKey) {
    return {
      rawResponse: "",
      parsedRecommendations: {
        texto_analisis: "Recomendaciones pendientes: configurar OPENAI_API_KEY.",
        sugerencias: [],
      },
      confidenceScore: 0,
      promptUsed,
      promptHash,
      aiModel: model,
    };
  }

  const response = await axios.post(
    "https://api.openai.com/v1/chat/completions",
    {
      model,
      temperature: 0.2,
      messages: [
        { role: "system", content: "Responde solo con JSON valido." },
        { role: "user", content: promptUsed },
      ],
    },
    {
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
    }
  );

  const rawResponse = response.data.choices?.[0]?.message?.content ?? "";
  let parsed = { texto_analisis: rawResponse, sugerencias: [] };
  try {
    parsed = JSON.parse(rawResponse);
  } catch {
    parsed = { texto_analisis: rawResponse, sugerencias: [] };
  }

  return {
    rawResponse,
    parsedRecommendations: parsed,
    confidenceScore: 0.7,
    promptUsed,
    promptHash,
    aiModel: model,
  };
}

module.exports = { generateRecommendations };
