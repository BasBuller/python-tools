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

def download_files(url, download_folder, file_types):
    os.makedirs(download_folder, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
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
    
    return downloaded_files, page_text

def generate_summary(page_text, download_folder):
    """Generate a summary of the webpage using an LLM and save it."""
    prompt = f"Briefly summarize the following webpage content (in Markdown), don't write tables and such, just a few sentences summary that's easy to read:\n\n{page_text[:5000]}"
    summary = llm.get_model("gpt-4o-mini").prompt(prompt)
    
    summary_path = os.path.join(download_folder, "summary.txt")
    with open(summary_path, "w") as summary_file:
        summary_file.write(summary.text())
    
    print("\nSummary saved to:", summary_path)

@click.command()
@click.argument("url")
@click.option("--download-folder", default="downloads", help="Folder to save files")
@click.option("--file-types", default="csv", help="Comma-separated list of file extensions (e.g., csv,png,txt)")
@click.option("--summarize", is_flag=True, help="Generate a summary of the webpage")
def cli(url, download_folder, file_types, summarize):
    """Download files from a webpage and optionally summarize it."""
    file_types = [f".{ext.strip()}" for ext in file_types.split(",")]
    downloaded_files, page_text = download_files(url, download_folder, file_types)
    if summarize:
        generate_summary(page_text, download_folder)

if __name__ == "__main__":
    cli()
