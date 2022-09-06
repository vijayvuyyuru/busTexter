import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import pytz
import os
from twilio.rest import Client
from dotenv import load_dotenv

url = "https://www.capmetro.org/planner/?language=en_US&P=SQ&input=San%20Gabriel/25%201/2,%20Stop%20ID%204121&start=yes&widget=1.0.0&"

def get_bus_timings():
    driver = webdriver.Chrome()
    driver.get(url)
    WebDriverWait(driver, 20).until(
        EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[title='Trip Planner']")))
    all_times = [timing.text for timing in WebDriverWait(driver, 10).until(
        EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "span.lyr_timeCount")))]
    unclean_times = list(filter(lambda cur_time: ("min" in cur_time), all_times))
    cleaned_times = []
    for string_time in unclean_times:
        if "confirmed" in string_time:
            cleaned_times.append(int(string_time.split()[0]))
    return cleaned_times


def compute_best_action(times: list, goal_time: datetime):
    tz_TX = pytz.timezone('US/Central')
    current_time = datetime.now(tz_TX)
    soon_enough_buses = []
    for next_bus in times:
        if current_time + timedelta(minutes=next_bus) < goal_time:
            soon_enough_buses.append(next_bus)

    msg = f"Good morning! Here is your bus update. \n" \
          f"There {'are' if len(soon_enough_buses) > 1 or len(soon_enough_buses) == 0 else 'is'} " \
          f"{len(soon_enough_buses) if len(soon_enough_buses) > 0  else 'no' } " \
          f"{'buses' if len(soon_enough_buses) > 1 or len(soon_enough_buses) == 0 else 'bus'} that will arrive before " \
          f"{goal_time.strftime('%H:%M')}.\n"
    if len(soon_enough_buses) > 0:
        msg += "They will arrive in: \n"
        for bus in soon_enough_buses:
            msg += f"in {bus} minutes\n"
    else:
        msg += "You should walk to class today"

    account_sid = os.environ['ACCOUNT_SID']
    auth_token = os.environ['AUTH_TOKEN']
    client = Client(account_sid, auth_token)

    message = client.messages \
        .create(
        body=msg,
        from_='+19793104958',
        to=os.environ['PHONE_NUMBER']
    )
    print(message)


if __name__ == '__main__':
    load_dotenv()
    goal_time_unaware = datetime(2022, 9, 6, 11, 50)
    timezone = pytz.timezone('US/Central')
    goal_time = timezone.localize(goal_time_unaware)
    compute_best_action(get_bus_timings(), goal_time)
