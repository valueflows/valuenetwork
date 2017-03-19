#!/usr/bin/env bash

# Start the FairCoin processor daemon if config is ready
if [[ -f ./faircoin_nrp/daemon/daemon.conf ]]; then
    echo "Faircoin daemon config found. Starting daemon..."
    ./faircoin_nrp/daemon/daemon_service start
else
    echo "Faircoin daemon config not inited yet, if you wish to run Faircoins locally please init first."
fi

# Run the webserver
./manage.py runserver 0.0.0.0:8000
