#!/usr/bin/python3

import dns
import urllib3
import dns.resolver
import json
from bs4 import BeautifulSoup
import xlsxwriter


print("Here we go!\n-------------------------------------------------------------")


def OrgName():
    # orgname = input("Enter organisation name: ") # Commented out for testing only
    orgname = "conradgargett" # < hard coded for testing only.
    org1 = orgname + ".com.au"
    org2 = orgname + ".com"
    org3 = orgname + ".net"
    orglist = [org1, org2, org3]

    print("Scan will assess for:\n  " + org1 + "\n  " + org2 + "\n  " + org3)

    # response = input("Do you want to commence the scan, y/n?  ") # < commented out for testing.
    response = "y" # < in for testing only
    if response == "y":
        print("\nApproved to carry on. \n-------------------------------------------------------------\nPerforming "
              "DNS lookup")
        return DnsSearch(orglist)
    else:
        response = input("Do you want to try a different organisation name, y/n?")
        if response == "n":
            exit()
        else:
            OrgName()


def DnsSearch(orglist):
    iplist = {}
    for x in orglist:
        try:
            arecord = dns.resolver.query(x, 'A')
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            print("'" + x + "'" + " has no DNS response. Removing from list")
        else:
            for ipvalue in arecord:
                print("'" + x + "'" + " -- IP: ", ipvalue.to_text())
                iplist[x] = ipvalue.to_text()
    print("The following url's have returned positive IP addresses. Referencing the line number, enter the line "
          "which represents the corporate website.")
    i = 1
    temp = {}

    for l in iplist:
        temp[str(i)] = l
        i = i + 1
    print("Line  URL")

    for x, y in temp.items():
        print(" " + x + "/. ", y)
    # linecheck = input("Line Number: ") # < comment out for testing only
    linecheck = "1" # < in for testing only
    print("\n-------------------------------------------------------------\nSelected URL: " + temp[linecheck] +
          "\n-------------------------------------------------------------\n")
    websiteurl = temp[linecheck]

    return ContactScrape(websiteurl)


def ContactScrape(websiteurl):
    print("Performing website contact detail extraction @" + websiteurl)
    http = urllib3.PoolManager()
    contacturllist = ["/contact/" , "/contactus/", "/contact_us/", "/about/"]
    contactemails = {}
    contactemails[websiteurl] = []
    for li in contacturllist:
        checkurl = "http://www." + websiteurl + li
        print("\nNow scanning: " + checkurl)
        response = http.request('GET', checkurl)
        print("HTTP Response: " + str(response.status))
        soup = BeautifulSoup(response.data, features="lxml")
        mailtos = soup.select('a[href^=mailto]')

        if not mailtos:
            print("No email addresses found using href")
        else:
            for i in mailtos:
                href = i['href']
                try:
                    str1, str2 = href.split(':')
                    print(str2)
                    contactemails[str2] = []
                except ValueError:
                    break

        # There should be another lookup here to identify where a page in built on json eg. 'email' : 'user@domain.com'
    print("\n-------------------------------------------------------------\n")
    return CleanContacts(contactemails)


def CleanContacts(contactemails):
    list = {}
    for i in contactemails.keys():
        try:
            x = i.split('@', 1)[1]
            list[x] = []
        except IndexError:
            list[i] = []

    print("The following unique domain names have been found:\n")
    for i in list:
        print(i)
    return mxlookup(list)


def mxlookup(list):
    print("\n-------------------------------------------------------------\nCommencing MX Lookup on identified "
          "domains\n")
    mxlist = {}
    for i in list:
        result = dns.resolver.query(i, 'MX')
        for j in result:
            #arecord = dns.resolver.query(j.to_text(), 'A')
            #for ipvalue in arecord:
            #    mxlist[j.to_text] = ipvalue.to_text()
            print(i + "MX record at: " + j.to_text())
    url = next(iter(list))
    # return GrabSiteDetails(url)


OrgName()
