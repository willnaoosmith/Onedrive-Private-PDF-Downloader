from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
import sys, os, img2pdf
from time import sleep

try:
	#Sets up selenium with no logfile
	service = Service(log_path=os.devnull)
	browser = webdriver.Firefox(service=service)

	#Asks for user URL and navigates to it
	YourUrl = input("Paste your URL: ")
	browser.get(YourUrl)

	#Waits for user authentication and confirmation
	input("Make sure to authenticate and on the preview of the desired PDF File.\nOnce the file is loaded, and you can see the page counter on the bottom, press [ENTER] to start.\nThe script will stop when all the pages are exported.")
	sleep(1)

	#Gets the total number of pages inside the file
	try:
		totalOfPages = int(browser.find_element(By.CLASS_NAME, "status_719d330e").text.replace("/", ""))
	
	except NoSuchElementException:
		totalOfPages = int(browser.find_element(By.CLASS_NAME, "status_5a88b9b2").text.replace("/", ""))	

	except Exception as error:
		print(f"""
			An unexpected error ocurred while getting the total of pages of the document!
			You can report this message to https://github.com/willnaoosmith/Onedrive-Private-PDF-Downloader/issues
			Here's the error message: {str(error)}
		""")
		
		try:
			totalOfPages = int(input("\nFor now, type here the total quantity of pages in your document: "))
		
		except Exception as error:
			print(f"An error ocurred while getting the total of pages you provided, please try again with a valid total of pages.")
	else:
		counter = 1
	
	#Gets the filename
	browser.find_element(By.XPATH, "//button[@aria-label='Info. Open the details pane']").click()
	sleep(1)
	filename = browser.find_element(By.CLASS_NAME, "od-DetailsPane-PrimaryPane-header-title").text	
	
	print(f'Starting the export of the file "{filename}". This might take a while depending on the amount of pages.')

	filesList = []

	#Creates a temporary directory to save the files
	try:
		os.mkdir("Images")
		
	except:
		print("Error creating temporary directory. Make sure to have permissions on the current folder.")
		sys.exit(1)

	while counter <= totalOfPages:		
		sleep(1)
		
		#Takes a screenshot of every page of the PDF file inside the browser and saves it as a PNG file
		browser.find_element(By.CSS_SELECTOR, "canvas").screenshot(f"Images/{str(counter)}.png")	
		filesList.append(f"Images/{str(counter)}.png")
		print(f"Page {str(counter)} of {str(totalOfPages)} exported.")
		
		counter += 1

		nextPageButton = browser.find_elements(By.XPATH, "//button[@aria-label='Go to the next page.']")[-1]
		browser.execute_script("arguments[0].click();", nextPageButton)

	#Saves all the exported PNG files in a PDF file
	print('Saving the file as "{filename}"')
	with open(filename, "wb") as out:
		out.write(img2pdf.convert(filesList))

except Exception as error:
	print(error)
	sys.exit(1)

finally:

	#Deletes the temporary folder and quits the selenium job
	try:
		os.rmdir("Images")

	except:
		pass

	browser.quit()