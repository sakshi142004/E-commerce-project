CREATE DATABASE belt_store;
USE belt_store;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100),
    remember_token VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(100),
    product_name VARCHAR(255),
    price INT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wishlist (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_email VARCHAR(100),
    product_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    price INT NOT NULL,
    offer VARCHAR(100),
    guarantee VARCHAR(100),
    material VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE product_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    image_url VARCHAR(255),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);


CREATE TABLE product_videos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    video_url VARCHAR(255),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE product_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    product_id INT,
    tag VARCHAR(100),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);


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




select * from products;

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