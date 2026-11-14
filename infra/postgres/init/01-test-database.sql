-- Runs once, when the data volume is first created.
-- A separate database for the backend's db tests, which rebuild their schema each run.
CREATE DATABASE zira_test OWNER zira;
