def wpisz_do_logu(timestamp,level,data):
  with open('mojlog.log', 'a', newline='\n') as file:
    file.write('{0} {1} : {2}'.format(timestamp,level,data)) 
    #logwriter = csv.writer(file, delimiter=' ')
    #logwriter.writerow('{0} {1} : {2}'.format(timestamp,level,data))
  file.close()