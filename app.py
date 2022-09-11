from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import pandas as pd
import time
from pandastable import Table
import tkinter as tk
import re
from tkinter import ttk
from tkmacosx import Button
from PIL import Image, ImageTk

from flask import Flask, render_template, request, flash

# user agent to get through websites that detect scrapers
ua = UserAgent()
user_agent = ua.random

# driver settings
option = webdriver.ChromeOptions()
option.add_argument('headless')
path = Service('/Users/saahibdeepdhaliwal/Downloads/chromedriver')
option.add_argument('user-agent=' + user_agent)
option.add_argument('--disable-blink-features=AutomationControlled')
option.add_experimental_option("excludeSwitches", ['enable-automation']);
driver = webdriver.Chrome(service=path, options=option)


# websites
website1 = 'https://www.amazon.ca'
website2 = 'https://www.ebay.ca'
website3 = 'https://www.bestbuy.ca/en-ca'

# amazon scraper
def amazonSearch(search_item, max_pages):
    # try getting into amazon with a different user_agent if it does not display the search page
    original_button = False
    while not original_button:
        global user_agent
        user_agent = ua.random
        driver.get('https://www.amazon.ca')
        try:
            search_box = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.ID, 'twotabsearchtextbox')))
            original_button = True
        except:
            original_button = False
            
    # enter the search term
    search_box.send_keys(search_item)
    search_btn = driver.find_element(By.ID, 'nav-search-submit-button')
    search_btn.click()
    time.sleep(3)
    page = 1
    page_bar = driver.find_element(By.CLASS_NAME, "s-pagination-strip")
    real_max_pages = page_bar.find_elements(By.CLASS_NAME, "s-pagination-item")[-2].text
    prod_names = []
    prod_prices = []
    prod_ratings = []
    prod_ratings_nums = []
    prod_links = []
    
    # search the required pages
    while page <= max_pages:
        if page == int(real_max_pages):
            break
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        products = soup.select(".s-result-item.s-asin")
        for product in products:
            # get product price
            price_range = product.find('span', class_='a-price-range')
            # do not include prices with ranges
            if price_range is None:
                main_price = product.find_all('span', class_='a-price-whole')
                decimal_price = product.find_all('span', class_='a-price-fraction')
                if main_price != [] and decimal_price != []:
                    price = ''.join([main_price[0].get_text(), decimal_price[0].get_text()])
                    price = re.sub(r'[^.0-9]', '', price)
                    prod_prices.append(price)
                else:
                    continue
            else:
                continue
            # get product name
            name = product.find('span', class_='a-size-base-plus a-color-base a-text-normal')
            prod_names.append(name.get_text())
            
            # get product rating
            web_rating = product.find('div', class_='a-row a-size-small')
            if web_rating is not None:
                rating = web_rating.find('span', class_='a-icon-alt').get_text()
                rating_num = web_rating.find('span', class_='a-size-base s-underline-text').get_text()
            else:
                rating = 'None'
                rating_num = '0'

            prod_ratings.append(rating)
            prod_ratings_nums.append(rating_num)
            
            # get product url
            url = product.find('a', class_='a-link-normal s-underline-text s-underline-link-text s-link-style'
                                           ' a-text-normal').get('href')
            url = "https:/amazon.ca/" + url
            prod_links.append(url)

        # get pagination and go to next page
        pagination = driver.find_element(By.CLASS_NAME, "s-pagination-strip")
        next_page = pagination.find_element(By.XPATH, './/a[contains(@class, "s-pagination-next")]').get_attribute(
            "href")
        page = page + 1
        driver.get(next_page)
        time.sleep(3)
        
    # store the data into a pandas dataframe
    data = {"Name": prod_names, "Price": prod_prices, "Rating": prod_ratings, "Rating Count": prod_ratings_nums,
            "URL": prod_links}
    result = pd.DataFrame(data)

    return result



# ebaySearch
def ebaySearch(search_item, max_pages):
    original_button = False
     # try getting into ebay with a different user_agent if it does not display the search page
    while not original_button:
        global user_agent
        user_agent = ua.random
        driver.get('https://www.ebay.ca')
        try:
            search_box = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.ID, 'gh-ac')))
            original_button = True
        except:
            original_button = False
            
    # enter the search term
    search_box.send_keys(search_item)
    search_btn = driver.find_element(By.ID, 'gh-btn')
    search_btn.click()
    time.sleep(3)
    page = 1
    prod_names = []
    prod_prices = []
    prod_ratings = []
    prod_ratings_nums = []
    prod_links = []
    prod_shipping = []
    # search the pages
    while page <= max_pages:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        result = soup.find('ul', class_='srp-results srp-list clearfix')
        products = result.find_all('li', class_="s-item")
        for product in products:
            # get product price
            price = product.find('span', class_='s-item__price').get_text()
            # do not include items with no price
            if price is not None:
                if 'to' in price:
                    continue
                else:
                    price = re.sub(r'[^.0-9]', '', price)
                    prod_prices.append(price)
            else:
                continue
            
            # get product name
            name = product.find('div', class_='s-item__title').get_text()
            if 'New Listing' in name:
                name = name.replace('New Listing', '')

            prod_names.append(name)

            # get product ratings
            web_rating = product.find('div', class_='s-item__reviews')
            if web_rating is not None:
                rating_box = product.find('div', class_='x-star-rating')
                rating = rating_box.find('span', class_='clipped').get_text()
                rating_num_box = product.find('div', class_='s-item__reviews')
                rating_num = rating_num_box.select_one('.s-item__reviews-count span:first-child').get_text()
                rating_num = re.sub(r'[^0-9]', '', rating_num)
            else:
                rating = 'None'
                rating_num = '0'

            prod_ratings.append(rating)
            prod_ratings_nums.append(rating_num)

            # get product shipping
            shipping = product.find('span', class_='s-item__shipping s-item__logisticsCost')

            if shipping is not None:
                shipping_cost = shipping.get_text()
                shipping_cost = re.sub(r'[^.0-9]', '', shipping_cost)
            else:
                shipping_cost = 0

            if shipping_cost == '':
                shipping_cost = 0

            prod_shipping.append(shipping_cost)
            
            # get product link
            url = product.find('a', class_='s-item__link').get('href')
            prod_links.append(url)

        # find pagination and go to next page
        pagination = driver.find_element(By.CLASS_NAME, "s-pagination")
        next_page = pagination.find_element(By.XPATH, './/a[contains(@class, "pagination__next '
                                                      'icon-link")]').get_attribute("href")
        page = page + 1

        page_bar = driver.find_element(By.CLASS_NAME, "pagination__items")
        if page_bar is None:
            real_max_pages = 2
        else:
            real_max_pages = page_bar.find_elements(By.CLASS_NAME, "pagination__item")[-2].text

        if page == int(real_max_pages) or page > max_pages:
            break
        driver.get(next_page)
        time.sleep(3)
        
   # store the data into a pandas dataframe
    data = {"Name": prod_names, "Price": prod_prices, "Rating": prod_ratings, "Rating Count": prod_ratings_nums,
            "Shipping Cost": prod_shipping, "URL": prod_links}
    result = pd.DataFrame(data)
    return result



# Best Buy Search
def bestBuySearch(search_item, max_pages):
    # change user agent for best buy to work
    global user_agent
    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
    driver.get(website3)
    time.sleep(3)
    search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'textField_XaJoz')))
    search_box.send_keys(search_item)
    search_box.submit()
    time.sleep(3)
    page = 1
    prod_names = []
    prod_prices = []
    prod_ratings = []
    prod_ratings_nums = []
    prod_links = []
    # search required pages
    while page <= max_pages:
        try:
            driver.find_element(By.CLASS_NAME, "loadMore_3AoXT").click()
            page = page + 1
        except Exception as e:
            if check_end_of_page():
                break
    time.sleep(3)
    products = driver.find_elements(By.CLASS_NAME, "x-productListItem")
    for product in products:
        # find "avaliable in-store" and "avaliable online" messages and only get products that are available
        available_message = product.find_elements(By.XPATH, (".//p[@class='availabilityMessageSearchPickup_1h9CR']"))
        shipping_message = product.find_elements(By.XPATH, (".//p[@class='shippingAvailability_2X3xt']"))
        available = []
        if available_message != []:
            available = available_message[0].find_elements(By.XPATH,
                                                           (".//span[@data-automation='store-availability-checkmark']"))
        if shipping_message != [] and available == []:
            available = shipping_message[0].find_elements(By.XPATH,
                                                           (".//span[@data-automation='store-availability-checkmark']"))
            if available != []:
                # get product name
                name = product.find_element(By.CLASS_NAME, "productItemName_3IZ3c").text
                prod_names.append(name)
                
                #get product price
                price = product.find_element(By.XPATH, (".//span[@class='screenReaderOnly_2mubv large_3uSI_']")).text
                price = re.sub(r'[^.0-9]', '', price)
                prod_prices.append(price)
                
                # get url
                try:
                    url = product.find_element(By.CLASS_NAME, "link_3hcyN").get_attribute('href')
                except:
                    url = product.find_element(By.CLASS_NAME, "link_18NOy").get_attribute('href')

                prod_links.append(url)

                # get number of ratings
                rating_num = product.find_element(By.XPATH, (".//span[@data-automation='rating-count']"))
                rating_num = rating_num.text
                rating_num = re.sub(r'[^0-9]', '', rating_num)
                prod_ratings_nums.append(rating_num)
                
                # create custom star rating based on stars elements
                if rating_num != '0':
                    stars = product.find_elements(By.CLASS_NAME, "partialStar_2NEf9")
                    rating = 0
                    for star in stars:
                        star = star.get_attribute('style')
                        star = re.sub(r'[^0-9]', '', star)
                        rating = rating + int(star)
                    rating = str(rating/100)
                else:
                    rating = 'None'
                prod_ratings.append(rating)
        else:
            continue

   # store the data into a pandas dataframe
    data = {"Name": prod_names, "Price": prod_prices, "Rating": prod_ratings, "Rating Count": prod_ratings_nums,
            "URL": prod_links}
    result = pd.DataFrame(data)
    return result

# see if you can keep "showing more" in bestbuy
def check_end_of_page():
    try:
        driver.find_element(By.CLASS_NAME, "endOfList_b04RG")
    except:
        return False
    return True

# ensures that the item name is prevalent in the collected data, if it is not, we create a list of what rows contain the irrelavent results
def remove_irrelevant(drop_rows, data, item):
    for name in data['Name']:
         for word in item.split(' '):
             if word.lower() not in name.lower():
              drop_index = data[data['Name'] == name].index.tolist()
              drop_rows.extend(drop_index)
    #remove repeated items
    drop_rows = list(set(drop_rows))
    return drop_rows
    
#------- FLASK UI ------- #
app = Flask(__name__)
app.secret_key = "secret ecommerce"

@app.route("/")
def index():
    return render_template("index.html", scale = 100)

@app.route ("/search-item", methods=["POST"])
def search():
    item = request.form["item_input"]
    pages = request.form["page_input"]
    page_int = False
    try:
        pages = int(pages)
        if pages > 0:
            page_int = True
    except ValueError:
        page_int = False
    
    if page_int and pages > 0 and len(item) > 3:
            # call all the functions and get all data
            amazon_data = amazonSearch(item, pages)
            ebay_data = ebaySearch(item, pages)
            bestbuy_data = bestBuySearch(item, pages)
         
            amazon_data['Price'] = pd.to_numeric(amazon_data['Price'])
            ebay_data['Price'] = pd.to_numeric(ebay_data['Price'])
            bestbuy_data['Price'] = pd.to_numeric(bestbuy_data['Price'])

            amazon_data['Rating Count'] = amazon_data['Rating Count'].str.replace(',', '')
            for amazon_rating in amazon_data['Rating Count']:
                try:
                    float(amazon_rating)
                except ValueError:
                    index = amazon_data[amazon_data['Rating Count'] == amazon_rating].index
                    amazon_data.iloc[index, 3] = 0

            amazon_data['Rating Count'] = pd.to_numeric(amazon_data['Rating Count'])

            ebay_data['Rating Count'] = ebay_data['Rating Count'].str.replace(',', '')
            for ebay_rating_num in ebay_data['Rating Count']:
                try:
                    float(ebay_rating_num)
                except ValueError:
                    index = ebay_data[ebay_data['Rating Count'] == ebay_rating_num].index
                    ebay_data.iloc[index, 3] = 0

            ebay_data['Rating Count'] = pd.to_numeric(ebay_data['Rating Count'])
            bestbuy_data['Rating Count'] = pd.to_numeric(bestbuy_data['Rating Count'])
            amazon_data['Rating'] = amazon_data['Rating'].str.replace('out of 5 stars', '')
            ebay_data['Rating'] = ebay_data['Rating'].str.replace('out of 5 stars.', '')
            
            
            amazonRowsDrop = []
            ebayRowsDrop = []
            bestbuyRowsDrop = []
            
            # filter data
            amazonRowsDrop = remove_irrelevant (amazonRowsDrop, amazon_data, item)
            ebayRowsDrop = remove_irrelevant(ebayRowsDrop, ebay_data, item)
            bestbuyRowsDrop = remove_irrelevant(bestbuyRowsDrop, bestbuy_data, item)

            # Sort by rating count
            amazon_data = amazon_data.drop(amazonRowsDrop)
            amazon_data = amazon_data.sort_values(['Rating Count'], ascending=False)
            ebay_data = ebay_data.drop(ebayRowsDrop)
            ebay_data = ebay_data.sort_values(['Rating Count'], ascending=False)
            bestbuy_data = bestbuy_data.drop(bestbuyRowsDrop)
            bestbuy_data = bestbuy_data.sort_values(['Rating Count'], ascending=False)
            
            #If all the ratings do not exist, we sort by the price
            if (amazon_data['Rating'] == 0).all() == True:
                amazon_data = amazon_data.sort_values(['Price'], ascending = False)
            if (ebay_data['Rating'] == 0).all() == True:
                ebay_data = ebay_data.sort_values(['Price'], ascending = False)
            if (bestbuy_data['Rating'] == 0).all() == True:
                bestbuy_data = bestbuy_data.sort_values(['Price'], ascending = False)
                
            # format all prices/costs
            amazon_data['Price'] = amazon_data['Price'].map('${:,.2f}'.format)
            ebay_data['Price'] = ebay_data['Price'].map('${:,.2f}'.format)
            ebay_data['Shipping Cost'] = pd.to_numeric(ebay_data['Shipping Cost'])

            ebay_data['Shipping Cost'] = ebay_data['Shipping Cost'].map('${:,.2f}'.format)
            bestbuy_data['Price'] = bestbuy_data['Price'].map('${:,.2f}'.format)

            amazon_data = amazon_data.head(10)
            ebay_data = ebay_data.head(10)
            bestbuy_data = bestbuy_data.head(10)
            
            return render_template("index.html", item = item, amazon_column_names=amazon_data.columns.values, amazon_row_data=list(amazon_data.values.tolist()),
                                ebay_column_names=ebay_data.columns.values, ebay_row_data=list(ebay_data.values.tolist()),
                                bestbuy_column_names=bestbuy_data.columns.values, bestbuy_row_data=list(bestbuy_data.values.tolist()),
                                zip=zip, link_column = "URL",enumerate = enumerate, scale = 70)
    else:
        if page_int:
            error_message = "Enter a longer search term"
        elif len(item) > 3:
            error_message = "Enter a positive whole number for pages"
        else: 
            error_message = "Enter a positive whole number for pages and a longer search term"
            
        return render_template("index.html", error_message = error_message, enumerate = enumerate, scale = 100) 
      

if __name__ == "__main__":
    app.run(debug=True)
    
# ------------------- IF USING TKINTER GUI----------------- #     
# The code below is to use the TKinter GUI instead of flask #

# def main(item, pages):
#     amazon_data = amazonSearch(item, pages)
#     ebay_data = ebaySearch(item, pages)
#     bestbuy_data = bestBuySearch(item, pages)
#     pd.set_option('display.max_columns', None)

#     amazon_data['Price'] = pd.to_numeric(amazon_data['Price'])
#     ebay_data['Price'] = pd.to_numeric(ebay_data['Price'])
#     bestbuy_data['Price'] = pd.to_numeric(bestbuy_data['Price'])

#     amazon_data['Rating Count'] = amazon_data['Rating Count'].str.replace(',', '')
#     for amazon_rating in amazon_data['Rating Count']:
#         try:
#             float(amazon_rating)
#         except ValueError:
#             index = amazon_data[amazon_data['Rating Count'] == amazon_rating].index
#             amazon_data.iloc[index, 3] = 0

#     amazon_data['Rating Count'] = pd.to_numeric(amazon_data['Rating Count'])

#     ebay_data['Rating Count'] = ebay_data['Rating Count'].str.replace(',', '')
#     for ebay_rating_num in ebay_data['Rating Count']:
#         try:
#             float(ebay_rating_num)
#         except ValueError:
#             index = ebay_data[ebay_data['Rating Count'] == ebay_rating_num].index
#             ebay_data.iloc[index, 3] = 0

#     ebay_data['Rating Count'] = pd.to_numeric(ebay_data['Rating Count'])
#     bestbuy_data['Rating Count'] = pd.to_numeric(bestbuy_data['Rating Count'])
#     amazon_data['Rating'] = amazon_data['Rating'].str.replace('out of 5 stars', '')
#     ebay_data['Rating'] = ebay_data['Rating'].str.replace('out of 5 stars.', '')

#     amazonRowsDrop = []
#     ebayRowsDrop = []
#     bestbuyRowsDrop = []

#     amazonRowsDrop = remove_irrelevant (amazonRowsDrop, amazon_data, item)
#     ebayRowsDrop = remove_irrelevant(ebayRowsDrop, ebay_data, item)
#     bestbuyRowsDrop = remove_irrelevant(bestbuyRowsDrop, bestbuy_data, item)

#     # Sort by price
#     amazon_data = amazon_data.drop(amazonRowsDrop)
#     amazon_data = amazon_data.sort_values(['Rating Count'], ascending=False)
#     ebay_data = ebay_data.drop(ebayRowsDrop)
#     ebay_data = ebay_data.sort_values(['Rating Count'], ascending=False)
#     bestbuy_data = bestbuy_data.drop(bestbuyRowsDrop)
#     bestbuy_data = bestbuy_data.sort_values(['Rating Count'], ascending=False)
    
#       #If there is a case where all the ratings do not exist, we sort by the price
#     if (amazon_data['Rating'] == 0).all() == True:
#         amazon_data = amazon_data.sort_values(['Price'], ascending = False)
#     if (ebay_data['Rating'] == 0).all() == True:
#         ebay_data = ebay_data.sort_values(['Price'], ascending = False)
#     if (bestbuy_data['Rating'] == 0).all() == True:
#         bestbuy_data = bestbuy_data.sort_values(['Price'], ascending = False)

#     amazon_data['Price'] = amazon_data['Price'].map('${:,.2f}'.format)
#     ebay_data['Price'] = ebay_data['Price'].map('${:,.2f}'.format)
#     ebay_data['Shipping Cost'] = pd.to_numeric(ebay_data['Shipping Cost'])

#     ebay_data['Shipping Cost'] = ebay_data['Shipping Cost'].map('${:,.2f}'.format)
#     bestbuy_data['Price'] = bestbuy_data['Price'].map('${:,.2f}'.format)

#     amazon_data = amazon_data.head(10)
#     ebay_data = ebay_data.head(10)
#     bestbuy_data = bestbuy_data.head(10)

#     table1 = Table(lower_frame1, dataframe=amazon_data)
#     table1.show()

#     table2 = Table(lower_frame2, dataframe=ebay_data)
#     table2.show()

#     table3 = Table(lower_frame3, dataframe=bestbuy_data)
#     table3.show()
#     driver.quit()

# HEIGHT = 800
# WIDTH = 1300
# root = tk.Tk()

# canvas = tk.Canvas(root, height=HEIGHT, width=WIDTH)
# canvas.pack()

# background_colour = '#061C80'
# frame = tk.Frame(root, bg=background_colour)
# frame.place(relx=0.5, rely=0.05, relwidth=0.75, relheight=0.2, anchor='n')


# label1 = tk.Label(frame, text="Enter Item:", bg=background_colour, fg="white")
# label1.place(relx=0, rely=0.25, relwidth=0.2, relheight=0.25, anchor='w')

# label2 = tk.Label(frame, text="Enter Pages:", bg=background_colour, fg="white")
# label2.place(relx=0, rely=0.75, relwidth=0.2, relheight=0.25, anchor='w')

# entry1 = tk.Entry(frame, bg='black')
# entry1.place(relx=0.2, rely=0.25, relwidth=0.5, relheight=0.25, anchor='w')

# entry2 = tk.Entry(frame, bg='black')
# entry2.place(relx=0.2, rely=0.75, relwidth=0.5, relheight=0.25, anchor='w')

# button = tk.Button(frame, text='Search', highlightbackground=background_colour, command = lambda: main(entry1.get(), int(entry2.get())))
# button.place(relx=0.75, rely=0.5, relwidth=0.2, relheight=0.5, anchor='w')

# lower_frame = tk.Frame(root, bg=background_colour, bd=5)
# lower_frame.place(relx=0.5, rely=0.3, relwidth=0.75, relheight=0.65, anchor='n')

# lower_frame1 = tk.Frame(lower_frame, bg='#36384c', width=150, height=200)
# lower_frame1.place(relx=0.50, rely=0.03, relwidth=1.0, relheight=0.30, anchor='n')

# lower_frame2 = tk.Frame(lower_frame, bg='#36384c', width=150, height=200)
# lower_frame2.place(relx=0.50, rely=0.36, relwidth=1.0, relheight=0.30, anchor='n')

# lower_frame3 = tk.Frame(lower_frame, bg='#36384c', width=150, height=200)
# lower_frame3.place(relx=0.50, rely=0.69, relwidth=1.0, relheight=0.30, anchor='n')

# root.mainloop()
