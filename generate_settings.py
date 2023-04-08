import sys
import os

if __name__ == "__main__":
    if len(args := sys.argv) != 3:
        print("You should provide 2 args. Token and G-Cloud project name\nExample:\n"
              "python generate_settings.py my_token my_project")
    else:
        try:
            if os.path.exists("settings.ini"):
                print("Current file settings.ini will be rewritten")
            with open('settings.ini', 'w') as out:
                out.write(f"[BOT]\n"
                          f"bot_token = {args[1]}\n\n"
                          f"[GCLOUD]\n"
                          f"project_name = {args[2]}")
            print("settings.ini created!")
        except Exception:
            print("cant create settings.ini")
