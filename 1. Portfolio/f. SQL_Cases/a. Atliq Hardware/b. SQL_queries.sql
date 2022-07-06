-- Show total number of customers
select * from customers; -- All customer records
select count(*) from customers; -- Total number of customers
select * from transactions where market_code='Mark001'; -- Chennai market transactions

select distinct product_code, sales_amount
from transactions
where market_code = 'Mark001'; -- Product codes sold in Chennai

select * from transactions where currency='USD'; -- Transactions in USD (all) 

-- All transactions in 2020
--
select t.*,  d.* 
from transactions as t
inner join date as d
on t.order_date=d.date
where d.year=2020;

-- Total revenue in 2020
--
select sum(t.sales_amount) as total_sales 
from transactions as t
inner join date as d 
on t.order_date=d.date
where d.year=2020 and t.currency='INR\r'
or t.currency='USD\r';

-- Total revenue in January 2020
-- 
select sum(t.sales_amount) as jan_sales_2020
from transactions as t
inner join date as d
on t.order_date=d.date
where d.year=2020 and d.month_name='January' 
and (t.currency='INR\r' or t.currency='USD\r');


-- Total revenue in Chennai 2020
select sum(t.sales_amount) as chennai_total_sales_2020
from transactions as t
inner join date as d
on t.order_date=d.date 
where d.year=2020 and t.market_code='Mark001';
