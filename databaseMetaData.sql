

-- CREATE TABLE IF NOT EXISTS Customers (
--     customer_id INT PRIMARY KEY,
--     first_name VARCHAR(100),
--     last_name VARCHAR(100),
--     date_of_birth DATE,
--     email VARCHAR(150),
--     phone_number VARCHAR(15)
-- );

-- CREATE TABLE Loans (
--     loan_id INT PRIMARY KEY,
--     customer_id INT,
--     loan_amount DECIMAL(15, 2),
--     interest_rate DECIMAL(5, 2),
--     loan_start_date DATE,
--     loan_end_date DATE,
--     FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
-- );

-- CREATE TABLE Loan_Impairments (
--     impairment_id INT PRIMARY KEY,
--     loan_id INT,
--     impairment_type VARCHAR(50),
--     impairment_amount DECIMAL(15, 2),
--     impairment_date DATE,
--     FOREIGN KEY (loan_id) REFERENCES Loans(loan_id)
-- );

-- CREATE TABLE Loan_Payments (
--     payment_id INT PRIMARY KEY,
--     loan_id INT,
--     payment_date DATE,
--     payment_amount DECIMAL(15, 2),
--     FOREIGN KEY (loan_id) REFERENCES Loans(loan_id)
-- );



CREATE TABLE IF NOT EXISTS Customers (
    customer_id INT PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    date_of_birth DATE,
    email VARCHAR(150),
    phone_number VARCHAR(15)
);

CREATE TABLE Loans (
    loan_id INT PRIMARY KEY,
    customer_id INT,
    loan_amount DECIMAL(15, 2),
    interest_rate DECIMAL(5, 2),
    loan_start_date DATE,
    loan_end_date DATE,
    FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
);

CREATE TABLE Loan_Impairments (
    impairment_id INT PRIMARY KEY,
    loan_id INT,
    impairment_type VARCHAR(50),
    impairment_amount DECIMAL(15, 2),
    impairment_date DATE,
    FOREIGN KEY (loan_id) REFERENCES Loans(loan_id)
);

CREATE TABLE Loan_Payments (
    payment_id INT PRIMARY KEY,
    loan_id INT,
    payment_date DATE,
    payment_amount DECIMAL(15, 2),
    FOREIGN KEY (loan_id) REFERENCES Loans(loan_id)
);



CREATE TABLE Impairments (
    impairment_id TEXT PRIMARY KEY,
    loan_id TEXT,
    AssesmentDate DATE,
    stage INTEGER,
    expected_credit_loss INTEGER,
    provision_amount INTEGER,
    FOREIGN KEY (loan_id) REFERENCES Loans(loan_id)
);
"""