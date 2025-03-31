import tempfile
import shutil
import os
import subprocess

def set_persistent_env_var(key, value):
    """
    Set or update a persistent environment variable in /etc/environment.
    The change is immediately applied and persists after reboots.
    
    Requires root privileges.
    """
    env_file = "/etc/environment"
    temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)

    try:
        with open(env_file, "r") as f, temp_file:
            updated = False
            for line in f:
                if line.strip().startswith(f"{key}="):  
                    temp_file.write(f'{key}="{value}"\n')  # Update existing key
                    updated = True
                else:
                    temp_file.write(line)

            if not updated:  
                temp_file.write(f'{key}="{value}"\n')  # Add new key if missing

        # Replace original file safely
        shutil.move(temp_file.name, env_file)

        # Apply changes immediately
        subprocess.run(["source", env_file], shell=True, check=False)
        os.environ[key] = value  # Update current process environment

        print(f"✅ Successfully set {key} in {env_file} and reloaded environment.")

    except Exception as e:
        print(f"❌ Error updating {env_file}: {e}")
    finally:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)  # Cleanup if error occurs