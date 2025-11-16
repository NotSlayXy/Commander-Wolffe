import discord
from discord.ext import commands
import time
from datetime import timedelta
import os  # <<-- ASEGÚRATE DE AÑADIR ESTA LÍNEA

# --- CONFIGURACIÓN ---
# El token AHORA se lee de las variables de entorno de Railway
TOKEN = os.environ.get("DISCORD_TOKEN") 

# ID del servidor (Guild ID)
GUILD_ID = 1016504055838822430 # <--- Reemplaza con tu ID REAL
# ... (El resto del código sigue igual)

# Lógica Anti-Spam
SPAM_LIMIT = 3       # Número de mensajes
TIME_WINDOW = 5      # En segundos (en 5 segundos)
TIMEOUT_DURATION = 30 # Duración del Mute (Timeout) en minutos

# Estructura para guardar el historial de mensajes: {user_id: [timestamp1, timestamp2, ...]}
message_history = {}

# --- INICIALIZACIÓN DEL BOT ---

# Necesitas activar los Intents de 'messages' y 'members'
intents = discord.Intents.default()
intents.message_content = True  # Para leer el contenido de los mensajes
intents.members = True          # Para manejar miembros y timeouts

# El prefijo (prefix) no es tan importante, pero es estándar para comandos
bot = commands.Bot(command_prefix='!', intents=intents)

# --- EVENTOS Y LÓGICA DE SEGURIDAD ---

@bot.event
async def on_ready():
    """Se ejecuta cuando el bot está conectado y listo."""
    print(f'✅ Comandante Wolffe ({bot.user}) conectado.')
    try:
        # Sincroniza los comandos (si usas comandos de barra /)
        await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f'Comandos sincronizados en el servidor {GUILD_ID}.')
    except Exception as e:
        print(f'Error al sincronizar comandos: {e}')

@bot.event
async def on_message(message):
    """Lógica de detección y acción de spam."""
    # Ignora mensajes del propio bot
    if message.author.bot:
        return

    user_id = message.author.id
    current_time = time.time()

    # 1. ACTUALIZAR HISTORIAL
    if user_id not in message_history:
        message_history[user_id] = []
        
    message_history[user_id].append(current_time)
    
    # 2. ELIMINAR TIEMPOS VIEJOS
    # Mantén solo los mensajes dentro de la ventana de tiempo o los últimos 4 mensajes
    message_history[user_id] = [t for t in message_history[user_id] if t > current_time - TIME_WINDOW]

    # 3. DETECCIÓN DE SPAM (LOGICA: 3 mensajes en 5 segundos)
    if len(message_history[user_id]) >= SPAM_LIMIT:
        
        # Mute al miembro
        reason = (
            "Fuiste muteado debido a algún problema de spam, contáctate con nuestro STAFF "
            "para cualquier apelación o detalles. -Comandante Wolffe"
        )
        
        # El Time Out (Mute) se aplica a través del objeto Member
        try:
            # Obtiene el objeto Member (necesario para el timeout)
            member = message.author
            
            # Aplica el timeout (mute)
            await member.timeout(timedelta(minutes=TIMEOUT_DURATION), reason=reason)
            
            print(f"🚨 WOLFFE MUTED {member.name} por spam. Duración: {TIMEOUT_DURATION} minutos.")
            
        except discord.Forbidden:
            print(f"❌ Error: El bot no tiene permiso para aplicar el timeout a {message.author.name}.")
        
        # 4. BORRAR MENSAJES DE SPAM
        try:
            # Borra los mensajes que activaron el spam.
            # Borra el número de mensajes en la ventana de tiempo del canal.
            await message.channel.purge(limit=SPAM_LIMIT + 1, check=lambda m: m.author.id == user_id)
            print(f"🗑️ Mensajes de {message.author.name} borrados.")

        except discord.Forbidden:
            print("❌ Error: El bot no tiene permiso para borrar mensajes.")
        
        # 5. Reiniciar el contador para evitar un bucle de spam
        message_history[user_id] = []

    await bot.process_commands(message) # Necesario para que los comandos !funcionen

# --- INICIAR EL BOT ---
bot.run(TOKEN)