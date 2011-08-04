from pombo import PomboEntry
from time import gmtime
from datetime import timedelta, datetime

# POMBODAYS is the number of days to keep database/pombo entries to not exceed free quota 1Gb in the datastore
# You can use the formula below to get the max number of days to keep entries
# POMBOSIZE in kb is the average size of a pombo entry in the datastore
# POMBOMIN is the number of minutes you run the pombo cron job

# POMBODAYS = (1024*1024)/((24*60/POMBOMIN)*POMBOSIZE)

POMBODAYS = timedelta(days=30)

t = gmtime()
current_date = datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)

# clean the older entries
entries = PomboEntry.all()
if entries is not None:
    for e in entries:
        if current_date - e.creation_date > POMBODAYS:
            e.delete()
