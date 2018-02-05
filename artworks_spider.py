import scrapy
import requests
from io import open as iopen


#For now keep the artist we're scraping the works of in the global variable
artist = 'wolfgang-tillmans'

class QuotesSpider(scrapy.Spider):
  name = "artworks"
  start_urls = [
    'https://www.artsy.net/artist/'+ artist + '/works/',
  ]
  downloaded_artworks = []

  def parse(self, response):
    #get links from the first page
    links = response.css('a').xpath('@href').extract()
    for link in links:
      if (link.startswith('/artwork')):
        yield response.follow(link, self.parse_artwork)

    #now scroll
    page_number = 2
    links = self.scroll_the_page(artist, page_number)
    while len(links) > 0:
      for link in links:
        yield response.follow(link, self.parse_artwork)
      page_number +=1
      links = self.scroll_the_page(artist, page_number)
    print("NO MORE PAGES AT PAGE: " + str(page_number))  

  def parse_artwork(self, response):
    images = response.css('body').css('img').xpath('@data-src').extract()
    for img in images:
      if img.find("larger.jpg") >=0:
        img.replace("larger.jpg", "normalized.jpg")
        i = response.url.rfind('/')
        artwork_name = response.url[i+1:]
        artwork_name += '.jpg'
        if artwork_name not in self.downloaded_artworks:
          self.downloaded_artworks.append(artwork_name)
          self.download_image(img, artwork_name)

  def download_image(self, url, filename):
    image = requests.get(url)
    with iopen(filename, 'wb') as file:
      file.write(image.content)

  def scroll_the_page(self, artist, page_number):
    headers = {
        'Origin': 'https://www.artsy.net',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9,pl;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Referer': 'https://www.artsy.net/artist/' + artist + '/works',
        'Connection': 'keep-alive',
        'X-Request-Id': '2c0b1c9c-cd14-49ea-81d0-454bb307c4a3',
    }

    data = '{"query":"query filterArtworks(\\n  $artist_id: String!,\\n  $page: Int,\\n  $size: Int,\\n  $for_sale: Boolean,\\n  $medium: String,\\n  $period: String,\\n  $partner_id: ID,\\n  $sort: String\\n) {\\n  filter_artworks(\\n    artist_id:$artist_id,\\n    aggregations: [TOTAL],\\n    page: $page,\\n    size: $size,\\n    for_sale: $for_sale,\\n    medium: $medium,\\n    period: $period,\\n    partner_id: $partner_id\\n    sort: $sort\\n  ){\\n    total\\n    hits {\\n      ... artwork_brick\\n    }\\n  }\\n}\\n\\nfragment artwork_brick on Artwork {\\n  id\\n  href\\n  title\\n  image {\\n    placeholder\\n    thumb: resized(width: 350, version: [\\"large\\", \\"larger\\"]) {\\n      url\\n      height\\n    }\\n  }\\n\\n  ... artwork_metadata_stub\\n}\\n\\nfragment artwork_metadata_stub on Artwork {\\n  ... artwork_metadata_stub_didactics\\n  ... artwork_metadata_stub_contact\\n}\\nfragment artwork_metadata_stub_didactics on Artwork {\\n  href\\n  title\\n  date\\n  sale_message\\n  cultural_maker\\n  artists(shallow: true) {\\n    href\\n    name\\n  }\\n  collecting_institution\\n  partner(shallow: true) {\\n    name\\n  }\\n}\\nfragment artwork_metadata_stub_contact on Artwork {\\n  _id\\n  href\\n  is_inquireable\\n  sale {\\n    href\\n    is_auction\\n    is_closed\\n    is_live_open\\n    is_open\\n    is_preview\\n  }\\n  sale_artwork {\\n    highest_bid {\\n      display\\n    }\\n    opening_bid {\\n      display\\n    }\\n    counts {\\n      bidder_positions\\n    }\\n  }\\n  partner(shallow: true) {\\n    type\\n    href\\n  }\\n}","variables":{"artist_id":' + '"' + artist + '"' + ',"size":9,"page":' + str(page_number) + ',"sort":"-partner_updated_at"}}'   
    response = requests.post('https://metaphysics-production.artsy.net/', headers=headers, data=data)
    hits = response.json()['data']['filter_artworks']['hits']
    links_to_artworks = []
    for hit in hits:
      links_to_artworks.append(hit['href'])
    return links_to_artworks  
