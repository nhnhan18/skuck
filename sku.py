import streamlit as st
import pandas as pd
import time
import re

from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By

def extract_product_links(url, container_class, start_token, end_token):
    # Cấu hình trình duyệt Edge ở chế độ headless
    options = EdgeOptions()
    options.add_argument("--headless")  # Chạy không hiển thị giao diện
    options.add_argument("--disable-gpu")  # Tắt tăng tốc GPU
    options.add_argument("--window-size=1920,1080")  # Cố định kích thước trình duyệt

    # Đường dẫn tuyệt đối đến msedgedriver đã tải về
    service = EdgeService(executable_path="C:/path/to/msedgedriver.exe")  # ⚠️ Cập nhật đúng đường dẫn trên máy bạn

    driver = webdriver.Edge(service=service, options=options)

    try:
        driver.get(url)
        time.sleep(3)  # Chờ trang tải xong

        # Cuộn trang để tải toàn bộ sản phẩm (infinite scroll)
        last_height = driver.execute_script("return document.body.scrollHeight")
        unchanged_scroll_count = 0

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                unchanged_scroll_count += 1
                if unchanged_scroll_count >= 3:
                    break  # Dừng nếu không còn cuộn thêm được
            else:
                unchanged_scroll_count = 0
                last_height = new_height

        # Xác định khu vực chứa sản phẩm (nếu có class)
        if container_class:
            product_section = driver.find_element(By.CLASS_NAME, container_class)
            elements = product_section.find_elements(By.TAG_NAME, "a")
        else:
            elements = driver.find_elements(By.TAG_NAME, "a")

        links = []
        codes = []

        # Tạo regex để lọc đúng các link sản phẩm dựa trên URL prefix
        url_prefix = st.session_state.get("url_prefix", "")
        pattern = rf"^{re.escape(url_prefix)}[A-Z]{{2,3}}\d?-\d+.*\.html$"

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

# Giao diện Streamlit
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
