import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .base import ArtefactBase, ArtefactStatus

class Webpage(ArtefactBase):

    def __init__(self, platform_config: dict, artefact_config: dict):
        super().__init__(platform_config, artefact_config)
    
    @classmethod
    def get_type(cls):
        return 'webpage'

    def _setup(self):
        pass

    def _get_request(self):
        source_url = self._artefact_config['src']['url']
        selector = self._artefact_config['src']['selector']
        attribute = self._artefact_config['src']['attribute']
        version_regex = re.compile(self._artefact_config['src']['version_regex'])

        try:
            response = requests.get(source_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            selected_element = soup.select_one(selector)

            if selected_element:
                relative_url = selected_element.get(attribute)
                absolute_url = urljoin(source_url, relative_url)

                version_match = re.search(version_regex, absolute_url)

                if version_match:
                    version = version_match.group(1)
                else:
                    version = None
                
                self._download_url = absolute_url
                self._version = version
        except:
            raise ValueError("Issue getting data")
        
        self._status = ArtefactStatus.READY_TO_DOWNLOAD