import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from parser import parse_lamina, save_snapshot, load_historico

st.set_page_config(
    page_title="FIDC Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS mínimo ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.metric-label { font-size: 12px; color: #6c757d; text-transform: uppercase; letter-spacing: .04em; }
.metric-value { font-size: 22px; font-weight: 600; color: #212529; margin-top: 4px; }
.metric-sub   { font-size: 12px; color: #6c757d; margin-top: 2px; }
.pos { color: #2d6a2d; }
.neg { color: #a32d2d; }
.section-title { font-size: 13px; font-weight: 600; color: #495057;
                 text-transform: uppercase; letter-spacing: .05em;
                 margin: 1.5rem 0 .75rem; border-bottom: 1px solid #dee2e6; padding-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

HISTORICO_PATH = os.path.join(os.path.dirname(__file__), "data", "historico.json")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 FIDC Dashboard")
    st.markdown("---")
    uploaded = st.file_uploader("Upload da lâmina (.xlsx)", type=["xlsx"])

    if uploaded:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name
        try:
            data = parse_lamina(tmp_path)
            historico = save_snapshot(data, HISTORICO_PATH)
            st.success(f"✅ Importado: {data['parametros']['data_posicao']}")
        except Exception as e:
            st.error(f"Erro ao processar: {e}")
        finally:
            os.unlink(tmp_path)

    historico = load_historico(HISTORICO_PATH)
    if not historico:
        st.info("Faça upload de uma lâmina para começar.")
        st.stop()

    datas_disponiveis = [h["parametros"]["data_posicao"] for h in historico]
    data_selecionada = st.selectbox("Data de posição", datas_disponiveis[::-1])
    st.markdown("---")
    st.caption(f"{len(historico)} período(s) armazenado(s)")

# ── Dados da data selecionada ────────────────────────────────────────────────
snap = next(h for h in historico if h["parametros"]["data_posicao"] == data_selecionada)
p = snap["parametros"]
rent = snap.get("rentabilidade", {})

def fmt_brl(v): return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
def fmt_pct(v): return f"{v:+.2f}%".replace(".", ",") if v is not None else "—"
def cor_pct(v): return "pos" if v and v >= 0 else "neg"

# ── Header ────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(f"## {p['carteira']}")
    st.caption(f"CNPJ {p['cnpj']} · {p['administrador']} · {p['gestor']}")
with col_h2:
    st.markdown(f"**Data-posição:** {p['data_posicao']}")
    status_color = "🟢" if p["status_cota"] == "Liberada" else "🟡"
    st.markdown(f"**Status:** {status_color} {p['status_cota']}")

st.markdown("---")

# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

def kpi(col, label, value, sub=""):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {"<div class='metric-sub'>" + sub + "</div>" if sub else ""}
    </div>""", unsafe_allow_html=True)

kpi(k1, "PL Posição", fmt_brl(p["pl_posicao"]), f"Patrimônio total: {fmt_brl(p['patrimonio_total'])}")
kpi(k2, "Cota Líquida", f"R$ {p['valor_cota_liquida']:,.6f}".replace(",","X").replace(".",",").replace("X","."), f"Bruta: R$ {p['valor_cota_bruta']:,.6f}".replace(",","X").replace(".",",").replace("X","."))
kpi(k3, "Qtd. Cotas", f"{p['qtde_cota']:,.2f}".replace(",","X").replace(".",",").replace("X","."), "")
kpi(k4, "Ingressos", fmt_brl(p["ingressos"]), f"Retiradas: {fmt_brl(p['retiradas'])}")
kpi(k5, "Caixa Disponível", fmt_brl(snap.get("caixa_total", 0)), f"{snap['caixa_total']/p['pl_posicao']*100:.2f}% do PL" if p["pl_posicao"] else "")

# ── Rentabilidade ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Rentabilidade</div>', unsafe_allow_html=True)

periodos = ["Diária", "MTD", "YTD", "30d", "90d", "180d", "360d", "720d"]
chaves   = ["diaria", "mtd", "ytd", "d30", "d90", "d180", "d360", "d720"]
valores  = [rent.get(c) for c in chaves]

cols_r = st.columns(8)
for col, label, val in zip(cols_r, periodos, valores):
    cls = cor_pct(val)
    txt = fmt_pct(val)
    col.markdown(f"""
    <div class="metric-card" style="text-align:center; padding:12px 8px;">
        <div class="metric-label">{label}</div>
        <div class="metric-value {cls}" style="font-size:17px">{txt}</div>
    </div>""", unsafe_allow_html=True)

# ── Gráfico de rentabilidade histórica ───────────────────────────────────────
if len(historico) > 1:
    st.markdown('<div class="section-title">Evolução histórica</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📈 Cota & PL", "📊 Rentabilidade acumulada", "🏗️ Composição da carteira"])

    with tab1:
        datas_h = [h["parametros"]["data_posicao"] for h in historico]
        cotas_h = [h["parametros"]["valor_cota_liquida"] for h in historico]
        pl_h    = [h["parametros"]["pl_posicao"] for h in historico]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=datas_h, y=cotas_h, name="Cota líquida", line=dict(color="#185FA5", width=2), yaxis="y1"))
        fig.add_trace(go.Bar(x=datas_h, y=pl_h, name="PL", marker_color="rgba(30,158,117,0.25)", yaxis="y2"))
        fig.update_layout(
            yaxis=dict(title="Cota (R$)", side="left"),
            yaxis2=dict(title="PL (R$)", side="right", overlaying="y", showgrid=False),
            legend=dict(orientation="h", y=1.05),
            margin=dict(l=0, r=0, t=30, b=0),
            height=340,
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        periodos_graf = ["diaria","mtd","ytd","d30","d90","d180"]
        labels_graf   = ["Diária","MTD","YTD","30d","90d","180d"]
        for h in historico:
            for k in periodos_graf:
                if h["rentabilidade"].get(k) is None:
                    h["rentabilidade"][k] = 0

        df_rent_hist = pd.DataFrame([{
            "Data": h["parametros"]["data_posicao"],
            **{labels_graf[i]: h["rentabilidade"].get(periodos_graf[i], 0) for i in range(len(periodos_graf))}
        } for h in historico])

        periodo_escolhido = st.selectbox("Período", labels_graf, index=2)
        fig2 = go.Figure()
        cores = [("#2d6a2d" if v >= 0 else "#a32d2d") for v in df_rent_hist[periodo_escolhido]]
        fig2.add_trace(go.Bar(x=df_rent_hist["Data"], y=df_rent_hist[periodo_escolhido],
                              marker_color=cores, name=periodo_escolhido))
        fig2.add_hline(y=0, line_dash="dash", line_color="#adb5bd", line_width=1)
        fig2.update_layout(yaxis_title=f"Rentabilidade % ({periodo_escolhido})", margin=dict(l=0,r=0,t=20,b=0), height=300)
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        datas_comp = [h["parametros"]["data_posicao"] for h in historico]
        comp_hist = []
        for h in historico:
            dc = h.get("direitos_creditorios_total", {}).get("pct_pl", 0) or 0
            cf = sum(c["pct_pl"] for c in h.get("cotas_fundos", [])) or 0
            cx = h["caixa_total"] / h["parametros"]["pl_posicao"] * 100 if h["parametros"]["pl_posicao"] else 0
            comp_hist.append({"Data": h["parametros"]["data_posicao"], "DC": abs(dc), "Cotas RF": abs(cf), "Caixa": abs(cx)})

        df_comp = pd.DataFrame(comp_hist)
        fig3 = go.Figure()
        cores_comp = {"DC": "#185FA5", "Cotas RF": "#1D9E75", "Caixa": "#888780"}
        for col_name, cor in cores_comp.items():
            fig3.add_trace(go.Bar(x=df_comp["Data"], y=df_comp[col_name], name=col_name, marker_color=cor))
        fig3.update_layout(barmode="stack", yaxis_title="% PL", legend=dict(orientation="h", y=1.05),
                           margin=dict(l=0,r=0,t=30,b=0), height=300)
        st.plotly_chart(fig3, use_container_width=True)

# ── Composição atual ───────────────────────────────────────────────────────────
# Monta comp_labels/values fora do bloco histórico para garantir disponibilidade com 1 período
comp_labels = []
comp_values = []

dc_total = snap.get("direitos_creditorios_total", {})
if dc_total.get("pct_pl"):
    comp_labels.append("Direitos Creditórios")
    comp_values.append(abs(dc_total["pct_pl"]))

cf_total_pct = sum(c["pct_pl"] for c in snap.get("cotas_fundos", []))
if cf_total_pct:
    comp_labels.append("Cotas RF")
    comp_values.append(abs(cf_total_pct))

swap_total_pct = sum(s["pct_pl"] for s in snap.get("swap", []))
if swap_total_pct:
    comp_labels.append("Swap")
    comp_values.append(abs(swap_total_pct))

caixa_pct = snap["caixa_total"] / p["pl_posicao"] * 100 if p["pl_posicao"] else 0
if caixa_pct:
    comp_labels.append("Caixa")
    comp_values.append(abs(caixa_pct))

pdd_total_pct = sum(abs(r["pct_pl"]) for r in snap.get("pdd", []))
if pdd_total_pct:
    comp_labels.append("PDD")
    comp_values.append(pdd_total_pct)

st.markdown('<div class="section-title">Composição da carteira — posição atual</div>', unsafe_allow_html=True)

col_a, col_b = st.columns([1, 1])

with col_a:
    # Donut composição
    fig_donut = go.Figure(go.Pie(
        labels=comp_labels, values=comp_values,
        hole=0.55,
        marker_colors=["#185FA5","#1D9E75","#BA7517","#888780","#E24B4A"],
        textinfo="label+percent",
        hovertemplate="%{label}: %{value:.2f}% PL<extra></extra>",
    ))
    fig_donut.update_layout(margin=dict(l=0,r=0,t=20,b=0), height=280,
                            showlegend=False,
                            annotations=[dict(text="Carteira", x=0.5, y=0.5, font_size=13, showarrow=False)])
    st.plotly_chart(fig_donut, use_container_width=True)

with col_b:
    st.markdown("**Estrutura de cotas superiores**")
    for c in snap.get("cotas_superiores", []):
        tipo = "Sênior" if "SNR" in c["mnemonico"] else "Mezanino" if "MZA" in c["mnemonico"] else c["mnemonico"]
        spread = ""
        if "Spread:" in c["detalhes"]:
            spread = "Spread " + c["detalhes"].split("Spread:")[-1].strip()
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center;
                    padding:8px 12px; margin-bottom:6px; background:#f8f9fa; border-radius:8px;
                    border-left: 4px solid {'#185FA5' if 'SNR' in c['mnemonico'] else '#1D9E75'}">
            <div>
                <div style="font-weight:600;font-size:14px">{tipo}</div>
                <div style="font-size:11px;color:#6c757d">{spread}</div>
            </div>
            <div style="text-align:right">
                <div style="font-weight:600">{fmt_brl(c['valor_total'])}</div>
                <div style="font-size:12px;color:#6c757d">{c['pct_pl']:.2f}% PL</div>
            </div>
        </div>""", unsafe_allow_html=True)

# ── Direitos Creditórios ───────────────────────────────────────────────────────
st.markdown('<div class="section-title">Direitos creditórios</div>', unsafe_allow_html=True)
col_dc1, col_dc2 = st.columns(2)

with col_dc1:
    dc_rows = snap.get("direitos_creditorios", [])
    if dc_rows:
        df_dc_show = pd.DataFrame([{
            "Situação": r["papel"],
            "Valor Presente": fmt_brl(r["valor_presente"]) if r["valor_presente"] else "—",
            "% PL": f"{r['pct_pl']:.2f}%" if r["pct_pl"] else "—",
        } for r in dc_rows])
        st.dataframe(df_dc_show, use_container_width=True, hide_index=True)

with col_dc2:
    dc_vals = [(r["papel"], r["valor_presente"]) for r in snap.get("direitos_creditorios", []) if r["valor_presente"] and r["valor_presente"] > 0]
    pdd_val = abs(sum(r["valor_total"] for r in snap.get("pdd", [])))
    if dc_vals:
        fig_dc = go.Figure(go.Bar(
            x=[d[0] for d in dc_vals],
            y=[d[1] for d in dc_vals],
            marker_color=["#185FA5","#E24B4A","#888780","#BA7517"][:len(dc_vals)],
            text=[fmt_brl(d[1]) for d in dc_vals],
            textposition="outside",
        ))
        if pdd_val:
            fig_dc.add_hline(y=-pdd_val, line_dash="dash", line_color="#E24B4A",
                             annotation_text=f"PDD: {fmt_brl(pdd_val)}", annotation_position="bottom right")
        fig_dc.update_layout(yaxis_title="R$", margin=dict(l=0,r=0,t=10,b=0), height=260, showlegend=False)
        st.plotly_chart(fig_dc, use_container_width=True)

# ── Swap ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Derivativos — swap</div>', unsafe_allow_html=True)
swaps = snap.get("swap", [])
if swaps:
    df_swap_show = pd.DataFrame([{
        "Mnemônico": s["mnemonico"],
        "Câmara": s["camara"],
        "Vencimento": s["data_vencimento"],
        "Valor Base": fmt_brl(s["valor_base"]),
        "Ponta Ativa": fmt_brl(s["valor_ponta_ativa"]),
        "Ponta Passiva": fmt_brl(s["valor_ponta_passiva"]),
        "Resultado": fmt_brl(s["valor_total"]),
        "% PL": f"{s['pct_pl']:.2f}%",
    } for s in swaps])
    st.dataframe(df_swap_show, use_container_width=True, hide_index=True)

    total_ativo  = sum(s["valor_ponta_ativa"] for s in swaps)
    total_passivo = sum(s["valor_ponta_passiva"] for s in swaps)
    total_result  = sum(s["valor_total"] for s in swaps)
    col_s1, col_s2, col_s3 = st.columns(3)
    kpi(col_s1, "Total ponta ativa",   fmt_brl(total_ativo))
    kpi(col_s2, "Total ponta passiva", fmt_brl(total_passivo))
    kpi(col_s3, "Resultado líquido swap", fmt_brl(total_result))

# ── Obrigações ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Obrigações e direitos</div>', unsafe_allow_html=True)
col_op, col_or = st.columns(2)

with col_op:
    st.markdown("**A pagar**")
    pagar = snap.get("valores_a_pagar", [])
    if pagar:
        df_p = pd.DataFrame([{"Histórico": r["historico"], "Liquidação": r["liquidacao"], "Valor": fmt_brl(r["valor_total"])} for r in pagar])
        st.dataframe(df_p, use_container_width=True, hide_index=True)
        st.markdown(f"**Total: {fmt_brl(snap.get('total_a_pagar', 0))}**")

with col_or:
    st.markdown("**A receber**")
    receber = snap.get("valores_a_receber", [])
    if receber:
        df_r = pd.DataFrame([{"Histórico": r["historico"], "Liquidação": r["liquidacao"], "Valor": fmt_brl(r["valor_total"])} for r in receber])
        st.dataframe(df_r, use_container_width=True, hide_index=True)
        st.markdown(f"**Total: {fmt_brl(snap.get('total_a_receber', 0))}**")

# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"FIDC Dashboard · Posição {p['data_posicao']} · {p['codigo_anbima']}")