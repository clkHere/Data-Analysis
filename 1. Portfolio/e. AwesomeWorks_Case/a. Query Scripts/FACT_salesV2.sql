-- Cleansed sales table
SELECT
	ProductKey, OrderDateKey, DueDateKey, ShipDateKey, CustomerKey,
	SalesOrderNumber, round(SalesAmount,2)
FROM
	dbo.FactInternetSales
WHERE
	LEFT (OrderDateKey, 4) >= Year(GetDate()) -2 -- Limiting extraction to 2 years
ORDER BY
	OrderDateKey asc