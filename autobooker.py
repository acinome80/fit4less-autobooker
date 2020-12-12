from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
from pytz import timezone
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

load_dotenv()
# set permissions for local chromedriver to test locally
start_url = "https://myfit4less.gymmanager.com/portal/login.asp"
#booking_date = str(datetime.now().date() + timedelta(days=int(os.getenv("DAYS")) or 2))
chrome_options = Options()

# first condition just for debugging locally
if os.getenv("ENVIRONMENT") == "dev":
    chrome_options.add_argument("--kiosk") # use this for debugging on Linux/Mac
    # chrome_options.add_argument("--window-size=1920,1080") # use this for debugging on Windows
else:
    chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--kiosk") # use this for debugging on Linux/Mac
    chrome_options.add_argument("--window-size=3072,1920") # use this for debugging on Windows 3072 x 1920

driver = webdriver.Chrome(os.getenv("WEBDRIVER_PATH"), options=chrome_options)
driver.get(start_url)

try:
    # Login
    email_input = driver.find_element_by_id("emailaddress")
    password_input = driver.find_element_by_id("password")
    driver.implicitly_wait(5)
    email_input.send_keys(os.getenv("F4L_LOGIN"))
    password_input.send_keys(os.getenv("F4L_PASSWORD"))
    driver.implicitly_wait(5)
    password_input.send_keys(Keys.ENTER)
    driver.implicitly_wait(5)
    print("Logged In!")

    # Find your club
    if "F4L_CLUB" in os.environ:
        driver.find_element_by_id("btn_club_select").click()
        driver.implicitly_wait(3)
        all_clubs = driver.find_element_by_id("modal_clubs").find_element_by_class_name("dialog-content").find_elements_by_class_name("button")
        for club in all_clubs:
            if os.getenv("F4L_CLUB") == club.text:
                print("Club found: ", club.text)
                club.click()
                break
    
    driver.implicitly_wait(5)
    any_slots_available = False
    booked_appointment = False
    for i in range(3):        
        booking_date = str(datetime.now(timezone('est')).date() + timedelta(days=i))
        curr_dt = datetime.now(timezone('est'))
        curr_time = datetime.strptime(str(curr_dt.hour) + ":" + str(curr_dt.minute), '%H:%M')
        curr_day = (datetime.now(timezone('est')).date() + timedelta(days=i)).weekday() # 0-4 is weekday, 5-6 is weekend
        driver.find_element_by_id("btn_date_select").click()  # day selector
        driver.implicitly_wait(20)
        driver.find_element_by_id("date_" + booking_date).click()
        driver.implicitly_wait(20)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        driver.implicitly_wait(5)

        # Check current reservations
        already_have_reservation = False
        try:
            reserved_slots = driver.find_element_by_class_name("reserved-slots").find_elements_by_class_name("time-slot-box")      
            for slot in reserved_slots:
                if str(datetime.now(timezone('est')).day + i) == str(slot.text).split()[4]:
                    print("Already have reservation for the day: ", booking_date)
                    already_have_reservation = True
                    break
        except:
            pass # No reserved appointments
        if already_have_reservation == True:
            continue
                        
        # check available_slots class 2nd index -> see if child elements exist
        available_slots = driver.find_elements_by_class_name("available-slots")[1].find_elements_by_class_name("time-slot-box")
        if len(available_slots) == 0:
            print("No available time slots for " + booking_date)
            continue
        else:
            any_slots_available = True
        
        # define range of wanted time periods
        start_range = d_slot = datetime.strptime("7:00PM", '%I:%M%p')
        end_range = d_slot = datetime.strptime("10:00PM", '%I:%M%p')
        if curr_day >= 5:
            start_range = d_slot = datetime.strptime("11:00AM", '%I:%M%p')
            end_range = d_slot = datetime.strptime("6:00PM", '%I:%M%p')
   
        # check the available slots.
        for slot in available_slots:
            a_slot = datetime.strptime(str(slot.text).split()[5] + str(slot.text).split()[6], '%I:%M%p')
            
            if a_slot == curr_time or abs((a_slot - curr_time).total_seconds() / 60) <= 30:
                print("Time slot: {} is too close to current time. Curr time: {}".format(a_slot.strftime("%I:%M %p"), curr_time.strftime("%I:%M %p")))
                continue
                
            if start_range <= a_slot and end_range >= a_slot:
                slot.find_element_by_xpath('..').click()
                driver.implicitly_wait(10)
                driver.find_element_by_id("dialog_book_yes").click()
                driver.implicitly_wait(10)
                print("Booked {} on {}".format(a_slot.strftime("%I:%M %p"),booking_date))
                booked_appointment = True
                break
            else:
                print("Skipping slot: {}".format(a_slot.strftime("%I:%M %p")))
    if any_slots_available == False:
        print("No available slots at all")
        exit(1)
    elif booked_appointment == False:
        print("No appointment booked.")
        exit(1)        

except Exception as err:
    print("Seems like we're fully booked!")
    print(str(err))
    exit(1)
finally:
    driver.quit()
