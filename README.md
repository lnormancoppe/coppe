# Coppe projects

Script to take an organisations name and perform various non-intrusive scans. The output is to an xlsx document, 
providing a report indicating the organsiations position towards security/redundancy.

Includes:
- dns and reverse dns scans
- corporate website scan for email addresses
- mx lookup: mail hosting and spam filtering, redundancy/priority of mx service 
- brute force domain scan for iterations of domain names

The following modules need to be installed for this app:
- dns
- requests
- urllib3
- xlsxwriter
- bs4
