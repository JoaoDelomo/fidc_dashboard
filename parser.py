import pandas as pd
import json
import os
from datetime import datetime


def parse_lamina(filepath: str) -> dict:
    xl = pd.ExcelFile(filepath)

    data = {}

    # --- Parâmetros ---
    df_params = xl.parse("Parâmetros", header=None)
    params = dict(zip(df_params[0], df_params[1]))
    data["parametros"] = {
        "carteira": str(params.get("Carteira", "")),
        "cnpj": str(params.get("CNPJ", "")),
        "data_posicao": str(params.get("Data Posição", "")),
        "tipo_carteira": str(params.get("Tipo Carteira", "")),
        "isin": str(params.get("ISIN", "")),
        "codigo_anbima": str(params.get("Código ANBIMA", "")),
        "status_cota": str(params.get("Status da Cota", "")),
        "administrador": str(params.get("Administrador", "")),
        "gestor": str(params.get("Gestor", "")),
        "pl_posicao": _to_float(params.get("PL Posição")),
        "pl_contabil": _to_float(params.get("PL Contábil")),
        "patrimonio_total": _to_float(params.get("Patrimônio (total das classes)")),
        "qtde_cota": _to_float(params.get("Qtde. Cota")),
        "ingressos": _to_float(params.get("Ingressos (R$)")),
        "retiradas": _to_float(params.get("Retiradas (R$)")),
        "valor_cota_liquida": _to_float(params.get("Valor da Cota Líquida")),
        "valor_cota_bruta": _to_float(params.get("Valor da Cota Bruta")),
    }

    # --- Cotas de Fundos RF ---
    df_cotas = xl.parse("Cotas de Fundos", header=1)
    df_cotas = df_cotas.dropna(how="all")
    df_cotas = df_cotas[df_cotas["Cód. Papel"].notna()]
    df_cotas = df_cotas[~df_cotas["Cód. Papel"].astype(str).str.startswith("Total")]
    df_cotas = df_cotas[df_cotas["%PL"].notna()]
    cotas_list = []
    for _, row in df_cotas.iterrows():
        cotas_list.append({
            "papel": str(row.get("Cód. Papel", "")),
            "administrador": str(row.get("Administrador", "")),
            "qtde": _to_float(row.get("Qtde. Total")),
            "preco_unit": _to_float(row.get("Preço Unitário")),
            "valor_impostos": _to_float(row.get("Valor Impostos")),
            "valor_total": _to_float(row.get("Valor Total")),
            "pct_pl": _to_float(row.get("%PL")),
        })
    data["cotas_fundos"] = cotas_list

    # --- Direitos Creditórios ---
    df_dc = xl.parse("Outros | Direitos Creditórios", header=1)
    df_dc = df_dc.dropna(how="all")
    df_dc = df_dc[df_dc["Cód. Papel"].notna()]
    df_dc = df_dc[~df_dc["Cód. Papel"].astype(str).str.startswith("Total")]
    dc_list = []
    for _, row in df_dc.iterrows():
        dc_list.append({
            "papel": str(row.get("Cód. Papel", "")),
            "valor_nominal": _to_float(row.get("Valor Nominal")),
            "valor_presente": _to_float(row.get("Valor Presente")),
            "pct_pl": _to_float(row.get("%PL")),
        })
    data["direitos_creditorios"] = dc_list

    # Total DC (linha Total:)
    df_dc_raw = xl.parse("Outros | Direitos Creditórios", header=1)
    total_row = df_dc_raw[df_dc_raw["Cód. Papel"].astype(str).str.startswith("Total")]
    data["direitos_creditorios_total"] = {
        "valor_presente": _to_float(total_row["Valor Presente"].values[0]) if not total_row.empty else 0,
        "pct_pl": _to_float(total_row["%PL"].values[0]) if not total_row.empty else 0,
    }

    # --- PDD ---
    df_pdd = xl.parse("Outros | PDD", header=1)
    df_pdd = df_pdd.dropna(how="all")
    df_pdd = df_pdd[df_pdd["Cód. Papel"].notna()]
    df_pdd = df_pdd[~df_pdd["Cód. Papel"].astype(str).str.startswith("Total")]
    data["pdd"] = [{"papel": str(r.get("Cód. Papel","")), "valor_total": _to_float(r.get("Valor Total")), "pct_pl": _to_float(r.get("%PL"))} for _, r in df_pdd.iterrows()]

    # --- Swap ---
    df_swap = xl.parse("Swap", header=1)
    df_swap = df_swap.dropna(how="all")
    df_swap = df_swap[df_swap["Mnemônico"].notna()]
    df_swap = df_swap[~df_swap["Mnemônico"].astype(str).str.startswith("Total")]
    swap_list = []
    for _, row in df_swap.iterrows():
        swap_list.append({
            "mnemonico": str(row.get("Mnemônico", "")),
            "camara": str(row.get("Câmara", "")),
            "data_operacao": str(row.get("Data Operação", "")),
            "data_vencimento": str(row.get("Data Vencimento", "")),
            "valor_base": _to_float(row.get("Valor Base Atual")),
            "ponta_ativa": str(row.get("Ponta Ativa", "")),
            "valor_ponta_ativa": _to_float(row.get("Valor Ponta Ativa")),
            "ponta_passiva": str(row.get("Ponta Passiva", "")),
            "valor_ponta_passiva": _to_float(row.get("Valor Ponta Passiva")),
            "valor_total": _to_float(row.get("Valor Total")),
            "pct_pl": _to_float(row.get("%PL")),
        })
    data["swap"] = swap_list

    # --- Valores a Pagar ---
    df_pagar = xl.parse("Valores a Pagar", header=1)
    df_pagar = df_pagar.dropna(how="all")
    df_pagar = df_pagar[df_pagar["Segmento"].notna()]
    df_pagar = df_pagar[~df_pagar["Segmento"].astype(str).str.startswith(("Total", "Subtotal"))]
    pagar_list = []
    for _, row in df_pagar.iterrows():
        pagar_list.append({
            "segmento": str(row.get("Segmento", "")),
            "historico": str(row.get("Histórico", "")),
            "liquidacao": str(row.get("Liquidação Prevista", "")),
            "valor_total": _to_float(row.get("Valor Total")),
        })
    data["valores_a_pagar"] = pagar_list
    data["total_a_pagar"] = sum(r["valor_total"] for r in pagar_list)

    # --- Valores a Receber ---
    df_receber = xl.parse("Valores a Receber", header=1)
    df_receber = df_receber.dropna(how="all")
    df_receber = df_receber[df_receber["Segmento"].notna()]
    df_receber = df_receber[~df_receber["Segmento"].astype(str).str.startswith(("Total", "Subtotal"))]
    receber_list = []
    for _, row in df_receber.iterrows():
        receber_list.append({
            "segmento": str(row.get("Segmento", "")),
            "historico": str(row.get("Histórico", "")),
            "liquidacao": str(row.get("Liquidação Prevista", "")),
            "valor_total": _to_float(row.get("Valor Total")),
        })
    data["valores_a_receber"] = receber_list
    data["total_a_receber"] = sum(r["valor_total"] for r in receber_list)

    # --- Cotas Superiores ---
    df_cotas_sup = xl.parse("Cotas Superiores", header=1)
    df_cotas_sup = df_cotas_sup.dropna(how="all")
    df_cotas_sup = df_cotas_sup[df_cotas_sup["Ordem"].notna()]
    df_cotas_sup = df_cotas_sup[~df_cotas_sup["Ordem"].astype(str).str.startswith("Total")]
    cotas_sup_list = []
    for _, row in df_cotas_sup.iterrows():
        cotas_sup_list.append({
            "ordem": str(row.get("Ordem", "")),
            "mnemonico": str(row.get("Mnemônico", "")),
            "detalhes": str(row.get("Detalhes", "")),
            "qtde": _to_float(row.get("Qtde. Total")),
            "valor_cota": _to_float(row.get("Valor Cota")),
            "valor_total": _to_float(row.get("Valor Total")),
            "pct_pl": _to_float(row.get("%PL")),
        })
    data["cotas_superiores"] = cotas_sup_list

    # --- Caixa ---
    df_caixa = xl.parse("Caixa", header=1)
    df_caixa = df_caixa.dropna(how="all")
    df_caixa = df_caixa[df_caixa["Saldo"].notna()]
    df_caixa = df_caixa[~df_caixa["Saldo"].astype(str).str.startswith("Total")]
    caixa_list = []
    for _, row in df_caixa.iterrows():
        caixa_list.append({
            "saldo": str(row.get("Saldo", "")),
            "valor_total": _to_float(row.get("Valor Total")),
            "pct_pl": _to_float(row.get("%PL")),
        })
    data["caixa"] = caixa_list
    data["caixa_total"] = sum(r["valor_total"] for r in caixa_list)

    # --- Rentabilidade ---
    df_rent = xl.parse("Rentabilidade (%)", header=1)
    df_rent = df_rent.dropna(how="all")
    df_rent = df_rent[df_rent.iloc[:, 0].astype(str).str.strip() == "Cota"]
    rent = {}
    if not df_rent.empty:
        row = df_rent.iloc[0]
        rent = {
            "diaria": _to_float_str(row.get("Diária")),
            "mtd": _to_float_str(row.get("Mensal (MTD)")),
            "ytd": _to_float_str(row.get("Anual (YTD)")),
            "d30": _to_float_str(row.get("Últimos 30 dias")),
            "d90": _to_float_str(row.get("Últimos 90 dias")),
            "d180": _to_float_str(row.get("Últimos 180 dias")),
            "d360": _to_float_str(row.get("Últimos 360 dias")),
            "d720": _to_float_str(row.get("Últimos 720 dias")),
        }
    data["rentabilidade"] = rent

    return data


def _to_float(val) -> float:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return 0.0
    try:
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip()
        if "E" in s.upper() and not s.startswith("R"):
            return float(s)
        s = s.replace(".", "").replace(",", ".")
        return float(s)
    except:
        return 0.0


def _to_float_str(val) -> float | None:
    if val is None or str(val).strip() in ("—", "", "nan"):
        return None
    try:
        return float(str(val).replace(",", "."))
    except:
        return None


def _parse_data(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%d/%m/%Y")
    except:
        return datetime.min


# 🛠️ FUNÇÃO ATUALIZADA: Agora usa o leitor seguro para carregar dados existentes
def save_snapshot(data: dict, storage_path: str = "data/historico.json"):
    os.makedirs(os.path.dirname(storage_path), exist_ok=True)
    
    # Usa a função blindada para ler o arquivo existente sem estourar erro
    historico = load_historico(storage_path)

    data_posicao = data["parametros"]["data_posicao"]
    historico = [h for h in historico if h["parametros"]["data_posicao"] != data_posicao]
    historico.append(data)
    historico.sort(key=lambda x: _parse_data(x["parametros"]["data_posicao"]))

    # Força o salvamento em UTF-8 limpo
    with open(storage_path, "w", encoding="utf-8") as f:
        json.dump(historico, f, ensure_ascii=False, indent=2)

    return historico


# 🛠️ FUNÇÃO ATUALIZADA: Try-Except posicionado corretamente protegendo o escopo inteiro
def load_historico(storage_path: str = "data/historico.json") -> list:
    if not os.path.exists(storage_path):
        return []
        
    # 🛡️ Tentativa 1: UTF-8 completo
    try:
        with open(storage_path, "r", encoding='utf-8') as f:
            return json.load(f)
    except (UnicodeDecodeError, json.JSONDecodeError):
        # 🛡️ Tentativa 2: Fallback para arquivos gerados no Windows antigo
        try:
            with open(storage_path, "r", encoding='latin-1') as f:
                return json.load(f)
        except:
            return []
    except:
        return []