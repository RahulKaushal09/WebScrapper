import json

from numpy import place
from pygments import highlight
from streamlit import image
import scrape

def extract_description(soup):
    description_section = soup.find('div', class_='readMoreText compact')
    if not description_section:
        return None

    paragraphs = description_section.find_all('p')
    overview = []
    for p in paragraphs:
        text = p.get_text(separator=' ').strip()
        if text:
            overview.append(text)

    return " ".join(overview)

# Function to extract additional information
def extract_additional_info(soup):
    additional_info_section = soup.find('div', class_='row no-gutters objective-information')
    if not additional_info_section:
        return None

    list_items = additional_info_section.find_all('li')
    info_list = [li.text.strip() for li in list_items]
    return info_list

# Function to extract top places
def extract_top_places(soup ,base_url="https://www.holidify.com"):
    top_places_section = soup.find('div', class_='row no-gutters')
    if not top_places_section:
        return None

    places = []
    place_cards = top_places_section.find_all('div', class_='ptv-item card')
    for card in place_cards:
        link_tag = card.find('a', href=True)
        image_div = card.find('div', class_='lazyBG')
        place_name = card.find('p').text.strip() if card.find('p') else None

        if link_tag and image_div:
            places.append({
                "name": place_name,
                "link": f"{base_url}{link_tag['href']}",
                "image": image_div.get('data-original')
            })

    return places
def extract_photos(soup):
    photos_section = soup.find('div', id='lightgallery2')
    if not photos_section:
        return None

    photos = []
    photo_cards = photos_section.find_all('div', class_='images-columns-fixed')
    for card in photo_cards:
        image_div = card.find('div', class_='lazyBG')
        if image_div:
            photos.append(image_div.get('data-original'))

    return photos
def extract_hotel_info(soup, base_url="https://www.holidify.com"):
    # Parse the HTML content with BeautifulSoup

    # List to store hotel data
    hotel_list = []

    # Iterate through each hotel metadata element
    for hotel in soup.find_all('div', class_='hotel-metadata'):
        hotel_data = {}

        # Hotel ID (assuming it's a data attribute or a unique identifier)
        hotel_id = hotel.get('data-itemid')
        hotel_data['hotel_id'] = hotel_id

        # Hotel Name
        hotel_name = hotel.find('h3', class_='card-heading')
        hotel_data['hotel_name'] = hotel_name.text.strip() if hotel_name else None

        # Hotel Link
        hotel_link = hotel.find('a', href=True)
        hotel_data['hotel_link'] = (base_url+hotel_link['href']) if hotel_link else None

        # Hotel Location details
        location = hotel.find('p', class_='hotel-neighbourhood')
        location_data = {}
        if location:
            location_parts = location.text.strip().split(", ")
            if len(location_parts) > 1:
                location_data['neighbourhood'] = location_parts[0]
                location_data['distance_from_city_centre'] = location_parts[1]
            else:
                location_data['neighbourhood'] = location_parts[0]
                location_data['distance_from_city_centre'] = None
        hotel_data['hotel_location'] = location_data

        # Rating and Reviews
        rating_section = hotel.find('span', class_='rating-badge')
        rating_count = hotel.find('span', class_='rating-count')
        rating = rating_section.find('b').text.strip() if rating_section else None
        rateCount = rating_count.text.strip() if rating_count else None
        hotel_data['hotel_location']['rating'] = {
            'score': rating,
            'review_count': rateCount  # Review count to be extracted from another section if needed
        }

        # Top Location (static for now, assuming this data is constant across hotels)
        hotel_data['hotel_location']['top_location'] = "Kashmir"

        # Hotel Images
        img_elements = hotel.find_all('img', class_='card-img-top')
        img_sources = [img.get('data-original')
            for img in img_elements if img.get('data-original')]

        # Extract all <div> elements with 'data-original' attribute
        div_elements = hotel.find_all('div', class_='lazyBG')
        div_sources = [div['data-original'].strip() for div in div_elements if div.get('data-original')]

        # Combine all image URLs
        all_images = img_sources + div_sources

        hotel_data['hotel_images'] = all_images

        # Hotel Description
        hotel_description = hotel.find('div', class_='readMoreSmall')
        hotel_data['hotel_description'] = hotel_description.text.strip() if hotel_description else None

        # Price details
        price = hotel.find('span', class_='price')
        price_data = {}
        if price:
            price_data['amount'] = price.text.strip()
            price_data['description'] = "onwards"
        hotel_data['price'] = price_data

        # Extract the `onclick` attribute
        link_element = hotel.find('a', class_='btn btn-read-more')
        onclick_content = link_element['onclick'] if link_element and 'onclick' in link_element.attrs else None

        # Extract the URL from `onclick`
        import re
        booking_url = None
        if onclick_content:
            match = re.search(r'&quot;(https[^&]+)&quot;', onclick_content)
            if match:
                booking_url = match.group(1)

        

        hotel_data['booking_info'] = {
            'website': "Booking",
            'url': booking_url,
            'hotel_page_url': hotel_data['hotel_link'],
            'hotel_id': hotel_data['hotel_id'],
            'hotel_name': hotel_data['hotel_name']
        }

        # Append the data to the hotel list
        hotel_list.append(hotel_data)

    return hotel_list
def extract_Places_toVisit(soup,base_url="https://www.holidify.com"):
    place_cards = soup.find_all('div', class_='content-card')
    if not place_cards:
        return None

    places = []
    for card in place_cards:
        place_detials = {}
        link_tag = card.find('a', href=True)
        place_detials['link'] = f"{base_url}{link_tag['href']}" if link_tag else None
        title = card.find('h3', class_='card-heading')
        place_detials['title'] = title.text.strip() if title else None
        rating = card.find('span', class_='rating-badge')
        place_detials['rating'] = rating.text.strip() if rating else None
        description = card.find('p', class_='card-text')
        place_detials['description'] = description.text.strip() if description else None
        image_div = card.find_all('img', class_='card-img-top')
        place_detials['image'] = [
            img.get('data-original')
            for img in image_div if img.get('data-original')
        ]
        highlights = card.find('div', class_='readMoreSmall')
        place_detials['highlights'] = highlights.text.strip() if highlights else None

        places.append(place_detials)

    return places
with open('locations.json', 'r') as file:
    data = json.load(file)

for location in data:
    # print(location)
    href = location['href']
    location['PlaceImageLink'] = location['href'] +'photos.html'
    location['PlacesToVisitLink'] = location['href'] +'sightseeing-and-things-to-do.html'
    location['HotelsLink'] = location['href'] +'hotels-where-to-stay.html'
    soup = scrape.scrape_website(location['href'],'holidify')
    insider_data = {
        "full_description": extract_description(soup),
        "additional_info": extract_additional_info(soup),
        "top_places_to_visit": extract_top_places(soup)
    }
    location['fullDetials'] = insider_data
    soup = scrape.scrape_website(location['PlaceImageLink'],'holidify')
    location['photos'] = extract_photos(soup)
    soup = scrape.scrape_website(location['HotelsLink'],'holidify')
    location['hotels'] = extract_hotel_info(soup)
    soup = scrape.scrape_website(location['PlacesToVisitLink'],'holidify')
    location['PlacesToVisit'] = extract_Places_toVisit(soup)
    with open('locations_new.json', 'w') as file:
        json.dump(data, file, indent=4)