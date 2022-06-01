########################################
# Python script written by Gregg Brown #
########################################

import urllib.request, urllib.parse, urllib.error
from bs4 import BeautifulSoup
import ssl
import sys
import pandas as pd
import numpy as np
from datetime import *
from os import walk
from string import digits

def ExpandRange(in_range,in_prefix=''):
    out_range = []
    if in_prefix != '':
        prefix = '00'+in_prefix
    else:
        prefix = ''
    split_in_range = {rng for rng in in_range.split(",")}
    for item in split_in_range:
        split_range = item.split("-")
        if len(split_range) == 1:
            out_range.append(prefix + item)
        else:
            digits = max([len(x) for x in split_range])
            range_start = split_range[0].ljust(digits,'0')
            range_end = split_range[1].ljust(digits,'0')
            for i in range(int(range_start),int(range_end)+1):
                new_prefix = prefix + str(i).zfill(digits)
                out_range.append(new_prefix)
    out_range.sort()
    if prefix == '':
        return set(out_range)
    else:
        return SimplifyRange(out_range)

def SimplifyRange(in_range):
    in_range = list(in_range)
    in_range.sort()
    out_range = set(in_range)
    for x in range(1,7):
        range_len = len(out_range)
        check_size = 10**x
        if range_len >= check_size:
            for checked in in_range[:1-check_size]:
                if (checked[-1]=='0'):
                    add_to_remove = []
                    for i in range(check_size):
                        next_check = str(int(checked)+i).zfill(len(checked))
                        if next_check in out_range:
                            add_to_remove.append(next_check)
                    if len(add_to_remove) == check_size:
                        out_range.add(checked[:-x])
                        for adds in add_to_remove:
                            out_range.remove(adds)
                    add_to_remove = []
    out_range = list(out_range)
    out_range.sort()
    if len(out_range) == len(in_range):
        return out_range
    else:
        return SimplifyRange(out_range)

def CreateIntMobDataFile(tblrows,attr,clss=''):
    data,errors,removed,hidden,fixed = [],[],[],[],[]
    for tblrow in tblrows:
        try:
            CountryName = tblrow.find_all(attr, class_=clss)[0]
            if 'style="display:none"' in str(CountryName): # remove Hidden rows
                hidden.append(tblrow.find_all(attr, class_=clss))
                continue
            CountryName = CountryName.text.upper().strip().replace("  "," ")
            DiallngCode = tblrow.find_all(attr, class_=clss)[1].text.strip()
            if (CountryName == 'COTE D \' IVOIRE (FORMERLY IVORY COAST)') & (DiallngCode == '255'): # fix broken Cote d'Ivoire code
                DiallngCode = '225'
                fixed.append(tblrow.find_all(attr, class_=clss))
            if (DiallngCode == ''):
                DiallngCode = tblrow.find_all(attr, class_=clss)[2].text.strip()
                prefixIndex = 3
            else:
                prefixIndex = 2
            prefixRows = tblrow.find_all(attr, class_=clss)[prefixIndex:]
            prefixRows = [x for x in prefixRows if 'style="display:none"' not in str(x)]
            PrefixRange = prefixRows[0].text.replace(" ","").replace("?","-").replace(".",",").replace("–","-")
            if len(prefixRows)!=1:
                for cellRow in prefixRows[1:]:
                    next_row = cellRow.text.replace(" ","").replace("?","-").replace(".",",").replace("–","-")
                    if PrefixRange[-1] == '-' or PrefixRange[-1] == ',' or next_row[0] == '-' or next_row[0] == ',':
                        PrefixRange = PrefixRange + next_row
                    else:
                        PrefixRange = PrefixRange + ',' + next_row
            if 'See' in PrefixRange: # remove SeePortugal & SeeSpain
                removed.append([x.text for x in tblrow.find_all(attr, class_=clss)])
                continue
            newrow = True
            for datarow in data:
                if (datarow[0] == CountryName) & (datarow[1] == DiallngCode):
                    for prefix in ExpandRange(PrefixRange):
                        datarow[2].add(prefix)
                    newrow = False
                    break
            if newrow:
                data.append([CountryName,DiallngCode,ExpandRange(PrefixRange)])

        except:
            errorRow = tblrow.find_all(attr)
            if 'class=s1' in errorRow:
                errors.append(tblrow.find_all(attr))
            continue
    return data,errors,removed,hidden,fixed

def nonGeo(urls):
    prntTime('Non-Geo Process started')
    data, fixed = [], []

    prntTime('Downloading Non-Geo data from sources')

    for url in urls:
        tblrows = getSoup(url[1]).find_all('tr', class_='datarow')
        
        removed, errors = [],[]
        for tblrow in tblrows:
            try:
                DiallngCode = ''.join(c for c in tblrow.find_all('td')[0].text if c in digits)
                ChargeBand = tblrow.find_all('td')[1].text.strip()
                
                if (ChargeBand.upper()[:2] == 'SC'):
                    ChargeBand = ChargeBand.upper()
                
                if DiallngCode == '0800' or DiallngCode == '0808':
                    removed.append([DiallngCode,ChargeBand])
                else:
                    data.append([DiallngCode,ChargeBand])
            except:
                errors.append(tblrow.find_all('p'))
                continue
        prntTime(' '.join([url[0],'->',str(len(tblrows)-len(removed)-len(errors)),'rows added']))
        if len(removed) > 0:
            print(' Removed:\n ',removed)
        if len(errors) > 0:
            print(' Errors:\n ',errors)
    return data

def prntTime(msg):
    timeNow = datetime.now().time().strftime('%H:%M:%S')
    print('-> '.join([timeNow,msg]))

def getSoup(url):
    # Ignore SSL certificate errors
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    np.set_printoptions(threshold=sys.maxsize)
    html = urllib.request.urlopen(url, context=ctx).read()
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def FindMasterFile(mypath) :
    myFiles = []
    for (dirpath, dirnames, filenames) in walk(mypath):
        myFiles.extend(x for x in filenames if 'Master NCIP Reference Data' in x)
        break
    if len(myFiles) == 1:
        return myFiles
    else:
        i=0
        print('***',len(myFiles),'Master Ref Data files found ***')
        for mf in myFiles:
            i += 1
            print('  ',i,'-', mf)
        userResponse = int(input('Please select file to use (1-' + str(len(myFiles)) + '): '))-1
        return mypath + myFiles[userResponse]

def UpdateURLsList(csvFile):
    prntTime('Getting URLs from Master')
    # Get master URL List from csv
    csvDataFile = open(csvFile, 'r')
    csvData = csvDataFile.readlines()
    oldDate = csvData[0][-11:-1]
    oldestDate = datetime(int(oldDate[-4:]),int(oldDate[3:5]),int(oldDate[:2]))
    oldList = csvData[1:]
    csvDataFile.close

    # Find new notifications for Parts from BT Website
    prntTime('Checking BT Website for New Notifications')
    URLs = []
    baseURL = 'http://www.bt.com/pricing/notifs/'
    searchText = 'Section 2: Call Charges & Exchange Line Services '
    notifURLs = {'Part 10': '','Part 11':'','Part 12':'','Part 13':'','Part 14':'','Part 15':'','Part 17':''}

    URLlist = [baseURL+link.get('href') for link in getSoup(baseURL+'index.htm').findAll('a') if link.text == link.get('name') and datetime(int(link.text[-5:-1]),int(link.text[-8:-6]),int(link.text[-11:-9])) > oldestDate]

    for notifLink in URLlist:
        if len([x for x in notifURLs.values() if x == '']) == 0:
            break
        else:
            try:
                links = [[link.text.replace(searchText,"")[:7],notifLink.replace('index.htm','')+link.get('href')] for link in getSoup(notifLink).findAll('a') if ('..' not in link.get('href')) and (searchText in link.text)]
            except:
                print(str.format('Error with {0}',notifLink))
            for link in links:
                if link[0] in notifURLs and len(notifURLs[link[0]])==0:
                    notifURLs.update({link[0]:link[1]})
                    prntTime(str.format('New source for {0} found.',link[0]))

    # Compare new & old URLs
    for listLine in oldList:
        listLine = listLine.replace('\n','').split(',')
        PartNo,oldURL = listLine[0],listLine[1]
        newURL = notifURLs[PartNo]
        if newURL == '':
            URLs.append([PartNo,oldURL])
        else:
            URLs.append([PartNo,newURL])
    
    # Update Master URLs list of required
    if len([x for x in notifURLs.values() if x != '']) > 0:
        prntTime('Updating Master URL List')
        # Update Master CSV file
        newList = open(csvFile,'w')
        newList.write(str.format('URL List Updated on {0}',datetime.today().strftime('%d/%m/%Y')))
        newList = open(csvFile,'a')
        for URL in URLs:
            newList.write('\n'+','.join(URL))   
        newList.close
        prntTime('Master URL List Updated')
    else:
        prntTime('No new BT sources')
    return URLs

############################################
############# Start of Process #############
############################################

if __name__ == '__main__':
    prntTime('Collecting master data file') # Get data from Master Ref spreadsheet
    masterFile = FindMasterFile('//livoffice01/DATA/share/DIGITAL/Interconnect Billing/NCIP/Master Files/')

    URLs = UpdateURLsList(r'C:\Users\ggb02\OneDrive - Sky\Documents\Python\Automation\notifURLs.csv')

    url = URLs[-1]
    prntTime('Downloading Data from '+url[0])
    if url[1][:4] != 'http':
        url = 'file:///'+url[1]
        rowClass = ''
        dataClass = 's2'
    elif url[1][:4] == 'http':
        rowClass = 'datarow'
        dataClass = ''

    prntTime('Formatting International Data') # Create datatables 
    data,errors,removed,hidden,fixed = CreateIntMobDataFile(getSoup(url[1]).find_all('tr', class_=rowClass),'p',dataClass)

    prntTime('Reading International data from Master Ref Data file')
    mobileIntCodes = pd.read_excel(masterFile, sheet_name='International Mobile Bands')
    mobileIntCodes['Bt Section 17 Description'] = mobileIntCodes['Bt Section 17 Description'].str.upper()
    mobileIntCodes.set_index('Bt Section 17 Description', inplace=True)

    intMobData = pd.DataFrame([], columns=['Code','CB','Description'])

    for datarow in data:
        prefix_range = ExpandRange(','.join(datarow[2]),datarow[1])
        newData = {
            'Code':[prefix for prefix in prefix_range],
            'CB':str(mobileIntCodes.loc[datarow[0]]['CB']),
            'Description':mobileIntCodes.loc[datarow[0]]['NCIP description']
        }
        # intMobData = intMobData.append(pd.DataFrame(newData))
        intMobData = pd.concat([intMobData, pd.DataFrame(newData)])

    prntTime('Writing to Excel')
    intMobData.to_excel(r'C:\Users\ggb02\OneDrive - Sky\Documents\Python\Automation\Intl Final.xlsx', index=False, header=False)

    print('Success:\n ', intMobData.shape[0], 'records')
    print('Fixed rows:\n ',fixed)
    print('Removed rows:\n ',removed)
    print('Hidden rows:\n ',len(hidden))
    print('Other errors:\n ',len(errors))

    #non-geo process

    data = nonGeo(URLs[:-1])

    prntTime('Reading Non-Geo data from Master Ref Data file')
    nonGeoCodes = pd.read_excel(masterFile, sheet_name='UK Non Geo Ref Data', dtype=str)
    nonGeoCodes.set_index('Charge Band', inplace=True)

    nonGeoData = {
        'Code':[datarow[0] for datarow in data],
        'CB':[nonGeoCodes.loc[datarow[1]][0] for datarow in data],
        'Description':[nonGeoCodes.loc[datarow[1]][1] for datarow in data]
    }
    nonGeoData = pd.DataFrame(nonGeoData)

    prntTime('Writing to Excel')
    nonGeoData.to_excel(r'C:\Users\ggb02\OneDrive - Sky\Documents\Python\Automation\Non Geo Final.xlsx', index=False, header=False)
    print('Success:\n ',nonGeoData.shape[0], 'records')

    prntTime('Done')
    input('Press [Enter] to finish.')