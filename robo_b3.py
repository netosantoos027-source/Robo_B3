import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ---------------------------------------------------------------------
# CONFIGURAÇÃO DE E-MAIL (Preencha com seus dados)
# ---------------------------------------------------------------------
CONFIG_EMAIL = {
    "remetente": "netosantoos027@gmail.com",     # Seu e-mail do Gmail
    "senha_app": "ryrj sher ueqr awsl", # A senha de app de 16 letras sem espaços
    "destinatario": "netosantoos027@gmail.com"  # O e-mail onde você quer receber o relatório
}

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
        # Sistema robusto de download com dupla tentativa em caso de oscilação de rede
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

        # 🚨 MUDADO PARA O TESTE DA ESTRATÉGIA (Na próxima etapa ativaremos os filtros reais)
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

# Montagem do RelatórioTexto
df_ops = pd.DataFrame(oportunidades)
mensagem_texto = f"🚨 RELATÓRIO IA B3 - {data_hoje} 🚨\n"
mensagem_texto += "Modo de Teste Forçado Ativo (Enviando primeiras ações da lista)\n\n"

if not df_ops.empty:
    df_ops = df_ops.sort_values(by='Vol', ascending=False).head(3)
    mensagem_texto += "Olá, Neto! Aqui está o seu relatório de teste do robô automático:\n\n"
    for index, row in df_ops.iterrows():
        mensagem_texto += f"📌 Ação: {row['Ação']}\n"
        mensagem_texto += f" • Preço de Entrada: R$ {row['Entrada']}\n"
        mensagem_texto += f" • Alvo Técnico: R$ {row['Alvo']} (+{row['Alvo_Porc']}%)\n"
        mensagem_texto += f" • Stop Loss Protetor: R$ {row['Stop']} (-{row['Stop_Porc']}%)\n"
        mensagem_texto += f" • Força do Volume: {row['Vol']}x acima da média\n\n"
else:
    mensagem_texto += "Varredura concluída.\n\nNenhuma ação encontrada nos registros."

# ---------------------------------------------------------------------
# FUNÇÃO DE ENVIO DE E-MAIL ROBUSTA (SMTP SSL PORTA 465 / 587)
# ---------------------------------------------------------------------
def enviar_email(conteudo):
    msg = MIMEMultipart()
    msg['From'] = CONFIG_EMAIL["remetente"]
    msg['To'] = CONFIG_EMAIL["destinatario"]
    msg['Subject'] = f"🚀 Teste do Relatório IA B3 - {data_hoje}"
    
    msg.attach(MIMEText(conteudo, 'plain'))
    
    try:
        # Tenta a conexão direta e blindada via SSL na Porta 465
        print("🔗 Conectando ao servidor SMTP do Gmail via SSL (Porta 465)...")
        server = smtplib.SMTP_SSL('://gmail.com', 465, timeout=15)
        server.login(CONFIG_EMAIL["remetente"], CONFIG_EMAIL["senha_app"])
        server.sendmail(CONFIG_EMAIL["remetente"], CONFIG_EMAIL["destinatario"], msg.as_string())
        server.quit()
        print("✉️ E-mail enviado com sucesso para o Neto via SSL!")
    except Exception as e:
        print(f"⚠️ Porta 465 falhou ({e}). Tentando rota alternativa TLS (Porta 587)...")
        try:
            # Rota alternativa caso a rede do GitHub bloqueie a porta padrão
            server = smtplib.SMTP('://gmail.com', 587, timeout=15)
            server.starttls()
            server.login(CONFIG_EMAIL["remetente"], CONFIG_EMAIL["senha_app"])
            server.sendmail(CONFIG_EMAIL["remetente"], CONFIG_EMAIL["destinatario"], msg.as_string())
            server.quit()
            print("✉️ E-mail enviado com sucesso para o Neto via TLS!")
        except Exception as e_alt:
            print(f"❌ Erro crítico total ao enviar o e-mail: {e_alt}")

enviar_email(mensagem_texto)
