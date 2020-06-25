import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="snow",
  password="Aa04369484911",
  database="mydatabase"
)
mycursor = mydb.cursor()

###
#mycursor.execute("CREATE TABLE customers (name VARCHAR(255), address VARCHAR(255))")

###
#mycursor.execute("SHOW TABLES")
#for x in mycursor:
#  print(x)

###
#mycursor.execute("CREATE TABLE customers2 (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), address VARCHAR(255))")

###
#mycursor.execute("ALTER TABLE customers ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY")

###
# sql = "INSERT INTO customers (name, address) VALUES (%s, %s)"
# val = ("John", "Highway 21")
# mycursor.execute(sql, val)

# mydb.commit()

# print(mycursor.rowcount, "record inserted.")

###
# sql = "INSERT INTO customers (name, address) VALUES (%s, %s)"
# val = [
#   ('Peter', 'Lowstreet 4'),
#   ('Amy', 'Apple st 652'),
#   ('Hannah', 'Mountain 21'),
#   ('Michael', 'Valley 345'),
#   ('Sandy', 'Ocean blvd 2'),
#   ('Betty', 'Green Grass 1'),
#   ('Richard', 'Sky st 331'),
#   ('Susan', 'One way 98'),
#   ('Vicky', 'Yellow Garden 2'),
#   ('Ben', 'Park Lane 38'),
#   ('William', 'Central st 954'),
#   ('Chuck', 'Main Road 989'),
#   ('Viola', 'Sideway 1633')
# ]

# mycursor.executemany(sql, val)

# mydb.commit()

# print(mycursor.rowcount, "was inserted.")

###
# sql = "INSERT INTO customers (name, address) VALUES (%s, %s)"
# val = ("Michelle", "Blue Village")
# mycursor.execute(sql, val)

# mydb.commit()

# print("1 record inserted, ID:", mycursor.lastrowid)

###
# mycursor.execute("SELECT * FROM customers")

# myresult = mycursor.fetchall()

# for x in myresult:
#   print(x)

###
# mycursor.execute("SELECT name, id FROM customers")

# myresult = mycursor.fetchall()

# for x in myresult:
#   print(x)

###
# mycursor.execute("SELECT * FROM customers")

# myresult = mycursor.fetchone()

# print(myresult)

###
# sql = "SELECT * FROM customers WHERE address ='Park Lane 38'"

# mycursor.execute(sql)

# myresult = mycursor.fetchall()

# for x in myresult:
#   print(x)

###
# sql = "SELECT * FROM customers WHERE address LIKE '%way%'"

# mycursor.execute(sql)

# myresult = mycursor.fetchall()

# for x in myresult:
#   print(x)

###
# sql = "SELECT * FROM customers WHERE address = %s"
# adr = ("Yellow Garden 2", )

# mycursor.execute(sql, adr)

# myresult = mycursor.fetchall()

# for x in myresult:
#   print(x)

###
# sql = "SELECT * FROM customers ORDER BY id DESC"

# mycursor.execute(sql)

# myresult = mycursor.fetchall()

# for x in myresult:
#   print(x)

###
# sql = "DELETE FROM customers WHERE address = 'Highway 21'"

# mycursor.execute(sql)

# mydb.commit()

# print(mycursor.rowcount, "record(s) deleted")

###
# sql = "DELETE FROM customers WHERE address = %s"
# adr = ("Yellow Garden 2", )

# mycursor.execute(sql, adr)

# mydb.commit()

# print(mycursor.rowcount, "record(s) deleted")

###
# sql = "DROP TABLE customers2"

# mycursor.execute(sql)

###
# sql = "DROP TABLE IF EXISTS customers"

# mycursor.execute(sql)

###
# sql = "UPDATE customers SET address = 'Canyon 123' WHERE address = 'Valley 345'"

# mycursor.execute(sql)

# mydb.commit()

# print(mycursor.rowcount, "record(s) affected")

###
# mycursor.execute("SELECT * FROM customers LIMIT 5")

# myresult = mycursor.fetchall()

# for x in myresult:
#   print(x)

###
# mycursor.execute("SELECT * FROM customers LIMIT 5 OFFSET 2")

# myresult = mycursor.fetchall()

# for x in myresult:
#   print(x)

###
# sql = "SELECT \
#   users.name AS user, \
#   products.name AS favorite \
#   FROM users \
#   INNER JOIN products ON users.fav = products.id"

# mycursor.execute(sql)

# myresult = mycursor.fetchall()

# for x in myresult:
#   print(x)

###
# sql = "SELECT \
#   users.name AS user, \
#   products.name AS favorite \
#   FROM users \
#   LEFT JOIN products ON users.fav = products.id"

# mycursor.execute(sql)

# myresult = mycursor.fetchall()

# for x in myresult:
#   print(x)

###
sql = "SELECT \
  users.name AS user, \
  products.name AS favorite \
  FROM users \
  RIGHT JOIN products ON users.fav = products.id"

mycursor.execute(sql)

myresult = mycursor.fetchall()

for x in myresult:
  print(x)