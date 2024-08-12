import streamlit as st
from PIL import Image
import io
import google.generativeai as genai
import requests
from io import BytesIO
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Function to configure the API key
def configure_api(api_key):
    genai.configure(api_key=api_key)

# Convert input images to bytes
def input_image_setup(images):
    if not images:
        raise ValueError("No images provided")

    image_parts = []
    for image in images:
        img = Image.open(image)
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        image_parts.append({
            "mime_type": "image/jpeg",
            "data": img_byte_arr
        })

    return image_parts

def improve_prompt(image_prompts, question):
    generation_config = {
        "temperature": 0,
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": 4096,
    }

    model = genai.GenerativeModel(model_name="gemini-1.5-pro", generation_config=generation_config)

    input_prompt = """You are an expert in writing prompts using prompting techniques."""

    question_prompt = f"""Given a chart and an accompanying question, enhance the question using advanced prompting techniques such as chain-of-thought 
    reasoning or self-consistency to provide a more comprehensive and accurate response. Divide problem into small steps. Do not include any other information in the output.

    Question : {question}"""

    prompt_parts = [input_prompt] + image_prompts + [question_prompt]
    response = model.generate_content(prompt_parts)
    return str(response.text)

def get_image_info(image_prompts, question, task_type):
    generation_config = {
        "temperature": 0,
        "max_output_tokens": 4096,
    }

    model = genai.GenerativeModel(model_name="gemini-1.5-pro", generation_config=generation_config)

    input_prompt = """You are an expert in reading and analyzing the charts."""

    question_prompt = f"""Question : {question}"""

    if task_type == "Summarization":
        question_prompt = f"""Question : {question}

                              Address the following points, you don't need to include every point or print the output in the given format, these points 
                              are just for understanding the chart: 

                              Chart Type and Structure:

                              Identify the type of chart (e.g., bar chart, line graph, pie chart).
                              Note the axes labels, units, and any legend information.
                              Mention the time period or categories represented, if applicable.

                              Main Topic and Purpose:

                              Determine the primary subject matter of the chart.
                              Infer the intended purpose or main message of the visualization.

                              Key Data Points:

                              Identify the highest and lowest values.
                              Highlight any significant outliers or anomalies.
                              Note any critical threshold values or benchmarks.

                              Trends and Patterns:

                              Describe the overall trend (e.g., increasing, decreasing, stable).
                              Identify any cyclical patterns or seasonality.
                              Mention any notable sub-trends within specific segments.

                              Comparisons and Relationships:

                              Compare different categories or time periods.
                              Identify any correlations between variables.
                              Highlight proportions or distributions, if relevant.

                              Context and Implications:

                              Consider any provided context or background information.
                              Infer potential causes for observed trends or anomalies.
                              Suggest possible implications or consequences of the data.

                              Data Quality and Limitations:

                              Note any apparent gaps or inconsistencies in the data.
                              Mention any potential biases or limitations in the presentation."""
    elif task_type == "Question Answering":
        question_prompt = improve_prompt(image_prompts,question)
      
    elif task_type == "Comparison":
        question_prompt = f"""Question : {question}

                              Address the following points, you don't need to include every point or print the output in the given format, these points 
                              are just for understanding the chart:

                              Basic Information:

                              Identify the type of each chart (e.g., bar, line, pie)
                              Note the subject matter, time periods, or categories represented in each
                              Describe the key variables or metrics being measured

                              Structural Similarities and Differences:

                              Compare the scales, units, and axes used
                              Identify any differences in data granularity or time frames
                              Note variations in how data is grouped or categorized

                              Data Trends:

                              Describe the overall trend in each chart (e.g., increasing, decreasing, fluctuating)
                              Compare the magnitude and direction of trends across charts
                              Identify any common patterns or divergences

                              Key Data Points:

                              Compare the highest and lowest values across charts
                              Identify notable outliers or anomalies in each chart
                              Highlight any significant threshold values or benchmarks

                              Relative Performance:

                              Compare performance metrics across charts (e.g., growth rates, market share)
                              Identify which chart shows better performance in relevant metrics
                              Note any crossover points where relative performance changes

                              Time-based Analysis (if applicable):

                              Compare data at specific time points across charts
                              Identify any lag or lead relationships between trends
                              Note differences in seasonality or cyclical patterns

                              Composition and Distribution:

                              Compare the distribution of data across categories
                              Identify differences in the composition of totals or wholes
                              Note any shifts in proportions or ratios between charts

                              Correlations and Relationships:

                              Identify any correlations between variables across charts
                              Compare the strength and direction of relationships
                              Note any unexpected or contradictory relationships

                              Context and External Factors:

                              Consider how external factors might explain differences
                              Identify any relevant events or conditions that could impact the comparison
                              Note any limitations in comparing the data sets"""

    prompt_parts = [input_prompt] + image_prompts + [question_prompt]
    response = model.generate_content(prompt_parts)
    return str(response.text)

def identify_task_type(image_prompts, question):
    generation_config = {
        "temperature": 0,
        "max_output_tokens": 4096,
    }

    model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)

    input_prompt = """You are an expert in reading and analyzing the charts."""

    question_prompt = f"""Given a chart and a question you have tell the question belongs to which category. Only return the category type of the question nothing else.
                          Question : {question}

                          Categories: 
                          1.  If question is related to question answering or numerical question answering based on chart return 'Question Answering'
                          2.  If question related to Chart Summarization or Chart Analysis is given return 'Summarization'
                          3.  Find number of images given, If more than 1 images are given return 'Comparison'
                      """

    prompt_parts = [input_prompt] + image_prompts + [question_prompt]
    response = model.generate_content(prompt_parts)
    return str(response.text).strip()

def final_setup(images, question):
    image_prompts = input_image_setup(images)
    task_type_output = identify_task_type(image_prompts, question)
    image_output = get_image_info(image_prompts, question, task_type_output)
    return image_output

def take_screenshot(url):
    # Configure Selenium WebDriver
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_service = Service('/path/to/chromedriver')  # Update this path
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    # Open the URL and take a screenshot
    driver.get(url)
    screenshot = driver.get_screenshot_as_png()
    driver.quit()
    return Image.open(BytesIO(screenshot))

# Streamlit app
st.set_page_config(page_title="InsightsBoard", page_icon=":bar_chart:", layout="wide")

# Apply the theme
st.markdown("""
    <style>
    .reportview-container {
        background-color: #f5f5f5;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
    .sidebar .sidebar-content .sidebar-header {
        background-color: #1e3a8a;
        color: #ffffff;
    }
    .stButton>button {
        background-color: #1e3a8a;
        color: #ffffff;
        border-radius: 4px;
        border: none;
    }
    .stImage {
        max-width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.image("https://github.com/GauravDdhanwant/Insightsboard/blob/main/Nice%20Icon%203.png", width=150)
st.sidebar.title("InsightsBoard")

api_key = st.sidebar.text_input("Enter your API Key", type="password")

if api_key:
    configure_api(api_key)

    uploaded_files = st.sidebar.file_uploader("Upload Chart Images", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    dashboard_url = st.sidebar.text_input("Enter Dashboard URL (optional)")
    question = st.sidebar.text_input("Enter Your Question Here")

    if st.sidebar.button("Analyze"):
        col1, col2 = st.columns([3, 6])
        
        with col1:
            if uploaded_files:
                uploaded_image = Image.open(uploaded_files[0])
                st.image(uploaded_image, use_column_width=True)
        
        with col2:
            if dashboard_url:
                screenshot = take_screenshot(dashboard_url)
                st.image(screenshot, caption="Screenshot of Dashboard", use_column_width=True)

            if uploaded_files and question:
                with st.spinner("Processing..."):
                    result = final_setup(uploaded_files, question)
                    st.write(result)
            else:
                st.warning("Please upload images and enter a question.")
else:
    st.warning("Please enter your API Key.")
