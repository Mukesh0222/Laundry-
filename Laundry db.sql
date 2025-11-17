use laundry_db; 
select * from users;
select * from addresses;
select * from order_items;
select * from orders;
select * from pickups_deliveries;

ALTER TABLE users MODIFY image_url LONGTEXT;

SHOW COLUMNS FROM pickups_deliveries LIKE 'status';


ALTER TABLE pickups_deliveries 
ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;