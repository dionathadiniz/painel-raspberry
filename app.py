from flask import Flask, render_template
import socket
import shutil
import time
from datetime import datetime

app = Flask(__name__)


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    