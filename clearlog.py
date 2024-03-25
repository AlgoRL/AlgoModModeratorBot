import sys
import json

def clear_logs(username):
    try:
        with open("warnings_log.json", "r+") as file:
            data = json.load(file)
            if username in data:
                del data[username]
                file.seek(0)
                json.dump(data, file, indent=4)
                print(f"Warning logs for user '{username}' cleared successfully.")
            else:
                print(f"User '{username}' not found in the warning logs.")
    except FileNotFoundError:
        print("Warning logs file not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python clearlog.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    clear_logs(username)
