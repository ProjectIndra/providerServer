import os

def load_env(env_file=".env"):

    if not os.path.exists(env_file):
        # create the file if it does not exist
        with open(env_file, "w") as f:
            f.write("")  # create an empty .env file
            
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                key, value = line.strip().split("=", 1)
                os.environ[key] = value.strip('"')

def set_persistent_env_var(key, value, env_file=".env"):
    """
    Set or update an environment variable in a project-specific .env file.
    The change does not persist globally but can be sourced manually.
    """

    lines = []
    updated = False

    # Read existing .env file if it exists
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                if line.strip().startswith(f"{key}="):  
                    lines.append(f'{key}="{value}"\n')  # Update existing key
                    updated = True
                else:
                    lines.append(line)

    if not updated:  
        lines.append(f'{key}="{value}"\n')  # Add new key if missing

    # Write back to .env file
    with open(env_file, "w") as f:
        f.writelines(lines)

    # now update the environment variable
    load_env(env_file)

    print(f"✅ Successfully set {key} in {env_file}.")

if __name__ == "__main__":
    set_persistent_env_var("MY_VARIABLE", "hello_world")
