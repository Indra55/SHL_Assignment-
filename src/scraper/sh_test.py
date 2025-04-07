import json
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://www.shl.com/solutions/products/product-catalog/"
MAX_WORKERS = 3  # Number of concurrent browser instances

def get_stealthy_driver():
    options = uc.ChromeOptions()
    
    # Stealth settings
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    
    # Randomize user agent
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ]
    user_agent = random.choice(user_agents)
    options.add_argument(f"user-agent={user_agent}")
    
    # For undetected_chromedriver
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    
    try:
        driver = uc.Chrome(
            options=options,
            use_subprocess=True,
            headless=False,  # Changed to non-headless to improve reliability
        )
        
        # Mask selenium detection
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": user_agent
        })
        
        return driver
    except Exception as e:
        print(f"Error initializing driver: {e}")
        raise

def human_like_delay(min_sec=1, max_sec=2):
    """Random delay to mimic human behavior"""
    time.sleep(random.uniform(min_sec, max_sec))

def accept_cookies(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
        )
        btn = driver.find_element(By.ID, "onetrust-accept-btn-handler")
        human_like_delay(0.5, 1)
        btn.click()
        print("🍪 Cookie banner accepted.")
        human_like_delay(1)
    except:
        print("⚠️ No cookie banner or already accepted.")

def extract_product_info(driver, product_url, index):
    """Extract information from a single product page"""
    start_time = time.time()
    try:
        driver.get(product_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
    except Exception as e:
        print(f"⚠️ [{index}] Failed to load product page: {str(e)}")
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
    except Exception as e:
        print(f"⚠️ [{index}] Failed to extract title: {str(e)}")

    def safe_extract(xpath):
        try:
            return driver.find_element(By.XPATH, xpath).text.strip()
        except:
            return ""

    data["description"] = safe_extract("//h4[text()='Description']/following-sibling::p")
    data["job_level"] = safe_extract("//h4[text()='Job levels']/following-sibling::p")
    data["languages"] = safe_extract("//h4[text()='Languages']/following-sibling::p")
    
    try:
        time_text = safe_extract("//h4[text()='Assessment length']/following-sibling::p")
        data["completion_time"] = time_text.split('=')[-1].strip() if "=" in time_text else time_text
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

    elapsed = time.time() - start_time
    print(f"⏱ Product extraction completed in {elapsed:.1f} seconds")
    return data

def scrape_links_traditional(driver):
    """Extract all product links using reliable traditional pagination"""
    all_links = set()
    page = 1
    max_pages = 13  # From your console output it looks like 32 pages total
    
    driver.get(BASE_URL)
    accept_cookies(driver)
    human_like_delay(2, 3)
    
    while page <= max_pages:
        try:
            print(f"\n🔍 Processing page {page}...")
            
            # Wait for the table to load
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[contains(@class,'custom__table-wrapper')][.//th[contains(text(),'Individual Test Solutions')]]")
                )
            )
            human_like_delay(1, 2)
            
            # Get the correct table
            tables = driver.find_elements(
                By.XPATH, "//div[contains(@class,'custom__table-wrapper')][.//th[contains(text(),'Individual Test Solutions')]]")
            
            if not tables:
                print("⚠️ No Individual Tests table found")
                break
                
            table = tables[0]
            
            # Extract links
            links = table.find_elements(
                By.CSS_SELECTOR, "table tbody tr td.custom__table-heading__title a")
            
            print(f"Found {len(links)} product links on this page")
            
            if not links:
                print("⚠️ No links found on this page")
                break
                
            # Store links
            new_links = 0
            for link in links:
                href = link.get_attribute("href")
                if href and href not in all_links:
                    all_links.add(href)
                    new_links += 1
            print(f"Added {new_links} new links (total: {len(all_links)})")
            
            # Save progress after each page
            with open(f"shl_links_progress_page{page}.json", "w") as f:
                json.dump(list(all_links), f)
            
            # Check if we should continue pagination
            try:
                # Find the next button by looking for all page buttons first
                pagination = table.find_element(By.CSS_SELECTOR, "ul.pagination")
                next_btn = None
                
                # Try multiple methods to find the next button
                try:
                    next_btn = pagination.find_element(
                        By.CSS_SELECTOR, "li.pagination__item.-arrow.-next:not(.-disabled) a")
                except:
                    try:
                        # Look for a specific class or attribute pattern
                        next_btns = pagination.find_elements(
                            By.CSS_SELECTOR, "li.pagination__item.-arrow.-next a")
                        for btn in next_btns:
                            # Check if the button isn't disabled
                            if "disabled" not in btn.get_attribute("class"):
                                next_btn = btn
                                break
                    except:
                        pass
                
                if not next_btn:
                    print("✅ Reached last page or couldn't find next button")
                    break
                
                # Ensure the button is in view
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", next_btn)
                human_like_delay(1, 2)
                
                print("➡️ Clicking to page", page + 1)
                driver.execute_script("arguments[0].click();", next_btn)
                page += 1
                
                # Wait for page to load
                human_like_delay(3, 5)
                
            except Exception as e:
                print(f"⛔ Pagination error: {str(e)}")
                # Try to recover if possible
                if page < max_pages:
                    try:
                        # Try directly going to the next page via URL if appropriate
                        current_url = driver.current_url
                        if "?page=" in current_url:
                            base_url = current_url.split("?page=")[0]
                            next_page_url = f"{base_url}?page={page+1}"
                            driver.get(next_page_url)
                            page += 1
                            human_like_delay(3, 5)
                            continue
                    except:
                        pass
                
                break
                
        except Exception as e:
            print(f"⚠️ Scraping error on page {page}: {str(e)}")
            # Try to recover
            try:
                driver.refresh()
                human_like_delay(3, 5)
                continue
            except:
                break
            
    print(f"\n✅ Finished scraping. Total unique product links found: {len(all_links)}")
    return list(all_links)

def worker_process(worker_id, links_chunk):
    """Process a chunk of links with a dedicated browser instance"""
    print(f"🔄 Worker {worker_id} starting with {len(links_chunk)} links")
    driver = get_stealthy_driver()
    results = []
    
    try:
        # Process each link in this worker's chunk
        for i, url in enumerate(links_chunk, 1):
            link_index = f"{worker_id}:{i}/{len(links_chunk)}"
            print(f"\nWorker {worker_id} processing {i}/{len(links_chunk)} - {url}")
            
            for attempt in range(2):  # Max 2 retries
                try:
                    data = extract_product_info(driver, url, link_index)
                    if data and data.get("title"):
                        results.append(data)
                        print(f"✅ Worker {worker_id} successfully scraped {i}/{len(links_chunk)}")
                        break
                    human_like_delay(1, 2)
                except Exception as e:
                    print(f"⚠️ Worker {worker_id}, attempt {attempt+1} failed for link {i}: {str(e)}")
                    human_like_delay(1, 3)
            
            # Save progress every 5 items
            if i % 5 == 0 or i == len(links_chunk):
                with open(f"shl_worker_{worker_id}_progress.json", "w") as f:
                    json.dump(results, f, indent=2)
                print(f"💾 Worker {worker_id} saved progress ({len(results)} items)")
    finally:
        driver.quit()
        print(f"🚗 Worker {worker_id} browser closed")
    
    return results

def main():
    print("🚀 Starting improved SHL product scraper...")
    
    # Step 1: Get all product links
    print("\n🔍 Collecting product links...")
    start_time = time.time()
    
    # Check if we have saved links from a previous run
    product_links = []
    try:
        with open("shl_all_links.json", "r") as f:
            product_links = json.load(f)
            print(f"📂 Loaded {len(product_links)} links from previous run")
    except:
        print("📂 No saved links found, scraping fresh...")
        main_driver = get_stealthy_driver()
        try:
            product_links = scrape_links_traditional(main_driver)
            # Save all links for future runs
            with open("shl_all_links.json", "w") as f:
                json.dump(product_links, f, indent=2)
        finally:
            main_driver.quit()
    
    print(f"✅ Found {len(product_links)} products in {time.time()-start_time:.1f} seconds")
    
    if not product_links:
        print("❌ No product links found. Exiting.")
        return
    
    # Step 2: Process products in parallel
    print("\n📝 Extracting product details using parallel workers...")
    start_time = time.time()
    
    # Split links into chunks for parallel processing
    chunks = []
    chunk_size = max(1, len(product_links) // MAX_WORKERS)
    
    for i in range(0, len(product_links), chunk_size):
        end = min(i + chunk_size, len(product_links))
        chunks.append(product_links[i:end])
    
    print(f"🧩 Split {len(product_links)} links into {len(chunks)} chunks for {MAX_WORKERS} workers")
    
    # Process chunks in parallel
    all_results = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(worker_process, i+1, chunk): i+1 for i, chunk in enumerate(chunks)}
        
        for future in futures:
            worker_id = futures[future]
            try:
                results = future.result()
                all_results.extend(results)
                print(f"📦 Worker {worker_id} completed with {len(results)} results")
            except Exception as e:
                print(f"❌ Worker {worker_id} failed: {str(e)}")
                
                # Try to load partial results if available
                try:
                    with open(f"shl_worker_{worker_id}_progress.json", "r") as f:
                        partial_results = json.load(f)
                        print(f"📂 Recovered {len(partial_results)} partial results from worker {worker_id}")
                        all_results.extend(partial_results)
                except:
                    print(f"⚠️ Could not recover any results from worker {worker_id}")
    
    # Combine and save final results
    with open("shl_individual_tests_final.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    elapsed_time = time.time() - start_time
    print(f"\n✅ Successfully scraped {len(all_results)}/{len(product_links)} products")
    print(f"⏱ Total processing time: {elapsed_time/60:.1f} minutes")
    
    if all_results:
        print(f"⏱ Average time per product: {elapsed_time/len(all_results):.1f} seconds")

if __name__ == "__main__":
    main()