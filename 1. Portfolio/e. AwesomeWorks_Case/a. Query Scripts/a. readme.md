## Software Used to Perform Queries
- Microsoft SQL Server 2019
- SQL Server Management Studio

## Snapshot

```sql
--Cleansed DIM_Calendar Table--
SELECT
	DateKey,
	FullDateAlternateKey Date,
	EnglishDayNameOfWeek Day,
	EnglishMonthName Month, 
	LEFT(EnglishMonthName, 3) as MonthShort,
	MonthNumberofYear MonthNo, 
	CalendarQuarter Quarter, 
	CalendarYear as Year 
FROM dbo.DimDate
-- Sales Manager wanted sales numbers for 2019 --
WHERE CalendarYear >= 2019;

-- Cleansed Customer Table
SELECT
	c.customerkey CustomerKey, 
  c.firstname [First Name], 
  c.lastname [Last Name], 
  c.firstname + ' ' + lastname [Full Name],
	-- Convert Single letters to full description
	CASE c.gender WHEN 'M' Then 'Male' WHEN 'F' Then 'Female' END AS Gender,
	c.datefirstpurchase DateFirstPurchase,
	g.city [Customer City] -- joining Customer City from Geography table. 
FROM
	dbo.dimcustomer as c
	LEFT JOIN dbo.dimgeography as g on g.geographykey = c.geographykey
ORDER BY
	CustomerKey ASC -- Ordered list by Customer Key;
  
-- Cleansed Products Table
SELECT
	p.ProductKey,
	p.[ProductAlternateKey] AS ProductItemCode, 
	p.EnglishProductName [Product Name], 
	ps.EnglishProductSubcategoryName [Sub Category], --Joined from 'Sub Category' table
	pc.EnglishProductCategoryName [Product Category], --Joined from 'Category' table
	p.Color [Product Color],
	p.Size [Product Size], 
	p.ProductLine [Product Line],
	p.ModelName [Product Model Name],
	p.EnglishDescription [Product Description],	
	ISNULL (p.Status, 'Outdated') [Product Status] -- Differentiates between current/outdated results

FROM 
	dbo.DimProduct as p
	LEFT JOIN dbo.DimProductSubcategory AS ps ON ps.ProductSubcategoryKey = p.ProductSubcategoryKey
	LEFT JOIN dbo.DimProductCategory AS pc ON ps.ProductCategoryKey = pc.ProductCategoryKey

ORDER BY
	p.ProductKey asc;
  
-- Cleansed FACT_Sales table
SELECT
	ProductKey, OrderDateKey, DueDateKey, ShipDateKey, CustomerKey,
	SalesOrderNumber, round(SalesAmount,2)
FROM
	dbo.FactInternetSales
WHERE
	LEFT (OrderDateKey, 4) >= Year(GetDate()) -2 -- Limiting extraction to 2 years
ORDER BY
	OrderDateKey asc

```
