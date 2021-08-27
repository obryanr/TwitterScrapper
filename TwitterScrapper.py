import pandas as pd
import os
import csv
from time import sleep
# from msedge.selenium_tools import Edge, EdgeOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.common import exceptions
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

def create_chrome_webdriver():
  chromeOptions = Options()
  chromeOptions.add_argument('--headless')
  prefs = {"profile.managed_default_content_settings.images": 2}
  chromeOptions.add_experimental_option("prefs", prefs)
  driver = webdriver.Chrome(options=chromeOptions)
  return driver

# def create_edge_webdriver():
#     options = EdgeOptions()
#     options.use_chromium = True
#     driver = Edge(options=options)
#     return driver


def login_to_twitter(username, password, driver):
    url = 'https://twitter.com/login'
    try:
        driver.get(url)
        xpath_username = '//input[@name="session[username_or_email]"]'
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.XPATH, xpath_username)))
        uid_input = driver.find_element_by_xpath(xpath_username)
        uid_input.send_keys(username)
    except exceptions.TimeoutException:
        print("Timeout while waiting for Login screen")
        return False

    pwd_input = driver.find_element_by_xpath('//input[@name="session[password]"]')
    pwd_input.send_keys(password)
    try:
        pwd_input.send_keys(Keys.RETURN)
        url = "https://twitter.com/home"
        WebDriverWait(driver, 10).until(expected_conditions.url_to_be(url))
    except exceptions.TimeoutException:
        print("Timeout while waiting for home screen")
    return True


def find_search_input_and_enter_criteria(search_term, driver):
    sleep(5)
    xpath_search = '//input[@aria-label="Search query"]'
    search_input = driver.find_element_by_xpath(xpath_search)
    search_input.send_keys(search_term)
    search_input.send_keys(Keys.RETURN)
    return True


def change_page_sort(tab_name, driver):
    """Options for this program are `Latest` and `Top`"""
    tab = driver.find_element_by_link_text(tab_name)
    tab.click()
    xpath_tab_state = f'//a[contains(text(),\"{tab_name}\") and @aria-selected=\"true\"]'


def generate_tweet_id(tweet):
    return ''.join(tweet)


def scroll_down_page(driver, last_position, num_seconds_to_load=0.5, scroll_attempt=0, max_attempts=5):
    """
    The function will try to scroll down the page and will check the current
    and last positions as an indicator. 
    """
    end_of_scroll_region = False
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    sleep(num_seconds_to_load)
    curr_position = driver.execute_script("return window.pageYOffset;")
    if curr_position == last_position:
        if scroll_attempt < max_attempts:
            end_of_scroll_region = True
        else:
            scroll_down_page(last_position, curr_position, scroll_attempt + 1)
    last_position = curr_position
    return last_position, end_of_scroll_region


def save_tweet_data_to_csv(records, filepath, mode='a+'):
    header = ['User', 'Handle', 'PostDate', 'TweetText', 'ReplyCount', 'RetweetCount', 'LikeCount']
    with open(filepath, mode=mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if mode == 'w':
            writer.writerow(header)
        if records:
            writer.writerow(records)


def collect_all_tweets_from_current_view(driver, lookback_limit=25):
    """
    set the
    "lookback_limit" to only process the last "x" number of tweets extracted from the page in each iteration.
    """
    page_cards = driver.find_elements_by_xpath('//div[@data-testid="tweet"]')
    if len(page_cards) <= lookback_limit:
        return page_cards
    else:
        return page_cards[-lookback_limit:]


def extract_data_from_current_tweet_card(card):
    try:
        user = card.find_element_by_xpath('.//span').text
    except exceptions.NoSuchElementException:
        user = ""
    except exceptions.StaleElementReferenceException:
        return
    try:
        handle = card.find_element_by_xpath('.//span[contains(text(), "@")]').text
    except exceptions.NoSuchElementException:
        handle = ""
    try:
        """
        If there is no post date here, there it is usually sponsored content, or some
        other form of content where post dates do not apply. 
        """
        postdate = card.find_element_by_xpath('.//time').get_attribute('datetime')
    except exceptions.NoSuchElementException:
        return
    try:
        _comment = card.find_element_by_xpath('.//div[2]/div[2]/div[1]').text
    except exceptions.NoSuchElementException:
        _comment = ""
    try:
        _responding = card.find_element_by_xpath('.//div[2]/div[2]/div[2]').text
    except exceptions.NoSuchElementException:
        _responding = ""
    tweet_text = _comment + ' ' + _responding
    try:
        reply_count = card.find_element_by_xpath('.//div[@data-testid="reply"]').text
    except exceptions.NoSuchElementException:
        reply_count = ""
    try:
        retweet_count = card.find_element_by_xpath('.//div[@data-testid="retweet"]').text
    except exceptions.NoSuchElementException:
        retweet_count = ""
    try:
        like_count = card.find_element_by_xpath('.//div[@data-testid="like"]').text
    except exceptions.NoSuchElementException:
        like_count = ""

    tweet = (user, handle, postdate, tweet_text, reply_count, retweet_count, like_count)
    return tweet


def main(username, password, search_term, filepath, page_sort='Latest'):
    save_tweet_data_to_csv(None, filepath, 'w')  # create file for saving records
    last_position = None
    end_of_scroll_region = False
    unique_tweets = set()

    driver = create_chrome_webdriver()
    driver.maximize_window()
    logged_in = login_to_twitter(username, password, driver)
    if not logged_in:
        return

    search_found = find_search_input_and_enter_criteria(search_term, driver)
    if not search_found:
        return

    change_page_sort(page_sort, driver)

    while not end_of_scroll_region:
        cards = collect_all_tweets_from_current_view(driver)
        for card in cards:
            try:
                tweet = extract_data_from_current_tweet_card(card)
            except exceptions.StaleElementReferenceException:
                continue
            if not tweet:
                continue
            tweet_id = generate_tweet_id(tweet)
            if tweet_id not in unique_tweets:
                unique_tweets.add(tweet_id)
                save_tweet_data_to_csv(tweet, filepath)
        last_position, end_of_scroll_region = scroll_down_page(driver, last_position)
    driver.quit()

    
if __name__ == "__main__":
    keyword = input('Masukkan keyword yang ingin dicari: ')
    year = int(input("Masukkan tahun: "))
    start_month = int(input("Masukkan bulan mulai: "))
    end_month = int(input("Masukkan bulan berakhir: "))
    start = int(input("Masukkan hari tanggal mulai: "))
    end = int(input("Masukkan hari tanggal berakhir: "))
    print('-'*30)
    print(f"Data '{keyword}' akan diambil mulai tanggal {str(start)+'-'+str(start_month)+'-'+str(year)} hingga {str(end)+'-'+str(end_month)+'-'+str(year)}")

    for month in range(start_month, end_month+1):
        for i in range(start, end+1):
            if __name__ == '__main__':
                usr = 'username'
                pwd = 'twitterpassword'
                path = '{}_{}_{}_{}.csv'.format(str(keyword), str(i),str(month), str(year))
                term = f'{keyword} -VCS -PO lang:id until:{str(year)}-0{str(month)}-0{str(i+1)} since:{str(year)}-0{str(month)}-0{str(i)}'
                try:
                    main(usr, pwd, term, path)
                except Exception as e:
                    print(e)
                    print("Next day ...")

    list_files = [file for file in os.listdir() if file.endswith('.csv')]
    new_df = pd.DataFrame()
    for file in list_files:
        df = pd.read_csv(file)
        new_df = pd.concat([new_df, df], axis=0, ignore_index=True)

    input_name = 'Result'
    name = input_name
    len_name = len(input_name)
    i = 1
    while True:
        if name+'.xlsx' not in os.listdir():
            new_df.to_excel(f'{name}.xlsx')
            break 
            
        else:
            name = name[:input_name] + str(i)
            i += 1
