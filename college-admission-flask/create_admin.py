from werkzeug.security import generate_password_hash
import mysql.connector

# Connect to database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='ads'
)
cursor = conn.cursor()

password_hash = generate_password_hash('testing1234')

# Create or update admin account
cursor.execute("""
    INSERT INTO users (email, password) 
    VALUES ('admin@gmail.com', %s)
    ON DUPLICATE KEY UPDATE password = %s
""", (password_hash, password_hash))

conn.commit()
conn.close()

print("✅ Admin account created/updated successfully!")
print("Email: admin@gmail.com")
print("Password: testing1234")