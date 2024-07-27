import json
import bcrypt

def hash_passwords(users):
    for user in users:
        password = user['password'].encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password, salt)
        user['password'] = hashed.decode('utf-8')  # Store as string
    return users

# Read the current users.json file
with open('users.json', 'r') as f:
    data = json.load(f)

# Hash the passwords
data['users'] = hash_passwords(data['users'])

# Write the updated data back to users.json
with open('users.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Passwords hashed and users.json updated successfully.")