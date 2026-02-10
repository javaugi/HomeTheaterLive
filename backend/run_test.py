import sys
import psycopg
import sqlalchemy
import jwt
sys.stdout.reconfigure(encoding="utf-8")

def main():
    print("Hello, world! The main function is running.")
    print("Printing emoji: Hello World! \U0001f600")
    print("Printing emoji: Hello World! 🔍 \U0001f50d")

    print(f"psycopg version: {psycopg.__version__}")
    print(f"jwt version: {jwt.__version__}")
    print(f"sqlalchemy version: {sqlalchemy.__version__}")
    print('Sys Paths: \n'.join(sys.path))


if __name__ == "__main__":
    # This block executes when the script is run directly
    main()# -*- coding: utf-8 -*-

