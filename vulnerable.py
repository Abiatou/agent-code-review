def get_user(username):
    # Requête vulnérable à l'injection SQL
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)