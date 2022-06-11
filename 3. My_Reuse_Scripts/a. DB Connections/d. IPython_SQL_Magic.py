#Load the SQL module
%load_ext sql

#Connect to a database
%sql sqlite://
  
#Option 1: Create a new database
%%sql
Create Table EMPLOYEE(firstname, varchar(50), lastname varchar(50));
Insert Into EMPLOYEE values('Cal', 'David');
Insert Into EMPLOYEE value('Dwight', 'Freeman');

%sql Select * From EMPLOYEE;
#------------------------------------

#Option 2: Load existing database

##Specify path of the database
%sql sqlite:////users/[PATH]/[PATH]/[FILENAME].sqlite
  
#Display first few rows of table
%sql select * from EMPLOYEE where emp_num = '007' And ID <=3 Limit 10;
