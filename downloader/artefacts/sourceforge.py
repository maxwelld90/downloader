import re
import ssl
import feedparser
import requests
from bs4 import BeautifulSoup
from .base import ArtefactBase, ArtefactStatus

class SourceForge(ArtefactBase):

    def __init__(self, platform_config: dict, artefact_config: dict):
        super().__init__(platform_config, artefact_config)
    
    @classmethod
    def get_type(cls):
        return 'sourceforge'

    def _setup(self):
        # Setup required variables for determining the latest version
        self.__version_url = f"https://sourceforge.net/projects/{self._artefact_config['src']['project']}/files/{self._artefact_config['src']['folder']}/"
        self.__version_selector = self._artefact_config['src']['version_finder']['selector']
        self.__version_regex = re.compile(self._artefact_config['src']['version_finder']['regex'])

        if hasattr(ssl, '_create_unverified_context'):
            ssl._create_default_https_context = ssl._create_unverified_context

    def _get_request(self):
        self._version = self._artefact_config['src']['version']
        
        if self._artefact_config['src']['version'] == '' or self._artefact_config['src']['version'].lower() == 'latest':
            self.__get_latest_version_number()
        
        self.__get_download_url()

        if self._download_url is None:
            raise ValueError("No URL!")

        self._status = ArtefactStatus.READY_TO_DOWNLOAD
    
    def __get_latest_version_number(self):
        response = requests.get(self.__version_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        selected_element = soup.select_one(self.__version_selector)

        if selected_element:
            version_match = re.search(self.__version_regex, selected_element.text)

            if version_match:
                self._version = version_match.group(1)
                return
        
        # What to do here?
        print("Version not found.")
        self._version = None
    
    def __generate_filename_pattern(self):
        regex_str = self._artefact_config['src']['filename_regex'].replace('{version}', self._version)
        regex_str = f'.*{regex_str}/download'

        return re.compile(regex_str)
    
    def __get_download_url(self):
        rss_url = f"https://sourceforge.net/projects/{self._artefact_config['src']['project']}/rss?path=/{self._artefact_config['src']['folder']}"
        feed = feedparser.parse(rss_url)

        pattern = self.__generate_filename_pattern()

        for item in feed.entries:
            link = item.link

            if re.match(pattern, link):                
                if link.endswith('/download'):
                    link = link.rstrip('/download')

                self._download_url = link
                return
        
        # What to do here?
        print('No link found!')