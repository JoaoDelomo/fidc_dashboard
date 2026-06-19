import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from parser import parse_lamina, save_snapshot, load_historico

st.set_page_config(page_title="FIDC Dashboard", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.metric-card { background:#f8f9fa;border-radius:10px;padding:16px 20px;margin-bottom:8px; }
.metric-label { font-size:12px;color:#6c757d;text-transform:uppercase;letter-spacing:.04em; }
.metric-value { font-size:22px;font-weight:600;color:#212529;margin-top:4px; }
.metric-sub   { font-size:12px;color:#6c757d;margin-top:2px; }
.pos { color:#2d6a2d; } .neg { color:#a32d2d; }
.section-title { font-size:13px;font-weight:600;color:#495057;text-transform:uppercase;
                 letter-spacing:.05em;margin:1.5rem 0 .75rem;
                 border-bottom:1px solid #dee2e6;padding-bottom:4px; }
</style>
""", unsafe_allow_html=True)

HISTORICO_PATH = os.path.join(os.path.dirname(__file__), "data", "historico.json")

def parse_data(s):
    try: return datetime.strptime(s, "%d/%m/%Y")
    except: return datetime.min

with st.sidebar:
    st.title("📊 FIDC Dashboard")
    st.markdown("---")
    uploaded = st.file_uploader("Upload da lâmina (.xlsx)", type=["xlsx"])
    if uploaded:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(uploaded.read()); tmp_path = tmp.name
        try:
            data = parse_lamina(tmp_path)
            historico = save_snapshot(data, HISTORICO_PATH)
            st.success(f"✅ Importado: {data['parametros']['data_posicao']}")
        except Exception as e: st.error(f"Erro: {e}")
        finally: os.unlink(tmp_path)

    historico = load_historico(HISTORICO_PATH)
    if not historico: st.info("Faça upload de uma lâmina para começar."); st.stop()
    historico = sorted(historico, key=lambda h: parse_data(h["parametros"]["data_posicao"]))
    datas_disponiveis = [h["parametros"]["data_posicao"] for h in historico]
    data_selecionada = st.selectbox("Data de posição", datas_disponiveis[::-1])
    st.markdown("---")
    st.caption(f"{len(historico)} período(s) armazenado(s)")

snap = next(h for h in historico if h["parametros"]["data_posicao"] == data_selecionada)
p    = snap["parametros"]
rent = snap.get("rentabilidade", {})
idx_atual = next(i for i, h in enumerate(historico) if h["parametros"]["data_posicao"] == data_selecionada)
snap_ant  = historico[idx_atual - 1] if idx_atual > 0 else None
p_ant     = snap_ant["parametros"] if snap_ant else None

def fmt_brl(v): return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
def fmt_pct(v): return f"{v:+.2f}%".replace(".",",") if v is not None else "—"
def cor_pct(v): return "pos" if v and v >= 0 else "neg"

def tipo_cota(m):
    m = m.upper()
    if "SNR" in m: return "Sênior"
    if "MZA_A" in m: return "Mezanino A"
    if "MZA_B" in m: return "Mezanino B"
    if "SUB" in m: return "Subordinada"
    return m

def spread_cota(d):
    if "Spread:" in d: return d.split("Spread:")[-1].strip()
    return "—"

def seta(a, b):
    if b is None: return ""
    return "▲" if a > b else "▼" if a < b else "—"

def cor_seta(a, b):
    if b is None: return "#6c757d"
    return "#2d6a2d" if a > b else "#a32d2d" if a < b else "#6c757d"

def kpi(col, label, value, sub=""):
    col.markdown(f"""<div class="metric-card"><div class="metric-label">{label}</div>
    <div class="metric-value">{value}</div>
    {"<div class='metric-sub'>" + sub + "</div>" if sub else ""}</div>""", unsafe_allow_html=True)

# Header
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(f"## {p['carteira']}")
    st.caption(f"CNPJ {p['cnpj']} · {p['administrador']} · {p['gestor']}")
with col_h2:
    st.markdown(f"**Data-posição:** {p['data_posicao']}")
    st.markdown(f"**Status:** {'🟢' if p['status_cota'] == 'Liberada' else '🟡'} {p['status_cota']}")
st.markdown("---")

# KPIs
k1,k2,k3,k4,k5 = st.columns(5)
kpi(k1,"PL Posição",fmt_brl(p["pl_posicao"]),f"Patrimônio total: {fmt_brl(p['patrimonio_total'])}")
kpi(k2,"Cota Líquida",f"R$ {p['valor_cota_liquida']:,.6f}".replace(",","X").replace(".",",").replace("X","."),
    f"Bruta: R$ {p['valor_cota_bruta']:,.6f}".replace(",","X").replace(".",",").replace("X","."))
kpi(k3,"Qtd. Cotas",f"{p['qtde_cota']:,.2f}".replace(",","X").replace(".",",").replace("X","."))
kpi(k4,"Ingressos",fmt_brl(p["ingressos"]),f"Retiradas: {fmt_brl(p['retiradas'])}")
kpi(k5,"Caixa Disponível",fmt_brl(snap.get("caixa_total",0)),
    f"{snap['caixa_total']/p['pl_posicao']*100:.2f}% do PL" if p["pl_posicao"] else "")

# Rentabilidade
st.markdown('<div class="section-title">Rentabilidade</div>', unsafe_allow_html=True)
periodos = ["Diária","MTD","YTD","30d","90d","180d","360d","720d"]
chaves   = ["diaria","mtd","ytd","d30","d90","d180","d360","d720"]
cols_r = st.columns(8)
for col, label, chave in zip(cols_r, periodos, chaves):
    val = rent.get(chave)
    cls = cor_pct(val); txt = fmt_pct(val)
    col.markdown(f"""<div class="metric-card" style="text-align:center;padding:12px 8px;">
    <div class="metric-label">{label}</div>
    <div class="metric-value {cls}" style="font-size:17px">{txt}</div></div>""", unsafe_allow_html=True)

# Evolução histórica
if len(historico) > 1:
    st.markdown('<div class="section-title">Evolução histórica</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📈 Cota & PL","📊 Rentabilidade","🏗️ Composição da carteira"])
    hist_sorted = sorted(historico, key=lambda h: parse_data(h["parametros"]["data_posicao"]))

    with tab1:
        datas_dt = [parse_data(h["parametros"]["data_posicao"]) for h in hist_sorted]
        cotas_h  = [h["parametros"]["valor_cota_liquida"] for h in hist_sorted]
        pl_h     = [h["parametros"]["pl_posicao"] for h in hist_sorted]
        tooltips = []
        for h in hist_sorted:
            hp = h["parametros"]; hr = h.get("rentabilidade",{})
            tooltips.append(f"<b>{hp['data_posicao']}</b><br>Cota: R$ {hp['valor_cota_liquida']:,.6f}<br>"
                f"PL: {fmt_brl(hp['pl_posicao'])}<br>MTD: {fmt_pct(hr.get('mtd'))}<br>"
                f"YTD: {fmt_pct(hr.get('ytd'))}<br>Ingressos: {fmt_brl(hp['ingressos'])}<br>"
                f"Retiradas: {fmt_brl(hp['retiradas'])}")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=datas_dt,y=cotas_h,name="Cota líquida",
            line=dict(color="#185FA5",width=2),mode="lines+markers",marker=dict(size=6),
            yaxis="y1",hovertemplate="%{customdata}<extra></extra>",customdata=tooltips))
        fig.add_trace(go.Bar(x=datas_dt,y=pl_h,name="PL",
            marker_color="rgba(30,158,117,0.25)",yaxis="y2",
            hovertemplate="PL: R$ %{y:,.2f}<extra></extra>"))
        fig.update_layout(xaxis=dict(type="date",tickformat="%d/%m/%Y",tickangle=-30),
            yaxis=dict(title="Cota (R$)",side="left"),
            yaxis2=dict(title="PL (R$)",side="right",overlaying="y",showgrid=False),
            legend=dict(orientation="h",y=1.05),margin=dict(l=0,r=0,t=30,b=0),
            height=360,hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        periodos_graf = ["diaria","mtd","ytd","d30","d90","d180"]
        labels_graf   = ["Diária","MTD","YTD","30d","90d","180d"]
        df_rh = pd.DataFrame([{"Data_dt":parse_data(h["parametros"]["data_posicao"]),
            **{labels_graf[i]: h["rentabilidade"].get(periodos_graf[i]) or 0 for i in range(6)}}
            for h in hist_sorted])
        pc = st.selectbox("Período", labels_graf, index=2)
        cores = [("#2d6a2d" if v>=0 else "#a32d2d") for v in df_rh[pc]]
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=df_rh["Data_dt"],y=df_rh[pc],marker_color=cores,name=pc,
            hovertemplate="<b>%{x|%d/%m/%Y}</b><br>"+pc+": %{y:+.4f}%<extra></extra>"))
        fig2.add_hline(y=0,line_dash="dash",line_color="#adb5bd",line_width=1)
        fig2.update_layout(xaxis=dict(type="date",tickformat="%d/%m/%Y",tickangle=-30),
            yaxis_title=f"Rentabilidade % ({pc})",margin=dict(l=0,r=0,t=20,b=0),height=300)
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        comp_hist = []
        for h in hist_sorted:
            dc = h.get("direitos_creditorios_total",{}).get("pct_pl",0) or 0
            cf = sum(c["pct_pl"] for c in h.get("cotas_fundos",[])) or 0
            cx = h["caixa_total"]/h["parametros"]["pl_posicao"]*100 if h["parametros"]["pl_posicao"] else 0
            comp_hist.append({"Data_dt":parse_data(h["parametros"]["data_posicao"]),
                "DC":abs(dc),"Cotas RF":abs(cf),"Caixa":abs(cx)})
        df_comp = pd.DataFrame(comp_hist)
        fig3 = go.Figure()
        for cn, cor in {"DC":"#185FA5","Cotas RF":"#1D9E75","Caixa":"#888780"}.items():
            fig3.add_trace(go.Bar(x=df_comp["Data_dt"],y=df_comp[cn],name=cn,marker_color=cor,
                hovertemplate="<b>%{x|%d/%m/%Y}</b><br>"+cn+": %{y:.2f}% PL<extra></extra>"))
        fig3.update_layout(barmode="stack",xaxis=dict(type="date",tickformat="%d/%m/%Y",tickangle=-30),
            yaxis_title="% PL",legend=dict(orientation="h",y=1.05),
            margin=dict(l=0,r=0,t=30,b=0),height=300)
        st.plotly_chart(fig3, use_container_width=True)

# Composição atual
comp_labels,comp_values = [],[]
dc_total = snap.get("direitos_creditorios_total",{})
if dc_total.get("pct_pl"): comp_labels.append("Direitos Creditórios"); comp_values.append(abs(dc_total["pct_pl"]))
cf_pct = sum(c["pct_pl"] for c in snap.get("cotas_fundos",[]))
if cf_pct: comp_labels.append("Cotas RF"); comp_values.append(abs(cf_pct))
sw_pct = sum(s["pct_pl"] for s in snap.get("swap",[]))
if sw_pct: comp_labels.append("Swap"); comp_values.append(abs(sw_pct))
cx_pct = snap["caixa_total"]/p["pl_posicao"]*100 if p["pl_posicao"] else 0
if cx_pct: comp_labels.append("Caixa"); comp_values.append(abs(cx_pct))
pdd_pct = sum(abs(r["pct_pl"]) for r in snap.get("pdd",[]))
if pdd_pct: comp_labels.append("PDD"); comp_values.append(pdd_pct)

cotas_sup = snap.get("cotas_superiores",[])
total_sup = sum(c["valor_total"] for c in cotas_sup)
valor_sub = p["patrimonio_total"] - total_sup
pct_sub   = valor_sub/p["patrimonio_total"]*100 if p["patrimonio_total"] else 0

st.markdown('<div class="section-title">Composição da carteira — posição atual</div>', unsafe_allow_html=True)
col_a, col_b = st.columns([1,1])

with col_a:
    fig_d = go.Figure(go.Pie(labels=comp_labels,values=comp_values,hole=0.55,
        marker_colors=["#185FA5","#1D9E75","#BA7517","#888780","#E24B4A"],
        textinfo="label+percent",hovertemplate="%{label}: %{value:.2f}% PL<extra></extra>"))
    fig_d.update_layout(margin=dict(l=0,r=0,t=20,b=0),height=300,showlegend=False,
        annotations=[dict(text="Carteira",x=0.5,y=0.5,font_size=13,showarrow=False)])
    st.plotly_chart(fig_d, use_container_width=True)

with col_b:
    cores_map = {"Sênior":"#185FA5","Mezanino A":"#1D9E75","Mezanino B":"#2DC4A0","Subordinada":"#BA7517"}
    pizza_labels,pizza_values,pizza_tooltip,pizza_cores = [],[],[],[]
    for c in cotas_sup:
        tipo = tipo_cota(c["mnemonico"]); spr = spread_cota(c["detalhes"])
        pizza_labels.append(tipo); pizza_values.append(c["valor_total"])
        pizza_tooltip.append(f"<b>{tipo}</b><br>Valor: {fmt_brl(c['valor_total'])}<br>"
            f"% Patrim.: {c['pct_pl']:.2f}%<br>Spread: {spr}%<br>"
            f"Valor cota: {fmt_brl(c['valor_cota'])}<br>Qtd: {c['qtde']:,.2f}")
        pizza_cores.append(cores_map.get(tipo,"#888780"))
    if valor_sub > 0:
        pizza_labels.append("Subordinada"); pizza_values.append(valor_sub)
        pizza_tooltip.append(f"<b>Subordinada</b><br>Valor: {fmt_brl(valor_sub)}<br>"
            f"% Patrim.: {pct_sub:.2f}%<br>Valor cota: {fmt_brl(p['valor_cota_liquida'])}<br>"
            f"Qtd: {p['qtde_cota']:,.2f}<br>Spread: —")
        pizza_cores.append(cores_map["Subordinada"])
    fig_c = go.Figure(go.Pie(labels=pizza_labels,values=pizza_values,hole=0.5,
        marker_colors=pizza_cores,textinfo="label+percent",
        customdata=pizza_tooltip,hovertemplate="%{customdata}<extra></extra>"))
    fig_c.update_layout(margin=dict(l=0,r=0,t=20,b=0),height=300,showlegend=False,
        annotations=[dict(text="Cotas",x=0.5,y=0.5,font_size=13,showarrow=False)])
    st.plotly_chart(fig_c, use_container_width=True)

# Tabela de cotas com comparação
cotas_ant = {}
if snap_ant:
    for c in snap_ant.get("cotas_superiores",[]):
        cotas_ant[tipo_cota(c["mnemonico"])] = c
    pat_ant = snap_ant["parametros"]["patrimonio_total"]
    total_sup_ant = sum(c["valor_total"] for c in snap_ant.get("cotas_superiores",[]))
    cotas_ant["Subordinada"] = {
        "valor_total": pat_ant - total_sup_ant,
        "pct_pl": (pat_ant-total_sup_ant)/pat_ant*100 if pat_ant else 0,
        "valor_cota": snap_ant["parametros"]["valor_cota_liquida"],
        "qtde": snap_ant["parametros"]["qtde_cota"],
    }

linhas_cotas = []
for c in cotas_sup:
    tipo = tipo_cota(c["mnemonico"]); ant = cotas_ant.get(tipo)
    linhas_cotas.append({"tipo":tipo,"spread":spread_cota(c["detalhes"]),
        "valor_total":c["valor_total"],"pct_pl":c["pct_pl"],"valor_cota":c["valor_cota"],"qtde":c["qtde"],
        "valor_total_ant":ant["valor_total"] if ant else None,
        "pct_pl_ant":ant["pct_pl"] if ant else None,
        "valor_cota_ant":ant["valor_cota"] if ant else None})
if valor_sub > 0:
    ant_sub = cotas_ant.get("Subordinada")
    linhas_cotas.append({"tipo":"Subordinada","spread":"—",
        "valor_total":valor_sub,"pct_pl":pct_sub,
        "valor_cota":p["valor_cota_liquida"],"qtde":p["qtde_cota"],
        "valor_total_ant":ant_sub["valor_total"] if ant_sub else None,
        "pct_pl_ant":ant_sub["pct_pl"] if ant_sub else None,
        "valor_cota_ant":ant_sub["valor_cota"] if ant_sub else None})

data_ant_label = p_ant["data_posicao"] if p_ant else "—"
st.markdown(f'<div class="section-title">Estrutura de cotas — comparação com {data_ant_label}</div>', unsafe_allow_html=True)

hdr_cols = st.columns([2,1,2.5,1.5,2.5,2])
for col, txt in zip(hdr_cols, ["Classe","Spread","Valor Total","% Patrim.","Valor Cota","Qtd Cotas"]):
    col.markdown(f'<span style="font-size:11px;color:#6c757d;text-transform:uppercase;letter-spacing:.04em">{txt}</span>', unsafe_allow_html=True)
st.markdown("<hr style='margin:4px 0 8px;border-color:#dee2e6'>", unsafe_allow_html=True)

def cel_md(atual, anterior, formatter):
    if anterior is None: return formatter(atual)
    cor = cor_seta(atual, anterior); arrow = seta(atual, anterior)
    return f'<span style="color:{cor};font-weight:600">{formatter(atual)} {arrow}</span>'

for l in linhas_cotas:
    cols = st.columns([2,1,2.5,1.5,2.5,2])
    spr_txt = f"{l['spread']}%" if l['spread'] != "—" else "—"
    cols[0].markdown(f"**{l['tipo']}**")
    cols[1].markdown(spr_txt)
    cols[2].markdown(cel_md(l["valor_total"],l["valor_total_ant"],fmt_brl), unsafe_allow_html=True)
    cols[3].markdown(cel_md(l["pct_pl"],l["pct_pl_ant"],lambda v: f"{v:.2f}%"), unsafe_allow_html=True)
    cols[4].markdown(cel_md(l["valor_cota"],l["valor_cota_ant"],fmt_brl), unsafe_allow_html=True)
    cols[5].markdown(f"{l['qtde']:,.2f}")
    st.markdown("<hr style='margin:2px 0;border-color:#f0f0f0'>", unsafe_allow_html=True)

# Direitos Creditórios
st.markdown('<div class="section-title">Direitos creditórios</div>', unsafe_allow_html=True)
col_dc1, col_dc2 = st.columns(2)
with col_dc1:
    dc_rows = snap.get("direitos_creditorios",[])
    if dc_rows:
        st.dataframe(pd.DataFrame([{"Situação":r["papel"],
            "Valor Presente":fmt_brl(r["valor_presente"]) if r["valor_presente"] else "—",
            "% PL":f"{r['pct_pl']:.2f}%" if r["pct_pl"] else "—"} for r in dc_rows]),
            use_container_width=True,hide_index=True)
with col_dc2:
    dc_vals = [(r["papel"],r["valor_presente"]) for r in snap.get("direitos_creditorios",[])
               if r["valor_presente"] and r["valor_presente"]>0]
    pdd_val = abs(sum(r["valor_total"] for r in snap.get("pdd",[])))
    if dc_vals:
        fig_dc = go.Figure(go.Bar(x=[d[0] for d in dc_vals],y=[d[1] for d in dc_vals],
            marker_color=["#185FA5","#E24B4A","#888780","#BA7517"][:len(dc_vals)],
            text=[fmt_brl(d[1]) for d in dc_vals],textposition="outside"))
        if pdd_val:
            fig_dc.add_hline(y=-pdd_val,line_dash="dash",line_color="#E24B4A",
                annotation_text=f"PDD: {fmt_brl(pdd_val)}",annotation_position="bottom right")
        fig_dc.update_layout(yaxis_title="R$",margin=dict(l=0,r=0,t=10,b=0),height=260,showlegend=False)
        st.plotly_chart(fig_dc, use_container_width=True)

# Swap
st.markdown('<div class="section-title">Derivativos — swap</div>', unsafe_allow_html=True)
swaps = snap.get("swap",[])
if swaps:
    total_ativo   = sum(s["valor_ponta_ativa"]  for s in swaps)
    total_passivo = sum(s["valor_ponta_passiva"] for s in swaps)
    total_result  = sum(s["valor_total"]         for s in swaps)
    col_s1,col_s2,col_s3 = st.columns(3)
    kpi(col_s1,"Total ponta ativa",fmt_brl(total_ativo))
    kpi(col_s2,"Total ponta passiva",fmt_brl(total_passivo))
    kpi(col_s3,"Resultado líquido swap",fmt_brl(total_result))

    if "swap_aberto" not in st.session_state: st.session_state.swap_aberto = False
    label_btn = "▲ Fechar tabela detalhada" if st.session_state.swap_aberto else f"▼ Ver tabela detalhada ({len(swaps)} contratos)"
    if st.button(label_btn, key="btn_swap"):
        st.session_state.swap_aberto = not st.session_state.swap_aberto
    if st.session_state.swap_aberto:
        st.dataframe(pd.DataFrame([{"Mnemônico":s["mnemonico"],"Câmara":s["camara"],
            "Vencimento":s["data_vencimento"],"Valor Base":fmt_brl(s["valor_base"]),
            "Ponta Ativa":fmt_brl(s["valor_ponta_ativa"]),"Ponta Passiva":fmt_brl(s["valor_ponta_passiva"]),
            "Resultado":fmt_brl(s["valor_total"]),"% PL":f"{s['pct_pl']:.2f}%"} for s in swaps]),
            use_container_width=True,hide_index=True)

# Obrigações
st.markdown('<div class="section-title">Obrigações e direitos</div>', unsafe_allow_html=True)
col_op, col_or = st.columns(2)
with col_op:
    st.markdown("**A pagar**")
    pagar = snap.get("valores_a_pagar",[])
    if pagar:
        st.dataframe(pd.DataFrame([{"Histórico":r["historico"],"Liquidação":r["liquidacao"],
            "Valor":fmt_brl(r["valor_total"])} for r in pagar]),use_container_width=True,hide_index=True)
        st.markdown(f"**Total: {fmt_brl(snap.get('total_a_pagar',0))}**")
with col_or:
    st.markdown("**A receber**")
    receber = snap.get("valores_a_receber",[])
    if receber:
        st.dataframe(pd.DataFrame([{"Histórico":r["historico"],"Liquidação":r["liquidacao"],
            "Valor":fmt_brl(r["valor_total"])} for r in receber]),use_container_width=True,hide_index=True)
        st.markdown(f"**Total: {fmt_brl(snap.get('total_a_receber',0))}**")

st.markdown("---")
st.caption(f"FIDC Dashboard · Posição {p['data_posicao']} · {p['codigo_anbima']}")