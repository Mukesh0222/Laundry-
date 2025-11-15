use laundry_db; 
select * from users;
select * from addresses;
select * from order_items;
select * from orders;
select * from pickups_deliveries;

ALTER TABLE users MODIFY image_url LONGTEXT;

