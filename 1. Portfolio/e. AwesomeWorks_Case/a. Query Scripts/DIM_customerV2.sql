-- Cleansed Customer Table
SELECT
	c.customerkey CustomerKey, c.firstname [First Name], c.lastname [Last Name], c.firstname + ' ' + lastname [Full Name],
	-- Convert Single letters to full description
	CASE c.gender WHEN 'M' Then 'Male' WHEN 'F' Then 'Female' END AS Gender,
	c.datefirstpurchase DateFirstPurchase,
	g.city [Customer City] -- joining Customer City from Geography table. 
FROM
	dbo.dimcustomer as c
	LEFT JOIN dbo.dimgeography as g on g.geographykey = c.geographykey
ORDER BY
	CustomerKey ASC -- Ordered list by Customer Key