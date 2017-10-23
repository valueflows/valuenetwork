#!/usr/bin/env bash

# Start the FairCoin processor daemon if config is ready
if [[ -f ./faircoin_nrp/daemon/daemon.conf ]]; then
    echo "Faircoin daemon config found. Starting daemon..."
    pushd ./faircoin_nrp/daemon/
        ./daemon_service start
        ./daemon_service status
    popd
else
    echo "Faircoin daemon config not inited yet, if you wish to run Faircoins locally please init first."
fi

# Run the webserver
./manage.py runserver 155.92.15.29:8000
# ./manage.py test
