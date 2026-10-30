import unittest
from crawl import normalize_url, get_heading_from_html, get_first_paragraph_from_html, get_urls_from_html, get_images_from_html, extract_page_data


class TestCrawl(unittest.TestCase):
    def test_normalize_url(self):
        input_url = "https://www.boot.dev/blog/path"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_slash(self) -> None:
        input_url = "https://crawler-test.com/path/"
        actual = normalize_url(input_url)
        expected = "crawler-test.com/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_capitals(self) -> None:
        input_url = "https://CRAWLER-TEST.com/path"
        actual = normalize_url(input_url)
        expected = "crawler-test.com/path"
        self.assertEqual(actual, expected)

    def test_normalize_url_http(self) -> None:
        input_url = "http://CRAWLER-TEST.com/path"
        actual = normalize_url(input_url)
        expected = "crawler-test.com/path"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_basic(self) -> None:
        input_body = "<html><body><h1>Test Title</h1></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "Test Title"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_h2_fallback(self) -> None:
        input_body = "<html><body><h2>Fallback Title</h2></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "Fallback Title"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_with_whitespace(self) -> None:
        input_body = "<html><body><h1>   Whitespace Title   </h1></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "Whitespace Title"
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_basic(self) -> None:
        input_body = "<html><body><p>This is the first paragraph.</p></body></html>"
        actual = get_first_paragraph_from_html(input_body)
        expected = "This is the first paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_main_priority(self) -> None:
        input_body = """<html><body>
            <p>Outside paragraph.</p>
            <main>
                <p>Main paragraph.</p>
            </main>
        </body></html>"""
        actual = get_first_paragraph_from_html(input_body)
        expected = "Main paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_no_paragraph(self) -> None:
        input_body = "<html><body><h1>No paragraphs here</h1></body></html>"
        actual = get_first_paragraph_from_html(input_body)
        expected = ""
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_absolute(self) -> None:
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="https://crawler-test.com"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_relative(self) -> None:
        input_url = "https://crawler-test.com"
        input_body = (
            '<html><body><a href="/path/one"><span>Boot.dev</span></a></body></html>'
        )
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/path/one"]
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_both(self) -> None:
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="/path/one"><span>Boot.dev</span></a><a href="https://other.com/path/one"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/path/one", "https://other.com/path/one"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_absolute(self) -> None:
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="https://crawler-test.com/logo.png" alt="Logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/logo.png"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_relative(self) -> None:
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="/logo.png" alt="Logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/logo.png"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_multiple(self) -> None:
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="/logo.png" alt="Logo"><img src="https://cdn.boot.dev/banner.jpg"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = [
            "https://crawler-test.com/logo.png",
            "https://cdn.boot.dev/banner.jpg",
        ]
        self.assertEqual(actual, expected)

    def test_extract_page_data_basic(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_empty_html(self):
        actual = extract_page_data("<html><body></body></html>", "https://crawler-test.com")
        expected = {
            "url": "https://crawler-test.com",
            "heading": "",
            "first_paragraph": "",
            "outgoing_links": [],
            "image_urls": [],
        }
        self.assertEqual(actual, expected)

    def test_extract_page_data_h2_fallback(self):
        input_body = "<html><body><h2>Sub Title</h2><p>Text.</p></body></html>"
        actual = extract_page_data(input_body, "https://crawler-test.com")
        self.assertEqual(actual["heading"], "Sub Title")

    def test_extract_page_data_h1_preferred_over_h2(self):
        input_body = "<html><body><h2>Second</h2><h1>First</h1></body></html>"
        actual = extract_page_data(input_body, "https://crawler-test.com")
        self.assertEqual(actual["heading"], "First")

    def test_extract_page_data_main_paragraph_preferred(self):
        input_body = """<html><body>
            <p>Outside paragraph.</p>
            <main><p>Main paragraph.</p></main>
        </body></html>"""
        actual = extract_page_data(input_body, "https://crawler-test.com")
        self.assertEqual(actual["first_paragraph"], "Main paragraph.")

    def test_extract_page_data_strips_whitespace(self):
        input_body = "<html><body><h1>  Spaced Title \n</h1><p>\n  Spaced text.  </p></body></html>"
        actual = extract_page_data(input_body, "https://crawler-test.com")
        self.assertEqual(actual["heading"], "Spaced Title")
        self.assertEqual(actual["first_paragraph"], "Spaced text.")

    def test_extract_page_data_multiple_links_and_images(self):
        input_body = """<html><body>
            <a href="/one">One</a>
            <a href="https://other.com/two">Two</a>
            <a href="three">Three</a>
            <img src="/a.png">
            <img src="https://cdn.example.com/b.png">
        </body></html>"""
        actual = extract_page_data(input_body, "https://crawler-test.com")
        self.assertEqual(
            actual["outgoing_links"],
            [
                "https://crawler-test.com/one",
                "https://other.com/two",
                "https://crawler-test.com/three",
            ],
        )
        self.assertEqual(
            actual["image_urls"],
            ["https://crawler-test.com/a.png", "https://cdn.example.com/b.png"],
        )

    def test_extract_page_data_skips_missing_or_empty_attributes(self):
        input_body = """<html><body>
            <a name="top">No href</a>
            <a href="">Empty href</a>
            <a href="/ok">OK</a>
            <img alt="no src">
            <img src="">
        </body></html>"""
        actual = extract_page_data(input_body, "https://crawler-test.com")
        self.assertEqual(actual["outgoing_links"], ["https://crawler-test.com/ok"])
        self.assertEqual(actual["image_urls"], [])

    def test_extract_page_data_relative_to_page_path(self):
        input_body = '<html><body><a href="other">Other</a><img src="pic.png"></body></html>'
        actual = extract_page_data(input_body, "https://crawler-test.com/blog/post")
        self.assertEqual(actual["url"], "https://crawler-test.com/blog/post")
        self.assertEqual(actual["outgoing_links"], ["https://crawler-test.com/blog/other"])
        self.assertEqual(actual["image_urls"], ["https://crawler-test.com/blog/pic.png"])

if __name__ == "__main__":
    unittest.main()