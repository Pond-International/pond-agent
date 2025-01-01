"""Competition scraper agent for fetching competition information from Pond's website"""

import logging
import os
import re
from typing import Dict, Optional, Tuple
import aiohttp
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Page
import zipfile
import shutil
from pathlib import Path

from .base import BaseAgent

logger = logging.getLogger(__name__)


class CompetitionScraper(BaseAgent):
    """Agent for scraping competition information from Pond's website."""

    def __init__(self, output_dir: str) -> None:
        """Initialize the scraper."""
        super().__init__()
        self.output_dir = Path(output_dir).resolve()
        self.dataset_dir = self.output_dir / "dataset"
        self.playwright = None
        self.browser = None
        os.makedirs(self.dataset_dir, exist_ok=True)

    async def __aenter__(self):
        p = await async_playwright().start()
        self.playwright = p
        self.browser = await p.chromium.launch()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def _convert_sheets_url_to_export(self, url: str) -> str:
        """Convert Google Sheets URL to export URL for XLSX format."""
        # Extract the document ID from the URL
        match = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
        if not match:
            logger.warning("Could not parse Google Sheets URL")
            return url

        doc_id = match.group(1)
        # Use the direct download URL format
        export_url = f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=xlsx&id={doc_id}"
        logger.debug(f"Converted sheets URL to export URL: {export_url}")
        return export_url

    async def _download_file(self, url: str, output_path: str) -> bool:
        """Download a file from URL to the specified path."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(output_path, "wb") as f:
                            f.write(content)
                        logger.debug(f"Downloaded file to: {output_path}")
                        return True
                    else:
                        logger.warning(f"Failed to download file: {response.status}")
                        return False
        except Exception as e:
            logger.warning(f"Error downloading file: {e}")
            return False

    async def _init_browser(self):
        """Initialize Playwright browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch()

    async def _close_browser(self):
        """Close Playwright browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _get_page_content(self, url):
        """Get rendered page content using Playwright"""
        page = await self.browser.new_page()

        # Set viewport size
        await page.set_viewport_size({"width": 1920, "height": 1080})

        # Navigate to page
        await page.goto(url, wait_until="networkidle")

        # Wait for key elements with longer timeout
        try:
            # Wait for either the competitions page or any main content
            await page.wait_for_selector(
                'div[class*="competitions-page"], div[class*="main-content"]',
                timeout=20000,
            )

            # Additional wait to ensure dynamic content loads
            await page.wait_for_load_state("networkidle")

            # Small delay to ensure React renders
            await page.wait_for_timeout(2000)

        except Exception as e:
            logger.error(f"Timeout waiting for content: {e}")

        content = await page.content()
        logger.debug("Page HTML length: %d", len(content))

        # Save HTML for debugging
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(content)

        # Take screenshot for debugging
        await page.screenshot(path="debug_screenshot.png")

        await page.close()
        return content

    async def _download_and_extract_dataset(self, url: str, filename: str) -> bool:
        """Download dataset zip file and extract its contents."""
        try:
            # Clear dataset directory
            if os.path.exists(self.dataset_dir):
                shutil.rmtree(self.dataset_dir)
            os.makedirs(self.dataset_dir)

            # Download zip file
            zip_path = self.output_dir / filename
            if not await self._download_file(url, zip_path):
                return False

            logger.info(f"Downloaded dataset to: {zip_path}")

            # Extract zip file
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # First, extract to a temporary extraction directory
                extract_dir = self.output_dir / "extract"
                if os.path.exists(extract_dir):
                    shutil.rmtree(extract_dir)
                os.makedirs(extract_dir)

                zip_ref.extractall(extract_dir)
                logger.info(f"Extracted dataset to: {extract_dir}")

                # Find all parquet files
                parquet_files = []
                for root, _, files in os.walk(extract_dir):
                    for file in files:
                        if file.endswith(".parquet"):
                            parquet_files.append((root, file))

                # Process each parquet file
                processed_dirs = set()
                for root, file in parquet_files:
                    # Skip hidden files (starting with a dot)
                    if file.startswith('.'):
                        continue
                        
                    # Skip if we've already processed this directory
                    if root in processed_dirs:
                        continue
                    
                    # Check if this is a partitioned parquet file
                    is_partitioned = bool(re.search(r'_\d+_\d+_\d+\.snappy\.parquet$', file))
                    
                    if is_partitioned:
                        # Move the entire directory containing partitioned files
                        dir_name = os.path.basename(root)
                        dst_dir = os.path.join(self.dataset_dir, dir_name)
                        if os.path.exists(dst_dir):
                            shutil.rmtree(dst_dir)
                        shutil.move(root, dst_dir)
                        logger.info(f"Moved partitioned parquet directory: {dir_name}")
                        processed_dirs.add(root)
                    else:
                        # Move individual parquet file
                        src = os.path.join(root, file)
                        dst = os.path.join(self.dataset_dir, file)
                        shutil.move(src, dst)
                        logger.info(f"Moved individual parquet file: {file}")

                # Clean up
                shutil.rmtree(extract_dir)
                os.remove(zip_path)

            return True

        except Exception as e:
            logger.error(f"Error processing dataset: {e}")
            return False

    async def scrape(self, url: str) -> Dict[str, str]:
        """
        Scrape the competition page.

        Args:
            url: URL of the competition page

        Returns:
            Dict with keys:
            - overview: Path to overview markdown file
            - data_dictionary: Path to data dictionary file
            - datasets: Dict of dataset name to download URL
            - dataset_dir: Path to dataset directory
        """
        async with self:
            # Launch browser
            page = await self.browser.new_page()

            # Go to URL
            await page.goto(url)

            # Wait for content to load
            await page.wait_for_selector("div.block-note-edit-container-model")

            # Get page content
            content = await page.content()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            logger.debug("Page HTML length: %d", len(content))

            # Extract data from rendered content
            logger.info("Extracting overview...")
            overview = await self._extract_overview(soup)
            logger.info("Overview length: %d", len(overview) if overview else 0)

            # Write overview to file
            overview_file = None
            if overview:
                overview_file = self.output_dir / "overview.md"
                with open(overview_file, "w") as f:
                    f.write(overview)
                logger.info(f"Saved overview to: {overview_file}")
            else:
                logger.error("Failed to extract overview")
                

            # Extract datasets
            logger.info("Extracting datasets...")
            data_dict_url, dataset_urls = await self._extract_datasets(page)
            logger.info("Data dictionary URL: %s", data_dict_url)
            logger.info("Dataset URLs: %s", dataset_urls)

            # Write data dictionary to file if exists
            data_dict_file = None
            if data_dict_url:
                # Convert Google Sheets URL to export URL
                export_url = self._convert_sheets_url_to_export(data_dict_url)

                # Download as XLSX
                data_dict_file = self.output_dir / "data_dictionary.xlsx"
                if await self._download_file(export_url, data_dict_file):
                    logger.info(f"Downloaded data dictionary to: {data_dict_file}")
                else:
                    logger.error("Failed to download data dictionary")
                    data_dict_file = None

            # Download and extract dataset
            dataset_files = None
            if dataset_urls:
                dataset_files = self.dataset_dir
                for filename, url in dataset_urls.items():
                    if await self._download_and_extract_dataset(url, filename):
                        logger.info(f"Successfully processed dataset: {filename}")
                    else:
                        logger.error(f"Failed to process dataset: {filename}")
                        dataset_files = None

            return {
                "overview": overview_file,
                "data_dictionary": data_dict_file,
                "dataset_dir": dataset_files,
            }

    async def _extract_overview(self, soup: BeautifulSoup) -> str:
        """Extract overview content from the page."""
        overview_sections = []

        # Extract title and tagline
        title_div = soup.find("div", {"class": "css-1hruafo"})
        if title_div:
            title = title_div.find("p", {"class": "css-zypwzg"})
            tagline = title_div.find("p", {"class": "css-1b41181"})
            if title:
                overview_sections.append(f"# {title.get_text(strip=True)}")
            if tagline:
                overview_sections.append(f"_{tagline.get_text(strip=True)}_")

        # Try to find the content in the React component
        content_container = soup.find(
            "div", {"class": "block-note-edit-container-model"}
        )
        if not content_container:
            logger.warning("Could not find content container")
            return ""

        # Log the structure
        logger.debug("Content container found")

        # Extract all text blocks
        text_blocks = content_container.find_all("div", {"class": "bn-block-content"})
        logger.debug(f"Found {len(text_blocks)} text blocks")

        # Debug: Print all text blocks and their types
        for i, block in enumerate(text_blocks):
            content_type = block.get("data-content-type", "unknown")
            inline = block.find("p", {"class": "bn-inline-content"})
            if inline:
                msg = f"Block {i} ({content_type}): {inline.get_text(strip=True)[:100]}"
                logger.debug(msg)
            else:
                logger.debug(f"Block {i} ({content_type}): No inline content")

            # Debug: Print all text nodes in this block
            for text_node in block.stripped_strings:
                logger.debug(f"  Text node: {text_node[:100]}...")

            # Debug: Print block HTML
            logger.debug(f"  HTML: {block}")

        # Find section headers
        section_headers = soup.find_all("p", {"class": "chakra-text css-ugr7x1"})
        logger.debug(f"Found {len(section_headers)} section headers")

        # Process sections
        for i, header in enumerate(section_headers):
            title = header.get_text(strip=True)
            logger.debug(f"Found section: {title}")

            # Get section content
            section_content = []

            # Get all content until next section header
            current = header.find_parent("div")
            while current:
                # Stop if we find the next section header
                if (
                    i < len(section_headers) - 1
                    and current.find("p", {"class": "chakra-text css-ugr7x1"})
                    == section_headers[i + 1]
                ):
                    break

                # Look for content blocks
                blocks = current.find_all("div", {"class": "bn-block-content"})
                for block in blocks:
                    content_type = block.get("data-content-type", "")
                    inline = block.find("p", {"class": "bn-inline-content"})
                    if inline:
                        # Get text with proper link formatting
                        text = ""
                        for element in inline.children:
                            if element.name == "a":
                                href = element.get("href", "")
                                link_text = element.get_text(strip=True)
                                text += f" [{link_text}]({href}) "
                            elif element.name == "br":
                                continue
                            elif element.name == "strong":
                                text += f" **{element.get_text(strip=True)}** "
                            else:
                                text += element.get_text(strip=True)

                        # Skip empty text
                        if not text or text == "...":
                            continue

                        # Format bullet list items as markdown list items
                        if content_type == "bulletListItem":
                            text = "- " + text

                        # Format table names with backticks and handle bold formatting
                        text = re.sub(
                            r"the\s*\*\*(\w+)\*\*\s*table", r"the `\1` table", text
                        )
                        text = re.sub(r"the\s*(\w+)\s*table", r"the `\1` table", text)

                        section_content.append(text)

                # Move to next sibling or parent's next sibling
                next_sibling = current.find_next_sibling()
                if next_sibling:
                    current = next_sibling
                else:
                    parent = current.find_parent()
                    if parent:
                        current = parent.find_next_sibling()
                    else:
                        current = None

            if section_content:
                overview_sections.append(
                    f"## {title}\n\n" + "\n\n".join(section_content)
                )
                logger.debug(f"Added {title} section")

        result = "\n\n".join(filter(None, overview_sections))
        logger.debug(f"Total sections: {len(overview_sections)}")
        return result

    async def _extract_datasets(
        self, page: Page
    ) -> Tuple[Optional[str], Dict[str, str]]:
        """Extract dataset URLs from the page."""
        logger.info("Clicking Datasets tab...")

        # Click the Datasets tab and wait for content
        await page.click('button:has-text("Datasets")')

        try:
            # Wait for table to appear
            await page.wait_for_selector("table", timeout=10000)
            # Additional wait for content to load
            await page.wait_for_timeout(2000)
        except Exception as e:
            logger.warning(f"Timeout waiting for table: {e}")
            return None, {}

        # Initialize return values
        logger.info("Getting data dictionary and dataset URLs...")
        dictionary_url = None
        dataset_urls = {}

        try:
            # Look for the table containing datasets
            tables = page.locator("table")
            count = await tables.count()
            logger.debug(f"Found {count} tables")

            for i in range(count):
                table = tables.nth(i)
                header = await table.locator("thead").text_content()
                logger.debug(f"Table {i} header: {header}")

                # Wait for rows to be visible
                await table.locator("tbody tr").first.wait_for(timeout=5000)

                if "File" in header and "Size" in header and "Action" in header:
                    rows = table.locator("tbody tr")
                    count = await rows.count()
                    logger.debug(f"Found {count} rows in table")

                    # First pass: find all zip files
                    zip_files = []
                    for i in range(count):
                        row = rows.nth(i)
                        cells = row.locator("td")
                        cell_count = await cells.count()
                        if cell_count >= 4:
                            filename = await cells.nth(0).text_content()
                            filename = filename.strip()
                            if filename.endswith(".zip"):
                                zip_files.append((i, filename))
                    
                    # Determine which zip file to download
                    target_row = None
                    if len(zip_files) == 1:
                        # If only one zip file, use that
                        target_row = zip_files[0][0]
                        logger.info(f"Found single zip file: {zip_files[0][1]}")
                    elif len(zip_files) == 2:
                        # If two zip files, use the one with _subset.zip
                        for row_idx, filename in zip_files:
                            if filename.endswith("_subset.zip"):
                                target_row = row_idx
                                logger.info(f"Found subset zip file: {filename}")
                                break
                    else:
                        logger.warning(f"Unexpected number of zip files: {len(zip_files)}")
                        return None, {}

                    if target_row is None:
                        logger.warning("Could not find appropriate zip file to download")
                        return None, {}

                    # Process the target row
                    row = rows.nth(target_row)
                    cells = row.locator("td")
                    filename = await cells.nth(0).text_content()
                    filename = filename.strip()
                    
                    # Get download URL for the zip file
                    download_cell = cells.nth(2)
                    download_button = download_cell.locator('div[role="group"]')
                    if await download_button.count() > 0:
                        button_text = await download_button.text_content()
                        if "Download" in button_text:
                            try:
                                async with page.expect_download(timeout=5000) as download_info:
                                    await download_button.click()
                                download = await download_info.value
                                dataset_urls[filename] = download.url
                                await download.cancel()
                            except Exception as e:
                                logger.warning(f"Error getting download URL: {e}")

                    # Get data dictionary URL from the same row
                    dict_cell = cells.nth(3)
                    dict_button = dict_cell.locator('div[role="group"]')
                    if await dict_button.count() > 0:
                        button_text = await dict_button.text_content()
                        logger.debug(f"Dictionary button text: {button_text}")
                        if "View Dictionary" in button_text:
                            try:
                                async with page.expect_popup() as popup_info:
                                    await dict_button.click()
                                popup = await popup_info.value
                                dictionary_url = popup.url
                                await popup.close()
                            except Exception as e:
                                logger.warning(f"Error getting dictionary URL: {e}")
                    break
        except Exception as e:
            logger.warning(f"Error getting dataset URLs: {e}")

        logger.debug(f"Data dictionary URL: {dictionary_url}")
        logger.debug(f"Dataset URLs: {dataset_urls}")
        return dictionary_url, dataset_urls
