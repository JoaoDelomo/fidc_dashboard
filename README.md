# FIDC Dashboard

Dashboard local para análise de lâminas do FIDC Larca Aurora (e outros FIDCs com mesmo layout).

## Instalação

```bash
pip install -r requirements.txt
```

## Rodando

```bash
cd fidc_dashboard
streamlit run app.py
```

Abre automaticamente em http://localhost:8501

## Como usar

1. Faça upload do Excel (.xlsx) da lâmina pelo painel lateral
2. O app parseia e salva o snapshot em `data/historico.json`
3. Repita a cada novo período — o histórico se acumula automaticamente
4. Use o seletor de data para navegar entre períodos

## Estrutura

```
fidc_dashboard/
├── app.py          # Dashboard Streamlit
├── parser.py       # Lê o Excel e estrutura os dados
├── requirements.txt
└── data/
    └── historico.json  # Gerado automaticamente
```

## Gráficos disponíveis

- Evolução da cota líquida e PL ao longo do tempo
- Rentabilidade por período (diária, MTD, YTD, 30/90/180d)
- Composição da carteira empilhada (DC, Cotas RF, Caixa)
- Donut de alocação atual
- Estrutura de cotas superiores (Sênior / Mezanino)
- Detalhamento de Direitos Creditórios e PDD
- Tabela de Swaps com resultado líquido
- Obrigações a pagar e a receber

## Metas 18/06 x 19/06

- Melhorar nomes/descrições.
- Colocar valores de cotas sênior, mezanino e sub.
- razão de subordinação precisa ser calculado.
- preciso ver as informações no tempo, tal qual ver diário.
- SWAP precisa abrir Mnemônico (escondido), além de colocar mais informações sobre DI COM PERCENTUAL, buscar no regulamento ou falar com alguém que sabe.