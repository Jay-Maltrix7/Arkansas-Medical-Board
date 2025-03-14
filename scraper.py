import requests
from bs4 import BeautifulSoup
import csv
import time
from datetime import datetime

def get_form_values(session):
    url = 'https://www.armedicalboard.org/public/directory/lookup.aspx'
    response = session.get(url)
    print(f"Initial GET request status code: {response.status_code}")
    
    if response.status_code != 200:
        print("Failed to get initial page")
        print("Response content:", response.text[:500])
        raise Exception(f"Initial request failed with status code {response.status_code}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Debug form values
    form_values = {
        '__VIEWSTATE': soup.find('input', {'id': '__VIEWSTATE'})['value'],
        '__VIEWSTATEGENERATOR': soup.find('input', {'id': '__VIEWSTATEGENERATOR'})['value'],
        '__EVENTVALIDATION': soup.find('input', {'id': '__EVENTVALIDATION'})['value'],
        '__VIEWSTATEENCRYPTED': soup.find('input', {'id': '__VIEWSTATEENCRYPTED'})['value'] if soup.find('input', {'id': '__VIEWSTATEENCRYPTED'}) else ''
    }
    
    print("Found form values:")
    for key, value in form_values.items():
        print(f"{key}: {value[:50]}..." if value else f"{key}: None")
    
    return form_values

def make_request(session, page_number, form_values):
    base_url = 'https://www.armedicalboard.org'
    
    if page_number == 1:
        # First get the advanced search page
        url = f'{base_url}/public/directory/lookup.aspx'
        response = session.get(url)
        print(f"Initial GET request status code: {response.status_code}")
        
        # Get redirected to AdvancedDirectorySearch.aspx and get its form values
        soup = BeautifulSoup(response.text, 'html.parser')
        form_values = {
            '__VIEWSTATE': soup.find('input', {'id': '__VIEWSTATE'})['value'],
            '__VIEWSTATEGENERATOR': soup.find('input', {'id': '__VIEWSTATEGENERATOR'})['value'],
            '__EVENTVALIDATION': soup.find('input', {'id': '__EVENTVALIDATION'})['value'],
            '__VIEWSTATEENCRYPTED': soup.find('input', {'id': '__VIEWSTATEENCRYPTED'})['value'] if soup.find('input', {'id': '__VIEWSTATEENCRYPTED'}) else ''
        }
        
        # Submit the search form with all checkboxes checked
        data = {
            '__VIEWSTATE': form_values['__VIEWSTATE'],
            '__VIEWSTATEGENERATOR': form_values['__VIEWSTATEGENERATOR'],
            '__EVENTVALIDATION': form_values['__EVENTVALIDATION'],
            '__VIEWSTATEENCRYPTED': form_values['__VIEWSTATEENCRYPTED'],
            'ctl00$MainContentPlaceHolder$txtBoxdirectoryFirstName': '',
            'ctl00$MainContentPlaceHolder$txtBoxdirLastName': '',
            'ctl00$MainContentPlaceHolder$ckBoxdirAnySpeciality': 'on',
            'ctl00$MainContentPlaceHolder$chBoxdirAnySearchLicType': 'on',
            'ctl00$MainContentPlaceHolder$ckBoxdirSearchAnyBoardCert': 'on',
            'ctl00$MainContentPlaceHolder$ckBoxdirSearchAnyCity': 'on',
            'ctl00$MainContentPlaceHolder$ckBoxdirSearchAnyState': 'on',
            'ctl00$MainContentPlaceHolder$ckBoxdirSearchAnyCount': 'on',
            'ctl00$MainContentPlaceHolder$txtBoxdirSearchZip': '',
            'ctl00$MainContentPlaceHolder$btnDirSearch': 'Search'
        }
        
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': base_url,
            'Referer': response.url,
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        
        print("\nSubmitting search form...")
        print("Using URL:", response.url)
        print("Form data:", {k: v[:50] + '...' if isinstance(v, str) and len(v) > 50 else v for k, v in data.items()})
        
        response = session.post(response.url, headers=headers, data=data)
        print(f"Search form POST status code: {response.status_code}")
        
    else:
        # For pagination, use the form values from the results page
        url = f'{base_url}/public/directory/lookup.aspx'
        data = {
            '__EVENTTARGET': 'ctl00$MainContentPlaceHolder$gvLookup',
            '__EVENTARGUMENT': f'Page${page_number}',
            '__VIEWSTATE': form_values['__VIEWSTATE'],
            '__VIEWSTATEGENERATOR': form_values['__VIEWSTATEGENERATOR'],
            '__EVENTVALIDATION': form_values['__EVENTVALIDATION'],
            '__VIEWSTATEENCRYPTED': form_values['__VIEWSTATEENCRYPTED']
        }
        
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': base_url,
            'Referer': url,
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        
        print(f"\nFetching page {page_number}...")
        response = session.post(url, headers=headers, data=data)
        print(f"Page {page_number} POST status code: {response.status_code}")
    
    print("Final URL:", response.url)
    
    return response.text

def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    doctors = []
    
    # Debug - check if we got any table
    table = soup.find('table', {'id': 'ctl00_MainContentPlaceHolder_gvLookup'})
    if not table:
        print("No table found in response!")
        print("Available tables:")
        tables = soup.find_all('table')
        for i, t in enumerate(tables):
            print(f"Table {i} ID: {t.get('id', 'No ID')}")
        return doctors
    
    # Find all rows in the table
    rows = table.find_all('tr')
    print(f"Found {len(rows)} rows in table")
    
    for row in rows[1:]:  # Skip header row
        cells = row.find_all('td')
        if len(cells) == 7:  # Make sure it's a data row
            try:
                license_id = cells[0].find('a')['href'].split('=')[1]
                name = cells[1].find('span').text.strip()
                city = cells[2].find('span').text.strip()
                state = cells[3].find('span').text.strip()
                specialty = cells[4].find('span').text.strip()
                title = cells[5].find('span').text.strip()
                verification_url = cells[6].find('a')['href']
                
                doctors.append({
                    'license_id': license_id,
                    'name': name,
                    'city': city,
                    'state': state,
                    'specialty': specialty,
                    'title': title,
                    'verification_url': verification_url
                })
            except Exception as e:
                print(f"Error parsing row: {str(e)}")
                print("Row content:", row)
    
    return doctors

def save_to_csv(doctors, filename):
    fieldnames = ['license_id', 'name', 'city', 'state', 'specialty', 'title', 'verification_url']
    
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerows(doctors)

def main():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'doctors_{timestamp}.csv'
    
    # Create CSV file with headers
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['license_id', 'name', 'city', 'state', 'specialty', 'title', 'verification_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
    
    session = requests.Session()
    form_values = get_form_values(session)
    
    page = 1
    total_doctors = 0
    
    while True:
        try:
            print(f"\nFetching page {page}...")
            html = make_request(session, page, form_values)
            doctors = parse_page(html)
            
            if not doctors:  # If no doctors found, we've reached the end
                print("No doctors found on this page")
                break
                
            total_doctors += len(doctors)
            save_to_csv(doctors, filename)
            print(f"Found {len(doctors)} doctors on page {page}")
            print(f"Total doctors scraped: {total_doctors}")
            
            # Update form values for next request from the current response
            soup = BeautifulSoup(html, 'html.parser')
            form_values = {
                '__VIEWSTATE': soup.find('input', {'id': '__VIEWSTATE'})['value'],
                '__VIEWSTATEGENERATOR': soup.find('input', {'id': '__VIEWSTATEGENERATOR'})['value'],
                '__EVENTVALIDATION': soup.find('input', {'id': '__EVENTVALIDATION'})['value'],
                '__VIEWSTATEENCRYPTED': soup.find('input', {'id': '__VIEWSTATEENCRYPTED'})['value'] if soup.find('input', {'id': '__VIEWSTATEENCRYPTED'}) else ''
            }
            
            page += 1
            time.sleep(1)  # Be nice to the server
            
        except Exception as e:
            print(f"Error on page {page}: {str(e)}")
            print("Full error:", e)
            break
    
    print(f"\nScraping complete! Total doctors found: {total_doctors}")
    print(f"Data saved to: {filename}")

if __name__ == "__main__":
    main()
