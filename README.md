# q_capacity_dump
A project to dump the capacity graph of a Qumulo cluster into a csv file

Qumulo provides a lot useful real-time analytics.  While the reports in the UI are useful, sometimes it is desired to generate custom reports based on the data.  This project is focused on the capacity trends report.  I

The script simply requites Pyhon 3.x and the only module that may need to be added is 'keyring'.  This can be done in the standard way via pip.  It generates a file in csv format so that it can be imported into a spreadsheet which can then be used to generate reports in many formats.

<pre>
Usage: q_capacity_dump.py [-hD] [-c creds] [-t token] [-f token_file [-o output_file] -s start [-e end] -i inverval [-u unit] qumulo
-h | --help: Prints usage
-D | --DEBUG : Generated info for debugging
-c | --creds : Specify credentials format is user[:password]
-t | --token : Specify an access token
-f | --token-file : Specify is token file [def: .qfds_cred]
-s | -- start : Specify start time period. Format: YY-MM-DD[THH:MM]
-e | --end : Specify end time.  Format YY-MM-DD[THH:MM].  Default is current time
-i | --interval: Specify a time interval [hourly, daily, weekly]
-u | --unit : Specify a unit of size in the report. [kb, mb, gb, tb, pb] [def: bytes]
-o | --output-file : Specify an output file for the report [def: stdout]
qumulo : Name or IP of a Qumulo node
</pre>

## Authentication

Qumulo API calls must be authenticated and the script provides multuiple ways to do so:

1. Specify the credentials on the command line with the -c flag.  The format is user[:password].  If the password is not specified the script will check the keyring, and if still not found will prompt the user.
2. Specify an access token.  It is possible to generate an access token on the Qumulo cluster and specify it on the command line with the -t flag.
3. Specify an access token file.  The -f flag will read a specified file that will read the access token from that file.  By default it looks for .qfsd_cred as that is the default location for many qumulo CLI commands.
4. Keyring.  If a user and password are manually entered, the option will be given to put those credentials into the keyring of that system.  Once that is done, only the user needs to be specified either via the -c flag or manually via a user prompt.
5. If all else fails, the script will simply prompt the user for credentials.  It will then offer to store the in the keyring for future use.

## Units

By default, all space units are specified in bytes.  Units can be changed with the -u flag.  The default unit can be over-ridden with the standard abbreviations [kb, mb, gb, tb, pb].  They are case insenstive and the final 'b' is optional. 

## Minimum Privilege

The script can be run using the admin user, of course.  But for those who wish to run it as a user with minimal priveleges, the following are all that is needed:

<pre>
ANALYTICS_READ
</pre>
