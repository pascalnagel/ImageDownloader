import unittest
import logging
import os
import requests
import requests_mock
import image_downloader as idl


class TestGetFilenameFromUrl(unittest.TestCase):
    def test_get_filename_from_url(self):
        url = 'http://media.test.com/image.jpg?v=2&c=4'
        self.assertEqual(idl.get_filename_from_url(url), 'image.jpg')


class TestIsValidResponse(unittest.TestCase):
    def setUp(self):
        self.session = requests.Session()
        self.adapter = requests_mock.Adapter()
        self.session.mount('mock', self.adapter)

    def test_http_ok(self):
        url = 'mock://test.com/index.jpg'
        self.adapter.register_uri(
            'GET',
            url,
            status_code=200,
            reason='200 OK',
            headers={
                'content-type': 'image/jpg'
            })
        response = self.session.get(url)
        self.assertTrue(idl.is_valid_response(response, url))

    def test_http_not_found(self):
        url = 'mock://test.com/somewhere/index.jpg'
        self.adapter.register_uri(
            'GET', url, status_code=404, reason='Not found')
        response = self.session.get(url)
        self.assertFalse(idl.is_valid_response(response, url))


class TestIsValidContent(unittest.TestCase):
    def setUp(self):
        self.session = requests.Session()
        self.adapter = requests_mock.Adapter()
        self.session.mount('mock', self.adapter)

    def test_none_image_content(self):
        url = 'mock://test.com/index.php'
        self.adapter.register_uri(
            'GET',
            url,
            status_code=200,
            reason='200 OK',
            headers={
                'content-type': 'text/html'
            })
        response = self.session.get(url)
        self.assertFalse(idl.is_valid_content(response, url))

    def test_image_content(self):
        url = 'mock://test.com/index.jpg'
        self.adapter.register_uri(
            'GET',
            url,
            status_code=200,
            reason='200 OK',
            headers={
                'content-type': 'image/jpg'
            })
        response = self.session.get(url)
        self.assertTrue(idl.is_valid_content(response, url))


class TestIsValidURL(unittest.TestCase):
    def test_random_string(self):
        self.assertFalse(idl.is_valid_url('isjdfsdfpwej42423n4k235'))

    def test_bad_protocol(self):
        self.assertFalse(idl.is_valid_url('nonono://somehost.com/image.jpg'))


class TestSaveImage(unittest.TestCase):
    def setUp(self):
        session = requests.Session()
        adapter = requests_mock.Adapter()
        session.mount('mock', adapter)
        url = 'mock://test.com/index.jpg'
        adapter.register_uri(
            'GET',
            url,
            status_code=200,
            reason='200 OK',
            headers={'content-type': 'image/jpg'},
            text='I am an image')
        self.response = session.get(url)

    def test_write_content_of_request_to_file(self):
        file_path = 'test.jpg'
        self.assertTrue(idl.save_image(self.response, file_path))
        self.assertTrue(os.path.isfile(file_path))
        os.remove(file_path)

    def test_write_to_nonexistent_dir(self):
        file_path = 'jiofdgndfgng/test.jpg'
        idl.save_image(self.response, file_path)
        self.assertFalse(idl.save_image(self.response, file_path))


class TestReadLinesFromFile(unittest.TestCase):
    def test_invalid_file(self):
        self.assertFalse(idl.read_lines_from_file('fjsiodfjosdods.txt'))


class TestLoggingLevelFromVebosity(unittest.TestCase):
    def test_logging_level_from_verbosity(self):
        verbosities = [None, 1, 2, 3, 4, 5, 18, 105]
        expected_levels = [
            logging.CRITICAL, logging.ERROR, logging.WARNING, logging.INFO,
            logging.DEBUG, logging.DEBUG, logging.DEBUG, logging.DEBUG
        ]
        for e, v in enumerate(verbosities):
            self.assertEqual(
                idl.logging_level_from_verbosity(v), expected_levels[e])


if __name__ == '__main__':
    logger = logging.getLogger('image_downloader')
    logger.disabled = True
    unittest.main()
