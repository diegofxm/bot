import numpy as np
import time
import requests

# Configuración de Telegram
TELEGRAM_TOKEN = "7483932776:AAGFZMGmDWHuMt6zqtkh-lp318wP86zXli0"  # Token del bot
CHAT_ID = "7985261643"  # Chat ID del usuario

# Parámetros
PAIR = "BTC"  # Par de trading (BTC)
VS_CURRENCY = "usd"  # Moneda base (USD)
TIMEFRAME = "daily"  # Temporalidad (1 día)
SMA_FAST_PERIOD = 10  # SMA rápida
SMA_SLOW_PERIOD = 20  # SMA lenta
TRADE_PERCENT = 0.10  # Porcentaje del balance para operar (10%)

# Función para enviar notificaciones de Telegram
def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Notificación enviada a Telegram: {message}")
    except Exception as e:
        print(f"Error al enviar notificación: {e}")

# Función para calcular una SMA
def calculate_sma(prices, period):
    return np.mean(prices[-period:])

# Función para obtener datos históricos de CryptoCompare
def get_historical_data(pair, vs_currency, days):
    url = "https://min-api.cryptocompare.com/data/v2/histoday"
    headers = {
        "Authorization": "Apikey df549c808eef09d2268ec42e4a5e68ad8d65302ad8a6c014e515ec08764540f4"
    }
    params = {
        "fsym": pair.upper(),
        "tsym": vs_currency.upper(),
        "limit": days
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    if data['Response'] == 'Success':
        prices = [entry['close'] for entry in data['Data']['Data']]
        return prices
    else:
        print(f"Error obteniendo datos: {data['Message']}")
        return []

# Variables de estado para rastrear señales
last_signal = None  # 'buy', 'sell' o None
confirmed_signal = None

# Función principal para monitorear y notificar
def monitor():
    global last_signal, confirmed_signal
    
    while True:
        try:
            # Obtener datos históricos
            prices = get_historical_data(PAIR, VS_CURRENCY, SMA_SLOW_PERIOD)

            # Calcular SMAs
            sma_fast = calculate_sma(prices, SMA_FAST_PERIOD)
            sma_slow = calculate_sma(prices, SMA_SLOW_PERIOD)

            # Obtener el último precio
            last_price = prices[-1]

            # Imprimir SMAs y precio actual
            print(f"Precio actual: {last_price:.2f}, SMA Fast: {sma_fast:.2f}, SMA Slow: {sma_slow:.2f}")

            # Detectar cruce inicial
            current_signal = None
            if sma_fast > sma_slow:
                current_signal = 'buy'
            elif sma_fast < sma_slow:
                current_signal = 'sell'

            # Solo enviar señal si hay un cambio y se confirma en la siguiente vela
            if current_signal != last_signal:
                # Esperar confirmación en la siguiente vela
                last_signal = current_signal
                confirmed_signal = None
            elif current_signal == last_signal and confirmed_signal is None:
                # Confirmar señal después de la siguiente vela
                confirmed_signal = current_signal
                if current_signal == 'buy':
                    message = f"Señal de COMPRA confirmada: Precio actual {last_price:.2f}, SMA Fast: {sma_fast:.2f}, SMA Slow: {sma_slow:.2f}"
                    send_telegram_message(TELEGRAM_TOKEN, CHAT_ID, message)
                elif current_signal == 'sell':
                    message = f"Señal de VENTA confirmada: Precio actual {last_price:.2f}, SMA Fast: {sma_fast:.2f}, SMA Slow: {sma_slow:.2f}"
                    send_telegram_message(TELEGRAM_TOKEN, CHAT_ID, message)

            # Esperar antes del próximo ciclo
            time.sleep(60 * 60 * 24)  # Esperar 24 horas

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

# Probar notificación de Telegram
if __name__ == "__main__":
    send_telegram_message(TELEGRAM_TOKEN, CHAT_ID, "¡Hola Diego! El bot está configurado correctamente.")
    monitor()
