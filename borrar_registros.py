
import configparser
import mysql.connector


parser = configparser.ConfigParser()
parser.read('config_autoconsumido.ini')


# Parametros de BBDD (user=DB_USER, password=DB_PASS, host=DB_HOST, database=DB_NAME)
DB_HOST = parser.get('database_server', 'db_host')
DB_USER = parser.get('database_server', 'db_user')
DB_PASS = parser.get('database_server', 'db_pass')
DB_NAME = parser.get('database_server', 'db_name')


conexion = mysql.connector.connect(user=DB_USER, password=DB_PASS, host=DB_HOST, database=DB_NAME)
conexion._open_connection()
cursor = conexion.cursor(buffered=True)


sql = "select cups, id_user from cometa.user_info WHERE nif = '12345678Z'"

cursor.execute(sql)
rowData = cursor.fetchone()

print("Row Data: " + str(rowData))

'''
user_counter
-----------
id_user_counter
id_user
timestamp
exported_energy
imported_energy
self_consumed_energy

'''

# sentenciaInsert = "DELETE FROM cometa.user_counter WHERE timestamp = '2022-05-05 10:01:00' AND id_user = 12 "
sentenciaInsert = "DELETE FROM cometa.user_counter WHERE id_user = 13 OR id_user = 14"

cursor.execute(sentenciaInsert)
cursor.close()
conexion.commit()