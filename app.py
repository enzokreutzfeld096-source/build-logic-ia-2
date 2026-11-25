import os
import requests
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

fila_letras = []
indice_atual = 0
ultimo_texto = "PRONTO"

HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IA - Build Logic</title>
    <style>
        body { font-family: Arial, sans-serif; background: #121212; color: #fff; display: flex; justify-content: center; padding: 30px; }
        .box { background: #1e1e1e; padding: 25px; border-radius: 12px; width: 100%; max-width: 500px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        h2 { margin-top: 0; color: #4ade80; }
        textarea { width: 100%; height: 90px; border-radius: 8px; border: none; padding: 10px; font-size: 16px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; margin-top: 12px; background: #22c55e; border: none; border-radius: 8px; color: #000; font-weight: bold; font-size: 16px; cursor: pointer; }
        button:hover { background: #16a34a; }
        .resp { margin-top: 20px; background: #2a2a2a; padding: 15px; border-radius: 8px; font-family: monospace; white-space: pre-wrap; }
    </style>
</head>
<body>
    <div class="box">
        <h2>IA para Build Logic (16x16)</h2>
        <form method="POST" action="/perguntar">
            <textarea name="pergunta" placeholder="Digite a pergunta do jogador aqui..." required></textarea>
            <button type="submit">Enviar para IA e Telao</button>
        </form>
        <div class="resp"><strong>Ultima resposta enviada ao jogo:</strong><br><br>{{ resposta }}</div>
    </div>
</body>
</html>
"""

def limpar_texto_ascii(texto):
    mapa = str.maketrans("ÁÀÃÂÉÈÊÍÌÓÒÕÔÚÙÇáàãâéèêíìóòõôúùç", "AAAAEEEIIOOOOUUCaaaaeeeiioooouuc")
    texto = texto.translate(mapa).upper()
    return "".join(c for c in texto if 32 <= ord(c) <= 95)[:256]

@app.route("/", methods=["GET", "POST"])
def home():
    global indice_atual, ultimo_texto
    if request.method == "POST" or "Roblox" in request.headers.get("User-Agent", ""):
        if not fila_letras:
            return jsonify({"value": "0000000000000000"})

        char_code = fila_letras.pop(0)
        codigo = 0 if char_code == 32 else (char_code & 0x7F)
        bits_7 = format(codigo, "07b")[::-1]
        resposta_binaria = (bits_7 + "100000000")[::-1]
        return jsonify({"value": resposta_binaria})

    return render_template_string(HTML_PAGE, resposta=ultimo_texto)

@app.route("/perguntar", methods=["POST"])
def perguntar():
    global fila_letras, indice_atual, ultimo_texto
    pergunta = request.form.get("pergunta", "")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": "Responda bem curto, apenas com letras, sem acentos, sem pontuacao e escreva numeros por extenso."},
            {"role": "user", "content": pergunta}
        ]
    }
    url_groq = "https://api.groq.com/openai/v1/chat/completions"

    try:
        r = requests.post(url_groq, headers=headers, json=payload, timeout=10)
        if r.status_code != 200:
            resposta_ia = f"ERRO HTTP {r.status_code}: {r.text[:100]}"
        else:
            dados = r.json()
            resposta_ia = dados["choices"][0]["message"]["content"]
    except Exception as e:
        resposta_ia = f"ERRO: {str(e)}"

    texto_limpo = limpar_texto_ascii(resposta_ia)
    ultimo_texto = texto_limpo
    fila_letras = [ord(c) for c in texto_limpo]
    indice_atual = 0

    return render_template_string(HTML_PAGE, resposta=ultimo_texto)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
