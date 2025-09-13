from __future__ import annotations
import contextlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import streamlit as st
from streamlit.components.v1 import html

# Definimos las rutas base del proyecto
SRC_DIR = Path(__file__).resolve().parents[1]  # Obtiene el directorio padre, es decir, .../repo/src
REPO_ROOT = SRC_DIR.parent                     # .../repo

# Aseguramos que los paquetes bajo src/ sean importables sin depender de PYTHONPATH externo
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Importación de dependencias internas del compilador
from parsing.antlr import build_from_text, ParseResult  # type: ignore
with contextlib.suppress(Exception):
    from parsing.antlr.CompiscriptLexer import CompiscriptLexer  # type: ignore

# Intentamos importar Streamlit ACE para el editor de código, si no está disponible, se marca como False.
try:
    from streamlit_ace import st_ace
    HAS_ACE = True
except Exception:
    HAS_ACE = False

# Intentamos importar la función de análisis semántico
try:
    from semantic.checker import analyze  # type: ignore
except Exception as _ex:  # Mensaje diferido a la UI si hace falta
    analyze = None  # type: ignore

# Definición del estilo CSS para la app de Streamlit.
_DEF_CSS = _NEW_CSS = """
<style>
  :root{
    --bg:#ffffff;              /* Fondo principal (blanco) */
    --layer:#f0f6ff;           /* Paneles/tiles (azul muy claro) */
    --ink:#0b1f44;             /* Texto principal (azul marino) */
    --ink-sub:#3b5b8a;         /* Texto secundario */
    --brand:#1e66ff;           /* Azul de marca / primario */
    --brand-600:#1553d6;       /* Hover/active */
    --ok:#2e7d32;
    --warn:#ffca3a;
    --err:#e63946;
    --header-bg:#e8f0ff;       /* Cabecera clara */
    --header-text:#0b1f44;
    --message-bg:#edf2ff;      /* Tarjetas / alerts */
    --border:#c7dbff;          /* Bordes suaves azules */
  }

  /* App */
  .stApp{
    background:var(--bg);
    color:var(--ink);
    font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
  }

  /* Sidebar (antes gris) */
  [data-testid="stSidebar"]{
    background:var(--layer) !important;
    border-right:1px solid var(--border);
  }

  /* Cabecera superior */
  .stApp > header{
    background:var(--header-bg) !important;
    color:var(--header-text) !important;
    padding:20px 30px;
    border-bottom:1px solid var(--border);
    border-radius:10px 10px 0 0;
    box-shadow:none;
  }
  .stApp > header .header-logo{ color:var(--brand); }
  .stApp > header h1,
  .stApp > header .header-text{ color:var(--header-text) !important; }

  /* Títulos y texto */
  .stMarkdown h1, .stMarkdown h2, .stMarkdown h3,
  .stMarkdown h4, .stMarkdown h5, .stMarkdown h6{
    color:var(--ink);
  }
  .stMarkdown p, .stCaption, .st-emotion-cache-10trblm{
    color:var(--ink);
  }
  a{ color:var(--brand); }

  /* Contenedores / cards */
  .stAlert, .stInfo, .stWarning, .stSuccess, .stError{
    background:var(--message-bg) !important;
    color:var(--ink) !important;
    border:1px solid var(--border) !important;
  }
  .stAlert{ border-left:5px solid var(--err) !important; }

  /* Tabs */
  [data-baseweb="tab-list"]{
    background:var(--layer);
    padding:.5rem; gap:.5rem; border-radius:10px; border:1px solid var(--border);
  }
  [data-baseweb="tab"]{
    background:#ffffff; color:var(--ink);
    border-radius:8px; padding:0.75rem 1.1rem; border:1px solid var(--border);
  }
  [aria-selected="true"][data-baseweb="tab"]{
    background:var(--brand); color:#fff; border-color:var(--brand);
  }

  /* Inputs */
  .stTextInput input, .stTextArea textarea{
    background:#fff; color:var(--ink);
    border:1px solid var(--border); border-radius:8px; padding:.6rem;
  }

  /* Botones (incluye Guardar/Download) */
  .stButton > button,
  .stDownloadButton > button,
  .st-emotion-cache-7ym5gk button,              /* fallback */
  [data-testid="baseButton-secondary"]{
    background:#ffffff; color:var(--ink);
    border:1px solid var(--border); border-radius:10px;
    padding:.7rem 1.2rem; transition:background .2s, transform .15s;
  }
  .stButton > button:hover,
  .stDownloadButton > button:hover,
  [data-testid="baseButton-secondary"]:hover{
    background:var(--brand); color:#fff; transform:translateY(-1px);
    border-color:var(--brand);
  }

  /* Code blocks */
  .code-like, .stCode, pre, code{
    background:#f7faff !important;
    border:1px solid var(--border) !important;
    color:var(--ink) !important; border-radius:10px; padding:1rem;
  }

  /* Editor Ace (cuando no uses tema oscuro) */
  .ace_editor{
    background:#ffffff !important;
    color:var(--ink) !important;
    border:1px solid var(--border); border-radius:10px;
  }
  .ace_gutter{ background:#eaf2ff !important; color:#405b9a !important; }
  .ace_marker-layer .ace_active-line{ background:#dfe8ff !important; }
  .ace_cursor{ color:var(--brand) !important; }

  /* Tablas/Dataframe */
  .stDataFrame, .st-emotion-cache-1s3b6h1{
    background:#fff; border:1px solid var(--border); border-radius:10px;
  }

  /* Paneles/expander */
  .st-expander{
    background:#fff; border:1px solid var(--border); border-radius:12px !important;
  }

  /* Encabezado compacto del título personalizado */
  .cs-header{
    display:flex;align-items:center;gap:.75rem;background:#ffffff;
    border-bottom:1px solid var(--border);padding:.6rem 1rem;
  }
  .cs-title{ color:var(--ink); font-weight:700; letter-spacing:.3px; }
  .cs-sub{ color:var(--ink-sub); font-size:.85rem; }

  /* Uploader y selector de ejemplos */
.stFileUploader,
.stSelectbox,
.stFileUploader input {
    background-color: #f0f6ff;  /* Fondo claro azul */
    color: #0b1f44;  /* Texto oscuro */
    border: 1px solid #c7dbff;  /* Borde suave azul */
}

.stFileUploader input:focus,
.stSelectbox select:focus {
    outline: 2px solid #1e66ff;  /* Resalta al seleccionar */
}

.stSelectbox {
    background-color: #f0f6ff;
    color: #0b1f44;
    border: 1px solid #c7dbff;
}

/* Preferencias */
.st-expander header {
    color: #0b1f44;  /* Color de texto oscuro */
}

.stCheckbox label,
.stCheckbox span,
.stMarkdown p {
    color: #0b1f44;  /* Hacer más oscuro el texto en las preferencias */
}

</style>
"""

# Función que pinta el encabezado de la aplicación en Streamlit
def paint_header() -> None:
    st.markdown(
        """
        <div class="cs-header">
          <div style="font-size:1.25rem;color:#1e66ff;">🧪</div>
          <div>
            <div class="cs-title">Compiscript IDE</div>
            <div class="cs-sub">Refactor limpio • v1.0.0</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,  # Permitimos HTML no seguro para insertar el encabezado
    )

# ------------------ Utilidades núcleo ------------------
@st.cache_data(show_spinner=False)
def discover_samples() -> dict[str, str]:
    """Escanea los directorios de ejemplo y devuelve {ruta_visible: contenido}."""
    buckets = [REPO_ROOT / "program", REPO_ROOT / "src/tests"]  # Definimos los directorios de donde leer los ejemplos
    out: dict[str, str] = {}
    for root in buckets:
        if not root.exists():
            continue
        for p in sorted(root.glob("*")):
            if not p.is_file():
                continue
            if p.suffix.lower() in {".cps", ".cspt", ".txt", ".code"}:
                with contextlib.suppress(Exception):
                    out[f"{root.name}/{p.name}"] = p.read_text(encoding="utf-8")  # Añadimos el contenido de los archivos
    return out


# Función que normaliza la tabla de símbolos para mostrarla en una tabla comprensible.
def normalize_symbol_table(payload: Any) -> list[dict[str, str]]:
    """Aplana la tabla de símbolos devuelta por el checker a filas tabulares."""
    scopes = payload if isinstance(payload, list) else [payload]
    rows: list[dict[str, str]] = []
    for sc in scopes:
        scope = sc.get("scope", "") if isinstance(sc, dict) else ""
        entries = sc.get("entries", []) if isinstance(sc, dict) else []
        for e in entries:
            etype = e.get("type") if isinstance(e, dict) else ""
            rows.append({
                "scope": scope,
                "name": e.get("name", ""),
                "kind": e.get("kind", ""),
                "type": str(etype),
            })
    return rows


# Función que convierte el árbol ANTLR a un formato DOT para usarlo en Graphviz y visualizarlo en Streamlit
def to_dot_graph(tree, parser) -> str:
    """Convierte el árbol ANTLR a DOT para visualizar con Graphviz en Streamlit."""
    from antlr4 import RuleContext
    from antlr4.tree.Tree import TerminalNode

    rule_names = getattr(parser, "ruleNames", None)
    seq = 0
    lines = [
        "digraph G {",
        'node [shape=box, fontsize=10, fontname="Consolas"];',
        'graph [bgcolor="transparent"];',
        'edge  [color="#5b7bd5"];',
    ]

    def new_id() -> str:
        nonlocal seq
        seq += 1
        return f"n{seq}"

    def label(ctx) -> str:
        if isinstance(ctx, TerminalNode):
            txt = ctx.symbol.text.replace("\\", "\\\\").replace('"', '\\"')
            return f'"{txt}"'
        if isinstance(ctx, RuleContext):
            idx = ctx.getRuleIndex()
            name = rule_names[idx] if rule_names and 0 <= idx < len(rule_names) else f"rule_{idx}"
            return f'"{name}"'
        return '"?"'

    def paint(ctx) -> str:
        me = new_id()
        is_rule = isinstance(ctx, RuleContext)
        color = "#3f7ef7" if is_rule else "#7aa2ff"
        shape = "box" if is_rule else "ellipse"
        lines.append(f'{me} [label={label(ctx)}, color="{color}", fontcolor="#0b1f44", fillcolor="#eaf2ff", style="filled", shape={shape}];')
        for i in range(ctx.getChildCount()):
            ch = ctx.getChild(i)
            cid = paint(ch)
            lines.append(f"{me} -> {cid};")
        return me

    paint(tree)
    lines.append("}")
    return "\n".join(lines)


# Función que extrae la información de los tokens desde el resultado de análisis sintáctico.
def token_table(parse_result: ParseResult) -> list[dict[str, int | str]]:
    ts = parse_result.tokens
    ts.fill()
    all_tokens = getattr(ts, "tokens", []) or []
    visible = [t for t in all_tokens if getattr(t, "channel", 0) == 0]

    names = getattr(CompiscriptLexer, "symbolicNames", None) if 'CompiscriptLexer' in globals() else None

    rows: list[dict[str, int | str]] = []
    for t in visible:
        ttype = getattr(t, "type", None)
        if ttype == -1:
            name = "EOF"
        elif names and isinstance(ttype, int) and 0 <= ttype < len(names):
            name = names[ttype] or str(ttype)
        else:
            name = str(ttype)
        rows.append({
            "type": name,
            "text": getattr(t, "text", ""),
            "line": getattr(t, "line", -1),
            "column": getattr(t, "column", -1),
        })
    return rows


# ------------------ Estado y configuración ------------------
DEFAULT_SNIPPET = (
    "const x: integer = 1;\n"
    "function main() {\n"
    "  print(1);\n"
    "}\n"
)

st.set_page_config(
    page_title="Compiscript IDE",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(_DEF_CSS, unsafe_allow_html=True)  # Se aplica el CSS para darle estilo a la app.
paint_header()  # Pinta el encabezado en la app.

# Inicializa session_state con valores predeterminados para evitar errores de acceso a atributos no inicializados.
st.session_state.setdefault("code", DEFAULT_SNIPPET)
st.session_state.setdefault("console", "")
st.session_state.setdefault("ace_key", 0)
st.session_state.setdefault("last_result", None)

# ------------------ Sidebar ------------------
with st.sidebar:
    st.markdown("### 📁 Proyecto")

    # Uploader (buffer)
    def _decode(b: bytes) -> str:
        for enc in ("utf-8", "latin-1"):
            with contextlib.suppress(UnicodeDecodeError):
                return b.decode(enc)
        return b.decode("utf-8", errors="replace")

    uploaded = st.file_uploader(
        "Subir archivo",
        type=["cps", "cspt", "txt", "code"],
        accept_multiple_files=False,
        key="uploader",
    )
    if uploaded is not None:
        buf = _decode(uploaded.getvalue())
        st.session_state.code = buf
        st.session_state.console += f"📂 Archivo importado → {uploaded.name}\n"
        st.session_state.ace_key += 1
        st.session_state["_force_compile"] = True
        st.session_state["uploaded_name"] = uploaded.name

    samples = discover_samples()
    # Inserta el archivo subido como pseudo-ejemplo al tope
    if uploaded is not None:
        samples = {f"(subido) {uploaded.name}": st.session_state.code, **samples}

    choice = st.selectbox("Ejemplos", ["(ninguno)"] + sorted(samples.keys()))
    if choice != "(ninguno)":
        if st.session_state.get("_example_name") != choice:
            st.session_state.code = samples[choice]
            st.session_state.console += f"🧰 Ejemplo abierto → {choice}\n"
            st.session_state.ace_key += 1
            st.session_state["_force_compile"] = True
            st.session_state["_example_name"] = choice

    st.markdown("---")
    with st.expander("⚙️ Preferencias", expanded=True):
        auto_compile = st.checkbox("Compilación automática", value=False)
        show_tokens = st.checkbox("Ver tokens", value=False)
        show_dot = st.checkbox("Ver árbol (DOT)", value=True)
        show_string_tree = st.checkbox("Ver árbol (texto)", value=False)

    st.markdown("---")
    st.caption("Compiscript IDE • Streamlit • Refactor limpio")

# ------------------ Editor ------------------
st.markdown("## 📝 Editor")
ace_key = st.session_state.ace_key
if HAS_ACE:
    code = st_ace(
        value=st.session_state.code,
        language="typescript",
        theme="github",
        height=360,
        key=f"ace_{ace_key}",
        auto_update=auto_compile,
        show_gutter=True,
        wrap=False,
        tab_size=2,
        show_print_margin=False,
        keybinding="vscode",
    )
else:
    code = st.text_area("Código fuente", value=st.session_state.code, height=320)

st.session_state.code = code

# Acciones
col1, col2, col3, _ = st.columns([1, 1, 1, 5])
run_now = col1.button("▶️ Analizar", use_container_width=True)
if col2.button("🧹 Limpiar salida", use_container_width=True):
    st.session_state.console = ""
col3.download_button(
    "💾 Guardar", data=st.session_state.code.encode("utf-8"), file_name="program.cps", mime="text/plain", use_container_width=True
)

# Dispara compilación si hubo click o forzado por carga/ejemplo
run_now = run_now or st.session_state.pop("_force_compile", False)

# ------------------ Pipeline: parse + semántica ------------------
if run_now or (auto_compile and st.session_state.code.strip()):
    try:
        res = build_from_text(st.session_state.code, entry_rule="program")
        st.session_state.last_result = res
        st.session_state.semantic = None
        if res.ok():
            st.session_state.console += "✔️ Sintaxis: sin problemas.\n"
            if analyze is None:
                st.session_state.console += "⚠️ Analizador semántico no disponible (semantic.checker).\n"
            else:
                try:
                    sem = analyze(res.tree)
                    st.session_state.semantic = sem
                    errs = sem.get("errors", []) if isinstance(sem, dict) else []
                    if errs:
                        st.session_state.console += f"❗ Semántica: {len(errs)} problema(s) detectado(s).\n"
                    else:
                        st.session_state.console += "✔️ Semántica: OK.\n"
                except Exception as ex:  # pragma: no cover
                    st.session_state.console += f"💣 Falló semántica: {ex}\n"
        else:
            st.session_state.console += f"⛔ Sintaxis: {len(res.errors)} error(es).\n"
    except Exception as ex:  # pragma: no cover
        st.session_state.last_result = None
        st.session_state.console += f"💣 Error no controlado: {ex}\n"

# ------------------ Consola ------------------
st.markdown("## 🖥️ Salida")
st.code(st.session_state.console or "// La salida aparecerá aquí...", language="bash")

# ------------------ Resultados ------------------
st.markdown("## 📊 Resultados")
res: ParseResult | None = st.session_state.last_result
sem = st.session_state.get("semantic")

tabs = st.tabs(["Diagnósticos", "Árbol", "Tokens"])

with tabs[0]:
    if not res:
        st.info("Ejecuta el análisis para ver resultados.")
    else:
        rows: list[dict[str, Any]] = []
        if not res.ok():
            for i, e in enumerate(res.errors, 1):
                rows.append({
                    "Fase": "Sintaxis",
                    "#": i,
                    "Línea": getattr(e, "line", -1),
                    "Columna": getattr(e, "column", -1),
                    "Código": "-",
                    "Mensaje": getattr(e, "message", ""),
                    "Token": getattr(e, "offending", "-"),
                })
        if res.ok() and isinstance(sem, dict):
            for j, se in enumerate(sem.get("errors", []), 1):
                rows.append({
                    "Fase": "Semántica",
                    "#": j,
                    "Línea": se.get("line", -1),
                    "Columna": se.get("col", -1),
                    "Código": se.get("code", "-"),
                    "Mensaje": se.get("message", ""),
                    "Token": "-",
                })
        if rows:
            st.dataframe(
                rows,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "#": st.column_config.NumberColumn(width="small"),
                    "Línea": st.column_config.NumberColumn(width="small"),
                    "Columna": st.column_config.NumberColumn(width="small"),
                },
            )
        else:
            st.success("✅ Sin errores reportados.")

        if res and res.ok() and isinstance(sem, dict) and sem.get("symbols"):
            with st.expander("📚 Tabla de símbolos", expanded=True):
                flat = normalize_symbol_table(sem.get("symbols"))
                if flat:
                    st.dataframe(
                        flat,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "scope": st.column_config.TextColumn("scope", width="large"),
                            "name": st.column_config.TextColumn("name", width="medium"),
                            "kind": st.column_config.TextColumn("kind", width="small"),
                            "type": st.column_config.TextColumn("type", width="small"),
                        },
                    )
                    if st.toggle("Ver JSON crudo", value=False):
                        st.json(sem.get("symbols"))
                else:
                    st.info("No hay símbolos para mostrar.")

with tabs[1]:
    if not res or not res.ok():
        st.info("No hay árbol disponible.")
    else:
        if show_dot:
            dot = to_dot_graph(res.tree, res.parser)
            st.graphviz_chart(dot, use_container_width=True)
            c1, c2 = st.columns(2)
            c1.download_button("Descargar DOT", data=dot.encode("utf-8"), file_name="ast.dot", mime="text/vnd.graphviz", use_container_width=True)
            if c2.button("Copiar DOT", use_container_width=True):
                st.session_state["dot_copy"] = dot
                st.toast("DOT copiado al portapapeles", icon="📋")
        if show_string_tree:
            try:
                from antlr4.tree.Trees import Trees
                s = Trees.toStringTree(res.tree, None, res.parser)
                st.code(s, language="text")
            except Exception as ex:
                st.warning(f"No se pudo generar el árbol en texto: {ex}")

with tabs[2]:
    if not res:
        st.info("Analiza un programa para ver los tokens.")
    elif show_tokens:
        table = token_table(res)
        st.info(f"Total de tokens: {len(table)}")
        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            column_config={
                "line": st.column_config.NumberColumn("Línea", width="small"),
                "column": st.column_config.NumberColumn("Columna", width="small"),
            },
        )
    else:
        st.info("Activa \"Ver tokens\" en Preferencias para listarlos.")