import os
import re
import json
from dotenv import load_dotenv
from typing import Dict
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
    "country": "US",
    "headers": {
        "Accept-Language": "en-US,en;q=0.9",
    }
}

def parse_job_page(response: ScrapeApiResponse) -> Dict[str, str]:
    """
    Parse the job title and description from the Indeed job page response.

    Args:
        response (ScrapeApiResponse): The response object from Scrapfly.

    Returns:
        Dict[str, str]: A dictionary containing 'title' and 'description' keys.
    """
    html_content = response.content
    # Use regex to find the JSON data
    data_match = re.search(r"_initialData=(\{.+?\});", html_content)
    if data_match:
        data_json = data_match.group(1)
        script_data = json.loads(data_json)
    else:
        script_data = {}

    # Extract job information
    job_info = script_data.get("jobInfoWrapperModel", {}).get("jobInfoModel", {})

    # Extract the job title
    job_title = job_info.get('jobInfoHeaderModel', {}).get('jobTitle', 'No job title found')

    # Extract and process the job description
    job_description_html = job_info.get('sanitizedJobDescription', 'No job description found')
    description_selector = Selector(text=job_description_html)
    description_text_list = description_selector.xpath("//text()").getall()
    job_description = '\n'.join([text.strip() for text in description_text_list if text.strip()])

    return {
        'title': job_title,
        'description': job_description
    }

def scrape_job_page(job_id: str) -> Dict[str, str]:
    """
    Scrape the Indeed job page using the job ID and parse its content.

    Args:
        job_id (str): The Indeed job ID.

    Returns:
        Dict[str, str]: A dictionary containing the job data.
    """
    # Construct the job URL using the job ID
    url = f"https://www.indeed.com/m/basecamp/viewjob?viewtype=embedded&jk={job_id}"

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

def get_indeed_job_info(job_id: str) -> str:
    """
    Retrieve the job title and description for an Indeed job.

    Args:
        job_id (str): The Indeed job ID.

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
