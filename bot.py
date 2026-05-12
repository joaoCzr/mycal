import telebot
import os
from dotenv import load_dotenv
from telebot import types

from mensagens import (
    START_MESSAGE,
    SOBRE_MESSAGE,
    CONTATO_MESSAGE,
    COMANDOS_MESSAGE
)

from functions import (
    get_or_create_user_db,
    add_food_db,
    view_food_db,
    edit_food_db,
    delete_food_db,
    create_meal_db,
    add_food_to_meal_db,
    calculate_meal_macros_db,
    set_meta_db,
    get_meta_db,
    get_daily_status_db
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def start(msg: telebot.types.Message):
    markup = types.InlineKeyboardMarkup()

    botao_sobre = types.InlineKeyboardButton('Sobre', callback_data='sobre')
    botao_contato = types.InlineKeyboardButton('Contato', callback_data='contato')
    botao_comandos = types.InlineKeyboardButton('Comandos', callback_data='comandos')

    markup.add(botao_sobre, botao_contato)
    markup.add(botao_comandos)

    bot.send_message(msg.chat.id, START_MESSAGE, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    bot.answer_callback_query(call.id)

    if call.data == 'sobre':
        bot.send_message(call.message.chat.id, SOBRE_MESSAGE)

    elif call.data == 'contato':
        bot.send_message(call.message.chat.id, CONTATO_MESSAGE)

    elif call.data == 'comandos':
        bot.send_message(call.message.chat.id, COMANDOS_MESSAGE)

    elif call.data.startswith("add_food_meal:"):
        meal_id = int(call.data.split(":")[1])
        mostrar_alimentos_para_refeicao(call.message, meal_id)

    elif call.data.startswith("finish_meal:"):
        meal_id = int(call.data.split(":")[1])
        result = calculate_meal_macros_db(meal_id)

        texto = "✅ Refeição finalizada!\n\n"
        texto += "📊 Total da refeição:\n\n"

        if result["foods"]:
            texto += "🍽️ Alimentos:\n"

            for food in result["foods"]:
                texto += f"""
- {food["name_food"]} ({food["quantity"]:.0f}g)
  🔥 {food["kcal"]:.2f} kcal
  🥩 {food["prot"]:.2f}g proteína
  🍚 {food["carb"]:.2f}g carboidrato
  🥑 {food["fat"]:.2f}g gordura
"""

        texto += f"""
----------------------

🔥 Calorias totais: {result["total_kcal"]:.2f} kcal
🥩 Proteínas totais: {result["total_prot"]:.2f}g
🍚 Carboidratos totais: {result["total_carb"]:.2f}g
🥑 Gorduras totais: {result["total_fat"]:.2f}g
"""

        bot.send_message(call.message.chat.id, texto)


@bot.message_handler(commands=['addfood'])
def addfood(msg):
    bot.send_message(msg.chat.id, "Digite o nome do alimento:")
    bot.register_next_step_handler(msg, receber_nome_food)


def receber_nome_food(msg):
    name_food = msg.text

    bot.send_message(msg.chat.id, "Digite a proteína por 100g:")
    bot.register_next_step_handler(msg, receber_prot, name_food)


def receber_prot(msg, name_food):
    try:
        prot = float(msg.text)

        bot.send_message(msg.chat.id, "Digite o carboidrato por 100g:")
        bot.register_next_step_handler(msg, receber_carb, name_food, prot)

    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite um valor numérico para proteína.")


def receber_carb(msg, name_food, prot):
    try:
        carb = float(msg.text)

        bot.send_message(msg.chat.id, "Digite a gordura por 100g:")
        bot.register_next_step_handler(msg, receber_fat, name_food, prot, carb)

    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite um valor numérico para carboidrato.")


def receber_fat(msg, name_food, prot, carb):
    try:
        fat = float(msg.text)

        add_food_db(name_food, prot, carb, fat)

        bot.send_message(msg.chat.id, "✅ Alimento cadastrado com sucesso!")

    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite um valor numérico para gordura.")


@bot.message_handler(commands=['listfood'])
def listfood(msg):
    foods = view_food_db()

    if not foods:
        bot.send_message(msg.chat.id, "📭 Nenhum alimento cadastrado ainda.")
        return

    texto = "📋 Alimentos cadastrados:\n\n"

    for food in foods:
        texto += f"""
ID: {food[0]}
🍽️ Alimento: {food[1]}
🥩 Proteína: {food[2]}g
🍚 Carboidrato: {food[3]}g
🥑 Gordura: {food[4]}g
----------------------
"""

    bot.send_message(msg.chat.id, texto)


@bot.message_handler(commands=['editfood'])
def editfood(msg):
    foods = view_food_db()

    if not foods:
        bot.send_message(msg.chat.id, "📭 Nenhum alimento cadastrado ainda.")
        return

    texto = "✏️ Escolha o ID do alimento que deseja editar:\n\n"

    for food in foods:
        texto += f"ID: {food[0]} - {food[1]}\n"

    bot.send_message(msg.chat.id, texto)
    bot.register_next_step_handler(msg, receber_id_edit)


def receber_id_edit(msg):
    try:
        id_food = int(msg.text)

        bot.send_message(msg.chat.id, "Digite o novo nome do alimento:")
        bot.register_next_step_handler(msg, receber_novo_nome_food, id_food)

    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite um ID válido. Exemplo: 1")


def receber_novo_nome_food(msg, id_food):
    name_food = msg.text

    bot.send_message(msg.chat.id, "Digite a nova proteína por 100g:")
    bot.register_next_step_handler(msg, receber_nova_prot, id_food, name_food)


def receber_nova_prot(msg, id_food, name_food):
    try:
        prot = float(msg.text)

        bot.send_message(msg.chat.id, "Digite o novo carboidrato por 100g:")
        bot.register_next_step_handler(msg, receber_novo_carb, id_food, name_food, prot)

    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite um valor numérico para proteína.")


def receber_novo_carb(msg, id_food, name_food, prot):
    try:
        carb = float(msg.text)

        bot.send_message(msg.chat.id, "Digite a nova gordura por 100g:")
        bot.register_next_step_handler(msg, receber_nova_fat, id_food, name_food, prot, carb)

    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite um valor numérico para carboidrato.")


def receber_nova_fat(msg, id_food, name_food, prot, carb):
    try:
        fat = float(msg.text)

        rows = edit_food_db(id_food, name_food, prot, carb, fat)

        if rows == 0:
            bot.send_message(msg.chat.id, "❌ Nenhum alimento encontrado com esse ID.")
        else:
            bot.send_message(msg.chat.id, "✅ Alimento editado com sucesso!")

    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite um valor numérico para gordura.")


@bot.message_handler(commands=['deletefood'])
def deletefood(msg):
    foods = view_food_db()

    if not foods:
        bot.send_message(msg.chat.id, "📭 Nenhum alimento cadastrado ainda.")
        return

    texto = "🗑️ Escolha o ID do alimento que deseja excluir:\n\n"

    for food in foods:
        texto += f"ID: {food[0]} - {food[1]}\n"

    bot.send_message(msg.chat.id, texto)
    bot.register_next_step_handler(msg, receber_id_delete)


def receber_id_delete(msg):
    try:
        id_food = int(msg.text)

        rows = delete_food_db(id_food)

        if rows == 0:
            bot.send_message(msg.chat.id, "❌ Nenhum alimento encontrado com esse ID.")
        else:
            bot.send_message(msg.chat.id, "✅ Alimento excluído com sucesso!")

    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite um ID válido. Exemplo: 1")


@bot.message_handler(commands=['createmeal'])
def createmeal(msg):
    bot.send_message(msg.chat.id, "Digite o nome da refeição:")
    bot.register_next_step_handler(msg, receber_nome_refeicao)


def receber_nome_refeicao(msg):
    telegram_id = msg.from_user.id
    nome = msg.from_user.first_name
    name_meal = msg.text

    user_id = get_or_create_user_db(telegram_id, nome)

    meal_id = create_meal_db(user_id, name_meal)

    bot.send_message(
        msg.chat.id,
        f"✅ Refeição criada com sucesso!\n\nID da refeição: {meal_id}"
    )

    mostrar_alimentos_para_refeicao(msg, meal_id)


def mostrar_alimentos_para_refeicao(msg, meal_id):
    foods = view_food_db()

    if not foods:
        bot.send_message(msg.chat.id, "📭 Nenhum alimento cadastrado ainda.")
        return

    texto = "🍽️ Escolha o ID do alimento que deseja adicionar:\n\n"

    for food in foods:
        texto += f"ID: {food[0]} - {food[1]}\n"

    bot.send_message(msg.chat.id, texto)
    bot.register_next_step_handler(msg, receber_food_id_refeicao, meal_id)


def receber_food_id_refeicao(msg, meal_id):
    try:
        food_id = int(msg.text)

        bot.send_message(msg.chat.id, "Digite a quantidade em gramas:")
        bot.register_next_step_handler(
            msg,
            receber_quantidade_refeicao,
            meal_id,
            food_id
        )

    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite um ID válido.")


def receber_quantidade_refeicao(msg, meal_id, food_id):
    try:
        quantity = float(msg.text)

        add_food_to_meal_db(meal_id, food_id, quantity)

        markup = types.InlineKeyboardMarkup()

        botao_add = types.InlineKeyboardButton(
            "➕ Adicionar outro alimento",
            callback_data=f"add_food_meal:{meal_id}"
        )

        botao_finalizar = types.InlineKeyboardButton(
            "✅ Finalizar refeição",
            callback_data=f"finish_meal:{meal_id}"
        )

        markup.add(botao_add)
        markup.add(botao_finalizar)

        bot.send_message(
            msg.chat.id,
            "✅ Alimento adicionado à refeição.\n\nDeseja adicionar outro alimento?",
            reply_markup=markup
        )

    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite uma quantidade válida.")


@bot.message_handler(commands=['meta'])
def meta(msg):
    bot.send_message(msg.chat.id, "🎯 Vamos definir sua meta diária!\n\nDigite sua meta de calorias (kcal):")
    bot.register_next_step_handler(msg, receber_meta_kcal)


def receber_meta_kcal(msg):
    try:
        kcal = float(msg.text)
        bot.send_message(msg.chat.id, "🥩 Digite sua meta de proteína (g):")
        bot.register_next_step_handler(msg, receber_meta_prot, kcal)
    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite um valor numérico. Exemplo: 2000")


def receber_meta_prot(msg, kcal):
    try:
        prot = float(msg.text)
        bot.send_message(msg.chat.id, "🍚 Digite sua meta de carboidrato (g):")
        bot.register_next_step_handler(msg, receber_meta_carb, kcal, prot)
    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite um valor numérico. Exemplo: 150")


def receber_meta_carb(msg, kcal, prot):
    try:
        carb = float(msg.text)
        bot.send_message(msg.chat.id, "🥑 Digite sua meta de gordura (g):")
        bot.register_next_step_handler(msg, receber_meta_fat, kcal, prot, carb)
    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite um valor numérico. Exemplo: 250")


def receber_meta_fat(msg, kcal, prot, carb):
    try:
        fat = float(msg.text)

        telegram_id = msg.from_user.id
        nome = msg.from_user.first_name
        user_id = get_or_create_user_db(telegram_id, nome)

        set_meta_db(user_id, kcal, prot, carb, fat)

        bot.send_message(
            msg.chat.id,
            f"✅ Meta diária definida!\n\n"
            f"🔥 Calorias: {kcal:.0f} kcal\n"
            f"🥩 Proteína: {prot:.0f}g\n"
            f"🍚 Carboidrato: {carb:.0f}g\n"
            f"🥑 Gordura: {fat:.0f}g"
        )
    except ValueError:
        bot.send_message(msg.chat.id, "❌ Digite um valor numérico. Exemplo: 70")


@bot.message_handler(commands=['status'])
def status(msg):
    telegram_id = msg.from_user.id
    nome = msg.from_user.first_name
    user_id = get_or_create_user_db(telegram_id, nome)

    consumo = get_daily_status_db(user_id)
    meta = get_meta_db(user_id)

    texto = "📊 Seu status de hoje:\n\n"

    if meta:
        kcal_goal, prot_goal, carb_goal, fat_goal = meta

        def barra(atual, meta):
            if meta <= 0:
                return ""
            pct = min(atual / meta * 100, 100)
            blocos = int(pct / 10)
            return f"[{'█' * blocos}{'░' * (10 - blocos)}] {pct:.0f}%"

        texto += (
            f"🔥 Calorias: {consumo['kcal']:.0f} / {kcal_goal:.0f} kcal\n"
            f"{barra(consumo['kcal'], kcal_goal)}\n\n"
            f"🥩 Proteína: {consumo['prot']:.0f} / {prot_goal:.0f}g\n"
            f"{barra(consumo['prot'], prot_goal)}\n\n"
            f"🍚 Carboidrato: {consumo['carb']:.0f} / {carb_goal:.0f}g\n"
            f"{barra(consumo['carb'], carb_goal)}\n\n"
            f"🥑 Gordura: {consumo['fat']:.0f} / {fat_goal:.0f}g\n"
            f"{barra(consumo['fat'], fat_goal)}"
        )
    else:
        texto += (
            f"🔥 Calorias: {consumo['kcal']:.0f} kcal\n"
            f"🥩 Proteína: {consumo['prot']:.0f}g\n"
            f"🍚 Carboidrato: {consumo['carb']:.0f}g\n"
            f"🥑 Gordura: {consumo['fat']:.0f}g\n\n"
            f"💡 Use /meta para definir suas metas diárias."
        )

    bot.send_message(msg.chat.id, texto)


print("bot rodando")
bot.infinity_polling()