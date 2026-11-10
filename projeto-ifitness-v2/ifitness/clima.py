
import requests

# Consumo de uma API externa: Open-Meteo (gratuita e sem chave de acesso).
# Documentação: https://open-meteo.com/en/docs
URL_OPEN_METEO = "https://api.open-meteo.com/v1/forecast"

# local consultado: Campos do Jordão - SP
CIDADE = "Campos do Jordão"
LATITUDE = -22.7394
LONGITUDE = -45.5914

# Tradução dos códigos de tempo devolvidos pela API (padrão WMO)
DESCRICOES = {
    0: "Céu limpo",
    1: "Predomínio de sol",
    2: "Parcialmente nublado",
    3: "Nublado",
    45: "Neblina",
    48: "Neblina",
    51: "Garoa fraca",
    53: "Garoa",
    55: "Garoa forte",
    61: "Chuva fraca",
    63: "Chuva",
    65: "Chuva forte",
    80: "Pancadas de chuva",
    81: "Pancadas de chuva",
    82: "Pancadas fortes de chuva",
    95: "Trovoada",
    96: "Trovoada com granizo",
    99: "Trovoada com granizo",
}


# Busca o clima atual da cidade.
# Devolve um dicionário ou None se a API externa falhar: o nosso site não
# pode parar de funcionar porque um serviço de terceiros está fora do ar.
def buscar_clima():
    parametros = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "timezone": "America/Sao_Paulo",
    }

    try:
        # timeout: sem ele, a requisição poderia ficar esperando para sempre
        resposta = requests.get(URL_OPEN_METEO, params=parametros, timeout=5)
        resposta.raise_for_status()  # levanta erro se o status não for 2xx
        atual = resposta.json()["current"]
        return {
            "cidade": CIDADE,
            "temperatura": atual["temperature_2m"],
            "vento": atual["wind_speed_10m"],
            "descricao": DESCRICOES.get(atual["weather_code"],
                                        "Tempo instável"),
        }
    except (requests.RequestException, KeyError, ValueError):
        return None
