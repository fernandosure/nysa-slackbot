Nysa Slackbot
----------

This is a python slackbot application that enables you to update a single existing service with a newer image tag definition.
You can invoke nysa from a specific slack channel “infrabot” and has the following features:


Usage
-----

List the recent tags from an existing service
-----

    @nysa deploy to <cluster> <service>

This will show you the first 20th most recent images that are stored in the Docker Registry


Update an existing service(s) with a newer image tag
-----

    @nysa deploy to <cluster> <service>:<tag>[,<service>:<tag>]

This command will trigger a new deployment using the newer image


Installation
------------

The project is available as a docker image simply run::

    $ docker run -e PROFILE=prod -e AWS_DEFAULT_REGION=us-east-1 xxx.dkr.ecr.us-east-1.amazonaws.com/nysa-slackbot


Configuration
-------------
Nysa-Slackbot its integrated with AWS Secret Manager for managing the secrets used during the application life cycle.
The only configuration that nysa expects as a environment variable is the PROFILE variable that indicates the desired configuration from AWS Secret Manager

- SLACK_BOT_TOKEN: The slack bot token generated by Slack
- SLACK_BOT_AUTHORIZED_CHANNEL: The slack channel authorized for deployments
- ROLLBAR_KEY: A rollbar project key for sending application exceptions occurred
- NYSA_API_BASEURL: Where is located the nysa-api-server for passing the commands

Deploy new changes
------------

If you want to make some changes and then distribute the application you can build a docker image

    $ docker build -t xxx.dkr.ecr.us-east-1.amazonaws.com/nysa-slackbot .

and then in the destination server you just need to pull this new image created

    $ docker pull xxx.dkr.ecr.us-east-1.amazonaws.com/nysa-slackbot
