"""
Fixtures de prueba para regresión del FinancialCalculator.

Cada fixture representa el output de Azure Document Intelligence para un documento
real que fue probado y validado manualmente. Están construidos en formato
tables_data: List[List[{text, row, col}]] tal como lo produce AzureDocumentService.

Empresas incluidas:
  - ECOGREEN       : anual 2024, balance lado a lado (4 columnas)
  - TECH_SOLUCIONES: anual 2024, balance vertical con secciones
  - GCMK           : mensual oct-2023, balance lado a lado + ER multi-columna
  - TAAS_ENE       : mensual ene-2026, balance jerárquico + ER dos columnas
  - TAAS_MAR       : trimestral Q1-2026, mismo balance + ER con columnas mensuales
  - COCACOLA       : trimestral 1T-2026, balances corporativos BMV (millones)
"""

import json
import os


def _cells(*rows):
    """Convierte una lista de tuplas (col0, col1, ...) a una lista de celdas OCR.
    Las celdas vacías se omiten (Azure no emite celdas vacías)."""
    result = []
    for r_idx, row in enumerate(rows):
        for c_idx, text in enumerate(row):
            if str(text).strip():
                result.append({"text": str(text), "row": r_idx, "col": c_idx})
    return result


# ============================================================
#  ECOGREEN — anual 2024
#  Formato: balance lado a lado (activo izq, pasivo+capital der)
# ============================================================

ECOGREEN_BALANCE = {
    "text_content": (
        "Eco-Green Sociedad Cooperativa de R.L.\n"
        "Estado de situación financiera al 31 de diciembre de 2024"
    ),
    "tables_data": [
        _cells(
            # col0=concepto_activo  col1=valor_activo  col2=concepto_pasivo  col3=valor_pasivo
            ("ACTIVO",                    "2024",      "PASIVO + CAPITAL",           "2024"),
            ("Circulante",                "",          "Pasivo C.P.",                ""),
            ("Efectivo",                  "350,000",   "Proveedores",                "400,000"),
            ("Clientes",                  "380,000",   "PTU por Pagar",              "32,000"),
            ("Inventarios",               "900,000",   "ISR por Pagar",              "96,000"),
            ("Seguros Anticipados",       "25,000",    "Total Pasivo a Corto Plazo", "528,000"),
            ("Total Activo Circulante",   "1,655,000", "Pasivo L.P.",                "1,200,000"),
            ("No Circulante",             "",          "Total Pasivo",               "1,728,000"),
            ("Terrenos",                  "900,000",   "Capital",                    ""),
            ("Maquinaria",                "1,500,000", "Certif. Aportación",         "2,000,000"),
            ("(-) Deprec. Acum.",         "(300,000)", "Reservas",                   "350,000"),
            ("Total Activo No Circulante","2,100,000", "Utilid. Ejercicios",         "377,000"),
            ("",                          "",          "Total Capital Contable",     "2,727,000"),
            ("TOTAL ACTIVO",              "4,455,000", "TOT. PAS+CAP",               "4,455,000"),
        )
    ],
}

ECOGREEN_RESULTADOS = {
    "text_content": (
        "Eco-Green Sociedad Cooperativa de R.L.\n"
        "Estado de resultados del 1 de enero al 31 de diciembre de 2024"
    ),
    "tables_data": [
        _cells(
            ("Ventas Netas",                        "3,500,000"),
            ("(-) Costo de Ventas",                 "(1,900,000)"),
            ("Utilidad Bruta",                      "1,600,000"),
            ("(-) Gastos de Administración",        "(550,000)"),
            ("(-) Gastos de Venta",                 "(630,000)"),
            ("Utilidad de Operación",               "420,000"),
            ("(-) Gastos Financieros",              "(100,000)"),
            ("Utilidad antes de Impuestos y PTU",   "320,000"),
            ("(-) PTU (10%)",                       "(32,000)"),
            ("(-) ISR (30%)",                       "(96,000)"),
            ("UTILIDAD NETA",                       "192,000"),
        )
    ],
}

ECOGREEN_CFG = {
    "balance": ECOGREEN_BALANCE,
    "resultados": ECOGREEN_RESULTADOS,
    "periodicidad": "anual",
    "col_index": 0,
}

# ============================================================
#  TECH SOLUCIONES — anual 2024
#  Formato: balance vertical, secciones separadas con headers
# ============================================================

TECH_BALANCE = {
    "text_content": (
        "Tech Soluciones SA. de C.V.\n"
        "Estado de situación financiera al 31 de diciembre de 2024"
    ),
    "tables_data": [
        # Tabla 1: Activos
        _cells(
            ("Activo Circulante",                    ""),
            ("Efectivo y Equivalentes",              "480,000"),
            ("Cuentas por Cobrar (Clientes)",        "650,000"),
            ("Inventarios (Hardware para servicios)","280,000"),
            ("Seguros Pagados por Anticipado",       "45,000"),
            ("Rentas Pagadas por Anticipado",        "110,000"),
            ("Total Activo Circulante",              "1,565,000"),
            ("Activo No Circulante (Propiedad, Planta y Equipo)", ""),
            ("Terrenos",                             "1,200,000"),
            ("Edificios",                            "2,800,000"),
            ("Mobiliario y Equipo de Oficina",       "210,000"),
            ("Equipo de Cómputo",                    "850,000"),
            ("Equipo de Transporte",                 "420,000"),
            ("(-) Depreciación Acumulada",           "(850,000)"),
            ("Patentes y Marcas (Neto)",             "300,000"),
            ("Gastos de Instalación",                "105,000"),
            ("Total Activo No Circulante",           "5,035,000"),
            ("TOTAL ACTIVO",                         "6,600,000"),
        ),
        # Tabla 2: Pasivos y Capital
        _cells(
            ("Pasivo a Corto Plazo",                 ""),
            ("Proveedores",                          "410,000"),
            ("PTU por Pagar",                        "25,500"),
            ("Impuestos (ISR) por Pagar",            "76,500"),
            ("Préstamos Bancarios (C.P.)",           "200,000"),
            ("Total Pasivo Corto Plazo",             "712,000"),
            ("Pasivo a Largo Plazo",                 "2,200,000"),
            ("TOTAL PASIVO",                         "2,912,000"),
            ("Capital Social",                       "3,000,000"),
            ("Utilidades Acumuladas",                "688,000"),
            ("TOTAL CAPITAL CONTABLE",               "3,688,000"),
            ("TOTAL PASIVO + CAPITAL",               "6,600,000"),
        ),
    ],
}

TECH_RESULTADOS = {
    "text_content": (
        "Tech Soluciones SA. de C.V.\n"
        "Estado de resultados del 1 de enero al 31 de diciembre de 2024"
    ),
    "tables_data": [
        _cells(
            ("Ventas Netas",                         "2,800,000"),
            ("(-) Costo de Ventas",                  "(1,450,000)"),
            ("Utilidad Bruta",                       "1,350,000"),
            ("(-) Gastos de Administración",         "(650,000)"),
            ("(-) Gastos de Venta",                  "(400,000)"),
            ("Utilidad de Operación",                "300,000"),
            ("(-) Gastos Financieros (Intereses)",   "(45,000)"),
            ("Utilidad antes de Impuestos y PTU",    "255,000"),
            ("(-) PTU (10%)",                        "(25,500)"),
            ("(-) ISR (30%)",                        "(76,500)"),
            ("UTILIDAD NETA",                        "153,000"),
        )
    ],
}

TECH_CFG = {
    "balance": TECH_BALANCE,
    "resultados": TECH_RESULTADOS,
    "periodicidad": "anual",
    "col_index": 0,
}

# ============================================================
#  COMERCIALIZADORA GCMK — mensual oct-2023
#  Formato: balance lado a lado, ER multi-columna (mes + acumulado)
# ============================================================

GCMK_BALANCE = {
    "text_content": (
        "COMERCIALIZADORA GCMK 2023\n"
        "BALANCE GENERAL AL 31 DE OCTUBRE DE 2023"
    ),
    "tables_data": [
        _cells(
            # col0=concepto_activo  col1=val_activo  col2=concepto_pasivo  col3=val_pasivo
            ("BANCOS",                    "990,575.98",    "ACREEDORES DIVERSOS",       "-1,612,763.58"),
            ("CLIENTES",                  "1,385,929.80",  "IVA COBRADO",               "-68,958.08"),
            ("DEUDORES DIVERSOS",         "76,804.26",     "I.V.A TRASLADADO",          "507,806.71"),
            ("ISR ANTICIPOS",             "394,904.00",    "IMPUESTOS POR PAGAR",       "101,166.38"),
            ("IVA RETENIDO",              "6,200.47",      "PASIVO CIRCULANTE",         "-1,072,748.57"),
            ("IVA A FAVOR EJER ANT",      "37,845.06",     "CAPITAL SOCIAL FIJO",       "100,000.00"),
            ("ISR A FAVOR",               "161,128.00",    "RESERVA LEGAL",             "364,145.00"),
            ("SUB-SIDIO AL EMPLEO",       "160,746.33",    "RESULS. EJERCICIOS ANT.",   "-620,106.08"),
            ("ACTIVO CIRCULANTE",         "3,214,133.90",  "RESUL. DEL EJERCICIO",      "3,784,287.01"),
            ("CASA OFICINA",              "3,800,000.00",  "UTILIDADES Y PERDIDAS ACUM.","5,304,611.25"),
            ("EQUIPO AUTOMOTRIZ",         "1,911,468.71",  "CAPITAL CONTABLE",          "8,932,937.18"),
            ("DEP. ACUM. CASA OFICINA",   "-380,000.00",   "TOTAL DE PASIVO Y CAPITAL", "7,860,188.61"),
            ("DEP. ACUM. EQ. AUT.",       "-685,414.00",   "",                          ""),
            ("ACTIVO FIJO",               "4,646,054.71",  "",                          ""),
            ("TOTAL DE ACTIVOS",          "7,860,188.61",  "",                          ""),
        )
    ],
}

# GCMK ER: 7 columnas → col0=desc, col1=importe_mes, col2=subtotal_mes, col3=%ventas,
#                        col4=importe_acum, col5=subtotal_acum, col6=%ventas_acum
# Para mensual (col_index=0) se toman los valores de las columnas impares (mes actual).
GCMK_RESULTADOS = {
    "text_content": (
        "COMERCIALIZADORA GCMK 2023\n"
        "ESTADO DE RESULTADOS DEL MES DE OCTUBRE DE 2023"
    ),
    "tables_data": [
        _cells(
            # (desc, val_mes, subtotal_mes, %ventas, val_acum, subtotal_acum, %ventas_acum)
            ("ING POR SERVICIOS",           "496,288.60",  "",           "100.00", "8,573,072.78", "",            "99.86"),
            ("INGRESOS EXENTOS",            "-0.00",       "",           "",       "12,230.40",    "",            "0.14"),
            ("INGRESOS POR SERVICIOS",      "",            "496,288.60", "100.00", "",             "8,585,303.18","100.00"),
            ("GASTOS DE OPERACION",         "331,029.83",  "",           "66.70",  "4,792,628.15", "",            "55.82"),
            ("GASTOS DE ADMINISTRACION",    "331,029.83",  "",           "66.70",  "4,792,628.15", "",            "55.82"),
            ("UTILIDAD DE OPERACION",       "",            "165,258.77", "33.30",  "",             "3,792,675.03","44.18"),
            ("GASTOS FINANCIEROS",          "0.00",        "",           "",       "8,388.02",     "",            "0.10"),
            ("TOTAL DE OTROS GASTOS",       "",            "0.00",       "",       "",             "8,388.02",    "0.10"),
            ("UTILIDAD ANTES DE IMPUESTOS", "165,258.77",  "",           "33.30",  "3,784,287.01", "",            "44.08"),
        )
    ],
}

GCMK_CFG = {
    "balance": GCMK_BALANCE,
    "resultados": GCMK_RESULTADOS,
    "periodicidad": "mensual",
    "col_index": 0,
}

# ============================================================
#  TAAS LOGISTICS — mensual ene-2026
#  Formato: balance jerárquico con indentación, ER dos columnas
# ============================================================

TAAS_ENE_BALANCE = {
    "text_content": (
        "TAAS LOGISTICS SA DE CV\n"
        "BALANCE GENERAL AL 31/01/2026"
    ),
    "tables_data": [
        _cells(
            ("ACTIVOS",                   "4,582,804.97",  "PASIVOS",               "423,385.47"),
            ("Activo a Corto Plazo",      "2,853,404.97",  "Pasivo a corto plazo",  "423,385.47"),
            ("Caja",                      "10,000.00",     "Proveedores",           "398,401.77"),
            ("Bancos",                    "1,209,742.96",  "Impuestos trasladados", "21,101.25"),
            ("Clientes",                  "1,643,223.10",  "Impuestos retenidos",   "3,882.45"),
            ("Impuestos a favor",         "-11,900.27",    "",                      ""),
            ("Activo a Largo Plazo",      "1,729,400.00",  "CAPITAL",               ""),
            ("Maquinaria y equipo",       "395,600.00",    "Capital contable",      "4,159,419.50"),
            ("Automóviles y camiones",    "1,050,300.00",  "Capital social",        "4,739,400.00"),
            ("Mobiliario y equipo",       "160,000.00",    "Resultado del ejercicio","-579,980.50"),
            ("Equipo de cómputo",         "73,200.00",     "",                      ""),
            ("Equipo de comunicación",    "50,300.00",     "",                      ""),
            ("Total Activos:",            "4,582,804.97",  "Total Pasivo + Capital:","4,582,804.97"),
        )
    ],
}

TAAS_ENE_RESULTADOS = {
    "text_content": (
        "TAAS LOGISTICS SA DE CV\n"
        "ESTADO DE RESULTADOS ENERO DE 2026"
    ),
    "tables_data": [
        _cells(
            # col0=concepto, col1=valor_mes, col2=acumulado
            ("Ingresos",                                  "479,242.08", "479,242.08"),
            ("Ventas y/o servicios gravados",             "219,068.98", "219,068.98"),
            ("Ventas y/o servicios exentos",              "260,173.10", "260,173.10"),
            ("Total ingresos",                            "479,242.08", "479,242.08"),
            ("Costo de venta y/o servicio",               "11,048.73",  "11,048.73"),
            ("Compras nacionales",                        "60,469.35",  "60,469.35"),
            ("Devoluciones, descuentos o bonificaciones", "1,834.46",   "1,834.46"),
            ("Total costos",                              "69,683.62",  "69,683.62"),
            ("Gastos generales",                          "30,140.28",  "30,140.28"),
            ("Gastos de venta",                           "581.90",     "581.90"),
            ("Gastos de administración",                  "1,492.69",   "1,492.69"),
            ("Total gastos",                              "32,214.87",  "32,214.87"),
            ("Gastos financieros",                        "14,669.35",  "14,669.35"),
            ("Total resultado financiero",                "14,669.35",  "14,669.35"),
            ("Utilidad Total",                            "362,674.24", "362,674.24"),
        )
    ],
}

TAAS_ENE_CFG = {
    "balance": TAAS_ENE_BALANCE,
    "resultados": TAAS_ENE_RESULTADOS,
    "periodicidad": "mensual",
    "col_index": 0,
}

# ============================================================
#  TAAS LOGISTICS — trimestral Q1 2026 (ene-mar)
#  Mismo balance a marzo, ER con columnas: ene | feb | mar | total
# ============================================================

TAAS_MAR_BALANCE = {
    "text_content": (
        "TAAS LOGISTICS SA DE CV\n"
        "BALANCE GENERAL AL 31/03/2026"
    ),
    "tables_data": [
        _cells(
            ("ACTIVOS",                   "4,828,580.34",  "PASIVOS",                "367,653.98"),
            ("Activo a Corto Plazo",      "3,099,180.34",  "Pasivo a corto plazo",   "367,653.98"),
            ("Caja",                      "10,000.00",     "Proveedores",            "353,633.80"),
            ("Bancos",                    "1,613,576.78",  "Impuestos trasladados",  "10,135.73"),
            ("Clientes",                  "1,515,323.53",  "Impuestos retenidos",    "3,882.45"),
            ("Activo a Largo Plazo",      "1,729,400.00",  "CAPITAL",                ""),
            ("Maquinaria y equipo",       "395,600.00",    "Capital contable",       "4,460,926.36"),
            ("Automóviles y camiones",    "1,050,300.00",  "Capital social",         "4,739,400.00"),
            ("Mobiliario y equipo",       "160,000.00",    "Resultado del ejercicio","-278,473.64"),
            ("Equipo de cómputo",         "73,200.00",     "",                       ""),
            ("Equipo de comunicación",    "50,300.00",     "",                       ""),
            ("Total Activos:",            "4,828,580.34",  "Total Pasivo + Capital:", "4,828,580.34"),
        )
    ],
}

# ER trimestral con columnas: ene | feb | mar | total (col_index=0 para Q1)
# Para periodicidad trimestral, la regla francotirador suma las 3 columnas del periodo.
# Incluimos las 4 columnas reales del documento.
TAAS_MAR_RESULTADOS = {
    "text_content": (
        "TAAS LOGISTICS SA DE CV\n"
        "ESTADO DE RESULTADOS DE 1 DE ENERO DE 2026 AL 31 DE MARZO DE 2026"
    ),
    "tables_data": [
        _cells(
            # col0=concepto, col1=ene, col2=feb, col3=mar, col4=total
            ("Ingresos",                                  "479,242.08", "245,586.97", "244,831.81", "969,660.86"),
            ("Ventas y/o servicios gravados",             "219,068.98", "135,687.07", "102,912.41", "457,668.46"),
            ("Ventas y/o servicios exentos",              "260,173.10", "109,899.90", "141,919.40", "511,992.40"),
            ("Total ingresos",                            "479,242.08", "245,586.97", "244,831.81", "969,660.86"),
            ("Costo de venta y/o servicio",               "11,048.73",  "15,020.89",  "15,654.19",  "26,693.98"),
            ("Compras nacionales",                        "60,469.35",  "62,301.63",  "15,654.19",  "138,425.17"),
            ("Devoluciones, descuentos o bonificaciones", "1,834.46",   "624.36",     "3,108.14",   "5,567.54"),
            ("Total costos",                              "69,683.62",  "76,698.16",  "28,200.24",  "159,551.61"),
            ("Gastos generales",                          "30,140.28",  "24,775.67",  "15,332.03",  "70,247.98"),
            ("Gastos de venta",                           "581.90",     "0.00",       "29,438.79",  "30,020.69"),
            ("Gastos de administración",                  "1,492.69",   "0.00",       "17,068.97",  "18,561.66"),
            ("Total gastos",                              "32,214.87",  "24,775.67",  "61,839.79",  "118,830.33"),
            ("Gastos financieros",                        "14,669.35",  "3,524.77",   "9,904.81",   "28,098.93"),
            ("Total resultado financiero",                "14,669.35",  "3,524.77",   "9,904.81",   "28,098.93"),
            ("Utilidad Total",                            "362,674.24", "140,588.37", "145,888.78", "664,181.10"),
        )
    ],
}

TAAS_MAR_CFG = {
    "balance": TAAS_MAR_BALANCE,
    "resultados": TAAS_MAR_RESULTADOS,
    "periodicidad": "trimestral",
    "col_index": 0,
}

# ============================================================
#  COCA-COLA FEMSA — trimestral 1T-2026
#  Formato: balance corporativo BMV (millones de pesos),
#           ER con columnas 1T2026 | 1T2025
# ============================================================

COCACOLA_BALANCE = {
    "text_content": (
        "COCA-COLA FEMSA\n"
        "ESTADO DE SITUACIÓN FINANCIERA CONSOLIDADO\n"
        "Millones de pesos\n"
        "31 de marzo de 2026"
    ),
    "tables_data": [
        _cells(
            # col0=concepto_activo   col1=mar26  col2=concepto_pasivo    col3=mar26
            ("Activos Corrientes",                "",        "Pasivo Corriente",                   ""),
            ("Efectivo y equivalentes",           "41,346",  "Deuda a corto plazo",                "4,875"),
            ("Total cuentas por cobrar",          "17,749",  "Proveedores",                        "29,385"),
            ("Inventarios",                       "14,814",  "Vencimiento CP pasivo arrendamiento","952"),
            ("Otros activos circulantes",         "12,233",  "Otros pasivos corto plazo",          "43,133"),
            ("Total activos circulantes",         "86,141",  "Pasivo circulante",                  "78,345"),
            ("Activos no corrientes",             "",        "Pasivos no corrientes",              ""),
            ("Propiedad, planta y equipo",        "180,491", "Préstamos bancarios",                "82,233"),
            ("Depreciación acumulada",            "(68,766)","Obligaciones arrendamiento LP",      "2,857"),
            ("Total propiedad, planta y equipo, neto","111,725","Otros pasivos de largo plazo",    "22,811"),
            ("Activos por Derechos de Uso",       "3,461",   "Total pasivo",                       "186,246"),
            ("Inversión en acciones",             "10,587",  "Capital",                            ""),
            ("Activos intangibles",               "104,318", "Participación no controladora",      "8,645"),
            ("Otros activos no circulantes",      "16,883",  "Total participación controladora",   "138,225"),
            ("Total activos",                     "333,116", "Total Capital",                      "146,870"),
        )
    ],
}

COCACOLA_RESULTADOS = {
    "text_content": (
        "COCA-COLA FEMSA\n"
        "ESTADO DE RESULTADOS CONSOLIDADO\n"
        "Millones de pesos (1)\n"
        "Por el primer trimestre de:"
    ),
    "tables_data": [
        _cells(
            # col0=concepto, col1=1T2026, col2=%ing, col3=1T2025, col4=%ing_2025
            ("Ventas netas",                       "70,631",  "99.6%",  "70,073",  "99.9%"),
            ("Otros ingresos de operación",        "295",     "0.4%",   "84",      "0.1%"),
            ("Ingresos totales",                   "70,925",  "100.0%", "70,157",  "100.0%"),
            ("Costo de ventas",                    "37,670",  "53.1%",  "38,324",  "54.6%"),
            ("Utilidad bruta",                     "33,255",  "46.9%",  "31,832",  "45.4%"),
            ("Gastos de operación",                "24,145",  "34.0%",  "22,478",  "32.0%"),
            ("Otros gastos operativos, neto",      "176",     "0.2%",   "184",     "0.3%"),
            ("Utilidad de operación",              "9,032",   "12.7%",  "9,248",   "13.2%"),
            ("Gastos financieros",                 "2,087",   "",       "1,879",   ""),
            ("Productos financieros",              "515",     "",       "590",     ""),
            ("Resultado integral de financiamiento","1,752",  "",       "1,126",   ""),
            ("Utilidad antes de impuestos",        "7,422",   "",       "8,172",   ""),
            ("Impuestos",                          "2,688",   "",       "2,681",   ""),
            ("Utilidad neta consolidada",          "4,735",   "",       "5,492",   ""),
            ("Utilidad neta atribuible a la participación controladora","4,342","6.1%","5,139","7.3%"),
            ("Participación no controladora",      "392",     "0.6%",   "352",     "0.5%"),
        )
    ],
}

COCACOLA_CFG = {
    "balance": COCACOLA_BALANCE,
    "resultados": COCACOLA_RESULTADOS,
    "periodicidad": "trimestral",
    "col_index": 0,
}

# ============================================================
#  Mapa global de casos de prueba
# ============================================================
ALL_CASES = {
    "ecogreen":        ECOGREEN_CFG,
    "tech_soluciones": TECH_CFG,
    "gcmk":            GCMK_CFG,
    "taas_ene":        TAAS_ENE_CFG,
    "taas_mar":        TAAS_MAR_CFG,
    "cocacola":        COCACOLA_CFG,
}

GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "golden")
