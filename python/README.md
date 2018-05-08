Katie DJ - Python client
========================

This folder contains the Python client for listening to the data brodcast from Katie DJ. To run the client, make sure you have Python >= 3.5 and follow the below procedure. We recommend to have the Python 3.5 (or 3.6) executable installed into a virtual environment.


## How to run the client

  1. Clone this repo `git clone git@gitlab.com:pgrandinetti/net-listener.git katiedj-client`
  2. Move into the python folder `cd katiedj-client/python`
  3. Install all requirements `pip3 install -r requirements.txt`. As previously said, we recommend to do it into a virtualenv.
  4. Run the actual client (finally!) `python app.py`. This will start a Dash/Flask app.
  5. Open your internet browser and go to the URL `http://127.0.0.1:8050/`

The client will show to you the historical time series of the streamed data, starting from the instant you ran it.


## Save the data in a storage

It is possible to save the data in a local SQLite database. Let's say you want to store data into a database located at `/home/yourname/katiedj.db`, then at step 4 run instead

  4. `python app.py -s /home/yourname/katiedj.db`

If you stop the client and later want to restart it, then you can simply pass the same database as storage option, and you will see the following message


```
Found existing storage
This storage already exists.
Enter 1 to continue (previous data will be lost if they are not consistent).
Enter other key to exit > 
```

Enter `1` to continue writing on the same database the new data that you will get. If the existing database was created by the same application then it will be fine and you will not loose any data. However, if the database has a different schema, then whatever data is in the database will be destroyed.
