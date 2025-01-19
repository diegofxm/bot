from binance.client import Client
from binance.enums import *
import numpy as np
import time
import requests

# Leer claves desde binance.key
with open('binance.key') as f:
    lines = f.readlines()
    api_key = lines[0].split('=')[1].strip()
    api_secret = lines[1].split('=')[1].strip()

# Configurar cliente para Binance.US
client = Client(api_key, api_secret, tld='us')

# Configuración de Telegram
TELEGRAM_TOKEN = "7483932776:AAGFZMGmDWHuMt6zqtkh-lp318wP86zXli0"  # Token del bot
CHAT_ID = "7985261643"  # Chat ID del usuario

# Parámetros
PAIR = "BTCUSDT"  # Par de trading
TIMEFRAME = "15m"  # Temporalidad (15 minutos)
RCI_PERIOD = 14  # Periodo del RCI
RCI_MIN = -80  # Límite inferior para compra
RCI_MAX = 80  # Límite superior para venta
RSI_PERIOD = 14  # Periodo del RSI
RSI_OVERBOUGHT = 70  # Nivel de sobrecompra
RSI_OVERSOLD = 30  # Nivel de sobreventa
EMA_FAST = 10  # EMA rápida
EMA_SLOW = 50  # EMA lenta
TP_PERCENT = 0.02  # Take profit (2%)
TRADE_PERCENT = 0.05  # Porcentaje del balance para operar (5%)

# Función para enviar notificaciones de Telegram
def send_telegram_message(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Error al enviar notificación: {e}")

# Función para calcular el RCI
def calculate_rci(prices, period):
    if len(prices) < period:
        return None
    ranks = np.argsort(np.argsort(prices[-period:]))
    n = len(ranks)
    numerator = 6 * sum((ranks[i] - i) ** 2 for i in range(n))
    denominator = n * (n ** 2 - 1)
    rci = 1 - numerator / denominator
    return rci * 100

# Función para calcular el RSI
def calculate_rsi(prices, period):
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Función para calcular una EMA
def calculate_ema(prices, period):
    weights = np.exp(np.linspace(-1., 0., period))
    weights /= weights.sum()
    ema = np.convolve(prices, weights, mode='full')[:len(prices)]
    ema[:period] = ema[period]
    return ema

# Función para obtener el balance de la cuenta
def get_account_balance(asset):
    try:
        balance = client.get_asset_balance(asset=asset)
        return float(balance['free'])
    except Exception as e:
        print(f"Error al obtener balance: {e}")
        return 0.0

# Función para imprimir el balance de todas las monedas en la cuenta
def print_account_balances():
    try:
        account_info = client.get_account()
        balances = account_info['balances']
        for balance in balances:
            if float(balance['free']) > 0:
                print(f"{balance['asset']}: {balance['free']}")
    except Exception as e:
        print(f"Error al obtener balances de la cuenta: {e}")

# Función principal de trading
def trade():
    while True:
        try:
            # Obtener datos del mercado
            klines = client.get_klines(symbol=PAIR, interval=TIMEFRAME)
            prices = [float(kline[4]) for kline in klines]  # Cierre de precios

            # Calcular indicadores
            rci = calculate_rci(prices, RCI_PERIOD)
            rsi = calculate_rsi(prices, RSI_PERIOD)
            ema_fast = calculate_ema(prices, EMA_FAST)
            ema_slow = calculate_ema(prices, EMA_SLOW)

            if rci is None or rsi is None:
                print("No hay suficientes datos para calcular indicadores.")
                time.sleep(60)
                continue

            print(f"RCI: {rci:.2f}, RSI: {rsi:.2f}, EMA Fast: {ema_fast[-1]:.2f}, EMA Slow: {ema_slow[-1]:.2f}")

            # Confirmar tendencia (EMA)
            trend_up = ema_fast[-1] > ema_slow[-1]
            trend_down = ema_fast[-1] < ema_slow[-1]

            # Obtener el último precio
            last_price = prices[-1]

            # Calcular el volumen dinámico
            balance = get_account_balance("USDT")
            trade_volume = balance * TRADE_PERCENT / last_price
            trade_volume = max(trade_volume, 0.0001)  # Asegurar un volumen mínimo

            # Estrategia de compra
            if rci < RCI_MIN and rsi < RSI_OVERSOLD and trend_up:
                print(f"Comprando {trade_volume:.6f} {PAIR} a {last_price}")
                order = client.order_market_buy(
                    symbol=PAIR,
                    quantity=round(trade_volume, 6)
                )
                print("Orden de compra enviada: ", order)

                # Notificar por Telegram
                send_telegram_message(TELEGRAM_TOKEN, CHAT_ID, f"Compra abierta: {trade_volume:.6f} {PAIR} a {last_price}")

            # Estrategia de venta
            elif rci > RCI_MAX and rsi > RSI_OVERBOUGHT and trend_down:
                print(f"Vendiendo {trade_volume:.6f} {PAIR} a {last_price}")
                order = client.order_market_sell(
                    symbol=PAIR,
                    quantity=round(trade_volume, 6)
                )
                print("Orden de venta enviada: ", order)

                # Notificar por Telegram
                send_telegram_message(TELEGRAM_TOKEN, CHAT_ID, f"Venta abierta: {trade_volume:.6f} {PAIR} a {last_price}")

            # Esperar antes del próximo ciclo
            time.sleep(60 * int(TIMEFRAME[:-1]))

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(60)

# Probar notificación de Telegram
if __name__ == "__main__":
    send_telegram_message(TELEGRAM_TOKEN, CHAT_ID, "¡Hola! El bot de Binance está configurado correctamente.")
    print_account_balances()  # Imprimir balances de la cuenta
    trade()
