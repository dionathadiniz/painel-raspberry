from flask import Flask, render_template, request
import socket
import shutil
import time
import subprocess
import re
from datetime import datetime

app = Flask(__name__)


# =========================
# ATIVIDADE 1
# =========================

def obter_nome():
    return socket.gethostname()


def obter_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Indisponível"


def obter_uptime():
    try:
        with open("/proc/uptime", "r") as arquivo:
            segundos = float(arquivo.readline().split()[0])

        dias = int(segundos // 86400)
        horas = int((segundos % 86400) // 3600)
        minutos = int((segundos % 3600) // 60)

        return f"{dias} dias, {horas} horas e {minutos} minutos"

    except:
        return "Indisponível"


def obter_cpu():
    try:
        with open("/proc/stat", "r") as arquivo:
            linha = arquivo.readline()

        valores = [int(valor) for valor in linha.split()[1:]]

        total = sum(valores)
        idle = valores[3]

        time.sleep(0.1)

        with open("/proc/stat", "r") as arquivo:
            linha2 = arquivo.readline()

        valores2 = [int(valor) for valor in linha2.split()[1:]]

        total2 = sum(valores2)
        idle2 = valores2[3]

        total_diferenca = total2 - total
        idle_diferenca = idle2 - idle

        if total_diferenca == 0:
            return 0

        uso = 100 * (1 - idle_diferenca / total_diferenca)

        return round(uso, 1)

    except:
        return "Indisponível"


def obter_temperatura():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as arquivo:
            temperatura = int(arquivo.read()) / 1000

        return round(temperatura, 1)

    except:
        return "Indisponível"


def obter_memoria():
    try:
        memoria_total = 0
        memoria_disponivel = 0

        with open("/proc/meminfo", "r") as arquivo:
            for linha in arquivo:
                if linha.startswith("MemTotal:"):
                    memoria_total = int(linha.split()[1])

                elif linha.startswith("MemAvailable:"):
                    memoria_disponivel = int(linha.split()[1])

        uso = (1 - memoria_disponivel / memoria_total) * 100

        return round(uso, 1)

    except:
        return "Indisponível"


def obter_armazenamento():
    try:
        total, usado, livre = shutil.disk_usage("/")

        uso = (usado / total) * 100

        return round(uso, 1)

    except:
        return "Indisponível"


# =========================
# ATIVIDADE 2 - REDE
# =========================

def obter_interface():
    try:
        resultado = subprocess.check_output(
            ["ip", "-o", "route", "show", "default"],
            text=True,
            timeout=3
        )

        match = re.search(r"dev\s+(\S+)", resultado)

        if match:
            return match.group(1)

        return "Indisponível"

    except:
        return "Indisponível"


def obter_estado_interface(interface):
    try:
        resultado = subprocess.check_output(
            ["ip", "link", "show", interface],
            text=True,
            timeout=3
        )

        if "state UP" in resultado:
            return "Ativa"

        return "Inativa"

    except:
        return "Indisponível"


def obter_tipo_conexao(interface):
    if interface.startswith("wl"):
        return "Wi-Fi"

    if interface.startswith("eth"):
        return "Ethernet"

    return "Outro"


def obter_ip_rede(interface):
    try:
        resultado = subprocess.check_output(
            ["ip", "-4", "addr", "show", interface],
            text=True,
            timeout=3
        )

        match = re.search(
            r"inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)",
            resultado
        )

        if not match:
            return "Indisponível"

        return match.group(1)

    except:
        return "Indisponível"


def obter_mascara(interface):
    try:
        resultado = subprocess.check_output(
            ["ip", "-4", "addr", "show", interface],
            text=True,
            timeout=3
        )

        match = re.search(
            r"inet\s+\d+\.\d+\.\d+\.\d+/(\d+)",
            resultado
        )

        if not match:
            return "Indisponível"

        prefixo = int(match.group(1))

        mascara = []

        for i in range(4):
            bits = max(0, min(8, prefixo - i * 8))

            if bits == 0:
                valor = 0
            else:
                valor = 256 - (2 ** (8 - bits))

            mascara.append(str(valor))

        return ".".join(mascara)

    except:
        return "Indisponível"


def obter_gateway():
    try:
        resultado = subprocess.check_output(
            ["ip", "route", "show", "default"],
            text=True,
            timeout=3
        )

        match = re.search(
            r"default via\s+(\S+)",
            resultado
        )

        if match:
            return match.group(1)

        return "Indisponível"

    except:
        return "Indisponível"


def obter_dns():
    try:
        servidores = []

        with open("/etc/resolv.conf", "r") as arquivo:
            for linha in arquivo:
                if linha.startswith("nameserver"):
                    servidor = linha.split()[1]
                    servidores.append(servidor)

        if servidores:
            return ", ".join(servidores)

        return "Indisponível"

    except:
        return "Indisponível"


def testar_conexao(destino):
    inicio = time.time()

    try:
        resultado = subprocess.run(
            ["ping", "-c", "1", "-W", "2", destino],
            capture_output=True,
            text=True,
            timeout=4
        )

        tempo = round((time.time() - inicio) * 1000, 1)

        if resultado.returncode == 0:
            return {
                "destino": destino,
                "status": "OK",
                "tempo": f"{tempo} ms",
                "classe": "ok"
            }

        return {
            "destino": destino,
            "status": "FALHA",
            "tempo": "Indisponível",
            "classe": "falha"
        }

    except subprocess.TimeoutExpired:
        return {
            "destino": destino,
            "status": "FALHA",
            "tempo": "Tempo excedido",
            "classe": "falha"
        }

    except:
        return {
            "destino": destino,
            "status": "FALHA",
            "tempo": "Indisponível",
            "classe": "falha"
        }


# =========================
# ROTAS
# =========================

@app.route("/")
def index():

    dados = {
        "nome": obter_nome(),
        "ip": obter_ip(),
        "uptime": obter_uptime(),
        "cpu": obter_cpu(),
        "temperatura": obter_temperatura(),
        "memoria": obter_memoria(),
        "armazenamento": obter_armazenamento(),
        "atualizacao": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

    return render_template("index.html", dados=dados)


@app.route("/rede")
def rede():

    interface = obter_interface()
    gateway = obter_gateway()

    destino_local = request.args.get(
        "destino_local",
        ""
    ).strip()

    teste_gateway = testar_conexao(gateway)

    if destino_local:
        teste_local = testar_conexao(destino_local)

    else:
        teste_local = {
            "destino": "Não informado",
            "status": "ATENÇÃO",
            "tempo": "Informe um destino local",
            "classe": "atencao"
        }

    teste_externo = testar_conexao("8.8.8.8")

    dados_rede = {
        "nome": obter_nome(),
        "interface": interface,
        "estado": obter_estado_interface(interface),
        "tipo": obter_tipo_conexao(interface),
        "ip": obter_ip_rede(interface),
        "mascara": obter_mascara(interface),
        "gateway": gateway,
        "dns": obter_dns(),
        "verificacao": datetime.now().strftime(
            "%d/%m/%Y %H:%M:%S"
        ),
        "teste_gateway": teste_gateway,
        "teste_local": teste_local,
        "teste_externo": teste_externo
    }

    return render_template(
        "rede/index.html",
        dados=dados_rede
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )