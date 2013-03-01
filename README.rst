================
PadLocker Design
================

PadLocker is a client service and web interface designed to enable the
mostly-secure delivery of encryption keys in a mostly-trusted environment.

Goals
=====

- Do not require modification of standard Linux services (allow key reading via
  normal open() calls)
- Prevent the need for any encryption keys to be written to disk on client
  servers
- Allow rules-based automatic key delivery approval
- Allow manual approval-based key delivery approval, and require it by default
- Support LDAP authentication and LDAP group authorization on an individual key
  basis
- Support server-side storage of keys in an encrypted, secure-when-off form


Client
======

- Take a config file that lists locations on disk of fifos to create/watch, and
  any metadata required about those files
- On startup, attempt to create all fifos
- Watch all fifos for ability to write (preferably with select or something
  nice)
- When a fifo is writeable, make a request to the server, including all known
  metadata about the fifo being read
- If the connection to the server times out without returning a key, do
  something reasonable

Server
======

- Take a config file that lists keys to be dispersed, including matching
  patterns for metadata, and authorization information
- Authenticate web-based users via LDAP
- Notify users viewing the interface of incoming requests for the contents of
  fifos
- Upon automatic or manual approval, return the requested key to the client

