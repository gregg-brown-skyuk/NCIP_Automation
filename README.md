# NCIP Automated Process

This python script creates a list of Dialling Codes, Cost Codes and Destination Names for International Mobile and Non-Geographic prefixes.

This is done by:
1. scraping the [BT Notifications Site][bt_notifs] for updated lists and downloading new data,
2. reformatting the data to the correct format,
3. condensing all number ranges where there exists a final digit for each 0-9,
4. writing the new number list to excel sheet.

---
### Required Additional Python Libraries

* `beautifulboup4`
* `pandas`
* `numpy`


---
[Gregg Brown][email]

*Commited to Github June 2022*

<!-- links -->
[email]: mailto:gregg.brown@sky.uk
[bt_notifs]: http://www.bt.com/pricing/notifs/