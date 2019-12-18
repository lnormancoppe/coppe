#!/usr/bin/python3

import dns
import dns.resolver
import urllib3
import xlsxwriter
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as ThreadPool
from pathlib import Path
from functools import partial
import threading

print("Here we go!\n\n-------------------------------------------------------------")


def OrgName():
    print("    _____  ")
    print("   / ___/__  ___  ___  ___")
    print("  / /__/ _ \/ _ \/ _ \/ -_)")
    print("  \___/\___/ .__/ .__/\__/")
    print("     ____ /_/  /_/___               ___           ____ __")
    print("    / __/_ ______/ _/__ ________   / _ \_______  / _(_) /__ ____")
    print("   _\ \/ // / __/ _/ _ `/ __/ -_) / ___/ __/ _ \/ _/ / / -_) __/")
    print("  /___/\_,_/_/ /_/ \_,_/\__/\__/ /_/  /_/  \___/_//_/_/\__/_/")
    print('')

    orgname = input("Enter organisation name: ")  # Commented out for testing only
    # orgname = "bbc"  # < hard coded for testing only.
    org1 = orgname + ".com.au"
    org2 = orgname + ".com"
    org3 = orgname + ".net"
    orglist = [org1, org2, org3]

    print("\nScan will assess for:\n  " + org1 + "\n  " + org2 + "\n  " + org3)

    response = input("Do you want to commence the scan, y/n?  ")  # < commented out for testing.
    # response = "y"  # < in for testing only
    if response == "y":
        print("\nApproved to carry on. \n\n-------------------------------------------------------------\n\nPerforming "
              "DNS lookup")
        return DnsSearch(orglist, orgname)
    else:
        response = input("Do you want to try a different organisation name, y/n? ")
        if response == "n":
            exit()
        else:
            OrgName()


def DnsSearch(orglist, orgname):
    # Loop though the given variants of the org name to validate IP address existence.
    # NB: We will need the ability to exclude those which are not applicable, as well as the ability to stipulate
    # a complete address from scratch.

    iplist = {}  # Table to store org name and IP address
    home = str(Path.home())

    # Create xlsx workbook to store output.
    workbook = xlsxwriter.Workbook(home + "/Desktop/" + orgname + "-SurfProfOutput.xlsx")  # This location will need to
    # be made generic to suit all of our users.
    worksheet = workbook.add_worksheet("Output")
    worksheet.set_column('A:A', 48)
    worksheet.set_column('B:B', 30)
    worksheet.set_column('C:C', 40)
    worksheet.set_column('D:D', 30)
    worksheet.write('A1', "Org Name")
    worksheet.write('B1', orgname)
    wsrow = 2
    wscol = 0

    worksheet.write(wsrow, wscol, "Query")
    worksheet.write(wsrow, wscol + 1, "Domain")
    worksheet.write(wsrow, wscol + 2, "IP Address")

    for x in orglist:
        try:
            arecord = dns.resolver.query(x, 'A')
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            print("'" + x + "'" + " has no DNS response. Removing from list")
        else:
            for ipvalue in arecord:
                print("'" + x + "'" + " -- IP: ", ipvalue.to_text())
                iplist[x] = ipvalue.to_text()
                wsrow = wsrow + 1
                worksheet.write(wsrow, wscol, "Org Variant")
                worksheet.write(wsrow, wscol + 1, x)
                worksheet.write(wsrow, wscol + 2, ipvalue.to_text())

    print("The following url's have returned positive IP addresses. Referencing the line number, enter the line "
          "which represents the corporate website's domain.")

    i = 1  # Counter for line numbers
    temp = {}  # Temporary table to store counter number and org name < for user experience only.

    for l in iplist:
        temp[str(i)] = l
        i = i + 1
    print("Line  URL")

    for x, y in temp.items():
        print(" " + x + "/. ", y)

    # Request a user input that corresponds to the line number to determine the corporate website. We take that input
    # and pass to the next function to begin scraping for email credentials.
    linecheck = input("Line Number: ")  # < comment out for testing only
    # linecheck = "1"  # < in for testing only
    print("\n-------------------------------------------------------------\nSelected URL: " + temp[linecheck] +
          "\n-------------------------------------------------------------\n")

    websiteurl = temp[linecheck]

    # Write corporate domain to output file.
    wsrow = wsrow + 2
    worksheet.write(wsrow, wscol, "Corporate website domain:")
    worksheet.write(wsrow, wscol + 1, websiteurl)

    return ContactScrape(websiteurl, wsrow, wscol, workbook, worksheet)


def ContactScrape(websiteurl, wsrow, wscol, workbook, worksheet):
    # Here, we scrape against common variants of the 'contact' page of a website in search of 'a' tags with href lines.
    # We use BeautifulSoup4 to parse the response and allow us to easily extract given bodies of information. The output
    # is stored in a table named 'mailtos'.

    print("Performing website contact detail extraction @ " + websiteurl)
    http = urllib3.PoolManager()
    contacturllist = ["/contact/"]
    # ["/contact/", "/contactus/", "/contact_us/", "/contact-us/", "/about/", "/aboutus/", "/about-us/",
    # "/about_us/", "/about_us/"]
    contactemails = {}
    contactemails[websiteurl] = []  # This is here in case the contact pages show domains which are completely different
    # to the website URL.

    wsrow = wsrow + 2
    worksheet.write(wsrow, wscol, "URL Scanned")
    worksheet.write(wsrow, wscol + 1, "http status")
    worksheet.write(wsrow, wscol + 2, "Email address found")

    for li in contacturllist:
        checkurl = "http://www." + websiteurl + li  # Check for port 80 before 443 by redirect. ie best practice

        print("\nNow scanning: " + checkurl)
        response = http.request('GET', checkurl)

        print("HTTP Response: " + str(response.status))  # Return the status of the page tells us what information is
        # present on the 404 pages as well.
        soup = BeautifulSoup(response.data, features="lxml")
        mailtos = soup.select('a[href^=mailto]')

        if not mailtos:
            print("No email addresses found using href scan")
        else:
            for i in mailtos:
                href = i['href']
                try:
                    # We are now separating the html tag content from the email address.
                    str1, str2 = href.split(':')
                    print(str2)
                    contactemails[str2] = []

                    wsrow = wsrow + 1
                    worksheet.write(wsrow, wscol, checkurl)
                    worksheet.write(wsrow, wscol + 1, str(response.status))
                    worksheet.write(wsrow, wscol + 2, str2)

                except ValueError:
                    break

        # There should be another lookup here to identify where a page in built on json eg. 'email' : 'user@domain.com'
    print("\n-------------------------------------------------------------\n")
    return CleanContacts(contactemails, wsrow, wscol, workbook, worksheet, websiteurl)


def CleanContacts(contactemails, wsrow, wscol, workbook, worksheet, websiteurl):
    # This function is cleaning up the returned list of email addresses. The intention being to pivot the output so we
    # are only dealing with one instance of each domain variant before we commence MX lookup.

    wsrow = wsrow + 2
    worksheet.write(wsrow, wscol, "Unique Domains")

    list = {}  # Forced to be a dictionary which prevents duplicate entries.
    for i in contactemails.keys():
        try:
            x = i.split('@', 1)[1]
            list[x] = []
        except IndexError:
            list[i] = []

    print("The following unique domain names have been found:\n")
    for i in list:
        wsrow = wsrow + 1
        worksheet.write(wsrow, wscol, i)
        print(i)

    return MxLookup(list, wsrow, wscol, workbook, worksheet, websiteurl)


def MxLookup(list, wsrow, wscol, workbook, worksheet, websiteurl):
    # Performing a MX Lookup against the unique list of domain names, returned from the website URL and scraping of the
    # various "contact" pages across the site.

    print("\n-------------------------------------------------------------\n\nCommencing MX Lookup on identified "
          "domains\n")

    wsrow = wsrow + 2
    worksheet.write(wsrow, wscol, "Domain MX Assessment")
    wsrow = wsrow + 1
    worksheet.write(wsrow, wscol, "Domain")
    worksheet.write(wsrow, wscol + 1, "MX Records")
    worksheet.write(wsrow, wscol + 2, "Priority")
    worksheet.write(wsrow, wscol + 3, "IP Address")

    mxlist = {}
    for i in list:
        result = dns.resolver.query(i, 'MX')

        for j in result:
            wsrow = wsrow + 1
            x = j.to_text()
            str1, str2 = x.split()
            arecord = dns.resolver.query(str2, 'A')

            for ipvalue in arecord:
                mxlist[str2] = ipvalue.to_text()
                ipval = ipvalue.to_text()

            print(i + " MX record at: " + str2 + " @ Priority: " + str1 + ", IP: " + ipval)
            worksheet.write(wsrow, wscol, i)
            worksheet.write(wsrow, wscol + 1, str2)
            worksheet.write(wsrow, wscol + 2, str1)
            worksheet.write(wsrow, wscol + 3, ipval)

    return FindCName(websiteurl, wsrow, wscol, workbook, worksheet)


def FindCName(websiteurl, wsrow, wscol, workbook, worksheet):
    print("-------------------------------------------------------------\n\nCommencing CName query on identified "
          "domains\n")

    wsrow = wsrow + 2
    worksheet.write(wsrow, wscol, "CName Scan")
    wsrow = wsrow + 1
    worksheet.write(wsrow, wscol, "Domain")
    worksheet.write(wsrow, wscol + 1, "CNames")

    try:
        result = dns.resolver.query(websiteurl, 'CNAME')
        for j in result:
            print(j.target)

            wsrow = wsrow + 1
            worksheet.write(wsrow, wscol, websiteurl)
            worksheet.write(wsrow, wscol, j.target)

    except dns.resolver.NoAnswer:
        print("No CName found for " + websiteurl)

    return InitThread(websiteurl, wsrow, wscol, workbook, worksheet)


def SubdomainSearch(wscol, wsrow, workbook, worksheet, dnsservers, finallist):
    threadid = threading.get_ident()

    for i, j in dnsservers.items():
        if dnsservers.get(i) == 0:
            x = i
            dnsservers.pop(i)
            dnsservers[x] = threadid
            # print("Thread ID added to list using DNS Server: " + x) # < print for testing only.
            break
        elif dnsservers.get(i) == threadid:
            x = dnsservers.get(i)
            # print("ThreadID Exists") # < print for testing only.
            break

    while True:
        try:
            specresolver = dns.resolver.Resolver()
            specresolver.nameservers = [x]

            print("Scanning: " + finallist + " using NS: " + x + ", on threadID: " + str(threadid))
            response = specresolver.query(finallist)
            for ipval in response:
                print("HIT: " + finallist + " : " + ipval.to_text())
                worksheet.write(wsrow, wscol, finallist)
                worksheet.write(wsrow, wscol + 1, ipval.to_text())
                break

        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            dnsservers[i] = 0
            break

        except dns.resolver.Timeout:
            print("Experienced Timeout. Retrying DNS query.")
            continue

        dnsservers[i] = 0
        break
    return


def InitThread(websiteurl, wsrow, wscol, workbook, worksheet):
    print("-------------------------------------------------------------\n\nCommencing brute sub-domain query on "
          "identified corporate domain\n")

    # Set up the Excel worksheet headings.
    wsrow = wsrow + 2
    worksheet.write(wsrow, wscol, "SubDomain Scan")
    wsrow = wsrow + 1
    worksheet.write(wsrow, wscol, "SubDomain")
    worksheet.write(wsrow, wscol + 1, "IP Address")

    # Introduce the words list.
    f = open("dnswords.txt", "r")
    j = int(1)
    x = {"index": {"Sub Domain": "IP"}}

    # Create a local list, concatenating the dnswords.txt line with the domian.
    finallist = []
    for i in f.readlines():
        d = i.split("\n")[0]
        finallist.append(d + "." + websiteurl)

    # Create a dictionary for the nameservers.
    dnsservers = {
        "8.8.8.8": 0,
        "8.8.4.4": 0,
        "208.67.222.222": 0,
        "208.67.220.220": 0,
        "1:1:1:1": 0,
        "1.0.0.1": 0,
    }

    # Create function to handle passing additional parametres into pool.map
    func = partial(SubdomainSearch, wscol, wsrow, workbook, worksheet, dnsservers)

    # Introduce the threading.
    pool = ThreadPool(6)
    pool.map(func, finallist)
    pool.close()
    pool.join()

    #Close the xlsx workbook to save changes.
    workbook.close()

    # The remaining task is:
    """
    For the convenience of the user, to print the results of hits to the terminal at the end of the the subdomainsearch.
    To do so, we need to pass out 'ipval.to_text()' and the corresponding 'finallist' value. However, as duplicates 
    appear in the search for the 'finallist' value, and potentially the ipval value, this needs to be a nested 
    dictionary. - {1: {finallist: ipval}, 2: {finallist: ipval}} and so on.
    The challenge is: storing and incrementing the key (1, 2, 3, and so on) from within the subdomainsearch.
    """

if __name__ == '__main__':
    OrgName()
