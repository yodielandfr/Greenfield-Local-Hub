README Contents:

- file structure
- how to set up (dependencies and pip installs)
- example login information and producer information
------------------------
File structure:

once the zipped file is downloaded and unzipped it should contain:

- queries.py
- main.py
- easy.py
- README.txt
- Task2_Test_Log_[U00090325]_[Kelly]_[M]
- Task2_ContentAssetsLog_[U00090325]_[Kelly]_[M]
- > static
	- settings.js
	- styles.css
	- > images
		- apples.png
		- bacon.png
		- cheese.png
		- eggs.png
		- farm1.png
		- farm2.png
		- farm3.png
		- GLH.png (logo)
		- honey.jpg
		- milk.png
		- potato.png
		- salad.png
		- sourdough.png
- > Templates 
	- about.html
	- alerts.html
	- basket.html
	- checkout.html
	- error.html
	- landing.html
	- my_account.html
	- my_orders.html
	- order_confirmed.html
	- producer_dashboard.html
	- producer_profile.html
	- producers_login.html
	- producers.html
	- product.html
	- products.html
	- settings.html
	- sign_in.html
	- sign_up.html

------------------------

How to set up this project:

Python:
- Please ensure you are using Python 3.11+ (any version higher still works). You can test in the python terminal by doing 'py --version'

Install the libraries:
- Open the powershell in the project file and run the following commands:
	- py -m pip install flask
	- py -m pip install argon2-cffi

Now you can run 'main.py', refresh the directory in the file explorer - You should now have a file named 'database.db'.

If you have the database file then run 'main.py' again, look in the terminal and CTRL + CLICK 'http://127.0.0.1:5000'. This will bring you to your locally hosted version of this site.

------------------------

Example login information:

- For a customer account >
	- You will need to make an account to interact as a customer, navigate to sign up and fill in the fields 
	- example signup/login information: Email: test@test | Password: Newpass123!

For a producer account >
	- Since we only want local farmers to be sellers; the producer login requires a producer ID which would be 'issued' to somebody rather than having them sign up. 
	- Because of this, the company (GLH) would create the sellers login information. 
	- This ensures that only trusted producers would have a sellers profile on our site.

	- Test producer login information: email: quartzfarm@example.com | password: Producer1!Pass | ID: 1




