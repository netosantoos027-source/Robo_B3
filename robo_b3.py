import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
import pytz
import requests

# ---------------------------------------------------------------------
# CONFIGURAÇÃO DO TELEGRAM (Preencha com seus dados corretos)
# ---------------------------------------------------------------------
# Cole aqui os números do Token que o @BotFather te deu (sem a palavra 'bot' antes)
TELEGRAM_TOKEN = "8977957095:AAH7t7a5pc4mjfdrQOlyyOrI1-1vbsJecFc"

# Cole aqui o seu número de ID que o @userinfobot te deu (apenas números)
TELEGRAM_CHAT_ID = "8650206759"

# Configura fuso horário de Brasília
fuso_br = pytz.timezone('America/Sao_Paulo')
data_hoje = datetime.now(fuso_br).strftime('%d-%m-%Y %H:%M')

# Lista de ações principais da B3
acoes = [
    'ALOS3.SA', 'ALPA4.SA', 'ABEV3.SA', 'ARZZ3.SA', 'ASAI3.SA', 'AZUL4.SA',
    'B3SA3.SA', 'BBAS3.SA', 'BBDC3.SA', 'BBDC4.SA', 'BBSE3.SA', 'BEEF3.SA', 'BPAC11.SA',
    'BRAP4.SA', 'BRFS3.SA', 'BRKM5.SA', 'CCRO3.SA', 'CMIG4.SA', 'CMIN3.SA',
    'COGN3.SA', 'CPFE3.SA', 'CPLE6.SA', 'CRFB3.SA', 'CSAN3.SA', 'CSNA3.SA', 'CVCB3.SA',
    'CYRE3.SA', 'DXCO3.SA', 'ELET3.SA', 'ELET6.SA', 'EMBR3.SA', 'ENEV3.SA', 'ENGI11.SA',
    'EQTL3.SA', 'EZTC3.SA', 'FLRY3.SA', 'GGBR4.SA', 'GOAU4.SA',
    'HAPV3.SA', 'HYPE3.SA', 'IGTI11.SA', 'IRBR3.SA', 'ITSA4.SA', 'ITUB4.SA', 'JBSS3.SA',
    'KLBN11.SA', 'LREN3.SA', 'LWSA3.SA', 'MGLU3.SA', 'MRVE3.SA', 'MULT3.SA', 'NTCO3.SA',
    'PCAR3.SA', 'PETR3.SA', 'PETR4.SA', 'RECV3.SA', 'RAIZ4.SA', 'RADL3.SA', 'RENT3.SA',
    'SANB11.SA', 'SMTO3.SA', 'SUZB3.SA', 'TAEE11.SA', 'TIMS3.SA', 'TOTS3.SA', 'UGPA3.SA',
    'USIM5.SA', 'VALE3.SA', 'VAMO3.SA', 'VBBR3.SA', 'WEGE3.SA', 'YDUQ3.SA'
]

oportunidades = []
print(f"🔎 Iniciando varredura estratégica B3 às {data_hoje}...")

for ticker in acoes:
    try:
        try:
            dados = yf.download(ticker, period='250d', progress=False)
        except:
            time.sleep(1)
            dados = yf.download(ticker, period='250d', progress=False)

        if dados.empty or len(dados) < 200: 
            continue
            
        if isinstance(dados.columns, pd.MultiIndex):
            dados.columns = dados.columns.get_level_values(0)

        time.sleep(0.1)

        # Indicadores Técnicos
        dados['Media_20'] = dados['Close'].rolling(window=20).mean()
        dados['Desvio_20'] = dados['Close'].rolling(window=20).std()
        dados['Banda_Sup'] = dados['Media_20'] + (dados['Desvio_20'] * 2)
        dados['Vol_Media_20'] = dados['Volume'].rolling(window=20).mean()
        dados['Media_200'] = dados['Close'].rolling(window=200).mean()
        dados['High_Low'] = dados['High'] - dados['Low']
        dados['ATR'] = dados['High_Low'].rolling(window=14).mean()

        preco_atual = float(dados['Close'].iloc[-1])
        banda_sup_atual = float(dados['Banda_Sup'].iloc[-1])
        media_200_atual = float(dados['Media_200'].iloc[-1])
        volume_atual = float(dados['Volume'].iloc[-1])
        volume_medio = float(dados['Vol_Media_20'].iloc[-1])
        atr_atual = float(dados['ATR'].iloc[-1])

        # Mantido em True para o nosso teste rápido de funcionamento
        if True:
            stop_tecnico = preco_atual - (2 * atr_atual)
            distancia_risco = preco_atual - stop_tecnico
            alvo_tecnico = preco_atual + (3 * distancia_risco)
            
            porcentagem_stop = ((preco_atual - stop_tecnico) / preco_atual) * 100
            porcentagem_alvo = ((alvo_tecnico - preco_atual) / preco_atual) * 100
            score_volume = volume_atual / volume_medio if volume_medio > 0 else 1.0

            oportunidades.append({
                'Ação': ticker.replace('.SA', ''),
                'Entrada': round(preco_atual, 2),
                'Alvo': round(alvo_tecnico, 2),
                'Alvo_Porc': round(porcentagem_alvo, 1),
                'Stop': round(stop_tecnico, 2),
                'Stop_Porc': round(porcentagem_stop, 1),
                'Vol': round(score_volume, 1)
            })
    except Exception as e:
        continue

# Montagem do Relatório Técnico
df_ops = pd.DataFrame(oportunidades)
mensagem_texto = f"🚨 *RELATÓRIO IA B3 - {data_hoje}* 🚨\n"
mensagem_texto += "_Modo de Teste Automático via Telegram_\n\n"

if not df_ops.empty:
    df_ops = df_ops.sort_values(by='Vol', ascending=False).head(3)
    mensagem_texto += "Olá, Neto! Aqui está o seu relatório:\n\n"
    for index, row in df_ops.iterrows():
        mensagem_texto += f"📌 *Ação: {row['Ação']}*\n"
        mensagem_texto += f" • Entrada sugerida: R$ {row['Entrada']}\n"
        mensagem_texto += f" • Alvo Técnico: R$ {row['Alvo']} (+{row['Alvo_Porc']}%)\n"
        mensagem_texto += f" • Stop Loss (ATR): R$ {row['Stop']} (-{row['Stop_Porc']}%)\n"
        mensagem_texto += f" • Volume: {row['Vol']}x acima da média\n\n"
else:
    mensagem_texto += "Varredura concluída. Nenhuma ação encontrada."

# ---------------------------------------------------------------------
# FUNÇÃO DE ENVIO VIA TELEGRAM CORRIGIDA E BLINDADA CONTRA ERROS DE CONEXÃO
# ---------------------------------------------------------------------
def enviar_telegram(texto):
    # Correção estrutural da URL para blindar contra digitação manual errada
    url_base = "https://telegram.org"
    rota = f"/bot{TELEGRAM_TOKEN}/sendMessage"
    url_final = url_base + rota
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": texto,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url_final, json=payload, timeout=15)
        if response.status_code == 200:
            print("📱 Relatório enviado com sucesso para o seu Telegram!")
        else:
            print(f"❌ O Telegram recusou a mensagem. Erro: {response.text}")
    except Exception as e:
        print(f"❌ Erro de rede ao conectar com os servidores do Telegram: {e}")

enviar_telegram(mensagem_texto)
