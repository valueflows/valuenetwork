To install within Docker for development:
--------------------------------------------------------------------------------

*All docker commands should be run from within the `docker` subdirectory: ensure this is your working directory before running any docker-compose commands documented below.*

### Setting up OCP

1. Copy the app settings for development:  
    ```
    cp valuenetwork/local_settings{_development,}.py
    ```
2. Bring up the containers with docker-compose:  
    ```
    docker-compose up
    ```
3. Now you have a running instance but the DB is still empty or copied from testOCP. To run locally you will need to run the DB migrations and create a new superadmin user to login with so you can access the admin backend.
    a. Run DB migrations:  
    ```
    docker-compose exec valuenetwork ./docker/valuenetwork/run-db-migrations.sh
    ```
    b. Create new superuser account (feel free to use your own details if you wish):  
    ```
    docker-compose exec valuenetwork ./docker/valuenetwork/create-superuser.sh valuenetwork_user admin@example.com mrY7rZZ6ztjN90fN6hy6
    ```
4. You can now kill the running containers started with `docker-compose up` and re-run them in order to get OCP up and running.


### Setting up Electrum

Perform the following steps with the Electrum container up and running (started either together with OCP via `docker-compose up` or on its own with `docker-compose up electrum`).


1. Setup the Electrum daemon settings for development:  
    ```
    cp faircoin_nrp/daemon/daemon.conf{.sample,}
    cp faircoin_nrp/daemon/daemon.py{.sample,}
    cp faircoin_nrp/daemon/daemon_service{.sample,}
    chmod +x faircoin_nrp/daemon/daemon.py
    chmod +x faircoin_nrp/daemon/daemon_service
    ```  
    Now edit `faircoin_nrp/daemon/daemon_service` to set `user=` to the unix username who will be running the daemon.  
    You must also edit `faircoin_nrp/daemon/daemon.conf`. To match the wallet you will generate in the Electrum container in step 2, set the following:  
    ```
    [electrum]
    wallet_path = /home/ocp/.electrum-fair/wallets/default_wallet
    seed = 
    password =  
    ```  
    The other settings can all be left as they are.
2. Init a new wallet:  
    ```
    docker-compose exec electrum electrum-fair create
    ```
    Set a password if you wish (you don't really need one for development).
3. Restart both containers. You should now see "Electrum wallet found" in the output for Electrum and "Faircoin daemon config found" in the output for OCP.



To create a production Docker image:
--------------------------------------------------------------------------------

*:TODO: This needs to be re-tested / synced with the development Docker configurations, but should be mostly the same, and differences are already documented. Also, a production dockerfile for Electrum still needs to be configured.*

1. Simply run a docker build with the name of your image and you're done:  
    ```
    docker build -t freedomcoop/valuenetwork:latest .
    ```
