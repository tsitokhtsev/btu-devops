import json

import mysql.connector
import requests


def check_connection(conn):
    try:
        conn.ping()
        return True
    except mysql.connector.Error as e:
        print("Error connecting to database:", e)
        return False


def view_movies_by_genre(conn, genre):
    cursor = conn.cursor()
    query = """
    SELECT *
    FROM 1990s_movies
    WHERE FIND_IN_SET(%s, genres) > 0
    LIMIT 5
    """
    cursor.execute(query, (genre,))
    movies = cursor.fetchall()
    cursor.close()

    return movies


def suggest_movies_by_cast(conn, cast_member):
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM 1990s_movies WHERE FIND_IN_SET(%s, cast) > 0", (cast_member,)
    )
    movies = cursor.fetchall()
    cursor.close()
    return movies


def main():
    conn = mysql.connector.connect(
        host="btu-db-1.c4uqlpxptwgg.us-east-1.rds.amazonaws.com",
        port=3306,
        user="admin",
        password="rng3k9HDLZOwWFRLoVmK",
    )

    if not check_connection(conn):
        exit(1)

    cursor = conn.cursor()

    database = "myDB"

    url = "https://raw.githubusercontent.com/prust/wikipedia-movie-data/master/movies-1990s.json"
    response = requests.get(url)
    data = json.loads(response.content.decode("utf-8"))

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database};")
    cursor.execute(f"USE {database};")
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS 1990s_movies (title VARCHAR(255), year INT, genres VARCHAR(255), cast VARCHAR(255), href VARCHAR(255), extract TEXT, thumbnail VARCHAR(255), thumbnail_width INT, thumbnail_height INT)"
    )

    rows = []
    for item in data:
        title = item.get("title", None)
        year = item.get("year", None)
        genres = ",".join(item.get("genres", []))
        cast = ",".join(item.get("cast", []))
        href = item.get("href", None)
        extract = item.get("extract", None)
        thumbnail = item.get("thumbnail", None)
        thumbnail_width = item.get("thumbnail_width", None)
        thumbnail_height = item.get("thumbnail_height", None)

        row = (
            title,
            year,
            genres,
            cast,
            href,
            extract,
            thumbnail,
            thumbnail_width,
            thumbnail_height,
        )
        rows.append(row)

    cursor.executemany(
        "INSERT INTO 1990s_movies (title, year, genres, cast, href, extract, thumbnail, thumbnail_width, thumbnail_height) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        rows,
    )
    conn.commit()
    print("seed - succesfull")

    # genre = input("Enter a genre to view movies: ")
    # movies = view_movies_by_genre(conn, genre)
    # if movies:
    #   for movie in movies:
    #     print(movie)
    # else:
    #   print("No movies found for the given genre.")

    # cast_member = input("Enter the name of a cast member to suggest movies: ")
    # movies = suggest_movies_by_cast(conn, cast_member)
    # if movies:
    #   for movie in movies:
    #     print(movie)
    # else:
    #   print("No movies found featuring the given cast member.")

    conn.close()


if __name__ == "__main__":
    main()
