CREATE DATABASE belt_paradise;
USE belt_paradise;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    avatar VARCHAR(255),
    remember_token VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    image VARCHAR(255),
    category VARCHAR(50),
    brand VARCHAR(50),
    description TEXT,
    stock INT DEFAULT 0,
    is_guarantee BOOLEAN DEFAULT FALSE,
    is_offer BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wishlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    product_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    total_amount DECIMAL(10,2),
    status VARCHAR(50),
    tracking_number VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

INSERT INTO products (name, price, image, category, brand, description, stock, is_guarantee, is_offer) VALUES
('Classic Leather Belt', 29.99, 'belt1.jpg', 'Leather', 'Gucci', 'Premium full-grain leather belt', 50, TRUE, FALSE),
('Canvas Web Belt', 19.99, 'belt2.jpg', 'Canvas', 'Levi\'s', 'Durable canvas belt with metal buckle', 30, FALSE, TRUE),
('Braided Leather Belt', 39.99, 'belt3.jpg', 'Leather', 'Armani', 'Hand-braided genuine leather', 25, TRUE, FALSE);


DELETE FROM users;



select * from users;


-- 📍 Addresses
CREATE TABLE addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    full_name VARCHAR(100),
    phone VARCHAR(15),
    address_line TEXT,
    city VARCHAR(50),
    state VARCHAR(50),
    pincode VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 🧾 Order Items (very important)
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    price DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

ALTER TABLE orders 
ADD COLUMN address_id INT,
ADD FOREIGN KEY (address_id) REFERENCES addresses(id);


UPDATE orders SET status='Shipped' WHERE id=1;
UPDATE orders SET status='Out for Delivery' WHERE id=1;
UPDATE orders SET status='Delivered' WHERE id=1;


DESCRIBE users;
DROP TABLE users;

ALTER TABLE users CHANGE name username VARCHAR(50) NOT NULL;


select * from users;


drop table products;


-- Change column types & names
ALTER TABLE products 
MODIFY name VARCHAR(255),
MODIFY price INT;

-- Remove unwanted columns
ALTER TABLE products 
DROP COLUMN image,
DROP COLUMN category,
DROP COLUMN brand,
DROP COLUMN stock,
DROP COLUMN is_guarantee,
DROP COLUMN is_offer;

-- Add new required columns
ALTER TABLE products 
ADD COLUMN offer VARCHAR(100),
ADD COLUMN guarantee VARCHAR(100),
ADD COLUMN material VARCHAR(255);



CREATE TABLE IF NOT EXISTS product_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    image_url VARCHAR(255),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS product_videos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    video_url VARCHAR(255),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS product_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    tag VARCHAR(100),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);


show tables;


select * from products;

delete from products;
INSERT INTO products (name, price, offer, guarantee, material, description)
VALUES (
    'Premium Leather Belt',
    999,
    '20% OFF',
    '1 Year Warranty',
    'Genuine Leather',
    'High quality stylish belt for men'
);

INSERT INTO product_images (product_id, image_url)
VALUES 
(1, '/static/images/belt1.jpg'),
(1, '/static/images/belt2.jpg'),
(1, '/static/images/belt3.jpg');



INSERT INTO product_videos (product_id, video_url)
VALUES 
(1, '/static/videos/belt.mp4');


INSERT INTO product_tags (product_id, tag)
VALUES 
(1, 'Best Seller'),
(1, 'Guaranteed');



-- ================= PRODUCT 2 =================
INSERT INTO products (name, price, offer, guarantee, material, description)
VALUES ('Classic Formal Belt', 799, '15% OFF', '6 Months Warranty', 'PU Leather', 'Perfect belt for office and formal wear');

INSERT INTO product_images (product_id, image_url) VALUES
(2, '/static/images/belt2.jpg'),
(2, '/static/images/belt2.jpg'),
(2, '/static/images/belt2.jpg');

INSERT INTO product_videos (product_id, video_url) VALUES
(2, '/static/videos/belt2.mp4');

INSERT INTO product_tags (product_id, tag) VALUES
(2, 'Formal'),
(2, 'Office Wear');


-- PRODUCT
INSERT INTO products (name, price, offer, guarantee, material, description)
VALUES ('Luxury Designer Belt', 1999, '25% OFF', '2 Years Warranty', 'Italian Leather', 'Premium luxury belt');

SET @pid = LAST_INSERT_ID();

INSERT INTO product_images (product_id, image_url) VALUES
(@pid, '/static/images/belt3.jpg'),
(@pid, '/static/images/belt3.jpg');

INSERT INTO product_videos (product_id, video_url) VALUES
(@pid, '/static/videos/belt4.mp4');

INSERT INTO product_tags (product_id, tag) VALUES
(@pid, 'Luxury'),
(@pid, 'Premium');



select * from wishlist;


CREATE TABLE cart (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    product_id INT,
    quantity INT DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);


CREATE TABLE blog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE,
    content TEXT,
    image VARCHAR(500),
    author VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_published BOOLEAN DEFAULT TRUE
);


INSERT INTO blog (title, slug, content, image, author)
VALUES 
(
    'Top 5 Leather Belts in 2026',
    'top-5-leather-belts',
    'This is a premium guide about leather belts...',
    'C:\Users\saksh\OneDrive\Documents\E-commerce-project\static\images\01.png',
    'Admin'
),
(
    'How to Choose Perfect Belt',
    'choose-perfect-belt',
    'Choosing the right belt is important...',
    '/static/images/blog2.jpg',
    'Admin'
),
(
    'best belts',
    'perfect-belt',
    'Choosing the perfect belt is important...',
    '/static/images/blog3.jpg',
    'Admin'
),
(
    'client love products',
    'clients love',
    'customer requirements are important for us..',
    '/static/images/blog1.jpg',
    'Admin'
);


INSERT INTO blog (title, slug, content, image, author)
VALUES 
(
    'Top 5  Belts in 2026',
    'top-5-belts',
    'This is a premium guide about leather belts...',
    'C:\Users\saksh\OneDrive\Documents\E-commerce-project\static\images\01.png',
    'Admin'
);

CREATE TABLE subscribers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

show tables;

select * from products;
describe products;


ALTER TABLE users 
ADD COLUMN is_admin varchar(500); 

UPDATE users SET is_admin = 1 WHERE email = 'sakshibhati180@gmail.com';

select * from users;


ALTER TABLE product_images ADD COLUMN is_primary BOOLEAN DEFAULT FALSE;

ALTER TABLE products
ADD COLUMN original_price INT DEFAULT NULL,
ADD COLUMN discount_percent INT DEFAULT 0,
ADD COLUMN rating FLOAT DEFAULT NULL,
ADD COLUMN size_unit VARCHAR(20) DEFAULT 'inch';


CREATE TABLE product_sizes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    size_label VARCHAR(50),
    size_value FLOAT,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);
CREATE TABLE category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);


ALTER TABLE blog
ADD COLUMN category_id INT,
ADD COLUMN seo_title VARCHAR(255),
ADD COLUMN seo_description VARCHAR(255);


ALTER TABLE blog
ADD CONSTRAINT fk_category
FOREIGN KEY (category_id) REFERENCES category(id)
ON DELETE SET NULL;


INSERT INTO category (name) VALUES
('Leather'),
('Fashion'),
('Style Guide'),
('Care Tips'),
('New Collection');


UPDATE blog
SET 
    category_id = 1,
    seo_title = title,
    seo_description = SUBSTRING(content, 1, 150)
WHERE category_id IS NULL;

CREATE TABLE tag (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE
);

CREATE TABLE blog_tags (
    blog_id INT,
    tag_id INT,
    PRIMARY KEY (blog_id, tag_id),
    FOREIGN KEY (blog_id) REFERENCES blog(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
);

INSERT INTO tag (name) VALUES
('leather'),
('premium'),
('fashion'),
('style'),
('men'),
('luxury');

-- Blog 1 → leather, premium
INSERT INTO blog_tags (blog_id, tag_id) VALUES (1, 1), (1, 2);

-- Blog 2 → fashion, style
INSERT INTO blog_tags (blog_id, tag_id) VALUES (2, 3), (2, 4);

-- Blog 3 → men
INSERT INTO blog_tags (blog_id, tag_id) VALUES (3, 5);

-- Blog 4 → luxury
INSERT INTO blog_tags (blog_id, tag_id) VALUES (4, 6);
SELECT id, title, category_id, seo_title FROM blog;

INSERT INTO blog_tags (blog_id, tag_id)
SELECT b.id, t.id
FROM blog b, tag t
WHERE b.title = 'best belts' AND t.name = 'men';


UPDATE blog SET image = '/static/images/01.png' WHERE id = 1;

UPDATE blog SET slug = 'clients-love' WHERE id = 4;


-- Drop old wrong FK (name check first)
ALTER TABLE orders DROP FOREIGN KEY orders_ibfk_2;

-- Add correct FK
ALTER TABLE orders
ADD CONSTRAINT fk_orders_address
FOREIGN KEY (address_id) REFERENCES addresses(id)
ON DELETE SET NULL;


ALTER TABLE orders
MODIFY total_amount DECIMAL(10,2),
MODIFY status VARCHAR(50) DEFAULT 'Pending';

ALTER TABLE order_items
DROP FOREIGN KEY order_items_ibfk_1;

ALTER TABLE order_items
ADD CONSTRAINT fk_order_items_order
FOREIGN KEY (order_id) REFERENCES orders(id)
ON DELETE CASCADE;

CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);

ALTER TABLE addresses
ADD CONSTRAINT fk_address_user
FOREIGN KEY (user_id) REFERENCES users(id)
ON DELETE CASCADE;

UPDATE orders 
SET status = 'Processing' 
WHERE status IS NULL AND id > 0;

ALTER TABLE orders
MODIFY status ENUM('Pending','Shipped','Out for Delivery','Delivered','Cancelled') DEFAULT 'Pending';


SET SQL_SAFE_UPDATES = 0;

UPDATE orders SET status = 'Processing' WHERE status IS NULL;

SET SQL_SAFE_UPDATES = 1;

UPDATE orders 
SET status = 'Pending' 
WHERE status IS NULL AND id > 0;

ALTER TABLE orders
MODIFY status ENUM('Pending','Shipped','Out for Delivery','Delivered','Cancelled') DEFAULT 'Pending';

SHOW COLUMNS FROM orders LIKE 'status';

SELECT DISTINCT status FROM orders;

ALTER TABLE orders 
ADD COLUMN new_status ENUM(
'Pending','Shipped','Out for Delivery','Delivered','Cancelled'
) DEFAULT 'Pending';

UPDATE orders 
SET new_status = 
CASE 
    WHEN status IN ('Pending','Shipped','Out for Delivery','Delivered','Cancelled') THEN status
    ELSE 'Pending'
END;

ALTER TABLE orders DROP COLUMN status;

ALTER TABLE orders 
CHANGE new_status status ENUM(
'Pending','Shipped','Out for Delivery','Delivered','Cancelled'
) DEFAULT 'Pending';

SHOW COLUMNS FROM orders LIKE 'status';

UPDATE orders SET status='Pending' WHERE status='Processing';
ALTER TABLE orders 
MODIFY status ENUM('Pending','Shipped','Out for Delivery','Delivered','Cancelled') 
DEFAULT 'Pending';


select * from products;

UPDATE products 
SET original_price = 700,
    discount_percent = 21,
    rating = 4.6
WHERE id = 1;

UPDATE products 
SET original_price = 650,
    discount_percent = 23,
    rating = 4.4
WHERE id = 2;

UPDATE products 
SET original_price = 1250,
    discount_percent = 20,
    rating = 4.8
WHERE id = 4;

UPDATE products 
SET original_price = 940,
    discount_percent = 15,
    rating = 4.5
WHERE id = 5;

UPDATE products 
SET original_price = 2600,
    discount_percent = 23,
    rating = 4.9
WHERE id = 6;

UPDATE products 
SET original_price = 750,
    discount_percent = 20,
    rating = 4.5
WHERE id = 7;

UPDATE products 
SET original_price = 2400,
    discount_percent = 17,
    rating = 4.3
WHERE id = 8;

UPDATE products 
SET original_price = 1175,
    discount_percent = 15,
    rating = 4.7
WHERE id = 9;


INSERT INTO product_sizes (product_id, size_label, size_value) VALUES
(1, '28', 28),
(1, '30', 30),
(1, '32', 32),
(1, '34', 34),
(1, '36', 36),

(2, '30', 30),
(2, '32', 32),
(2, '34', 34),

(4, '30', 30),
(4, '32', 32),
(4, '34', 34),
(4, '36', 36),

(5, '32', 32),
(5, '34', 34),
(5, '36', 36),

(6, '30', 30),
(6, '32', 32),
(6, '34', 34),
(6, '36', 36),
(6, '38', 38),

(7, '30', 30),
(7, '32', 32),
(7, '34', 34),

(8, '32', 32),
(8, '34', 34),
(8, '36', 36),

(9, '30', 30),
(9, '32', 32),
(9, '34', 34),
(9, '36', 36);

CREATE TABLE email_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subject VARCHAR(255),
    content TEXT,
    sent_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    sent_by VARCHAR(100),
    total_users INT,
    opened INT DEFAULT 0
);


CREATE TABLE email_track (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email_id INT,
    user_email VARCHAR(100),
    opened BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (email_id) REFERENCES email_history(id) ON DELETE CASCADE
);
select * from products;

describe products;


CREATE TABLE colors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    code VARCHAR(20)
);

CREATE TABLE product_colors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    color_id INT,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY (color_id) REFERENCES colors(id) ON DELETE CASCADE
);

INSERT INTO colors (name, code) VALUES
('Blue', '#1E3A8A'),
('Grey', '#808080');


INSERT INTO product_colors (product_id, color_id) VALUES

-- 1 Classic Leather Belt
(1,1), (1,2), (1,3),

-- 2 Canvas Web Belt
(2,4), (2,5),

-- 4 Premium Leather Belt
(4,1), (4,2), (4,3),

-- 5 Classic Formal Belt
(5,1), (5,2),

-- 6 Luxury Designer Belt
(6,1), (6,2), (6,3),

-- 7 Leather Belt
(7,1), (7,2),

-- 8 Canvas Web Belt
(8,4), (8,5),

-- 9 Luxury Designer Belt
(9,1), (9,2), (9,3),

-- 10 Canvas Web Belt
(10,4), (10,5),

-- 11 Classic Leather Belt
(11,1), (11,2), (11,3);

describe payment_;


SELECT p.name, c.name AS color
FROM products p
JOIN product_colors pc ON p.id = pc.product_id
JOIN colors c ON pc.color_id = c.id
ORDER BY p.id;