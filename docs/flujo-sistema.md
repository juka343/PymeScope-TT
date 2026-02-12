# Flujo del Sistema (Firestore + Storage)

## Estructura y Flujo

```mermaid
flowchart TB
	subgraph Estructura_Firestore
		U[users] --> U1[users/{userId}]
		U1 --> C[companies]
		C --> C1[companies/{companyId}]
		C1 --> A[analysisSessions]
		A --> A1[analysisSessions/{analysisId}]
		A1 --> FS[financialStatements]
		A1 --> ED[extractedData]
		A1 --> FR[financialRatios]
		A1 --> PR[projections]
		A1 --> RC[recommendations]
		A1 --> AL[auditLogs]
	end

	subgraph Flujo_Datos
		Ux[Usuario/Frontend] -->|Sube PDF| S[Firebase Storage]
		Ux -->|Crea analysisSession + financialStatement| F[Firestore]
		F -->|Trigger onCreate| CF[Cloud Function]
		CF -->|Descarga PDF| S
		CF -->|OCR| OCR[Azure Document Intelligence]
		OCR -->|Datos crudos| CF
		CF -->|Mapeo a Income/Balance| MAP[Normalizacion]
		MAP -->|extractedData| F
		MAP -->|Ratios| RAT[Financial Calculations]
		RAT -->|financialRatios| F
		RAT -->|Proyecciones| PRJ[Projection Engine]
		PRJ -->|projections| F
		PRJ -->|IA| AI[OpenAI]
		AI -->|recommendations| F
		CF -->|auditLogs + status| F
	end
```
