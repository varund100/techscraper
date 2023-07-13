from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import pandas as pd
from bs4 import BeautifulSoup
import os

app = Flask(__name__)
app.secret_key = "file not uploaded"

UPLOAD_FOLDER = 'uploads/'


def techScraper(website):
    # Initialize the ChromeDriver
    chrome_driver_path = r'C:\webdrivers\chromedriver.exe'  # Adjust the path to the ChromeDriver executable if necessary
    driver = webdriver.Chrome(service=Service(chrome_driver_path))
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')

    try:
        website = website.split('/')
        website = website[len(website) - 1]
        if 'www.' in website:
            website = website.split('www.')[1]

        company_tech_url = f'https://www.builtwith.com/{website}'
        driver.get(str(company_tech_url))
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        src = driver.page_source
        soup = BeautifulSoup(src, 'lxml')

        sections = soup.find_all(attrs={'class': 'card mt-4 mb-2'})

        analytics_tech = ''
        ecommerce_tech = ''

        for section in sections:
            header = section.find('h6').get_text(strip=True)
            if header == 'Analytics and Tracking':
                analytics_list = section.find_all('h5')
                analytics_tech = ', '.join([tool.get_text(strip=True) for tool in analytics_list])
            elif header == 'eCommerce':
                ecommerce_list = section.find_all('h2')
                ecommerce_tech = ', '.join([tool.get_text(strip=True) for tool in ecommerce_list])

        driver.quit()

        return analytics_tech, ecommerce_tech
    except:
        driver.quit()
        return '', ''


@app.route('/', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file.filename == '':
            flash('No file selected. Please upload a file.', 'warning')
            return redirect(url_for('upload'))

        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)  # Save the file to the 'uploads/' directory

        # Check if the file exists
        if os.path.exists(file_path):
            print("File Path:", file_path)
            try:
                # Read the Excel file using pandas
                dataset = pd.read_excel(file_path)

                # Update the DataFrame with the new values 
                updated_dataset = dataset.copy()
                for index, row in updated_dataset.iterrows():
                    website = row["Website URL"]
                    if pd.isna(row["Analytics Tech"]) and pd.isna(row["Webtech1.0"]):
                        print(f"Updating row {index}")
                        a, b = techScraper(website)
                        print(f"Retrieved values: {a}, {b}")
                        updated_dataset.at[index, "Analytics Tech"] = a
                        updated_dataset.at[index, "Webtech1.0"] = b

                # Save the updated DataFrame to a new Excel file
                updated_file_path = os.path.join(UPLOAD_FOLDER, 'updated_' + file.filename)
                updated_dataset.to_excel(updated_file_path, index=False)
                print("Updated DataFrame saved to:", updated_file_path)

                # Provide the download link to the newly created file
                download_link = f"/download/{updated_file_path}"
                print("Download link:", download_link)

                return render_template('index.html', file_path=download_link)
            except Exception as e:
                print("Error processing the file:", str(e))
                flash("Error processing the file. Please try again.", 'danger')
                return redirect(url_for('upload'))
        else:
            flash("Error saving the file. Please try again.", 'danger')
            return redirect(url_for('upload'))

    return render_template('index.html')


@app.route('/download/<path:file_path>')
def download(file_path):
    # Convert the file path separators to match the platform
    file_path = file_path.replace('/', os.sep)

    # Get the relative file path
    relative_file_path = os.path.relpath(file_path, app.root_path)

    # Check if the file exists
    if os.path.exists(relative_file_path):
        print("File saved successfully:", file_path)
        return send_file(relative_file_path, as_attachment=True)
    else:
        return "Error: File not found."


if __name__ == '__main__':
    app.run(debug=True)
