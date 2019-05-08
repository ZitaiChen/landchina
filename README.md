# Install
Require package: Scarpy
```bash
$ conda install scrapy
```
# Usage
Start crawl the website and all the records will be shown in the terminal.

```bash
$ scrapy crawl landchinaV3
```

Save all the records in a json file
```bash
$ scrapy crawl landchinaV3 -o records.json
```
Note that all the records are in GBK coding. In MacOS, we can convert to UTF-8 as follow: for single file
```bash
$ iconv -f GBK -t UTF-8 records.json > utf8.json
```
for batch of files
```bash
$ find *.json -exec sh -c "iconv -f GBK -t UTF8 {} > {}.utf8" \;
```

