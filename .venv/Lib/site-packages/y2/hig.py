import pathlib
import tempfile
import queue
import threading
import time
from urllib import parse

import bs4
import cyclopts
from selenium import webdriver
from selenium.webdriver.common import by

from y2._console import console


_ROOT_URL = "https://developer.apple.com/design/human-interface-guidelines"


app = cyclopts.App(
    name="hig",
    help="Download and extract information from Apple's Human Interface Guidelines for the Daily HIG bot.",
)


@app.command()
def download(
    to: pathlib.Path | None = None,
    num_threads: int = 8,
    website_loading_wait_seconds: float = 5.0,
):
    """Download Apple's HIG to a directory."""
    if to is None:
        to = pathlib.Path(tempfile.mkdtemp(prefix="y2.hig."))
    else:
        if to.exists():
            console.fatal(f"Directory {to} already exists")
        to.mkdir(parents=True)

    console.print("Downloading Apple's HIG to", to)

    cralwer = _Crawler(
        console=console,
        seed_url=_ROOT_URL,
        output_directory=to,
        website_loading_wait_seconds=website_loading_wait_seconds,
    )
    cralwer.start_crawl(num_threads)

    console.print("Finished downloading Apple's HIG to", to)


@app.command()
def extract(hig_directory: pathlib.Path):
    """Extract information from downloaded Apple's HIG."""
    urls_to_lines: dict[str, str] = {}
    for root, _, filenames in hig_directory.walk():
        for filename in filenames:
            if not filename.endswith(".html"):
                continue
            path = root / filename
            url = _to_url(path, hig_directory)
            if url == _ROOT_URL:
                # Root.
                continue
            soup = bs4.BeautifulSoup(path.read_text(), "html.parser")
            description = ""
            title = ""
            for meta in soup.find_all("meta"):
                if meta.get("property") == "og:description":
                    description = meta.get("content")
                    break
            if not description:
                continue
            for title in soup.find_all("title"):
                title = title.text
                break
            title = title.replace(
                "Apple Developer Documentation", "Human Interface Guidelines"
            )

            primary_elements = soup.find_all("div", {"class": "primary-content"})
            if len(primary_elements) != 1:
                console.print(
                    f"WARNING: Found {len(primary_elements)} primary-content on {path}, ignoring"
                )
                continue
            content_root = primary_elements[0]
            first_image = content_root.find_all("img")[0]["src"]

            urls_to_lines[url] = (
                f'{{Title: "{title}", URL: "{url}", Description: "{description}", HeaderImageURL: "{first_image}"}},'
            )
    for _, line in sorted(urls_to_lines.items()):
        print(line)


def _to_url(filepath: pathlib.Path, hig_directory: pathlib.Path) -> str:
    return "https://developer.apple.com" + str(filepath)[len(str(hig_directory)) : -5]


class _Crawler:
    def __init__(
        self,
        *,
        seed_url: str,
        output_directory: pathlib.Path,
        website_loading_wait_seconds: float,
    ) -> None:
        self._output_directory = output_directory
        self._website_loading_wait_seconds = website_loading_wait_seconds

        self._queue = queue.Queue()
        self._queue.put(seed_url)
        self._visited: set[str] = set()
        self._visited.add(seed_url)
        self._lock = threading.RLock()

    def start_crawl(self, num_threads: int) -> None:
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=self._crawl_thread)
            thread.start()
            threads.append(thread)
        self._queue.join()
        self._queue.shutdown()
        for t in threads:
            t.join()

    def _crawl_thread(self) -> None:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

        while True:
            try:
                url = self._queue.get()
            except queue.ShutDown:
                console.print("Closing driver and shutting down thread.")
                driver.close()
                return
            try:
                self._download(driver, url)
            finally:
                self._queue.task_done()

    def _download(self, driver: webdriver.Chrome, url: str) -> None:
        console.print("Downloading", url)
        driver.get(url)
        time.sleep(self._website_loading_wait_seconds)
        current_url = driver.current_url
        parsed = parse.urlparse(current_url)
        output_file = self._output_directory / (parsed.path[1:] + ".html")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(driver.page_source)

        for link in driver.find_elements(by.By.TAG_NAME, "a"):
            if (href := link.get_attribute("href")) is None:
                continue

            # Get the full URL from href. Can be full URL, absolute path, relative path.
            new_url = parse.urljoin(current_url, href)

            # Remove fragments (#)
            new_parsed = parse.urlparse(new_url)
            new_url = new_parsed._replace(fragment="").geturl()
            if not new_url.startswith(_ROOT_URL):
                continue

            with self._lock:
                if new_url not in self._visited:
                    console.print("Queuing link:", new_url)
                    self._queue.put(new_url)
                    self._visited.add(new_url)
