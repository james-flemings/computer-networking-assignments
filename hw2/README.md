# TCP Client

This assignment implements a rudimentary TCP client to run against a TCP client provided by my instructor, so it vaguely follows the attatched RFC. I initially was doing a good job organizing my code and making it modular. But after encountering many issues with the selective repeat protocol, the code started getting messy. `tcp_client.py` is where the main execution occurs while `tcp.py` and `header.py` are helper classes. `header.py` provides a module to create and store proper tcp packets while `tcp.py` contains all the important functions like handshake.
