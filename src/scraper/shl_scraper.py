import json
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_URL = "https://www.shl.com/solutions/products/product-catalog/"

options = uc.ChromeOptions()

options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")

driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 10)

def accept_cookies():
    try:
        btn = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        btn.click()
        print("🍪 Cookie banner accepted.")
    except:
        print("⚠️ No cookie banner or already accepted.")

def extract_product_info(product_url, index):
    try:
        driver.get(product_url)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        time.sleep(2)
    except:
        print(f"⚠️ [{index}] Failed to load product page: {product_url}")
        return None

    data = {
        "url": product_url,
        "title": "",
        "description": "",
        "job_level": "",
        "languages": "",
        "completion_time": "",
        "test_types": [],
        "remote_testing": "no",
        "pdf_links": []
    }

    try:
        data["title"] = driver.find_element(By.TAG_NAME, "h1").text.strip()
        print(f"📝 [{index}] {data['title']}")
    except:
        print(f"⚠️ [{index}] Failed to extract title")

    def extract_xpath_text(xpath):
        try:
            return driver.find_element(By.XPATH, xpath).text.strip()
        except:
            return ""

    data["description"] = extract_xpath_text("//h4[text()='Description']/following-sibling::p")
    data["job_level"] = extract_xpath_text("//h4[text()='Job levels']/following-sibling::p")
    data["languages"] = extract_xpath_text("//h4[text()='Languages']/following-sibling::p")
    try:
        time_text = extract_xpath_text("//h4[text()='Assessment length']/following-sibling::p")
        data["completion_time"] = time_text.split('=')[-1].strip()
    except:
        pass

    try:
        test_type_parent = driver.find_element(By.XPATH, "//p[contains(., 'Test Type')]")
        type_spans = test_type_parent.find_elements(By.XPATH, ".//span[@class='product-catalogue__key']")
        data["test_types"] = [span.text.strip() for span in type_spans if span.text.strip()]
    except:
        pass

    try:
        remote_el = driver.find_element(By.XPATH, "//p[contains(text(), 'Remote Testing')]/span")
        if "yes" in remote_el.get_attribute("class"):
            data["remote_testing"] = "yes"
    except:
        pass

    try:
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            text = link.text.strip()
            if href and href.endswith(".pdf"):
                data["pdf_links"].append({"name": text, "url": href})
    except:
        pass

    return data

def scrape_table(table_index):
    all_links = set()
    page = 1
    
    while True:
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.custom__table-wrapper")))
            time.sleep(2)
            
            tables = driver.find_elements(By.CSS_SELECTOR, "div.custom__table-wrapper")
            if len(tables) <= table_index:
                print(f"⚠️ Table {table_index + 1} not found on page {page}")
                break
                
            current_table = tables[table_index]
            try:
                links = current_table.find_elements(By.CSS_SELECTOR, "table tbody tr a")
                print(f"📄 Table {table_index + 1}, Page {page}: Found {len(links)} links")
                
                if not links:
                    break
                    
                for link in links:
                    href = link.get_attribute("href")
                    if href:
                        all_links.add(href)
            except:
                print(f"⚠️ Failed to find links in table {table_index + 1}")
                break
            
            try:
                pagination = current_table.find_element(By.CSS_SELECTOR, "ul.pagination")
                next_button = pagination.find_element(By.CSS_SELECTOR, "li.pagination__item.-arrow.-next a.pagination__arrow")
                
                if "disabled" in next_button.get_attribute("class"):
                    print("✅ Reached last page of table")
                    break
                    
                next_button.click()
                page += 1
                time.sleep(3)
            except Exception as e:
                print(f"⛔ No pagination found or error for table {table_index + 1}: {str(e)}")
                break
                
        except Exception as e:
            print(f"⚠️ Error processing table {table_index + 1}: {str(e)}")
            break
            
    return list(all_links)

def get_all_product_links():
    driver.get(BASE_URL)
    accept_cookies()
    time.sleep(3)
    
    all_links = []
    for table_index in range(2):
        print(f"\n🔍 Starting to scrape table {table_index + 1}")
        table_links = scrape_table(table_index)
        all_links.extend(table_links)
        print(f"✅ Finished table {table_index + 1}, found {len(table_links)} links")
    
    return all_links

def main():
    print("🚀 Starting SHL scraper...\n")
    try:
        product_links = get_all_product_links()
        print(f"\n🔗 Total product URLs collected: {len(product_links)}\n")

        all_product_data = []
        success_count = 0
        MAX_RETRIES = 3

        for i, url in enumerate(product_links, start=1):
            for attempt in range(MAX_RETRIES):
                try:
                    data = extract_product_info(url, i)
                    if data and data["title"]:
                        all_product_data.append(data)
                        success_count += 1
                        break
                except Exception as e:
                    print(f"⚠️ Retry {attempt+1}/{MAX_RETRIES} failed for {url}: {str(e)}")
                    time.sleep(2)

            if i % 10 == 0:
                with open("shl_partial_backup.json", "w", encoding="utf-8") as f:
                    json.dump(all_product_data, f, indent=2, ensure_ascii=False)
                print(f"💾 Backup saved at {i} items")

        with open("shl_all_products_paginated.json", "w", encoding="utf-8") as f:
            json.dump(all_product_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Done! Scraped {success_count} products in total.")
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
