from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt

pepperstring = "ASI2019"

## ABSOLUTNIE NIEBEZPIECZE METODY HASHOWANIA 
# PATRZ NA @app.route('/hash/<string:test>' w pliku main.py
def hash_string_sha(passwd):
  return generate_password_hash(str(passwd)+pepperstring, 'sha256')

def check_string_sha(passwd, generatedhash):
  # print ("passwd:", str(passwd)+pepperstring)
  return check_password_hash(generatedhash, str(passwd)+pepperstring)

## BEZPIECZNE METODY
## Dzisiaj już nikt recznie nie korzysta z SHA, albo o zgrozo hashy typu MD5
## Używa się np. bcrypt - https://www.npmjs.com/package/bcrypt
def gensalt_bcrypt():
  return bcrypt.gensalt(12)

def hash_string_bcrypt(passwrd, salt):
  if isinstance(passwrd, str):
    passwrd = passwrd.encode('utf-8')
  if isinstance(salt, str):
    salt = salt.encode('utf-8')  
  return bcrypt.hashpw(passwrd, salt)

def check_string_bcrypt(plain_text_password, salt, hashed_password):
  if isinstance(plain_text_password, str):
      plain_text_password = plain_text_password.encode('utf-8')
  if isinstance(salt, str):
      salt = salt.encode('utf-8')
  return bcrypt.hashpw(plain_text_password, salt) == hashed_password
