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
	p.ProductKey asc


