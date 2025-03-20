import os
import json
import hashlib

class Session:
    def __init__(self, character_file, env_file, api_key):
        self.character_file = character_file
        self.env_file = env_file
        self.api_key = api_key
        self.session_id = self.generate_session_id()
        self.session_folder = os.path.join("sessions", f"session_{self.session_id}")

    def generate_session_id(self):
        # Generate a unique session ID using the API key
        return hashlib.sha256(self.api_key.encode()).hexdigest()

    def create_session(self):
        # Check if the session folder already exists
        if os.path.exists(self.session_folder):
            raise FileExistsError("Previous session is not closed.")

        # Create the session folder
        os.makedirs(self.session_folder)

        # Save the character file as JSON
        with open(os.path.join(self.session_folder, "character.json"), "w") as char_file:
            json.dump(self.character_file, char_file)

        # Save the env file in .env format
        with open(os.path.join(self.session_folder, ".env"), "w") as env_file:
            for key, value in self.env_file.items():
                env_file.write(f"{key}={value}\n")

        return {"message": "Session created successfully.", "session_id": self.session_id}

    def close_session(self):
        # Remove the session folder if it exists
        if os.path.exists(self.session_folder):
            for root, dirs, files in os.walk(self.session_folder, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.session_folder)
            return {"message": "Session closed successfully."}
        else:
            raise FileNotFoundError("Session does not exist.")
