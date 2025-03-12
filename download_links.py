# /// script
# dependencies = [
#   "requests<3",
#   "beautifulsoup4",
#   "click",
#   "llm",
#   "html2text",
# ]
# ///

import os
import requests
import click
import llm
import html2text
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

def download_files(url, base_download_folder, file_types):
    # Fetch webpage content
    response = requests.get(url)
    response.raise_for_status()
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract page title and sanitize it for folder name
    page_title = soup.title.string if soup.title else "untitled"  # Fallback to "untitled" if no title
    page_title = re.sub(r'[<>:"/\\|?*]', '', page_title).strip()
    if not page_title:  # Ensure non-empty folder name
        page_title = "untitled"
    
    # Create subfolder with page title inside base_download_folder
    download_folder = os.path.join(base_download_folder, page_title)
    os.makedirs(download_folder, exist_ok=True)
    
    # Download linked files of specified types
    downloaded_files = []
    for link in soup.find_all('a', href=True):
        file_url = urljoin(url, link['href'])
        if any(file_url.endswith(ext) for ext in file_types):
            filename = os.path.join(download_folder, os.path.basename(file_url))
            print(f"Downloading: {file_url}")
            file_response = requests.get(file_url)
            file_response.raise_for_status()
            with open(filename, "wb") as file:
                file.write(file_response.content)
            print(f"Saved: {filename}")
            downloaded_files.append(filename)
    
    # Convert HTML to Markdown using html2text
    h = html2text.HTML2Text()
    h.ignore_links = False  # Include links in Markdown
    h.ignore_images = True  # Skip images for cleaner output
    page_text = h.handle(str(soup))
    
    return downloaded_files, page_text, download_folder

def generate_summary(page_text, download_folder):
    """Generate a summary of the webpage using an LLM and save it in the subfolder."""
    prompt = f"Briefly summarize the following webpage content (in Markdown), keep it to a couple of sentence that is easy to read, no tables etc:\n\n{page_text[:5000]}"
    summary = llm.get_model("gpt-4o-mini").prompt(prompt)
    summary_path = os.path.join(download_folder, "summary.txt")
    with open(summary_path, "w") as summary_file:
        summary_file.write(summary.text())
    print("\nSummary saved to:", summary_path)

@click.command()
@click.argument("url")
@click.option("--download-folder", default="downloads", help="Base folder to save subfolders")
@click.option("--file-types", default="csv", help="Comma-separated list of file extensions (e.g., csv,png,txt)")
@click.option("--summarize", is_flag=True, help="Generate a summary of the webpage")
def cli(url, download_folder, file_types, summarize):
    """Download files from a webpage into a subfolder named after the page title and optionally summarize it."""
    file_types = [f".{ext.strip()}" for ext in file_types.split(",")]
    downloaded_files, page_text, subfolder = download_files(url, download_folder, file_types)
    with open(os.path.join(subfolder, "url.txt"), "w") as f:
        f.write(url)
    if summarize:
        generate_summary(page_text, subfolder)

if __name__ == "__main__":
    cli()

