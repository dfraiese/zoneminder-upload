#!/usr/bin/env python
# -*- coding: utf-8
#!/usr/bin/python

import os
import sys
import datetime 
import time
import dropbox
import imageio
import fnmatch
import pymysql
import smtplib
import fcntl
from datetime import timedelta

def lockear_file(oPath):
    try:
        x = open(oPath + "/" + "log.txt", 'w+')
        fcntl.flock(x, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except Exception, e:
        return False
    else:
        return True
    finally:
        fcntl.flock(x, fcntl.LOCK_UN)
   
def error_general(codigoError, descError, respError, oOut="", oPath=""):
    msgError = "ERROR - " + str(codigoError) + " " + str(descError) + " " + str(respError) + "\n"
    
    if oOut == "LOG":
        f = open(oPath + "/" + "log.txt", "a+")
        f.write(str(datetime.datetime.now()) + " " + msgError)
        f.close
    else:
        print msgError 
        
    sys.exit()


def aviso(codigoAviso, descAviso, respAviso, oOut="", oPath=""):
    msgAviso = str(codigoAviso) + " " + str(descAviso) + " " + str(respAviso) + "\n"
    
    if oOut == "LOG":
        f = open(oPath + "/" + "log.txt", "a+")
        f.write(str(datetime.datetime.now()) + " " + msgAviso)
        f.close
    else:
        print msgAviso

    
def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)

inicio = datetime.datetime.now()
path = "YOUR_LOCAL_PATH_HERE"
token = "YOUR_TOKEN_HERE"

token_gmail = "646965676f66726169657365"

cnx = pymysql.connect(host="localhost", user="root", passwd="YOUR_PSW_MYSQL_ZONEMINDER", db="zm")
cursor = cnx.cursor()

query = "select StartTime from Eventos a \
         where Cause = 'Motion' \
         and StartTime = (select max(StartTime) from Eventos where Cause = a.Cause) "

lstFiles = []

if __name__ == "__main__":
    if not lockear_file(path):
        sys.exit()
        
    try:
        cursor.execute(query)
        
        row = cursor.fetchone()
        
        FechaEvento = row[0]
        
        cursor.close()
        cnx.close()
    except Exception, e:
        error_general(1001, "ERROR SELECT TABLEX", e, "LOG", path)    
    else:
        aviso(1001, "SELECT TABLE OK", "OK " + str(FechaEvento), "LOG", path)    
        
    try:
        client = dropbox.client.DropboxClient(token)    
    except Exception, e:
        error_general(1002, "ERROR CONNECT DROPBOX", e)    
    else:
        aviso(1002, "CONNECT DROPBOX", "OK", "LOG", path)

    lstDir = os.walk(path)
    lstFiles = []
    image_jpg = []
    image_gif = []
    
    rootAux = ""
    i = 1
    
    for root, dirs, files in lstDir:
        for filename in files:
            if os.path.splitext(filename)[1] == ".jpg":
                
                if root != rootAux:
                    if (modification_date(root + "/" + filename) > (FechaEvento-timedelta(minutes=10))) \
                        and (FechaEvento > inicio-timedelta(days=10)):
                            
                        image_jpg.append(os.path.join(root, filename))
                
                filepath = os.path.join(root, filename)
                lstFiles.append(filepath)  
        
        image_jpg_sort = sorted(image_jpg)
        
        if len(image_jpg_sort) != 0:
            images = []
                        
            for f_jpg in image_jpg_sort:
                images.append(imageio.imread(f_jpg))
                
            filename_gif = "_" + str(i) + ".gif"
            
            imageio.mimsave(path + "/" + filename_gif, images)
            aviso(1003, "GIF FINALIZADO", "OK " + filename_gif, "LOG", path)
            
            image_gif.append(path + "/" + filename_gif)
        
            i = i + 1
            image_jpg = []       
            
        rootAux = root
      
    aviso(1004, "GIFS FINALIZADO", "OK", "LOG", path)
    
    for i in image_gif:
        try:
            f = open(i, "rb")

            nameFile = str(modification_date(i)).replace("-","")
            nameFile = nameFile.replace(" ", "_")
            nameFile = nameFile.replace(":", "")
            nameFile = nameFile.replace(".", "_")
            
            response = client.put_file("/ZM/" + nameFile + ".gif", f, overwrite=True)
        except Exception, e:
            error_general(1006, "ERROR UPLOAD DROPBOX", e)    
        else:
            aviso(1006, "UPLOAD DROPBOX", "OK " + i + "->" + nameFile + ".gif", "LOG", path)

    try:
        for j in fnmatch.filter(image_gif, '*.gif'):
            os.unlink(os.path.join(path, j))
    except Exception, e: 
        error_general(1007, "ERROR DELETE GIFS", e)        
    else:
        aviso(1007, "DELETE GIFS", "OK", "LOG", path)
        
    aviso(1008, "SCRIPT FINALIZADO", "OK", "LOG", path)
    
    print "fin"
