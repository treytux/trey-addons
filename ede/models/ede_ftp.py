###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
import os

_log = logging.getLogger(__name__)

try:
    from ftplib import FTP
except ImportError:
    _log.debug('Can not `import ftputil`.')
try:
    import xmltodict
except ImportError:
    _log.debug('Can not `import xmltodict`.')


class EdeFTP(object):
    def __init__(self, host, user, password, local_path, remote_path,
                 user_notify):
        self.host = host
        self.user = user
        self.password = password
        self.local_path = local_path
        self.remote_path = remote_path
        self.user_notify = user_notify

    def connection(self):
        try:
            ftp = FTP(host=self.host)
            ftp.login(user=self.user, passwd=self.password)
            ftp.cwd(self.remote_path)
            if not os.path.exists(self.local_path):
                os.makedirs(self.local_path)
            return ftp
        except RuntimeError as detail:
            _log.critical('EDE ftp critical error', detail)

    def list_files(self, client=None):
        return client.mlsd()

    def delete_file(self, client=None, filename=None):
        client.delete(filename)
        local_file = os.path.join(self.local_path, filename)
        os.remove(local_file)

    def process_xml_invoice(self, client=None, filename=None):
        def download_file(file):
            with open(local_file, 'wb') as lf:
                client.retrbinary('RETR %s' % filename, lf.write, 8 * 1024)
                lf.close()
        local_file = os.path.join(self.local_path, filename)
        if not os.path.exists(local_file):
            download_file(filename)
        if os.stat(local_file).st_size == 0:
            os.remove(local_file)
        retry = 3
        while retry != 0:
            if os.stat(local_file).st_size != 0:
                break
            download_file(filename)
            if os.stat(local_file).st_size == 0:
                os.remove(local_file)
        retry -= 1
        try:
            with open(local_file, 'r') as lf:
                xml = xmltodict.parse(lf.read())
        except RuntimeError as detail:
            _log.critical('EDE ftp critical error', detail)
            raise
        if not xml:
            return []
        return xml
