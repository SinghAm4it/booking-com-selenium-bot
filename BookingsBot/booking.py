from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException
)
from webdriver_manager.chrome import ChromeDriverManager
import time
from typing import Literal
from datetime import datetime
from prettytable import PrettyTable
import BookingsBot.constants as const

class Booking(webdriver.Chrome):
    """
    Booking class inherits from webdriver.Chrome.
    Handles stale elements, missing elements, explicit waits, and retries automatically.
    
    """

    # -------------- CONSTRUCTOR --------------
    def __init__(self, driver_path=None, teardown=False, implicit_wait:int=15):
        if driver_path is None:
            driver_path = ChromeDriverManager().install()
        self.driver_path = driver_path
        self.teardown = teardown

        options = Options()

        options.add_experimental_option("excludeSwitches", ["enable-logging"])

        options.add_argument("--ignore-certificate-errors")

        if not teardown:
            options.add_experimental_option("detach", True)  # keep browser open

        service = Service(self.driver_path)
        super().__init__(service=service, options=options)

        # Implicit wait for element presence
        self.implicitly_wait(implicit_wait)

        # Maximize browser window
        self.maximize_window()



    # ---------- CONTEXT MANAGER ENTER ----------
    def __enter__(self):
        return self



    # ---------- CONTEXT MANAGER EXIT ----------   
    def __exit__(self, exc_type, exc, traceback):
        if self.teardown:
            self.quit()



    # ---------- UNIVERSAL SAFE CLICK ----------
    def safe_click(self, locator, retries=3, wait_time=5):
        """
        Clicks an element safely with retries and explicit wait.
        locator: tuple(By.<METHOD>, "selector")
        """
        for attempt in range(retries):
            try:
                element = WebDriverWait(self, wait_time).until(
                    EC.element_to_be_clickable(locator)
                )
                element.click()
                return True
            except StaleElementReferenceException:
                time.sleep(0.5)
            except TimeoutException:
                if attempt == retries - 1:
                    print(f"Element not found: {const.RED}{const.BOLD}{locator}{const.RESET}")
                    raise



    # ---------- UNIVERSAL SAFE SEND KEYS ----------
    def safe_send_keys(self, locator, text, retries=3, wait_time=5):
        """
        Sends text to an input element safely with retries and explicit wait.
        """
        for attempt in range(retries):
            try:
                element = WebDriverWait(self, wait_time).until(
                    EC.presence_of_element_located(locator)
                )
                element.clear()
                element.send_keys(text)
                return True
            except StaleElementReferenceException:
                time.sleep(0.5)
            except TimeoutException:
                if attempt == retries - 1:
                    print(f"Input element not found: {const.RED}{const.BOLD}{locator}{const.RESET}")
                    raise



    # ---------- PAGE METHODS ----------
    def land_first_page(self):
        """
        Navigates the browser to the base URL (Booking.com home page).
        """
        self.get(const.BASE_URL)
        try:
            sign_in_info = WebDriverWait(self, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 
                                        "button[aria-label='Dismiss sign-in info.']")))
            sign_in_info.click()
        except:
            pass


    # ---------- FETCH ALL CURRENCIES ----------
    def fetch_all_currencies(self,update=False):
        """
        Opens the currency picker and scrapes all available currencies.

        Args:
            update (bool): If True, overwrite the hardcoded currency list in const.CURRENCIES.

        Returns:
            set: A set of all available currencies as strings.
        """
         # Local locator
        currency_button_locator = (By.CSS_SELECTOR, 'button[data-testid="header-currency-picker-trigger"]')
        self.safe_click(currency_button_locator)

    
        select_currency = WebDriverWait(self, 10).until(
                          EC.presence_of_all_elements_located(    
                          (By.CSS_SELECTOR, "div.CurrencyPicker_currency")
                          ))

        scraped = {currency.text for currency in select_currency}

        if update:
            const.CURRENCIES = scraped   # overwrite the hardcoded list

        return scraped



    # ---------- CHANGE CURRENCY ----------
    def change_currency(self,currency : str = "INR"):
        """
        Changes the site's currency to the given value.

        Args:
            currency (str): Desired currency (e.g., "INR", "USD", "EUR").

        Raises:
            ValueError: If the given currency is not supported.
        """
        # Local locator
        currency_button_locator = (By.CSS_SELECTOR, 'button[data-testid="header-currency-picker-trigger"]')
        self.safe_click(currency_button_locator)

        currency_selector = (By.XPATH,
        f"//div[contains(@class, 'CurrencyPicker_currency') and normalize-space(text())='{currency}']"
        )
        self.safe_click(currency_selector)

        if currency not in const.CURRENCIES:
            raise ValueError(f"Currency {const.RED}{const.BOLD}'{currency}'{const.RESET} is not supported.\n"
                             f" Choose from {const.RED}{const.BOLD}'{const.CURRENCIES}'{const.RESET}")
        


    # ---------- SEARCH LOCATION ----------
    def search_location(self,location : str = None):
        """
        Searches for a given location in the destination input box.

        Args:
            location (str): The name of the location (e.g., "New York", "Paris").

        Notes:
            Automatically selects the first autocomplete suggestion.
        """
        location_input_locator = (By.CSS_SELECTOR,"input[name='ss']")
        self.safe_send_keys(location_input_locator,location)
        time.sleep(2.5)
        first_suggestion = (By.CSS_SELECTOR,"li[id='autocomplete-result-0']")
        self.safe_click(first_suggestion)



    # ---------- SELECT DATES ----------
    def select_dates(self,
                     mode: Literal["calendar","flexible"]="calendar",
                     checkin_date : str = None,
                     checkout_date : str = None,
                     flexibility : str = None,
                     stay_duration : str = None,
                     stay_duration_days : int = None,
                     day_number : int = None,
                     time_of_stay : list[str] = None
                     ):
        """
        Selects booking dates either using the calendar (exact dates) 
        or the flexible date option on Booking.com.

        Modes:
        - "calendar":
            Requires `checkin_date` and `checkout_date` in "yyyy-mm-dd" format.
            Optional: `flexibility` (e.g., "Exact dates", "+/- 1 day").
            Disallows stay_duration-related parameters.
        - "flexible":
            Requires `stay_duration` (e.g., "Weekend", "Week", "Month", "Other")
            and `time_of_stay` (list of months in "MonthName YYYY" format).
            If `stay_duration` = "Other", then `stay_duration_days` (1–90 nights) 
            and `day_number` (1–7, day of week) are required.

        Args:
            mode (Literal): Mode of date selection ("calendar" or "flexible").
            checkin_date (str): Check-in date, format "yyyy-mm-dd" (calendar mode only).
            checkout_date (str): Check-out date, format "yyyy-mm-dd" (calendar mode only).
            flexibility (str): Flexible date option (calendar mode only).
            stay_duration (str): Duration of stay type (flexible mode only).
            stay_duration_days (int): Nights to stay if stay_duration="Other".
            day_number (int): Starting weekday number if stay_duration="Other" (1=Monday).
            time_of_stay (list[str]): Months user is willing to stay, format: ["March 2025", "April 2025"].

        Raises:
            ValueError: If required arguments are missing or in the wrong format.
        
        """

        if mode == "calendar":
            if not checkin_date or not checkout_date:
                raise ValueError(f"{const.RED}{const.BOLD}Both checkin_date and checkout_date must be provided in 'calendar' mode.{const.RESET}")
            
            if not flexibility:
                flexibility  = "Exact dates"

            if stay_duration or stay_duration_days or day_number or time_of_stay:
                raise ValueError(f"{const.RED}{const.BOLD}Stay Duration parameter is only valid in flexible mode.{const.RESET}")

            # Validate date format
            try:
                checkin_dt = datetime.strptime(checkin_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"checkin_date {const.RED}{const.BOLD}'{checkin_date}'{const.RESET} is not in the required format {const.RED}{const.BOLD}'yyyy-mm-dd'{const.RESET}")

            try:
                checkout_dt = datetime.strptime(checkout_date, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"checkout_date {const.RED}{const.BOLD}'{checkout_date}'{const.RESET} is not in the required format {const.RED}{const.BOLD}'yyyy-mm-dd'{const.RESET}")

            if checkin_dt >= checkout_dt:
                raise ValueError(f"{const.RED}{const.BOLD}Checkout Date must be after Checkin Date.{const.RESET}")
            
            checkin_locator = (By.CSS_SELECTOR,f"span[data-date='{checkin_date}']")
            checkout_locator = (By.CSS_SELECTOR,f"span[data-date='{checkout_date}']")
            next_button_locator = (By.CSS_SELECTOR,"button[aria-label='Next month']")

            while True:
                try:
                    self.safe_click(checkin_locator)
                    break
                except :
                    try:
                        self.safe_click(next_button_locator)
                    except:
                        raise ValueError(f"{const.RED}{const.BOLD}Checkin Date is out of range.{const.RESET}")
                    
            while True:
                try:
                    self.safe_click(checkout_locator)
                    break
                except :
                    try:
                        self.safe_click(next_button_locator)
                    except:
                        raise ValueError(f"{const.RED}{const.BOLD}Checkout Date is out of range.{const.RESET}")
            
            if flexibility != "Exact dates":
                try:   
                    span_locator = (By.XPATH,f"//span[normalize-space(text())='{flexibility}']")
                    self.safe_click(span_locator)
                except:
                    raise ValueError(f"flexibility must be one of {const.RED}{const.BOLD}{const.DATE_FLEXIBILITY}{const.RESET}")


        elif mode == "flexible":

            if not stay_duration:
                raise ValueError (f"{const.RED}{const.BOLD}Stay duration argument is missing.{const.RESET}")
            
            if not time_of_stay:
                raise ValueError (f"{const.RED}{const.BOLD}Time of Stay argument is missing.{const.RESET}")

            if checkin_date or checkout_date or flexibility:
                raise ValueError(f"{const.RED}{const.BOLD}checkin_date, checkout_date and flexibility are only valid in calendar mode, not in flexible mode.{const.RESET}")
            
            flexible_button_locator = (By.CSS_SELECTOR,"button[id='flexible-searchboxdatepicker-tab-trigger']")
            self.safe_click(flexible_button_locator)

            try:
                stay_duration_locator = (By.XPATH,f"//div[text()='{stay_duration}']")
                self.safe_click(stay_duration_locator)
                time.sleep(1)
            except:
                raise ValueError(f"Stay Duration must be from : {const.RED}{const.BOLD}{const.STAY_DURATION}{const.RESET}")

            if stay_duration == "Other":

                if not stay_duration_days or stay_duration_days < 1 or stay_duration_days > 90:
                    raise ValueError(f"{const.RED}{const.BOLD}Stay Duration days{const.RESET} is required for {const.RED}{const.BOLD}'Other'{const.RESET} option.\n" ,
                                     f"Stay duration days must be between {const.RED}{const.BOLD} 1 to 90 {const.RESET} ")

                if not day_number or day_number < 1 or day_number > 7:
                    raise ValueError(f"{const.RED}{const.BOLD}Day Number{const.RESET} is required for {const.RED}{const.BOLD}'Other'{const.RESET} option.\n" ,
                                     f"Day Number must be between {const.RED}{const.BOLD} 1 to 7 {const.RESET} ")

                input_locator = (By.CSS_SELECTOR,"input[aria-label='Number of nights']")
                self.safe_click(input_locator)
                input_box = WebDriverWait(self, 10).until(
                            EC.visibility_of_element_located(input_locator)
                            )
                input_box.send_keys(Keys.DELETE)      
                input_box.send_keys(str(stay_duration_days))  
                
                time.sleep(2)
                select_locator = (By.CSS_SELECTOR,"select[aria-label='Check-in day']")
                self.safe_click(select_locator)

                options_locator = (By.CSS_SELECTOR,f"option[data-key='{day_number}']")
                self.safe_click(options_locator)

            else:

                if stay_duration_days or day_number:
                    raise ValueError(f"{const.RED}{const.BOLD}stay_duration_days and day_number arguments are only valid for stay_duration = 'Other'{const.RESET}")

            calendar_container = self.find_element(By.CSS_SELECTOR,"div[data-testid='flexible-dates-months']")
            
            staytime = [tuple(i.split(" ")) for i in time_of_stay]

            for t in staytime:
                target_month,target_year = t
                while True:

                    try:
                        li = WebDriverWait(calendar_container,5).until(
                            EC.visibility_of_element_located((By.XPATH,f".//div[contains(@role,'group') and "
                                                                f".//span[contains(normalize-space(text()),'{target_month}')] and "
                                                                f".//span[contains(normalize-space(text()),'{target_year}')]]")
                        ))
                        li.click()
                        break
                    
                    except:
                        next_button = (By.CSS_SELECTOR,"button[aria-label='Next']")
                        self.safe_click(next_button)
            select_button_locator = (By.XPATH,"//button//span[normalize-space(text())='Select dates']") 
            self.safe_click(select_button_locator)
        else:
            raise ValueError (f"Mode should be selected from: {const.RED}{const.BOLD}{'calendar', 'flexible'}{const.RESET}")



    # ---------- SELECT CUSTOMERS ----------
    def select_guests(self,adults: int, children: int,
                           rooms: int, pets=False,
                           children_ages_list : list[int] = None):

        """
        Configures the number of guests in the Booking.com occupancy popup.

        Args:
            adults (int): Number of adults.
            children (int): Number of children.
            rooms (int): Number of rooms.
            pets (bool, optional): Whether traveling with pets. Defaults to False.
            children_ages_list (list[int], optional): Required if children > 0.
                A list of ages (0–17) for each child.

        Raises:
            ValueError:
                - If children > 0 and ages list is missing or mismatched.
                - If children ages are not between 0–17.
        
        """
        customer_locator = (By.CSS_SELECTOR,"button[data-testid='occupancy-config']")
        self.safe_click(customer_locator)

        groups = {"Adults":adults,"Children":children,"Rooms":rooms}

        for group_name,target_value in groups.items():

            container_locator : WebElement = WebDriverWait(self,10).until(
                                EC.presence_of_element_located
                                ((By.XPATH,f"//label[text()='{group_name}']/parent::div/following-sibling::div")))

            span_value = container_locator.find_element(By.XPATH,".//span[normalize-space()]")

            current_value = int(span_value.text)
            
            for attempt in range(3):
                try:
                    decrement = container_locator.find_element(By.XPATH, ".//button[1]")
                    increment = container_locator.find_element(By.XPATH, ".//button[last()]")
                    break
                except:
                    print(f"{const.RED}{const.BOLD}Increment/Decrement not found {const.RESET}")

            while current_value < target_value:
                for attempt in range(3):
                    try:
                        increment.click()
                        current_value += 1
                        time.sleep(0.4)
                        break
                    except:
                        print(f"Element not found: {const.RED}{const.BOLD}'.//button[last()]'{const.RESET}")
                time.sleep(0.4)

            while current_value > target_value:
                for attempt in range(3):
                    try:
                        decrement.click()
                        current_value -=1
                        time.sleep(0.4)
                        break
                    except:
                        print(f"Element not found: {const.RED}{const.BOLD}'.//button[1]'{const.RESET}")
                time.sleep(0.4)


        if children > 0:
            
            if not children_ages_list or len(children_ages_list) != children:
                raise ValueError(f"You must provide {const.RED}{const.BOLD}{children}{const.RESET} ages for children ages list.")


            child_age_selects = WebDriverWait(self, 10).until(
            EC.presence_of_all_elements_located((
                By.XPATH, "//div[contains(@data-testid,'kids-ages-select')]//select[contains(@name,'age')]"
            )))

            for i , element in enumerate(child_age_selects):
                age = children_ages_list[i]
                if age > 17 or age < 0:
                    raise ValueError (f"{const.RED}{const.BOLD}Children ages must be between 0 and 17{const.RESET}")
                element.click()
                option = element.find_element(By.CSS_SELECTOR, f"option[data-key='{age}']")
                option.click()

        pet_checkbox_locator = (By.CSS_SELECTOR,"label[for='pets']")

        if pets:
            self.safe_click(pet_checkbox_locator)

        done_locator = (By.XPATH,"//span[text()='Done']/parent::button")
        self.safe_click(done_locator)



    # ---------- SEARCH ----------
    def search_results(self):
        """
        Triggers the search action on Booking.com after all inputs 
        (destination, dates, guests, etc.) have been configured.

        This clicks the main "Search" button on the homepage.

        Raises:
            Exception: If the search button is not found or not clickable.
        
        """
        search_box_locator = (By.CSS_SELECTOR,"button[type='submit']")
        self.safe_click(search_box_locator)



    # ---------- SET RANGE OF PRICE ----------
    def set_price_slider(self, min_value: int, max_value: int, timeout: int = 10):
        """
        Set Booking.com price slider by dragging handles with ActionChains.
        Handles dynamic changes after moving min handle.
        """
        if min_value >= max_value:
            raise ValueError(f"{const.RED}{const.BOLD}min_value must be < max_value.{const.RESET}")

        wait = WebDriverWait(self, timeout)
        actions = ActionChains(self)

        # --- Helper: Fetch container, inputs, handles, track ---
        def get_slider_elements():
            container = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="filters-group-slider"]'))
            )
            min_input = container.find_element(By.CSS_SELECTOR, 'input[aria-label="Min."]')
            max_input = container.find_element(By.CSS_SELECTOR, 'input[aria-label="Max."]')

            slider_min = int(min_input.get_attribute("min") or 0)
            slider_max = int(max_input.get_attribute("max") or 0)
            step = int(min_input.get_attribute("step") or 1)

            handles = container.find_elements(By.CSS_SELECTOR, '.fc835e65e6')
            if len(handles) < 2:
                raise RuntimeError(f"{const.RED}{const.BOLD}Could not locate slider handles.{const.RESET}")
            min_handle, max_handle = handles[0], handles[1]

            track = container.find_element(By.CSS_SELECTOR, '.e7e72a1761')
            track_width = track.size["width"]

            return container, slider_min, slider_max, step, min_handle, max_handle, track_width

        # --- Helper: Snap value to step ---
        def snap(v, slider_min, slider_max, step):
            v = max(slider_min, min(slider_max, int(v)))
            remainder = (v - slider_min) % step
            if remainder != 0:
                if remainder >= step / 2:
                    v += (step - remainder)
                else:
                    v -= remainder
            return v

        # --- Initial fetch ---
        container, slider_min, slider_max, step, min_handle, max_handle, track_width = get_slider_elements()

        # Snap target values
        target_min = snap(min_value, slider_min, slider_max, step)
        target_max = snap(max_value, slider_min, slider_max, step)
        if target_min >= target_max:
            target_max = min(slider_max, target_min + step)

        # --- Move MIN handle ---
        min_percent = (target_min - slider_min) / (slider_max - slider_min)
        # actions.click_and_hold(min_handle).move_by_offset(-track_width, 0).release().perform()
        time.sleep(0.3)
        actions.click_and_hold(min_handle).move_by_offset(int(track_width * min_percent), 0).release().perform()
        time.sleep(2.5)  # allow DOM to update

        # --- Re-fetch max handle and track after DOM update ---
        container, slider_min, slider_max, step, min_handle, max_handle, track_width = get_slider_elements()

        # Snap target_max again in case slider_max changed
        target_max = snap(max_value, slider_min, slider_max, step)
        if target_max <= target_min:
            target_max = min(slider_max, target_min + step)

        # --- Move MAX handle ---
        max_percent = (target_max - slider_min) / (slider_max - slider_min)
        # actions.click_and_hold(max_handle).move_by_offset(track_width, 0).release().perform()
        time.sleep(0.3)
        actions.click_and_hold(max_handle).move_by_offset(int(track_width * (max_percent - 1)), 0).release().perform()
        time.sleep(2.5)



    # ---------- APPLY FILTERS ----------
    def apply_filters(self,filters:list[str] = None):

        if not filters:
            return

        for filter in filters:
            if filter not in const.FILTERS:
                raise ValueError(f"{const.RED}{const.BOLD}{filter}{const.RESET} is not supported."
                                 f"Please choose from : {const.RED}{const.BOLD}{const.FILTERS}{const.RESET}")

        filter_containers = WebDriverWait(self,5).until(
            EC.presence_of_all_elements_located((
                By.XPATH,"//div[@data-testid='filters-group']")))
        
        applied = set()

        for filter_container in filter_containers:

            for attempt in range(2):
                try :
                    expand_collapse_buttons =filter_container.find_elements(
                        By.XPATH,".//button[@data-testid='filters-group-expand-collapse']")
                    
                    if expand_collapse_buttons:
                        
                        expand_collapse_buttons[0].click()

                    labels = filter_container.find_elements(
                                By.XPATH,".//div[@data-testid='filters-group-label-container']"
                                "//div[@data-testid='filters-group-label-content']")

                    for label in labels:
                        if label.text in filters and label.text not in applied:
                            label.click()
                            applied.add(label.text)
                            time.sleep(3)
                            break
                except StaleElementReferenceException:
                    time.sleep(0.3)
                except TimeoutException:
                    raise

            if len(applied) == len(filters):
                break



    # ---------- SORT ----------
    def sort_according(self,sort:str = None):
        sort_button = (By.CSS_SELECTOR,"button[data-testid='sorters-dropdown-trigger']")
        self.safe_click(sort_button)

        sort_option = (By.XPATH,f"//div[@data-testid='sorters-dropdown']//li//span[normalize-space(text())='{sort}']")

        self.safe_click(sort_option)

        if sort not in const.SORT_LIST:
            raise ValueError(f"Results can be sorted only according to {const.RED}{const.BOLD}{const.SORT_LIST}{const.RESET}")
        


    # ---------- EXTRACT RESULTS ----------
    def extract_results(self):
        """
        Extracts hotel names, review scores, prices and tax information from the search results page.

        Returns:
            list of dict: A list where each dict contains 'name', 'review_score', 'price' and 'tax_info' of a hotel.
        """
        results = []

        hotel_cards = WebDriverWait(self, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-testid="property-card"]'))
        )

        for card in hotel_cards:
            try:
                try:
                    name = card.find_element(By.CSS_SELECTOR, 'div[data-testid="title"]').text.strip()
                except:
                    name = "N/A"
                try:
                    review_score = card.find_element(By.XPATH, './/div[@data-testid="review-score"]/div[@aria-hidden="true"]').text.strip()
                except:
                    review_score = "N/A"
                try:
                    price = card.find_element(By.CSS_SELECTOR, 'span[data-testid="price-and-discounted-price"]').text.strip()
                except:
                    price = "N/A"
                try:
                    tax_info = card.find_element(By.CSS_SELECTOR, 'div[data-testid="taxes-and-charges"]').text.strip()
                except:
                    tax_info = "N/A"
                    
                hotel_info = [
                    name,
                    review_score,
                    price,
                    tax_info
                ]
                results.append(hotel_info)
            except Exception as e:
                print(f"Error extracting data from a card: {e}")
                continue
            
            table = PrettyTable(field_names=['Hotel Name','Review Score','Price','Taxes'])
            table.add_rows(results)

        return table