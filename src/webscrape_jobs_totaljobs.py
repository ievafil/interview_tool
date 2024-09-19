import os
import json
from dotenv import load_dotenv
from typing import Dict, Any
from parsel import Selector
from scrapfly import ScrapeConfig, ScrapflyClient, ScrapeApiResponse

# Load environment variables from .env file
load_dotenv()
scrapfly_api_key = os.getenv("SCRAPFLY_API_KEY")

if not scrapfly_api_key:
    raise ValueError("SCRAPFLY_API_KEY is not set in the environment.")

# Initialize the Scrapfly client with your API key
client = ScrapflyClient(key=scrapfly_api_key)

# Base configuration for Scrapfly
BASE_CONFIG = {
    "country": "GB",  # Set the proxy country to GB (United Kingdom)
    "headers": {
        "Accept-Language": "en-GB,en;q=0.5"
    }
}

def parse_job_page(response: ScrapeApiResponse) -> Dict[str, Any]:
    """
    Parse the job title and description from the Totaljobs job page response.

    Args:
        response (ScrapeApiResponse): The response object from Scrapfly.

    Returns:
        Dict[str, Any]: A dictionary containing job data.
    """
    html_content = response.content
    selector = Selector(html_content)

    # Extract structured data from the script tag
    data_json = selector.xpath("//script[@type='application/ld+json']/text()").get()
    if data_json:
        script_data = json.loads(data_json)
    else:
        script_data = {}

    # Extract the job title directly from the page if not in script_data
    if not script_data.get('title'):
        job_title = selector.xpath("//h1/text()").get()
        script_data['title'] = job_title.strip() if job_title else 'No job title found'

    # Process the description field if it exists
    if script_data.get('description'):
        job_description_html = script_data['description']
        description_selector = Selector(text=job_description_html)
        description_text_list = description_selector.xpath("//text()").getall()
        # Join the text content
        job_description = ' '.join([text.strip() for text in description_text_list if text.strip()])
        # Update script_data with processed description
        script_data['description'] = job_description
    else:
        # Extract the job description from the page if not in script_data
        description_elements = selector.xpath("//div[contains(@class, 'job-description')]//text()").getall()
        job_description = ' '.join([text.strip() for text in description_elements if text.strip()])
        script_data['description'] = job_description

    return script_data

def scrape_job_page(job_id: str) -> Dict[str, Any]:
    """
    Scrape the Totaljobs job page using the job ID and parse its content.

    Args:
        job_id (str): The Totaljobs job ID.

    Returns:
        Dict[str, Any]: A dictionary containing the job data.
    """
    # Construct the job URL using the job ID
    url = f"https://www.totaljobs.com/job/{job_id}/"

    # Create the scrape configuration
    scrape_config = ScrapeConfig(
        url=url,
        **BASE_CONFIG
    )

    # Perform the scrape
    response = client.scrape(scrape_config)

    # Parse the job page
    job_data = parse_job_page(response)

    return job_data

def get_totaljobs_job_info(job_id: str) -> str:
    """
    Retrieve the job title and description for a Totaljobs job.

    Args:
        job_id (str): The Totaljobs job ID.

    Returns:
        str: A string combining the job title and description.
    """
    # Scrape the job page
    job_data = scrape_job_page(job_id)

    # Extract the job title and description
    job_title = job_data.get('title', 'No job title found')
    job_description = job_data.get('description', 'No description found')

    # Combine the title and description with a line break
    combined_info = f"{job_title}\n{job_description}"

    return combined_info
