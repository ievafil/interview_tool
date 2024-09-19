import re
from urllib.parse import urlparse, parse_qs
from webscrape_jobs_indeed import get_indeed_job_info
from webscrape_jobs_linkedin import get_linkedin_job_info
from webscrape_jobs_totaljobs import get_totaljobs_job_info

def detect_link(job_description: str):
    """Pass description and find corresponding links to job sites."""
    # Extract URLs from job_description
    url_pattern = r'(https?://[^\s]+)'
    urls = re.findall(url_pattern, job_description)

    for url in urls:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        path = parsed_url.path
        query = parsed_url.query

        if 'indeed.com' in domain and '/m/basecamp/viewjob' in path:
            params = parse_qs(query)
            job_key_list = params.get('jk')
            if job_key_list:
                job_key = job_key_list[0]
                try:
                    job_description = get_indeed_job_info(job_key)
                    break
                except Exception as e:
                    print(f"Error fetching Indeed job info: {e}")
        elif 'linkedin.com' in domain and '/jobs/' in path:
            params = parse_qs(query)
            job_id_list = params.get('currentJobId')
            if job_id_list:
                job_id = job_id_list[0]
                try:
                    job_description = get_linkedin_job_info(job_id)
                    break
                except Exception as e:
                    print(f"Error fetching LinkedIn job info: {e}")
        elif 'totaljobs.com' in domain and path.startswith('/job/'):
            job_id = path.split('/job/')[1].split('/')[0]
            try:
                job_description = get_totaljobs_job_info(job_id)
                break
            except Exception as e:
                print(f"Error fetching TotalJobs job info: {e}")

    return job_description
