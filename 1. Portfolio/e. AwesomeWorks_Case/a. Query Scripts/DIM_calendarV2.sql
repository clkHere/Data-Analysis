--Cleansed DIM_Date Table--
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
WHERE CalendarYear >= 2019