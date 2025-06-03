import streamlit as st
import pandas as pd
import time
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def extract_product_links(url, container_class, start_token, end_token):
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(3)

        last_height = driver.execute_script("return document.body.scrollHeight")
        unchanged_scroll_count = 0

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                unchanged_scroll_count += 1
                if unchanged_scroll_count >= 3:
                    break
            else:
                unchanged_scroll_count = 0
                last_height = new_height

        if container_class:
            product_section = driver.find_element(By.CLASS_NAME, container_class)
            elements = product_section.find_elements(By.TAG_NAME, "a")
        else:
            elements = driver.find_elements(By.TAG_NAME, "a")

        links = []
        codes = []

        url_prefix = st.session_state.get("url_prefix", "")
        pattern = rf"^{re.escape(url_prefix)}[A-Z]{{2,3}}\d?-\d+.*\\.html$"

        for elem in elements:
            href = elem.get_attribute("href")
            if href and "#" not in href and re.match(pattern, href):
                try:
                    code = href.split(start_token)[1].split(end_token)[0]
                except:
                    code = "Không xác định"
                links.append(href)
                codes.append(code)

        return codes, links

    finally:
        driver.quit()

st.set_page_config(page_title="Trích xuất mã sản phẩm", layout="wide")
st.title("🛒 Trích xuất mã sản phẩm từ website")

url = st.text_input("Nhập đường dẫn trang web sản phẩm:")
container_class = st.text_input("Class vùng sản phẩm (bỏ trống nếu toàn trang):", value="js-product-grid")
url_prefix = st.text_input("🌐 Nhập phần đầu URL sản phẩm:", value="https://www.charleskeith.vn/vn")
start_token = st.text_input("🔍 Chuỗi bắt đầu để lấy mã:", value="/vn/")
end_token = st.text_input("🔚 Chuỗi kết thúc để lấy mã:", value=".html")

if st.button("🚀 Trích xuất") and url:
    st.session_state["url_prefix"] = url_prefix
    with st.spinner("Đang tải và xử lý trang web..."):
        try:
            codes, links = extract_product_links(url, container_class, start_token, end_token)
            st.success(f"✅ Tìm thấy {len(links)} sản phẩm.")
            df = pd.DataFrame({"Mã sản phẩm": codes, "Link": links})
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"❌ Đã xảy ra lỗi: {e}")
