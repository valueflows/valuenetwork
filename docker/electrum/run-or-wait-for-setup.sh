#!/usr/bin/env bash

# Start the wallet only if a wallet has been initialised
if [[ -f /root/.electrum-fair/wallets/default_wallet ]]; then
    echo "Electrum wallet found. Starting daemon..."
    electrum-fair daemon start
else
    echo "Electrum wallet not inited yet, please run 'electrum-fair create' then restart this container."
fi

# keep a process running to prevent Docker container from exiting
tail -f /dev/null
