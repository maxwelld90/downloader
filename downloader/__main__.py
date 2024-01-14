from argparse import ArgumentParser
from .manager import DownloadManager

if __name__ == '__main__':
    parser = ArgumentParser(prog='Downloader',
                            description='Automates the downloading of installer files and images.')
    
    parser.add_argument('config_path',
                        action='store',
                        help='the location on the filesystem of the configuration file.')

    parser.add_argument('-d',
                        '--dryrun',
                        action='store_true',
                        help="performs a dry run, reporting the state of each required file without downloading them.")
    
    args = parser.parse_args()
    manager = DownloadManager(args)
    manager.run()