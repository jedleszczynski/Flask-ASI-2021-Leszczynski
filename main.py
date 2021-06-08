from app import app
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
#os.environ['FLASK_ENV']='development'
if __name__ == "__main__":
  app.run(
    host='0.0.0.0', 
    port=8080, debug=True)