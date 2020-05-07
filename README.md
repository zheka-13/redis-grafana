# redis-grafana

Based on https://github.com/keenlabs/redis-statsd, dependency free Python program for periodically fetching stats via Redis' `INFO`command and emitting them to carbon server.



# Usage

Edit script and set all your params in the beginnig of the file (addresses, password etc.)
Use cron for periodical execution of the script and emmiting metrics to Carbon

For example, every minute would be like this:

*/1     *       *       *       *       root    /srv/redis-grafana.py


