from collections import namedtuple
import re
import unittest
import urlparse

from bs4 import BeautifulSoup

class Mail(namedtuple('Mail',
                      ('subject', 'href', 'sender'))):
    def get_url(self, index_url):
        return urlparse.urljoin(index_url, self.href)

class MailArchive:
    def __init__(self, path):
        with open(path) as f:
            html_doc = f.read()
        soup = BeautifulSoup(html_doc)
        if 0:
            print(soup.prettify())

        # "threads" view has an <ul> holding the top-level
        # threads, with <li> within them

        # index.html view has a plain <table> for navigation followed
        # by a series of tables:
        #   <table border="0" width="100%">
        # containing the emails for a given date, all in reverse
        # chronological order.
        self.mails = []
        for table in soup.find_all('table', border='0', width='100%'):
            for tr in table.find_all('tr'):
                m = Mail(subject=tr.a.string,
                         href=tr.a['href'],
                         sender=tr.find('td', align='right').string)
                if 0:
                    print(m)
                self.mails.append(m)
        # Put the mails in chronological order
        self.mails.reverse()

    def find_by_subject(self, pattern):
        for m in self.mails:
            if re.match(pattern, m.subject):
                return m

class ArchiveTests(unittest.TestCase):
    def test_reading_index(self):
        # Verify that we can locate patches 01/89 - 89/89 that I sent
        # to gcc-patches in April 2014.

        # From https://gcc.gnu.org/ml/gcc-patches/2014-04/index.html:
        ma = MailArchive('gcc-patches-2014-04-index.html')

        for i in range(1, 90):
            m = ma.find_by_subject(r'\[PATCH %02i/89\]' % i)
            self.assertEqual(m.sender, u'David Malcolm')
            self.assert_(m.subject.startswith, '[PATCH %02i/89] ' % i)
            if 0:
                print(m)

if __name__ == '__main__':
    unittest.main()
