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
    "asp": True,  # Bypass LinkedIn's scraping protections
    "country": "US",
    "headers": {
        "Accept-Language": "en-US,en;q=0.5"
    }
}

def parse_job_page(response: ScrapeApiResponse) -> Dict[str, Any]:
    """
    Parse the job title and description from the LinkedIn job page response.

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

    # Extract the job description
    description_elements = selector.xpath("//div[contains(@class, 'show-more')]/ul/li/text()").getall()
    job_description = [text.strip() for text in description_elements if text.strip()]

    # Update the script_data with the job description
    script_data["jobDescription"] = job_description
    script_data.pop("description", None)  # Remove the key with the encoded HTML if it exists

    return script_data

def scrape_job_page(job_id: str) -> Dict[str, Any]:
    """
    Scrape the LinkedIn job page using the job ID and parse its content.

    Args:
        job_id (str): The LinkedIn job ID.

    Returns:
        Dict[str, Any]: A dictionary containing the job data.
    """
    # Construct the job URL using the job ID
    url = f"https://www.linkedin.com/jobs/view/{job_id}/"

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

def get_linkedin_job_info(job_id: str) -> str:
    """
    Retrieve the job title and description for a LinkedIn job.

    Args:
        job_id (str): The LinkedIn job ID.

    Returns:
        str: A string combining the job title and description.
    """
    # Scrape the job page
    job_data = scrape_job_page(job_id)

    # Extract the job title and description
    job_title = job_data.get('title', 'No job title found')
    job_description = ' '.join(job_data.get('jobDescription', []))

    # Combine the title and description with a line break
    combined_info = f"{job_title}\n{job_description}"

    return combined_info
