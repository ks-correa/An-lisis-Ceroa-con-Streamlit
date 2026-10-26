import os
import math
import zipfile
import xml.etree.ElementTree as ET
import streamlit as st
import pandas as pd
import plotly.express as px
from dashboard_ui import aplicar_estilo, mostrar_grafica

# Configuración del entorno de visualización (primera instrucción de Streamlit)
st.set_page_config(
    page_title="Ceroa BI | Plataforma de Bienestar Financiero",
    layout="wide",
    initial_sidebar_state="expanded"
)

aplicar_estilo()
st.title("Ceroa | Resumen del negocio")
st.caption("Suscripciones, recaudo y costos de operación. Todos los valores monetarios están en pesos colombianos (COP).")
st.markdown("---")


def _leer_csv_robusto(ruta_archivo):
    """
    Lectura tolerante de archivos CSV:
    - Autodetecta separador (coma, punto y coma, tabulador)
    - Limpia caracteres BOM y espacios en blanco de las cabeceras
    """
    try:
        df = pd.read_csv(ruta_archivo, sep=None, engine="python", encoding="utf-8-sig")
    except Exception:
        df = pd.read_csv(ruta_archivo, sep=",", encoding="latin1")
    df.columns = df.columns.astype(str).str.strip()
    return df


def _leer_hoja_excel_xml(ruta_excel, nombre_hoja):
    """
    Lector de respaldo nativo (sin dependencias adicionales) para hojas de un archivo .xlsx
    en caso de que el entorno virtual no tenga instalado openpyxl.
    """
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    rel_ns = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    with zipfile.ZipFile(ruta_excel) as z:
        shared_strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            root_ss = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root_ss:
                shared_strings.append("".join([t.text or "" for t in si.iter() if t.tag.endswith("}t")]))

        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rel_map = {r.attrib["Id"]: r.attrib["Target"].lstrip("/") for r in rels}

        target = None
        for sheet in wb.iter():
            if sheet.tag.endswith("}sheet") and sheet.attrib.get("name") == nombre_hoja:
                rid = sheet.attrib[rel_ns]
                target = rel_map[rid]
                if not target.startswith("xl/"):
                    target = "xl/" + target
                break

        if not target:
            raise KeyError(f"No se encontró la hoja '{nombre_hoja}' en '{ruta_excel}'.")

        sroot = ET.fromstring(z.read(target))
        rows = list(sroot.iter(f"{ns}row"))
        data = []
        for r in rows:
            row_dict = {}
            for c in r:
                ref = c.attrib.get("r", "")
                col_letters = "".join([ch for ch in ref if ch.isalpha()])
                t = c.attrib.get("t", "")
                v_el = c.find(f"{ns}v")
                is_el = c.find(f"{ns}is")
                val = v_el.text if v_el is not None else None
                if is_el is not None:
                    val = "".join([x.text or "" for x in is_el.iter() if x.tag.endswith("}t")])
                elif t == "s" and val is not None:
                    val = shared_strings[int(val)]
                row_dict[col_letters] = val
            data.append(row_dict)
        return pd.DataFrame(data)


def _leer_hoja_excel(ruta_excel, nombre_hoja, columna_clave=None):
    """
    Lee una hoja del libro Excel usando pandas (openpyxl) o el lector XML de respaldo,
    detectando automáticamente la fila de encabezado mediante 'columna_clave'.
    """
    try:
        df_raw = pd.read_excel(ruta_excel, sheet_name=nombre_hoja, header=None)
    except Exception:
        df_raw = _leer_hoja_excel_xml(ruta_excel, nombre_hoja)

    if df_raw.empty:
        return pd.DataFrame()

    fila_encabezado = 0
    if columna_clave is not None:
        clave_norm = str(columna_clave).strip().lower()
        for idx in range(min(10, len(df_raw))):
            valores_fila = [str(v).strip().lower() for v in df_raw.iloc[idx].values if pd.notna(v)]
            if clave_norm in valores_fila:
                fila_encabezado = idx
                break

    headers = {col: str(val).strip() for col, val in df_raw.iloc[fila_encabezado].items()}
    df = df_raw.iloc[fila_encabezado + 1:].rename(columns=headers).reset_index(drop=True)
    df.columns = df.columns.astype(str).str.strip()
    if columna_clave is not None and columna_clave in df.columns:
        df = df[df[columna_clave].notna() & (df[columna_clave].astype(str).str.strip() != "")].reset_index(drop=True)
    return df


def _normalizar_numerico(df, columnas):
    """
    Normaliza columnas numéricas manejando formato texto, símbolo '$' o coma decimal.
    """
    for col in columnas:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace("$", "", regex=False)
                    .str.replace(" ", "", regex=False)
                    .str.replace(",", ".", regex=False)
                )
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


@st.cache_data
def cargar_datos():
    """
    Carga robusta de la base de datos de Ceroa:
    - Lee los registros completos desde la carpeta 'datos/' (CSV)
    - Lee las hojas de parámetros y catálogo ('Tarifas', 'Supuestos', 'Finanzas_Mes',
      'Proveedores', 'Insumos') desde el archivo Excel de Ceroa
    - Limpia nombres de columnas, convierte fechas y normaliza tipos numéricos
    - Reproduce en Python los cálculos financieros de MRR, Recaudo, COGS, Margen Bruto y OPEX
      a partir de la hoja 'Supuestos' para evitar celdas vacías de fórmulas de Excel
    """
    carpeta_datos = "datos"
    archivos_csv = {
        "usuarios_mes": os.path.join(carpeta_datos, "usuarios_mes.csv"),
        "actividad_mensual": os.path.join(carpeta_datos, "actividad_mensual.csv"),
        "cobros": os.path.join(carpeta_datos, "cobros.csv"),
        "suscripciones": os.path.join(carpeta_datos, "suscripciones.csv"),
        "deudas": os.path.join(carpeta_datos, "deudas.csv"),
        "abonos_deuda": os.path.join(carpeta_datos, "abonos_deuda.csv"),
        "adquisicion": os.path.join(carpeta_datos, "adquisicion.csv"),
    }

    for nombre, ruta in archivos_csv.items():
        if not os.path.exists(ruta):
            raise FileNotFoundError(f"No se encontró el archivo requerido: '{ruta}'.")

    # Localización del libro Excel (acepta nombre recalculado o nombre base)
    ruta_excel = "Ceroa_Base_Datos_Recalculada.xlsx"
    if not os.path.exists(ruta_excel):
        if os.path.exists("Ceroa_Base_Datos.xlsx"):
            ruta_excel = "Ceroa_Base_Datos.xlsx"
        else:
            raise FileNotFoundError(
                "No se encontró 'Ceroa_Base_Datos_Recalculada.xlsx' ni 'Ceroa_Base_Datos.xlsx'."
            )

    # 1. Carga de archivos CSV completos
    df_usuarios_mes = _leer_csv_robusto(archivos_csv["usuarios_mes"])
    df_actividad = _leer_csv_robusto(archivos_csv["actividad_mensual"])
    df_cobros = _leer_csv_robusto(archivos_csv["cobros"])
    df_suscripciones = _leer_csv_robusto(archivos_csv["suscripciones"])
    df_deudas = _leer_csv_robusto(archivos_csv["deudas"])
    df_abonos = _leer_csv_robusto(archivos_csv["abonos_deuda"])
    df_adquisicion = _leer_csv_robusto(archivos_csv["adquisicion"])

    # 2. Validación preventiva de columnas requeridas en los CSV principales
    validaciones_columnas = {
        "usuarios_mes.csv": (
            df_usuarios_mes,
            [
                "mes", "usuario_id", "plan", "tipo_plan", "ciudad",
                "deudas_activas", "saldo_deudas_fin_mes_cop",
                "abonos_deudas_mes_cop", "mrr_equivalente_cop"
            ],
        ),
        "actividad_mensual.csv": (
            df_actividad,
            [
                "mes", "usuarios_nuevos", "usuarios_activos", "usuarios_gratis",
                "plus_mensual_activos", "plus_anual_activos", "usuarios_plus",
                "deudas_activas", "saldo_deudas_administradas_cop",
                "abonos_a_acreedores_cop", "cobros_aprobados", "cobros_rechazados",
                "recaudo_ceroa_cop", "inversion_marketing_cop", "altas_plus"
            ],
        ),
        "cobros.csv": (
            df_cobros,
            [
                "transaccion_id", "mes", "fecha_transaccion", "usuario_id",
                "plan_solicitado", "estado", "importe_cop"
            ],
        ),
    }

    for nombre_archivo, (df_val, cols_req) in validaciones_columnas.items():
        faltantes = [c for c in cols_req if c not in df_val.columns]
        if faltantes:
            raise KeyError(
                f"Columnas faltantes en {nombre_archivo}: {faltantes}. "
                f"Columnas leídas: {list(df_val.columns)}"
            )

    # 3. Carga de hojas de referencia desde el Excel ('Tarifas', 'Supuestos', 'Finanzas_Mes', 'Proveedores', 'Insumos')
    df_tarifas = _leer_hoja_excel(ruta_excel, "Tarifas", columna_clave="Plan")
    df_supuestos = _leer_hoja_excel(ruta_excel, "Supuestos", columna_clave="Variable")
    df_finanzas_excel = _leer_hoja_excel(ruta_excel, "Finanzas_Mes", columna_clave="mes")
    df_proveedores = _leer_hoja_excel(ruta_excel, "Proveedores", columna_clave="proveedor_id")
    df_insumos = _leer_hoja_excel(ruta_excel, "Insumos", columna_clave="insumo_id")

    # Extracción dinámica de parámetros desde la hoja 'Supuestos'
    supuestos_map = {}
    if not df_supuestos.empty and "Variable" in df_supuestos.columns and "Valor editable" in df_supuestos.columns:
        for _, row in df_supuestos.iterrows():
            var_name = str(row["Variable"]).strip()
            try:
                supuestos_map[var_name] = float(row["Valor editable"])
            except (ValueError, TypeError):
                pass

    meses_por_anio = supuestos_map.get("Meses por año", 12.0)
    trm_cop = supuestos_map.get("TRM usada en el escenario", 4050.0)
    cap_servidor = supuestos_map.get("Capacidad por servidor", 1000.0)
    servidor_aws_usd = supuestos_map.get("Servidor AWS", 25.0)
    backup_base_gb = supuestos_map.get("Copia de seguridad inicial", 50.0)
    backup_gb_usuario = supuestos_map.get("Almacenamiento por usuario", 0.03)
    costo_backup_usd = supuestos_map.get("Costo backup", 0.055)
    cuentas_workspace = supuestos_map.get("Cuentas Workspace", 2.0)
    costo_workspace_usd = supuestos_map.get("Costo Workspace", 8.5)
    licencia_n8n_cop = supuestos_map.get("Licencia n8n community", 0.0)
    costo_msg_telegram = supuestos_map.get("Costo por mensaje Telegram", 0.0)
    comision_pct_mp = supuestos_map.get("Comisión porcentual pasarela", 0.029)
    comision_fija_mp = supuestos_map.get("Comisión fija pasarela", 750.0)
    iva_comision_mp = supuestos_map.get("IVA comisión", 0.19)
    soporte_gratis_cop = supuestos_map.get("Soporte plataforma usuario gratis", 90.0)
    soporte_plus_cop = supuestos_map.get("Soporte plataforma usuario Plus", 165.0)
    costo_deuda_cop = supuestos_map.get("Procesamiento deuda activa", 28.0)
    personal_mes_cop = supuestos_map.get("Equipo humano y operación", 2800000.0)
    admin_mes_cop = supuestos_map.get("Administración y herramientas", 350000.0)

    # Precios oficiales desde la hoja 'Tarifas' (con respaldo del modelo comercial de Ceroa)
    precio_plus_mensual = 29900.0
    precio_plus_anual = 299000.0
    if not df_tarifas.empty and "Plan" in df_tarifas.columns:
        for _, row in df_tarifas.iterrows():
            plan_nom = str(row["Plan"]).strip()
            if plan_nom == "Plus mensual" and "Precio mensual (COP)" in df_tarifas.columns:
                try:
                    precio_plus_mensual = float(row["Precio mensual (COP)"])
                except (ValueError, TypeError):
                    pass
            elif plan_nom == "Plus anual" and "Precio anual (COP)" in df_tarifas.columns:
                try:
                    precio_plus_anual = float(row["Precio anual (COP)"])
                except (ValueError, TypeError):
                    pass
    mrr_plus_anual = precio_plus_anual / meses_por_anio  # $299.000 / 12 = $24.916,67 COP

    # 4. Normalización numérica y conversión de fechas
    df_usuarios_mes = _normalizar_numerico(
        df_usuarios_mes,
        [
            "edad", "deudas_activas", "deudas_pagadas_acumuladas",
            "saldo_deudas_fin_mes_cop", "abonos_deudas_mes_cop",
            "cantidad_abonos_mes", "mrr_equivalente_cop", "antiguedad_meses"
        ],
    )
    df_actividad = _normalizar_numerico(
        df_actividad,
        [
            "usuarios_nuevos", "usuarios_activos", "usuarios_gratis",
            "plus_mensual_activos", "plus_anual_activos", "usuarios_plus",
            "deudas_activas", "saldo_deudas_administradas_cop",
            "abonos_a_acreedores_cop", "cobros_aprobados", "cobros_rechazados",
            "recaudo_ceroa_cop", "inversion_marketing_cop", "altas_plus",
            "bajas_plus", "mensajes_estimados", "sesiones_estimadas", "visitas_estimadas"
        ],
    )
    df_cobros = _normalizar_numerico(df_cobros, ["intento", "importe_cop"])
    df_deudas = _normalizar_numerico(
        df_deudas,
        ["capital_inicial_cop", "tasa_efectiva_anual", "tasa_mensual_efectiva", "cuota_referencia_cop", "saldo_final_cop"],
    )
    df_abonos = _normalizar_numerico(
        df_abonos,
        ["pago_credito_cop", "intereses_pagados_cop", "abono_capital_cop", "saldo_credito_pospago_cop"],
    )
    df_adquisicion = _normalizar_numerico(
        df_adquisicion,
        ["usuarios_nuevos", "inversion_marketing_cop", "impresiones", "visitas"],
    )

    # Conversión estandarizada de fechas
    df_cobros["fecha_transaccion"] = pd.to_datetime(df_cobros["fecha_transaccion"], errors="coerce")
    df_suscripciones["fecha_inicio"] = pd.to_datetime(df_suscripciones["fecha_inicio"], errors="coerce")
    df_suscripciones["ultimo_mes_en_plan"] = pd.to_datetime(df_suscripciones["ultimo_mes_en_plan"], errors="coerce")
    df_deudas["fecha_apertura"] = pd.to_datetime(df_deudas["fecha_apertura"], errors="coerce")
    df_abonos["fecha_abono"] = pd.to_datetime(df_abonos["fecha_abono"], errors="coerce")
    df_usuarios_mes["Fecha_Mes"] = pd.to_datetime(df_usuarios_mes["mes"] + "-01", errors="coerce")
    df_actividad["Fecha_Mes"] = pd.to_datetime(df_actividad["mes"] + "-01", errors="coerce")

    # 5. Validaciones financieras sobre MRR por usuario-mes
    # - Plan Cero: $0 COP
    # - Plan Plus mensual: $29.900 COP
    # - Plan Plus anual: $299.000 / 12 COP
    df_usuarios_mes["mrr_equivalente_cop"] = 0.0
    df_usuarios_mes.loc[df_usuarios_mes["plan"] == "Plus mensual", "mrr_equivalente_cop"] = precio_plus_mensual
    df_usuarios_mes.loc[df_usuarios_mes["plan"] == "Plus anual", "mrr_equivalente_cop"] = mrr_plus_anual

    # Enriquecer cobros con la ciudad del usuario (mapa único usuario_id -> ciudad)
    mapa_ciudad = (
        df_usuarios_mes[["usuario_id", "ciudad"]]
        .drop_duplicates(subset=["usuario_id"])
        .set_index("usuario_id")["ciudad"]
        .to_dict()
    )
    df_cobros["ciudad"] = df_cobros["usuario_id"].map(mapa_ciudad).fillna("Sin ciudad")

    # 6. Reproducción exacta de la hoja 'Finanzas_Mes' usando 'Supuestos' y 'Actividad_Mensual'
    # Auditoría de recaudo efectivo: exclusivamente transacciones con estado == 'Aprobado'
    cobros_aprob_mes = (
        df_cobros[df_cobros["estado"] == "Aprobado"]
        .groupby("mes")
        .agg(
            cobros_aprobados_audit=("transaccion_id", "count"),
            recaudo_aprobado_cop=("importe_cop", "sum"),
        )
        .reset_index()
    )

    df_finanzas = df_actividad.sort_values("mes").copy()
    df_finanzas = df_finanzas.merge(cobros_aprob_mes, on="mes", how="left")
    df_finanzas["recaudo_cop"] = df_finanzas["recaudo_aprobado_cop"].fillna(df_finanzas["recaudo_ceroa_cop"])
    df_finanzas["cobros_aprobados_calc"] = df_finanzas["cobros_aprobados_audit"].fillna(df_finanzas["cobros_aprobados"])

    # Ingresos recurrentes (MRR) e Ingresos devengados del período
    df_finanzas["mrr_cop"] = (
        df_finanzas["plus_mensual_activos"] * precio_plus_mensual
        + df_finanzas["plus_anual_activos"] * mrr_plus_anual
    )
    df_finanzas["ingreso_devengado_cop"] = df_finanzas["mrr_cop"]

    # Cálculo detallado de COGS (Costos Directos) según 'Supuestos' e 'Insumos'
    df_finanzas["aws_cop"] = (
        df_finanzas["usuarios_activos"].apply(lambda u: math.ceil(u / cap_servidor) if u > 0 else 0)
        * servidor_aws_usd
        * trm_cop
    )
    df_finanzas["backup_cop"] = (
        (backup_base_gb + df_finanzas["usuarios_activos"] * backup_gb_usuario)
        * costo_backup_usd
        * trm_cop
    )
    df_finanzas["costo_soporte_cop"] = (
        df_finanzas["usuarios_gratis"] * soporte_gratis_cop
        + df_finanzas["usuarios_plus"] * soporte_plus_cop
    )
    df_finanzas["costo_deudas_cop"] = df_finanzas["deudas_activas"] * costo_deuda_cop
    df_finanzas["telegram_cop"] = df_finanzas.get("mensajes_estimados", 0.0) * costo_msg_telegram
    df_finanzas["comision_mp_cop"] = (
        (df_finanzas["recaudo_cop"] * comision_pct_mp + df_finanzas["cobros_aprobados_calc"] * comision_fija_mp)
        * (1.0 + iva_comision_mp)
    )
    df_finanzas["cogs_total_cop"] = (
        df_finanzas["aws_cop"]
        + df_finanzas["backup_cop"]
        + df_finanzas["costo_soporte_cop"]
        + df_finanzas["costo_deudas_cop"]
        + df_finanzas["telegram_cop"]
        + df_finanzas["comision_mp_cop"]
    )

    # Margen Bruto sobre ingresos devengados del mismo período (no sobre cobro anual anticipado)
    df_finanzas["margen_bruto_cop"] = df_finanzas["ingreso_devengado_cop"] - df_finanzas["cogs_total_cop"]
    df_finanzas["margen_bruto_pct"] = df_finanzas.apply(
        lambda r: (r["margen_bruto_cop"] / r["ingreso_devengado_cop"] * 100.0) if r["ingreso_devengado_cop"] > 0 else 0.0,
        axis=1,
    )

    # Cálculo de OPEX y Resultado Operativo (EBIT)
    df_finanzas["workspace_cop"] = cuentas_workspace * costo_workspace_usd * trm_cop
    df_finanzas["n8n_cop"] = licencia_n8n_cop
    df_finanzas["personal_cop"] = personal_mes_cop
    df_finanzas["administracion_cop"] = admin_mes_cop
    df_finanzas["marketing_cop"] = df_finanzas["inversion_marketing_cop"]
    df_finanzas["opex_total_cop"] = (
        df_finanzas["workspace_cop"]
        + df_finanzas["n8n_cop"]
        + df_finanzas["personal_cop"]
        + df_finanzas["administracion_cop"]
        + df_finanzas["marketing_cop"]
    )
    df_finanzas["resultado_operativo_cop"] = df_finanzas["margen_bruto_cop"] - df_finanzas["opex_total_cop"]

    # Indicadores unitarios complementarios (Conversión a Plus, CAC, Churn Plus)
    df_finanzas["conversion_a_plus_pct"] = df_finanzas.apply(
        lambda r: (r["usuarios_plus"] / r["usuarios_activos"] * 100.0) if r["usuarios_activos"] > 0 else 0.0,
        axis=1,
    )
    df_finanzas["cac_altas_plus_cop"] = df_finanzas.apply(
        lambda r: (r["marketing_cop"] / r["altas_plus"]) if r["altas_plus"] > 0 else 0.0,
        axis=1,
    )
    df_finanzas["churn_plus_pct"] = df_finanzas.apply(
        lambda r: (
            r.get("bajas_plus", 0.0)
            / (r["usuarios_plus"] - r["altas_plus"] + r.get("bajas_plus", 0.0))
            * 100.0
        )
        if (r["usuarios_plus"] - r["altas_plus"] + r.get("bajas_plus", 0.0)) > 0
        else 0.0,
        axis=1,
    )

    return {
        "usuarios_mes": df_usuarios_mes,
        "actividad": df_actividad,
        "finanzas": df_finanzas,
        "cobros": df_cobros,
        "suscripciones": df_suscripciones,
        "deudas": df_deudas,
        "abonos": df_abonos,
        "adquisicion": df_adquisicion,
        "tarifas": df_tarifas,
        "supuestos": df_supuestos,
        "proveedores": df_proveedores,
        "insumos": df_insumos,
    }


try:
    datos = cargar_datos()
    df_raw = datos["usuarios_mes"]
    df_finanzas_raw = datos["finanzas"]
    df_cobros_raw = datos["cobros"]
    df_proveedores_raw = datos["proveedores"]
    df_insumos_raw = datos["insumos"]
except FileNotFoundError as e:
    st.error(f"Error Crítico de Archivo: {e}")
    st.info(
        "Consejo: Asegúrate de que la carpeta 'datos/' con los archivos CSV completos "
        "y el archivo 'Ceroa_Base_Datos_Recalculada.xlsx' estén en la misma carpeta que este script."
    )
    st.stop()
except KeyError as e:
    st.error(f"Error en estructura de datos: {e}")
    st.info(
        "Consejo: Verifica que los archivos CSV en 'datos/' conserven sus cabeceras originales "
        "(mes, usuario_id, plan, ciudad, deudas_activas, saldo_deudas_fin_mes_cop, abonos_deudas_mes_cop, mrr_equivalente_cop)."
    )
    st.stop()
except Exception as e:
    st.error(f"Error inesperado al procesar los datos: {e}")
    st.stop()

# ==============================================================================
# BARRA LATERAL: FILTROS DE CONTROL MULTIDIMENSIONAL
# ==============================================================================
vista = st.sidebar.radio("Vista", ["Histórico", "Simulador a 3 años"])
if vista == "Simulador a 3 años":
    from simulador_ceroa import mostrar_simulador
    mostrar_simulador(datos)
    st.stop()

st.sidebar.header("Filtros")

meses_lista = sorted(df_raw["mes"].dropna().unique().tolist())

# Filtro 1: Período de análisis
opciones_periodo = (
    ["Todos (Ene 2025 - Sep 2026)", "Año 2025", "Año 2026"]
    + meses_lista
)
filtro_periodo = st.sidebar.selectbox("Período", opciones_periodo)

# Filtro 2: Tipo de Plan comercial
planes_disponibles = ["Todos", "Cero", "Plus mensual", "Plus anual"]
filtro_plan = st.sidebar.selectbox("Plan", planes_disponibles)

# Filtro 3: Ciudad (complemento geográfico)
ciudades_disponibles = ["Todas"] + sorted(df_raw["ciudad"].dropna().unique().tolist())
filtro_ciudad = st.sidebar.selectbox("Ciudad", ciudades_disponibles)

# Determinación de los meses incluidos en el período seleccionado
if filtro_periodo == "Todos (Ene 2025 - Sep 2026)":
    meses_seleccionados = meses_lista
elif filtro_periodo == "Año 2025":
    meses_seleccionados = [m for m in meses_lista if m.startswith("2025")]
elif filtro_periodo == "Año 2026":
    meses_seleccionados = [m for m in meses_lista if m.startswith("2026")]
else:
    meses_seleccionados = [filtro_periodo]

ultimo_mes_periodo = max(meses_seleccionados)

# Aplicación de filtros sobre la tabla de usuarios-mes y cobros
df_filtrado = df_raw[df_raw["mes"].isin(meses_seleccionados)].copy()
df_finanzas_periodo = df_finanzas_raw[df_finanzas_raw["mes"].isin(meses_seleccionados)].copy()
df_cobros_filtrado = df_cobros_raw[df_cobros_raw["mes"].isin(meses_seleccionados)].copy()

if filtro_plan != "Todos":
    df_filtrado = df_filtrado[df_filtrado["plan"] == filtro_plan]
    if filtro_plan == "Cero":
        # Los usuarios del plan gratuito Cero no generan cobros de suscripción
        df_cobros_filtrado = df_cobros_filtrado.iloc[0:0]
    else:
        df_cobros_filtrado = df_cobros_filtrado[df_cobros_filtrado["plan_solicitado"] == filtro_plan]

if filtro_ciudad != "Todas":
    df_filtrado = df_filtrado[df_filtrado["ciudad"] == filtro_ciudad]
    df_cobros_filtrado = df_cobros_filtrado[df_cobros_filtrado["ciudad"] == filtro_ciudad]

# Corte al cierre del período seleccionado para evitar duplicar usuarios o saldos entre meses
df_cierre_filtrado = df_filtrado[df_filtrado["mes"] == ultimo_mes_periodo].drop_duplicates(
    subset=["usuario_id"], keep="last"
)

hay_segmentacion = (filtro_plan != "Todos") or (filtro_ciudad != "Todas")

st.sidebar.info(
    f"**Cierre del período:** {ultimo_mes_periodo}\n\n"
    f"**Usuarios únicos al cierre:** {df_cierre_filtrado['usuario_id'].nunique():,}\n\n"
    f"**Registros usuario-mes filtrados:** {len(df_filtrado):,} de {len(df_raw):,}"
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Modelo Comercial Ceroa:**\n"
    "- **Plan Cero:** Gratuito (hasta 2 deudas)\n"
    "- **Ceroa Plus Mensual:** $29.900 COP\n"
    "- **Ceroa Plus Anual:** $299.000 COP ($24.917/mes)"
)

# ==============================================================================
# SECCIÓN 1: INDICADORES CLAVE DE GESTIÓN (C-SUITE SCORECARDS)
# ==============================================================================
st.subheader("Indicadores del período")

if hay_segmentacion:
    st.caption(
        "ℹ**Nota metodológica:** *MRR*, *Recaudo* y *Usuarios Activos* reflejan el segmento seleccionado "
        f"(`Plan: {filtro_plan}` | `Ciudad: {filtro_ciudad}`). Los indicadores de *COGS*, *Margen Bruto*, "
        "*CAC* y *Resultado Operativo* se mantienen **globales para el período** ya que la infraestructura AWS, "
        "backups, soporte, OPEX e inversión de marketing son costos compartidos de toda la operación."
    )

# 1. MRR al cierre del período seleccionado
mrr_cierre = df_cierre_filtrado["mrr_equivalente_cop"].sum()

# 2. Recaudo efectivo (exclusivamente transacciones con estado == 'Aprobado')
df_cobros_aprobados = df_cobros_filtrado[df_cobros_filtrado["estado"] == "Aprobado"]
recaudo_efectivo = df_cobros_aprobados["importe_cop"].sum()
total_tx_aprobadas = len(df_cobros_aprobados)

# 3. COGS Directo y 4. Margen Bruto (globales del período sobre ingresos devengados compatibles)
ingresos_devengados_periodo = df_finanzas_periodo["ingreso_devengado_cop"].sum()
cogs_total_periodo = df_finanzas_periodo["cogs_total_cop"].sum()
margen_bruto_cop = ingresos_devengados_periodo - cogs_total_periodo
margen_bruto_pct = (
    (margen_bruto_cop / ingresos_devengados_periodo * 100.0)
    if ingresos_devengados_periodo > 0
    else 0.0
)

# 5. Usuarios activos únicos al cierre del período (diferenciando gratuitos y Plus)
usuarios_activos_cierre = df_cierre_filtrado["usuario_id"].nunique()
usuarios_gratis_cierre = df_cierre_filtrado[df_cierre_filtrado["plan"] == "Cero"]["usuario_id"].nunique()
usuarios_plus_cierre = df_cierre_filtrado[
    df_cierre_filtrado["plan"].isin(["Plus mensual", "Plus anual"])
]["usuario_id"].nunique()

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    f"MRR ({ultimo_mes_periodo})",
    f"${mrr_cierre:,.0f} COP",
    delta=f"ARR equiv.: ${mrr_cierre * 12:,.0f} COP",
)
c2.metric(
    "Recaudo Efectivo",
    f"${recaudo_efectivo:,.0f} COP",
    delta=f"{total_tx_aprobadas:,} cobros aprobados",
)
c3.metric(
    "COGS Directo (Global)",
    f"${cogs_total_periodo:,.0f} COP",
    delta=f"{(cogs_total_periodo / ingresos_devengados_periodo * 100.0) if ingresos_devengados_periodo > 0 else 0.0:.1f}% del devengado",
    delta_color="inverse",
)
c4.metric(
    "Margen Bruto (Global)",
    f"${margen_bruto_cop:,.0f} COP",
    delta=f"{margen_bruto_pct:.1f}% sobre devengado",
)
c5.metric(
    f"Usuarios Activos ({ultimo_mes_periodo})",
    f"{usuarios_activos_cierre:,}",
    delta=f"{usuarios_gratis_cierre:,} Cero | {usuarios_plus_cierre:,} Plus",
)

# Métricas ejecutivas complementarias: Conversión a Plus, Churn Plus, CAC y Resultado Operativo
conversion_plus_cierre = (
    (usuarios_plus_cierre / usuarios_activos_cierre * 100.0)
    if usuarios_activos_cierre > 0
    else 0.0
)
fila_finanzas_cierre = df_finanzas_raw[df_finanzas_raw["mes"] == ultimo_mes_periodo].iloc[0]
churn_cierre_pct = float(fila_finanzas_cierre["churn_plus_pct"])
churn_promedio_pct = df_finanzas_periodo["churn_plus_pct"].mean()

marketing_periodo = df_finanzas_periodo["marketing_cop"].sum()
altas_plus_periodo = df_finanzas_periodo["altas_plus"].sum()
cac_periodo_cop = (marketing_periodo / altas_plus_periodo) if altas_plus_periodo > 0 else 0.0

opex_periodo_cop = df_finanzas_periodo["opex_total_cop"].sum()
resultado_operativo_cop = df_finanzas_periodo["resultado_operativo_cop"].sum()
resultado_cierre_cop = float(fila_finanzas_cierre["resultado_operativo_cop"])

# Cálculos de TCO (Total Cost of Ownership) y ROI (Return on Investment)
tco_periodo_cop = cogs_total_periodo + opex_periodo_cop
tco_cierre_cop = float(fila_finanzas_cierre["cogs_total_cop"] + fila_finanzas_cierre["opex_total_cop"])

# Costo directo de proveedores tecnológicos y operativos (COGS + Google Workspace + Herramientas)
costo_ti_periodo_cop = (
    cogs_total_periodo
    + df_finanzas_periodo["workspace_cop"].sum()
    + df_finanzas_periodo["administracion_cop"].sum()
)

# ROI Operativo sobre Recaudo Efectivo (Flujo de Caja) y sobre Ingreso Devengado
beneficio_neto_caja_cop = recaudo_efectivo - tco_periodo_cop
roi_caja_periodo_pct = ((recaudo_efectivo - tco_periodo_cop) / tco_periodo_cop * 100.0) if tco_periodo_cop > 0 else 0.0
roi_devengado_periodo_pct = (resultado_operativo_cop / tco_periodo_cop * 100.0) if tco_periodo_cop > 0 else 0.0
roi_cierre_devengado_pct = (resultado_cierre_cop / tco_cierre_cop * 100.0) if tco_cierre_cop > 0 else 0.0
roi_ti_periodo_pct = (
    ((ingresos_devengados_periodo - costo_ti_periodo_cop) / costo_ti_periodo_cop * 100.0)
    if costo_ti_periodo_cop > 0
    else 0.0
)

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric(
    f"Conversión a Plus ({ultimo_mes_periodo})",
    f"{conversion_plus_cierre:.1f}%",
    delta=f"{usuarios_plus_cierre:,} suscriptores pagos",
)
k2.metric(
    f"Churn Plus ({ultimo_mes_periodo})",
    f"{churn_cierre_pct:.2f}%",
    delta=f"Promedio período: {churn_promedio_pct:.2f}%",
    delta_color="inverse",
)
k3.metric(
    "CAC por Alta Plus (Global)",
    f"${cac_periodo_cop:,.0f} COP",
    delta=f"{int(altas_plus_periodo):,} altas Plus en el período",
)
k4.metric(
    f"Resultado Operativo ({ultimo_mes_periodo})",
    f"${resultado_cierre_cop:,.0f} COP",
    delta=f"Acumulado: ${resultado_operativo_cop:,.0f} COP",
)
k5.metric(
    "ROI Efectivo (Recaudo vs. TCO)",
    f"{roi_caja_periodo_pct:.1f}%",
    delta=f"ROI Cierre ({ultimo_mes_periodo}): {roi_cierre_devengado_pct:.1f}%",
)

st.markdown("---")

# ==============================================================================
# SECCIÓN 2: ANÁLISIS VISUAL DE RENDIMIENTO
# ==============================================================================
st.subheader("Evolución del negocio")
st.caption("Pasa el cursor por un punto para ver su valor. Haz clic en una leyenda para mostrar u ocultar una serie.")
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    # Gráfico 1: Evolución financiera mensual (MRR vs Recaudo Efectivo)
    mrr_mensual_seg = (
        df_filtrado.groupby("mes")["mrr_equivalente_cop"]
        .sum()
        .reindex(meses_seleccionados, fill_value=0.0)
        .reset_index()
    )
    recaudo_mensual_seg = (
        df_cobros_aprobados.groupby("mes")["importe_cop"]
        .sum()
        .reindex(meses_seleccionados, fill_value=0.0)
        .reset_index()
    )
    df_tiempo = mrr_mensual_seg.merge(recaudo_mensual_seg, on="mes", how="left").rename(
        columns={
            "mrr_equivalente_cop": "Ingreso mensual (MRR)",
            "importe_cop": "Recaudo aprobado",
        }
    )

    fig_temporal = px.line(
        df_tiempo,
        x="mes",
        y=["Ingreso mensual (MRR)", "Recaudo aprobado"],
        title="Ingresos y recaudo mensual",
        markers=True,
        labels={
            "mes": "Mes de Operación",
            "value": "Monto (COP)",
            "variable": "Indicador Financiero",
        },
        color_discrete_map={
            "Ingreso mensual (MRR)": "#0284C7",
            "Recaudo aprobado": "#10B981",
        },
    )
    fig_temporal.update_traces(line_width=3)
    fig_temporal.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.22))
    mostrar_grafica(fig_temporal)

with col_graf2:
    # Gráfico 2: Distribución de usuarios únicos activos por plan al cierre del período
    orden_planes = ["Cero", "Plus mensual", "Plus anual"]
    conteo_planes = (
        df_cierre_filtrado.groupby("plan")["usuario_id"]
        .nunique()
        .reindex(orden_planes, fill_value=0)
        .reset_index()
        .rename(columns={"usuario_id": "Usuarios_Unicos_Activos"})
    )

    fig_planes = px.bar(
        conteo_planes,
        x="plan",
        y="Usuarios_Unicos_Activos",
        color="plan",
        text_auto=True,
        title=f"Usuarios por plan · {ultimo_mes_periodo}",
        labels={"plan": "Modalidad de Plan", "Usuarios_Unicos_Activos": "Usuarios Únicos Activos"},
        color_discrete_map={
            "Cero": "#64748B",
            "Plus mensual": "#0284C7",
            "Plus anual": "#4F46E5",
        },
    )
    fig_planes.update_layout(showlegend=False)
    mostrar_grafica(fig_planes, tipo="usuarios")

# Segunda fila de gráficos complementarios: Costos por proveedor y Evolución de deudas administradas
col_graf3, col_graf4 = st.columns(2)

with col_graf3:
    df_costos_prov = pd.DataFrame(
        [
            {
                "Proveedor / Rubro": "Mercado Pago",
                "Tipo": "Costos directos",
                "Costo_COP": df_finanzas_periodo["comision_mp_cop"].sum(),
            },
            {
                "Proveedor / Rubro": "AWS y backups",
                "Tipo": "Costos directos",
                "Costo_COP": (
                    df_finanzas_periodo["aws_cop"].sum() + df_finanzas_periodo["backup_cop"].sum()
                ),
            },
            {
                "Proveedor / Rubro": "Soporte y deudas",
                "Tipo": "Costos directos",
                "Costo_COP": (
                    df_finanzas_periodo["costo_soporte_cop"].sum()
                    + df_finanzas_periodo["costo_deudas_cop"].sum()
                ),
            },
            {
                "Proveedor / Rubro": "Google Workspace",
                "Tipo": "Gastos operativos",
                "Costo_COP": df_finanzas_periodo["workspace_cop"].sum(),
            },
            {
                "Proveedor / Rubro": "Telegram",
                "Tipo": "Costos directos",
                "Costo_COP": df_finanzas_periodo["telegram_cop"].sum(),
            },
        ]
    )

    fig_costos = px.bar(
        df_costos_prov,
        x="Proveedor / Rubro",
        y="Costo_COP",
        color="Tipo",
        text_auto=",.0f",
        title="Costos por proveedor",
        labels={"Proveedor / Rubro": "Proveedor / Concepto", "Costo_COP": "Costo Acumulado (COP)"},
    )
    fig_costos.update_layout(legend=dict(orientation="h", y=-0.25))
    st.caption("Costos globales del período; no cambian al filtrar por plan o ciudad.")
    mostrar_grafica(fig_costos)

with col_graf4:
    df_cartera_mes = (
        df_filtrado.groupby("mes")
        .agg(
            Saldo_Deudas_Fin_Mes_COP=("saldo_deudas_fin_mes_cop", "sum"),
            Abonos_Acreedores_Mes_COP=("abonos_deudas_mes_cop", "sum"),
        )
        .reindex(meses_seleccionados, fill_value=0.0)
        .reset_index()
        .rename(
            columns={
                "Saldo_Deudas_Fin_Mes_COP": "Saldo de deudas",
                "Abonos_Acreedores_Mes_COP": "Abonos a acreedores",
            }
        )
    )

    fig_deudas = px.line(
        df_cartera_mes,
        x="mes",
        y=[
            "Saldo de deudas",
            "Abonos a acreedores",
        ],
        markers=True,
        title="Deudas y abonos mensuales",
        labels={
            "mes": "Mes de Operación",
            "value": "Monto (COP)",
            "variable": "Métrica de Cartera de Usuarios",
        },
        color_discrete_map={
            "Saldo de deudas": "#F59E0B",
            "Abonos a acreedores": "#8B5CF6",
        },
    )
    fig_deudas.update_traces(line_width=3)
    fig_deudas.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.25))
    st.caption("El saldo corresponde al cierre de cada mes. Los abonos a acreedores no son ingresos de Ceroa.")
    mostrar_grafica(fig_deudas)

st.markdown("---")

# ==============================================================================
# SECCIÓN 2.5: ANÁLISIS DE TCO, ROI, CURVA DE PAYBACK Y EVALUACIÓN DE PROVEEDORES
# ==============================================================================
st.subheader("Inversión y rentabilidad")
st.caption("Los costos y las curvas acumuladas son globales del período. El ROI de caja compara el recaudo filtrado con los costos globales.")
st.write(
    "Evaluación financiera del Costo Total de Propiedad (**TCO = COGS + OPEX**) frente a los ingresos "
    "generados por las suscripciones de Ceroa, junto con el simulador multianual de retorno (**ROI**)."
)

r1, r2, r3, r4 = st.columns(4)
r1.metric(
    label="TCO Consolidado del Período",
    value=f"${tco_periodo_cop:,.0f} COP",
    delta=f"COGS: ${cogs_total_periodo:,.0f} | OPEX: ${opex_periodo_cop:,.0f}",
    delta_color="off",
)
r2.metric(
    label="Beneficio Neto en Caja (Recaudo - TCO)",
    value=f"${beneficio_neto_caja_cop:,.0f} COP",
    delta="Superávit de Caja" if beneficio_neto_caja_cop >= 0 else "En Fase de Inversión",
)
r3.metric(
    label="ROI sobre Flujo de Caja (Recaudo vs. TCO)",
    value=f"{roi_caja_periodo_pct:.1f}%",
    delta=f"ROI Devengado Período: {roi_devengado_periodo_pct:.1f}%",
)
r4.metric(
    label="ROI Infraestructura y Proveedores TI",
    value=f"{roi_ti_periodo_pct:.1f}%",
    delta=f"Cierre ({ultimo_mes_periodo}) ROI Global: {roi_cierre_devengado_pct:.1f}%",
)

col_payback, col_donut = st.columns([3, 2])

with col_payback:
    # Curva de Payback Mensual Acumulada: TCO Acumulado vs. Recaudo e Ingreso Devengado Acumulado
    df_payback = df_finanzas_periodo[["mes", "recaudo_cop", "ingreso_devengado_cop", "cogs_total_cop", "opex_total_cop"]].copy()
    df_payback["TCO_Mes_COP"] = df_payback["cogs_total_cop"] + df_payback["opex_total_cop"]
    df_payback["Costo total acumulado"] = df_payback["TCO_Mes_COP"].cumsum()
    df_payback["Recaudo acumulado"] = df_payback["recaudo_cop"].cumsum()
    df_payback["Ingreso acumulado"] = df_payback["ingreso_devengado_cop"].cumsum()

    fig_payback = px.line(
        df_payback,
        x="mes",
        y=[
            "Costo total acumulado",
            "Recaudo acumulado",
            "Ingreso acumulado",
        ],
        markers=True,
        title="Recuperación de la inversión",
        labels={
            "mes": "Mes de Operación",
            "value": "Pesos Colombianos (COP)",
            "variable": "Línea Financiera",
        },
        color_discrete_map={
            "Costo total acumulado": "#EF4444",
            "Recaudo acumulado": "#10B981",
            "Ingreso acumulado": "#0284C7",
        },
    )
    fig_payback.update_traces(line_width=3)
    fig_payback.update_layout(hovermode="x unified", legend=dict(orientation="h", y=-0.25))
    mostrar_grafica(fig_payback)

with col_donut:
    # Gráfico de torta/anillo: Composición del TCO por categoría contable
    df_composicion_tco = pd.DataFrame(
        [
            {"Categoría": "Pasarela de pagos", "Monto_COP": df_finanzas_periodo["comision_mp_cop"].sum()},
            {"Categoría": "COGS: AWS y backups", "Monto_COP": df_finanzas_periodo["aws_cop"].sum() + df_finanzas_periodo["backup_cop"].sum()},
            {"Categoría": "Soporte y deudas", "Monto_COP": df_finanzas_periodo["costo_soporte_cop"].sum() + df_finanzas_periodo["costo_deudas_cop"].sum()},
            {"Categoría": "Marketing", "Monto_COP": df_finanzas_periodo["marketing_cop"].sum()},
            {"Categoría": "Equipo y operación", "Monto_COP": df_finanzas_periodo["personal_cop"].sum()},
            {"Categoría": "Administración", "Monto_COP": df_finanzas_periodo["administracion_cop"].sum() + df_finanzas_periodo["workspace_cop"].sum()},
        ]
    )
    fig_donut = px.pie(
        df_composicion_tco,
        names="Categoría",
        values="Monto_COP",
        title="Distribución del costo total",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Safe,
    )
    fig_donut.update_layout(legend=dict(orientation="h", y=-0.25))
    mostrar_grafica(fig_donut)
    with st.expander("Ver categorías y valores"): 
        st.dataframe(df_composicion_tco.rename(columns={"Monto_COP": "Monto (COP)"}), hide_index=True, width="stretch")

# Tabla de desglose anual / por período de TCO y ROI
resumen_periodos = []
for etiqueta_p, filtro_p in [
    ("Año 2025 (Ene - Dic 2025)", df_finanzas_raw[df_finanzas_raw["mes"].str.startswith("2025")]),
    ("Año 2026 (Ene - Sep 2026)", df_finanzas_raw[df_finanzas_raw["mes"].str.startswith("2026")]),
    ("Consolidado Total (21 Meses)", df_finanzas_raw),
]:
    if filtro_p.empty:
        continue
    u_cierre_p = int(filtro_p.iloc[-1]["usuarios_activos"])
    plus_cierre_p = int(filtro_p.iloc[-1]["usuarios_plus"])
    dev_p = filtro_p["ingreso_devengado_cop"].sum()
    rec_p = filtro_p["recaudo_cop"].sum()
    cogs_p = filtro_p["cogs_total_cop"].sum()
    opex_p = filtro_p["opex_total_cop"].sum()
    tco_p = cogs_p + opex_p
    util_caja_p = rec_p - tco_p
    util_dev_p = dev_p - tco_p
    roi_caja_p = (util_caja_p / tco_p * 100.0) if tco_p > 0 else 0.0
    roi_dev_p = (util_dev_p / tco_p * 100.0) if tco_p > 0 else 0.0
    resumen_periodos.append(
        {
            "Período Fiscal": etiqueta_p,
            "Usuarios Activos (Cierre)": f"{u_cierre_p:,} ({plus_cierre_p:,} Plus)",
            "COGS Directo (COP)": f"${cogs_p:,.0f}",
            "OPEX Operativo (COP)": f"${opex_p:,.0f}",
            "TCO Total (COGS + OPEX)": f"${tco_p:,.0f}",
            "Ingreso Devengado (COP)": f"${dev_p:,.0f}",
            "Recaudo Efectivo (COP)": f"${rec_p:,.0f}",
            "Beneficio Neto Caja (COP)": f"${util_caja_p:,.0f}",
            "ROI Flujo de Caja (%)": f"{roi_caja_p:.1f}%",
            "ROI Devengado (%)": f"{roi_dev_p:.1f}%",
        }
    )

st.markdown("**Resumen Ejecutivo de Inversión (TCO), Ingresos y Retorno (ROI) por Etapa:**")
st.dataframe(pd.DataFrame(resumen_periodos), width="stretch", hide_index=True)

st.markdown("---")

# ==============================================================================
# SECCIÓN 3: EXPLORADOR DE REGISTROS Y CATÁLOGO DE PROVEEDORES / INSUMOS
# ==============================================================================
st.subheader("Detalle de usuarios y suscripciones")

columnas_mostrar = [
    "usuario_id",
    "mes",
    "plan",
    "tipo_plan",
    "ciudad",
    "deudas_activas",
    "saldo_deudas_fin_mes_cop",
    "abonos_deudas_mes_cop",
    "mrr_equivalente_cop",
]
columnas_existentes = [col for col in columnas_mostrar if col in df_filtrado.columns]

df_tabla_exploracion = df_filtrado[columnas_existentes].rename(
    columns={
        "usuario_id": "ID Usuario",
        "mes": "Mes",
        "plan": "Plan",
        "tipo_plan": "Tipo de Plan",
        "ciudad": "Ciudad",
        "deudas_activas": "Deudas Activas",
        "saldo_deudas_fin_mes_cop": "Saldo de Deudas (COP)",
        "abonos_deudas_mes_cop": "Abonos del Mes a Acreedores (COP)",
        "mrr_equivalente_cop": "MRR Equivalente Ceroa (COP)",
    }
)

st.dataframe(
    df_tabla_exploracion,
    width="stretch",
    hide_index=True,
)

st.markdown("---")
st.subheader("Proveedores y servicios")

if not df_insumos_raw.empty and not df_proveedores_raw.empty:
    df_catalogo_prov = df_insumos_raw.merge(
        df_proveedores_raw[["proveedor_id", "nombre_proveedor", "funcion", "moneda_de_referencia"]],
        on="proveedor_id",
        how="left",
    )
    cols_cat = [
        "insumo_id",
        "nombre_proveedor",
        "nombre_insumo",
        "categoria",
        "modelo_costo",
        "unidad",
        "clasificacion",
        "moneda_de_referencia",
        "nota",
    ]
    cols_cat_existentes = [c for c in cols_cat if c in df_catalogo_prov.columns]
    st.dataframe(
        df_catalogo_prov[cols_cat_existentes].rename(
            columns={
                "insumo_id": "ID Insumo",
                "nombre_proveedor": "Proveedor",
                "nombre_insumo": "Insumo / Servicio",
                "categoria": "Categoría",
                "modelo_costo": "Modelo de Costo",
                "unidad": "Unidad de Cobro",
                "clasificacion": "Clasificación Contable",
                "moneda_de_referencia": "Moneda Base",
                "nota": "Nota Metodológica",
            }
        ),
        width="stretch",
        hide_index=True,
    )





