from cryptography.fernet import Fernet

def encrypt_database(input_file, output_file, key):
    """
    Encrypts the SQLite database file.
    :param input_file: Path to the original database file.
    :param output_file: Path to save the encrypted database file.
    :param key: Encryption key (generated using Fernet).
    """
    # Read the original database file
    with open(input_file, 'rb') as f:
        data = f.read()

    # Encrypt the data
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(data)

    # Save the encrypted data to a new file
    with open(output_file, 'wb') as f:
        f.write(encrypted_data)

# Generate a key (do this once and save the key securely)
key = Fernet.generate_key()
print(f"Encryption Key: {key.decode()}")  # Save this key securely

# Encrypt the database
encrypt_database('local_database.db', 'encrypted_database.db', key)