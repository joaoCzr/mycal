from db import conexao, cursor


def get_or_create_user_db(telegram_id, nome):
    sql_select = """
        SELECT id
        FROM users
        WHERE mtelegram_id = %s
    """

    cursor.execute(sql_select, (telegram_id,))
    user = cursor.fetchone()

    if user:
        return user[0]

    sql_insert = """
        INSERT INTO users (nome, mtelegram_id, senha_hash)
        VALUES (%s, %s, '')
    """

    cursor.execute(sql_insert, (nome, telegram_id))
    conexao.commit()

    return cursor.lastrowid


def add_food_db(name_food, prot, carb, fat):
    sql_add = """
        INSERT INTO foods (name_food, prot, carb, fat) 
        VALUES (%s, %s, %s, %s)
    """

    cursor.execute(sql_add, (name_food, prot, carb, fat))
    conexao.commit()


def view_food_db():
    sql_read = """
        SELECT id_food, name_food, prot, carb, fat
        FROM foods
        ORDER BY id_food
    """

    cursor.execute(sql_read)
    return cursor.fetchall()


def edit_food_db(id_food, name_food, prot, carb, fat):
    sql_edit = """
        UPDATE foods
        SET name_food = %s, prot = %s, carb = %s, fat = %s
        WHERE id_food = %s
    """

    cursor.execute(sql_edit, (name_food, prot, carb, fat, id_food))
    conexao.commit()

    return cursor.rowcount


def delete_food_db(id_food):
    sql_delete = """
        DELETE FROM foods
        WHERE id_food = %s
    """

    cursor.execute(sql_delete, (id_food,))
    conexao.commit()

    return cursor.rowcount


def create_meal_db(user_id, name_meal):
    sql = """
        INSERT INTO meals (user_id, name_meal)
        VALUES (%s, %s)
    """

    cursor.execute(sql, (user_id, name_meal))
    conexao.commit()

    return cursor.lastrowid


def add_food_to_meal_db(meal_id, food_id, quantity_grams):
    sql = """
        INSERT INTO meal_items (meal_id, food_id, quantity_grams)
        VALUES (%s, %s, %s)
    """

    cursor.execute(sql, (meal_id, food_id, quantity_grams))
    conexao.commit()


def set_meta_db(user_id, calories_goal, prot_goal, carb_goal, fat_goal):
    cursor.execute("SELECT id_goal FROM user_goals WHERE user_id = %s", (user_id,))
    existing = cursor.fetchone()

    if existing:
        sql = """
            UPDATE user_goals
            SET calories_goal = %s, prot_goal = %s, carb_goal = %s, fat_goal = %s
            WHERE user_id = %s
        """
        cursor.execute(sql, (calories_goal, prot_goal, carb_goal, fat_goal, user_id))
    else:
        sql = """
            INSERT INTO user_goals (user_id, calories_goal, prot_goal, carb_goal, fat_goal)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (user_id, calories_goal, prot_goal, carb_goal, fat_goal))

    conexao.commit()


def get_meta_db(user_id):
    sql = """
        SELECT calories_goal, prot_goal, carb_goal, fat_goal
        FROM user_goals
        WHERE user_id = %s
    """
    cursor.execute(sql, (user_id,))
    return cursor.fetchone()


def get_daily_status_db(user_id):
    sql = """
        SELECT
            SUM(f.prot * mi.quantity_grams / 100),
            SUM(f.carb * mi.quantity_grams / 100),
            SUM(f.fat * mi.quantity_grams / 100),
            SUM((f.prot * 4 + f.carb * 4 + f.fat * 9) * mi.quantity_grams / 100)
        FROM meal_items mi
        INNER JOIN foods f ON mi.food_id = f.id_food
        INNER JOIN meals m ON mi.meal_id = m.id_meal
        WHERE m.user_id = %s
          AND DATE(m.created_at) = CURDATE()
    """
    cursor.execute(sql, (user_id,))
    row = cursor.fetchone()

    return {
        "prot": float(row[0] or 0),
        "carb": float(row[1] or 0),
        "fat": float(row[2] or 0),
        "kcal": float(row[3] or 0),
    }


def calculate_meal_macros_db(meal_id):
    sql = """
        SELECT 
            f.name_food,
            mi.quantity_grams,
            f.prot,
            f.carb,
            f.fat
        FROM meal_items mi
        INNER JOIN foods f ON mi.food_id = f.id_food
        WHERE mi.meal_id = %s
    """

    cursor.execute(sql, (meal_id,))
    foods = cursor.fetchall()

    total_prot = 0
    total_carb = 0
    total_fat = 0
    total_kcal = 0

    food_details = []

    for food in foods:
        name_food = food[0]
        quantity = float(food[1])
        prot_100g = float(food[2])
        carb_100g = float(food[3])
        fat_100g = float(food[4])

        prot_total = prot_100g * quantity / 100
        carb_total = carb_100g * quantity / 100
        fat_total = fat_100g * quantity / 100
        kcal_total = (prot_total * 4) + (carb_total * 4) + (fat_total * 9)

        total_prot += prot_total
        total_carb += carb_total
        total_fat += fat_total
        total_kcal += kcal_total

        food_details.append({
            "name_food": name_food,
            "quantity": quantity,
            "prot": prot_total,
            "carb": carb_total,
            "fat": fat_total,
            "kcal": kcal_total
        })

    return {
        "foods": food_details,
        "total_prot": total_prot,
        "total_carb": total_carb,
        "total_fat": total_fat,
        "total_kcal": total_kcal
    }