import requests, asyncio, aiohttp
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup, Tag
from typing import TypedDict
from types import TracebackType

def normalize_url(raw_url: str) -> str:
    splitted_url = urlsplit(raw_url)
    return splitted_url.netloc.lower() + splitted_url.path.rstrip("/").lower()

def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    h2 = soup.find("h2")
    if isinstance(h1, Tag):
        return h1.get_text(strip=True)
    elif isinstance(h2, Tag):
        return h2.get_text(strip=True)
    else:
        return ""

def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")
    if isinstance(main, Tag):
        p = main.find("p")
        return p.get_text(strip=True) if isinstance(p, Tag) else ""
    elif isinstance(soup.find("p"), Tag):
        return (soup.find("p")).get_text(strip=True)
    else:
        return ""

def get_urls_from_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    a_tags = soup.find_all("a")
    urls = []
    for a in a_tags:
        if not isinstance(a, Tag):
            continue
        href = a.get("href")
        if isinstance(href, str) and href:
            try:
                urls.append(urljoin(base_url, href))
            except Exception as e:
                print(f"{str(e)}: {href}")
    return urls

def get_images_from_html(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    img_tags = soup.find_all("img")
    image_urls = []
    for img in img_tags:
        if not isinstance(img, Tag):
            continue
        src = img.get("src")
        if isinstance(src, str) and src:
            try:
                image_urls.append(urljoin(base_url, src))
            except Exception as e:
                print(f"{str(e)}: {src}")
    return image_urls

class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]

def extract_page_data(html: str, page_url: str) -> PageData:
    heading = get_heading_from_html(html)
    first_p = get_first_paragraph_from_html(html)
    links = get_urls_from_html(html, page_url)
    image_urls = get_images_from_html(html, page_url)

    return {
        "url": page_url,
        "heading": heading,
        "first_paragraph": first_p,
        "outgoing_links": links,
        "image_urls": image_urls,
    }





class AsyncCrawler:
    def __init__(self, base_url, max_concurrency=1, max_pages=10):
        self.base_url = base_url
        self.base_domain = urlsplit(base_url).netloc
        self.page_data = {}
        self.visited = set()
        self.lock = asyncio.Lock()
        self.max_concurrency = max_concurrency
        self.max_pages = max_pages
        self.should_stop = False
        self.all_tasks = set()
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self


    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def add_page_visit(self, normalized_url):
        async with self.lock:
            if self.should_stop:
                return False
            if len(self.visited) >= self.max_pages:
                self.should_stop = True
                print(f"Reached maximum number of pages to crawl ({self.max_pages}).")
                return False
            if normalized_url in self.visited:
                return False
            self.visited.add(normalized_url)
            return True

    async def get_html(self, url):
        if self.session is None:
            return None
        try: 
            async with self.session.get(url, headers={"User-Agent": "BootCrawler/1.0"}) as response:
                if response.status >= 400:
                    print(f"HTTP error: {response.status} {response.reason}")
                    return None

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    print(f"Non-HTML content: {content_type}")
                    return None

                return await response.text()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    async def run_task(self, url):
        task = asyncio.current_task()
        self.all_tasks.add(task)
        try:
            await self.crawl_page(url)
        finally:
            self.all_tasks.discard(task)

    async def crawl_page(self, current_url):
        if self.should_stop:
            return 
        base_domain = self.base_domain
        current_url_split = urlsplit(current_url)
        if current_url_split.netloc != base_domain:
            return

        normalized_url = normalize_url(current_url)

        is_new = await self.add_page_visit(normalized_url)
        if not is_new:
            return
        
        async with self.semaphore:
            print(f"Crawling {current_url} (Active: {self.max_concurrency - self.semaphore._value})")
            html = await self.get_html(current_url)
            if html is None:
                return

            page_info = extract_page_data(html, current_url)
            async with self.lock:
                self.page_data[normalized_url] = page_info

            links = page_info["outgoing_links"]

        tasks: list[asyncio.Task[None]] = []
        for link in links:
            tasks.append(asyncio.create_task(self.crawl_page(link)))

        if tasks:
            await asyncio.gather(*tasks)

    async def crawl(self):
        await self.crawl_page(self.base_url)
        return self.page_data

async def crawl_site_async(base_url, max_concurrency=1, max_pages=10):
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as Crawler:
        return await Crawler.crawl()