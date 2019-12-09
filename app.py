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
    orgname = "customshouse"  # < hard coded for testing only.
    org1 = orgname + ".com.au"
    org2 = orgname + ".com"
    org3 = orgname + ".net"
    orglist = [org1, org2, org3]

    print("Scan will assess for:\n  " + org1 + "\n  " + org2 + "\n  " + org3)

    # response = input("Do you want to commence the scan, y/n?  ") # < commented out for testing.
    response = "y"  # < in for testing only
    if response == "y":
        print("\nApproved to carry on. \n-------------------------------------------------------------\nPerforming "
              "DNS lookup")
        return DnsSearch(orglist, orgname)
    else:
        response = input("Do you want to try a different organisation name, y/n?")
        if response == "n":
            exit()
        else:
            OrgName()


def DnsSearch(orglist, orgname):
    # Loop though the given variants of the org name to validate IP address existence.
    # NB: We will need the ability to exclude those which are not applicable, as well as the ability to stipulate
    # a complete address from scratch.

    iplist = {}  # Table to store org name and IP address

    # Create xlsx workbook to store output.
    workbook = xlsxwriter.Workbook("/root/Desktop/" + orgname + "-SurfProfOutput.xlsx")  # This location will need to
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
    # linecheck = input("Line Number: ") # < comment out for testing only
    linecheck = "1"  # < in for testing only
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

    print("Performing website contact detail extraction @" + websiteurl)
    http = urllib3.PoolManager()
    contacturllist = ["/contact/", "/contactus/", "/contact_us/", "/about/"]
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
            print("No email addresses found using href")
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
    return CleanContacts(contactemails, wsrow, wscol, workbook, worksheet)


def CleanContacts(contactemails, wsrow, wscol, workbook, worksheet):
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

    return mxlookup(list, wsrow, wscol, workbook, worksheet)


def mxlookup(list, wsrow, wscol, workbook, worksheet):
    # Performing a MX Lookup against the unique list of domain names, returned from the website URL and scraping of the
    # various "contact" pages across the site.

    print("\n-------------------------------------------------------------\nCommencing MX Lookup on identified "
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

    workbook.close()
    print("\n")
    # return GrabSiteDetails(url)

if __name__ == '__main__':
    OrgName()
