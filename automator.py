from flask import Flask, request, jsonify, send_from_directory
from urllib.parse import quote
from time import sleep
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import os
import shutil
import subprocess

app = Flask(__name__)

def clean_old_files():
    try:
        chrome_user_data_dir = "/var/tmp/chrome_user_data"
        if os.path.exists(chrome_user_data_dir):
            shutil.rmtree(chrome_user_data_dir)
            print(f"Removed directory: {chrome_user_data_dir}")
    except Exception as e:
        print(f"Error cleaning old files: {str(e)}")

def kill_chrome_processes():
    try:
        subprocess.run(["pkill", "-f", "chrome"], check=True)
        print("Killed all Chrome processes")
    except subprocess.CalledProcessError:
        print("No Chrome processes were found to kill.")
    except Exception as e:
        print(f"Error killing Chrome processes: {str(e)}")

def initialize_webdriver():
    clean_old_files()
    
    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--user-data-dir=/var/tmp/chrome_user_data")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-session-crashed-bubble")

    chrome_driver_path = "/usr/bin/chromedriver-linux64/chromedriver"

    if not os.path.exists(chrome_driver_path):
        return None, "ChromeDriver not found at specified path."

    try:
        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        return driver, None
    except Exception as e:
        return None, str(e)

def send_whatsapp_message(numbers, message):
    driver, error = initialize_webdriver()
    if error:
        return {"error": f"Error initializing the WebDriver: {error}"}

    print('Once your browser opens up sign in to web whatsapp')
    driver.get('https://web.whatsapp.com')

    message = quote(message)

    for idx, number in enumerate(numbers):
        number = number.strip()
        if number == "":
            continue
        print(f'Sending message to {number}.')
        try:
            url = f'https://web.whatsapp.com/send?phone={number}&text={message}'
            sent = False
            for i in range(3):
                if not sent:
                    driver.get(url)
                    try:
                        click_btn = WebDriverWait(driver, 60).until(
                            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Send']"))
                        )
                    except Exception as e:
                        print(f"Failed to send message to: {number}, retry ({i+1}/3)")
                        print("Make sure your phone and computer is connected to the internet.")
                        print("If there is an alert, please dismiss it.")
                        try:
                            alert = driver.switch_to.alert
                            alert.accept()
                            print("Alert dismissed")
                        except:
                            pass
                    else:
                        sleep(1)
                        click_btn.click()
                        sent = True
                        sleep(3)
                        print(f'Message sent to: {number}')
        except Exception as e:
            print(f'Failed to send message to {number} {str(e)}')

    driver.close()
    return {"status": "Messages sent successfully"}

@app.route('/send', methods=['POST'])
def send_message():
    data = request.get_json()
    numbers = data.get('numbers')
    message = data.get('message')

    if isinstance(numbers, str):
        numbers = [numbers]

    if not numbers or not message:
        return jsonify({"error": "Invalid input"}), 400

    result = send_whatsapp_message(numbers, message)
    return jsonify(result)

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
