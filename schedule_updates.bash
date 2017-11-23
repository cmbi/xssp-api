#!/bin/bash

MYDIR=$(dirname $0)

UPDATE=$MYDIR/update_databanks.py

chmod 755 $UPDATE

if ! [ -f /srv/blast/hg-hssp.psq ] || ! [ -f /srv/blast/hssp3.psq ] ; then

    # Databanks not present, build now!
    /usr/local/bin/python $UPDATE
fi

# Copy this script's environment variables to cron job:
ENV="
PATH=$PATH
"

CRONFILE=$MYDIR/update_cron

/bin/echo -e "$ENV\n0 20 * * 5 /bin/bash $UPDATE\n" > $CRONFILE
crontab $CRONFILE

cron -f
