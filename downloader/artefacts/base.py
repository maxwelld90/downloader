import os
import sys
import tqdm
import hashlib
import requests
from enum import Enum
from abc import ABC, abstractmethod
from ..utils import pad_string, does_archiver_exist, run_archiver

class ArtefactStatus(Enum):
    INITIALISED = 1
    READY_TO_DOWNLOAD = 2
    HTTP_OR_URL_ERROR = 3
    DOWNLOADED = 4

SKIP_ARCHIVE_CHECKS = ['.exe']

def requires_url_or_version(func):
    def wrapper(self, *args, **kwargs):
        if self._status in [ArtefactStatus.INITIALISED,
                            ArtefactStatus.HTTP_OR_URL_ERROR]:
            raise ValueError("Artefact object is not ready yet to be queried.")

        return func(self, *args, **kwargs)
    return wrapper

def requires_download(func):
    def wrapper(self, *args, **kwargs):
        if self._status != ArtefactStatus.DOWNLOADED:
            raise ValueError("Artefact object must be downloaded first.")

        return func(self, *args, **kwargs)
    return wrapper


class ArtefactBase(ABC):

    def __init__(self, platform_config: dict, artefact_config: dict):
        self._platform_config = platform_config
        self._artefact_config = artefact_config
        self._status = ArtefactStatus.INITIALISED

        if self._artefact_config['architecture'] not in platform_config['architectures']:
            raise ValueError(f"Unknown architecture: {self._artefact_config['architecture']}")

        if not does_archiver_exist():
            print("archiver not found")
            sys.exit(1)

        self.identifier = self.__get_identifying_hash()  # The MD5 hash of "platform/name/architecture".
        
        self._download_url = None  # The URL to the source file to download, as a string.
        self._version = None  # The version of the downloaded file, as a string.

        self._downloaded_path = None  # The absolute path to the downloaded file on the local filesystem.
        self._downloaded_hash = None  # The SHA256 of the downloaded file, as a string.

        self._setup()
        self._get_request()
    
    @classmethod
    @abstractmethod
    def get_type(cls):
        raise NotImplementedError()
    
    @abstractmethod
    def _setup(self):
        raise NotImplementedError()
    
    @abstractmethod
    def _get_request(self):
        raise NotImplementedError()
    
    @requires_url_or_version
    def get_url(self):
        return self._download_url
    
    @requires_url_or_version
    def get_version(self):
        return self._version
    
    @requires_url_or_version
    def does_url_exist(self):
        try:
            response = requests.head(self._download_url)

            if response.status_code in (200, 301, 302):
                return True

            return False
        except requests.exceptions.RequestException:
            return False
    
    @requires_url_or_version
    def download(self):
        response = requests.get(self._download_url, stream=True)

        filename = os.path.basename(self._download_url)
        download_path = os.path.join(self._platform_config['temporary_directory'], filename)

        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            progress_bar = tqdm.tqdm(total=total_size, unit='B', unit_scale=True, desc=pad_string(self._artefact_config['name']))

            with open(download_path, 'wb') as file:
                for data in response.iter_content(chunk_size=1024):
                    file.write(data)
                    progress_bar.update(len(data))
            
            progress_bar.close()
            self._downloaded_path = download_path
            self._downloaded_hash = self.__get_file_hash()
            self._status = ArtefactStatus.DOWNLOADED
    
    def __get_identifying_hash(self) -> str:
        """
        
        """
        md5_hash = hashlib.md5()
        identifying_string = f"{self._platform_config['directory']}/{self._artefact_config['name']}/{self._artefact_config['architecture']}"

        md5_hash.update(identifying_string.encode('utf-8'))

        return md5_hash.hexdigest()

    def __get_file_hash(self) -> str:
        """
        Returns a `string` representing the SHA256 hash of the downloaded file.
        Note that the file must be downloaded; if the file is not downloaded, a `ValueError` will be raised.
        """
        sha256_hash = hashlib.sha256()

        with open(self._downloaded_path, "rb") as file:
            while chunk := file.read(4096):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()

    def update_state(self, state: dict):
        if self.identifier not in state['inventory'].keys():
            state['inventory'][self.identifier] = self._downloaded_hash
            return

        existing_sha256 = state['inventory'][self.identifier]

        if existing_sha256 != self._downloaded_hash:
            state['inventory'][self.identifier] = self._downloaded_hash
            
            state['changes'][self.identifier] = {
                'platform': self._platform_config['name'],
                'name': self._artefact_config['name'],
                'version': self._version,
                'architecture': self._artefact_config['architecture'],
            }
    
    @requires_download
    def is_archive(self):
        file_extension = os.path.splitext(self._downloaded_path)[1].lower()

        if file_extension in SKIP_ARCHIVE_CHECKS:
            return False

        if run_archiver(['t', self._downloaded_path]) == 0:
            return True
        
        return False
    
    @requires_download
    def extract_archive(self):
        if self.is_archive():
            result = run_archiver(['x', self._downloaded_path, f"-o{os.path.dirname(self._downloaded_path)}"])

            if result == 0:
                pass
                
                # Count
                # 7zz l Archive.zip | tail -n 1 |awk '{ print $5; }'