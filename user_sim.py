from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import base64
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import sys


if len(sys.argv) < 3 or (sys.argv[1] != 'guest' and len(sys.argv) < 4):
    print ("user_sim <login> <passwd> <iterations>  OR  user_sim guest <iterations>")
    sys.exit(1)

user = sys.argv[1]
if user != 'guest':
    passwd = sys.argv[2]
    iteration = int(sys.argv[3])
else:
    iteration = int(sys.argv[2])
    
# instance of Options class allows
# us to configure Headless Chrome
options = Options()
  
# this parameter tells Chrome that
# it should be run without UI (Headless)
#options.headless = True
  
# initializing webdriver for Chrome with our options
driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 90)


for i in range(1, iteration + 1):
    driver.get("http://localhost:8080/server/nocache/login.html")
    time.sleep(0.5)
    
    if user != 'guest':
        e1 = driver.find_element(By.ID,"login_username")
        e1.send_keys(user)
    
        e2 = driver.find_element(By.ID,"login_password")
        e2.send_keys(passwd)
        
        bt = driver.find_element(By.ID, 'login_button')
        bt.click()
    else:
        if i == 1:
            bt = driver.find_element(By.ID, 'guest_button')
            bt.click()
            time.sleep(1)
        driver.get("http://localhost:8080/submit/nocache/index.html")
    
    
    # We can also get some information
    # about page in browser.
    # So let's output webpage title into
    # terminal to be sure that the browser
    # is actually running. 
    print(driver.title)
    

    wait.until(EC.presence_of_element_located((By.ID,'jobdivspinnerdiv')))
    spin = driver.find_element(By.ID, 'jobdivspinnerdiv')
    wait.until(EC.invisibility_of_element(spin));
    time.sleep(0.5)

    
    driver.get("http://localhost:8080/submit/nocache/index.html")
      
    wait.until(EC.presence_of_element_located((By.ID,'jobdivspinnerdiv')))
    spin = driver.find_element(By.ID, 'jobdivspinnerdiv')
    wait.until(EC.invisibility_of_element(spin));
    time.sleep(0.5)
    
    driver.get("http://localhost:8080/submit/nocache/index.html")
      
    wait.until(EC.presence_of_element_located((By.ID,'jobdivspinnerdiv')))
    spin = driver.find_element(By.ID, 'jobdivspinnerdiv')
    wait.until(EC.invisibility_of_element(spin));
    time.sleep(0.5)
    
    if user != 'guest'  or i == iteration:
        #wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@title="Logout"]')))
        bt = driver.find_element(By.XPATH, '//*[@title="Logout"]')
        bt.click()
        wait.until(EC.presence_of_element_located((By.ID,'logindiv')))


# close browser after our manipulations
driver.close()