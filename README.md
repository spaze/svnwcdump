svnwcdump
=========

Dumps Subversion working copy located at a website and accessible using HTTP

Usage: ```svnwcdump.py <website> <directory> <logfile> [--no-tor] [--almost-dry]```

Where:
- ```<website>``` is without the path to entries file, just http://example.com
- ```<directory>``` where to dump the working copy
- ```<logfile>``` where to log messages

Options:
- ```--no-tor``` do not use Tor proxy
- ```--almost-dry``` create empty files, don't download

Example:
```svnwcdump.py http://example.com loot dump.log --no-tor```
