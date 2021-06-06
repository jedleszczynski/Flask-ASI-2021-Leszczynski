from datetime import date
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from passhasher import hash_string_bcrypt, check_string_bcrypt, gensalt_bcrypt

engine = create_engine('sqlite:///tutorial.db', echo=True)
Base = declarative_base()

class User(Base):
  __tablename__ = "users"
  id = Column(Integer, primary_key=True, autoincrement=True)
  username = Column(String, index=False)
  password = Column(String)
  saltstring = Column(String)

  def __init__(self, username, password):
    self.username = username
    self.saltstring = gensalt_bcrypt()
    self.password =  hash_string_bcrypt(password, self.saltstring)
    

  def check_password(self, passwordstring):
    print ("SALT when retrieved from user object: \t",str(self.saltstring))
    return check_string_bcrypt(passwordstring, self.saltstring, self.password)

# create a Session
def return_sqlalchemysession():
  Session = sessionmaker(bind=engine)
  session = Session()
  return session

class Grade(Base):
  __tablename__ = "grades"
  id = Column(Integer, primary_key=True, autoincrement=True)
  student_id = Column(Integer, ForeignKey('users.id')) #we specify column after .
  grade = Column(String(10))
  grade_date = Column(Date)

  def __init__(self, grade, grade_date, student_id):
    self.grade = grade
    self.grade_date = grade_date
    self.student_id = student_id
    


Base.metadata.create_all(engine)


sqlsession = return_sqlalchemysession()
user = User("admin","admin")
sqlsession.add(user)
user = User("igor","igor")
sqlsession.add(user)

for x in ["2", "3", "3.5", "4", "4.5", "5", "3.5", "2", "3.5"]:
  #date according to the https://docs.sqlalchemy.org/en/13/core/type_basics.html#sqlalchemy.types.Date
  #dodumentation
  grade = Grade(x, date.today(), 1)
  sqlsession.add(grade)

sqlsession.commit()