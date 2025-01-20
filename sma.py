import numpy as np
import time
import requests

# Configuración de Telegram
TELEGRAM_TOKEN = "7483932776:AAGFZMGmDWHuMt6zqtkh-lp318wP86zXli0"  # Token del bot
CHAT_ID = "7985261643"  # Chat ID del usuario

# Parámetros
PAIR = "bitcoin"  # Par de trading (BTC)
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

# Función para obtener datos históricos de CoinGecko
def get_historical_data(pair, vs_currency, days):
    url = f"https://api.coingecko.com/api/v3/coins/{pair}/market_chart"
    params = {
        "vs_currency": vs_currency,
        "days": days,
        "interval": TIMEFRAME
    }
    response = requests.get(url, params=params)
    data = response.json()
    prices = [entry[1] for entry in data['prices']]
    return prices

# Función principal para monitorear y notificar
def monitor():
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

            # Condiciones de compra y venta
            if sma_fast > sma_slow:
                message = f"Señal de COMPRA: Precio actual {last_price:.2f}, SMA Fast: {sma_fast:.2f}, SMA Slow: {sma_slow:.2f}"
                send_telegram_message(TELEGRAM_TOKEN, CHAT_ID, message)
            elif sma_fast < sma_slow:
                message = f"Señal de VENTA: Precio actual {last_price:.2f}, SMA Fast: {sma_fast:.2f}, SMA Slow: {sma_slow:.2f}"
                send_telegram_message(TELEGRAM_TOKEN, CHAT_ID, message)

            # Esperar antes del próximo ciclo
            time.sleep(60 * 60 * 24)  # Esperar 24 horas

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

# Probar notificación de Telegram
if __name__ == "__main__":
    send_telegram_message(TELEGRAM_TOKEN, CHAT_ID, "¡Hola Diego! El bot de CoinGecko está configurado correctamente.")
    monitor()
