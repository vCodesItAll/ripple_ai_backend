DROP TABLE products;

CREATE TABLE products (
    id SERIAL NOT NULL PRIMARY KEY,
    title varchar(50),
    description varchar(255),
    at_sale Boolean,
    inventory INT NOT NULL,
    added_at timestamp NOT NULL
)