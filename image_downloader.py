from multiprocessing import Pool
from functools import partial
import os
import logging
import argparse
import requests
import validators


def get_filename_from_url(url):
    last_path_element = url.split('/')[-1]
    # Remove GET parameters
    filename = last_path_element.split('?')[0]
    return filename


def is_valid_response(response, url):
    logger = logging.getLogger(__name__)
    if response.status_code != 200:
        logger.error('HTTP error when trying to access: ' + url)
        return False
    logger.debug('HTTP 200 received on URL: ' + url)
    return True


def is_valid_content(response, url):
    logger = logging.getLogger(__name__)
    content_type = response.headers.get('content-type')
    if 'image' not in content_type:
        logger.error('Content of the URL is not an image: ' + url)
        return False
    logger.debug('Content of URL is image/*: ' + url)
    return True


def is_valid_url(url):
    '''
    Checks if passed string is a valid URL expression
     (based on https://gist.github.com/dperini/729294)
    '''
    logger = logging.getLogger(__name__)
    # Regex validation
    if not validators.url(url):
        logger.error('Invalid URL: ' + url)
        return False
    logger.debug('URL is valid: ' + url)
    return True


def save_image(response, file_path):
    logger = logging.getLogger(__name__)
    try:
        with open(file_path, 'wb') as imf:
            imf.write(response.content)
        logger.debug('Saved image to: ' + file_path)
        return True
    except:
        logger.error('Could not save downloaded image to: ' + file_path)
        return False


def get_image(image_url, timeout=5):
    '''
    image_url: regex verified URL of image
    '''
    logger = logging.getLogger(__name__)
    try:
        response = requests.get(
            image_url, allow_redirects=True, timeout=timeout)
        return response
    except requests.exceptions.Timeout:
        logger.error('Request timed out for URL: ' + image_url)
    except:
        logger.error('Failed to download image: ' + image_url)
    return False


def create_dest_dir(dest_dir):
    logger = logging.getLogger(__name__)
    try:
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
            logger.info('Created destination directory: ' + dest_dir)
        return True
    except IOError:
        logger.critical(
            'Could not create download directory nor does it exist')
        return False


def download_single_image(url,
                          dest_dir='image_downloads',
                          replace_duplicates=False,
                          timeout=5):
    logger = logging.getLogger(__name__)
    if not is_valid_url(url):
        return False
    image = get_image(url, timeout)
    if not image:
        return False
    if not is_valid_response(image, url):
        return False
    if not is_valid_content(image, url):
        return False
    image_filename = get_filename_from_url(url)
    image_file_path = os.path.join(dest_dir, image_filename)
    if os.path.exists(image_file_path) and not replace_duplicates:
        logger.info('File already exists, skipping image: ' + image_file_path)
        return False
    save_image(image, image_file_path)
    logger.info('Successfully downloaded image: ' + image_file_path)
    return True


def read_lines_from_file(file_path):
    logger = logging.getLogger(__name__)
    try:
        url_file = open(file_path, 'r')
        lines = url_file.readlines()
        url_file.close()
        return lines
    except IOError:
        logger.critical('Could not read file: ' + file_path)
        return False


def download_images(url_filepath,
                    dest_dir='image_downloads',
                    replace_duplicates=False,
                    timeout=5,
                    processes=10):
    if not create_dest_dir(dest_dir):
        return False

    lines = read_lines_from_file(url_filepath)
    urls = [line.strip() for line in lines]

    pool = Pool(processes=processes)
    worker = partial(
        download_single_image,
        dest_dir=dest_dir,
        replace_duplicates=replace_duplicates,
        timeout=timeout)
    result = pool.map_async(worker, urls)
    result.wait()
    return True


def logging_level_from_verbosity(verbosity):
    '''
    Convert the number of verbosity flags to logging level
    Example: -vv will lead to WARNING level output
    '''
    logging_levels = {
        None: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARNING,
        3: logging.INFO,
        4: logging.DEBUG
    }
    if verbosity in logging_levels:
        return logging_levels[verbosity]
    else:
        return logging.DEBUG


def init_logger(logging_level=logging.CRITICAL):
    '''
    Initialize logging with level and console format
    '''
    logger = logging.getLogger(__name__)
    logger.setLevel(logging_level)
    logger_handler = logging.StreamHandler()
    logger_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger_handler.setFormatter(logger_formatter)
    logger.addHandler(logger_handler)


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        'urlfile',
        help='path of file with image urls, 1 line per url',
        type=str)
    argparser.add_argument(
        '-d',
        '--dest',
        help=('destination folder for downloaded images '
              '(folder will be created if it does not exist) '
              '(default: image_downloads)'),
        type=str,
        default='image_downloads')
    argparser.add_argument(
        '-t',
        '--timeout',
        help='timout for single URL requests in seconds (default: 5)',
        type=float,
        default=5)
    argparser.add_argument(
        '-pr',
        '--processes',
        help='number of parallel download processes (default: 10)',
        type=int,
        default=10)
    argparser.add_argument(
        '-rd',
        '--replace_duplicates',
        help=('overwrite existing files in destination '
              'folder (files are renamed by default)'),
        action='store_true')
    argparser.add_argument(
        '-v',
        '--verbose',
        help=('default: critical, '
              '-v: error, -vv: warning, -vvv: info, -vvvv: debug'),
        action='count')
    args = argparser.parse_args()
    url_filepath = args.urlfile
    dest_dir = args.dest
    timeout = args.timeout
    processes = args.processes
    replace_duplicates = args.replace_duplicates
    verbosity = args.verbose
    init_logger(logging_level=logging_level_from_verbosity(verbosity))

    download_images(url_filepath, dest_dir, replace_duplicates, timeout,
                    processes)


if __name__ == '__main__':
    main()
