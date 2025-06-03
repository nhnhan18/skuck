import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import tempfile
import time
import re

def extract_product_links(url, container_class, start_token, end_token):
    # Thiết lập Chrome headless
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get(url)
        time.sleep(3)

        # Cuộn để load hết trang
        last_height = driver.execute_script("return document.body.scrollHeight")
        unchanged_scroll_count = 0
        while unchanged_scroll_count < 3:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                unchanged_scroll_count += 1
            else:
                unchanged_scroll_count = 0
                last_height = new_height

        # Xác định vùng lấy dữ liệu
        if container_class:
            section = driver.find_element(By.CLASS_NAME, container_class)
            elements = section.find_elements(By.TAG_NAME, "a")
        else:
            elements = driver.find_elements(By.TAG_NAME, "a")

        links, codes = [], []
        seen_links = set()

        from urllib.parse import urlparse

        # --- BẮT ĐẦU VÒNG LẶP ---
        pattern = rf"^{re.escape(url_prefix)}[A-Z]{{2,3}}\d?-\d+.*\.html$"

        for elem in elements:
            href = elem.get_attribute("href")
            if href and "#" not in href:
                if re.match(pattern, href):
                    try:
                        code = href.split(start_token)[1].split(end_token)[0]
                    except:
                        code = "Không xác định"
                    links.append(href)
                    codes.append(code)

                    if href not in seen_links:
                        seen_links.add(href)
                        try:
                            code = href.split(start_token)[1].split(end_token)[0]
                        except:
                            code = "Không xác định"
                        links.append(href)
                        codes.append(code)

        driver.quit()
        df = pd.DataFrame({"Mã sản phẩm": codes, "Link": links})
        df = df.drop_duplicates(subset="Link")
        return df

    except Exception as e:
        driver.quit()
        raise e

# ===============================
# Giao diện Streamlit
# ===============================
st.set_page_config(page_title="CK Product Extractor", layout="centered")
st.title("👜 Trích xuất mã sản phẩm Charles & Keith")

url = st.text_input("🔗 Nhập URL trang web:", "")
url_prefix = st.text_input(
    "🌐 Nhập phần đầu URL sản phẩm (prefix để khớp) [mặc định: https://www.charleskeith.vn/vn]",
    value="https://www.charleskeith.vn/vn"
)
container_class = st.text_input("📦 Class vùng sản phẩm (để trống nếu muốn quét toàn trang):", "js-product-grid")
start_token = st.text_input("🔍 Chuỗi bắt đầu để lấy mã:", "/vn/")
end_token = st.text_input("🔍 Chuỗi kết thúc để lấy mã:", ".html")

if st.button("🚀 Trích xuất"):
    if not url.strip():
        st.warning("⚠️ Bạn cần nhập URL trang web.")
    else:
        with st.spinner("⏳ Đang xử lý..."):
            try:
                df = extract_product_links(url.strip(), container_class.strip(), start_token.strip(), end_token.strip())
                st.success(f"✅ Tìm thấy {len(df)} sản phẩm.")
                st.dataframe(df)

                # Nút tải CSV
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Tải về CSV", csv, file_name="products.csv", mime="text/csv")
            except Exception as e:
                st.error(f"❌ Đã xảy ra lỗi: {str(e)}")
