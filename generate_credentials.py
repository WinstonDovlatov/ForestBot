import sys
import os

if __name__ == "__main__":
    if len(args := sys.argv) != 3:
        print("\nYou should provide 2 args. Token and G-Cloud project name\n\nExample:\n"
              "python generate_credentials.py my_token my_project\n")
    else:
        try:
            if os.path.exists("credentials.ini"):
                print("Current file credentials.ini will be rewritten")
            with open('credentials.ini', 'w') as out:
                out.write(f"[BOT]\n"
                          f"bot_token = {args[1]}\n\n"
                          f"[GCLOUD]\n"
                          f"project_name = {args[2]}\n")
            print("credentials.ini created!")
        except Exception:
            print("cant create credentials.ini")
