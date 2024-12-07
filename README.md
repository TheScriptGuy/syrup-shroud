# :mag: :earth_africa: Syrup Shroud Project :earth_africa: :mag:
Looking to identify where connecting IP addresses are coming from common BGP Autonomous System Numbers? Look no further!

This script will search through log files and perform whois lookups of the public IP addresses, map them to BGP AS numbers using RIPE's [API](https://stat.ripe.net/docs/data_api) and either present a table summary (see example below) or write out the contents to a json file for automation purposes.

This table shows:
1. All the common BGP ASNs and the BGP description from WHOIS data.
2. Number of IP's unique counted within the log files
3. The number of Total log entries that matched that common BGP ASN
4. Sample IP addresses from the log files (up to 3). If you want all the IPs, then use the `--json` argument.

```
+---------+---------------------------------------------------------+----------+---------------+-------------------------------------------------+
| BGP ASN | BGP Description                                         | IP Count | Total Entries | Sample IPs                                      |
+---------+---------------------------------------------------------+----------+---------------+-------------------------------------------------+
| 398324  | censys-arin-01                                          |        7 |            14 | 206.168.34.49, 162.142.125.210, 162.142.125.196 |
| 14061   | digitalocean-asn                                        |        5 |             5 | 146.190.41.214, 139.59.58.140, 159.203.44.105   |
| 8075    | microsoft-corp-msn-as-block                             |        4 |             6 | 20.118.68.252, 13.83.43.70, 4.151.218.179       |
| 398705  | censys-arin-02                                          |        3 |             5 | 167.94.145.31, 167.94.145.103, 167.94.146.56    |
| 174     | cogent-174                                              |        3 |             3 | 207.90.244.2, 185.142.236.36, 207.90.244.14     |
| 6453    | as6453                                                  |        2 |            11 | 66.198.154.130, 64.86.79.118                    |
| 398823  | peg-la                                                  |        2 |             2 | 38.165.104.71, 38.33.108.194                    |
| 7474    | optuscom-as01-au singtel optus pty ltd                  |        1 |           247 | 59.154.163.62                                   |
| 3491    | console-connect-asn                                     |        1 |           179 | 63.216.60.34                                    |
| 2914    | ntt-ltd-2914                                            |        1 |            69 | 129.250.194.70                                  |
| 5650    | frontier-frtr                                           |        1 |            24 | 45.52.201.102                                   |
| 202425  | int-network                                             |        1 |             3 | 89.248.163.200                                  |
| 200019  | alexhost                                                |        1 |             2 | 91.208.197.167                                  |
| 58461   | ct-hangzhou-idc no.288                                  |        1 |             2 | 115.231.78.10                                   |
| 396982  | google-cloud-platform                                   |        1 |             2 | 34.144.255.55                                   |
| 138341  | shopee-as shopee singapore private limited              |        1 |             1 | 147.136.133.253                                 |
| 10439   | carinet                                                 |        1 |             1 | 71.6.134.235                                    |
| 50304   | blix                                                    |        1 |             1 | 185.12.59.118                                   |
| 61242   | multinet                                                |        1 |             1 | 46.22.172.190                                   |
| 140227  | hkcicl-as-ap hong kong communications international co. |        1 |             1 | 38.47.208.44                                    |
| 4837    | china169-backbone china unicom china169 backbone        |        1 |             1 | 123.191.151.129                                 |
| 138995  | antbox1-as-ap antbox networks limited                   |        1 |             1 | 103.101.191.239                                 |
| 4812    | chinanet-sh-ap china telecom group                      |        1 |             1 | 222.70.24.62                                    |
+---------+---------------------------------------------------------+----------+---------------+-------------------------------------------------+
```

## :wrench: Installation :wrench:
Installation is simple and easy!
1. Clone the repository
```bash
$ git clone https://github.com/TheScriptGuy/syrup-shroud
```

2. Create a virtual environment and activate it.
```bash
$ python3 -m venv .venv
$ source .venv/bin/activate
```

3. Install the necessary libaries.
```bash
$ pip install -r requirements.txt
```

4. You're good to go!

## :pencil2: Usage :pencil2:
There are some nifty features within this program.

:star: Regular Expression searching (find lines matching a particular regex)

:star: Column separator - useful identifying the write "column" within your log file that contains the public IP address.

:star: RIPE database - useful for minimizing the number of queries to the RIPE API.

:star: json output - outputs all data from the query to be used in automation tasks.

### Example 1
We have a log entry from the file `/syslog/server-log.2024-11-26` that looks like an SSH attempt to a linux host. It looks like this:
```
Nov 26 00:00:15 server Connection from 218.92.0.172 port 39171 on 123.123.123.123 port 22 rdomain ""
```
We are going to find all lines that match the regular expression `Connection from.*port 22`
We can use the "space" as the column indicator for this log entry.
Our public IP address that we want to lookup is in the 7th column but we use a zero index to reference it, so we will use `--column 6`.

We can run our python script like so:
```bash
(.venv) $ python3 main.py  --separator " " --column 6 /syslog/server-log.2024-11-26 'Connection from.*port 22'
```
Which will give us this output:
```
+---------+-------------------------+----------+---------------+--------------+
| BGP ASN | BGP Description         | IP Count | Total Entries | Sample IPs   |
+---------+-------------------------+----------+---------------+--------------+
| 4134    | chinanet-backbone no.31 |        1 |             1 | 218.92.0.172 |
+---------+-------------------------+----------+---------------+--------------+
```
### Example 2
If we're running this script many times, we'll be calling the RIPE API very frequently which might run into some API usage restrictions. The argument `--ripedb` can be used to store the results from RIPE API queries and used for future comparisons. This is particularly helpful if your log files have a lot of public IPs in them.

Using the same example as above, you could run it like this:
```bash
(.venv) $ python3 main.py  --separator " " --column 6 --ripedb ripe.json /syslog/server-log.2024-11-26 'Connection from.*port 22'
```

The script will check to see if the file exists, if so, it'll load it. If there are newer subnets that are discovered (that are not in the local RIPE database file), the updates will be added and written back to the json file when the script finishes.
If you need to "refresh" the database, just remove the file and the script will query the RIPE API again.

### Example 3
Assuming you want to have further automation within your pipeline, you can use the `--json` argument to write the analysis out into a json file.
```bash
(.venv) $ python3 main.py  --separator " " --column 6 --ripedb ripe.json --json output.json /syslog/server-log.2024-11-26 'Connection from.*port 22'
```

From the first example, the resulting output would be:
```json
{
    "4134_chinanet-backbone no.31": {
        "total_log_entries": 1,
        "ips": [
            "218.92.0.172"
        ]
    }
}
```

The key for the entry is the `<BGP AS Number>_<BGP Description>`

## List all subnets of a BGP ASN
If you want to get all the subnets of a particular BGP ASN, you can use the `get_subnets_from_asn.py` python script.

By default, this will output the (unsummarized) contents to stdout, but you can use the `--prefix` argument to separate the output into IPv4 and IPv6 subnets.

### Example 1
To return list of subnets to stdout:
```bash
(.venv) $ python3 get_subnets_from_asn.py 13355
```

### Example 2
To return list of summarized subnets to stdout:
```bash
(.venv) $ python3 get_subnets_from_asn.py --summarize 13355
```

### Example 3
To output the contents to files (this will separate both IPv4 and IPv6 subnets)
```bash
(.venv) $ python3 get_subnets_from_asn.py --prefix cloudflarenet --summarize 13335
```
Which would result in this output and 2 files being created with the appropriate subnets in it.
```
2024-12-01 10:23:50,548 - INFO - Fetching prefixes for ASN 13335
2024-12-01 10:23:51,785 - INFO - Written 462 prefixes to cloudflarenet-v4.txt
2024-12-01 10:23:51,785 - INFO - Written 763 prefixes to cloudflarenet-v6.txt
```

## Generate a Word Cloud
### Installation
To install:
```bash
$ pip install -r requirements-wordcloud.txt
```

### Usage
From the previous example above:
```bash
(.venv) $ python3 main.py  --separator " " --column 6 --ripedb ripe.json --json output.json /syslog/server-log.2024-11-26 'Connection from.*port 22'
```

You can use the `output.json` file to generate the word cloud image and table.

### Example output
#### Top 20 BGP ASN - Total Log Entries
```bash
(.venv) $ python3 generate_wordcloud.py -i output.json -o wordcloud-total_log_entries.png
```

Example image output:
![wordcloud-total-log-entries](images/wordcloud_log_entries.png?raw=true)

#### Image 2 - Top 20 BGP ASN - Unique IP Addresess
To create a wordcloud of the unique number of IP addresses:

```bash 
(.venv) $ python3 generate_wordcloud.py -i output.json -o wordcloud-total_log_entries.png --metric ip_count
```

Example image output:
![wordcloud-ipcount](images/wordcloud_ipcount.png?raw=true)

## Collaboration
I am always open to collaborate on projects like this. Feel free to submit a pull request to do so.

## Licensing
Free for personal use.
Commercial options available.

This project follows on from the [molasses-masses](https://github.com/TheScriptGuy/molasses-masses) project.
